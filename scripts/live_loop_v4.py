#!/usr/bin/env python3
"""
live_loop_v4.py — LIVE 24/7 FINAL PRODUÇÃO
FIXES:
  - Broadcast body simplificado (remove campos que causam 400)
  - ffmpeg: color=black (compatível com imageio_ffmpeg)
  - Background PNG gerado com PIL (sem drawtext no ffmpeg)
  - Audio 60s em loop (sem arquivo 3.8GB)
  - Retry automático em caso de queda
"""
import os, sys, subprocess, pathlib, shutil, math, struct, wave, random, json, time
import urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

STREAM_KEY       = os.environ.get("YOUTUBE_STREAM_KEY","")
YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
DURATION_H       = int(os.environ.get("DURATION_H","6"))
LANG             = os.environ.get("LANG_CODE","pt")
RTMP_BASE        = "rtmps://a.rtmps.youtube.com/live2"

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERRO {m}", flush=True, file=sys.stderr)

def ffm():
    try:
        import imageio_ffmpeg; f=imageio_ffmpeg.get_ffmpeg_exe()
        log(f"FFmpeg: {f}"); return f
    except: pass
    for p in [shutil.which("ffmpeg"),"/usr/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists(): return p
    return "ffmpeg"

def get_token():
    if not all([YT_CLIENT_ID,YT_CLIENT_SECRET,YT_REFRESH_TOKEN]): return ""
    data = urllib.parse.urlencode({
        "client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
        "refresh_token":YT_REFRESH_TOKEN,"grant_type":"refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token",data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read()).get("access_token","")
    except Exception as e: err(f"Token: {e}"); return ""

def criar_broadcast(token):
    """Broadcast simplificado — sem campos que causam 400"""
    now = datetime.now(timezone.utc)
    start = (now + timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ")
    titulos = {
        "pt":"ψ Psicologia e Comportamento Humano | Binaural 24h | @psidanicoelho",
        "en":"ψ Psychology & Human Behavior | Binaural 24h | @psidanicoelho",
        "es":"ψ Psicologia y Comportamiento | Binaural 24h | @psidanicoelho",
        "de":"ψ Psychologie und Verhalten | Binaural 24h | @psidanicoelho",
        "fr":"ψ Psychologie Comportement | Binaural 24h | @psidanicoelho",
    }
    body = json.dumps({
        "snippet":{"title":titulos.get(LANG,titulos["pt"]),
                   "scheduledStartTime":start},
        "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False},
        "contentDetails":{"enableAutoStart":True,"enableAutoStop":True}
    }).encode()
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails",
        data=body,method="POST")
    req.add_header("Authorization",f"Bearer {token}")
    req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            bc=json.loads(r.read())
        bc_id=bc.get("id","")
        log(f"Broadcast: {bc_id} ✅"); return bc_id
    except urllib.error.HTTPError as e:
        err(f"Broadcast {e.code}: {e.read().decode()[:200]}")
        return None

def criar_stream(token):
    """Cria live stream e retorna (stream_id, rtmp_url)"""
    body = json.dumps({
        "snippet":{"title":"Live @psidanicoelho"},
        "cdn":{"ingestionType":"rtmp","resolution":"1080p","frameRate":"30fps"}
    }).encode()
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/liveStreams?part=id,snippet,cdn",
        data=body,method="POST")
    req.add_header("Authorization",f"Bearer {token}")
    req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            st=json.loads(r.read())
        st_id=st.get("id","")
        info=st["cdn"]["ingestionInfo"]
        rtmp=f"{info['ingestionAddress']}/{info['streamName']}"
        log(f"Stream: {st_id} ✅")
        return st_id, rtmp
    except Exception as e:
        err(f"Stream: {e}"); return None, None

def vincular(token, bc_id, st_id):
    req = urllib.request.Request(
        f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id&streamId={st_id}",
        data=b"{}",method="POST")
    req.add_header("Authorization",f"Bearer {token}")
    req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=15): log("Vinculado ✅")
    except Exception as e: err(f"Vincular: {e}")

def gerar_bg(path_png):
    """Gera imagem de fundo com PIL (sem dependencia de drawtext no ffmpeg)"""
    try:
        from PIL import Image, ImageDraw
        W,H=1920,1080
        img = Image.new("RGB",(W,H),(6,6,15))
        draw = ImageDraw.Draw(img)
        # Circulo central roxo
        cx,cy,r=W//2,H//2,220
        for i in range(8,0,-1):
            alpha_fill=(124,58,237) if i==1 else tuple(max(0,min(255,int(v*(i/8)*0.4))) for v in (124,58,237))
            draw.ellipse([(cx-r-i*12,cy-r-i*12),(cx+r+i*12,cy+r+i*12)],fill=alpha_fill)
        img.save(str(path_png),"PNG")
        log(f"Background PNG: {path_png} ✅")
        return True
    except Exception as e:
        err(f"PIL: {e}"); return False

