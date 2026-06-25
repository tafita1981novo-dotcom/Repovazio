import requests, os, sys, time, subprocess

CLIENT_ID     = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
RT            = os.environ["REFRESH_TOKEN"]
CANAL         = os.environ["CANAL"]
CHANNEL_ID    = os.environ["CHANNEL_ID"]
TITULO        = TITULOS.get(CANAL, os.environ.get("TITULO", CANAL))
TAGS          = TAGS_MAP.get(CANAL, [t.strip() for t in os.environ.get("TAGS","").split(",") if t.strip()])
GH_TOKEN      = os.environ["GH_TOKEN"]
REPO          = os.environ["REPO"]
ASSET_NAME    = os.environ["ASSET_NAME"]
SB_URL        = os.environ.get("SUPABASE_URL","")
SB_KEY        = os.environ.get("SUPABASE_KEY","")

TITULOS = {
    "dbn": "Brown Noise 12 Hours | Deep Sleep, ADHD Focus & Study Music | Black Screen No Ads",
    "adhd": "ADHD Focus Brown Noise 12 Hours | Concentration, Deep Work & Study | Black Screen No Ads",
    "wnv": "White Noise 12 Hours | Deep Sleep, Baby Sleep & Tinnitus Masking | Black Screen No Ads",
    "bsn": "Baby Sleep White Noise 12 Hours | Newborn, Infant & Toddler Sleep Sounds | Black Screen No Ads",
    "pink": "Pink Noise 12 Hours | Deep Sleep, Memory Boost & Tinnitus Relief | Black Screen No Ads",
    "tinnitus": "Tinnitus Relief 12 Hours | Pink & White Noise Masking for Ringing Ears | Black Screen No Ads",
    "rain": "Rain Sounds 12 Hours | Heavy Rain for Deep Sleep, Study & Relaxation | Black Screen No Ads",
}

TAGS_MAP = {
    "dbn": ["brown noise", "brown noise 12 hours", "brown noise sleep", "brown noise ADHD", "brown noise study", "deep sleep sounds", "ADHD focus music", "focus sounds", "study music", "sleep sounds", "black screen", "sleep aid", "white noise sleep", "tinnitus relief", "stress relief", "relaxation music", "deep focus", "concentration music", "sleep fast", "insomnia relief"],
    "adhd": ["ADHD focus", "ADHD", "brown noise ADHD", "ADHD music", "focus music", "concentration music", "deep work", "study music", "ADHD brown noise", "neurodivergent", "executive function", "flow state", "work music", "adhd sounds", "focus 12 hours", "black screen", "productivity music", "study sounds", "brain focus", "adhd relief"],
    "wnv": ["white noise", "white noise 12 hours", "white noise sleep", "white noise baby", "baby sleep", "sleep sounds", "tinnitus masking", "tinnitus relief", "deep sleep", "insomnia", "black screen", "sleep aid", "newborn sleep", "pure white noise", "sleep fast", "sleep white noise", "relaxing sounds", "ambient noise", "sleep music", "noise for sleep"],
    "bsn": ["baby sleep", "white noise baby", "newborn sleep", "infant sleep", "baby sleep sounds", "womb sounds", "baby calm", "colic baby", "baby white noise", "toddler sleep", "baby sleep aid", "newborn white noise", "baby bedtime", "baby nap", "baby soothing sounds", "black screen", "12 hours", "new parents", "fussy baby", "baby sleep through night"],
    "pink": ["pink noise", "pink noise sleep", "pink noise 12 hours", "deep sleep", "tinnitus relief", "memory boost", "sleep science", "pink noise tinnitus", "sleep better", "slow wave sleep", "anxiety relief", "pure pink noise", "tinnitus masking", "pink noise benefits", "black screen", "sleep sounds", "relaxation", "stress relief", "sleep aid", "concentration"],
    "tinnitus": ["tinnitus", "tinnitus relief", "tinnitus masking", "ringing ears", "ear ringing", "tinnitus sounds", "pink noise tinnitus", "white noise tinnitus", "tinnitus help", "tinnitus therapy", "tinnitus sleep", "tinnitus treatment", "ear noise", "tinnitus habituation", "tinnitus cure", "black screen", "12 hours", "ringing in ears", "tinnitus noise", "hearing noise"],
    "rain": ["rain sounds", "rain for sleep", "heavy rain", "rain sounds sleep", "rain sounds 12 hours", "rainy night sleep", "sleep rain", "study rain", "rain ASMR", "relaxing rain", "rain sounds relaxation", "rain and thunder", "black screen rain", "rain noise", "ambient rain", "deep sleep rain", "anxiety relief rain", "stress relief sounds", "nature sounds sleep", "rain sleep sounds"],
}

