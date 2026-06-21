import requests, os

CI = os.environ["YT_CLIENT_ID"]
CS = os.environ["YT_CLIENT_SECRET"]

CANAIS = {
    "bsn":  {"rt_env": "YT_RT_BSN",  "ch": "UCy4d2yt8eRywJS7PMTDX3xA", "target_vid": "dGdrOUA0G9w",
             "title": "Baby White Noise 10 Hours | Black Screen Newborn Sleep",
             "tags": ["baby sleep","white noise","newborn","infant","black screen","lullaby"]},
    "pink": {"rt_env": "YT_RT_PINK", "ch": "UCXQ_-FOGTJk17T06gy0bYqQ", "target_vid": "NYpPMJOfsJQ",
             "title": "Pink Noise 10 Hours | Black Screen Sleep Therapy",
             "tags": ["pink noise","sleep therapy","relaxation","black screen","deep sleep"]},
}

for canal, info in CANAIS.items():
    rt = os.environ[info["rt_env"]]
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": CI, "client_secret": CS,
        "refresh_token": rt, "grant_type": "refresh_token"
    })
    at = r.json().get("access_token")
    print(f"\n=== {canal.upper()} AT={bool(at)} ===")
    if not at: continue

    # Buscar canal e playlist de uploads
    r2 = requests.get("https://www.googleapis.com/youtube/v3/channels",
        params={"mine": "true", "part": "contentDetails,snippet"},
        headers={"Authorization": f"Bearer {at}"})
    items = r2.json().get("items", [])
    if not items: print("  No channel"); continue
    ch_name = items[0]["snippet"]["title"]
    uploads_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    print(f"  Canal: {ch_name}")

    # Buscar últimos vídeos
    r3 = requests.get("https://www.googleapis.com/youtube/v3/playlistItems",
        params={"playlistId": uploads_id, "part": "contentDetails,snippet", "maxResults": 5},
        headers={"Authorization": f"Bearer {at}"})
    pl_items = r3.json().get("items", [])
    print(f"  Total uploads: {r3.json().get('pageInfo',{}).get('totalResults','?')}")
    for item in pl_items:
        vid_id = item["contentDetails"]["videoId"]
        title = item["snippet"]["title"]
        status = item["snippet"].get("videoPublishedAt", "?")
        print(f"  VIDEO: {vid_id} | {title[:50]} | pub={status[:10]}")

    # Tentar update no target_vid
    target = info["target_vid"]
    r4 = requests.get("https://www.googleapis.com/youtube/v3/videos",
        params={"id": target, "part": "snippet,status"},
        headers={"Authorization": f"Bearer {at}"})
    v_items = r4.json().get("items", [])
    if v_items:
        snippet = v_items[0]["snippet"]
        body = {
            "id": target,
            "snippet": {"title": info["title"], "description": snippet.get("description",""),
                        "categoryId": "22", "tags": info["tags"]},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "madeForKids": False}
        }
        r5 = requests.put("https://www.googleapis.com/youtube/v3/videos",
            params={"part": "snippet,status"},
            headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json"},
            json=body)
        if r5.status_code == 200:
            print(f"  OK UPDATED {target}")
        else:
            print(f"  FAIL {r5.status_code}: {r5.text[:150]}")
    else:
        print(f"  Target {target} not found via videos API (may still be processing)")
