#!/usr/bin/env python3
"""
auto_publisher.py — Publica automaticamente 1 vídeo por run no YouTube
Prioridade: viral_score DESC → shorts mp4_ready → séries organizadas
"""
import os, sys, json, urllib.request, urllib.parse, urllib.error, time, tempfile, pathlib

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
CLIENT_ID    = os.environ["YT_CLIENT_ID"]
CLIENT_SECRET= os.environ["YT_CLIENT_SECRET"]
REFRESH_TOKEN= os.environ["YT_REFRESH_TOKEN"]
SB_H = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"}

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def sb_get(table, qs=""):
    r = urllib.request.urlopen(
        urllib.request.Request(f"{SUPABASE_URL}/rest/v1/{table}?{qs}",
                               headers=SB_H), timeout=20)
    return json.loads(r.read())

def sb_patch(table, row_id, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{row_id}",
        data=body, method="PATCH",
        headers={**SB_H, "Prefer": "return=minimal"})
    try:
        urllib.request.urlopen(req, timeout=15)
        return True
    except Exception as e:
        log(f"PATCH error: {e}"); return False

def get_token():
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN, "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())["access_token"]

def download_mp4(url, dest):
    log(f"Baixando: {url[:70]}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        while chunk := r.read(1024*1024):
            f.write(chunk)
    size_mb = pathlib.Path(dest).stat().st_size / 1024 / 1024
    log(f"Download ok: {size_mb:.1f}MB")
    return size_mb

def get_or_create_playlist(token, name, desc, serie_slug):
    """Retorna playlist_id para a série, criando se necessário"""
    # Buscar playlists existentes
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/playlists?part=snippet&mine=true&maxResults=50")
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    for item in data.get("items", []):
        if serie_slug.lower() in item["snippet"]["title"].lower():
            return item["id"]
    # Criar nova playlist
    body = json.dumps({
        "snippet": {"title": name, "description": desc, "defaultLanguage": "pt"},
        "status": {"privacyStatus": "public"}
    }).encode()
    req2 = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/playlists?part=snippet,status",
        data=body)
    req2.add_header("Authorization", f"Bearer {token}")
    req2.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req2, timeout=15) as r:
        pl = json.loads(r.read())
        log(f"Playlist criada: {pl['id']} — {name}")
        return pl["id"]

def add_to_playlist(token, playlist_id, video_id):
    body = json.dumps({
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {"kind": "youtube#video", "videoId": video_id}
        }
    }).encode()
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet",
        data=body)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        urllib.request.urlopen(req, timeout=15)
        log(f"Adicionado à playlist {playlist_id}")
    except Exception as e:
        log(f"Playlist add warn: {e}")

def upload_video(token, mp4_path, title, description, tags, category_id="22"):
    """Upload multipart para YouTube"""
    size = pathlib.Path(mp4_path).stat().st_size
    metadata = json.dumps({
        "snippet": {
            "title": title[:100],
            "description": description[:4900],
            "tags": tags[:500].split(",") if isinstance(tags, str) else (tags or []),
            "categoryId": category_id,
            "defaultLanguage": "pt",
            "defaultAudioLanguage": "pt"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids": False
        }
    }).encode()

    boundary = b"--frontier"
    body = (b"--frontier\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
            + metadata + b"\r\n--frontier\r\nContent-Type: video/mp4\r\n\r\n")

    with open(mp4_path, "rb") as f:
        video_data = f.read()
    body = body + video_data + b"\r\n--frontier--"

    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=multipart&part=snippet,status",
        data=body)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "multipart/related; boundary=frontier")
    req.add_header("Content-Length", str(len(body)))

    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())

# SÉRIES CONFIGURADAS
SERIES_INFO = {
    "narcisismo":  ("🧠 Série: Narcisismo | Psicologia Doc",   "Série completa sobre narcisismo, manipulação e como se proteger. Pesquisa em comportamento humano."),
    "ansiedade":   ("😰 Série: Ansiedade | Psicologia Doc",    "Série sobre ansiedade, neurociência e como o cérebro responde ao medo. Baseado em pesquisas."),
    "trauma":      ("💔 Série: Trauma | Psicologia Doc",       "Série sobre trauma, cura e neuroplasticidade. Baseado em van der Kolk, Siegel e pesquisas."),
    "relacionamentos": ("❤️ Série: Relacionamentos | Psicologia Doc", "Série sobre apego, relacionamentos saudáveis e tóxicos. Baseado em Gottman e Ainsworth."),
    "cerebro":     ("🧬 Série: Neurociência | Psicologia Doc", "Série sobre como o cérebro funciona, neurociência aplicada ao comportamento humano."),
    "impostor":    ("🎭 Série: Síndrome do Impostor | Psicologia Doc", "Série sobre síndrome do impostor, perfeccionismo e autoestima."),
    "vicoemocional": ("🔗 Série: Vício Emocional | Psicologia Doc", "Série sobre dependência emocional, apego e como se libertar de padrões."),
}

