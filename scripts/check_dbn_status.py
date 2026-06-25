import requests, os, struct, numpy as np, random, subprocess

SR = 44100; N = SR * 30
np.random.seed(random.randint(1,999999))
white   = np.random.randn(N)
f_white = np.fft.rfft(white)
freqs   = np.fft.rfftfreq(N, d=1.0/SR); freqs[0]=1
f_brown = f_white / freqs
f_brown[freqs>300] *= (300.0/freqs[freqs>300])**2.2
f_brown[freqs<18]   = 0
brown = np.fft.irfft(f_brown, n=N)
brown = brown / np.max(np.abs(brown)) * 0.5
data  = (brown*32767).astype(np.int16).tobytes()

with open("/tmp/t.wav","wb") as f:
    f.write(b"RIFF"); f.write(struct.pack("<I",36+len(data)))
    f.write(b"WAVE"); f.write(b"fmt "); f.write(struct.pack("<I",16))
    f.write(struct.pack("<HHIIHH",1,1,SR,SR*2,2,16))
    f.write(b"data"); f.write(struct.pack("<I",len(data))); f.write(data)

subprocess.run([
    "ffmpeg","-y",
    "-f","lavfi","-i","color=c=0x000000:size=1920x1080:rate=1:duration=30",
    "-i","/tmp/t.wav","-t","30",
    "-c:v","libx264","-preset","ultrafast","-crf","51",
    "-c:a","aac","-b:a","192k","-movflags","+faststart","/tmp/t.mp4"
], capture_output=True)
print(f"MP4: {os.path.getsize('/tmp/t.mp4')//1024}KB")

r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": os.environ["YT_CLIENT_ID_2"],
    "client_secret": os.environ["YT_CLIENT_SECRET_2"],
    "refresh_token": os.environ["YOUTUBE_RT_DBN"],
    "grant_type": "refresh_token"})
TOKEN = r.json()["access_token"]
print("Token OK")

fsize = os.path.getsize("/tmp/t.mp4")
r2 = requests.post(
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    headers={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json",
             "X-Upload-Content-Length":str(fsize),"X-Upload-Content-Type":"video/mp4"},
    json={
        "snippet":{"title":"DBN TEST diagnose - delete","description":"test","categoryId":"22"},
        "status":{"privacyStatus":"private","selfDeclaredMadeForKids":False}
    })
print(f"Upload URL: {r2.status_code}")
if r2.status_code != 200:
    print(f"ERRO URL: {r2.text[:300]}"); exit()

with open("/tmp/t.mp4","rb") as f: d=f.read()
r3 = requests.put(r2.headers["Location"],
    headers={"Authorization":f"Bearer {TOKEN}",
             "Content-Range":f"bytes 0-{fsize-1}/{fsize}","Content-Type":"video/mp4"},
    data=d, timeout=60)
print(f"Upload: {r3.status_code}")
if r3.status_code in (200,201):
    resp = r3.json()
    vid  = resp.get("id")
    st   = resp.get("status",{})
    print(f"VIDEO ID:  {vid}")
    print(f"Upload:    {st.get('uploadStatus','?')}")
    print(f"Rejection: {st.get('rejectionReason','none')}")
    print(f"Failure:   {st.get('failureReason','none')}")
    print(f"Privacy:   {st.get('privacyStatus','?')}")
    print(f"URL:       https://youtube.com/watch?v={vid}")
else:
    print(f"ERRO upload: {r3.text[:300]}")
