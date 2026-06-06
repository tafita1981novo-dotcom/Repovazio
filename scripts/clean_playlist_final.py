#!/usr/bin/env python3
"""
clean_playlist_final.py
1. Busca TODOS os vídeos do canal via YouTube API (uploads playlist)
2. Para cada um, verifica no Supabase: score ≥ 95?
3. Baixa o MP4 (se tiver url) e verifica áudio vs vídeo
4. Deleta qualquer vídeo que falhar nos critérios
5. Verifica estado do broadcast — cancela upcoming se existir
"""
import os, json, re, time, subprocess, tempfile, urllib.request, urllib.error, urllib.parse

SBU = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
H_SB   = {"apikey": SBK, "Authorization": f"Bearer {SBK}"}
H_SB_J = {**H_SB, "Content-Type": "application/json"}

SCORE_MIN   = 95
AUDIO_GAP_MAX = 2.0

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
    if s not in (200,204): log(f"  WARN patch {s}: {b[:100]}")

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

def delete_yt_video(tok, vid_id):
    req = urllib.request.Request(
        f"https://www.googleapis.com/youtube/v3/videos?id={vid_id}", method="DELETE")
    req.add_header("Authorization", f"Bearer {tok}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="ignore")

def get_channel_videos(tok):
    """Busca todos os vídeos do canal via uploads playlist"""
    # Pegar o canal atual
    s, b, _ = http_json(
        "https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true",
        headers={"Authorization": f"Bearer {tok}"})
    if s != 200:
        log(f"  channels API {s}: {b[:100]}")
        return []
    data = json.loads(b)
    items = data.get("items", [])
    if not items: return []
    uploads_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    log(f"  uploads playlist: {uploads_id}")
    
    # Buscar todos os vídeos
    videos = []
    page_token = None
    while True:
        url = (f"https://www.googleapis.com/youtube/v3/playlistItems"
               f"?part=snippet,contentDetails&playlistId={uploads_id}&maxResults=50")
        if page_token: url += f"&pageToken={page_token}"
        s, b, _ = http_json(url, headers={"Authorization": f"Bearer {tok}"})
        if s != 200: break
        data = json.loads(b)
        for item in data.get("items", []):
            vid_id = item["contentDetails"]["videoId"]
            title  = item["snippet"]["title"]
            videos.append({"id": vid_id, "title": title})
        page_token = data.get("nextPageToken")
        if not page_token: break
    return videos

def get_videos_details(tok, video_ids):
    """Busca duração e status dos vídeos"""
    result = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        ids_str = ",".join(batch)
        url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails,snippet,status&id={ids_str}"
        s, b, _ = http_json(url, headers={"Authorization": f"Bearer {tok}"})
        if s != 200: continue
        for item in json.loads(b).get("items", []):
            dur_str = item.get("contentDetails",{}).get("duration","")
            m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', dur_str)
            dur_s = 0
            if m:
                dur_s = int(m.group(1) or 0)*3600 + int(m.group(2) or 0)*60 + int(m.group(3) or 0)
            result[item["id"]] = {
                "duration_s": dur_s,
                "title": item["snippet"]["title"],
                "upload_status": item["status"]["uploadStatus"],
            }
    return result

def ffprobe_audio_gap(mp4_url):
    """Retorna (ok, gap_info) — inconclusivo se download falha"""
    try:
        req = urllib.request.Request(mp4_url, headers={"User-Agent":"checker/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read(100 * 1024 * 1024)
    except Exception as e:
        return None, f"DOWNLOAD_FAIL: {e}"
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(data); path = tmp.name
    try:
        res = subprocess.run(
            ["ffprobe","-v","quiet","-print_format","json","-show_streams",path],
            capture_output=True, text=True, timeout=30)
        if res.returncode != 0:
            return None, "FFPROBE_ERROR"
        streams = json.loads(res.stdout).get("streams",[])
        vid_dur = aud_dur = None
        for s in streams:
            d = float(s.get("duration") or 0)
            if s["codec_type"] == "video" and d > 0: vid_dur = d
            elif s["codec_type"] == "audio" and d > 0: aud_dur = d
        if vid_dur is None:
            res2 = subprocess.run(
                ["ffprobe","-v","quiet","-print_format","json","-show_format",path],
                capture_output=True, text=True, timeout=30)
            if res2.returncode == 0:
                vid_dur = float(json.loads(res2.stdout).get("format",{}).get("duration",0)) or None
        if vid_dur is None:
            return None, "DURACAO_INDETERMINAVEL"
        if aud_dur is None:
            return True, f"vid={vid_dur:.1f}s (sem stream áudio separado — ok)"
        gap = vid_dur - aud_dur
        if gap > AUDIO_GAP_MAX:
            return False, f"AUDIO_TERMINA_ANTES: gap={gap:.1f}s (vid={vid_dur:.1f}s aud={aud_dur:.1f}s)"
        return True, f"vid={vid_dur:.1f}s aud={aud_dur:.1f}s gap={gap:.1f}s OK"
    except Exception as e:
        return None, f"FFPROBE_EXCEPTION: {e}"
    finally:
        try: os.unlink(path)
        except: pass

def cancel_upcoming_broadcasts(tok):
    """Deleta apenas broadcasts upcoming DUPLICADOS (mantém 1 eterno ativo)"""
    from datetime import datetime, timezone
    s, b, _ = http_json(
        "https://www.googleapis.com/youtube/v3/liveBroadcasts"
        "?part=id,snippet,status&broadcastStatus=upcoming&maxResults=50",
        headers={"Authorization": f"Bearer {tok}"})
    if s != 200:
        log(f"  broadcasts API {s}: {b[:100]}")
        return 0
    items = json.loads(b).get("items", [])
    log(f"  Broadcasts upcoming: {len(items)}")
    if len(items) <= 1:
        log("  ✅ 0 ou 1 upcoming — nada a deletar")
        return 0
    # Ordenar por scheduledStartTime — manter o MAIS RECENTE, deletar os outros
    def get_start(item):
        t = item["snippet"].get("scheduledStartTime","")
        try: return datetime.fromisoformat(t.replace("Z","+00:00"))
        except: return datetime.min.replace(tzinfo=timezone.utc)
    items_sorted = sorted(items, key=get_start, reverse=True)
    keep = items_sorted[0]
    to_del = items_sorted[1:]
    log(f"  Mantendo: {keep['snippet']['title'][:50]} | {keep['snippet'].get('scheduledStartTime','?')}")
    cancelled = 0
    for item in to_del:
        bid    = item["id"]
        btitle = item["snippet"]["title"][:50]
        req = urllib.request.Request(
            f"https://www.googleapis.com/youtube/v3/liveBroadcasts?id={bid}",
            method="DELETE")
        req.add_header("Authorization", f"Bearer {tok}")
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                log(f"  🗑  Duplicado deletado: {btitle} | HTTP {r.status}")
                cancelled += 1
        except urllib.error.HTTPError as e:
            log(f"  ❌ Erro ao deletar {bid}: {e.code}")
    return cancelled

def main():
    log("=" * 65)
    log("CLEAN PLAYLIST FINAL — Score≥95 + Áudio completo + Live sem upcoming")
    log("=" * 65)

    tok = get_yt_token()
    if not tok:
        log("ERRO: Token YouTube não obtido"); return

    # ── 1. Verificar e cancelar upcoming broadcasts ──────────────────
    log("\n[1] Verificando broadcasts upcoming...")
    n = cancel_upcoming_broadcasts(tok)
    log(f"  {n} upcoming cancelados")

    # ── 2. Listar todos os vídeos do canal ────────────────────────────
    log("\n[2] Listando vídeos do canal...")
    channel_videos = get_channel_videos(tok)
    log(f"  Total no canal: {len(channel_videos)}")
    if not channel_videos:
        log("  Canal vazio ou sem acesso"); return

    # Buscar detalhes (duração/status) em batch
    vid_ids = [v["id"] for v in channel_videos]
    details = get_videos_details(tok, vid_ids)
    log(f"  Detalhes obtidos: {len(details)}")

    # ── 3. Buscar scores do Supabase para cada vídeo ──────────────────
    log("\n[3] Cruzando com Supabase (scores e mp4_url)...")
    # Buscar todas as linhas com youtube_url preenchido
    sb_rows = sb_select("content_pipeline",
        "youtube_url=not.is.null"
        "&select=id,title,youtube_url,mp4_url,video_url,viral_score,quality_score_current,status"
        "&limit=500")
    # Indexar por video_id extraído da URL
    sb_by_vid = {}
    for row in sb_rows:
        url = row.get("youtube_url","") or ""
        m = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/))([A-Za-z0-9_-]{11})', url)
        if m: sb_by_vid[m.group(1)] = row

    # ── 4. Avaliar cada vídeo ─────────────────────────────────────────
    log("\n[4] Avaliando cada vídeo...")
    to_delete = []
    ok_count  = 0

    for vid in channel_videos:
        vid_id = vid["id"]
        info   = details.get(vid_id, {})
        dur_s  = info.get("duration_s", 0)
        yt_title = info.get("title", vid["title"])[:55]
        sb_row   = sb_by_vid.get(vid_id)

        # Score
        if sb_row:
            score = max(sb_row.get("viral_score") or 0,
                        sb_row.get("quality_score_current") or 0)
            mp4_url = sb_row.get("mp4_url") or sb_row.get("video_url")
        else:
            score   = 0
            mp4_url = None

        motivos = []

        # Score check
        if score > 0 and score < SCORE_MIN:
            motivos.append(f"SCORE_BAIXO:{score}")

        # Duração do YT: se for muito curta é incompleto
        if dur_s < 10 and dur_s > 0:
            motivos.append(f"DURACAO_YT_MUITO_CURTA:{dur_s}s")

        # Áudio check via MP4
        audio_ok = None
        audio_info = "sem_mp4"
        if mp4_url and not motivos:  # só verifica áudio se passou no score
            audio_ok, audio_info = ffprobe_audio_gap(mp4_url)
            if audio_ok is False:
                motivos.append(audio_info)
            elif audio_ok is None:
                log(f"  ⚠️  [{vid_id}] Áudio inconclusivo — não deletar: {audio_info}")

        if motivos:
            log(f"  ❌ [{vid_id}] {yt_title} | score={score} dur={dur_s}s | {' | '.join(motivos)}")
            to_delete.append((vid_id, sb_row, " | ".join(motivos)))
        else:
            log(f"  ✅ [{vid_id}] {yt_title} | score={score} dur={dur_s}s | {audio_info}")
            ok_count += 1

    log(f"\n[RESUMO] OK={ok_count} | Deletar={len(to_delete)}")

    # ── 5. Deletar os ruins ───────────────────────────────────────────
    deleted = errors = 0
    for vid_id, sb_row, motivo in to_delete:
        log(f"\n  🗑  {vid_id} — {motivo[:70]}")
        code, err = delete_yt_video(tok, vid_id)
        if code in (204, 200, 404):
            log(f"     ✅ HTTP {code}")
            deleted += 1
            if sb_row:
                sb_patch("content_pipeline", f"id=eq.{sb_row['id']}", {
                    "status": "deleted_bad_quality",
                    "error": f"DELETADO: {motivo[:400]}",
                    "youtube_url": None,
                })
        else:
            log(f"     ❌ {code}: {err[:80]}")
            errors += 1
        time.sleep(0.3)

    log(f"\n{'='*65}")
    log(f"CONCLUÍDO: {deleted} deletados | {errors} erros | {ok_count} aprovados no canal")

if __name__ == "__main__":
    main()
