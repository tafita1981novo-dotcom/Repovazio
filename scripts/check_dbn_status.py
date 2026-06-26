import requests, os

r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":     os.environ["YT_CLIENT_ID_2"],
    "client_secret": os.environ["YT_CLIENT_SECRET_2"],
    "refresh_token": os.environ["YOUTUBE_RT_DBN"],
    "grant_type":    "refresh_token"
})
TOKEN = r.json()["access_token"]

# Checar o video de teste 30s privado que subimos
TEST_ID = "-ktxYWYY_UI"
rv = requests.get(
    "https://www.googleapis.com/youtube/v3/videos",
    params={"part":"snippet,status,processingDetails","id":TEST_ID},
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
items = rv.json().get("items",[])
if items:
    v = items[0]
    print(f"TEST 30s:   EXISTE")
    print(f"Upload:     {v['status'].get('uploadStatus','?')}")
    print(f"Privacy:    {v['status']['privacyStatus']}")
    print(f"Rejection:  {v['status'].get('rejectionReason','none')}")
    proc = v.get("processingDetails",{})
    print(f"Processing: {proc.get('processingStatus','?')}")
else:
    print(f"TEST 30s:   DELETADO TAMBEM")

# Checar canal
rc = requests.get(
    "https://www.googleapis.com/youtube/v3/channels",
    params={"part":"snippet,status","mine":"true"},
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
for c in rc.json().get("items",[]):
    print(f"\nCanal: {c['snippet']['title']}")
    print(f"LongUploads: {c['status'].get('longUploadsStatus')}")
    print(f"IsLinked:    {c['status'].get('isLinked')}")
