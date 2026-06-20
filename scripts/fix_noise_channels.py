import json, os, sys, urllib.request, urllib.parse, urllib.error, zipfile, shutil

CID = os.environ["YT_CLIENT_ID"]
CSC = os.environ["YT_CLIENT_SECRET"]
GH_TOKEN = os.environ["GH_PAT"]
REPO = "tafita1981novo-dotcom/Repovazio"
SUPA = "https://tpjvalzwkqwttvmszvie.supabase.co"
SK = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwanZhbHp3a3F3dHR2bXN6dmllIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxMzk4MDkyNCwiZXhwIjoyMDI5NTU2OTI0fQ.RgYBGalHZy8a8PnlKCvF1mQr6BhVDGNv4j9OzomBCaA"

CANAIS = {
  "dbn":      {"rt_env": "YT_RT_DBN",      "artifact": "noise-dbn-36000s",      "ch_id": "UCD4LLFnsiVzA-DeSN6oaUzg",
               "title": "Deep Brown Noise | 10 Hours Black Screen Sleep & Focus",
               "desc": "Deep brown noise for sleep, ADHD focus and tinnitus masking. Pure black screen 10 hours.\n\n#BrownNoise #DeepSleep #ADHDFocus #BlackScreen #SleepSounds",
               "tags": ["brown noise","deep brown noise","sleep sounds","black screen","ADHD focus","tinnitus","sleep music","deep sleep"]},
  "adhd":     {"rt_env": "YT_RT_ADHD",     "artifact": "noise-adhd-36000s",     "ch_id": "UCK3xZDFY84ffNrLEAI1Qmyw",
               "title": "ADHD Brown Noise | 10 Hours Focus Music Black Screen",
               "desc": "Brown noise scientifically shown to improve ADHD focus. Pure black screen 10 hours.\n\n#ADHDFocus #BrownNoise #BlackScreen #FocusMusic #ADHD",
               "tags": ["ADHD focus","brown noise","ADHD brown noise","black screen","focus music","hyperfocus","study music"]},
  "wnv":      {"rt_env": "YT_RT_WNV",      "artifact": "noise-wnv-36000s",      "ch_id": "UC0mFKp42jfL0ZobYEj7uwUA",
               "title": "White Noise 10 Hours | Black Screen Sleep Sound",
               "desc": "Classic white noise for deep sleep and office noise blocking. Pure black screen 10 hours.\n\n#WhiteNoise #SleepSounds #BlackScreen #DeepSleep",
               "tags": ["white noise","sleep sounds","black screen","sleep music","deep sleep","white noise sleep"]},
  "tinnitus": {"rt_env": "YT_RT_TINNITUS", "artifact": "noise-tinnitus-36000s", "ch_id": "UCZ5pmYA2ESO1vIhtE86l3_Q",
               "title": "Tinnitus Relief Pink Noise | 10 Hours Black Screen",
               "desc": "Pink noise for tinnitus masking and sound therapy. Pure black screen 10 hours.\n\n#TinnitusRelief #PinkNoise #SoundTherapy #BlackScreen",
               "tags": ["tinnitus relief","tinnitus masking","pink noise","black screen","sound therapy"]},
}

