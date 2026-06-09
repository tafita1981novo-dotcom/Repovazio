#!/usr/bin/env python3
"""
Workflow: Criar live eterna, deletar histórico, aplicar thumbnail v13
"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error

# ── Credenciais ────────────────────────────────────────────────
CLIENT_ID     = os.environ['YT_CLIENT_ID']
CLIENT_SECRET = os.environ['YT_CLIENT_SECRET']
REFRESH_TOKEN = os.environ['YT_REFRESH_TOKEN']
STREAM_KEY    = os.environ.get('YOUTUBE_STREAM_KEY', '')
SUPABASE_URL  = os.environ['SUPABASE_URL']
SUPABASE_KEY  = os.environ['SUPABASE_SERVICE_KEY']

def yt(method, endpoint, data=None, params=None, token=None, files=None):
    base = "https://www.googleapis.com/youtube/v3"
    url  = f"{base}/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {"Authorization": f"Bearer {token}"}
    if data is not None and files is None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    elif files:
        body = files
    else:
        body = None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        err = e.read()
        try: return json.loads(err), e.code
        except: return {"error": str(err)}, e.code

# ── 1. Obter access token ───────────────────────────────────────
print("1. Obtendo access token...")
data = urllib.parse.urlencode({
    "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
    "refresh_token": REFRESH_TOKEN, "grant_type": "refresh_token"
}).encode()
req = urllib.request.Request("https://oauth2.googleapis.com/token",
    data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
with urllib.request.urlopen(req, timeout=15) as r:
    tok = json.loads(r.read())
TOKEN = tok["access_token"]
print(f"   ✅ Token obtido")

# ── 2. Listar TODOS os broadcasts ──────────────────────────────
print("\n2. Listando broadcasts existentes...")
all_ids = []
page = None
for status in ["active", "all", "completed", "upcoming"]:
    params = {"part":"id,snippet,status","broadcastStatus":status,"maxResults":"50"}
    if page: params["pageToken"] = page
    res, code = yt("GET", "liveBroadcasts", params=params, token=TOKEN)
    items = res.get("items", [])
    for item in items:
        bid = item["id"]
        title = item.get("snippet",{}).get("title","?")[:40]
        lstatus = item.get("status",{}).get("lifeCycleStatus","?")
        if bid not in all_ids:
            all_ids.append(bid)
            print(f"   {bid} | {lstatus:15s} | {title}")

print(f"\n   Total encontrado: {len(all_ids)} broadcasts")

# ── 3. Deletar TODOS os broadcasts ─────────────────────────────
print("\n3. Deletando todos os broadcasts...")
deleted = 0
for bid in all_ids:
    res, code = yt("DELETE", "liveBroadcasts", params={"id": bid}, token=TOKEN)
    if code in (200, 204):
        print(f"   ✅ Deletado: {bid}")
        deleted += 1
    elif code == 403:
        print(f"   ⚠️  Não deletável (em andamento?): {bid}")
    else:
        print(f"   ❌ Erro {code}: {bid}")
    time.sleep(0.3)

print(f"\n   Deletados: {deleted}/{len(all_ids)}")

# ── 4. Criar broadcast eterno ─────────────────────────────────
print("\n4. Criando broadcast eterno...")
from datetime import datetime, timezone, timedelta
start = (datetime.now(timezone.utc) + timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

TITLE = "🔴 WHITE NOISE & BROWN NOISE 24/7 | Black Screen | Ruido Blanco | Ruído Branco | 白噪音 | Sleep"

broadcast_body = {
    "snippet": {
        "title": TITLE,
        "scheduledStartTime": start,
        "description": """🌙 WHITE NOISE & BROWN NOISE 24/7 — Always LIVE, Never Recorded

Use headphones for the best experience | Utilize fones de ouvido para a melhor experiência

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🇺🇸 SLEEP • 🇪🇸 SUEÑO • 🇧🇷 DORMIR • 🇩🇪 SCHLAFEN • 🇫🇷 SOMMEIL • 🇮🇹 DORMIRE
🇯🇵 眠る • 🇰🇷 수면 • 🇨🇳 睡觉 • 🇸🇦 نوم • 🇷🇺 СОН • 🇮🇳 नींद
🇮🇩 TIDUR • 🇳🇱 SLAPEN • 🇹🇷 UYKU • 🇵🇱 SEN • 🇻🇳 NGỦ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ White Noise — Scientifically proven for sleep, concentration & baby calming
✅ Brown Noise — Deep bass frequency for ADHD, anxiety & tinnitus relief
✅ Mix 40% White + 60% Brown — Optimal balance for deep sleep

🔔 Subscribe and never miss a session | Inscreva-se e nunca perca uma sessão

#whitenoise #brownnoise #sleep #ASMR #blackscreen #lofi #tinnitus #babysleep
#백색소음 #白噪音 #ホワイトノイズ #ruidoblanco #ruidobranco #sommeil #schlaf""",
    },
    "status": {
        "privacyStatus": "public",
        "selfDeclaredMadeForKids": False,
        "madeForKids": False,
    },
    "contentDetails": {
        "enableAutoStart": True,
        "enableAutoStop": False,
        "enableDvr": False,
        "recordFromStart": False,
        "startWithSlate": False,
        "monitorStream": {"enableMonitorStream": False},
        "latencyPreference": "ultraLow",
    },
}

