#!/usr/bin/env python3
"""
live_loop_v3.py — Live 24/7 PRODUÇÃO FINAL
- SEM drawtext (imageio_ffmpeg não tem libfreetype)
- Audio binaural 60s em loop (evita arquivo 3.8GB)
- Cria broadcast via YouTube API (auto-start)
- Fallback: stream key manual
- Tela escura simples #06060F = branding mínimo
"""
import os, sys, subprocess, pathlib, shutil, math, struct, wave, random, json
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
        import imageio_ffmpeg
        f = imageio_ffmpeg.get_ffmpeg_exe()
        log(f"FFmpeg (imageio): {f}")
        return f
    except: pass
    for p in [shutil.which("ffmpeg"), "/usr/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists():
            log(f"FFmpeg (sys): {p}"); return p
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
    except Exception as e:
        err(f"Token: {e}"); return ""

def criar_live_api(token):
    """Cria broadcast + stream e retorna (bc_id, rtmp_url)"""
    now   = datetime.now(timezone.utc)
    start = now + timedelta(seconds=60)

    titulos = {
        "pt": "ψ Psicologia e Comportamento Humano | Live 24h | @psidanicoelho",
        "en": "ψ Psychology & Human Behavior | 24h Live | @psidanicoelho",
        "es": "ψ Psicología y Comportamiento Humano | En Vivo 24h | @psidanicoelho",
        "de": "ψ Psychologie und menschliches Verhalten | Live 24h | @psidanicoelho",
        "fr": "ψ Psychologie et Comportement Humain | En Direct 24h | @psidanicoelho",
    }
    titulo = titulos.get(LANG, titulos["pt"])

    bc_body = json.dumps({
        "snippet": {
            "title": titulo,
            "description": (
                "Daniela Coelho — Pesquisadora de Comportamento Humano\n"
                "Baseado em pesquisas de Harvard, UCLA e University of Texas\n\n"
                "#psicologia #comportamentohumano #danielacoelho"
            ),
            "scheduledStartTime": start.strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "madeForKids": False},
        "contentDetails": {
            "enableAutoStart": True, "enableAutoStop": True,
            "recordFromStart": False, "latencyPreference": "ultraLow", "enableDvr": False
        }
    }).encode()

    try:
        req = urllib.request.Request(
            "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails",
            data=bc_body, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type","application/json")
        with urllib.request.urlopen(req, timeout=30) as r:
            bc = json.loads(r.read())
        bc_id = bc.get("id","")
        if not bc_id: return None, None
        log(f"Broadcast: {bc_id} ✅")
    except Exception as e:
        err(f"Broadcast: {e}"); return None, None

    try:
        st_body = json.dumps({
            "snippet": {"title": "Live @psidanicoelho"},
            "cdn": {"ingestionType": "rtmp", "resolution": "1080p", "frameRate": "30fps"}
        }).encode()
        req2 = urllib.request.Request(
            "https://www.googleapis.com/youtube/v3/liveStreams?part=id,snippet,cdn,status",
            data=st_body, method="POST")
        req2.add_header("Authorization", f"Bearer {token}")
        req2.add_header("Content-Type","application/json")
        with urllib.request.urlopen(req2, timeout=30) as r:
            st = json.loads(r.read())
        st_id = st.get("id","")
        info  = st["cdn"]["ingestionInfo"]
        rtmp  = f"{info['ingestionAddress']}/{info['streamName']}"
        log(f"Stream: {st_id} ✅")
    except Exception as e:
        err(f"Stream: {e}"); return bc_id, None

    try:
        req3 = urllib.request.Request(
            f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id&streamId={st_id}",
            data=b"{}", method="POST")
        req3.add_header("Authorization", f"Bearer {token}")
        req3.add_header("Content-Type","application/json")
        with urllib.request.urlopen(req3, timeout=15): pass
        log("Broadcast vinculado ao stream ✅")
    except Exception as e:
        err(f"Bind: {e}")

    return bc_id, rtmp

def gerar_audio(path, freq_base=40, freq_beat=10):
    """Gera 60s de binaural — loop via ffmpeg (economiza memória)"""
    SR = 44100; dur = 60; n = int(dur * SR)
    log(f"Binaural: {freq_base}Hz carrier + {freq_beat}Hz beat | 60s loop")
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        for start in range(0, n, SR):
            frames = bytearray()
            for i in range(start, min(start+SR, n)):
                t = i / SR
                fade = 1.0
                if i < SR//4: fade = i / (SR//4)
                elif i > n - SR//4: fade = (n-i)/(SR//4)
                L = fade * 0.22 * math.sin(2*math.pi*freq_base*t)
                R = fade * 0.22 * math.sin(2*math.pi*(freq_base+freq_beat)*t)
                L += fade * 0.05 * math.sin(2*math.pi*freq_base*2*t)
                R += 0.02 * random.gauss(0, 1)
                lv = int(max(-32767, min(32767, L*32767)))
                rv = int(max(-32767, min(32767, R*32767)))
                frames.extend(struct.pack('<hh', lv, rv))
            wf.writeframes(bytes(frames))
    log(f"Audio OK: {pathlib.Path(path).stat().st_size//1024}KB")

def transmitir(rtmp_url, audio_path, dur_s):
    """Transmite tela escura + binaural em loop"""
    ff = ffm()
    log(f"Transmitindo {dur_s//3600}h → {rtmp_url[:60]}...")

    # SEM drawtext — imageio_ffmpeg não tem libfreetype
    # Video: cor sólida escura (branding via thumbnail/title)
    cmd = [
        ff, "-y", "-re",
        # Video: tela escura simples (sem filtros externos)
        "-f","lavfi","-i","color=c=0x06060F:size=1920x1080:rate=25",
        # Audio binaural em loop infinito (-stream_loop -1)
        "-stream_loop","-1","-i",str(audio_path),
        # Mapear video + audio
        "-map","0:v","-map","1:a",
        # Codec video: ultra-rápido sem filtros complexos
        "-c:v","libx264","-preset","ultrafast","-crf","28",
        "-b:v","800k","-maxrate","1000k","-bufsize","2000k",
        "-g","50","-keyint_min","50","-r","25","-pix_fmt","yuv420p",
        # Codec audio
        "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
        # Saída RTMP com duração limitada
        "-f","flv","-t",str(dur_s),
        rtmp_url
    ]

    result = subprocess.run(cmd, timeout=dur_s + 900)
    rc = result.returncode
    log(f"FFmpeg rc={rc}")
    return rc in (0, 255, -2)  # 0=sucesso, 255=SIGTERM normal, -2=SIGINT

def encerrar_live(bc_id, token):
    if not bc_id or not token: return
    req = urllib.request.Request(
        f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition"
        f"?broadcastStatus=complete&id={bc_id}&part=id",
        data=b"{}", method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req, timeout=15): pass
        log(f"Live {bc_id} encerrada ✅")
    except Exception as e:
        err(f"Encerrar live: {e}")

def main():
    log("="*65)
    log(f"LIVE LOOP V3 | lang={LANG} | {DURATION_H}h | {datetime.now():%Y-%m-%d %H:%M} UTC")
    log("="*65)

    token = get_token()
    bc_id = None; rtmp_url = None

    if token:
        log("Criando live via YouTube API...")
        bc_id, rtmp_url = criar_live_api(token)

    if not rtmp_url:
        if not STREAM_KEY:
            err("Sem RTMP! Configure YOUTUBE_STREAM_KEY no GitHub Secrets")
            sys.exit(1)
        rtmp_url = f"{RTMP_BASE}/{STREAM_KEY}"
        log(f"Stream key manual: {STREAM_KEY[:12]}...")

    # Gerar audio 60s (loop via ffmpeg)
    audio = pathlib.Path("/tmp/binaural.wav")
    freqs = {"pt":(40,10),"en":(40,10),"de":(14,6),"ja":(10,4),"ko":(40,10),"es":(40,10),"fr":(40,10)}
    fb, beat = freqs.get(LANG, (40, 10))
    gerar_audio(audio, fb, beat)

    # Transmitir
    ok = transmitir(rtmp_url, audio, DURATION_H * 3600)
    encerrar_live(bc_id, token)

    log(f"Live concluída: {'✅' if ok else '❌'}")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
