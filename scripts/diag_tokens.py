#!/usr/bin/env python3
import os, sys, json, urllib.request, urllib.parse

CID = os.environ.get("YT_CLIENT_ID","")
CSC = os.environ.get("YT_CLIENT_SECRET","")

CANAIS = {
    "dbn": os.environ.get("YT_RT_DBN",""),
    "adhd": os.environ.get("YT_RT_ADHD",""),
    "wnv": os.environ.get("YT_RT_WNV",""),
    "tinnitus": os.environ.get("YT_RT_TINNITUS",""),
}

print(f"CID presente: {bool(CID)}", flush=True)
print(f"CSC presente: {bool(CSC)}", flush=True)

errors = []
for canal, rt in CANAIS.items():
    print(f"\n--- {canal} ---", flush=True)
    if not rt:
        print(f"RT vazio!", flush=True)
        errors.append(canal)
        continue
    print(f"RT len={len(rt)}, prefix={rt[:20]}", flush=True)
    d = urllib.parse.urlencode({"client_id":CID,"client_secret":CSC,"refresh_token":rt,"grant_type":"refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token",data=d,method="POST",headers={"Content-Type":"application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            td = json.loads(r.read())
            at = td.get("access_token","")
            print(f"AT OK len={len(at)}", flush=True)
            # Verificar canal
            req2 = urllib.request.Request("https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",headers={"Authorization":f"Bearer {at}"})
            with urllib.request.urlopen(req2,timeout=10) as r2:
                ch = json.loads(r2.read())
            name = ch.get("items",[{}])[0].get("snippet",{}).get("title","NO_CHANNEL")
            print(f"Canal: {name}", flush=True)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP {e.code}: {body[:200]}", flush=True)
        errors.append(f"{canal}:HTTP{e.code}")
    except Exception as ex:
        print(f"ERR: {ex}", flush=True)
        errors.append(canal)

print(f"\nErros: {errors}", flush=True)
if errors:
    sys.exit(1)
print("TODOS OK", flush=True)
