import requests, os, json

r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":     os.environ["YT_CLIENT_ID_2"],
    "client_secret": os.environ["YT_CLIENT_SECRET_2"],
    "refresh_token": os.environ["YOUTUBE_RT_DBN"],
    "grant_type":    "refresh_token"
})
TOKEN = r.json()["access_token"]
print("Token OK")

# Checar canal completo
rc = requests.get(
    "https://www.googleapis.com/youtube/v3/channels",
    params={"part":"snippet,status,contentDetails,brandingSettings","mine":"true"},
    headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15
)
ch = rc.json()
print("Canal resposta:")
for item in ch.get("items",[]):
    print(f"  Nome:         {item['snippet']['title']}")
    print(f"  ID:           {item['id']}")
    print(f"  LongUploads:  {item['status'].get('longUploadsStatus')}")
    print(f"  MadeForKids:  {item['status'].get('madeForKids')}")
    print(f"  SelfDeclared: {item['status'].get('selfDeclaredMadeForKids')}")
    print(f"  PrivacyStatus:{item['status'].get('privacyStatus')}")
    print(f"  IsLinked:     {item['status'].get('isLinked')}")

# Tentar upload de video PEQUENO (30s) para testar se canal aceita
print("\nTestando upload de 30s...")
import subprocess, struct, numpy as np, random

SR = 44100
N  = SR * 30
np.random.seed(random.randint(1, 999999))
white   = np.random.randn(N)
f_white = np.fft.rfft(white)
freqs   = np.fft.rfftfreq(N, d=1.0/SR)
freqs[0]= 1
f_brown = f_white / freqs
brown   = np.fft.irfft(f_brown, n=N)
brown   = brown / np.max(np.abs(brown)) * 0.5
data    = (brown * 32767).astype(np.int16).tobytes()

with open("/tmp/test.wav","wb") as f:
    f.write(b"RIFF"); f.write(struct.pack("<I",36+len(data)))
    f.write(b"WAVE"); f.write(b"fmt "); f.write(struct.pack("<I",16))
    f.write(struct.pack("<HHIIHH",1,1,SR,SR*2,2,16))
    f.write(b"data"); f.write(struct.pack("<I",len(data))); f.write(data)

subprocess.run([
    "ffmpeg","-y",
    "-f","lavfi","-i","color=c=0x000000:size=1920x1080:rate=1:duration=30",
    "-i","/tmp/test.wav","-t","30",
    "-c:v","libx264","-preset","ultrafast","-crf","51",
    "-c:a","aac","-b:a","192k","-movflags","+faststart",
    "/tmp/test30s.mp4"
], capture_output=True)

file_size = os.path.getsize("/tmp/test30s.mp4")
print(f"Arquivo teste: {file_size//1024}KB")

r2 = requests.post(
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "X-Upload-Content-Length": str(file_size),
        "X-Upload-Content-Type": "video/mp4"
    },
    json={
        "snippet": {
            "title": "DBN TEST 30s check",
            "description": "test",
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "private",
            "selfDeclaredMadeForKids": False
        }
    }
)
print(f"Upload URL status: {r2.status_code}")
if r2.status_code != 200:
    print(f"ERRO: {r2.text[:300]}")
    exit()

upload_url = r2.headers["Location"]
with open("/tmp/test30s.mp4","rb") as f:
    data = f.read()
r3 = requests.put(upload_url,
    headers={"Authorization":f"Bearer {TOKEN}","Content-Range":f"bytes 0-{file_size-1}/{file_size}","Content-Type":"video/mp4"},
    data=data, timeout=60)
print(f"Upload result: {r3.status_code}")
if r3.status_code in (200,201):
    vid = r3.json().get("id")
    print(f"VIDEO ID: {vid}")
    status_v = r3.json().get("status",{})
    print(f"Upload status: {status_v.get('uploadStatus')}")
    print(f"Rejection: {status_v.get('rejectionReason','none')}")
else:
    print(f"Erro: {r3.text[:300]}")
