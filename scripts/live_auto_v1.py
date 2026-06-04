#!/usr/bin/env python3
"""
live_auto_v1.py - Live 24/7 com criacao automatica via YouTube API
FLUXO:
  1. Cria live broadcast via API (auto-start)
  2. Associa stream key
  3. Inicia ffmpeg para transmitir
  4. Conteudo: audio binaural + conteudo psicologia em loop
"""
import os, sys, json, time, subprocess, pathlib, wave, struct, math, shutil
import urllib.request, urllib.parse, random, re
from datetime import datetime, timezone, timedelta

YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
SBU = os.environ.get("SUPABASE_URL","")
SBK = os.environ.get("SUPABASE_SERVICE_KEY","")
DURATION_H = int(os.environ.get("DURATION_H","6"))
LANG       = os.environ.get("LANG_CODE","pt")

LIVE_TITLES = {
    "pt": ["Psicologia do Trauma | Binaural Foco 432Hz | Daniela Coelho",
           "Narcisismo Encoberto | Psicologia Profunda 24h | @psidanicoelho",
           "Ansiedade e Apego | Sons Binaurais | Pesquisa em Psicologia"],
    "en": ["Dark Psychology | Binaural Focus 432Hz | 24/7 Live",
           "Covert Narcissism | Deep Psychology | Live Research",
           "Attachment Theory | Binaural Sounds | Psychology Live"],
    "es": ["Psicología del Trauma | Binaural 432Hz | En Vivo 24h",
           "Narcisismo Encubierto | Psicología Profunda | En Directo",
           "Ansiedad y Apego | Sonidos Binaurales | Psicología Live"],
    "de": ["Psychologie des Traumas | Binaural 432Hz | Live 24h",
           "Verdeckter Narzissmus | Tiefenpsychologie | Live",
           "Bindungsangst | Binaurale Klange | Psychologie Live"],
    "fr": ["Psychologie du Trauma | Binaural 432Hz | 24h en Direct",
           "Narcissisme Masque | Psychologie Profonde | Live",
           "Anxiete et Attachement | Sons Binauraux | Psychologie"],
}

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERRO {m}", flush=True, file=sys.stderr)

