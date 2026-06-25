import requests, os, sys, time

CLIENT_ID     = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
RT            = os.environ["REFRESH_TOKEN"]
CANAL         = os.environ["CANAL"]
CHANNEL_ID    = os.environ["CHANNEL_ID"]
TITULO        = os.environ["TITULO"]
TAGS          = [t.strip() for t in os.environ.get("TAGS","").split(",") if t.strip()]
GH_TOKEN      = os.environ["GH_TOKEN"]
REPO          = os.environ["REPO"]
ASSET_NAME    = os.environ["ASSET_NAME"]
SB_URL        = os.environ.get("SUPABASE_URL","")
SB_KEY        = os.environ.get("SUPABASE_KEY","")

DESCRICOES = {
    "dbn":      "Brown Noise 12 Hours - Black Screen\n\nPure brown noise for deep sleep, ADHD focus, studying and stress relief. 12 uninterrupted hours.\n\n#BrownNoise #DeepSleep #ADHDFocus #SleepSounds #BlackScreen #12Hours",
    "adhd":     "ADHD Focus Noise 12 Hours - Black Screen\n\nCalibrated noise for ADHD brains. Brown noise supporting executive function and sustained attention.\n\n#ADHDFocus #BrownNoise #ADHD #Concentration #DeepWork #12Hours #BlackScreen",
    "bsn":      "Baby Sleep White Noise 12 Hours - Black Screen\n\nGentle white noise for babies. Safe, consistent and effective.\n\n#BabySleep #WhiteNoise #Newborn #WombSounds #12Hours #BlackScreen",
    "pink":     "Pink Noise 12 Hours - Black Screen\n\nPink noise increases deep sleep and improves memory consolidation.\n\n#PinkNoise #DeepSleep #Tinnitus #MemoryBoost #BlackScreen #12Hours",
    "rain":     "Rain Sounds 12 Hours - Black Screen\n\nHeavy continuous rain for deep sleep, study and relaxation.\n\n#RainSounds #SleepRain #ASMR #SleepSounds #BlackScreen #12Hours",
    "wnv":      "White Noise 12 Hours - Black Screen\n\nPure white noise for deep sleep, baby sleep and tinnitus masking.\n\n#WhiteNoise #SleepSounds #BabySleep #Tinnitus #BlackScreen #12Hours",
    "tinnitus": "Tinnitus Relief 12 Hours - Black Screen\n\nCalibrated noise masking ringing frequencies.\n\n#Tinnitus #TinnitusRelief #PinkNoise #WhiteNoise #BlackScreen #12Hours",
}

# 1. BAIXAR do GitHub Release
print(f"[{CANAL}] Baixando {ASSET_NAME} do GitHub Release...")
GH_H = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}

r = requests.get(
    f"https://api.github.com/repos/{REPO}/releases/tags/noise-videos",
    headers=GH_H, timeout=15)
if r.status_code != 200:
    print(f"ERRO release: {r.status_code} {r.text[:200]}")
    sys.exit(1)

asset_url = None
for asset in r.json().get("assets", []):
    if asset["name"].upper() == ASSET_NAME.upper():
        asset_url = asset["url"]
        size_total = asset["size"]
        print(f"  Encontrado: {asset['name']} ({size_total/(1024**3):.2f} GB)")
        break

if not asset_url:
    disponiveis = [a["name"] for a in r.json().get("assets", [])]
    print(f"ERRO: {ASSET_NAME} nao encontrado. Disponiveis: {disponiveis}")
    sys.exit(1)

path = f"/tmp/{CANAL}.mp4"
r2 = requests.get(asset_url,
    headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/octet-stream"},
    stream=True, timeout=3600)
if r2.status_code != 200:
    print(f"ERRO download: {r2.status_code}")
    sys.exit(1)

downloaded = 0
with open(path, "wb") as f:
    for chunk in r2.iter_content(chunk_size=32*1024*1024):
        if chunk:
            f.write(chunk)
            downloaded += len(chunk)
            print(f"\r  {downloaded/(1024**3):.2f}/{size_total/(1024**3):.2f} GB", end="", flush=True)
print(f"\n  Download OK: {os.path.getsize(path)/(1024**3):.2f} GB")

# 2. ACCESS TOKEN
r3 = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
    "refresh_token": RT, "grant_type": "refresh_token"}, timeout=15)
at = r3.json().get("access_token")
if not at:
    print(f"ERRO token: {r3.text[:150]}")
    sys.exit(1)
