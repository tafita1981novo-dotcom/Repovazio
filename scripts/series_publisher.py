#!/usr/bin/env python3
"""
📺 Series Publisher v2 — Publica na ordem correta de pub_order
Colunas reais: pub_order, series_slug, ep_number, youtube_title, youtube_description
"""
import os, json, time, urllib.request, urllib.parse, tempfile, pathlib
from datetime import datetime, timezone

SBU = os.getenv("SUPABASE_URL", "")
SBK = os.getenv("SUPABASE_SERVICE_KEY", "")

REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN", "")
CLIENT_ID     = os.getenv("YT_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET", "")

# Playlists por series_slug
PLAYLIST_MAP = {
    "narcisismo":    "PLi1KkHerdzM3nGVg5hoJW8hguE0RLTe8Z",
    "vicoemocional": "PLi1KkHerdzM3vi_u4XWHeDjMw777_QrTv",
    "ansiedade":     "PLi1KkHerdzM1yiy5qHUYVPALpCWCDmnmg",
    "depressao":     "PLi1KkHerdzM2IoxqPNTqGVH-Ax4ldgGzA",
    "cerebro":       "PLi1KkHerdzM3vi_u4XWHeDjMw777_QrTv",
}

MAX_PER_RUN = int(os.getenv("MAX_PER_RUN", "2"))