DESCRICOES = {
    "dbn": """🟫 BROWN NOISE 12 HOURS — Black Screen | No Ads | Looped

Pure brown noise for deep sleep, ADHD focus, studying, and stress relief.
12 uninterrupted hours. Black screen to save your battery.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• Deep Sleep & Insomnia Relief
• ADHD Focus & Concentration
• Study & Deep Work Sessions
• Tinnitus Masking
• Stress & Anxiety Relief
• Baby Sleep
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Headphones recommended for best effect
⚫ Black screen — screen stays dark all night
🔊 Set volume to a comfortable level
⏰ 12 hours — sleep all night without interruption
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 OUTROS IDIOMAS / OTHER LANGUAGES:
🇧🇷 Ruído marrom 12 horas para sono profundo, foco TDAH e estudo
🇪🇸 Ruido marrón 12 horas para dormir profundo, enfoque TDAH y estudio
🇫🇷 Bruit brun 12 heures pour sommeil profond, focus TDAH et étude
🇩🇪 Braunes Rauschen 12 Stunden für Tiefschlaf, ADHS-Fokus und Lernen
🇯🇵 ブラウンノイズ12時間 — 深い眠り・ADHD集中・勉強用
🇰🇷 브라운 노이즈 12시간 — 깊은 수면, ADHD 집중, 공부
🇮🇳 ब्राउन नॉइज़ 12 घंटे — गहरी नींद, ADHD फोकस, पढ़ाई
🇨🇳 棕色噪音12小时 — 深度睡眠、ADHD专注、学习
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#BrownNoise #DeepSleep #ADHDFocus #SleepSounds #BlackScreen #StudyMusic
#WhiteNoise #FocusMusic #Insomnia #SleepAid #12Hours #Concentration
#TinnitusRelief #StressRelief #RelaxingSound #DeepWork
""",
    "adhd": """🧠 ADHD FOCUS NOISE 12 HOURS — Black Screen | No Ads

Calibrated brown noise specifically for ADHD brains.
Reduces mental hyperactivity, boosts executive function and sustained attention.
12 uninterrupted hours. Black screen saves battery.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• ADHD Focus & Concentration
• Deep Work & Productivity
• Study Sessions & Homework
• Remote Work
• Anxiety & Restlessness Relief
• Executive Function Support
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Best with headphones or earbuds
⚫ Black screen — no visual distraction
🔊 Medium volume for best focus effect
⏰ 12 hours continuous
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 OUTROS IDIOMAS / OTHER LANGUAGES:
🇧🇷 Ruído marrom para foco TDAH 12 horas — trabalho e estudo
🇪🇸 Ruido marrón para enfoque TDAH 12 horas — trabajo y estudio
🇫🇷 Bruit brun pour focus TDAH 12 heures — travail et étude
🇩🇪 Braunes Rauschen für ADHS-Fokus 12 Stunden
🇯🇵 ADHD集中用ブラウンノイズ12時間 — 勉強・仕事
🇰🇷 ADHD 집중 브라운 노이즈 12시간 — 공부, 작업
🇮🇳 ADHD फोकस ब्राउन नॉइज़ 12 घंटे — पढ़ाई और काम
🇨🇳 ADHD专注棕色噪音12小时 — 学习和工作
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#ADHDFocus #ADHD #BrownNoise #Concentration #DeepWork #StudyMusic
#Neurodivergent #ExecutiveFunction #FlowState #FocusMusic #BlackScreen
#ProductivityMusic #WorkMusic #ADHDRelief #12Hours #BrainFocus
""",
    "wnv": """⬜ WHITE NOISE 12 HOURS — Black Screen | No Ads | Looped

Pure uninterrupted white noise for deep sleep, baby sleep, and tinnitus masking.
The most universally effective sleep sound.
12 hours. Black screen saves battery all night.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• Deep Sleep & Insomnia
• Baby & Newborn Sleep
• Tinnitus Masking
• Blocking Noisy Neighbors
• Shift Workers & Light Sleepers
• Naps & Travel Sleep
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Medium-low volume recommended for sleep
⚫ Black screen — stays dark all night
👶 Safe for all ages including infants
⏰ 12 hours continuous
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 OUTROS IDIOMAS / OTHER LANGUAGES:
🇧🇷 Ruído branco 12 horas para sono profundo, bebês e zumbido
🇪🇸 Ruido blanco 12 horas para dormir profundo, bebés y tinnitus
🇫🇷 Bruit blanc 12 heures pour sommeil profond, bébé et acouphènes
🇩🇪 Weißes Rauschen 12 Stunden für Tiefschlaf, Baby und Tinnitus
🇯🇵 ホワイトノイズ12時間 — 深い眠り・赤ちゃん・耳鳴り
🇰🇷 화이트 노이즈 12시간 — 깊은 수면, 아기 수면, 이명
🇮🇳 सफेद शोर 12 घंटे — गहरी नींद, बच्चे और टिनिटस
🇨🇳 白噪音12小时 — 深度睡眠、婴儿睡眠、耳鸣
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#WhiteNoise #SleepSounds #BabySleep #Tinnitus #BlackScreen #DeepSleep
#Insomnia #SleepAid #NewbornSleep #TinnitusMasking #12Hours #RelaxingSounds
#AmbientNoise #SleepMusic #PureWhiteNoise #NoisyNeighbors
""",
    "bsn": """👶 BABY SLEEP WHITE NOISE 12 HOURS — Black Screen | No Ads

Gentle white noise specially for babies from birth through toddler years.
Mimics womb sounds to instantly calm and help babies sleep longer.
12 hours. Safe volume. Black screen.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• Newborn & Infant Sleep
• Colic & Fussy Baby Relief
• Bedtime & Nap Time Routine
• Toddler Sleep
• Parents Sleeping Too
• Travel & Hotel Sleep for Babies
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Keep below 50dB for infant ears
⚫ Black screen — safe for nursery
👶 Suitable from birth
⏰ 12 hours — won't stop before morning
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 OUTROS IDIOMAS / OTHER LANGUAGES:
🇧🇷 Ruído branco para bebê 12 horas — recém-nascido e cólica
🇪🇸 Ruido blanco para bebé 12 horas — recién nacido y cólico
🇫🇷 Bruit blanc bébé 12 heures — nouveau-né et coliques
🇩🇪 Weißes Rauschen Baby 12 Stunden — Neugeborenes und Koliken
🇯🇵 赤ちゃん ホワイトノイズ12時間 — 新生児・コリック
🇰🇷 아기 화이트 노이즈 12시간 — 신생아 및 영아 수면
🇮🇳 बच्चे की नींद के लिए सफेद शोर 12 घंटे
🇨🇳 婴儿白噪音12小时 — 新生儿和婴幼儿睡眠
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#BabySleep #WhiteNoise #NewbornSleep #WombSounds #BabyCalm #BlackScreen
#InfantSleep #CosmicSleep #ToddlerSleep #BabySounds #12Hours #NewParents
#FussyBaby #BabyBedtime #BabyNap #SleepThroughTheNight
""",
    "pink": """🩷 PINK NOISE 12 HOURS — Black Screen | No Ads | Science-Backed Sleep

Pink noise is scientifically proven to increase deep sleep and improve memory consolidation.
Research from Northwestern University shows pink noise can boost memory by up to 35%.
12 hours. Black screen.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• Deep Sleep & Slow Wave Sleep
• Memory Consolidation & Learning
• Tinnitus Relief & Masking
• Stress & Anxiety Reduction
• Focus & Study
• Relaxation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 Backed by sleep science research
🎧 Headphones enhance the effect
⚫ Full black screen — 12 hour dark mode
⏰ Continuous — no interruptions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 OUTROS IDIOMAS / OTHER LANGUAGES:
🇧🇷 Ruído rosa 12 horas para sono profundo, memória e zumbido
🇪🇸 Ruido rosa 12 horas para sueño profundo, memoria y tinnitus
🇫🇷 Bruit rose 12 heures pour sommeil profond, mémoire et acouphènes
🇩🇪 Rosarauschen 12 Stunden für Tiefschlaf, Gedächtnis und Tinnitus
🇯🇵 ピンクノイズ12時間 — 深い眠り・記憶力・耳鳴り
🇰🇷 핑크 노이즈 12시간 — 깊은 수면, 기억력, 이명
🇮🇳 गुलाबी शोर 12 घंटे — गहरी नींद, स्मृति और टिनिटस
🇨🇳 粉红噪音12小时 — 深度睡眠、记忆力和耳鸣
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#PinkNoise #DeepSleep #Tinnitus #MemoryBoost #SleepScience #BlackScreen
#SlowWaveSleep #TinnitusRelief #AnxietyRelief #12Hours #SleepSounds
#PinkNoiseSleep #SleepBetter #NorthwesternUniversity #Relaxation
""",
    "tinnitus": """👂 TINNITUS RELIEF 12 HOURS — Black Screen | No Ads

Carefully calibrated blend of pink and white noise designed to mask tinnitus frequencies.
Helps with sleep, relaxation and tinnitus habituation therapy.
12 uninterrupted hours. Black screen.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• Tinnitus Masking & Relief
• Sleeping with Tinnitus
• Tinnitus Habituation Therapy
• Focus & Work with Tinnitus
• Ringing, Buzzing & Hissing Ear Sounds
• Hyperacusis Relief
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Match volume to your tinnitus level
⚫ Black screen — optimal for sleeping
⏰ 12 hours — covers full sleep cycle
💡 Tip: Use at a volume just below your tinnitus
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 OUTROS IDIOMAS / OTHER LANGUAGES:
🇧🇷 Alívio para zumbido no ouvido 12 horas — ruído rosa e branco
🇪🇸 Alivio para tinnitus 12 horas — ruido rosa y blanco
🇫🇷 Soulagement acouphènes 12 heures — bruit rose et blanc
🇩🇪 Tinnitus-Linderung 12 Stunden — Rosa und weißes Rauschen
🇯🇵 耳鳴り緩和ノイズ12時間 — ピンク&ホワイトノイズ
🇰🇷 이명 완화 소리 12시간 — 핑크 및 화이트 노이즈
🇮🇳 कान बजने से राहत 12 घंटे — गुलाबी और सफेद शोर
🇨🇳 耳鸣缓解噪音12小时 — 粉红色和白色噪音
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#Tinnitus #TinnitusRelief #RingingEars #TinnitusMasking #PinkNoise
#WhiteNoise #TinnitusTherapy #SleepWithTinnitus #EarRinging #BlackScreen
#TinnitusHabituation #12Hours #Hyperacusis #TinnitusTreatment #EarNoise
""",
    "rain": """🌧️ RAIN SOUNDS 12 HOURS — Black Screen | No Ads | Heavy Rain

Heavy continuous rain sounds for deep sleep, studying, and total relaxation.
No thunder. No gaps. No interruptions.
12 hours. Black screen saves battery.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• Deep Sleep & Insomnia
• Study & Focus Sessions
• Relaxation & Meditation
• Anxiety & Stress Relief
• ASMR & Rain Lovers
• Background Ambience for Work
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌧️ Heavy rain — no thunder
⚫ Black screen — no light pollution
🎧 Headphones for full immersion
⏰ 12 hours — full night coverage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 OUTROS IDIOMAS / OTHER LANGUAGES:
🇧🇷 Som de chuva 12 horas para dormir, estudar e relaxar
🇪🇸 Sonidos de lluvia 12 horas para dormir, estudiar y relajarse
🇫🇷 Sons de pluie 12 heures pour dormir, étudier et se détendre
🇩🇪 Regengeräusche 12 Stunden zum Schlafen, Lernen und Entspannen
🇯🇵 雨音12時間 — 深い眠り・勉強・リラックス
🇰🇷 빗소리 12시간 — 깊은 수면, 공부, 휴식
🇮🇳 बारिश की आवाज़ 12 घंटे — नींद, पढ़ाई और विश्राम
🇨🇳 雨声12小时 — 深度睡眠、学习和放松
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#RainSounds #SleepRain #HeavyRain #ASMR #SleepSounds #BlackScreen
#StudyRain #RelaxingRain #DeepSleep #AnxietyRelief #12Hours #NatureSounds
#RainASMR #StressRelief #AmbientRain #RainyNight #Insomnia #RainNoise
""",
}

