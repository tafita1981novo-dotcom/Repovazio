import requests, os

r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":     os.environ["YT_CLIENT_ID_2"],
    "client_secret": os.environ["YT_CLIENT_SECRET_2"],
    "refresh_token": os.environ["YOUTUBE_RT_DBN"],
    "grant_type":    "refresh_token"
})
TOKEN = r.json()["access_token"]
print("Token: OK")

# 1. Checar canal
rc = requests.get(
    "https://www.googleapis.com/youtube/v3/channels",
    params={"part":"snippet,status,contentDetails","mine":"true"},
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
ch = rc.json().get("items",[])
if ch:
    c = ch[0]
    print(f"Canal:        {c['snippet']['title']}")
    print(f"Canal ID:     {c['id']}")
    print(f"LongUploads:  {c['status'].get('longUploadsStatus','?')}")
    uploads_id = c["contentDetails"]["relatedPlaylists"]["uploads"]
    print(f"Playlist up:  {uploads_id}")

    # 2. Listar videos via playlist de uploads
    rp = requests.get(
        "https://www.googleapis.com/youtube/v3/playlistItems",
        params={"part":"snippet,status","playlistId":uploads_id,"maxResults":5},
        headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
    )
    items = rp.json().get("items",[])
    print(f"\nVideos no canal ({len(items)}):")
    for v in items:
        sn = v.get("snippet",{})
        st = v.get("status",{})
        vid = sn.get("resourceId",{}).get("videoId","?")
        print(f"  ID:{vid}  {sn.get('title','?')[:50]}  [{st.get('privacyStatus','?')}]")
    if not items:
        print("  NENHUM VIDEO")
else:
    print(f"Canal nao encontrado: {rc.json()}")

# 3. Checar video especifico com todos os campos possiveis
VIDEO_ID = "5tLftm98WPU"
rv = requests.get(
    "https://www.googleapis.com/youtube/v3/videos",
    params={"part":"snippet,status,processingDetails,contentDetails","id":VIDEO_ID},
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
items2 = rv.json().get("items",[])
print(f"\nVideo {VIDEO_ID}:")
if items2:
    v2 = items2[0]
    print(f"  Titulo:     {v2['snippet']['title']}")
    print(f"  Privacy:    {v2['status']['privacyStatus']}")
    print(f"  Upload:     {v2['status'].get('uploadStatus','?')}")
    print(f"  Rejection:  {v2['status'].get('rejectionReason','none')}")
    print(f"  Failure:    {v2['status'].get('failureReason','none')}")
    proc = v2.get("processingDetails",{})
    print(f"  Processing: {proc.get('processingStatus','?')}")
    print(f"  Duracao:    {v2['contentDetails'].get('duration','?')}")
else:
    print("  VIDEO NAO ENCONTRADO NA API")
    print("  Motivos possiveis:")
    print("  1. Rejeitado por Content ID (audio duplicado)")
    print("  2. Removido por spam/massa de uploads automaticos")  
    print("  3. Canal com restricao de upload automatizado")
    print("  4. Ainda processando (privado temporariamente)")
