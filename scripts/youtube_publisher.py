#!/usr/bin/env python3
"""
youtube_publisher.py — Publica vídeos do Supabase no @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ordem: #683 → #701 → #682 → #689 → #684 → #688 → sequência
Horário: 18h-20h BRT (21h-23h UTC)
Canal: UCSH63tBfY6wEIdkC4u4zKdg / @psidanicoelho / tafita81@gmail.com
"""
import os, requests, json, time, sys
from datetime import datetime, timezone, timedelta

SB_URL  = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY  = os.getenv("SUPABASE_SERVICE_KEY","")
YT_ID   = os.getenv("YT_CLIENT_ID","")
YT_SEC  = os.getenv("YT_CLIENT_SECRET","")
YT_REF  = os.getenv("YT_REFRESH_TOKEN","")
CHANNEL = os.getenv("YOUTUBE_CHANNEL_ID","UCSH63tBfY6wEIdkC4u4zKdg")
SBH     = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json"}

# Ordem de publicação definida
ORDEM_IDS = [683, 701, 682, 689, 684, 688, 685, 686, 687, 690, 691, 692, 693, 694, 695, 696, 700]

def refresh_token():
    if not all([YT_ID, YT_SEC, YT_REF]): return None
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id":YT_ID,"client_secret":YT_SEC,
        "refresh_token":YT_REF,"grant_type":"refresh_token"
    }, timeout=15)
    if r.status_code == 200:
        t = r.json().get("access_token")
        print(f"  Token OK: {t[:20]}...")
        return t
    print(f"  Token ERRO: {r.status_code} {r.text[:100]}")
    return None

def buscar_video(ep_id):
    r = requests.get(f"{SB_URL}/rest/v1/content_pipeline",
        params={"id":f"eq.{ep_id}","select":"*","limit":"1"},
        headers=SBH, timeout=10)
    rows = r.json()
    return rows[0] if rows else None

def download_mp4(url):
    print(f"  Baixando MP4: {url[:60]}...")
    r = requests.get(url, timeout=120, stream=True)
    path = f"/tmp/video_{int(time.time())}.mp4"
    with open(path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    size = os.path.getsize(path)
    print(f"  MP4 baixado: {size/1024/1024:.1f}MB → {path}")
    return path

def upload_youtube(token, video_path, title, description, tags, category="22"):
    """Upload resumável YouTube Data API v3"""
    meta = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": category,
            "defaultLanguage": "pt",
            "defaultAudioLanguage": "pt",
        },
        "status": {
            "privacyStatus": "public",
            "madeForKids": False,
            "selfDeclaredMadeForKids": False,
        }
    }

    # Iniciar upload resumável
    r = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos"
        "?uploadType=resumable&part=snippet,status",
        headers={"Authorization":f"Bearer {token}",
                 "Content-Type":"application/json",
                 "X-Upload-Content-Type":"video/mp4"},
        json=meta, timeout=30)

    if r.status_code != 200:
        print(f"  Upload init ERRO: {r.status_code} {r.text[:200]}")
        return None

    upload_url = r.headers["Location"]
    file_size  = os.path.getsize(video_path)

    # Enviar arquivo
    with open(video_path,"rb") as f:
        r2 = requests.put(upload_url,
            headers={"Content-Length":str(file_size),
                     "Content-Type":"video/mp4"},
            data=f, timeout=600)

    if r2.status_code in (200,201):
        vid = r2.json().get("id")
        print(f"  Upload OK: https://youtu.be/{vid}")
        return vid
    print(f"  Upload ERRO: {r2.status_code}")
    return None

def set_thumbnail(token, video_id, thumb_url):
    try:
        r = requests.get(thumb_url, timeout=30)
        r2 = requests.post(
            f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
            f"?videoId={video_id}&uploadType=media",
            headers={"Authorization":f"Bearer {token}","Content-Type":"image/jpeg"},
            data=r.content, timeout=60)
        ok = r2.status_code == 200
        print(f"  Thumbnail: {'✅' if ok else '❌'}")
        return ok
    except: return False

