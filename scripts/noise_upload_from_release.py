import requests, os, sys, time, subprocess

CLIENT_ID     = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
RT            = os.environ["REFRESH_TOKEN"]
CANAL         = os.environ["CANAL"]
CHANNEL_ID    = os.environ["CHANNEL_ID"]
GH_TOKEN      = os.environ["GH_TOKEN"]
REPO          = os.environ["REPO"]
ASSET_NAME    = os.environ["ASSET_NAME"]
SB_URL        = os.environ.get("SUPABASE_URL","")
SB_KEY        = os.environ.get("SUPABASE_KEY","")

TITULOS = {
    "dbn":      "Brown Noise 12 Hours | Deep Sleep, ADHD Focus & Study Music | Black Screen No Ads",
    "adhd":     "ADHD Focus Brown Noise 10 Hours | Concentration, Deep Work & Study | Black Screen No Ads",
    "wnv":      "White Noise 8 Hours | Deep Sleep, Baby Sleep & Tinnitus Masking | Black Screen No Ads",
    "bsn":      "Baby Sleep White Noise 8 Hours | Newborn, Infant & Toddler Sleep Sounds | Black Screen No Ads",
    "pink":     "Pink Noise 10 Hours | Deep Sleep, Memory Boost & Tinnitus Relief | Black Screen No Ads",
    "tinnitus": "Tinnitus Relief 8 Hours | Pink & White Noise Masking for Ringing Ears | Black Screen No Ads",
    "rain":     "Rain Sounds 8 Hours | Heavy Rain for Deep Sleep, Study & Relaxation | Black Screen No Ads",
}

TAGS_MAP = {
    "dbn":      ["brown noise","brown noise 12 hours","brown noise sleep","brown noise ADHD","brown noise study","deep sleep sounds","ADHD focus music","focus sounds","study music","sleep sounds","black screen","sleep aid","white noise sleep","tinnitus relief","stress relief","relaxation music","deep focus","concentration music","sleep fast","insomnia relief"],
    "adhd":     ["ADHD focus","ADHD","brown noise ADHD","ADHD music","focus music","concentration music","deep work","study music","ADHD brown noise","neurodivergent","executive function","flow state","work music","adhd sounds","focus 10 hours","black screen","productivity music","study sounds","brain focus","adhd relief"],
    "wnv":      ["white noise","white noise 8 hours","white noise sleep","white noise baby","baby sleep","sleep sounds","tinnitus masking","tinnitus relief","deep sleep","insomnia","black screen","sleep aid","newborn sleep","pure white noise","sleep fast","sleep white noise","relaxing sounds","ambient noise","sleep music","noise for sleep"],
    "bsn":      ["baby sleep","white noise baby","newborn sleep","infant sleep","baby sleep sounds","womb sounds","baby calm","colic baby","baby white noise","toddler sleep","baby sleep aid","newborn white noise","baby bedtime","baby nap","baby soothing sounds","black screen","8 hours","new parents","fussy baby","baby sleep through night"],
    "pink":     ["pink noise","pink noise sleep","pink noise 10 hours","deep sleep","tinnitus relief","memory boost","sleep science","pink noise tinnitus","sleep better","slow wave sleep","anxiety relief","pure pink noise","tinnitus masking","pink noise benefits","black screen","sleep sounds","relaxation","stress relief","sleep aid","concentration"],
    "tinnitus": ["tinnitus","tinnitus relief","tinnitus masking","ringing ears","ear ringing","tinnitus sounds","pink noise tinnitus","white noise tinnitus","tinnitus help","tinnitus therapy","tinnitus sleep","tinnitus treatment","ear noise","tinnitus habituation","black screen","8 hours","ringing in ears","tinnitus noise","hearing noise","hyperacusis"],
    "rain":     ["rain sounds","rain for sleep","heavy rain","rain sounds sleep","rain sounds 8 hours","rainy night sleep","sleep rain","study rain","rain ASMR","relaxing rain","rain sounds relaxation","black screen rain","rain noise","ambient rain","deep sleep rain","anxiety relief rain","stress relief sounds","nature sounds sleep","rain sleep sounds","rain white noise"],
}

