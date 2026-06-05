#!/usr/bin/env python3
"""Fix: bind broadcast NZpc6TiTH_A ao stream correto"""
import os, json, urllib.request, urllib.parse

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
ST_KEY_VAL       = "ewme-91sq-yae7-yj1q-5skw"
BC_ID            = "NZpc6TiTH_A"

def get_token():
    data=urllib.parse.urlencode({"client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
        "refresh_token":YT_REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    req=urllib.request.Request("https://oauth2.googleapis.com/token",data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req,timeout=15) as r:
        return json.loads(r.read())["access_token"]

def yt_get(token, url):
    req=urllib.request.Request(url)
    req.add_header("Authorization",f"Bearer {token}")
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read())

token = get_token()
print(f"Token OK: {token[:20]}...")

# Listar streams do usuário
data = yt_get(token, "https://www.googleapis.com/youtube/v3/liveStreams?part=id,snippet,cdn&mine=true&maxResults=50")
print(f"\nStreams encontrados: {len(data.get('items',[]))}")
stream_id = None
for item in data.get("items", []):
    key = item.get("cdn",{}).get("ingestionInfo",{}).get("streamName","")
    sid = item["id"]
    title = item.get("snippet",{}).get("title","")
    print(f"  {sid}: {title[:40]} | key: {key[:30]}")
    if key == ST_KEY_VAL:
        stream_id = sid
        print(f"  ✅ MATCH: stream_id={sid}")

if stream_id:
    # Bind broadcast ao stream
    bind_url=f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={BC_ID}&part=id&streamId={stream_id}"
    req=urllib.request.Request(bind_url,data=b"{}",method="POST")
    req.add_header("Authorization",f"Bearer {token}")
    req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            res=json.loads(r.read())
            print(f"\nBind OK: {res.get('id')}")
    except Exception as e:
        print(f"\nBind erro: {e}")
else:
    print("\nStream não encontrado pelo key — tentando bind pelo nome")
    # Tentar pegar o primeiro stream disponível
    if data.get("items"):
        stream_id = data["items"][0]["id"]
        bind_url=f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={BC_ID}&part=id&streamId={stream_id}"
        req=urllib.request.Request(bind_url,data=b"{}",method="POST")
        req.add_header("Authorization",f"Bearer {token}")
        req.add_header("Content-Type","application/json")
        try:
            with urllib.request.urlopen(req,timeout=15) as r:
                res=json.loads(r.read())
                print(f"Bind (fallback) OK: {res.get('id')}")
        except Exception as e:
            print(f"Bind erro: {e}")

# Listar broadcasts ativos para confirmar
data2 = yt_get(token, f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status&id={BC_ID}")
for item in data2.get("items",[]):
    print(f"\nBroadcast {item['id']}: {item.get('snippet',{}).get('title','')[:60]}")
    print(f"  Status: {item.get('status',{}).get('lifeCycleStatus')}")
