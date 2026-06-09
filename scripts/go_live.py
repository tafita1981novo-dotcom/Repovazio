#!/usr/bin/env python3
"""Live em produção: deletar upcoming + aplicar thumb v15 4K + transition para LIVE"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error

CI=os.environ["YT_CLIENT_ID"]; CS=os.environ["YT_CLIENT_SECRET"]
RT=os.environ["YT_REFRESH_TOKEN"]
BROADCAST_ID="5HqPWz058Qw"

def get_token():
    r=urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=urllib.parse.urlencode({"client_id":CI,"client_secret":CS,
            "refresh_token":RT,"grant_type":"refresh_token"}).encode(),
        headers={"Content-Type":"application/x-www-form-urlencoded"}),timeout=15)
    return json.loads(r.read())["access_token"]

def yt(method,ep,data=None,params=None,token=None):
    url="https://www.googleapis.com/youtube/v3/"+ep
    if params: url+="?"+urllib.parse.urlencode(params)
    headers={"Authorization":f"Bearer {token}"}
    body=None
    if data is not None:
        body=json.dumps(data).encode(); headers["Content-Type"]="application/json"
    req=urllib.request.Request(url,data=body,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read(); return (json.loads(raw) if raw else {}),r.status
    except urllib.error.HTTPError as e:
        raw=e.read(); return (json.loads(raw) if raw else {}),e.code

TOKEN=get_token()
print("Token OK")

# 1. Listar todos os broadcasts
print("\n1. Broadcasts atuais:")
all_ids=[]
for status in ["active","all","completed","upcoming"]:
    res,_=yt("GET","liveBroadcasts",params={
        "part":"id,snippet,status","broadcastStatus":status,"maxResults":"50"},token=TOKEN)
    for item in res.get("items",[]):
        bid=item["id"]
        if bid not in all_ids:
            all_ids.append(bid)
            lc=item.get("status",{}).get("lifeCycleStatus","?")
            t=item.get("snippet",{}).get("title","?")[:45]
            print(f"  {bid} | {lc:12s} | {t}")

# 2. Deletar TODOS exceto o eterno
to_del=[b for b in all_ids if b!=BROADCAST_ID]
if to_del:
    print(f"\n2. Deletando {len(to_del)} extras...")
    for bid in to_del:
        res,code=yt("DELETE","liveBroadcasts",params={"id":bid},token=TOKEN)
        print(f"  {'OK' if code in (200,204) else 'ERR '+str(code)} {bid}")
        time.sleep(0.4)
else:
    print("\n2. Canal limpo — nenhum extra")

# 3. Aplicar thumbnail v15 4K
print("\n3. Thumbnail v15 4K...")
url_t="https://raw.githubusercontent.com/tafita81/Repovazio/main/assets/thumbnail_live.png"
with urllib.request.urlopen(urllib.request.Request(url_t,
    headers={"User-Agent":"Mozilla/5.0","Cache-Control":"no-cache"}),timeout=30) as r:
    thumb=r.read()
print(f"   {len(thumb)//1024}KB")
bnd=b"tv15_bnd"
body=(b"--"+bnd+b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{}\r\n"
      +b"--"+bnd+b"\r\nContent-Type: image/jpeg\r\n\r\n"+thumb+b"\r\n--"+bnd+b"--")
req_t=urllib.request.Request(
    f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={BROADCAST_ID}&uploadType=multipart",
    data=body,method="POST",
    headers={"Authorization":f"Bearer {TOKEN}",
             "Content-Type":f"multipart/related; boundary={bnd.decode()}",
             "Content-Length":str(len(body))})
try:
    with urllib.request.urlopen(req_t,timeout=30) as r:
        print(f"   OK thumbnail! HTTP {r.status}")
except urllib.error.HTTPError as e:
    print(f"   WARN {e.code}: {e.read()[:150]}")

# 4. Verificar estado e fazer transition para LIVE
print(f"\n4. Estado do broadcast {BROADCAST_ID}...")
res,_=yt("GET","liveBroadcasts",params={
    "part":"id,status,contentDetails","id":BROADCAST_ID},token=TOKEN)
items=res.get("items",[])
if not items:
    print("   ERRO: broadcast nao encontrado!")
    sys.exit(1)
lc=items[0].get("status",{}).get("lifeCycleStatus","?")
print(f"   lifeCycleStatus: {lc}")
if lc in ("ready","testing"):
    print("   Fazendo transition -> live...")
    res2,code2=yt("POST","liveBroadcasts/transition",params={
        "broadcastStatus":"live","id":BROADCAST_ID,"part":"id,status"},token=TOKEN)
    if code2==200:
        lc2=res2.get("status",{}).get("lifeCycleStatus","?")
        print(f"   OK! Novo status: {lc2}")
    else:
        print(f"   {code2}: {res2.get('error',{}).get('message','?')[:150]}")
elif lc=="live":
    print("   JA ESTA LIVE!")
else:
    print(f"   Status '{lc}' — stream deve conectar via live-global-v5.yml")

print("\n===== LIVE EM PRODUCAO =====")
print(f"BROADCAST_ID = {BROADCAST_ID}")
print(f"Thumbnail    = v15 4K profissional")
print(f"Upcoming     = nenhum (limpo)")
