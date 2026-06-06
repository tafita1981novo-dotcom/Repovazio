#!/usr/bin/env python3
"""
check_playlist_quality.py — Verifica e apaga vídeos da playlist que:
  1. Têm score < 95 (viral_score OU quality_score_current)
  2. O áudio termina ANTES do vídeo (diferença > 2s)

Para vídeos já publicados no YouTube → deleta do canal + marca no Supabase
Para vídeos mp4_ready → bloqueia publicação (status=quality_blocked)
"""
import os, json, re, time, subprocess, tempfile, urllib.request, urllib.error, urllib.parse

SBU = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
H_SB  = {"apikey": SBK, "Authorization": f"Bearer {SBK}"}
H_SB_J = {**H_SB, "Content-Type": "application/json"}

SCORE_MIN = 95
AUDIO_GAP_MAX = 2.0  # segundos de tolerância

def log(*a): print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)

def http_json(url, method="GET", body=None, headers=None, timeout=30):
    h = dict(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode() if not isinstance(body, bytes) else body
        h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else b"", {}

def sb_select(table, q):
    s, b, _ = http_json(f"{SBU}/rest/v1/{table}?{q}", headers=H_SB)
    if s != 200: raise RuntimeError(f"select {s}: {b[:200]}")
    return json.loads(b)

def sb_patch(table, q, payload):
    s, b, _ = http_json(f"{SBU}/rest/v1/{table}?{q}", method="PATCH",
                        body=payload, headers=H_SB_J)
    if s not in (200, 204): log(f"  WARN patch {s}: {b[:200]}")

def get_yt_token():
    keys = ["secret:YT_CLIENT_ID","secret:YT_CLIENT_SECRET","secret:YT_REFRESH_TOKEN"]
    q = "cache_key=in.(" + ",".join(urllib.parse.quote(k) for k in keys) + ")&select=cache_key,value"
    _, b, _ = http_json(f"{SBU}/rest/v1/ia_cache?{q}", headers=H_SB)
    creds = {}
    for row in json.loads(b):
        k = row["cache_key"].replace("secret:YT_","")
        if row.get("value"): creds[k] = row["value"].strip()
    if not all(creds.get(k) for k in ["CLIENT_ID","CLIENT_SECRET","REFRESH_TOKEN"]):
        return None
    body = urllib.parse.urlencode({
        "client_id": creds["CLIENT_ID"], "client_secret": creds["CLIENT_SECRET"],
        "refresh_token": creds["REFRESH_TOKEN"], "grant_type": "refresh_token",
    }).encode()
    s, raw, _ = http_json("https://oauth2.googleapis.com/token", method="POST",
        body=body, headers={"Content-Type":"application/x-www-form-urlencoded"})
    if s != 200: return None
    return json.loads(raw)["access_token"]

def ffprobe_info(mp4_bytes):
    """Retorna (video_dur_s, audio_dur_s) ou (None, None)"""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(mp4_bytes)
        path = tmp.name
    try:
        res = subprocess.run(
            ["ffprobe","-v","quiet","-print_format","json","-show_streams",path],
            capture_output=True, text=True, timeout=30
        )
        if res.returncode != 0: return None, None
        streams = json.loads(res.stdout).get("streams", [])
        vid_dur = aud_dur = None
        for s in streams:
            dur = float(s.get("duration") or 0)
            if s.get("codec_type") == "video" and dur > 0:
                vid_dur = dur
            elif s.get("codec_type") == "audio" and dur > 0:
                aud_dur = dur
        # Fallback: format duration
        if vid_dur is None:
            res2 = subprocess.run(
                ["ffprobe","-v","quiet","-print_format","json","-show_format",path],
                capture_output=True, text=True, timeout=30
            )
            if res2.returncode == 0:
                fmt = json.loads(res2.stdout).get("format",{})
                vid_dur = float(fmt.get("duration") or 0) or None
        return vid_dur, aud_dur
    except Exception as e:
        log(f"  ffprobe err: {e}")
        return None, None
    finally:
        try: os.unlink(path)
        except: pass

def download_mp4(url, max_mb=150):
    """Baixa um MP4, retorna bytes ou None"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"quality-checker/1.0"})
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read(max_mb * 1024 * 1024 + 1)
        if len(data) > max_mb * 1024 * 1024:
            log(f"  ⚠️  MP4 muito grande (>{max_mb}MB), usando apenas header")
            return data[:20*1024*1024]  # 20MB para ffprobe estimar
        return data
    except Exception as e:
        log(f"  Download falhou: {e}")
        return None

def delete_yt_video(tok, video_id):
    req = urllib.request.Request(
        f"https://www.googleapis.com/youtube/v3/videos?id={video_id}",
        method="DELETE")
    req.add_header("Authorization", f"Bearer {tok}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="ignore")

def extract_yt_id(url):
    if not url: return None
    m = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/))([A-Za-z0-9_-]{11})', url)
    return m.group(1) if m else None

def get_score(row):
    """Retorna o melhor score disponível"""
    vs = row.get("viral_score") or 0
    qs = row.get("quality_score_current") or 0
    return max(vs, qs)

def check_mp4(mp4_url, title):
    """Verifica duração áudio vs vídeo. Retorna (ok, motivo)"""
    if not mp4_url:
        return False, "SEM_MP4_URL"
    log(f"  Baixando MP4 para verificar: {mp4_url[-60:]}")
    data = download_mp4(mp4_url)
    if not data:
        return False, "DOWNLOAD_FALHOU"
    vid_dur, aud_dur = ffprobe_info(data)
    if vid_dur is None:
        return False, "DURACAO_INDETERMINAVEL"
    if aud_dur is None:
        # Sem trilha de áudio separada — pode ser mux junto, verificar pelo formato
        log(f"  Sem stream de áudio separado detectado (dur={vid_dur:.1f}s)")
        return True, f"vid={vid_dur:.1f}s aud=mux"
    gap = vid_dur - aud_dur
    log(f"  Duração: vídeo={vid_dur:.2f}s | áudio={aud_dur:.2f}s | gap={gap:.2f}s")
    if gap > AUDIO_GAP_MAX:
        return False, f"AUDIO_TERMINA_ANTES: vídeo={vid_dur:.1f}s aud={aud_dur:.1f}s gap={gap:.1f}s"
    return True, f"vid={vid_dur:.1f}s aud={aud_dur:.1f}s gap={gap:.1f}s"

def main():
    log("=" * 65)
    log("CHECK PLAYLIST QUALITY — Score ≥95 + Áudio ≥ Vídeo")
    log(f"Critérios: score>={SCORE_MIN} | áudio gap ≤{AUDIO_GAP_MAX}s")
    log("=" * 65)

    tok = get_yt_token()
    if not tok: log("⚠️  Token YT falhou — só verificará mp4_ready"); 

    # Buscar todos os vídeos de playlist (published + mp4_ready)
    rows = sb_select("content_pipeline",
        "status=in.(published,mp4_ready)"
        "&target_platform=in.(youtube_long,youtube_shorts,youtube)"
        "&select=id,title,format,target_platform,youtube_url,mp4_url,video_url,"
        "viral_score,quality_score_current,seo_score,duracao_min,status"
        "&order=id.asc&limit=100")

    log(f"Vídeos para verificar: {len(rows)}")
    log("")

    to_delete_yt = []    # (youtube_id, row, motivo)
    to_block     = []    # (row, motivo)
    ok_rows      = []

    for row in rows:
        pid   = row['id']
        title = (row.get('title') or '?')[:55]
        score = get_score(row)
        yt_url = row.get('youtube_url')
        mp4_url = row.get('mp4_url') or row.get('video_url')
        status = row.get('status','')

        log(f"\n[{pid}] {title}")
        log(f"  score={score} | status={status} | yt={bool(yt_url)} | mp4={bool(mp4_url)}")

        motivos = []

        # 1. Verificar score
        if score < SCORE_MIN and score > 0:
            motivos.append(f"SCORE_BAIXO:{score}<{SCORE_MIN}")
            log(f"  ❌ Score {score} < {SCORE_MIN}")
        elif score == 0 and not yt_url:
            # Score 0 em mp4_ready sem publicação → checar só áudio
            log(f"  ⚠️  Score não calculado ({score})")
        else:
            log(f"  ✅ Score: {score}")

        # 2. Verificar áudio vs vídeo
        if mp4_url:
            ok_audio, audio_info = check_mp4(mp4_url, title)
            if not ok_audio:
                # Inconclusivo (ffprobe/download falhou) → NÃO deletar
                inconclusivo = any(x in audio_info for x in
                    ["DURACAO_INDETERMINAVEL","DOWNLOAD_FALHOU","ffprobe","SEM_MP4"])
                if inconclusivo:
                    log(f"  ⚠️  Áudio inconclusivo — não deletar: {audio_info}")
                else:
                    motivos.append(audio_info)
                    log(f"  ❌ Áudio: {audio_info}")
            else:
                log(f"  ✅ Áudio OK: {audio_info}")
        else:
            log(f"  ⚠️  Sem mp4_url para verificar áudio")

        if motivos:
            if yt_url:
                yt_id = extract_yt_id(yt_url)
                if yt_id:
                    to_delete_yt.append((yt_id, row, " | ".join(motivos)))
                    log(f"  🗑  MARCAR PARA DELETAR DO YOUTUBE: {yt_id}")
            else:
                to_block.append((row, " | ".join(motivos)))
                log(f"  🚫 BLOQUEAR (não está no YouTube ainda)")
        else:
            ok_rows.append(row)

        time.sleep(0.2)

    log("")
    log("=" * 65)
    log(f"RESUMO: {len(ok_rows)} OK | {len(to_delete_yt)} deletar YT | {len(to_block)} bloquear")
    log("=" * 65)

    # Deletar do YouTube
    deleted_yt = 0
    for yt_id, row, motivo in to_delete_yt:
        log(f"\n  🗑  Deletando YouTube {yt_id} — {motivo[:60]}")
        if tok:
            code, err = delete_yt_video(tok, yt_id)
            if code in (204, 200, 404):
                log(f"     ✅ HTTP {code}")
                deleted_yt += 1
                sb_patch("content_pipeline", f"id=eq.{row['id']}", {
                    "status": "deleted_bad_quality",
                    "error": f"DELETADO: {motivo[:400]}",
                    "youtube_url": None,
                })
            else:
                log(f"     ❌ HTTP {code}: {err[:80]}")
        else:
            log(f"     ⚠️  Sem token YT")

    # Bloquear mp4_ready
    blocked = 0
    for row, motivo in to_block:
        log(f"\n  🚫 Bloqueando [{row['id']}] — {motivo[:80]}")
        sb_patch("content_pipeline", f"id=eq.{row['id']}", {
            "status": "quality_blocked",
            "publish_blocked": True,
            "publish_block_reason": motivo[:400],
        })
        blocked += 1

    log("")
    log(f"✅ CONCLUÍDO: {deleted_yt} deletados do YT | {blocked} bloqueados | {len(ok_rows)} aprovados")

if __name__ == "__main__":
    main()