def get_at(rt):
    d = urllib.parse.urlencode({"client_id":CID,"client_secret":CSC,"refresh_token":rt,"grant_type":"refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token",data=d,method="POST",headers={"Content-Type":"application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req,timeout=15) as r:
        return json.loads(r.read())

def yt_del(at, vid_id):
    req = urllib.request.Request(f"https://www.googleapis.com/youtube/v3/videos?id={vid_id}",method="DELETE",headers={"Authorization":f"Bearer {at}"})
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code

def disk_info(label=""):
    disk = shutil.disk_usage("/")
    free_gb = disk.free/1024**3
    print(f"[DISCO {label}] livre={free_gb:.1f}GB ({(disk.used/disk.total)*100:.0f}% usado)", flush=True)
    return free_gb

ZIP_PATH = "/tmp/noise_current.zip"
gh_headers = {"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github.v3+json","User-Agent":"noise-bot"}

print("=== FIX NOISE CHANNELS ===", flush=True)
disk_info("inicio")

for canal, info in CANAIS.items():
    print(f"\n{'='*40}", flush=True)
    print(f"[{canal}] INICIANDO", flush=True)
    try:
        rt = os.environ.get(info["rt_env"],"")
        if not rt:
            print(f"[{canal}] SKIP: sem env {info['rt_env']}", flush=True)
            continue

        td = get_at(rt)
        at = td.get("access_token")
        if not at:
            print(f"[{canal}] NO_AT: {td.get('error','')} — {td.get('error_description','')}", flush=True)
            continue
        print(f"[{canal}] AT OK", flush=True)

        with urllib.request.urlopen(urllib.request.Request(
            "https://www.googleapis.com/youtube/v3/channels?part=snippet,contentDetails&mine=true",
            headers={"Authorization":f"Bearer {at}"}),timeout=10) as r:
            ch = json.loads(r.read())
        ch_name = ch.get("items",[{}])[0].get("snippet",{}).get("title","?")
        upl_pl = ch.get("items",[{}])[0].get("contentDetails",{}).get("relatedPlaylists",{}).get("uploads")
        print(f"[{canal}] Canal: {ch_name}", flush=True)

        if upl_pl:
            with urllib.request.urlopen(urllib.request.Request(
                f"https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&playlistId={upl_pl}&maxResults=10",
                headers={"Authorization":f"Bearer {at}"}),timeout=10) as r:
                pl = json.loads(r.read())
            for item in pl.get("items",[]):
                vid_id = item["contentDetails"]["videoId"]
                s = yt_del(at, vid_id)
                print(f"[{canal}] DEL {vid_id}: HTTP {s}", flush=True)

        with urllib.request.urlopen(urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/actions/artifacts?per_page=10&name={info['artifact']}",
            headers=gh_headers),timeout=10) as r:
            arts = [a for a in json.loads(r.read()).get("artifacts",[]) if not a.get("expired")]
        if not arts:
            print(f"[{canal}] ARTIFACT NAO ENCONTRADO: {info['artifact']}", flush=True)
            continue
        art = arts[0]
        print(f"[{canal}] Artifact: {art['id']} ({art['size_in_bytes']/1024**3:.2f}GB)", flush=True)

        free = disk_info(f"{canal} pre-dl")
        if free < 1.5:
            print(f"[{canal}] DISCO INSUFICIENTE: {free:.1f}GB", flush=True)
            continue

        print(f"[{canal}] Baixando ZIP...", flush=True)
        req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/actions/artifacts/{art['id']}/zip",headers=gh_headers)
        dl = 0; last = 0
        with urllib.request.urlopen(req,timeout=600) as r, open(ZIP_PATH,"wb") as f:
            while True:
                chunk = r.read(10*1024*1024)
                if not chunk: break
                f.write(chunk); dl += len(chunk)
                if dl - last >= 200*1024*1024:
                    print(f"[{canal}] dl={dl//1024//1024}MB", flush=True); last = dl
        print(f"[{canal}] ZIP ok: {os.path.getsize(ZIP_PATH)/1024**3:.2f}GB", flush=True)
        disk_info(f"{canal} pos-dl")

        with zipfile.ZipFile(ZIP_PATH) as zf:
            mp4s = [i for i in zf.infolist() if i.filename.endswith(".mp4")]
            if not mp4s:
                print(f"[{canal}] SEM MP4 NO ZIP: {zf.namelist()[:5]}", flush=True)
                continue
            mp4_info = mp4s[0]
            fsz = mp4_info.file_size
        print(f"[{canal}] MP4: {mp4_info.filename} ({fsz/1024**3:.2f}GB)", flush=True)

        td2 = get_at(rt)
        at2 = td2.get("access_token", at)

        body = {"snippet":{"title":info["title"],"description":info["desc"],"tags":info["tags"],"categoryId":"22","defaultLanguage":"en"},"status":{"privacyStatus":"public","selfDeclaredMadeForKids":False}}
        init_req = urllib.request.Request(
            "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
            data=json.dumps(body).encode(),method="POST",
            headers={"Authorization":f"Bearer {at2}","Content-Type":"application/json; charset=UTF-8","X-Upload-Content-Length":str(fsz),"X-Upload-Content-Type":"video/mp4"}
        )
        try:
            with urllib.request.urlopen(init_req,timeout=30) as r:
                upload_url = r.headers.get("Location")
        except urllib.error.HTTPError as e:
            print(f"[{canal}] INIT ERR {e.code}: {e.read().decode()[:300]}", flush=True)
            continue

        if not upload_url:
            print(f"[{canal}] SEM UPLOAD URL", flush=True)
            continue
        print(f"[{canal}] Upload URL OK. Streaming...", flush=True)

        CHUNK = 50*1024*1024
        up = 0; last = 0; vid_id = None
        with zipfile.ZipFile(ZIP_PATH) as zf:
            with zf.open(mp4_info) as stream:
                while up < fsz:
                    chunk = stream.read(CHUNK)
                    if not chunk: break
                    end = up + len(chunk) - 1
                    req2 = urllib.request.Request(upload_url,data=chunk,method="PUT",
                        headers={"Authorization":f"Bearer {at2}","Content-Length":str(len(chunk)),"Content-Range":f"bytes {up}-{end}/{fsz}","Content-Type":"video/mp4"})
                    try:
                        with urllib.request.urlopen(req2,timeout=300) as r2:
                            if r2.status in [200,201]:
                                vid_id = json.loads(r2.read()).get("id")
                                print(f"[{canal}] UPLOAD COMPLETO video_id={vid_id}", flush=True)
                    except urllib.error.HTTPError as e:
                        if e.code == 308:
                            rng = e.headers.get("Range","")
                            if rng: up = int(rng.split("-")[1]) + 1
                            if up - last >= 500*1024*1024:
                                print(f"[{canal}] {(up/fsz)*100:.1f}% {up//1024//1024}MB", flush=True)
                                disk_info(f"{canal} up"); last = up
                            continue
                        else:
                            print(f"[{canal}] UP ERR {e.code}: {e.read().decode()[:200]}", flush=True); break
                    up += len(chunk)

        if vid_id:
            body2 = json.dumps({"video_uploaded":True,"video_id":vid_id,"video_title":info["title"],"notas":"Noise video upado. Mid-rolls pendente."}).encode()
            req3 = urllib.request.Request(f"{SUPA}/rest/v1/noise_channels?channel_id=eq.{info['ch_id']}",data=body2,method="PATCH",
                headers={"apikey":SK,"Authorization":f"Bearer {SK}","Content-Type":"application/json","Prefer":"return=minimal"})
            try:
                with urllib.request.urlopen(req3,timeout=10) as r3:
                    print(f"[{canal}] Supabase patch: {r3.status}", flush=True)
            except Exception as ex:
                print(f"[{canal}] Supabase err: {ex}", flush=True)

    except Exception as e:
        import traceback
        print(f"[{canal}] ERRO: {e}", flush=True)
        traceback.print_exc()
    finally:
        if os.path.exists(ZIP_PATH):
            os.remove(ZIP_PATH)
            print(f"[{canal}] ZIP removido", flush=True)
        disk_info(f"{canal} pos")

print("\n=== FIM ===", flush=True)
