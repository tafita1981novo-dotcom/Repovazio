#!/usr/bin/env python3
"""
delete_bad_videos.py — Apaga do YouTube todos os vídeos fora dos critérios de qualidade

CRITÉRIOS:
- Shorts: duração obrigatória ENTRE 50s e 58s. Fora disso → deletar.
- Longs (playlists): duração mínima de 240s (4 min). Abaixo → deletar.
- Qualquer vídeo com duração 0 ou indefinida → deletar.

Execução: apaga do YouTube + marca status='deleted_bad_duration' no Supabase.
"""
import os, json, re, time, urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone

SBU = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
H_SB = {"apikey": SBK, "Authorization": f"Bearer {SBK}"}
H_SB_J = {**H_SB, "Content-Type": "application/json"}

SHORT_MIN = 50
SHORT_MAX = 58
LONG_MIN  = 240  # 4 minutos mínimo para longs

def log(*a): print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)

def sb_select(table, q):
    s, b, _ = http_json(f"{SBU}/rest/v1/{table}?{q}", headers=H_SB)
    if s != 200: raise RuntimeError(f"select {table} {s}: {b[:200]}")
    return json.loads(b)

def sb_patch(table, q, payload):
    s, b, _ = http_json(f"{SBU}/rest/v1/{table}?{q}", method="PATCH",
                       body=payload, headers=H_SB_J)
    if s not in (200, 204): log(f"  WARN patch {table} {s}: {b[:200]}")

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

def get_yt_token():
    keys = ["secret:YT_CLIENT_ID", "secret:YT_CLIENT_SECRET", "secret:YT_REFRESH_TOKEN"]
    q = "cache_key=in.(" + ",".join(urllib.parse.quote(k) for k in keys) + ")&select=cache_key,value"
    s, b, _ = http_json(f"{SBU}/rest/v1/ia_cache?{q}", headers=H_SB)
    creds = {}
    for row in json.loads(b):
        k = row["cache_key"].replace("secret:YT_", "")
        if row.get("value"): creds[k] = row["value"].strip()
    if not all(creds.get(k) for k in ["CLIENT_ID","CLIENT_SECRET","REFRESH_TOKEN"]):
        return None
    body = urllib.parse.urlencode({
        "client_id": creds["CLIENT_ID"], "client_secret": creds["CLIENT_SECRET"],
        "refresh_token": creds["REFRESH_TOKEN"], "grant_type": "refresh_token",
    }).encode()
    s, raw, _ = http_json("https://oauth2.googleapis.com/token", method="POST",
        body=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if s != 200: return None
    return json.loads(raw)["access_token"]

def parse_iso8601_duration(dur_str):
    """Converte PT1M30S → segundos"""
    if not dur_str: return 0
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', dur_str)
    if not m: return 0
    h = int(m.group(1) or 0)
    mn = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    return h*3600 + mn*60 + s

def get_yt_video_details(tok, video_ids):
    """Busca detalhes de até 50 vídeos por chamada"""
    if not video_ids: return {}
    ids_str = ",".join(video_ids[:50])
    url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails,snippet,status&id={ids_str}"
    s, b, _ = http_json(url, headers={"Authorization": f"Bearer {tok}"})
    if s != 200:
        log(f"  YT videos API {s}: {b[:200]}")
        return {}
    data = json.loads(b)
    result = {}
    for item in data.get("items", []):
        vid_id = item["id"]
        dur_str = item.get("contentDetails", {}).get("duration", "")
        duration_s = parse_iso8601_duration(dur_str)
        title = item.get("snippet", {}).get("title", "")
        status = item.get("status", {}).get("uploadStatus", "")
        result[vid_id] = {"duration_s": duration_s, "title": title, "status": status}
    return result

def delete_yt_video(tok, video_id):
    """Deleta um vídeo do YouTube via API"""
    url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}"
    req = urllib.request.Request(url, method="DELETE")
    req.add_header("Authorization", f"Bearer {tok}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors='ignore')
        return e.code, err

def is_short(row):
    """Detecta se é um short baseado em campos do pipeline"""
    fmt = row.get("format", "")
    target = row.get("target_platform", "")
    return fmt == "short" or "short" in target.lower()

def extract_video_id(url_str):
    """Extrai o video_id de uma URL do YouTube"""
    if not url_str: return None
    m = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/))([A-Za-z0-9_-]{11})', url_str)
    return m.group(1) if m else None

