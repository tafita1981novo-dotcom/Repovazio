#!/usr/bin/env python3
"""
📺 Series Publisher — Publicação na ordem correta de séries
════════════════════════════════════════════════════════════
Lê as séries do Supabase e publica vídeos em ordem crescente de episódio.
Auto-adiciona às playlists corretas por série.
"""
import os, json, time, urllib.request, urllib.parse
from datetime import datetime, timezone

# Config
SBU = os.getenv("SUPABASE_URL", "")
SBK = os.getenv("SUPABASE_SERVICE_KEY", "")

# IDs das playlists criadas
PLAYLIST_MAP = {
    "narcisismo":   os.getenv("PL_NARCISISMO", "PLi1KkHerdzM3nGVg5hoJW8hguE0RLTe8Z"),
    "apego":        os.getenv("PL_APEGO",      "PLi1KkHerdzM3vi_u4XWHeDjMw777_QrTv"),
    "ansiedade":    os.getenv("PL_ANSIEDADE",  "PLi1KkHerdzM1yiy5qHUYVPALpCWCDmnmg"),
    "burnout":      os.getenv("PL_BURNOUT",    "PLi1KkHerdzM2IoxqPNTqGVH-Ax4ldgGzA"),
    "lives":        os.getenv("PL_LIVES",      "PLi1KkHerdzM0G0nXoN7gUvtJMM4WgXoFO"),
}

# OAuth
REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN", "")
CLIENT_ID     = os.getenv("YT_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET", "")

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

def sb_update(table, data, match):
    q = "&".join(f"{k}=eq.{v}" for k,v in match.items())
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{SBU}/rest/v1/{table}?{q}", data=body, method="PATCH",
        headers={"apikey": SBK, "Authorization": f"Bearer {SBK}",
                 "Content-Type": "application/json", "Prefer": "return=minimal"})
    with urllib.request.urlopen(req, timeout=15): pass

def yt_api(endpoint, data=None, method="GET", params="", token=""):
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}"
    if params: url += f"?{params}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data: req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def detect_playlist(title, serie=""):
    """Detecta playlist baseado no título/série"""
    t = (title + " " + serie).lower()
    if any(w in t for w in ["narcis", "narc"]):             return "narcisismo"
    if any(w in t for w in ["apego", "relacionamento"]):    return "apego"
    if any(w in t for w in ["ansied", "ansioso", "panico"]): return "ansiedade"
    if any(w in t for w in ["burnout", "esgot", "fadiga"]): return "burnout"
    if any(w in t for w in ["live", "ao vivo", "debate"]):  return "lives"
    return None

