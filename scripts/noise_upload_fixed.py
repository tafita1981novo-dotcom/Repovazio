#!/usr/bin/env python3
"""
noise_upload_fixed.py — Upload automático de vídeos noise para 5 canais
CLIENT_ID correto: YT_CLIENT_ID_2 (98900709187-...)
"""
import json, urllib.request, urllib.parse, urllib.error, os, subprocess, sys

CLIENT_ID = os.environ.get("YT_CLIENT_ID_2", os.environ.get("YOUTUBE_CLIENT_ID", ""))
CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET_2", os.environ.get("YOUTUBE_CLIENT_SECRET", ""))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_SERVICE_KEY", ""))

CHANNELS = {
    "DBN":     {"rt_key": "YOUTUBE_RT_DBN",     "noise": "brown", "title": "Brown Noise 10 Hours | Deep Sleep, ADHD Focus & Study | Black Screen"},
    "ADHD":    {"rt_key": "YOUTUBE_RT_ADHD",    "noise": "brown", "title": "ADHD Brown Noise 10 Hours | Concentration & Deep Work | Black Screen"},
    "WNV":     {"rt_key": "YOUTUBE_RT_WNV",     "noise": "white", "title": "White Noise 10 Hours | Deep Sleep, Baby Sleep & Tinnitus | Black Screen"},
    "TINNITUS":{"rt_key": "YOUTUBE_RT_TINNITUS","noise": "pink",  "title": "Tinnitus Relief 10 Hours | Pink & White Noise | Black Screen"},
    "BSN":     {"rt_key": "YOUTUBE_RT_BSN",     "noise": "white", "title": "Baby Sleep White Noise 10 Hours | Newborn & Infant | Black Screen"},
}

def get_rt_from_supabase(key_name):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return os.environ.get(f"YOUTUBE_RT_{key_name.split('_')[-1]}", "")
    url = f"{SUPABASE_URL}/rest/v1/ia_cache?select=value&cache_key=eq.secret:{key_name}"
    req = urllib.request.Request(url, headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        if data:
            val = data[0]["value"]
            return val.strip('"') if isinstance(val, str) else val
    except:
        pass
    return os.environ.get(key_name, "")

def refresh_access_token(rt):
    data = urllib.parse.urlencode({"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "refresh_token": rt, "grant_type": "refresh_token"}).encode()
    resp = urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=data), timeout=10)
    return json.loads(resp.read())["access_token"]

def gen_video(noise_type, duration, output):
    filters = {"brown":"anoisesrc=c=brown:amplitude=0.3","white":"anoisesrc=c=white:amplitude=0.15","pink":"anoisesrc=c=pink:amplitude=0.2"}
    audio = output.replace(".mp4", ".mp3")
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i",filters[noise_type],"-t",str(duration),"-acodec","libmp3lame","-b:a","192k",audio], capture_output=True, timeout=300, check=True)
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","color=c=black:s=1920x1080:r=1","-i",audio,"-shortest","-c:v","libx264","-preset","ultrafast","-crf","51","-c:a","aac","-b:a","192k","-pix_fmt","yuv420p",output], capture_output=True, timeout=600, check=True)
    os.remove(audio)
    return output

def upload_video(at, video_file, title, description, tags):
    file_size = os.path.getsize(video_file)
    metadata = {"snippet": {"title": title, "description": description, "tags": tags, "categoryId": "22", "defaultLanguage": "en"}, "status": {"privacyStatus": "public", "madeForKids": False}}
    meta_json = json.dumps(metadata).encode()
    init_req = urllib.request.Request("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=meta_json, headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(file_size), "X-Upload-Content-Type": "video/mp4"}, method="POST")
    upload_url = urllib.request.urlopen(init_req, timeout=30).headers.get("Location")
    CHUNK = 10 * 1024 * 1024
    with open(video_file, "rb") as f:
        uploaded = 0
        while True:
            chunk = f.read(CHUNK)
            if not chunk: break
            end = uploaded + len(chunk) - 1
            req = urllib.request.Request(upload_url, data=chunk, headers={"Authorization": f"Bearer {at}",
                "Content-Range": f"bytes {uploaded}-{end}/{file_size}", "Content-Type": "video/mp4"}, method="PUT")
            try:
                resp = urllib.request.urlopen(req, timeout=120)
                return json.loads(resp.read()).get("id")
            except urllib.error.HTTPError as e:
                if e.code == 308: uploaded += len(chunk); print(f"  {int(uploaded/file_size*100)}%", end="\r")
                else: raise

if __name__ == "__main__":
    canal = sys.argv[1] if len(sys.argv) > 1 else "DBN"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 36000  # 10h default
    
    if canal not in CHANNELS:
        print(f"Canal {canal} não encontrado. Opções: {list(CHANNELS.keys())}")
        sys.exit(1)
    
    cfg = CHANNELS[canal]
    print(f"=== Upload para @{canal} ({cfg['noise']} noise, {duration//3600}h) ===")
    
    rt = get_rt_from_supabase(cfg["rt_key"])
    if not rt:
        print(f"❌ Refresh token não encontrado para {cfg['rt_key']}")
        sys.exit(1)
    
    at = refresh_access_token(rt)
    print(f"✅ Token OK")
    
    video_file = f"/tmp/{canal}_{duration//3600}h.mp4"
    print(f"Gerando vídeo {duration//3600}h...")
    gen_video(cfg["noise"], duration, video_file)
    mb = os.path.getsize(video_file)/1024/1024
    print(f"Vídeo: {mb:.0f} MB. Uploadando...")
    
    vid_id = upload_video(at, video_file, cfg["title"], cfg["title"], ["noise", "sleep", "black screen", "no ads"])
    print(f"✅ PUBLICADO: https://youtu.be/{vid_id}")
    os.remove(video_file)
