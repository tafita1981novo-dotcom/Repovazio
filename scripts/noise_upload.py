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
    "bsn":      "Baby Sleep White Noise 12 Hours - Black Screen\n\nGentle white noise for babies from birth through 12 months. Safe, consistent and effective.\n\n#BabySleep #WhiteNoise #Newborn #WombSounds #BabyCalm #12Hours #BlackScreen",
    "pink":     "Pink Noise 12 Hours - Black Screen\n\nPink noise increases deep sleep and improves memory by up to 35% (Northwestern University research).\n\n#PinkNoise #DeepSleep #Tinnitus #MemoryBoost #SleepScience #BlackScreen #12Hours",
    "rain":     "Rain Sounds 12 Hours - Black Screen\n\nHeavy continuous rain for deep sleep, study and relaxation. No thunder, no transitions.\n\n#RainSounds #SleepRain #ASMR #SleepSounds #BlackScreen #12Hours #AnxietyRelief",
    "wnv":      "White Noise 12 Hours - Black Screen\n\nPure white noise for deep sleep, baby sleep and tinnitus masking.\n\n#WhiteNoise #SleepSounds #BabySleep #Tinnitus #BlackScreen #12Hours",
    "tinnitus": "Tinnitus Relief 12 Hours - Black Screen\n\nCalibrated pink and white noise masking ringing frequencies.\n\n#Tinnitus #TinnitusRelief #RingingEars #PinkNoise #WhiteNoise #BlackScreen #12Hours",
}

# 1. BAIXAR arquivo do GitHub Release
print(f"Baixando {ASSET_NAME} do GitHub Release...")
GH_H = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}

# Buscar release
r = requests.get(f"https://api.github.com/repos/{REPO}/releases/tags/noise-videos", headers=GH_H, timeout=15)
if r.status_code != 200:
    print(f"ERRO release: {r.status_code} {r.text[:200]}")
    sys.exit(1)

release = r.json()
asset_url = None
for asset in release.get("assets", []):
    if asset["name"].upper() == ASSET_NAME.upper():
        asset_url = asset["url"]
        size_mb = asset["size"] / (1024*1024)
        print(f"Asset encontrado: {asset['name']} ({size_mb:.0f} MB)")
        break

if not asset_url:
    print(f"ERRO: {ASSET_NAME} nao encontrado no release")
    print(f"Assets disponiveis: {[a['name'] for a in release.get('assets',[])]}")
    sys.exit(1)

# Download
path = f"/tmp/{CANAL}.mp4"
r2 = requests.get(asset_url,
    headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/octet-stream"},
    stream=True, timeout=3600)

if r2.status_code != 200:
    print(f"ERRO download: {r2.status_code}")
    sys.exit(1)

downloaded = 0
with open(path, "wb") as f:
    for chunk in r2.iter_content(chunk_size=50*1024*1024):
        if chunk:
            f.write(chunk)
            downloaded += len(chunk)
            print(f"\rBaixando: {downloaded/(1024**3):.2f} GB...", end="", flush=True)
print(f"\nDownload completo: {os.path.getsize(path)/(1024**3):.2f} GB")

# 2. OBTER ACCESS TOKEN
r3 = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":CLIENT_ID,"client_secret":CLIENT_SECRET,
    "refresh_token":RT,"grant_type":"refresh_token"}, timeout=15)
at = r3.json().get("access_token")
print(f"Token: {'OK' if at else 'ERRO ' + r3.text[:100]}")
if not at: sys.exit(1)

# 3. APAGAR videos existentes
r4 = requests.get("https://www.googleapis.com/youtube/v3/channels",
    params={"part":"contentDetails,statistics","id":CHANNEL_ID},
    headers={"Authorization":f"Bearer {at}"}, timeout=10)
if r4.status_code==200 and r4.json().get("items"):
    n = int(r4.json()["items"][0]["statistics"].get("videoCount",0))
    if n > 0:
        pl = r4.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        r5 = requests.get("https://www.googleapis.com/youtube/v3/playlistItems",
            params={"part":"snippet","playlistId":pl,"maxResults":50},
            headers={"Authorization":f"Bearer {at}"}, timeout=10)
        for item in r5.json().get("items",[]):
            vid = item["snippet"]["resourceId"]["videoId"]
            rd = requests.delete("https://www.googleapis.com/youtube/v3/videos",
                params={"id":vid}, headers={"Authorization":f"Bearer {at}"}, timeout=10)
            print(f"Apagado {vid}: {rd.status_code}")
            time.sleep(0.5)

# 4. UPLOAD para YouTube
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

r6 = requests.post(
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    headers={"Authorization":f"Bearer {at}","Content-Type":"application/json",
             "X-Upload-Content-Type":"video/mp4","X-Upload-Content-Length":str(size)},
    json=meta, timeout=30)
print(f"Iniciar upload: {r6.status_code}")
if r6.status_code != 200:
    print(r6.text[:300])
    sys.exit(1)

upload_url = r6.headers["Location"]
CHUNK = 50*1024*1024
sent, video_id = 0, None

with open(path, "rb") as f:
    while sent < size:
        chunk = f.read(CHUNK)
        if not chunk: break
        end = sent+len(chunk)-1
        r7 = requests.put(upload_url,
            headers={"Authorization":f"Bearer {at}",
                     "Content-Range":f"bytes {sent}-{end}/{size}",
                     "Content-Type":"video/mp4"},
            data=chunk, timeout=600)
        sent += len(chunk)
        pct = sent/size*100
        if r7.status_code in (200,201):
            video_id = r7.json().get("id")
            print(f"\nUPLOAD COMPLETO: {video_id}")
            break
        elif r7.status_code == 308:
            print(f"\r{pct:.1f}%", end="", flush=True)
        elif r7.status_code == 503:
            time.sleep(20); sent-=len(chunk); f.seek(sent)
        else:
            print(f"\nERRO: {r7.status_code} {r7.text[:150]}")
            sys.exit(1)

if not video_id: sys.exit(1)

# 5. MONETIZACAO
time.sleep(5)
requests.put(
    "https://www.googleapis.com/youtube/v3/videos?part=monetizationDetails,status",
    headers={"Authorization":f"Bearer {at}","Content-Type":"application/json"},
    json={"id":video_id,"monetizationDetails":{"access":{"allowed":True}},
          "status":{"selfDeclaredMadeForKids":False,"madeForKids":False,
                    "license":"youtube","embeddable":True}},
    timeout=20)

# 6. SUPABASE
if SB_KEY and SB_KEY.startswith("eyJ"):
    sb_h = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json"}
    requests.patch(f"{SB_URL}/rest/v1/noise_channels?canal_key=eq.{CANAL}",
        headers=sb_h, json={"video_id":video_id,"video_uploaded":True}, timeout=10)

print(f"URL: https://youtube.com/watch?v={video_id}")
print(f"DONE: {CANAL} = {video_id}")
