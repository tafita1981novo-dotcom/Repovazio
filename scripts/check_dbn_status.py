import requests, os

r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": os.environ["YT_CLIENT_ID_2"],
    "client_secret": os.environ["YT_CLIENT_SECRET_2"],
    "refresh_token": os.environ["YOUTUBE_RT_DBN"],
    "grant_type": "refresh_token"})
TOKEN = r.json()["access_token"]

# Checar video de teste
for vid in ["-ktxYWYY_UI", "xpEdBTQUFmo", "5tLftm98WPU"]:
    rv = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={"part":"snippet,status","id":vid},
        headers={"Authorization": f"Bearer {TOKEN}"}, timeout=10)
    items = rv.json().get("items",[])
    if items:
        st = items[0]["status"]
        print(f"{vid}: EXISTE — upload={st.get('uploadStatus')} privacy={st.get('privacyStatus')} rejection={st.get('rejectionReason','none')}")
    else:
        print(f"{vid}: DELETADO/NAO ENCONTRADO")