def marcar_publicado(ep_id, youtube_id, youtube_url):
    now = datetime.now(timezone.utc).isoformat()
    requests.patch(f"{SB_URL}/rest/v1/content_pipeline",
        params={"id":f"eq.{ep_id}"},
        headers={**SBH,"Prefer":"return=minimal"},
        json={"status":"published","youtube_id":youtube_id,
              "youtube_url":youtube_url,"published_at":now},
        timeout=10)

def hora_brt():
    return (datetime.now(timezone.utc) - timedelta(hours=3)).hour

def run():
    print("=== PUBLICADOR YOUTUBE — @psidanicoelho ===")
    print(f"  Canal: {CHANNEL}")
    print(f"  Ordem: {ORDEM_IDS}")
    print()

    if not all([YT_ID, YT_SEC, YT_REF]):
        print("  ERRO: Credenciais YouTube não configuradas")
        print("  Adicionar GitHub Secrets: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN")
        sys.exit(1)

    token = refresh_token()
    if not token:
        print("  ERRO: Token YouTube inválido")
        sys.exit(1)

    h = hora_brt()
    print(f"  Hora BRT: {h}h")
    if not (18 <= h <= 23):
        print("  Fora do horário de publicação (18h-23h BRT)")
        print("  Verificando: há vídeos prontos para publicar?")

    publicados = 0

    # Combina prioridade + todos mp4_ready não publicados
    r_mp4 = requests.get(f"{SB_URL}/rest/v1/content_pipeline",
        params={"status":"eq.mp4_ready","select":"id","limit":"20","order":"id.asc"},
        headers=SBH, timeout=10)
    extra_ids = [row["id"] for row in (r_mp4.json() if r_mp4.status_code==200 else [])
                 if row["id"] not in ORDEM_IDS]
    todos_ids = ORDEM_IDS + extra_ids
    print(f"  Fila: {len(todos_ids)} vídeos ({len(ORDEM_IDS)} prioridade + {len(extra_ids)} extra)")

    for ep_id in todos_ids:
        video = buscar_video(ep_id)
        if not video:
            print(f"  #{ep_id}: não encontrado no Supabase")
            continue

        status = video.get("status","")
        yt_id  = video.get("youtube_id") or video.get("youtube_video_id")

        if status == "published" and yt_id:
            print(f"  #{ep_id}: já publicado → https://youtu.be/{yt_id}")
            continue

        mp4 = video.get("video_url") or video.get("mp4_url")
        if not mp4:
            print(f"  #{ep_id}: sem MP4 — status={status}")
            continue

        title = video.get("youtube_title") or video.get("title","Vídeo Psicologia")
        desc  = video.get("youtube_description") or video.get("script","")[:2000]
        tags  = json.loads(video.get("youtube_tags","[]")) if video.get("youtube_tags") else []
        thumb = video.get("thumbnail_url","")

        print(f"\n  PUBLICANDO #{ep_id}: {title[:60]}")

        # Download
        try:
            path = download_mp4(mp4)
        except Exception as e:
            print(f"  Download ERRO: {e}")
            continue

        # Refresh token antes do upload
        token = refresh_token() or token

        # Upload
        vid_id = upload_youtube(token, path, title, desc, tags)
        if not vid_id:
            continue

        # Thumbnail
        if thumb:
            set_thumbnail(token, vid_id, thumb)

        # Marcar publicado
        yt_url = f"https://youtu.be/{vid_id}"
        marcar_publicado(ep_id, vid_id, yt_url)
        print(f"  ✅ PUBLICADO: {yt_url}")
        publicados += 1

        # Intervalo entre publicações (evitar ban)
        if publicados < len(ORDEM_IDS):
            print(f"  Aguardando 30s antes do próximo...")
            time.sleep(30)

    print(f"\n  Total publicados: {publicados}")

if __name__=="__main__": run()