# 1. BAIXAR do GitHub Release
print(f"[{CANAL.upper()}] Baixando {ASSET_NAME} do GitHub Release...")
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

path_original = f"/tmp/{CANAL}_original.mp4"
path_final    = f"/tmp/{CANAL}.mp4"

r2 = requests.get(asset_url,
    headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/octet-stream"},
    stream=True, timeout=3600)
if r2.status_code != 200:
    print(f"ERRO download: {r2.status_code}")
    sys.exit(1)

downloaded = 0
with open(path_original, "wb") as f:
    for chunk in r2.iter_content(chunk_size=32*1024*1024):
        if chunk:
            f.write(chunk)
            downloaded += len(chunk)
            print(f"\r  {downloaded/(1024**3):.2f}/{size_total/(1024**3):.2f} GB", end="", flush=True)
print(f"\n  Download OK: {os.path.getsize(path_original)/(1024**3):.2f} GB")

# 2. FASTSTART — move moov atom para o inicio (sem recodificar audio/video)
print(f"  Aplicando faststart (moov atom para o inicio)...")
result = subprocess.run([
    "ffmpeg", "-y",
    "-i", path_original,
    "-c", "copy",           # copia audio e video sem recodificar
    "-movflags", "+faststart",  # move moov para o inicio
    path_final
], capture_output=True, text=True, timeout=600)

