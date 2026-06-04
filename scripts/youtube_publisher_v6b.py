#!/usr/bin/env python3
"""
youtube_publisher_v6b.py - Publica videos virais >=95% no YouTube
Filtra automaticamente URLs acessiveis antes de publicar.
"""
import os, sys, json, re, time, pathlib, urllib.request, urllib.parse
from datetime import datetime

SBU = os.environ.get("SUPABASE_URL","")
SBK = os.environ.get("SUPABASE_SERVICE_KEY","")
YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
MAX = int(os.environ.get("MAX_VIDEOS","5"))
HORA_PUBLICACAO  = os.environ.get("HORA_PUBLICACAO","18:00")  # 15h BR = 18h UTC

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

def url_acessivel(url):
    """Verifica se a URL e acessivel e tem tamanho minimo"""
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=8) as r:
            sz = int(r.headers.get("Content-Length","0"))
            return sz > 500000, sz  # Minimo 500KB
    except:
        return False, 0

def baixar_video(url, out_path):
    """Baixa o MP4"""
    log(f"    Baixando: {url[-50:]}")
    req = urllib.request.Request(url)
    req.add_header("User-Agent","Mozilla/5.0")
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    open(out_path,"wb").write(data)
    sz_mb = len(data)/1024/1024
    log(f"    Download: {sz_mb:.1f}MB")
    return sz_mb > 0.1

def publicar_youtube(access_token, video_path, title, description, tags):
    """Upload resumivel para o YouTube"""
    snippet = {
        "title": title[:100],
        "description": description[:5000],
        "tags": tags[:30] if isinstance(tags, list) else [],
        "categoryId": "22",
        "defaultLanguage": "pt",
        "defaultAudioLanguage": "pt-BR"
    }
    status = {"privacyStatus":"public","selfDeclaredMadeForKids":False,"madeForKids":False}
    body = json.dumps({"snippet":snippet,"status":status}).encode()
    file_size = pathlib.Path(video_path).stat().st_size

    # Iniciar upload
    init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
    req = urllib.request.Request(init_url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type","application/json")
    req.add_header("X-Upload-Content-Type","video/mp4")
    req.add_header("X-Upload-Content-Length", str(file_size))
    with urllib.request.urlopen(req, timeout=30) as r:
        upload_url = r.headers.get("Location","")

    if not upload_url:
        raise Exception("Upload URL nao retornada")

    log(f"    Enviando {file_size/1024/1024:.1f}MB para YouTube...")

    with open(video_path,"rb") as f:
        video_data = f.read()

    req2 = urllib.request.Request(upload_url, data=video_data, method="PUT")
    req2.add_header("Content-Type","video/mp4")
    req2.add_header("Content-Length", str(file_size))
    with urllib.request.urlopen(req2, timeout=600) as r:
        result = json.loads(r.read())

    return result.get("id","")

TAGS_PADRAO = [
    "psicologia","comportamento humano","saude mental","daniela coelho",
    "narcisismo","ansiedade","apego ansioso","trauma","burnout","neurociencia",
    "autoconhecimento","relacionamento toxico","depressao","inteligencia emocional"
]

def gerar_descricao(row):
    title = row.get("title","")
    serie = row.get("series_slug","") or ""
    
    parte_serie = ""
    if serie:
        parte_serie = f"\n\nFaz parte da serie: #{serie.upper()}"
    
    return f"""Daniela Coelho, pesquisadora de comportamento humano, explica:

{title}

Conteudo baseado em estudos cientificos reais — traduzido de forma clara e acessivel.{parte_serie}

---
Inscreva-se para nao perder os proximos episodios.
Canal: @psidanicoelho

#psicologia #comportamentohumano #saudemental #danielacoelho #{serie if serie else 'neurociencia'}"""

def main():
    log("="*60)
    log("YOUTUBE PUBLISHER V6B — Videos virais >=95%")
    log(f"Max por run: {MAX} | Apenas URLs acessiveis")
    log("="*60)

    # Access token
    log("Obtendo access token do YouTube...")
    access_token = get_access_token()
    if not access_token: err("Sem access token!"); sys.exit(1)
    log(f"Token: {access_token[:20]}... OK")

    # Buscar videos mp4_ready com score >= 95
    rows = sb("content_pipeline",
              "select=id,title,format,mp4_url,quality_score_current,youtube_title,pub_order,series_slug"
              "&status=eq.mp4_ready"
              "&quality_score_current=gte.95"
              "&mp4_url=not.is.null"
              "&order=pub_order.asc.nullslast,id.asc"
              "&limit=20")

    log(f"Videos mp4_ready (score>=95): {len(rows)}")

    # Filtrar apenas URLs acessiveis
    publicaveis = []
    for row in rows:
        url = row.get("mp4_url","")
        acessivel, sz = url_acessivel(url)
        if acessivel:
            log(f"  ✅ #{row['id']} {row['title'][:40]} | {sz/1024/1024:.1f}MB")
            publicaveis.append((row, sz))
        else:
            log(f"  ❌ #{row['id']} URL inacessivel: {url[-30:]}")

    log(f"\nPublicaveis: {len(publicaveis)} | Publicando: {min(len(publicaveis),MAX)}")

    ok = 0
    for row, sz in publicaveis[:MAX]:
        vid_id = row["id"]
        title  = row.get("youtube_title") or row.get("title") or f"Video {vid_id}"
        url    = row["mp4_url"]
        score  = row.get("quality_score_current",0)

        log(f"\n  ==> #{vid_id} | score={score} | {title[:50]}")

        local = f"/tmp/pub_{vid_id}.mp4"
        try:
            if not baixar_video(url, local):
                err(f"Download vazio: #{vid_id}"); continue
        except Exception as e:
            err(f"Download falhou: #{vid_id} | {e}"); continue

        desc = gerar_descricao(row)
        try:
            yt_id = publicar_youtube(access_token, local, title, desc, TAGS_PADRAO)
            if yt_id:
                yt_url = f"https://youtube.com/watch?v={yt_id}"
                log(f"  PUBLICADO: {yt_url}")
                patch(vid_id, {"status":"published","youtube_id":yt_id,"youtube_url":yt_url})
                ok += 1
            else:
                err(f"Upload sem ID: #{vid_id}")
        except Exception as e:
            err(f"Publicacao falhou: #{vid_id} | {e}")

        try: pathlib.Path(local).unlink()
        except: pass
        time.sleep(3)

    log(f"\n{'='*60}")
    log(f"RESULTADO: {ok}/{min(len(publicaveis),MAX)} publicados com sucesso")

if __name__ == "__main__":
    main()