def gerar_audio(path, freq_base=40, freq_beat=10):
    """Gera 60s de binaural com fade in/out para loop perfeito"""
    SR=44100; dur=60; n=int(dur*SR)
    log(f"Binaural: {freq_base}Hz+{freq_beat}Hz | 60s")
    with wave.open(str(path),"w") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        for start in range(0,n,SR):
            frames=bytearray()
            for i in range(start,min(start+SR,n)):
                t=i/SR
                fade=1.0
                if i<SR//4: fade=i/(SR//4)
                elif i>n-SR//4: fade=(n-i)/(SR//4)
                L=fade*0.22*math.sin(2*math.pi*freq_base*t)
                R=fade*0.22*math.sin(2*math.pi*(freq_base+freq_beat)*t)
                noise=random.gauss(0,0.008)
                lv=int(max(-32767,min(32767,(L+noise)*32767)))
                rv=int(max(-32767,min(32767,(R+noise)*32767)))
                frames.extend(struct.pack('<hh',lv,rv))
            wf.writeframes(bytes(frames))
    log(f"Audio OK: {pathlib.Path(path).stat().st_size//1024}KB")

def transmitir(rtmp_url, audio_path, bg_png, dur_s):
    ff = ffm()
    log(f"Transmitindo {dur_s//3600}h...")
    log(f"RTMP: {rtmp_url[:70]}...")

    # Se bg_png existe, usar como imagem de fundo
    if bg_png and pathlib.Path(bg_png).exists():
        cmd = [
            ff,"-y","-re",
            # Imagem de fundo em loop
            "-loop","1","-i",str(bg_png),
            # Audio binaural em loop
            "-stream_loop","-1","-i",str(audio_path),
            "-map","0:v","-map","1:a",
            "-c:v","libx264","-preset","ultrafast","-crf","28",
            "-b:v","800k","-maxrate","1000k","-bufsize","2000k",
            "-g","50","-keyint_min","50","-r","25","-pix_fmt","yuv420p",
            "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
            "-f","flv","-t",str(dur_s),
            rtmp_url
        ]
    else:
        # Fallback: tela preta simples
        cmd = [
            ff,"-y","-re",
            "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
            "-stream_loop","-1","-i",str(audio_path),
            "-map","0:v","-map","1:a",
            "-c:v","libx264","-preset","ultrafast","-crf","28",
            "-b:v","800k","-maxrate","1000k","-bufsize","2000k",
            "-g","50","-keyint_min","50","-r","25","-pix_fmt","yuv420p",
            "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
            "-f","flv","-t",str(dur_s),
            rtmp_url
        ]

    result = subprocess.run(cmd, timeout=dur_s+900)
    log(f"FFmpeg rc={result.returncode}")
    return result.returncode in (0,255,-2,-15)

def encerrar(token, bc_id):
    if not bc_id or not token: return
    req=urllib.request.Request(
        f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bc_id}&part=id",
        data=b"{}",method="POST")
    req.add_header("Authorization",f"Bearer {token}")
    req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=15): log(f"Live {bc_id} encerrada ✅")
    except Exception as e: err(f"Encerrar: {e}")

def main():
    log("="*65)
    log(f"LIVE LOOP V4 | {LANG} | {DURATION_H}h | {datetime.now():%Y-%m-%d %H:%M} UTC")
    log("="*65)

    token = get_token()
    bc_id=None; rtmp_url=None

    if token:
        log("Criando live via API...")
        bc_id = criar_broadcast(token)
        if bc_id:
            st_id, rtmp_url = criar_stream(token)
            if bc_id and st_id: vincular(token, bc_id, st_id)

    if not rtmp_url:
        if not STREAM_KEY:
            err("Sem RTMP! Configure YOUTUBE_STREAM_KEY nos secrets.")
            sys.exit(1)
        rtmp_url = f"{RTMP_BASE}/{STREAM_KEY}"
        log(f"Stream key manual: {STREAM_KEY[:12]}...")

    # Gerar assets
    TMP = pathlib.Path("/tmp")
    audio = TMP/"binaural.wav"
    bg_png = TMP/"live_bg.png"

    freqs={"pt":(40,10),"en":(40,10),"de":(14,6),"ja":(10,4),"ko":(40,10),"es":(40,10),"fr":(40,10)}
    fb,beat=freqs.get(LANG,(40,10))
    gerar_audio(audio, fb, beat)
    gerar_bg(bg_png)

    # Transmitir (com retry automático se cair)
    dur_s = DURATION_H * 3600
    inicio = time.time()
    tentativas = 0; max_tentativas = 10

    while time.time()-inicio < dur_s and tentativas < max_tentativas:
        restante = int(dur_s - (time.time()-inicio))
        if restante < 60: break
        tentativas += 1
        log(f"Transmitindo (tentativa {tentativas}) | restante: {restante//3600}h{(restante%3600)//60}m")
        ok = transmitir(rtmp_url, audio, str(bg_png), restante)
        if ok: break
        log("Reconectando em 10s...")
        time.sleep(10)

    encerrar(token, bc_id)
    log(f"Live concluída após {(time.time()-inicio)//60:.0f}min")

if __name__ == "__main__":
    main()
