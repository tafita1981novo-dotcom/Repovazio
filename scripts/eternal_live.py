#!/usr/bin/env python3
"""Live Eterna: criar broadcast limpo + thumbnail v13 + ψ"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error

CI = os.environ["YT_CLIENT_ID"]
CS = os.environ["YT_CLIENT_SECRET"]
RT = os.environ["YT_REFRESH_TOKEN"]
SK = os.environ.get("YOUTUBE_STREAM_KEY","")
SU = os.environ["SUPABASE_URL"]
SK2= os.environ["SUPABASE_SERVICE_KEY"]

def yt(method, ep, data=None, params=None, token=None):
    url = "https://www.googleapis.com/youtube/v3/" + ep
    if params: url += "?" + urllib.parse.urlencode(params)
    headers = {"Authorization": f"Bearer {token}"}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read(); return (json.loads(raw) if raw else {}), r.status
    except urllib.error.HTTPError as e:
        raw = e.read(); return (json.loads(raw) if raw else {}), e.code

# 1. Token
print("1. Token...")
resp = urllib.request.urlopen(urllib.request.Request(
    "https://oauth2.googleapis.com/token",
    data=urllib.parse.urlencode({"client_id":CI,"client_secret":CS,
        "refresh_token":RT,"grant_type":"refresh_token"}).encode(),
    headers={"Content-Type":"application/x-www-form-urlencoded"}),timeout=15)
TOKEN = json.loads(resp.read())["access_token"]
print("   OK")

# 2. Listar broadcasts restantes
print("\n2. Broadcasts existentes:")
all_ids = []
for status in ["active","all","completed","upcoming"]:
    res, _ = yt("GET","liveBroadcasts",params={
        "part":"id,snippet,status","broadcastStatus":status,"maxResults":"50"},token=TOKEN)
    for item in res.get("items",[]):
        bid = item["id"]
        if bid not in all_ids:
            all_ids.append(bid)
            t = item.get("snippet",{}).get("title","?")[:40]
            s = item.get("status",{}).get("lifeCycleStatus","?")
            print(f"   {bid} | {s:10s} | {t}")
print(f"   Total: {len(all_ids)}")

# 3. Deletar qualquer restante
if all_ids:
    print("\n3. Deletando restantes...")
    for bid in all_ids:
        res, code = yt("DELETE","liveBroadcasts",params={"id":bid},token=TOKEN)
        print(f"   {'OK' if code in (200,204) else 'ERR '+str(code)} {bid}")
        time.sleep(0.4)
else:
    print("\n3. Nenhum para deletar — tudo limpo!")

# 4. Criar broadcast eterno (configuração mínima que funciona)
print("\n4. Criando broadcast eterno...")
from datetime import datetime, timezone, timedelta
start = (datetime.now(timezone.utc)+timedelta(minutes=3)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
TITLE = "\U0001f534 WHITE NOISE & BROWN NOISE 24/7 | Black Screen | Ruido Blanco | Ru\u00eddo Branco | \u767d\u566a\u97f3 | Sleep"
DESC = """\U0001f319 WHITE NOISE & BROWN NOISE 24/7 — Always LIVE, Never Recorded

\U0001f1fa\U0001f1f8 Sleep \u2022 \U0001f1ea\U0001f1f8 Sue\u00f1o \u2022 \U0001f1e7\U0001f1f7 Dormir \u2022 \U0001f1e9\U0001f1ea Schlafen \u2022 \U0001f1eb\U0001f1f7 Sommeil \u2022 \U0001f1ee\U0001f1f9 Dormire
\U0001f1ef\U0001f1f5 \u7720\u308b \u2022 \U0001f1f0\U0001f1f7 \uc218\uba74 \u2022 \U0001f1e8\U0001f1f3 \u7761\u89c9 \u2022 \U0001f1f8\U0001f1e6 \u0646\u0648\u0645 \u2022 \U0001f1f7\U0001f1fa \u0421\u043e\u043d \u2022 \U0001f1ee\U0001f1f3 \u0928\u0940\u0902\u0926
\U0001f1ee\U0001f1e9 Tidur \u2022 \U0001f1f3\U0001f1f1 Slapen \u2022 \U0001f1f9\U0001f1f7 Uyku \u2022 \U0001f1f5\U0001f1f1 Sen \u2022 \U0001f1fb\U0001f1f3 Ng\u1ee7

