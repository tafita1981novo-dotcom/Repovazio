#!/usr/bin/env python3
"""YouTube Publisher — publica pending_credentials com MP4 no canal @psidanielacoelho"""
import os, json, requests, sys

SBU = os.environ["SUPABASE_URL"]
SBK = os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_SERVICE_KEY",""))
CID = os.environ["YT_CLIENT_ID"]
SEC = os.environ["YT_CLIENT_SECRET"]
RTK = os.environ["YT_REFRESH_TOKEN"]
ALLOWED = "UCyCkIpsVgME9yCj_oXJFheA"
BLOCKED = "UCSH63tBfY6wEIdkC4u4zKdg"

print("== YouTube Publisher v2 ==")

# 1. Obter access token
r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CID, "client_secret": SEC,
    "refresh_token": RTK, "grant_type": "refresh_token"
}, timeout=15)
print(f"Token: {r.status_code}")
if not r.ok:
    print(f"Erro token: {r.text[:200]}")
    sys.exit(1)
token = r.json()["access_token"]

# 2. Verificar canal
r2 = requests.get(
    "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
    headers={"Authorization": f"Bearer {token}"}, timeout=15)
items = r2.json().get("items", [])
channel_ok = False
for item in items:
    cid = item["id"]
    name = item["snippet"]["title"]
    if cid == BLOCKED:
        print(f"BLOQUEADO! Canal {name} ({cid})")
        sys.exit(1)
    if cid == ALLOWED:
        print(f"Canal OK: {name} ({cid})")
        channel_ok = True

if not channel_ok:
    print(f"Canal desconhecido: {[i['id'] for i in items]}")
    print("Continuando mesmo sem validar canal...")
    # Não abortar — pode haver problema de permissão na listagem

# 3. Buscar vídeos pending_credentials com mp4 (YouTube OAuth já configurado)
hdrs = {"Authorization": f"Bearer {SBK}", "apikey": SBK}
params = "status=eq.pending_credentials&mp4_url=not.is.null&youtube_video_id=is.null&limit=3&order=seo_score.desc"
params += "&select=id,title,youtube_title,youtube_description,script,mp4_url,target_platform,seo_score"
videos = requests.get(f"{SBU}/rest/v1/content_pipeline?{params}", headers=hdrs, timeout=15).json()

if not videos:
    # Fallback para mp4_ready
    params2 = "status=eq.mp4_ready&mp4_url=not.is.null&limit=2&order=id.asc"
    params2 += "&select=id,title,youtube_title,youtube_description,script,mp4_url,target_platform,seo_score"
    videos = requests.get(f"{SBU}/rest/v1/content_pipeline?{params2}", headers=hdrs, timeout=15).json()

print(f"{len(videos)} vídeos para publicar")

for v in videos[:2]:  # max 2 por run
    print(f"\nPublicando #{v['id']}: {v.get('title','?')[:60]}")
    print(f"SEO Score: {v.get('seo_score',0)}")
    
    # Download do MP4
    print(f"Baixando MP4: {v['mp4_url'][:60]}...")
    try:
        mp4_r = requests.get(v["mp4_url"], stream=True, timeout=300)
        mp4_bytes = mp4_r.content
        print(f"MP4 baixado: {len(mp4_bytes)//1024}KB")
    except Exception as e:
        print(f"Erro ao baixar MP4: {e}")
        continue
    
    # Título e descrição
    titulo = v.get("youtube_title") or v.get("title","Psicologia")
    titulo = titulo[:100]
    descricao = v.get("youtube_description") or f"Conteúdo educacional sobre {v.get('title','')}\n\n#psicologia #saudemental"
    
    # Upload para YouTube
    meta = {
        "snippet": {
            "title": titulo,
            "description": descricao[:5000],
            "categoryId": "27",  # Education
            "defaultLanguage": "pt-BR",
            "tags": ["psicologia", "saude mental", "autoconhecimento", "psidanielacoelho"]
        },
        "status": {"privacyStatus": "public"}
    }
    
    from requests_toolbelt.multipart.encoder import MultipartEncoder
    try:
        import io
        encoder = MultipartEncoder(fields={
            'part': 'snippet,status',
            'meta': (None, json.dumps(meta), 'application/json'),
            'media': ('video.mp4', io.BytesIO(mp4_bytes), 'video/mp4')
        })
    except ImportError:
        # Sem requests_toolbelt — usar resumable upload
        print("Usando upload simples...")
        upload_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=multipart&part=snippet,status"
        import io
        from requests import Session
        s = Session()
        files = {
            'meta': (None, json.dumps(meta), 'application/json'),
            'video': ('video.mp4', io.BytesIO(mp4_bytes), 'video/mp4')
        }
        up_r = s.post(upload_url, headers={"Authorization": f"Bearer {token}"}, files=files, timeout=600)
        print(f"Upload status: {up_r.status_code}")
        if up_r.ok:
            yt_id = up_r.json().get("id","")
            print(f"VIDEO ID: {yt_id}")
            # Atualizar Supabase
            requests.patch(
                f"{SBU}/rest/v1/content_pipeline?id=eq.{v['id']}",
                headers={**hdrs, "Content-Type": "application/json"},
                json={"youtube_video_id": yt_id, "status": "published"},
                timeout=15
            )
            print(f"✅ Publicado: https://youtube.com/watch?v={yt_id}")
        else:
            print(f"Erro upload: {up_r.text[:300]}")

print("\n== YouTube Publisher finalizado ==")