def ffm():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    for p in [shutil.which("ffmpeg"),"/usr/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists(): return p
    return "ffmpeg"

def get_token():
    data = urllib.parse.urlencode({
        "client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read()).get("access_token","")

def yt_api(endpoint, data=None, method="GET", token=""):
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:300]
        err(f"API {method} {endpoint}: {e.code} | {err_body}")
        return {}, e.code

def criar_live_broadcast(token, title, lang="pt"):
    """Cria live broadcast e stream key via YouTube API"""
    now = datetime.now(timezone.utc)
    start = now + timedelta(seconds=30)

    # 1. Criar broadcast
    broadcast_data = {
        "snippet": {
            "title": title[:100],
            "description": (
                "Conteudo de psicologia e comportamento humano baseado em pesquisa cientifica.\n\n"
                "@psidanicoelho | Daniela Coelho — Pesquisadora de Comportamento Humano"
            ),
            "scheduledStartTime": start.strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids": False
        },
        "contentDetails": {
            "enableAutoStart": True,
            "enableAutoStop": True,
            "recordFromStart": False,
            "enableDvr": False,
            "latencyPreference": "ultraLow"
        }
    }
    broadcast, bc_status = yt_api(
        "liveBroadcasts?part=id,snippet,status,contentDetails",
        broadcast_data, "POST", token)

    if bc_status not in (200, 201) or not broadcast.get("id"):
        err(f"Broadcast nao criado: {bc_status}")
        return None, None, None

    broadcast_id = broadcast["id"]
    log(f"  Broadcast criado: {broadcast_id}")

    # 2. Criar stream (chave de stream)
    stream_data = {
        "snippet": {"title": f"Stream {title[:30]}"},
        "cdn": {
            "ingestionType": "rtmp",
            "resolution": "1080p",
            "frameRate": "30fps"
        }
    }
    stream, st_status = yt_api(
        "liveStreams?part=id,snippet,cdn,status",
        stream_data, "POST", token)

    if st_status not in (200, 201) or not stream.get("id"):
        err(f"Stream nao criada: {st_status}")
        return broadcast_id, None, None

    stream_id  = stream["id"]
    stream_key = stream["cdn"]["ingestionInfo"]["streamName"]
    rtmp_url   = stream["cdn"]["ingestionInfo"]["ingestionAddress"]
    log(f"  Stream criada: {stream_id}")
    log(f"  RTMP: {rtmp_url}")

    # 3. Associar broadcast + stream
    yt_api(
        f"liveBroadcasts/bind?id={broadcast_id}&part=id&streamId={stream_id}",
        {}, "POST", token)
    log(f"  Broadcast associado ao stream")

    return broadcast_id, stream_id, f"{rtmp_url}/{stream_key}"

def gerar_audio_binaural(path, duracao_s=3600, freq_base=40, freq_beat=10):
    """Gera audio binaural de alta qualidade para foco/relaxamento"""
    log(f"  Gerando binaural {duracao_s//60}min @ {freq_base}Hz beat {freq_beat}Hz...")
    SR = 44100
    n  = int(duracao_s * SR)
    ch = 2

    with wave.open(str(path), "w") as wf:
        wf.setnchannels(ch); wf.setsampwidth(2); wf.setframerate(SR)
        CHUNK = 44100  # 1s por vez para economizar memória
        for start in range(0, n, CHUNK):
            end = min(start + CHUNK, n)
            frames = bytearray()
            for i in range(start, end):
                t = i / SR
                # Canal esquerdo: freq_base Hz
                # Canal direito: freq_base + freq_beat Hz
                # Isso cria o batimento binaural no cérebro
                amp = 0.25
                envelope = 1.0 - 0.03 * math.sin(2*math.pi*0.05*t)  # leve fade
                left  = amp * envelope * math.sin(2*math.pi*freq_base*t)
                right = amp * envelope * math.sin(2*math.pi*(freq_base+freq_beat)*t)
                # Adicionar harmônicos suaves para enriquecer
                left  += 0.08*math.sin(2*math.pi*freq_base*2*t)
                right += 0.08*math.sin(2*math.pi*(freq_base+freq_beat)*2*t)
                # Noise rosa leve para naturalidade
                noise = random.gauss(0, 0.015)
                lv = int(max(-32767, min(32767, (left + noise) * 32767)))
                rv = int(max(-32767, min(32767, (right + noise) * 32767)))
                frames.extend(struct.pack('<hh', lv, rv))
            wf.writeframes(bytes(frames))

def criar_video_bg(path_out, duracao_s=600):
    """Gera video de fundo com visualizacao cinematografica"""
    ff = ffm()
    subprocess.run([
        ff, "-y",
        "-f","lavfi",
        "-i",f"color=c=#06060F:size=1920x1080:r=25:d={duracao_s}",
        "-vf",(
            f"drawtext=text='ψ':fontsize=120:fontcolor=0x7C3AED@0.6:"
            f"x=(w-text_w)/2:y=(h-text_h)/2,"
            f"drawtext=text='@psidanicoelho':fontsize=28:fontcolor=white@0.4:"
            f"x=16:y=h-50"
        ),
        "-c:v","libx264","-preset","ultrafast","-crf","35",
        "-pix_fmt","yuv420p","-r","25","-t",str(duracao_s),
        str(path_out)
    ], capture_output=True, timeout=120)

def transmitir(rtmp_full_url, audio_path, duracao_s):
    """Transmite via ffmpeg para o RTMP do YouTube"""
    ff = ffm()
    log(f"  Iniciando transmissao {duracao_s//3600}h...")
    log(f"  RTMP: {rtmp_full_url[:50]}...")

    cmd = [
        ff, "-y", "-re",
        # Video: tela preta com simbolo psi
        "-f","lavfi","-i","color=c=#06060F:size=1920x1080:r=25",
        # Audio: binaural em loop
        "-stream_loop","-1","-i",str(audio_path),
        # Texto overlay
        "-vf",(
            "drawtext=text='\\u03c8':fontsize=150:fontcolor=0x7C3AED@0.5:"
            "x=(w-text_w)/2:y=(h-text_h)/2,"
            "drawtext=text='@psidanicoelho':fontsize=32:fontcolor=white@0.35:"
            "x=20:y=h-60,"
            "drawtext=text='Psicologia e Comportamento Humano':fontsize=24:"
            "fontcolor=white@0.25:x=(w-text_w)/2:y=h-95"
        ),
        "-map","0:v","-map","1:a",
        "-c:v","libx264","-preset","ultrafast","-crf","30",
        "-b:v","800k","-maxrate","1000k","-bufsize","2000k",
        "-g","50","-keyint_min","50","-r","25","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
        "-f","flv","-t",str(duracao_s),
        rtmp_full_url
    ]
    result = subprocess.run(cmd, timeout=duracao_s + 300)
    log(f"  Transmissao encerrada (rc={result.returncode})")
    return result.returncode == 0

def main():
    log("="*65)
    log(f"LIVE AUTO V1 — YouTube 24/7 | LANG={LANG} | {DURATION_H}h")
    log(f"FFmpeg: {ffm()}")
    log("="*65)

    # Obter token
    token = get_token()
    if not token: err("Sem token!"); sys.exit(1)
    log(f"Token: {token[:20]}... OK")

    # Selecionar titulo
    titles = LIVE_TITLES.get(LANG, LIVE_TITLES["pt"])
    title = random.choice(titles)
    log(f"Live: {title}")

    # Criar broadcast e stream
    log("Criando live broadcast via API...")
    broadcast_id, stream_id, rtmp_url = criar_live_broadcast(token, title, LANG)

    if not rtmp_url:
        err("Nao foi possivel criar live via API!")
        # Fallback: usar stream key configurada manualmente
        STREAM_KEY = os.environ.get("YOUTUBE_STREAM_KEY","")
        if STREAM_KEY:
            log(f"Usando stream key manual: {STREAM_KEY[:8]}...")
            rtmp_url = f"rtmps://a.rtmps.youtube.com/live2/{STREAM_KEY}"
        else:
            err("Sem stream key!"); sys.exit(1)

    log(f"RTMP: {rtmp_url[:60]}...")

    # Gerar audio binaural
    TMP = pathlib.Path("/tmp"); TMP.mkdir(exist_ok=True)
    audio_path = TMP/"binaural_live.wav"

    freq_por_lang = {"pt":40,"en":40,"es":40,"de":14,"fr":40,"ja":10,"ko":40}
    freq_base = freq_por_lang.get(LANG, 40)
    gerar_audio_binaural(audio_path, 3600, freq_base, 10)

    # Transmitir
    duracao_s = DURATION_H * 3600
    ok = transmitir(rtmp_url, audio_path, duracao_s)

    if ok:
        log(f"Live concluida com sucesso! {DURATION_H}h de transmissao")
    else:
        err(f"Live encerrada com erro")

    # Marcar broadcast como encerrado
    if broadcast_id:
        try:
            yt_api(f"liveBroadcasts/transition?broadcastStatus=complete&id={broadcast_id}&part=id",
                   {}, "POST", token)
            log(f"Broadcast marcado como complete: {broadcast_id}")
        except: pass

if __name__ == "__main__":
    main()