DESCRICOES = {
    "dbn": """Brown Noise 12 Hours - Black Screen | No Ads | Looped

Pure brown noise for deep sleep, ADHD focus, studying, and stress relief.
12 uninterrupted hours. Black screen to save your battery.

BEST FOR:
Deep Sleep & Insomnia Relief | ADHD Focus & Concentration
Study & Deep Work Sessions | Tinnitus Masking | Stress & Anxiety Relief

Headphones recommended | Black screen all night | 12 hours continuous

YOUR LANGUAGE:
BR/PT Ruido marrom 12 horas para sono profundo, foco TDAH e estudo
ES Ruido marron 12 horas para dormir profundo, enfoque TDAH y estudio
FR Bruit brun 12 heures pour sommeil profond, focus TDAH et etude
DE Braunes Rauschen 12 Stunden fur Tiefschlaf, ADHS-Fokus und Lernen
IT Rumore marrone 12 ore per sonno profondo, focus ADHD e studio
JP 12 - ADHD
KR 12 - ADHD
CN 12 - ADHD
IN 12 ADHD
AR 12
TR Kahverengi gurultu 12 saat derin uyku, ADHD odagi ve calisma icin

#BrownNoise #DeepSleep #ADHDFocus #SleepSounds #BlackScreen #StudyMusic #12Hours""",

    "adhd": """ADHD Focus Noise 10 Hours - Black Screen | No Ads

Calibrated brown noise for ADHD brains. Reduces mental hyperactivity,
boosts executive function and sustained attention.
10 uninterrupted hours. Black screen.

BEST FOR:
ADHD Focus & Concentration | Deep Work & Productivity
Study Sessions | Remote Work | Executive Function Support

Headphones recommended | No visual distraction | 10 hours continuous

YOUR LANGUAGE:
BR/PT Ruido marrom para foco TDAH 10 horas - trabalho e estudo
ES Ruido marron para enfoque TDAH 10 horas - trabajo y estudio
FR Bruit brun pour focus TDAH 10 heures - travail et etude
DE Braunes Rauschen fur ADHS-Fokus 10 Stunden - Arbeit und Lernen
IT Rumore marrone per focus ADHD 10 ore - lavoro e studio
JP ADHD 10
KR ADHD 10
CN ADHD 10
IN ADHD 10
AR ADHD 10
TR ADHD odak kahverengi gurultu 10 saat - is ve calisma

#ADHDFocus #ADHD #BrownNoise #Concentration #DeepWork #StudyMusic #10Hours #BlackScreen""",

    "wnv": """White Noise 8 Hours - Black Screen | No Ads | Looped

Pure uninterrupted white noise for deep sleep, baby sleep, and tinnitus masking.
8 hours. Black screen saves battery all night.

BEST FOR:
Deep Sleep & Insomnia | Baby & Newborn Sleep | Tinnitus Masking
Blocking Noisy Neighbors | Shift Workers | Naps & Travel Sleep

Medium-low volume for sleep | Black screen all night | Safe for all ages

YOUR LANGUAGE:
BR/PT Ruido branco 8 horas para sono profundo, bebes e zumbido
ES Ruido blanco 8 horas para dormir profundo, bebes y tinnitus
FR Bruit blanc 8 heures pour sommeil profond, bebe et acouphenes
DE Weisses Rauschen 8 Stunden fur Tiefschlaf, Baby und Tinnitus
IT Rumore bianco 8 ore per sonno profondo, bambino e tinnito
JP 8
KR 8
CN 8
IN 8
AR 8
TR Beyaz gurultu 8 saat derin uyku, bebek ve tinnitus icin

#WhiteNoise #SleepSounds #BabySleep #Tinnitus #BlackScreen #DeepSleep #8Hours""",

    "bsn": """Baby Sleep White Noise 8 Hours - Black Screen | No Ads

Gentle white noise for babies from birth through toddler years.
Mimics womb sounds to instantly calm and help babies sleep longer.
8 hours. Safe volume. Black screen.

BEST FOR:
Newborn & Infant Sleep | Colic & Fussy Baby Relief
Bedtime & Nap Time Routine | Toddler Sleep | Travel Sleep for Babies

Keep below 50dB for infant ears | Safe for nursery | Suitable from birth

YOUR LANGUAGE:
BR/PT Ruido branco para bebe 8 horas - recem-nascido e colica
ES Ruido blanco para bebe 8 horas - recien nacido y colico
FR Bruit blanc bebe 8 heures - nouveau-ne et coliques
DE Weisses Rauschen Baby 8 Stunden - Neugeborenes und Koliken
IT Rumore bianco bambino 8 ore - neonato e coliche
JP 8
KR 8
CN 8
IN 8
AR 8
TR Bebek beyaz gurultu 8 saat - yenidogan ve kolik

#BabySleep #WhiteNoise #NewbornSleep #WombSounds #BabyCalm #BlackScreen #8Hours""",

    "pink": """Pink Noise 10 Hours - Black Screen | No Ads | Science-Backed Sleep

Scientifically proven to increase deep sleep and improve memory consolidation.
Northwestern University research: pink noise boosts memory by up to 35%.
10 hours. Black screen.

BEST FOR:
Deep Sleep & Slow Wave Sleep | Memory Consolidation & Learning
Tinnitus Relief & Masking | Stress & Anxiety Reduction | Focus & Study

Backed by sleep science | Headphones enhance effect | 10 hours continuous

YOUR LANGUAGE:
BR/PT Ruido rosa 10 horas para sono profundo, memoria e zumbido
ES Ruido rosa 10 horas para sueno profundo, memoria y tinnitus
FR Bruit rose 10 heures pour sommeil profond, memoire et acouphenes
DE Rosarauschen 10 Stunden fur Tiefschlaf, Gedachtnis und Tinnitus
IT Rumore rosa 10 ore per sonno profondo, memoria e tinnito
JP 10
KR 10
CN 10
IN 10
AR 10
TR Pembe gurultu 10 saat derin uyku, hafiza ve tinnitus icin

#PinkNoise #DeepSleep #Tinnitus #MemoryBoost #SleepScience #BlackScreen #10Hours""",

    "tinnitus": """Tinnitus Relief 8 Hours - Black Screen | No Ads

Calibrated blend of pink and white noise to mask tinnitus frequencies.
Helps with sleep, relaxation and tinnitus habituation therapy.
8 uninterrupted hours. Black screen.

BEST FOR:
Tinnitus Masking & Relief | Sleeping with Tinnitus
Tinnitus Habituation Therapy | Ringing, Buzzing & Hissing Ear Sounds

Match volume to your tinnitus level | 8 hours full sleep cycle coverage

YOUR LANGUAGE:
BR/PT Alivio para zumbido 8 horas - ruido rosa e branco
ES Alivio para tinnitus 8 horas - ruido rosa y blanco
FR Soulagement acouphenes 8 heures - bruit rose et blanc
DE Tinnitus-Linderung 8 Stunden - Rosa und weisses Rauschen
IT Sollievo tinnito 8 ore - rumore rosa e bianco
JP 8
KR 8
CN 8
IN 8
AR 8
TR Tinnitus rahatlamasi 8 saat - pembe ve beyaz gurultu

#Tinnitus #TinnitusRelief #RingingEars #TinnitusMasking #PinkNoise #WhiteNoise #8Hours""",

    "rain": """Rain Sounds 8 Hours - Black Screen | No Ads | Heavy Rain

Heavy continuous rain for deep sleep, studying, and total relaxation.
No thunder. No gaps. No interruptions. 8 hours. Black screen.

BEST FOR:
Deep Sleep & Insomnia | Study & Focus Sessions
Relaxation & Meditation | Anxiety & Stress Relief | ASMR

Heavy rain no thunder | No light pollution | 8 hours full night coverage

YOUR LANGUAGE:
BR/PT Som de chuva 8 horas para dormir, estudar e relaxar
ES Sonidos de lluvia 8 horas para dormir, estudiar y relajarse
FR Sons de pluie 8 heures pour dormir, etudier et se detendre
DE Regengerausche 8 Stunden zum Schlafen, Lernen und Entspannen
IT Suoni di pioggia 8 ore per dormire, studiare e rilassarsi
JP 8
KR 8
CN 8
IN 8
AR 8
TR Yagmur sesleri 8 saat uyku, calisma ve rahatlama icin

#RainSounds #SleepRain #HeavyRain #ASMR #SleepSounds #BlackScreen #8Hours""",
}