def main():
    log("=" * 60)
    log("DELETE BAD VIDEOS — Limpeza de vídeos com duração errada")
    log("=" * 60)

    tok = get_yt_token()
    if not tok:
        log("ERRO: Não foi possível obter token YouTube")
        return

    # Buscar todos os vídeos publicados com URL do YouTube
    rows = sb_select("content_pipeline",
        "status=in.(published,mp4_ready)&youtube_url=not.is.null"
        "&select=id,title,format,target_platform,youtube_url,youtube_id,youtube_long_id,youtube_video_id,duracao_min"
        "&order=id.asc&limit=200")

    log(f"Vídeos publicados encontrados: {len(rows)}")

    # Coletar video IDs únicos
    video_map = {}  # video_id → row(s)
    for row in rows:
        urls = [
            row.get("youtube_url"),
            row.get("youtube_id"),
            row.get("youtube_long_id"),
            row.get("youtube_video_id"),
        ]
        for url in urls:
            if not url: continue
            vid_id = extract_video_id(url) or (url if len(url) == 11 else None)
            if vid_id:
                if vid_id not in video_map:
                    video_map[vid_id] = []
                video_map[vid_id].append(row)

    log(f"Video IDs únicos para verificar: {len(video_map)}")

    if not video_map:
        log("Nenhum video ID encontrado.")
        return

    # Buscar detalhes em batches de 50
    all_ids = list(video_map.keys())
    details = {}
    for i in range(0, len(all_ids), 50):
        batch = all_ids[i:i+50]
        batch_details = get_yt_video_details(tok, batch)
        details.update(batch_details)
        log(f"  Batch {i//50+1}: {len(batch_details)}/{len(batch)} encontrados na API")
        time.sleep(0.5)

    # Analisar e deletar os ruins
    to_delete = []
    ok_count = 0

    for vid_id, vid_rows in video_map.items():
        row = vid_rows[0]
        title = row.get("title", "?")[:60]
        short = is_short(row)

        if vid_id not in details:
            log(f"  ⚠️  {vid_id} — não encontrado na API (já deletado ou privado)")
            continue

        info = details[vid_id]
        dur = info["duration_s"]
        status = info["status"]
        yt_title = info["title"][:50]

        if status not in ("processed", "uploaded", ""):
            log(f"  ⚠️  {vid_id} — status={status} (upload incompleto)")
            to_delete.append((vid_id, vid_rows, f"upload_status={status}"))
            continue

        if dur == 0:
            log(f"  ❌ {vid_id} [{yt_title}] — duração=0s → DELETAR")
            to_delete.append((vid_id, vid_rows, "duracao_zero"))
            continue

        if short:
            if SHORT_MIN <= dur <= SHORT_MAX:
                log(f"  ✅ SHORT {vid_id} [{yt_title}] — {dur}s (OK: {SHORT_MIN}-{SHORT_MAX}s)")
                ok_count += 1
            else:
                log(f"  ❌ SHORT {vid_id} [{yt_title}] — {dur}s FORA do range ({SHORT_MIN}-{SHORT_MAX}s) → DELETAR")
                to_delete.append((vid_id, vid_rows, f"short_duracao_invalida_{dur}s"))
        else:
            if dur >= LONG_MIN:
                log(f"  ✅ LONG {vid_id} [{yt_title}] — {dur}s ({dur//60}min) OK")
                ok_count += 1
            else:
                log(f"  ❌ LONG {vid_id} [{yt_title}] — {dur}s ({dur//60}min) INCOMPLETO (min={LONG_MIN}s) → DELETAR")
                to_delete.append((vid_id, vid_rows, f"long_incompleto_{dur}s"))

    log(f"\n─── RESUMO ───")
    log(f"OK: {ok_count} | Para deletar: {len(to_delete)}")

    if not to_delete:
        log("Nada a deletar.")
        return

    # Deletar do YouTube e marcar no Supabase
    deleted = 0
    errors = 0
    for vid_id, vid_rows, motivo in to_delete:
        log(f"\n  🗑  Deletando {vid_id} — motivo: {motivo}")
        code, err = delete_yt_video(tok, vid_id)
        if code in (204, 200, 404):
            log(f"     ✅ Deletado (HTTP {code})")
            deleted += 1
            # Marcar no Supabase
            for row in vid_rows:
                sb_patch("content_pipeline", f"id=eq.{row['id']}", {
                    "status": "deleted_bad_duration",
                    "error": f"DELETADO: {motivo}",
                    "youtube_url": None,
                })
        else:
            log(f"     ❌ Erro HTTP {code}: {err[:100]}")
            errors += 1
        time.sleep(0.3)

    log(f"\n=== CONCLUÍDO: {deleted} deletados | {errors} erros ===")
    log(f"Total OK no canal: {ok_count}")

if __name__ == "__main__":
    main()