\u2705 White Noise \u2014 Scientifically proven for sleep, concentration & baby calming
\u2705 Brown Noise \u2014 Deep bass frequency for ADHD, anxiety & tinnitus relief

\U0001f514 Subscribe and never miss a session | Inscreva-se!

#whitenoise #brownnoise #sleep #ASMR #blackscreen #lofi #tinnitus #babysleep
#\ubc31\uc0c9\uc18c\uc74c #\u767d\u566a\u97f3 #\u30db\u30ef\u30a4\u30c8\u30ce\u30a4\u30ba #ruidoblanco #ruidobranco"""

res, code = yt("POST","liveBroadcasts",token=TOKEN,
    params={"part":"snippet,status,contentDetails"},
    data={
        "snippet":{"title":TITLE,"scheduledStartTime":start,"description":DESC},
        "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False,
                  "madeForKids":False},
        "contentDetails":{"enableAutoStart":True,"enableAutoStop":False,
            "monitorStream":{"enableMonitorStream":False},
            "latencyPreference":"ultraLow"}
    })
if code not in (200,201):
    print(f"   ERRO {code}: {res}")
    sys.exit(1)
BROADCAST_ID = res["id"]
print(f"   OK: {BROADCAST_ID}")

# 5. Stream ID
print("\n5. Stream ID...")
res2, _ = yt("GET","liveStreams",token=TOKEN,
    params={"part":"id,cdn,status","mine":"true","maxResults":"5"})
STREAM_ID = res2.get("items",[{}])[0].get("id","") if res2.get("items") else ""
print(f"   {STREAM_ID or 'nenhum'}")

# 6. Bind
if STREAM_ID:
    yt("POST","liveBroadcasts/bind",token=TOKEN,
       params={"id":BROADCAST_ID,"part":"id","streamId":STREAM_ID})
    print(f"6. Bound -> {STREAM_ID}")

# 7. Thumbnail v13
print("\n7. Thumbnail...")
req_t = urllib.request.Request(
    "https://raw.githubusercontent.com/tafita81/Repovazio/main/assets/thumbnail_live.png",
    headers={"User-Agent":"Mozilla/5.0"})
with urllib.request.urlopen(req_t,timeout=30) as r: thumb=r.read()
print(f"   {len(thumb)//1024}KB")
boundary=b"thumb_v13_boundary"
body=(b"--"+boundary+b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{}\r\n"
      +b"--"+boundary+b"\r\nContent-Type: image/jpeg\r\n\r\n"+thumb+b"\r\n"
      +b"--"+boundary+b"--")
req_u=urllib.request.Request(
    f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={BROADCAST_ID}&uploadType=multipart",
    data=body,method="POST",
    headers={"Authorization":f"Bearer {TOKEN}",
             "Content-Type":f"multipart/related; boundary={boundary.decode()}",
             "Content-Length":str(len(body))})
try:
    with urllib.request.urlopen(req_u,timeout=30): print("   OK thumbnail!")
except urllib.error.HTTPError as e:
    print(f"   WARN {e.code}: {e.read()[:150]}")

# 8. Supabase
print("\n8. Supabase...")
sb_body=json.dumps({"cache_key":"secret:live_broadcast_eternal",
    "value":json.dumps({"broadcast_id":BROADCAST_ID,"stream_id":STREAM_ID,
        "title":TITLE,"thumbnail":"v13","created":start}),
    "expires_at":"2099-12-31 23:59:59"}).encode()
req_sb=urllib.request.Request(f"{SU}/rest/v1/ia_cache",data=sb_body,method="POST",
    headers={"apikey":SK2,"Authorization":f"Bearer {SK2}",
             "Content-Type":"application/json","Prefer":"resolution=merge-duplicates"})
try:
    with urllib.request.urlopen(req_sb,timeout=15) as r: print(f"   OK {r.status}")
except urllib.error.HTTPError as e: print(f"   WARN {e.code}")

print(f"\n{'='*55}")
print(f"BROADCAST_ID = {BROADCAST_ID}")
print(f"STREAM_ID    = {STREAM_ID}")
print("LIVE ETERNA CONFIGURADA! Activating via live-global-v5")
print(f"{'='*55}")

gho=os.environ.get("GITHUB_OUTPUT","")
if gho:
    with open(gho,"a") as f:
        f.write(f"broadcast_id={BROADCAST_ID}\nstream_id={STREAM_ID}\n")
