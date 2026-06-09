#!/usr/bin/env python3
"""Live Eterna: deletar histórico + criar broadcast perfeito + thumbnail v13"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error

CLIENT_ID     = os.environ["YT_CLIENT_ID"]
CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
STREAM_KEY    = os.environ.get("YOUTUBE_STREAM_KEY", "")
SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_SERVICE_KEY"]

def yt(method, endpoint, data=None, params=None, token=None):
    url = "https://www.googleapis.com/youtube/v3/" + endpoint
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {"Authorization": f"Bearer {token}"}
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    else:
        body = None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return (json.loads(raw) if raw else {}), r.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        return (json.loads(raw) if raw else {}), e.code

# 1. Access token
print("1. Access token...")
resp = urllib.request.urlopen(urllib.request.Request(
    "https://oauth2.googleapis.com/token",
    data=urllib.parse.urlencode({
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN, "grant_type": "refresh_token"
    }).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"}
), timeout=15)
TOKEN = json.loads(resp.read())["access_token"]
print("   OK")

# 2. Listar todos broadcasts
print("\n2. Broadcasts existentes:")
all_ids = []
for status in ["active","all","completed","upcoming"]:
    res, _ = yt("GET","liveBroadcasts",params={"part":"id,snippet,status",
                 "broadcastStatus":status,"maxResults":"50"},token=TOKEN)
    for item in res.get("items",[]):
        bid = item["id"]
        if bid not in all_ids:
            all_ids.append(bid)
            t = item.get("snippet",{}).get("title","?")[:45]
            s = item.get("status",{}).get("lifeCycleStatus","?")
            print(f"   {bid} | {s:12s} | {t}")
print(f"   Total: {len(all_ids)}")

# 3. Deletar todos
print("\n3. Deletando...")
for bid in all_ids:
    res, code = yt("DELETE","liveBroadcasts",params={"id":bid},token=TOKEN)
    print(f"   {'OK' if code in (200,204) else 'ERR '+str(code)} {bid}")
    time.sleep(0.4)

# 4. Criar broadcast eterno
print("\n4. Criando broadcast eterno...")
from datetime import datetime, timezone, timedelta
start = (datetime.now(timezone.utc)+timedelta(minutes=3)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
TITLE = "\U0001f534 WHITE NOISE & BROWN NOISE 24/7 | Black Screen | Ruido Blanco | Ru\u00eddo Branco | \u767d\u566a\u97f3 | Sleep"
res, code = yt("POST","liveBroadcasts",token=TOKEN,
    params={"part":"snippet,status,contentDetails"},
    data={
        "snippet":{"title":TITLE,"scheduledStartTime":start,
            "description":"\U0001f319 WHITE NOISE & BROWN NOISE 24/7 — Always LIVE, Never Recorded\n\nSleep | Sue\u00f1o | Dormir | Schlafen | Sommeil | Dormire\n\u7720\u308b | \uc218\uba74 | \u7761\u89c9 | \u0646\u0648\u0645 | \u0421\u043e\u043d | \u0928\u0940\u0902\u0926\n\nTidur | Slapen | Uyku | Sen | Ng\u1ee7\n\n#whitenoise #brownnoise #sleep #ASMR #blackscreen #lofi"},
        "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False},
        "contentDetails":{"enableAutoStart":True,"enableAutoStop":False,
            "enableDvr":False,"recordFromStart":False,"startWithSlate":False,
            "monitorStream":{"enableMonitorStream":False},"latencyPreference":"ultraLow"}
    })
if code not in (200,201):
    print(f"   ERRO {code}: {res}")
    sys.exit(1)
BROADCAST_ID = res["id"]
print(f"   OK: {BROADCAST_ID}")

# 5. Stream existente
print("\n5. Stream ID...")
res2, _ = yt("GET","liveStreams",token=TOKEN,
    params={"part":"id,cdn,status","mine":"true","maxResults":"5"})
STREAM_ID = res2.get("items",[{}])[0].get("id","") if res2.get("items") else ""
print(f"   {STREAM_ID or 'nenhum'}")

# 6. Bind
if STREAM_ID:
    yt("POST","liveBroadcasts/bind",token=TOKEN,
       params={"id":BROADCAST_ID,"part":"id","streamId":STREAM_ID})
    print(f"6. Bound {BROADCAST_ID} -> {STREAM_ID}")

# 7. Thumbnail
print("\n7. Thumbnail...")
req_t = urllib.request.Request(
    "https://raw.githubusercontent.com/tafita81/Repovazio/main/assets/thumbnail_live.png",
    headers={"User-Agent":"Mozilla/5.0"})
with urllib.request.urlopen(req_t, timeout=30) as r:
    thumb = r.read()
print(f"   {len(thumb)//1024}KB baixada")
boundary = b"thumb_boundary_v13"
body = (b"--"+boundary+b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{}\r\n"
        +b"--"+boundary+b"\r\nContent-Type: image/jpeg\r\n\r\n"+thumb+b"\r\n"
        +b"--"+boundary+b"--")
req_u = urllib.request.Request(
    f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={BROADCAST_ID}&uploadType=multipart",
    data=body, method="POST",
    headers={"Authorization":f"Bearer {TOKEN}",
             "Content-Type":f"multipart/related; boundary={boundary.decode()}",
             "Content-Length":str(len(body))})
try:
    with urllib.request.urlopen(req_u, timeout=30) as r:
        print("   OK thumbnail aplicada!")
except urllib.error.HTTPError as e:
    print(f"   WARN {e.code}: {e.read()[:150]}")

# 8. Salvar no Supabase
print("\n8. Supabase...")
sb_body = json.dumps({"cache_key":"secret:live_broadcast_eternal",
    "value":json.dumps({"broadcast_id":BROADCAST_ID,"stream_id":STREAM_ID,
        "title":TITLE,"thumbnail":"v13","created":start}),
    "expires_at":"2099-12-31 23:59:59"}).encode()
req_sb = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/ia_cache",
    data=sb_body, method="POST",
    headers={"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}",
             "Content-Type":"application/json","Prefer":"resolution=merge-duplicates"})
try:
    with urllib.request.urlopen(req_sb, timeout=15) as r:
        print(f"   OK HTTP {r.status}")
except urllib.error.HTTPError as e:
    print(f"   WARN {e.code}")

print(f"\n{'='*50}")
print(f"BROADCAST_ID={BROADCAST_ID}")
print(f"STREAM_ID={STREAM_ID}")
print("LIVE ETERNA CONFIGURADA!")
print(f"{'='*50}")

# Output
gho = os.environ.get("GITHUB_OUTPUT","")
if gho:
    with open(gho,"a") as f:
        f.write(f"broadcast_id={BROADCAST_ID}\n")
        f.write(f"stream_id={STREAM_ID}\n")