DESC_PADRAO = """🖤 Pesquisa em comportamento humano | @psidanicoelho

🔔 Inscreva-se e ative o sininho para não perder nenhum episódio!

Baseado em pesquisas de Harvard, van der Kolk, Ainsworth, Gottman, Siegel/UCLA e Brown/U.Texas.

⚠️ Este conteúdo é informativo e educacional. Para suporte profissional, consulte um psicólogo.

#psicologia #comportamentohumano #saudemental #neurociencia #psidanicoelho"""

def main():
    log("=== AUTO PUBLISHER ===")
    token = get_token()
    log("Token OK")

    # Buscar próximo vídeo para publicar (viral_score DESC)
    videos = sb_get("content_pipeline",
        "status=eq.mp4_ready&select=id,topic,youtube_title,youtube_description,youtube_tags,mp4_url,video_url,series_slug,ep_number,viral_score,format"
        "&order=viral_score.desc.nullslast,id.asc&limit=1")

    if not videos:
        log("Nenhum vídeo mp4_ready encontrado")
        return 0

    v = videos[0]
    vid_id = v["id"]
    log(f"Publicando ID {vid_id}: {v.get('youtube_title','(sem título)')[:60]}")

    # Título e descrição
    title = v.get("youtube_title") or v.get("topic") or f"Psicologia Doc #{vid_id}"
    title = title.replace("...", "").strip()[:100]

    desc_custom = v.get("youtube_description") or ""
    desc = (desc_custom + "\n\n" + DESC_PADRAO).strip()[:4900]

    # Tags
    raw_tags = v.get("youtube_tags") or []
    if isinstance(raw_tags, str):
        try: raw_tags = json.loads(raw_tags)
        except: raw_tags = [raw_tags]
    default_tags = ["psicologia","comportamento humano","saúde mental","neurociência",
                    "psidanicoelho","autoconhecimento","ansiedade","trauma","relacionamentos"]
    all_tags = list(dict.fromkeys(raw_tags + default_tags))[:30]

    # Categoria: 22 = People & Blogs (melhor para psicologia/educação), 27 = Education
    cat = "27"  # Education — CPM alto

    # Download do MP4
    mp4_url = v.get("video_url") or v.get("mp4_url")
    if not mp4_url:
        log("Sem mp4_url — pulando")
        sb_patch("content_pipeline", vid_id, {"status": "publish_error", "error": "sem mp4_url"})
        return 1

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        size_mb = download_mp4(mp4_url, tmp_path)
        if size_mb < 0.1:
            raise Exception(f"Arquivo muito pequeno: {size_mb}MB")

        # Upload
        log("Enviando para YouTube...")
        result = upload_video(token, tmp_path, title, desc, all_tags, category_id=cat)

        yt_id = result.get("id")
        if not yt_id:
            raise Exception(f"Upload falhou: {result}")

        log(f"✅ Publicado: https://www.youtube.com/watch?v={yt_id}")

        # Adicionar à playlist da série se tiver
        serie = v.get("series_slug")
        if serie and serie in SERIES_INFO:
            sname, sdesc = SERIES_INFO[serie]
            pl_id = get_or_create_playlist(token, sname, sdesc, serie)
            add_to_playlist(token, pl_id, yt_id)

        # Atualizar Supabase
        sb_patch("content_pipeline", vid_id, {
            "status": "published",
            "youtube_id": yt_id,
            "youtube_url": f"https://www.youtube.com/watch?v={yt_id}",
            "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        log(f"✅ DB atualizado — ID {vid_id} → published")

    except Exception as e:
        log(f"❌ Erro: {e}")
        sb_patch("content_pipeline", vid_id, {"status": "publish_error", "error": str(e)[:200]})
        return 1
    finally:
        try: pathlib.Path(tmp_path).unlink()
        except: pass

    return 0

if __name__ == "__main__":
    sys.exit(main())
