import os, sys, subprocess, requests, math

CLIENT_ID  = os.environ["CLIENT_ID"]
CLIENT_SEC = os.environ["CLIENT_SECRET"]
RT         = os.environ["REFRESH_TOKEN"]
CANAL      = os.environ["CANAL"].lower()
DURACAO_H  = int(os.environ.get("DURACAO_H", "10"))
TITULO     = os.environ["TITULO"]

DURACAO_S  = DURACAO_H * 3600
OUT        = f"/tmp/{CANAL}_gen.mp4"

# Noise sintético por canal (seeds e filtros diferentes = fingerprint único)
NOISE_FILTERS = {
    "dbn":  "anoisesrc=color=brown:amplitude=0.3,aresample=44100",
    "adhd": "anoisesrc=color=brown:amplitude=0.25,highpass=f=60,aresample=44100",
    "bsn":  "anoisesrc=color=white:amplitude=0.2,lowpass=f=8000,aresample=44100",
    "pink": "anoisesrc=color=pink:amplitude=0.3,aresample=44100",
    "rain": "anoisesrc=color=white:amplitude=0.35,lowpass=f=6000,highpass=f=200,aresample=44100",
}

noise = NOISE_FILTERS.get(CANAL, "anoisesrc=color=brown:amplitude=0.3,aresample=44100")

print(f"Gerando {CANAL} | {DURACAO_H}h | noise={noise[:40]}")

cmd = [
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", f"color=c=black:size=1920x1080:rate=30:duration={DURACAO_S}",
    "-f", "lavfi", "-i", f"{noise}",
    "-t", str(DURACAO_S),
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    "-movflags", "+faststart",
    OUT
]
print(f"cmd: {' '.join(cmd[:8])}...")
ret = subprocess.call(cmd, timeout=7200)
if ret != 0:
    print(f"ERRO ffmpeg: {ret}"); sys.exit(1)

size_gb = os.path.getsize(OUT)/(1024**3)
print(f"Gerado OK: {size_gb:.2f}GB")

# Token
at = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":CLIENT_ID,"client_secret":CLIENT_SEC,
    "refresh_token":RT,"grant_type":"refresh_token"},timeout=10).json().get("access_token")
if not at: print("ERRO token"); sys.exit(1)

# Upload resumível
file_size = os.path.getsize(OUT)
r = requests.post(
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    headers={"Authorization":f"Bearer {at}","Content-Type":"application/json",
             "X-Upload-Content-Type":"video/mp4","X-Upload-Content-Length":str(file_size)},
    json={"snippet":{"title":TITULO,"categoryId":"22","defaultLanguage":"en",
                     "defaultAudioLanguage":"en"},
          "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False,"madeForKids":False,
                    "license":"youtube","embeddable":True,"publicStatsViewable":True}},
    timeout=30)

if r.status_code != 200:
    print(f"ERRO init upload: {r.status_code} {r.text[:150]}"); sys.exit(1)

upload_url = r.headers["Location"]
print(f"Upload iniciado: {file_size/(1024**2):.0f}MB")

# Upload em chunks de 64MB
CHUNK = 64 * 1024 * 1024
uploaded = 0
with open(OUT, "rb") as f:
    while uploaded < file_size:
        chunk = f.read(CHUNK)
        end   = uploaded + len(chunk) - 1
        resp  = requests.put(upload_url,
            headers={"Content-Type":"video/mp4",
                     "Content-Range":f"bytes {uploaded}-{end}/{file_size}"},
            data=chunk, timeout=300)
        uploaded += len(chunk)
        pct = uploaded/file_size*100
        print(f"  {pct:.1f}%")
        if resp.status_code in (200,201):
            vid = resp.json().get("id","?")
            print(f"UPLOAD OK: {vid}")
            print(f"DONE {CANAL.upper()} = {vid}")
            sys.exit(0)
        elif resp.status_code not in (308,):
            print(f"ERRO upload: {resp.status_code} {resp.text[:100]}"); sys.exit(1)

print("ERRO: upload não completou")
sys.exit(1)
