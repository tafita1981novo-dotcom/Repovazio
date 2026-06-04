#!/usr/bin/env python3
"""
youtube_publisher_v6.py - Publica videos mp4_ready com score>=95 no YouTube
Usa OAuth com refresh token para obter access token automaticamente.
"""
import os, sys, json, re, time, pathlib, urllib.request, urllib.parse
from datetime import datetime

SBU = os.environ.get("SUPABASE_URL","")
SBK = os.environ.get("SUPABASE_SERVICE_KEY","")
YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
MAX = int(os.environ.get("MAX_VIDEOS","3"))
CHANNEL_ID = "UCSH63tBfY6wEIdkC4u4zKdg"  # @psidanicoelho

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERRO {m}", flush=True, file=sys.stderr)

def get_access_token():
    data = urllib.parse.urlencode({
        "client_id": YT_CLIENT_ID,
        "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read())
    return d.get("access_token","")

def sb(ep, params="", method="GET", data=None):
    url = f"{SBU}/rest/v1/{ep}?{params}"
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("apikey", SBK); req.add_header("Authorization", f"Bearer {SBK}")
    req.add_header("Content-Type","application/json"); req.add_header("Prefer","return=minimal")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()) if method=="GET" else {}
    except: return [] if method=="GET" else {}

def patch(id_, data):
    sb(f"content_pipeline", f"id=eq.{id_}", "PATCH", json.dumps(data).encode())

def baixar_video(url, out_path):
    """Baixa o MP4 do Supabase Storage"""
    log(f"  Baixando: {url[-50:]}")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    open(out_path,"wb").write(data)
    sz = len(data)//1024//1024
    log(f"  Download: {sz}MB")
    return sz > 0

def publicar_youtube(access_token, video_path, title, description, tags):
    """Upload do vídeo para o YouTube via API resumable"""
    # Metadata do video
    snippet = {
        "title": title[:100],
        "description": description[:5000],
        "tags": tags[:500] if isinstance(tags, list) else tags.split(",")[:10],
        "categoryId": "22",  # People & Blogs
        "defaultLanguage": "pt",
        "defaultAudioLanguage": "pt-BR"
    }
    status = {
        "privacyStatus": "public",
        "selfDeclaredMadeForKids": False,
        "madeForKids": False
    }
    body = json.dumps({"snippet": snippet, "status": status}).encode()

    # Iniciar upload resumavel
    file_size = pathlib.Path(video_path).stat().st_size
    init_url = ("https://www.googleapis.com/upload/youtube/v3/videos"
                "?uploadType=resumable&part=snippet,status")
    req = urllib.request.Request(init_url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type","application/json")
    req.add_header("X-Upload-Content-Type","video/mp4")
    req.add_header("X-Upload-Content-Length", str(file_size))

    with urllib.request.urlopen(req, timeout=30) as r:
        upload_url = r.headers.get("Location","")

    if not upload_url:
        raise Exception("Upload URL nao retornada!")

    log(f"  Upload URL obtida. Enviando {file_size//1024//1024}MB...")

    # Enviar o arquivo
    with open(video_path,"rb") as f:
        video_data = f.read()

    req2 = urllib.request.Request(upload_url, data=video_data, method="PUT")
    req2.add_header("Content-Type","video/mp4")
    req2.add_header("Content-Length", str(file_size))

    with urllib.request.urlopen(req2, timeout=600) as r:
        result = json.loads(r.read())

    return result.get("id","")

def gerar_description(row):
    title = row.get("title","")
    serie = row.get("series_slug","")
    
    desc = f"""Pesquisadora de comportamento humano Daniela Coelho explica:

{title}

Este video aborda os padroes psicologicos que a ciencia ja comprovou - mas que poucos profissionais explicam de forma clara e acessivel.

---
DANIELA COELHO pesquisa comportamento humano ha anos.
Aqui voce encontra conteudo baseado em estudos cientificos reais.

Inscreva-se para nao perder os proximos episodios.
"""
    return desc

def main():
    log("="*58)
    log("YOUTUBE PUBLISHER V6 — Publica videos virais >=95%")
    log(f"Canal: @psidanicoelho | Max por run: {MAX}")
    log("="*58)

    # Obter access token
    log("Obtendo access token...")
    access_token = get_access_token()
    if not access_token:
        err("Nao foi possivel obter access token!"); sys.exit(1)
    log(f"Token: {access_token[:20]}... OK")

    # Buscar videos prontos
    rows = sb("content_pipeline",
              "select=id,title,format,mp4_url,quality_score_current,youtube_title,"
              "pub_order,series_slug"
              "&status=eq.mp4_ready"
              "&quality_score_current=gte.95"
              "&mp4_url=not.is.null"
              "&order=pub_order.asc.nullslast,id.asc"
              f"&limit={MAX}")

    log(f"Videos para publicar: {len(rows)}")

    ok = 0
    for row in rows[:MAX]:
        vid_id = row["id"]
        title  = row.get("youtube_title") or row.get("title") or f"Video {vid_id}"
        mp4_url = row.get("mp4_url","")
        score   = row.get("quality_score_current", 0)

        log(f"\n  #{vid_id} | score={score} | {title[:50]}")

        # Baixar video
        local_path = f"/tmp/pub_{vid_id}.mp4"
        try:
            ok_dl = baixar_video(mp4_url, local_path)
            if not ok_dl: raise Exception("Download vazio")
        except Exception as e:
            err(f"Download falhou: {e}"); continue

        # Publicar no YouTube
        tags = ["psicologia","comportamento humano","saude mental","daniela coelho",
                "narcisismo","ansiedade","apego","trauma","burnout","neurociencia"]
        desc = gerar_description(row)

        try:
            yt_id = publicar_youtube(access_token, local_path, title, desc, tags)
            if yt_id:
                yt_url = f"https://youtube.com/watch?v={yt_id}"
                log(f"  PUBLICADO: {yt_url}")
                patch(vid_id, {
                    "status": "published",
                    "youtube_id": yt_id,
                    "youtube_url": yt_url
                })
                ok += 1
            else:
                err(f"Upload falhou para #{vid_id}")
        except Exception as e:
            err(f"Publicacao falhou: {e}")

        # Limpar arquivo local
        try: pathlib.Path(local_path).unlink()
        except: pass

        time.sleep(2)

    log(f"\n{'='*58}")
    log(f"PUBLICADOS: {ok}/{len(rows[:MAX])} videos no YouTube")

if __name__ == "__main__":
    main()
