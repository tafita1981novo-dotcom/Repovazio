import requests, os

CI = os.environ["YT_CLIENT_ID"]
CS = os.environ["YT_CLIENT_SECRET"]

VIDS = {
    "bsn":  {"rt_env": "YT_RT_BSN",  "vid": "dGdrOUA0G9w",
             "title": "Baby White Noise 10 Hours | Black Screen Newborn Sleep",
             "tags": ["baby sleep","white noise","newborn","infant","black screen","lullaby"]},
    "pink": {"rt_env": "YT_RT_PINK", "vid": "NYpPMJOfsJQ",
             "title": "Pink Noise 10 Hours | Black Screen Sleep Therapy",
             "tags": ["pink noise","sleep therapy","relaxation","black screen","deep sleep"]},
}

for canal, info in VIDS.items():
    rt = os.environ[info["rt_env"]]
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": CI, "client_secret": CS,
        "refresh_token": rt, "grant_type": "refresh_token"
    })
    at = r.json().get("access_token")
    print(f"{canal} AT={bool(at)}")
    if not at: print(r.json()); continue

    r2 = requests.get("https://www.googleapis.com/youtube/v3/videos",
        params={"id": info["vid"], "part": "snippet,status,processingDetails"},
        headers={"Authorization": f"Bearer {at}"})
    items = r2.json().get("items", [])
    print(f"  vid={info['vid']} found={bool(items)}")
    if items:
        s = items[0]
        print(f"  title={s['snippet'].get('title','?')[:60]}")
        print(f"  mfk={s['status'].get('madeForKids')} selfDecl={s['status'].get('selfDeclaredMadeForKids')}")
        proc = s.get("processingDetails", {})
        print(f"  processing={proc.get('processingStatus','?')}")
        # Tentar update
        body = {
            "id": info["vid"],
            "snippet": {
                "title": info["title"],
                "description": s["snippet"].get("description", ""),
                "categoryId": "22",
                "tags": info["tags"],
            },
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "madeForKids": False}
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
    else:
        err = r2.json().get("error", {})
        print(f"  Error: {err.get('message','?')} code={err.get('code','?')}")