if result.returncode != 0:
    print(f"ERRO ffmpeg: {result.stderr[-300:]}")
    sys.exit(1)

size_orig = os.path.getsize(path_original)
size_fast = os.path.getsize(path_final)
print(f"  Faststart OK: {size_orig/(1024**3):.2f} GB -> {size_fast/(1024**3):.2f} GB")
os.remove(path_original)

# 3. ACCESS TOKEN
r3 = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
    "refresh_token": RT, "grant_type": "refresh_token"}, timeout=15)
at = r3.json().get("access_token")
if not at:
    print(f"ERRO token: {r3.text[:150]}")
    sys.exit(1)
print("  Token OAuth: OK")

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
            print(f"  Apagado {vid}: {rd.status_code}")
            time.sleep(0.5)
    else:
        print("  Canal limpo")

# 5. UPLOAD — part=snippet,status APENAS (sem monetizationDetails)
size = os.path.getsize(path_final)
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

with open(path_final, "rb") as f:
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
            print("\n  503 retry 20s...")
            time.sleep(20)
            sent -= len(chunk)
            f.seek(sent)
        else:
            print(f"\n  ERRO: {r7.status_code} {r7.text[:200]}")
            sys.exit(1)

if not video_id:
    print("ERRO: sem video_id ao final")
    sys.exit(1)

# 6. MONETIZACAO (separado do upload)
time.sleep(5)
r8 = requests.put(
    "https://www.googleapis.com/youtube/v3/videos?part=monetizationDetails,status",
    headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json"},
    json={"id": video_id,
          "monetizationDetails": {"access": {"allowed": True}},
          "status": {"selfDeclaredMadeForKids": False, "madeForKids": False,
                     "license": "youtube", "embeddable": True}},
    timeout=20)
print(f"  Monetizacao: {r8.status_code} {'OK' if r8.status_code==200 else r8.text[:80]}")

# 7. SUPABASE
if SB_KEY and len(SB_KEY) > 20:
    sb_h = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
            "Content-Type": "application/json"}
    requests.patch(f"{SB_URL}/rest/v1/noise_channels?canal_key=eq.{CANAL}",
        headers=sb_h, json={"video_id": video_id, "video_uploaded": True}, timeout=10)

print(f"\n  URL: https://youtube.com/watch?v={video_id}")
print(f"  DONE {CANAL.upper()} = {video_id}")
