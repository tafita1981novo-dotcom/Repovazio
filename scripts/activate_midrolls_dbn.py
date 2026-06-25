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
v = rv.json()["items"][0]
print(f"Titulo:   {v['snippet']['title']}")
print(f"Status:   {v['status']['privacyStatus']}")
print(f"Duracao:  {v['contentDetails']['duration']}")
print(f"URL:      https://youtube.com/watch?v={VIDEO_ID}")

# Ativar monetizacao com mid-rolls a cada 300s (5 min)
# 12h = 43200s → mid-rolls em: 300,600,900...43200 = 144 mid-rolls max
# YouTube limita a cada 5min → usaremos cue points
rm = requests.put(
    f"https://www.googleapis.com/youtube/v3/videos?part=monetizationDetails",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={
        "id": VIDEO_ID,
        "monetizationDetails": {
            "access": {"allowed": True}
        }
    }, timeout=15
)
print(f"Monetizacao API: {rm.status_code} — {rm.text[:100]}")

# Mid-rolls via liveBroadcast adInsertionDetails nao disponivel na API publica
# Confirmar que o video esta publico e elegivel para ads
print("\nPara mid-rolls automaticos:")
print("  YouTube Studio > Conteudo > Video > Monetizacao")
print("  Ativar 'Intervalos durante o video' (automatico)")
print(f"  Em video de 12h = ~47 mid-rolls automaticos")
print(f"\nVideo ID salvo: {VIDEO_ID}")
print(f"URL: https://youtube.com/watch?v={VIDEO_ID}")
