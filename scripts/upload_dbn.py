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

print("Gerando 72 blocos de 10min (12h)...")
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
        print(f"  {i+1}/72 ({(i+1)*10/60:.0f}h)")

print("Concatenando...")
with open("/tmp/lista.txt","w") as f:
    for p in blocos: f.write(f"file '{p}'\n")

subprocess.run([
    "ffmpeg","-y","-f","concat","-safe","0","-i","/tmp/lista.txt",
    "-c","copy","/tmp/dbn_12h.mp4"
], timeout=600, check=True)

for p in blocos: os.remove(p)
size_gb = os.path.getsize("/tmp/dbn_12h.mp4")/1024**3
print(f"MP4 final: {size_gb:.2f} GB")

# === UPLOAD YOUTUBE ===
print("Obtendo access token...")
r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":     os.environ["YT_CLIENT_ID_2"],
    "client_secret": os.environ["YT_CLIENT_SECRET_2"],
    "refresh_token": os.environ["YOUTUBE_RT_DBN"],
    "grant_type":    "refresh_token"
})
TOKEN = r.json()["access_token"]
print("Token OK")

TITLE = "Brown Noise 12 Hours | Deep Sleep, ADHD Focus & Study | Black Screen"

DESCRIPTION = """12 Hours of Deep Brown Noise — Pure Black Screen for Sleep, Focus & Relaxation

🎧 What is Brown Noise?
Brown noise (red noise) has more energy in low frequencies — a deep, rich rumble like a powerful waterfall or distant thunder. Scientifically studied for sleep, ADHD, tinnitus and focus.

✅ Benefits:
• Deep sleep & insomnia relief
• ADHD focus & concentration
• Study & deep work
• Tinnitus masking
• Baby & infant sleep
• Anxiety & stress relief

😴 Why Black Screen?
Total darkness promotes melatonin production for deeper, more restorative sleep.

⏱️ Timestamps:
00:00:00 — Start
03:00:00 — Hour 3
06:00:00 — Hour 6
09:00:00 — Hour 9
12:00:00 — End

— EN: Brown Noise 12 hours black screen sleep focus
— ES: Ruido marrón 12 horas pantalla negra dormir concentración
— PT: Ruído marrom 12 horas tela preta dormir foco
— FR: Bruit brun 12 heures écran noir sommeil concentration
— DE: Braunes Rauschen 12 Stunden schwarzer Bildschirm Schlaf Fokus
— JA: ブラウンノイズ 12時間 黒画面 睡眠 集中
— KO: 브라운 노이즈 12시간 검은 화면 수면 집중
— ZH: 棕色噪音12小时黑屏睡眠专注
— AR: ضوضاء بنية 12 ساعة شاشة سوداء نوم تركيز
— RU: Коричневый шум 12 часов чёрный экран сон концентрация

#BrownNoise #DeepSleep #ADHDFocus #BlackScreen #SleepSounds #StudyMusic #Tinnitus #Focus #Relaxation #BabySleep"""

TAGS = [
    "brown noise","brown noise 12 hours","deep brown noise","brown noise sleep",
    "brown noise ADHD","brown noise focus","brown noise study","black screen",
    "sleep sounds","ADHD focus","tinnitus relief","baby sleep","study music",
    "deep sleep","concentration","relaxation","ambient noise","sleep aid",
    "brown noise black screen","ruido marron","bruit brun","braunes rauschen",
    "ブラウンノイズ","브라운 노이즈","棕色噪音","коричневый шум","ضوضاء بنية",
    "brown noise 12 hours black screen","white noise","pink noise","sleep music"
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

file_size = os.path.getsize("/tmp/dbn_12h.mp4")
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
print("Upload URL obtida")

CHUNK = 50 * 1024 * 1024
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
            print(f"  {offset/file_size*100:.1f}%  ({offset//1024//1024}MB/{file_size//1024//1024}MB)")
        else:
            print(f"ERRO {r3.status_code}: {r3.text[:300]}")
            break

if video_id:
    print(f"\n✅ PUBLICADO!")
    print(f"URL: https://youtube.com/watch?v={video_id}")
    # Salvar ID para workflow de metadados
    with open("dbn_video_id.txt","w") as f:
        f.write(video_id)
