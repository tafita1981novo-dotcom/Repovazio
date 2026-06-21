import requests, os, glob, sys

def upload(canal, rt, title, tags):
    CI = os.environ["YT_CLIENT_ID"]
    CS = os.environ["YT_CLIENT_SECRET"]
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": CI, "client_secret": CS, "refresh_token": rt, "grant_type": "refresh_token"
    })
    at = r.json().get("access_token")
    print(f"AT={bool(at)}")
    if not at: return None
    
    files = glob.glob("**/*.mp4", recursive=True) + glob.glob("**/*.webm", recursive=True)
    print(f"Files: {files}")
    if not files: return None
    
    vf = files[0]; fs = os.path.getsize(vf)
    print(f"File: {vf} {fs/1e6:.0f}MB")
    
    meta = {
        "snippet": {"title": title, "description": title, "categoryId": "22", "tags": tags},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }
    
    r2 = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(fs)},
        json=meta)
    ul = r2.headers.get("Location")
    print(f"Init: {r2.status_code} url={bool(ul)}")
    if not ul: print(r2.text[:300]); return None
    
    CHUNK = 64*1024*1024; up = 0
    with open(vf, "rb") as f:
        while up < fs:
            ch = f.read(CHUNK); end = up + len(ch) - 1
            r3 = requests.put(ul, headers={
                "Content-Range": f"bytes {up}-{end}/{fs}", "Content-Type": "video/mp4"
            }, data=ch, timeout=300)
            up += len(ch)
            print(f"{up/fs*100:.0f}% s={r3.status_code}", flush=True)
            if r3.status_code in [200, 201]:
                v = r3.json()
                vid_id = v.get("id")
                mfk = v.get("status", {}).get("selfDeclaredMadeForKids")
                print(f"SUCCESS {canal} ID={vid_id} mfk={mfk}")
                return vid_id
    return None

canal = sys.argv[1] if len(sys.argv) > 1 else "unknown"
rt = os.environ.get("YT_RT", "")

configs = {
    "bsn":  ("Baby White Noise 10 Hours | Black Screen Newborn Sleep", ["baby sleep","white noise","newborn","black screen"]),
    "pink": ("Pink Noise 10 Hours | Black Screen Sleep Therapy", ["pink noise","sleep therapy","black screen","deep sleep"]),
    "rain": ("Rain and Thunder Sounds 10 Hours | Black Screen Sleep", ["rain sounds","thunder","sleep sounds","black screen","asmr"]),
}

if canal not in configs:
    print(f"Unknown canal: {canal}"); sys.exit(1)

title, tags = configs[canal]
result = upload(canal, rt, title, tags)
if not result:
    print(f"FAILED {canal}")
    sys.exit(1)
print(f"DONE {canal}={result}")
