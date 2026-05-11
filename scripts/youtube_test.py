#!/usr/bin/env python3
"""
Teste e publicação YouTube para @psidanielacoelho.
Uso: ACTION=test python3 scripts/youtube_test.py
     ACTION=publish LIMIT=2 python3 scripts/youtube_test.py
"""
import os, sys, json, time, urllib.request, urllib.parse

SBU  = os.environ["SUPABASE_URL"].rstrip("/")
SBK  = os.environ["SUPABASE_SERVICE_KEY"]
H_SB = {"apikey": SBK, "Authorization": f"Bearer {SBK}"}
H_SB_J = {**H_SB, "Content-Type": "application/json"}
YT_CID  = os.environ.get("YT_CLIENT_ID", "")
YT_CSEC = os.environ.get("YT_CLIENT_SECRET", "")
YT_RT   = os.environ.get("YT_REFRESH_TOKEN", "")
ACTION  = os.environ.get("ACTION", "test")
LIMIT   = int(os.environ.get("LIMIT", "2"))
CORRECT = "UCyCkIpsVgME9yCj_oXJFheA"
BLOCKED = "UCSH63tBfY6wEIdkC4u4zKdg"

def log(*a): print(f"[{time.strftime(\"%H:%M:%S\")}]", *a, flush=True)

def http(url, method="GET", body=None, headers=None, timeout=300, raw=False):
    h = dict(headers or {})
    data = None
    if body is not None:
        data = body if (raw or isinstance(body, (bytes,bytearray))) else json.dumps(body).encode()
        if not raw and not isinstance(body, (bytes,bytearray)):
            h.setdefault("Content-Type","application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    req.add_header("User-Agent","psicologia-doc/2.0")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, (e.read() if e.fp else b""), dict(e.headers or {})

# ── Token ──────────────────────────────────────────────────────────────────
log("Checando credenciais...")
creds_ok = all([YT_CID, YT_CSEC, YT_RT])
log(f"  CLIENT_ID:     {\"OK\" if YT_CID else \"FALTA\"}")
log(f"  CLIENT_SECRET: {\"OK\" if YT_CSEC else \"FALTA\"}")
log(f"  REFRESH_TOKEN: {\"OK\" if YT_RT else \"FALTA\"}")

if not creds_ok:
    log("ERRO: Credenciais faltando. Configure os GitHub Secrets.")
    sys.exit(1)

body = urllib.parse.urlencode({"client_id":YT_CID,"client_secret":YT_CSEC,"refresh_token":YT_RT,"grant_type":"refresh_token"}).encode()
s, raw, _ = http("https://oauth2.googleapis.com/token", method="POST", body=body, raw=True,
    headers={"Content-Type":"application/x-www-form-urlencoded"})

if s != 200:
    log(f"ERRO OAuth ({s}): {raw[:300].decode()}")
    log("Refresh Token invalido ou revogado.")
    log("Gere novo em: developers.google.com/oauthplayground")
    sys.exit(1)

at = json.loads(raw)["access_token"]
log("Access Token obtido!")

# ── Verificar canal ─────────────────────────────────────────────────────────
s2, raw2, _ = http("https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true",
    headers={"Authorization":f"Bearer {at}"})
ch_data = json.loads(raw2)
if not ch_data.get("items"):
    log(f"ERRO: Nenhum canal. Resposta={raw2[:200].decode()}")
    sys.exit(1)
ch = ch_data["items"][0]
ch_id = ch["id"]
if ch_id == BLOCKED:
    log(f"BLOQUEADO: canal antigo {ch_id}")
    sys.exit(1)
log(f"Canal: {ch[\"snippet\"][\"title\"]} | ID={ch_id} | Subs={ch[\"statistics\"].get(\"subscriberCount\",\"?\")} | Videos={ch[\"statistics\"].get(\"videoCount\",\"?\")} | Views={ch[\"statistics\"].get(\"viewCount\",\"?\")}")
log(f"Canal correto: {\"SIM\" if ch_id == CORRECT else \"ATENCAO: ID diferente do esperado\"}")

if ACTION == "test":
    log("TESTE OK - credenciais funcionando!")
    sys.exit(0)

# ── Publicar ────────────────────────────────────────────────────────────────
log(f"Buscando {LIMIT} videos mp4_ready...")
s3, raw3, _ = http(f"{SBU}/rest/v1/content_pipeline?status=eq.mp4_ready&mp4_url=not.is.null&order=id.asc&limit={LIMIT}&select=*",
    headers=H_SB)
pipelines = json.loads(raw3)
log(f"Encontrados: {len(pipelines)}")

if not pipelines:
    log("Nenhum video pendente.")
    sys.exit(0)

published = 0
for p in pipelines:
    pid = p["id"]
    title = (p.get("youtube_title") or p.get("title") or "Video")[:100]
    desc  = (p.get("youtube_description") or f"{p.get(\"title\",\"\")}

#psicologia #saudemental #danielacoelho")[:5000]
    tags  = json.loads(p.get("youtube_tags") or "[]") or ["psicologia","saude mental","Daniela Coelho"]
    mp4_url = p.get("mp4_url","")
    log(f"Publicando #{pid}: {title}")
    s4, mp4_data, _ = http(mp4_url, timeout=300)
    if s4 != 200:
        log(f"  Download falhou ({s4})")
        continue
    log(f"  MP4: {len(mp4_data)//1024}KB")
    meta = {"snippet":{"title":title,"description":desc,"tags":tags[:500],"categoryId":"26","defaultLanguage":"pt-BR","defaultAudioLanguage":"pt-BR"},"status":{"privacyStatus":"public","selfDeclaredMadeForKids":False}}
    s5, raw5, h5 = http("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        method="POST", body=json.dumps(meta).encode(), raw=True,
        headers={"Authorization":f"Bearer {at}","Content-Type":"application/json","X-Upload-Content-Type":"video/mp4","X-Upload-Content-Length":str(len(mp4_data))})
    if s5 not in (200,201):
        log(f"  Init upload falhou ({s5}): {raw5[:200].decode()}")
        continue
    uurl = h5.get("Location","")
    if not uurl:
        log("  Sem Location header")
        continue
    log("  Enviando video...")
    s6, raw6, _ = http(uurl, method="PUT", body=mp4_data, raw=True,
        headers={"Content-Type":"video/mp4","Content-Length":str(len(mp4_data))}, timeout=600)
    if s6 not in (200,201):
        log(f"  Upload falhou ({s6}): {raw6[:200].decode()}")
        continue
    vdata = json.loads(raw6)
    vid = vdata.get("id","")
    if not vid:
        log("  Sem video ID")
        continue
    yt_url = f"https://www.youtube.com/watch?v={vid}"
    log(f"  PUBLICADO: {yt_url}")
    http(f"{SBU}/rest/v1/content_pipeline?id=eq.{pid}", method="PATCH",
        body={"status":"published","youtube_id":vid,"youtube_url":yt_url,"published_at":time.strftime("%Y-%m-%dT%H:%M:%SZ")},
        headers=H_SB_J)
    published += 1
    time.sleep(5)

log(f"RESULTADO: {published}/{len(pipelines)} publicados")

