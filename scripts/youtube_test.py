#!/usr/bin/env python3
"""
Teste e publicacao YouTube para @psidanielacoelho.
ACTION=test|publish, LIMIT=N
"""
import os, sys, json, time, urllib.request, urllib.parse

SBU  = os.environ["SUPABASE_URL"].rstrip("/")
SBK  = os.environ["SUPABASE_SERVICE_KEY"]
H_SB = {"apikey": SBK, "Authorization": "Bearer " + SBK}
H_SB_J = dict(H_SB, **{"Content-Type": "application/json"})
YT_CID  = os.environ.get("YT_CLIENT_ID", "")
YT_CSEC = os.environ.get("YT_CLIENT_SECRET", "")
YT_RT   = os.environ.get("YT_REFRESH_TOKEN", "")
ACTION  = os.environ.get("ACTION", "test")
LIMIT   = int(os.environ.get("LIMIT", "2"))
CORRECT = "UCyCkIpsVgME9yCj_oXJFheA"
BLOCKED = "UCSH63tBfY6wEIdkC4u4zKdg"

def log(*a): print("[" + time.strftime("%H:%M:%S") + "]", *a, flush=True)

def http(url, method="GET", body=None, headers=None, timeout=300, raw=False):
    h = dict(headers or {})
    h.setdefault("User-Agent", "psicologia-doc/2.0")
    data = None
    if body is not None:
        if raw or isinstance(body, (bytes, bytearray)):
            data = body if isinstance(body, (bytes, bytearray)) else body.encode()
        else:
            data = json.dumps(body).encode()
            h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, (e.read() if e.fp else b""), dict(e.headers or {})

# Checar credenciais
log("Checando credenciais YT...")
for k, v, name in [(YT_CID,"cid","YT_CLIENT_ID"), (YT_CSEC,"cs","YT_CLIENT_SECRET"), (YT_RT,"rt","YT_REFRESH_TOKEN")]:
    log("  " + name + ": " + ("OK" if v else "FALTA"))
if not (YT_CID and YT_CSEC and YT_RT):
    log("ERRO: Credenciais faltando nos GitHub Secrets")
    sys.exit(1)

# Obter Access Token
body_str = urllib.parse.urlencode({
    "client_id": YT_CID, "client_secret": YT_CSEC,
    "refresh_token": YT_RT, "grant_type": "refresh_token"
})
s, raw, _ = http("https://oauth2.googleapis.com/token", method="POST",
    body=body_str.encode(), raw=True,
    headers={"Content-Type": "application/x-www-form-urlencoded"})
if s != 200:
    log("ERRO OAuth (" + str(s) + "): " + raw[:300].decode("utf-8","replace"))
    log("Refresh Token invalido. Gere novo: developers.google.com/oauthplayground")
    sys.exit(1)
at = json.loads(raw)["access_token"]
log("Access Token OK!")

# Verificar canal
s2, raw2, _ = http(
    "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true",
    headers={"Authorization": "Bearer " + at})
ch_data = json.loads(raw2)
items = ch_data.get("items", [])
if not items:
    log("ERRO: Sem canal. Resp=" + raw2[:200].decode("utf-8","replace"))
    sys.exit(1)
ch = items[0]
ch_id = ch["id"]
snip = ch.get("snippet", {})
stats = ch.get("statistics", {})
if ch_id == BLOCKED:
    log("BLOQUEADO: canal antigo " + ch_id)
    sys.exit(1)
log("Canal: " + snip.get("title","?") + " | ID=" + ch_id)
log("Subs=" + stats.get("subscriberCount","?") + " Videos=" + stats.get("videoCount","?"))
log("Canal correto: " + ("SIM" if ch_id == CORRECT else "ATENCAO: ID=" + ch_id))

if ACTION == "test":
    log("TESTE OK - credenciais funcionando!")
    sys.exit(0)

# Publicar pendentes
log("Buscando " + str(LIMIT) + " videos mp4_ready...")
s3, raw3, _ = http(
    SBU + "/rest/v1/content_pipeline?status=eq.mp4_ready&mp4_url=not.is.null&order=id.asc&limit=" + str(LIMIT) + "&select=*",
    headers=H_SB)
pipelines = json.loads(raw3)
log("Encontrados: " + str(len(pipelines)))
if not pipelines:
    log("Nada pendente.")
    sys.exit(0)

published = 0
for p in pipelines:
    pid = p["id"]
    title = (p.get("youtube_title") or p.get("title") or "Video")[:100]
    base_desc = p.get("title") or ""
    desc = (p.get("youtube_description") or base_desc + "\n\n#psicologia #saudemental #danielacoelho")[:5000]
    tags_raw = p.get("youtube_tags") or "[]"
    tags = json.loads(tags_raw) or ["psicologia", "saude mental", "Daniela Coelho"]
    mp4_url = p.get("mp4_url", "")
    log("Publicando #" + str(pid) + ": " + title)
    s4, mp4_data, _ = http(mp4_url, timeout=300)
    if s4 != 200:
        log("  Download falhou (" + str(s4) + ")")
        continue
    log("  MP4: " + str(len(mp4_data)//1024) + "KB")
    meta = {
        "snippet": {"title": title, "description": desc, "tags": tags[:500],
                    "categoryId": "26", "defaultLanguage": "pt-BR", "defaultAudioLanguage": "pt-BR"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }
    s5, raw5, h5 = http(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        method="POST", body=json.dumps(meta).encode(), raw=True,
        headers={"Authorization": "Bearer " + at, "Content-Type": "application/json",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(mp4_data))})
    if s5 not in (200, 201):
        log("  Init upload falhou (" + str(s5) + "): " + raw5[:200].decode("utf-8","replace"))
        continue
    uurl = h5.get("Location", "")
    if not uurl:
        log("  Sem Location header")
        continue
    log("  Enviando video...")
    s6, raw6, _ = http(uurl, method="PUT", body=mp4_data, raw=True,
        headers={"Content-Type": "video/mp4", "Content-Length": str(len(mp4_data))}, timeout=600)
    if s6 not in (200, 201):
        log("  Upload falhou (" + str(s6) + "): " + raw6[:200].decode("utf-8","replace"))
        continue
    vdata = json.loads(raw6)
    vid = vdata.get("id", "")
    if not vid:
        log("  Sem video ID")
        continue
    yt_url = "https://www.youtube.com/watch?v=" + vid
    log("  PUBLICADO: " + yt_url)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    http(SBU + "/rest/v1/content_pipeline?id=eq." + str(pid), method="PATCH",
        body={"status": "published", "youtube_id": vid, "youtube_url": yt_url, "published_at": now},
        headers=H_SB_J)
    published += 1
    time.sleep(5)

log("RESULTADO: " + str(published) + "/" + str(len(pipelines)) + " publicados")
