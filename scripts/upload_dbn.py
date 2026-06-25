import numpy as np, struct, os, subprocess, sys, json, time, requests

SR    = 44100
BLOCO = SR * 600  # 10 min

def gerar_bloco_wav(seed, n, caminho):
    np.random.seed(seed)
    white   = np.random.randn(n)
    f_white = np.fft.rfft(white)
    freqs   = np.fft.rfftfreq(n, d=1.0/SR)
    freqs[0]= 1
    f_brown  = f_white / freqs
    boost    = np.ones_like(freqs)
    boost   += 1.8 * np.exp(-((freqs - 50)**2) / (2 * 25**2))
    shelving = np.ones_like(freqs)
    shelving[freqs > 300] = (300.0 / freqs[freqs > 300]) ** 2.2
    f_final  = f_brown * boost * shelving
    f_final[freqs < 18] = 0
    brown = np.fft.irfft(f_final, n=n)
    brown = brown / np.max(np.abs(brown)) * 0.707
    data  = (brown * 32767).astype(np.int16).tobytes()
    with open(caminho, 'wb') as f:
        f.write(b'RIFF'); f.write(struct.pack('<I', 36+len(data)))
        f.write(b'WAVE'); f.write(b'fmt '); f.write(struct.pack('<I',16))
        f.write(struct.pack('<HHIIHH',1,1,SR,SR*2,2,16))
        f.write(b'data'); f.write(struct.pack('<I',len(data))); f.write(data)

print("=== GERANDO 72 BLOCOS DE 10MIN (12H TOTAL) ===")
blocos = []
for i in range(72):
    wav = f'/tmp/bloco_{i:03d}.wav'
    mp4 = f'/tmp/bloco_{i:03d}.mp4'
    gerar_bloco_wav(42 + i, BLOCO, wav)
    subprocess.run([
        'ffmpeg','-y',
        '-f','lavfi',
        '-i','color=c=0x000000:size=1920x1080:rate=1:duration=600',
        '-i', wav,
        '-t','600',
        '-c:v','libx264','-preset','ultrafast','-crf','51',
        '-tune','stillimage',
        '-x264-params','aq-mode=0',
        '-pix_fmt','yuv420p',
        '-c:a','aac','-b:a','192k',
        '-movflags','+faststart',
        mp4
    ], capture_output=True, timeout=180)
    os.remove(wav)
    blocos.append(mp4)
    if (i+1) % 6 == 0:
        print(f"  {i+1}/72 blocos ({(i+1)*10/60:.1f}h)")

print("=== CONCATENANDO EM MP4 FINAL ===")
with open('/tmp/lista.txt','w') as f:
    for p in blocos: f.write(f"file '{p}'\n")

subprocess.run([
    'ffmpeg','-y','-f','concat','-safe','0','-i','/tmp/lista.txt',
    '-c','copy','/tmp/dbn_12h_final.mp4'
], timeout=600, check=True)

for p in blocos: os.remove(p)

size = os.path.getsize('/tmp/dbn_12h_final.mp4') / 1024**3
print(f"MP4 final: {size:.2f} GB")

# === UPLOAD YOUTUBE ===
print("=== UPLOAD YOUTUBE ===")
CLIENT_ID     = os.environ['YT_CLIENT_ID_2']
CLIENT_SECRET = os.environ['YT_CLIENT_SECRET_2']
REFRESH_TOKEN = os.environ['YOUTUBE_RT_DBN']

# Obter access token
r = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
    'refresh_token': REFRESH_TOKEN, 'grant_type': 'refresh_token'
})
ACCESS_TOKEN = r.json()['access_token']
print("Token OK")

# Metadados SEO otimizados
TITLE = "Brown Noise 12 Hours | Deep Sleep, ADHD Focus & Study | Black Screen No Ads"

