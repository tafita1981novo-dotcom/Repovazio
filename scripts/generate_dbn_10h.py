import numpy as np, struct, os, subprocess, random

SR    = 44100
BLOCO = SR * 600

def gerar_bloco(seed, n):
    np.random.seed(seed)
    white   = np.random.randn(n)
    f_white = np.fft.rfft(white)
    freqs   = np.fft.rfftfreq(n, d=1.0/SR); freqs[0]=1
    f_brown  = f_white / freqs
    boost    = np.ones_like(freqs)
    boost   += 1.8 * np.exp(-((freqs-50)**2)/(2*25**2))
    shelving = np.ones_like(freqs)
    shelving[freqs>300] = (300.0/freqs[freqs>300])**2.2
    f_final  = f_brown * boost * shelving
    f_final[freqs<18] = 0
    brown = np.fft.irfft(f_final, n=n)
    return (brown/np.max(np.abs(brown))*0.707*32767).astype(np.int16)

def save_wav(fn, s):
    d = s.tobytes()
    with open(fn,"wb") as f:
        f.write(b"RIFF"); f.write(struct.pack("<I",36+len(d)))
        f.write(b"WAVE"); f.write(b"fmt "); f.write(struct.pack("<I",16))
        f.write(struct.pack("<HHIIHH",1,1,SR,SR*2,2,16))
        f.write(b"data"); f.write(struct.pack("<I",len(d))); f.write(d)

BASE = random.randint(100000,999999)
print(f"Seed: {BASE}")

blocos = []
for i in range(60):  # 60 x 10min = 10h
    wav = f"/tmp/b{i:02d}.wav"
    mp4 = f"/tmp/b{i:02d}.mp4"
    save_wav(wav, gerar_bloco(BASE+i, BLOCO))
    subprocess.run([
        "ffmpeg","-y",
        "-f","lavfi","-i","color=c=0x000000:size=1920x1080:rate=1:duration=600",
        "-i",wav,"-t","600",
        "-c:v","libx264","-preset","ultrafast","-crf","51",
        "-tune","stillimage","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","192k","-movflags","+faststart",mp4
    ], capture_output=True, timeout=180)
    os.remove(wav)
    blocos.append(mp4)
    if (i+1)%6==0: print(f"  {i+1}/60 ({(i+1)*10//60}h{((i+1)*10%60)}min)")

print("Concatenando...")
with open("/tmp/lista.txt","w") as f:
    for p in blocos: f.write(f"file '{p}'\n")

subprocess.run([
    "ffmpeg","-y","-f","concat","-safe","0","-i","/tmp/lista.txt",
    "-c","copy","/tmp/dbn_10h_v7.mp4"
], timeout=300, check=True)

for p in blocos: os.remove(p)
size_gb = os.path.getsize("/tmp/dbn_10h_v7.mp4")/1024**3
print(f"MP4 pronto: {size_gb:.2f} GB")

# Upload para GitHub Release como asset para download manual
import requests as req
GH_TOKEN = os.environ["GH_TOKEN"]
GH_H = {"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github.v3+json"}

# Criar release se não existir
rr = req.get("https://api.github.com/repos/tafita1981novo-dotcom/Repovazio/releases/tags/dbn-v7",
    headers=GH_H, timeout=10)
if rr.status_code == 200:
    release_id = rr.json()["id"]
    upload_url = rr.json()["upload_url"].replace("{?name,label}","")
    print(f"Release existe: {release_id}")
else:
    rc = req.post("https://api.github.com/repos/tafita1981novo-dotcom/Repovazio/releases",
        headers=GH_H,
        json={"tag_name":"dbn-v7","name":"DBN 10h V7","body":"Brown Noise 10h V7 — download manual","draft":False,"prerelease":False},
        timeout=15)
    release_id = rc.json()["id"]
    upload_url = rc.json()["upload_url"].replace("{?name,label}","")
    print(f"Release criada: {release_id}")

# Fazer upload do MP4 em chunks (GitHub aceita até 2GB por asset)
file_size = os.path.getsize("/tmp/dbn_10h_v7.mp4")
print(f"Enviando {file_size//1024//1024}MB para GitHub Release...")
with open("/tmp/dbn_10h_v7.mp4","rb") as f:
    ru = req.post(
        f"{upload_url}?name=dbn_10h_v7.mp4",
        headers={**GH_H,"Content-Type":"video/mp4","Content-Length":str(file_size)},
        data=f, timeout=600
    )
print(f"Upload release: {ru.status_code}")
if ru.status_code == 201:
    download_url = ru.json()["browser_download_url"]
    print(f"\n✅ DOWNLOAD URL:")
    print(download_url)
else:
    print(ru.text[:200])