def upload_youtube(video, token):
    """Upload de vídeo para YouTube com metadata de série"""
    mp4_url = video.get("mp4_url", "")
    if not mp4_url:
        print(f"  Sem mp4_url para ID {video['id']}")
        return None
    
    title       = video.get("title", "")
    description = video.get("description", "")
    tags        = video.get("tags", "").split(",") if video.get("tags") else []
    serie       = video.get("serie", "")
    ep_num      = video.get("episode_number", 0)
    
    # Montar título com série se houver
    full_title = title
    if serie and ep_num:
        full_title = f"S{ep_num:02d} | {title}"[:100]
    
    # Descrição completa
    full_desc = f"""{description}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 Daniela Coelho — Pesquisadora de Comportamento Humano
📺 @psidanicoelho

Este conteúdo é baseado em pesquisas científicas.
Fontes: Harvard Medical School, van der Kolk, Gottman Institute, UCLA

#psicologia #comportamentohumano #saudemental"""

    if serie:
        full_desc = f"📚 Série: {serie}\n" + (f"🎯 Episódio {ep_num}\n\n" if ep_num else "\n") + full_desc
    
    # Verificar cota antes de upload
    quota_ok = True  # simplificado
    
    # RESUMABLE UPLOAD
    print(f"  Upload: {full_title[:50]}...")
    
    # 1. Iniciar upload resumable
    metadata = {
        "snippet": {
            "title": full_title,
            "description": full_desc,
            "tags": tags[:20],
            "categoryId": "26",  # How-to & Style → mais amplo para psicologia
            "defaultLanguage": "pt",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    # Download do vídeo do Supabase Storage para upload ao YT
    import tempfile, pathlib
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name
    
    print(f"    Baixando vídeo ({mp4_url[-40:]})...")
    req_dl = urllib.request.Request(mp4_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req_dl, timeout=120) as r:
        open(tmp_path, "wb").write(r.read())
    
    size = pathlib.Path(tmp_path).stat().st_size
    print(f"    {size//1024//1024}MB baixados")
    
    # Iniciar upload resumable
    meta_body = json.dumps(metadata).encode()
    init_req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=meta_body, method="POST"
    )
    init_req.add_header("Authorization", f"Bearer {token}")
    init_req.add_header("Content-Type", "application/json")
    init_req.add_header("X-Upload-Content-Type", "video/mp4")
    init_req.add_header("X-Upload-Content-Length", str(size))
    
    with urllib.request.urlopen(init_req, timeout=30) as r:
        upload_url = r.headers.get("Location", "")
    
    if not upload_url:
        print("    Sem URL de upload!")
        return None
    
    # Upload do arquivo
    print(f"    Enviando {size//1024//1024}MB para YouTube...")
    video_data = open(tmp_path, "rb").read()
    up_req = urllib.request.Request(upload_url, data=video_data, method="PUT")
    up_req.add_header("Content-Type", "video/mp4")
    up_req.add_header("Content-Length", str(size))
    
    with urllib.request.urlopen(up_req, timeout=300) as r:
        result = json.loads(r.read())
    
    pathlib.Path(tmp_path).unlink(missing_ok=True)
    video_id = result.get("id", "")
    
    if video_id:
        yt_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"    ✅ Publicado: {yt_url}")
        
        # Adicionar à playlist correta
        pl_key = detect_playlist(title, serie)
        if pl_key and pl_key in PLAYLIST_MAP:
            try:
                yt_api("playlistItems", data={
                    "snippet": {
                        "playlistId": PLAYLIST_MAP[pl_key],
                        "resourceId": {"kind": "youtube#video", "videoId": video_id}
                    }
                }, method="POST", params="part=snippet", token=token)
                print(f"    + Adicionado à playlist: {pl_key}")
            except: pass
        
        return yt_url
    
    return None

def main():
    print("=" * 60)
    print("📺 Series Publisher — psicologia.doc")
    print("=" * 60)
    
    if not all([SBU, SBK, REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET]):
        print("⚠️ Credenciais não configuradas")
        return
    
    # Obter token
    token = get_token()
    if not token:
        print("❌ Token inválido")
        return
    
    # Verificar cota
    import datetime as dt
    today = dt.date.today().isoformat()
    quota_data = sb_get("ia_cache", f"cache_key=eq.quota:yt:{today}&select=value")
    quota = int(quota_data[0]["value"]) if quota_data else 0
    print(f"Quota hoje: {quota}/9500 units")
    
    if quota >= 9400:
        print("⚠️ Quota quase esgotada — aguardando reset")
        return
    
    # Buscar vídeos prontos, ordenados por série e episódio
    videos = sb_get("content_pipeline",
        "status=eq.mp4_ready&select=id,title,description,tags,serie,episode_number,format,mp4_url"
        "&order=serie.asc,episode_number.asc,id.asc&limit=2")
    
    print(f"{len(videos)} vídeos prontos para publicar")
    
    success = 0
    for video in videos:
        vid_id = video["id"]
        print(f"\n[{vid_id}] {video['title'][:55]}")
        print(f"  Série: {video.get('serie','?')} Ep:{video.get('episode_number','?')} Formato:{video.get('format','?')}")
        
        # Custo: 1600 units por upload
        if quota + 1600 > 9500:
            print("  ⚠️ Cota insuficiente para este vídeo")
            break
        
        yt_url = upload_youtube(video, token)
        if yt_url:
            sb_update("content_pipeline", {
                "status": "published",
                "youtube_url": yt_url,
                "published_at": datetime.now(timezone.utc).isoformat()
            }, {"id": vid_id})
            quota += 1600
            success += 1
            # Salvar quota atualizada
            body = json.dumps({"cache_key": f"quota:yt:{today}", "value": str(quota),
                              "expires_at": "2030-01-01T00:00:00Z"}).encode()
            req = urllib.request.Request(f"{SBU}/rest/v1/ia_cache", data=body, method="POST",
                headers={"apikey": SBK, "Authorization": f"Bearer {SBK}",
                         "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
            with urllib.request.urlopen(req, timeout=10): pass
        
        time.sleep(5)  # Respeitar rate limits
    
    print(f"\n✅ {success} vídeos publicados em ordem de série")

if __name__ == "__main__":
    main()
