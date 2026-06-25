import numpy as np, struct, os, subprocess, requests

SR    = 44100
BLOCO = SR * 600  # 10 min por bloco

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
    with open(caminho, "wb") as f:
        f.write(b"RIFF"); f.write(struct.pack("<I", 36+len(data)))
        f.write(b"WAVE"); f.write(b"fmt "); f.write(struct.pack("<I",16))
        f.write(struct.pack("<HHIIHH",1,1,SR,SR*2,2,16))
        f.write(b"data"); f.write(struct.pack("<I",len(data))); f.write(data)

print("Gerando 72 blocos de 10min (12h total)...")
blocos = []
for i in range(72):
    wav = f"/tmp/b_{i:03d}.wav"
    mp4 = f"/tmp/b_{i:03d}.mp4"
    gerar_bloco_wav(42+i, BLOCO, wav)
    subprocess.run([
        "ffmpeg","-y",
        "-f","lavfi","-i","color=c=0x000000:size=1920x1080:rate=1:duration=600",
        "-i", wav, "-t","600",
        "-c:v","libx264","-preset","ultrafast","-crf","51",
        "-tune","stillimage","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","192k","-movflags","+faststart", mp4
    ], capture_output=True, timeout=180)
    os.remove(wav)
    blocos.append(mp4)
    if (i+1) % 12 == 0:
        print(f"  {i+1}/72 blocos ({(i+1)*10/60:.0f}h concluidas)")

print("Concatenando em MP4 final...")
with open("/tmp/lista.txt","w") as f:
    for p in blocos: f.write(f"file '{p}'\n")

subprocess.run([
    "ffmpeg","-y","-f","concat","-safe","0","-i","/tmp/lista.txt",
    "-c","copy","/tmp/dbn_12h.mp4"
], timeout=600, check=True)
for p in blocos: os.remove(p)
print(f"MP4 final: {os.path.getsize('/tmp/dbn_12h.mp4')/1024**3:.2f} GB")

# === TOKEN ===
print("Obtendo access token YouTube...")
r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":     os.environ["YT_CLIENT_ID_2"],
    "client_secret": os.environ["YT_CLIENT_SECRET_2"],
    "refresh_token": os.environ["YOUTUBE_RT_DBN"],
    "grant_type":    "refresh_token"
})
TOKEN = r.json()["access_token"]
print("Token OK")

# === METADADOS SEO — validados contra limites YouTube ===
# Título: max 100 chars
TITLE = "Brown Noise 12 Hours | Sleep, ADHD Focus & Study Music | Black Screen"
assert len(TITLE) <= 100

# Descrição: max 5000 chars — 10 idiomas com os 6 termos mais buscados cada
DESCRIPTION = """12 Hours of Deep Brown Noise — Pure Black Screen for Sleep, ADHD Focus & Study

🎧 WHAT IS BROWN NOISE?
Brown noise has more energy in low frequencies — a deep rumble like a powerful waterfall or distant thunder. Scientifically studied for sleep quality, ADHD focus and tinnitus relief.

✅ BENEFITS:
• Deep sleep & insomnia relief
• ADHD concentration & focus
• Study, work & productivity
• Tinnitus masking
• Baby & infant sleep
• Anxiety & stress relief
• Meditation & mindfulness

😴 WHY BLACK SCREEN?
Pure black (RGB 0,0,0) — zero light emission, no flickering. Promotes melatonin production for deeper, more restorative sleep. Safe for all night use.

⏱️ TIMESTAMPS:
00:00:00 — Start
03:00:00 — Hour 3
06:00:00 — Hour 6
09:00:00 — Hour 9
12:00:00 — End

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌍 10 LANGUAGES — 10 IDIOMAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🇺🇸 EN — Brown Noise 12 hours black screen sleep focus ADHD study music
🇪🇸 ES — Ruido marrón 12 horas pantalla negra dormir concentración música estudio TDAH
🇧🇷 PT — Ruído marrom 12 horas tela preta dormir foco TDAH música estudo sons para dormir
🇫🇷 FR — Bruit brun 12 heures écran noir sommeil concentration musique étude TDAH
🇩🇪 DE — Braunes Rauschen 12 Stunden schwarzer Bildschirm Schlaf Fokus Lernen ADHS Musik
🇯🇵 JP — ブラウンノイズ 12時間 黒画面 睡眠 集中 勉強 ADHD 睡眠音楽
🇰🇷 KR — 브라운 노이즈 12시간 검은 화면 수면 집중 공부 ADHD 수면 음악
🇨🇳 ZH — 棕色噪音12小时黑屏深度睡眠专注学习ADHD睡眠音乐
🇸🇦 AR — ضوضاء بنية 12 ساعة شاشة سوداء نوم تركيز دراسة موسيقى ADHD
🇷🇺 RU — Коричневый шум 12 часов чёрный экран сон концентрация учёба музыка СДВГ

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#BrownNoise #DeepSleep #ADHDFocus #BlackScreen #SleepSounds
#StudyMusic #WhiteNoise #Tinnitus #BabySleep #Relaxation
#SleepAid #Focus #Concentration #Meditation #StressRelief
#RuidoMarron #BruitBrun #BraunesRauschen #ブラウンノイズ #棕色噪音"""

assert len(DESCRIPTION) <= 5000

# Tags: max 500 chars total — os 6 termos mais buscados + variações idiomas
TAGS = [
    "brown noise","brown noise 12 hours","deep brown noise",
    "brown noise sleep","brown noise ADHD","brown noise study",
    "brown noise focus","black screen","sleep sounds","ADHD focus",
    "tinnitus relief","baby sleep","study music","deep sleep",
    "concentration","relaxation","sleep aid","sleep music",
    "ruido marron","bruit brun","braunes rauschen","white noise","pink noise"
]
total = sum(len(t) for t in TAGS) + len(TAGS) - 1
assert total <= 500, f"Tags {total} > 500"
print(f"Metadados validados — titulo={len(TITLE)}, desc={len(DESCRIPTION)}, tags={total} chars")

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

# === UPLOAD RESUMABLE ===
file_size = os.path.getsize("/tmp/dbn_12h.mp4")
print(f"Iniciando upload ({file_size//1024//1024}MB)...")

r2 = requests.post(
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "X-Upload-Content-Length": str(file_size),
        "X-Upload-Content-Type": "video/mp4"
    },
    json=metadata
)
upload_url = r2.headers["Location"]
print("Upload URL OK")

CHUNK    = 50 * 1024 * 1024
video_id = None
with open("/tmp/dbn_12h.mp4","rb") as f:
    offset = 0
    while offset < file_size:
        chunk = f.read(CHUNK)
        end   = offset + len(chunk) - 1
        r3 = requests.put(upload_url,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Range": f"bytes {offset}-{end}/{file_size}",
                "Content-Type": "video/mp4"
            },
            data=chunk, timeout=300
        )
        if r3.status_code in (200,201):
            video_id = r3.json()["id"]
            print(f"Upload completo! ID: {video_id}")
            break
        elif r3.status_code == 308:
            offset = int(r3.headers.get("Range","bytes=-1").split("-")[1]) + 1
            print(f"  Upload: {offset/file_size*100:.1f}%  ({offset//1024//1024}MB/{file_size//1024//1024}MB)")
        else:
            print(f"ERRO {r3.status_code}: {r3.text[:300]}")
            break

if video_id:
    with open("dbn_video_id.txt","w") as f:
        f.write(video_id)
    print(f"\n✅ PUBLICADO!")
    print(f"URL: https://youtube.com/watch?v={video_id}")
else:
    print("FALHOU — sem video_id")