print(f"[{CANAL.upper()}] Iniciando...")

# 1. BAIXAR do GitHub Release
GH_H = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
r = requests.get(f"https://api.github.com/repos/{REPO}/releases/tags/noise-videos", headers=GH_H, timeout=15)
if r.status_code != 200:
    print(f"ERRO release: {r.status_code}")
    sys.exit(1)

asset_url = None
for asset in r.json().get("assets", []):
    if asset["name"].upper() == ASSET_NAME.upper():
        asset_url = asset["url"]
        size_total = asset["size"]
        print(f"  Asset: {asset['name']} ({size_total/(1024**3):.2f} GB)")
        break

if not asset_url:
    print(f"ERRO: {ASSET_NAME} nao encontrado")
    sys.exit(1)

path_orig = f"/tmp/{CANAL}_orig.mp4"
path_final = f"/tmp/{CANAL}.mp4"

r2 = requests.get(asset_url,
    headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/octet-stream"},
    stream=True, timeout=3600)

downloaded = 0
with open(path_orig, "wb") as f:
    for chunk in r2.iter_content(chunk_size=32*1024*1024):
        if chunk:
            f.write(chunk)
            downloaded += len(chunk)
            print(f"\r  Download: {downloaded/(1024**3):.2f} GB", end="", flush=True)
