#!/usr/bin/env python3
import requests, os, sys, json

CI = os.environ["YT_CLIENT_ID"]
CS = os.environ["YT_CLIENT_SECRET"]

CANAIS = {
  "bsn":  {"rt": os.environ["YT_RT_BSN"],  "vid": "dGdrOUA0G9w",
            "title": "Baby White Noise 10 Hours | Black Screen Newborn Sleep",
            "tags": ["baby sleep","white noise","newborn","infant","black screen","lullaby"]},
  "pink": {"rt": os.environ["YT_RT_PINK"], "vid": "NYpPMJOfsJQ",
            "title": "Pink Noise 10 Hours | Black Screen Sleep Therapy",
            "tags": ["pink noise","sleep therapy","relaxation","black screen","deep sleep"]},
  "rain": {"rt": os.environ["YT_RT_RAIN"], "vid": "-EG_D3khz1E",
            "title": "Rain and Thunder Sounds 10 Hours | Black Screen Sleep",
            "tags": ["rain sounds","thunder","sleep sounds","black screen","relaxing rain","asmr"]},
}

for canal, info in CANAIS.items():
    print(f"\n=== {canal.upper()} ===")
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": CI, "client_secret": CS,
        "refresh_token": info["rt"], "grant_type": "refresh_token"
    })
    at = r.json().get("access_token")
    print(f"  AT: {bool(at)}")
    if not at:
        print(f"  ERROR: {r.json()}")
        continue

    r2 = requests.get("https://www.googleapis.com/youtube/v3/videos",
        params={"id": info["vid"], "part": "snippet,status"},
        headers={"Authorization": f"Bearer {at}"})
    items = r2.json().get("items", [])
    if not items:
        print(f"  Video {info['vid']} not found")
        continue

    snippet = items[0]["snippet"]
    print(f"  Title: {snippet.get('title','?')[:60]}")
    print(f"  mfk: {items[0]['status'].get('madeForKids')}")

    body = {
        "id": info["vid"],
        "snippet": {
            "title": info["title"],
            "description": snippet.get("description", ""),
            "categoryId": "22",
            "tags": info["tags"],
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
        }
    }
    r3 = requests.put("https://www.googleapis.com/youtube/v3/videos",
        params={"part": "snippet,status"},
        headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json"},
        json=body)
    if r3.status_code == 200:
        v = r3.json()
        print(f"  OK updated | mfk={v.get('status',{}).get('selfDeclaredMadeForKids')}")
    else:
        print(f"  FAIL {r3.status_code}: {r3.text[:200]}")

print("\n=== DONE ===")
