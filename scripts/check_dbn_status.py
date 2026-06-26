import requests, os

r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":     os.environ["YT_CLIENT_ID_2"],
    "client_secret": os.environ["YT_CLIENT_SECRET_2"],
    "refresh_token": os.environ["YOUTUBE_RT_DBN"],
    "grant_type":    "refresh_token"
})
TOKEN = r.json()["access_token"]
print("Token OK")

# Checar se ha live ativa no canal DBN
rl = requests.get(
    "https://www.googleapis.com/youtube/v3/liveBroadcasts",
    params={"part":"snippet,status","broadcastStatus":"active","broadcastType":"all"},
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
items = rl.json().get("items", [])
print(f"Lives ativas: {len(items)}")
for v in items:
    print(f"  ID:     {v['id']}")
    print(f"  Titulo: {v['snippet']['title']}")
    print(f"  Status: {v['status']['lifeCycleStatus']}")
    print(f"  URL:    https://youtube.com/watch?v={v['id']}")

# Checar broadcasts em geral (all statuses)
ra = requests.get(
    "https://www.googleapis.com/youtube/v3/liveBroadcasts",
    params={"part":"snippet,status","broadcastStatus":"all","broadcastType":"all","maxResults":5},
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
all_items = ra.json().get("items", [])
print(f"\nTodos os broadcasts ({len(all_items)}):")
for v in all_items:
    print(f"  {v['id']}  {v['status']['lifeCycleStatus']}  {v['snippet']['title'][:50]}")
