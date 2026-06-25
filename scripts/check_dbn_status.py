import requests, os

r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":     os.environ["YT_CLIENT_ID_2"],
    "client_secret": os.environ["YT_CLIENT_SECRET_2"],
    "refresh_token": os.environ["YOUTUBE_RT_DBN"],
    "grant_type":    "refresh_token"
})
TOKEN = r.json()["access_token"]
print(f"Token: OK")

# 1. Listar todos os vídeos do canal para ver o que existe
rv = requests.get(
    "https://www.googleapis.com/youtube/v3/search",
    params={
        "part": "snippet",
        "forMine": "true",
        "type": "video",
        "maxResults": 10,
        "order": "date"
    },
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
data = rv.json()
print(f"\nVideos no canal DBN:")
items = data.get("items", [])
if items:
    for v in items:
        vid_id = v["id"]["videoId"]
        title  = v["snippet"]["title"]
        status = v["snippet"].get("liveBroadcastContent","")
        print(f"  ID:{vid_id}  {title[:60]}  [{status}]")
else:
    print(f"  Nenhum video encontrado")
    print(f"  Resposta: {data}")

# 2. Checar quota restante
rq = requests.get(
    "https://www.googleapis.com/youtube/v3/channels",
    params={"part":"snippet,status,contentDetails","mine":"true"},
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
ch = rq.json()
channels = ch.get("items",[])
if channels:
    c = channels[0]
    print(f"\nCanal: {c['snippet']['title']}")
    print(f"ID:    {c['id']}")
    print(f"Status:{c['status'].get('longUploadsStatus','?')}")
else:
    print(f"\nCanal: {ch}")