def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def get_token():
    body = urllib.parse.urlencode({
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN, "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read()).get("access_token", "")

def sb_get(endpoint, params=""):
    req = urllib.request.Request(f"{SBU}/rest/v1/{endpoint}?{params}",
        headers={"apikey": SBK, "Authorization": f"Bearer {SBK}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

def sb_patch(table, data, vid_id):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{SBU}/rest/v1/{table}?id=eq.{vid_id}", data=body, method="PATCH",
        headers={"apikey": SBK, "Authorization": f"Bearer {SBK}",
                 "Content-Type": "application/json", "Prefer": "return=minimal"})
    with urllib.request.urlopen(req, timeout=15): pass

def yt(endpoint, data=None, method="GET", params="", token=""):
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}"
    if params: url += f"?{params}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data: req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def publish_video(video, token):
    vid_id  = video["id"]
    mp4_url = video.get("mp4_url", "")
    title   = (video.get("youtube_title") or video.get("title", ""))[:100]
    desc    = video.get("youtube_description", "")
    tags    = video.get("youtube_tags") or []
    slug    = video.get("series_slug", "")
    ep_num  = video.get("ep_number", 0)
    pub_ord = video.get("pub_order", 999)
    pinned  = video.get("pinned_comment", "")

    if not mp4_url:
        log(f"  ❌ ID {vid_id}: sem mp4_url")
        return None

    # Descrição completa com CTAs
    full_desc = f"""{desc}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 Daniela Coelho — Pesquisadora de Comportamento Humano
📺 Novo vídeo toda semana @psidanicoelho

📚 Baseado em pesquisas reais:
Harvard Medical School · van der Kolk · Gottman Institute

#psicologia #comportamentohumano #saudemental"""

    if slug:
        full_desc = f"📚 Série: {slug.title()}" + (f" · Ep. {ep_num}\n\n" if ep_num else "\n\n") + full_desc

    metadata = {
        "snippet": {
            "title": title,
            "description": full_desc[:4900],
            "tags": (tags if isinstance(tags, list) else [])[:20],
            "categoryId": "26",
            "defaultLanguage": "pt",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }

    # Download do MP4
    log(f"  ⬇ Baixando {mp4_url[-50:]}")
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    req_dl = urllib.request.Request(mp4_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req_dl, timeout=120) as r:
        open(tmp_path, "wb").write(r.read())

    size = pathlib.Path(tmp_path).stat().st_size
    log(f"  📦 {size//1024//1024}MB — iniciando upload resumable")

    # Iniciar upload resumable
    meta_body = json.dumps(metadata).encode()
    init_req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=meta_body, method="POST")
    init_req.add_header("Authorization", f"Bearer {token}")
    init_req.add_header("Content-Type", "application/json")
    init_req.add_header("X-Upload-Content-Type", "video/mp4")
    init_req.add_header("X-Upload-Content-Length", str(size))

    with urllib.request.urlopen(init_req, timeout=30) as r:
        upload_url = r.headers.get("Location", "")

    if not upload_url:
        log("  ❌ Sem URL de upload")
        return None

    # Upload do arquivo
    log(f"  ⬆ Enviando para YouTube...")
    video_data = open(tmp_path, "rb").read()
    up_req = urllib.request.Request(upload_url, data=video_data, method="PUT")
    up_req.add_header("Content-Type", "video/mp4")
    up_req.add_header("Content-Length", str(size))

    with urllib.request.urlopen(up_req, timeout=300) as r:
        result = json.loads(r.read())

    pathlib.Path(tmp_path).unlink(missing_ok=True)
    yt_id  = result.get("id", "")
    yt_url = f"https://www.youtube.com/watch?v={yt_id}" if yt_id else ""

    if yt_url:
        log(f"  ✅ Publicado: {yt_url}")

        # Comentar pinado
        if pinned:
            try:
                yt("commentThreads", data={
                    "snippet": {
                        "videoId": yt_id,
                        "topLevelComment": {"snippet": {"textOriginal": pinned[:2000]}}
                    }
                }, method="POST", params="part=snippet", token=token)
                log("  📌 Comentário pinado adicionado")
            except: pass

        # Adicionar à playlist
        if slug in PLAYLIST_MAP:
            try:
                yt("playlistItems", data={
                    "snippet": {"playlistId": PLAYLIST_MAP[slug],
                                "resourceId": {"kind": "youtube#video", "videoId": yt_id}}
                }, method="POST", params="part=snippet", token=token)
                log(f"  📂 Adicionado à playlist: {slug}")
            except: pass

        # Atualizar Supabase
        sb_patch("content_pipeline", {
            "status": "published",
            "youtube_url": yt_url,
            "youtube_id": yt_id,
            "published_at": datetime.now(timezone.utc).isoformat()
        }, vid_id)

    return yt_url

def check_quota():
    """Retorna quota usada hoje"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = sb_get("ia_cache", f"cache_key=eq.quota:yt:{today}&select=value")
    return int(rows[0]["value"]) if rows else 0

def add_quota(units):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    current = check_quota()
    body = json.dumps({"cache_key": f"quota:yt:{today}", "value": str(current + units),
                       "expires_at": "2030-01-01T00:00:00Z"}).encode()
    req = urllib.request.Request(f"{SBU}/rest/v1/ia_cache", data=body, method="POST",
        headers={"apikey": SBK, "Authorization": f"Bearer {SBK}",
                 "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
    with urllib.request.urlopen(req, timeout=10): pass

def main():
    log("=" * 50)
    log("📺 Series Publisher v2 — @psidanicoelho")
    log("=" * 50)

    if not all([SBU, SBK, REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET]):
        log("⚠️  Configurar variáveis de ambiente primeiro")
        return

    quota = check_quota()
    log(f"Quota hoje: {quota}/9500 units")

    if quota >= 9000:
        log("⚠️  Quota esgotada — aguardando reset às 00h UTC")
        return

    token = get_token()
    if not token:
        log("❌ Falha ao obter token OAuth")
        return

    # Buscar próximos vídeos por pub_order
    videos = sb_get("content_pipeline",
        "status=eq.mp4_ready&format=eq.short"
        "&select=id,pub_order,title,youtube_title,youtube_description,youtube_tags,"
        "series_slug,ep_number,mp4_url,pinned_comment,viral_score"
        "&order=pub_order.asc.nullslast,id.asc"
        f"&limit={MAX_PER_RUN}")

    if not videos:
        log("Nenhum vídeo pronto para publicar")
        return

    log(f"{len(videos)} vídeos na fila")
    success = 0

    for v in videos:
        if quota + 1600 > 9500:
            log("⚠️  Cota insuficiente para mais uploads")
            break
        log(f"\n[#{v['pub_order'] or '?'}] {v['title'][:55]}")
        log(f"  Série: {v.get('series_slug','?')} | Ep:{v.get('ep_number','?')} | Score:{v.get('viral_score','?')}")

        url = publish_video(v, token)
        if url:
            add_quota(1600)
            quota += 1600
            success += 1
        time.sleep(10)

    log(f"\n✅ {success}/{len(videos)} publicados | quota restante: {9500-quota}")

if __name__ == "__main__":
    main()
