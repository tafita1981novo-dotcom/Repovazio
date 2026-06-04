#!/usr/bin/env python3
"""
live_loop_v1.py - Live 24/7 simplificada com stream key manual
Usa a stream key configurada manualmente no YouTube Studio
Gera audio binaural + tela ψ para máximo watch time
"""
import os, sys, subprocess, pathlib, shutil, math, struct, wave, random, re, time, json
import urllib.request, urllib.parse
from datetime import datetime

STREAM_KEY = os.environ.get("YOUTUBE_STREAM_KEY","")
YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
DURATION_H = int(os.environ.get("DURATION_H","6"))
LANG = os.environ.get("LANG_CODE","pt")

RTMP_BASE = "rtmps://a.rtmps.youtube.com/live2"

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)

def ffm():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    for p in [shutil.which("ffmpeg"),"/usr/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists(): return p
    return "ffmpeg"

def get_token():
    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]): return ""
    data = urllib.parse.urlencode({
        "client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("access_token","")
    except: return ""

def criar_live_api(token):
    """Tenta criar live broadcast via API e retorna stream key"""
    from datetime import timezone, timedelta
    now = datetime.now(timezone.utc)
    start = now + timedelta(seconds=60)

    body = json.dumps({
        "snippet": {
            "title": "Psicologia e Comportamento Humano | Live 24/7 | @psidanicoelho",
            "description": "Daniela Coelho — Pesquisadora de Comportamento Humano\nConteúdo baseado em pesquisa científica\n#psicologia #comportamentohumano",
            "scheduledStartTime": start.strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
        "contentDetails": {"enableAutoStart": True, "enableAutoStop": True,
                           "recordFromStart": False, "latencyPreference": "ultraLow"}
    }).encode()

    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails",
        data=body, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type","application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            bc = json.loads(r.read())
        bc_id = bc.get("id","")
        if not bc_id: return None, None

        # Criar stream
        stream_body = json.dumps({
            "snippet": {"title": "Live Stream"},
            "cdn": {"ingestionType": "rtmp", "resolution": "1080p", "frameRate": "30fps"}
        }).encode()
        req2 = urllib.request.Request(
            "https://www.googleapis.com/youtube/v3/liveStreams?part=id,snippet,cdn,status",
            data=stream_body, method="POST")
        req2.add_header("Authorization", f"Bearer {token}")
        req2.add_header("Content-Type","application/json")

        with urllib.request.urlopen(req2, timeout=30) as r2:
            st = json.loads(r2.read())
        st_id  = st.get("id","")
        key    = st["cdn"]["ingestionInfo"]["streamName"]
        rtmp   = st["cdn"]["ingestionInfo"]["ingestionAddress"]

        # Associar
        req3 = urllib.request.Request(
            f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id&streamId={st_id}",
            data=b"{}", method="POST")
        req3.add_header("Authorization", f"Bearer {token}")
        req3.add_header("Content-Type","application/json")
        try: urllib.request.urlopen(req3, timeout=15)
        except: pass

        log(f"✅ Broadcast criado: {bc_id}")
        log(f"  RTMP: {rtmp}/{key[:12]}...")
        return bc_id, f"{rtmp}/{key}"

    except Exception as e:
        log(f"⚠️  API broadcast falhou ({e}), usando stream key manual")
        return None, None

def gerar_audio(path, duracao_s, freq_base=40, freq_beat=10):
    log(f"Gerando binaural {duracao_s//60}min ({freq_base}Hz+{freq_beat}Hz)...")
    SR = 44100; n = int(duracao_s * SR)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        CHUNK = SR  # 1s por chunk
        for start in range(0, n, CHUNK):
            frames = bytearray()
            for i in range(start, min(start+CHUNK, n)):
                t = i / SR
                amp = 0.22
                L = amp * math.sin(2*math.pi*freq_base*t)
                R = amp * math.sin(2*math.pi*(freq_base+freq_beat)*t)
                L += 0.06*math.sin(2*math.pi*freq_base*2*t)
                R += 0.06*math.sin(2*math.pi*(freq_base+freq_beat)*2*t)
                noise = random.gauss(0,0.012)
                lv = int(max(-32767, min(32767, (L+noise)*32767)))
                rv = int(max(-32767, min(32767, (R+noise)*32767)))
                frames.extend(struct.pack('<hh', lv, rv))
            wf.writeframes(bytes(frames))
    log(f"Audio gerado: {pathlib.Path(path).stat().st_size//1024}KB")

def transmitir(rtmp_full, audio_path, dur_s):
    ff = ffm()
    log(f"Iniciando transmissão {dur_s//3600}h...")
    log(f"FFmpeg: {ff}")

    # Overlay de texto dinâmico
    topics = [
        "Narcisismo Encoberto — Pesquisa Harvard",
        "Trauma de Infância — van der Kolk",
        "Apego Ansioso — Teoria de Ainsworth",
        "Gaslighting — Como Identificar",
        "Depressão Silenciosa — 8 Sinais",
        "Ansiedade Social — Neurociência",
    ]
    topic_str = " | ".join(topics)

    vf = (
        "drawbox=x=0:y=0:w=iw:h=ih:color=#06060F@1:t=fill,"  # Fundo escuro
        "drawtext=text=\\u03c8:fontsize=200:fontcolor=0x7C3AED@0.4:"
        "x=(w-text_w)/2:y=(h-text_h)/2-60,"  # Símbolo ψ
        "drawtext=text='@psidanicoelho':fontsize=36:fontcolor=white@0.5:"
        "x=(w-text_w)/2:y=(h-text_h)/2+120,"  # Handle
        "drawtext=text='Pesquisa em Psicologia e Comportamento Humano':"
        "fontsize=22:fontcolor=0x7C3AED@0.7:"
        "x=(w-text_w)/2:y=h-80"  # Legenda
    )

    cmd = [
        ff, "-y", "-re",
        "-f","lavfi","-i",f"color=c=#06060F:size=1920x1080:r=25:d={dur_s}",
        "-stream_loop","-1","-i",str(audio_path),
        "-map","0:v","-map","1:a",
        "-vf", vf,
        "-c:v","libx264","-preset","veryfast","-crf","28",
        "-b:v","1500k","-maxrate","2000k","-bufsize","4000k",
        "-g","50","-r","25","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
        "-f","flv","-t",str(dur_s),
        rtmp_full
    ]

    log(f"RTMP: {rtmp_full[:60]}...")
    result = subprocess.run(cmd, timeout=dur_s+600)
    log(f"Transmissão encerrada (rc={result.returncode})")
    return result.returncode == 0

def main():
    log("="*65)
    log(f"LIVE LOOP V1 — LANG={LANG} | {DURATION_H}h")
    log("="*65)

    # Tentar criar via API primeiro
    token = get_token()
    rtmp_url = None
    bc_id = None

    if token:
        log("Tentando criar broadcast via API...")
        bc_id, rtmp_url = criar_live_api(token)

    # Fallback: stream key manual
    if not rtmp_url:
        if not STREAM_KEY:
            log("❌ Sem RTMP URL e sem STREAM_KEY! Abortando.")
            sys.exit(1)
        rtmp_url = f"{RTMP_BASE}/{STREAM_KEY}"
        log(f"Usando stream key manual: {STREAM_KEY[:8]}...")

    # Gerar audio binaural
    TMP = pathlib.Path("/tmp")
    audio = TMP/"binaural.wav"

    freqs = {"pt":(40,10),"en":(40,10),"de":(14,6),"ja":(10,4),"ko":(40,10),"es":(40,10),"fr":(40,10)}
    fb, beat = freqs.get(LANG,(40,10))
    gerar_audio(audio, DURATION_H*3600, fb, beat)

    # Transmitir
    ok = transmitir(rtmp_url, audio, DURATION_H*3600)

    # Encerrar broadcast se criado via API
    if bc_id and token:
        try:
            req = urllib.request.Request(
                f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition"
                f"?broadcastStatus=complete&id={bc_id}&part=id",
                data=b"{}", method="POST")
            req.add_header("Authorization", f"Bearer {token}")
            req.add_header("Content-Type","application/json")
            urllib.request.urlopen(req, timeout=15)
            log(f"Broadcast encerrado: {bc_id}")
        except: pass

    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
