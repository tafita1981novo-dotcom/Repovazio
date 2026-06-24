import requests, os, time, sys

CLIENT_ID     = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
RT            = os.environ["REFRESH_TOKEN"]
CANAL         = os.environ["CANAL"]
CHANNEL_ID    = os.environ["CHANNEL_ID"]
TITULO        = os.environ["TITULO"]
TAGS          = [t.strip() for t in os.environ.get("TAGS","").split(",") if t.strip()]
SB_URL        = os.environ.get("SUPABASE_URL","")
SB_KEY        = os.environ.get("SUPABASE_KEY","")

DESCRICOES = {
    "dbn":  "Brown Noise 12 Hours - Black Screen\n\nPure brown noise for deep sleep, ADHD focus, studying and stress relief.\n\n#BrownNoise #DeepSleep #ADHDFocus #SleepSounds #BlackScreen #12Hours",
    "adhd": "ADHD Focus Noise 12 Hours - Black Screen\n\nCalibrated noise for ADHD brains. Brown noise supporting executive function.\n\n#ADHDFocus #BrownNoise #ADHD #Concentration #DeepWork #12Hours",
    "bsn":  "Baby Sleep White Noise 12 Hours - Black Screen\n\nGentle white noise for babies from birth through 12 months.\n\n#BabySleep #WhiteNoise #Newborn #WombSounds #BabyCalm #12Hours",
    "pink": "Pink Noise 12 Hours - Black Screen\n\nPink noise increases deep sleep and improves memory by up to 35%.\n\n#PinkNoise #DeepSleep #Tinnitus #MemoryBoost #SleepScience #12Hours",
    "rain": "Rain Sounds 12 Hours - Black Screen\n\nHeavy continuous rain for deep sleep, study and relaxation.\n\n#RainSounds #SleepRain #ASMR #SleepSounds #BlackScreen #12Hours",
}

# Access token
r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":CLIENT_ID,"client_secret":CLIENT_SECRET,
    "refresh_token":RT,"grant_type":"refresh_token"}, timeout=15)
at = r.json().get("access_token")
print(f"Token: {'OK' if at else 'ERRO'}")
if not at:
    print(r.text[:200])
    sys.exit(1)

# Apagar videos existentes
r2 = requests.get("https://www.googleapis.com/youtube/v3/channels",
    params={"part":"contentDetails,statistics","id":CHANNEL_ID},
    headers={"Authorization":f"Bearer {at}"}, timeout=10)
if r2.status_code==200 and r2.json().get("items"):
    n = int(r2.json()["items"][0]["statistics"].get("videoCount",0))
    print(f"Videos existentes: {n}")
    if n > 0:
        pl = r2.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        r3 = requests.get("https://www.googleapis.com/youtube/v3/playlistItems",
            params={"part":"snippet","playlistId":pl,"maxResults":50},
            headers={"Authorization":f"Bearer {at}"}, timeout=10)
        for item in r3.json().get("items",[]):
            vid = item["snippet"]["resourceId"]["videoId"]
            rd = requests.delete("https://www.googleapis.com/youtube/v3/videos",
                params={"id":vid},headers={"Authorization":f"Bearer {at}"},timeout=10)
            print(f"Apagado {vid}: {rd.status_code}")
            time.sleep(0.5)

# Upload
path = f"/tmp/{CANAL}.mp4"
size = os.path.getsize(path)
print(f"Arquivo: {size/(1024**3):.2f} GB")

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

r4 = requests.post(
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    headers={"Authorization":f"Bearer {at}","Content-Type":"application/json",
             "X-Upload-Content-Type":"video/mp4","X-Upload-Content-Length":str(size)},
    json=meta, timeout=30)
print(f"Iniciar upload: {r4.status_code}")
if r4.status_code != 200:
    print(r4.text[:300])
    sys.exit(1)

upload_url = r4.headers["Location"]
CHUNK = 50*1024*1024
sent, video_id = 0, None

with open(path, "rb") as f:
    while sent < size:
        chunk = f.read(CHUNK)
        if not chunk: break
        end = sent+len(chunk)-1
        r5 = requests.put(upload_url,
            headers={"Authorization":f"Bearer {at}",
                     "Content-Range":f"bytes {sent}-{end}/{size}",
                     "Content-Type":"video/mp4"},
            data=chunk, timeout=600)
        sent += len(chunk)
        pct = sent/size*100
        if r5.status_code in (200,201):
            video_id = r5.json().get("id")
            print(f"\nUPLOAD COMPLETO: {video_id}")
            break
        elif r5.status_code == 308:
            print(f"\r{pct:.1f}%", end="", flush=True)
        elif r5.status_code == 503:
            time.sleep(20); sent-=len(chunk); f.seek(sent)
        else:
            print(f"\nERRO chunk: {r5.status_code} {r5.text[:150]}")
            sys.exit(1)

if not video_id:
    print("Upload falhou")
    sys.exit(1)

# Monetizacao
time.sleep(5)
r6 = requests.put(
    "https://www.googleapis.com/youtube/v3/videos?part=monetizationDetails,status",
    headers={"Authorization":f"Bearer {at}","Content-Type":"application/json"},
    json={"id":video_id,"monetizationDetails":{"access":{"allowed":True}},
          "status":{"selfDeclaredMadeForKids":False,"madeForKids":False,"license":"youtube","embeddable":True}},
    timeout=20)
print(f"Monetizacao: {r6.status_code}")

# Supabase
if SB_KEY and SB_KEY.startswith("eyJ"):
    sb_h = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json"}
    requests.patch(f"{SB_URL}/rest/v1/noise_channels?canal_key=eq.{CANAL}",
        headers=sb_h, json={"video_id":video_id,"video_uploaded":True}, timeout=10)

print(f"URL: https://youtube.com/watch?v={video_id}")
print(f"DONE: {CANAL} = {video_id}")
