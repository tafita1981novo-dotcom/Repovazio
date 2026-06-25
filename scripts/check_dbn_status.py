import requests, os

r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":     os.environ["YT_CLIENT_ID_2"],
    "client_secret": os.environ["YT_CLIENT_SECRET_2"],
    "refresh_token": os.environ["YOUTUBE_RT_DBN"],
    "grant_type":    "refresh_token"
})
TOKEN = r.json()["access_token"]
print("Token: OK")

VIDEO_ID = "xpEdBTQUFmo"

# Checar video direto
rv = requests.get(
    "https://www.googleapis.com/youtube/v3/videos",
    params={"part":"snippet,status,processingDetails,contentDetails","id":VIDEO_ID},
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
items = rv.json().get("items",[])
if items:
    v = items[0]
    print(f"Titulo:     {v['snippet']['title']}")
    print(f"Privacy:    {v['status']['privacyStatus']}")
    print(f"Upload:     {v['status'].get('uploadStatus','?')}")
    print(f"Rejection:  {v['status'].get('rejectionReason','none')}")
    print(f"Failure:    {v['status'].get('failureReason','none')}")
    proc = v.get("processingDetails",{})
    print(f"Processing: {proc.get('processingStatus','?')}")
    print(f"Duracao:    {v['contentDetails'].get('duration','?')}")
else:
    print(f"VIDEO NAO ENCONTRADO: {rv.json()}")

# Listar playlist de uploads
rc = requests.get(
    "https://www.googleapis.com/youtube/v3/channels",
    params={"part":"contentDetails","mine":"true"},
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
uploads_id = rc.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
rp = requests.get(
    "https://www.googleapis.com/youtube/v3/playlistItems",
    params={"part":"snippet,status","playlistId":uploads_id,"maxResults":5},
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
print("\nVideos no canal:")
for v in rp.json().get("items",[]):
    sn = v.get("snippet",{})
    st = v.get("status",{})
    vid = sn.get("resourceId",{}).get("videoId","?")
    print(f"  {vid}  {sn.get('title','?')[:50]}  [{st.get('privacyStatus','?')}]")