print(f"\n  Download OK: {downloaded/(1024**3):.2f} GB")

# 2. FASTSTART
print("  Aplicando faststart...")
# Rodar ffmpeg sem capturar saída (evita timeout de subprocess com arquivos grandes)
# timeout 1800 = 30min (suficiente para 1.2GB opus→aac)
import shlex
cmd = ["ffmpeg", "-y", "-i", path_orig,
       "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
       "-r", "30", "-vf", "fps=30",
       "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
       "-threads", "0",
       "-movflags", "+faststart",
       path_final]
print(f"  cmd: {' '.join(cmd)}")
ret = subprocess.call(cmd, timeout=1800)
if ret != 0:
    print(f"ERRO ffmpeg: exit code {ret}")
    sys.exit(1)
print(f"  Faststart OK: {os.path.getsize(path_final)/(1024**3):.2f} GB")
os.remove(path_orig)

# 3. TOKEN
r3 = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
    "refresh_token": RT, "grant_type": "refresh_token"}, timeout=15)
at = r3.json().get("access_token")
if not at:
    print(f"ERRO token: {r3.text[:150]}")
    sys.exit(1)
print("  Token: OK")

# 4. LIMPAR canal
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
            print(f"  Apagado: {vid} ({rd.status_code})")
            time.sleep(0.5)

# 5. UPLOAD
size = os.path.getsize(path_final)
titulo = TITULOS.get(CANAL, CANAL)
tags   = TAGS_MAP.get(CANAL, [])
descr  = DESCRICOES.get(CANAL, titulo)

meta = {
    "snippet": {
        "title": titulo,
        "description": descr,
        "tags": tags,
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

print(f"  Upload: {size/(1024**3):.2f} GB | {titulo[:50]}...")
r6 = requests.post(
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json",
             "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
    json=meta, timeout=30)

if r6.status_code != 200:
    print(f"ERRO iniciar: {r6.status_code} {r6.text[:300]}")
    sys.exit(1)

upload_url = r6.headers["Location"]
CHUNK = 50 * 1024 * 1024
sent, video_id = 0, None

with open(path_final, "rb") as f:
    while sent < size:
        chunk = f.read(CHUNK)
        if not chunk: break
        end = sent + len(chunk) - 1
        r7 = requests.put(upload_url,
            headers={"Authorization": f"Bearer {at}",
                     "Content-Range": f"bytes {sent}-{end}/{size}",
                     "Content-Type": "video/mp4"},
            data=chunk, timeout=600)
        sent += len(chunk)
        if r7.status_code in (200, 201):
            video_id = r7.json().get("id")
            print(f"\n  UPLOAD OK: {video_id}")
            break
        elif r7.status_code == 308:
            print(f"\r  {sent/size*100:.1f}%", end="", flush=True)
        elif r7.status_code == 503:
            time.sleep(20); sent -= len(chunk); f.seek(sent)
        else:
            print(f"\n  ERRO: {r7.status_code} {r7.text[:200]}")
            sys.exit(1)

if not video_id:
    print("ERRO: sem video_id")
    sys.exit(1)

# 6. MONETIZACAO
time.sleep(5)
r8 = requests.put(
    "https://www.googleapis.com/youtube/v3/videos?part=monetizationDetails,status",
    headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json"},
    json={"id": video_id,
          "monetizationDetails": {"access": {"allowed": True}},
          "status": {"selfDeclaredMadeForKids": False, "madeForKids": False,
                     "license": "youtube", "embeddable": True}},
    timeout=20)
print(f"  Monetizacao: {r8.status_code}")

# 7. SUPABASE
if SB_KEY and len(SB_KEY) > 20:
    sb_h = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}", "Content-Type": "application/json"}
    requests.patch(f"{SB_URL}/rest/v1/noise_channels?canal_key=eq.{CANAL}",
        headers=sb_h, json={"video_id": video_id, "video_uploaded": True}, timeout=10)

print(f"\n  URL: https://youtube.com/watch?v={video_id}")
print(f"  DONE {CANAL.upper()} = {video_id}")
