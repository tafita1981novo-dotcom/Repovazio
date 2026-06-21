import requests, os

CI = os.environ["YT_CLIENT_ID"]
CS = os.environ["YT_CLIENT_SECRET"]

# Verificar RAIN
rt = os.environ["YT_RT_RAIN"]
r = requests.post("https://oauth2.googleapis.com/token", data={"client_id":CI,"client_secret":CS,"refresh_token":rt,"grant_type":"refresh_token"})
at = r.json().get("access_token")
print(f"RAIN AT={bool(at)}")

# Buscar via videos API
r2 = requests.get("https://www.googleapis.com/youtube/v3/videos",
    params={"id": "-EG_D3khz1E", "part": "snippet,status,processingDetails"},
    headers={"Authorization": f"Bearer {at}"})
items = r2.json().get("items", [])
print(f"RAIN found={bool(items)}")
if items:
    s = items[0]
    print(f"  title={s['snippet'].get('title','?')[:60]}")
    print(f"  mfk={s['status'].get('madeForKids')}")
    print(f"  processing={s.get('processingDetails',{}).get('processingStatus','?')}")
    print(f"  privacyStatus={s['status'].get('privacyStatus')}")
else:
    print(f"  Erro: {r2.json().get('error',{})}")

# Buscar via uploads playlist
r3 = requests.get("https://www.googleapis.com/youtube/v3/channels",
    params={"mine":"true","part":"contentDetails"},
    headers={"Authorization": f"Bearer {at}"})
if r3.json().get("items"):
    up_id = r3.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    r4 = requests.get("https://www.googleapis.com/youtube/v3/playlistItems",
        params={"playlistId": up_id, "part": "contentDetails,snippet", "maxResults": 5},
        headers={"Authorization": f"Bearer {at}"})
    for item in r4.json().get("items", []):
        print(f"  UPLOAD: {item['contentDetails']['videoId']} | {item['snippet']['title'][:50]}")
