import requests, os

VIDEO_ID = "5tLftm98WPU"

r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":     os.environ["YT_CLIENT_ID_2"],
    "client_secret": os.environ["YT_CLIENT_SECRET_2"],
    "refresh_token": os.environ["YOUTUBE_RT_DBN"],
    "grant_type":    "refresh_token"
})
TOKEN = r.json()["access_token"]
print(f"Token: OK")

rv = requests.get(
    "https://www.googleapis.com/youtube/v3/videos",
    params={"part":"snippet,status,contentDetails,processingDetails","id":VIDEO_ID},
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
data  = rv.json()
items = data.get("items", [])

if not items:
    print(f"VIDEO NAO ENCONTRADO — pode ter sido removido ou rejeitado")
    print(f"Resposta API: {data}")
else:
    v = items[0]
    print(f"Titulo:     {v['snippet']['title']}")
    print(f"Status:     {v['status']['privacyStatus']}")
    print(f"Upload:     {v['status'].get('uploadStatus','?')}")
    print(f"Rejeicao:   {v['status'].get('rejectionReason','nenhuma')}")
    print(f"Falha:      {v['status'].get('failureReason','nenhuma')}")
    print(f"Duracao:    {v['contentDetails'].get('duration','?')}")
    proc = v.get('processingDetails',{})
    print(f"Processing: {proc.get('processingStatus','?')}")
    print(f"URL:        https://youtube.com/watch?v={VIDEO_ID}")