DESCRIPTION = """🎧 12 Hours of Deep Brown Noise for Sleep, Focus, ADHD & Relaxation | Pure Black Screen

Brown noise is scientifically proven to help with:
✅ Deep sleep & insomnia relief
✅ ADHD focus & concentration
✅ Study & deep work sessions
✅ Tinnitus masking & relief
✅ Baby & infant sleep
✅ Anxiety & stress reduction
✅ Meditation & mindfulness

🔬 What is Brown Noise?
Brown noise (also called red noise) has more energy in lower frequencies, producing a deep, rich rumble similar to a powerful waterfall, strong wind, or thunder in the distance. Unlike white noise, it lacks the harsh high frequencies that can cause fatigue.

😴 Why Black Screen?
Complete darkness promotes melatonin production for deeper, more restorative sleep. No flickering, no light — just pure sound in total darkness.

⏱️ Timestamps:
00:00:00 — Start
03:00:00 — Hour 3
06:00:00 — Hour 6
09:00:00 — Hour 9
12:00:00 — End

🎵 Best used with:
• Headphones or speakers at low-medium volume
• Sleep timer on your device
• Volume just loud enough to mask background noise

#BrownNoise #DeepSleep #ADHDFocus #SleepSounds #BlackScreen #StudyMusic #WhiteNoise #Relaxation #Tinnitus #BabySleep #Focus #Concentration #SleepAid #Meditation

---
🌍 Available in all languages | Disponível em todos os idiomas

PT: Ruído marrom 12 horas para dormir profundamente e foco
ES: Ruido marrón 12 horas para dormir y concentración
FR: Bruit brun 12 heures pour dormir et se concentrer
DE: Braunes Rauschen 12 Stunden Schlaf und Fokus
IT: Rumore marrone 12 ore per dormire e concentrarsi
JA: ブラウンノイズ 12時間 睡眠・集中
KO: 브라운 노이즈 12시간 수면 집중
ZH: 棕色噪音12小时深度睡眠专注
AR: ضوضاء بنية 12 ساعة للنوم والتركيز
RU: Коричневый шум 12 часов сон и концентрация
HI: ब्राउन नॉइज़ 12 घंटे नींद और फोकस
NL: Bruine ruis 12 uur slaap en concentratie"""

TAGS = [
    "brown noise","brown noise 12 hours","deep brown noise","brown noise sleep",
    "brown noise ADHD","brown noise study","brown noise focus","black screen",
    "sleep sounds","white noise","pink noise","noise for sleep","ADHD focus",
    "study music","concentration","deep sleep","tinnitus relief","baby sleep",
    "brown noise 12 hours black screen","sleep aid","relaxation sounds",
    "ambient noise","background noise","noise masking","sleep music",
    "deep sleep music","focus music","study sounds","work from home music",
    "productivity music","meditation sounds","mindfulness","stress relief",
    "anxiety relief","insomnia help","sleep better","brown noise for babies"
]

metadata = {
    "snippet": {
        "title": TITLE,
        "description": DESCRIPTION,
        "tags": TAGS,
        "categoryId": "22",
        "defaultLanguage": "en",
        "defaultAudioLanguage": "en"
    },
    "status": {
        "privacyStatus": "public",
        "selfDeclaredMadeForKids": False,
        "license": "youtube",
        "embeddable": True,
        "publicStatsViewable": True
    }
}

# Upload resumable
file_size = os.path.getsize('/tmp/dbn_12h_final.mp4')
r2 = requests.post(
    'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
    headers={
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json',
        'X-Upload-Content-Length': str(file_size),
        'X-Upload-Content-Type': 'video/mp4'
    },
    json=metadata
)
upload_url = r2.headers['Location']
print(f"Upload URL obtida")

# Enviar arquivo em chunks de 50MB
CHUNK = 50 * 1024 * 1024
video_id = None
with open('/tmp/dbn_12h_final.mp4', 'rb') as f:
    offset = 0
    while offset < file_size:
        chunk = f.read(CHUNK)
        end   = offset + len(chunk) - 1
        r3 = requests.put(upload_url,
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Range': f'bytes {offset}-{end}/{file_size}',
                'Content-Type': 'video/mp4'
            },
            data=chunk, timeout=300
        )
        if r3.status_code in (200, 201):
            video_id = r3.json()['id']
            print(f"Upload completo! Video ID: {video_id}")
            break
        elif r3.status_code == 308:
            offset = int(r3.headers.get('Range','bytes=-1').split('-')[1]) + 1
            pct = offset/file_size*100
            print(f"  {pct:.1f}% ({offset//1024//1024}MB / {file_size//1024//1024}MB)")
        else:
            print(f"Erro {r3.status_code}: {r3.text[:200]}")
            break

if video_id:
    # Ativar monetização — mid-rolls a cada 15 min
    r4 = requests.put(
        f'https://www.googleapis.com/youtube/v3/videos?part=monetizationDetails',
        headers={'Authorization': f'Bearer {ACCESS_TOKEN}', 'Content-Type': 'application/json'},
        json={"id": video_id, "monetizationDetails": {"access": {"allowed": True}}}
    )
    print(f"Monetizacao: {r4.status_code}")

    # Adicionar à playlist do canal se existir
    print(f"\n✅ SUCESSO!")
    print(f"Video ID: {video_id}")
    print(f"URL: https://youtube.com/watch?v={video_id}")

    with open('/tmp/video_id_dbn.txt', 'w') as f:
        f.write(video_id)

