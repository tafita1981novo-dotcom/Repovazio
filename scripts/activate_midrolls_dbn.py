import requests, os

VIDEO_ID = "5tLftm98WPU"

r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":     os.environ["YT_CLIENT_ID_2"],
    "client_secret": os.environ["YT_CLIENT_SECRET_2"],
    "refresh_token": os.environ["YOUTUBE_RT_DBN"],
    "grant_type":    "refresh_token"
})
TOKEN = r.json()["access_token"]
print("Token OK")

# Verificar video
rv = requests.get(
    "https://www.googleapis.com/youtube/v3/videos",
    params={"part":"snippet,status,contentDetails","id":VIDEO_ID},
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
data  = rv.json()
items = data.get("items", [])

if items:
    v = items[0]
    print(f"Titulo:  {v['snippet']['title']}")
    print(f"Status:  {v['status']['privacyStatus']}")
    print(f"Duracao: {v['contentDetails']['duration']}")
else:
    print(f"Video ainda processando ou nao encontrado: {data}")

print(f"URL: https://youtube.com/watch?v={VIDEO_ID}")

# Tentar ativar monetizacao
rm = requests.put(
    f"https://www.googleapis.com/youtube/v3/videos?part=monetizationDetails",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={
        "id": VIDEO_ID,
        "monetizationDetails": {"access": {"allowed": True}}
    }, timeout=15
)
print(f"Monetizacao: {rm.status_code} — {rm.text[:150]}")
print("\nDone!")