print("  Token OAuth: OK")

# 3. LIMPAR canal
r4 = requests.get("https://www.googleapis.com/youtube/v3/channels",
    params={"part": "contentDetails,statistics", "id": CHANNEL_ID},
    headers={"Authorization": f"Bearer {at}"}, timeout=10)
if r4.status_code == 200 and r4.json().get("items"):
    n = int(r4.json()["items"][0]["statistics"].get("videoCount", 0))
    if n > 0:
        pl = r4.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        r5 = requests.get("https://www.googleapis.com/youtube/v3/playlistItems",
            params={"part": "snippet", "playlistId": pl, "maxResults": 50},
            headers={"Authorization": f"Bearer {at}"}, timeout=10)
        for item in r5.json().get("items", []):
            vid = item["snippet"]["resourceId"]["videoId"]
            rd = requests.delete("https://www.googleapis.com/youtube/v3/videos",
                params={"id": vid}, headers={"Authorization": f"Bearer {at}"}, timeout=10)
            print(f"  Apagado {vid}: {rd.status_code}")
            time.sleep(0.5)
    else:
        print("  Canal limpo")

# 4. UPLOAD — part=snippet,status APENAS
size = os.path.getsize(path)
meta = {
    "snippet": {
        "title": TITULO,
        "description": DESCRICOES.get(CANAL, TITULO),
        "tags": TAGS,
        "categoryId": "22",
        "defaultLanguage": "en",
        "defaultAudioLanguage": "en",
    },
    "status": {
        "privacyStatus": "public",
        "selfDeclaredMadeForKids": False,
        "madeForKids": False,
        "license": "youtube",
        "embeddable": True,
        "publicStatsViewable": True,
        "notifySubscribers": True,
    }
}

print(f"  Iniciando upload ({size/(1024**3):.2f} GB)...")
r6 = requests.post(
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    headers={"Authorization": f"Bearer {at}",
             "Content-Type": "application/json",
             "X-Upload-Content-Type": "video/mp4",
             "X-Upload-Content-Length": str(size)},
    json=meta, timeout=30)

if r6.status_code != 200:
    print(f"ERRO iniciar upload: {r6.status_code} {r6.text[:300]}")
    sys.exit(1)

upload_url = r6.headers["Location"]
CHUNK = 50 * 1024 * 1024
sent, video_id = 0, None

with open(path, "rb") as f:
    while sent < size:
        chunk = f.read(CHUNK)
        if not chunk:
            break
        end = sent + len(chunk) - 1
        r7 = requests.put(upload_url,
            headers={"Authorization": f"Bearer {at}",
                     "Content-Range": f"bytes {sent}-{end}/{size}",
                     "Content-Type": "video/mp4"},
            data=chunk, timeout=600)
        sent += len(chunk)
        if r7.status_code in (200, 201):
            video_id = r7.json().get("id")
            print(f"\n  UPLOAD COMPLETO: {video_id}")
            break
        elif r7.status_code == 308:
            print(f"\r  {sent/size*100:.1f}%...", end="", flush=True)
        elif r7.status_code == 503:
            print("\n  503 retry...")
            time.sleep(20)
            sent -= len(chunk)
            f.seek(sent)
        else:
            print(f"\n  ERRO upload: {r7.status_code} {r7.text[:200]}")
            sys.exit(1)

if not video_id:
    print("ERRO: sem video_id ao final")
    sys.exit(1)

# 5. MONETIZACAO (separado do upload)
time.sleep(5)
r8 = requests.put(
    "https://www.googleapis.com/youtube/v3/videos?part=monetizationDetails,status",
    headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json"},
    json={"id": video_id,
          "monetizationDetails": {"access": {"allowed": True}},
          "status": {"selfDeclaredMadeForKids": False, "madeForKids": False,
                     "license": "youtube", "embeddable": True}},
    timeout=20)
print(f"  Monetizacao: {r8.status_code} {'OK' if r8.status_code==200 else r8.text[:100]}")

# 6. SUPABASE
if SB_KEY and len(SB_KEY) > 20:
    sb_h = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
            "Content-Type": "application/json"}
    requests.patch(f"{SB_URL}/rest/v1/noise_channels?canal_key=eq.{CANAL}",
        headers=sb_h, json={"video_id": video_id, "video_uploaded": True}, timeout=10)

print(f"\nURL: https://youtube.com/watch?v={video_id}")
print(f"DONE {CANAL.upper()} = {video_id}")