res, code = yt("POST", "liveBroadcasts", data=broadcast_body,
               params={"part": "snippet,status,contentDetails"}, token=TOKEN)
if code not in (200, 201):
    print(f"   ❌ Erro ao criar broadcast: {code} → {res}")
    sys.exit(1)

BROADCAST_ID = res["id"]
print(f"   ✅ Broadcast criado: {BROADCAST_ID}")

# ── 5. Buscar live stream existente ou criar ──────────────────
print("\n5. Buscando/criando live stream...")
res, code = yt("GET", "liveStreams", params={
    "part":"id,snippet,cdn,status","mine":"true","maxResults":"10"
}, token=TOKEN)
streams = res.get("items",[])
STREAM_ID = None
for s in streams:
    skey = s.get("cdn",{}).get("ingestionInfo",{}).get("streamName","")
    if STREAM_KEY and STREAM_KEY in skey:
        STREAM_ID = s["id"]
        print(f"   ✅ Stream existente: {STREAM_ID}")
        break
    elif streams:
        STREAM_ID = streams[0]["id"]
        print(f"   ✅ Usando primeiro stream: {STREAM_ID}")
        break

if not STREAM_ID:
    print("   Criando novo live stream...")
    stream_body = {
        "snippet": {"title": "White/Brown Noise Live Stream"},
        "cdn": {
            "frameRate": "30fps",
            "ingestionType": "rtmp",
            "resolution": "1080p",
        },
        "contentDetails": {"isReusable": True},
    }
    res, code = yt("POST", "liveStreams", data=stream_body,
                   params={"part":"snippet,cdn,contentDetails,status"}, token=TOKEN)
    if code in (200,201):
        STREAM_ID = res["id"]
        print(f"   ✅ Stream criado: {STREAM_ID}")
    else:
        print(f"   ❌ {code}: {res}")

# ── 6. Bind broadcast ao stream ────────────────────────────────
if STREAM_ID:
    print(f"\n6. Binding broadcast {BROADCAST_ID} ao stream {STREAM_ID}...")
    res, code = yt("POST", "liveBroadcasts/bind", params={
        "id": BROADCAST_ID,
        "part": "id,contentDetails",
        "streamId": STREAM_ID
    }, token=TOKEN)
    if code == 200:
        print(f"   ✅ Bound!")
    else:
        print(f"   ⚠️  {code}: {res}")

# ── 7. Aplicar thumbnail ───────────────────────────────────────
print("\n7. Aplicando thumbnail v13...")
# Baixar thumbnail do GitHub
thumb_url = "https://raw.githubusercontent.com/tafita81/Repovazio/main/assets/thumbnail_live.png"
req = urllib.request.Request(thumb_url, headers={"User-Agent":"Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    thumb_data = r.read()
print(f"   Thumbnail baixada: {len(thumb_data)//1024}KB")

# Upload para YouTube (multipart)
import email.mime.multipart, email.mime.base, email.mime.application
boundary = b"--livestream_boundary_v13--"
body = (
    b"--" + boundary + b"\r\n" +
    b"Content-Type: application/json; charset=UTF-8\r\n\r\n" +
    b"{}\r\n" +
    b"--" + boundary + b"\r\n" +
    b"Content-Type: image/jpeg\r\n\r\n" +
    thumb_data + b"\r\n" +
    b"--" + boundary + b"--"
)
upload_url = (f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
              f"?videoId={BROADCAST_ID}&uploadType=multipart")
req2 = urllib.request.Request(upload_url, data=body, method="POST", headers={
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": f"multipart/related; boundary={boundary.decode()}",
    "Content-Length": str(len(body)),
})
try:
    with urllib.request.urlopen(req2, timeout=30) as r:
        res2 = json.loads(r.read())
    print(f"   ✅ Thumbnail aplicada!")
except urllib.error.HTTPError as e:
    print(f"   ⚠️  Thumbnail: {e.code} — {e.read()[:200]}")

# ── 8. Salvar broadcast_id no Supabase ────────────────────────
print("\n8. Salvando broadcast_id no Supabase...")
sb_data = json.dumps({
    "cache_key": "secret:live_broadcast_eternal",
    "value": json.dumps({
        "broadcast_id": BROADCAST_ID,
        "stream_id": STREAM_ID,
        "title": TITLE,
        "created": start,
        "thumbnail": "v13"
    }),
    "expires_at": "2099-12-31 23:59:59"
}).encode()

sb_req = urllib.request.Request(
    f"{SUPABASE_URL}/rest/v1/ia_cache",
    data=sb_data,
    headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    },
    method="POST"
)
try:
    with urllib.request.urlopen(sb_req, timeout=15) as r:
        print(f"   ✅ Salvo no Supabase (HTTP {r.status})")
except urllib.error.HTTPError as e:
    print(f"   ⚠️  Supabase: {e.code}")

print(f"\n{'='*50}")
print(f"✅ BROADCAST_ID={BROADCAST_ID}")
print(f"✅ STREAM_ID={STREAM_ID}")
print(f"✅ Live eterna configurada!")
print(f"{'='*50}")

# Output para o workflow
with open(os.environ.get('GITHUB_OUTPUT','//dev/null'), 'a') as f:
    f.write(f"broadcast_id={BROADCAST_ID}\n")
    f.write(f"stream_id={STREAM_ID}\n")
