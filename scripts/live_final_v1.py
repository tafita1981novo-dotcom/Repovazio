#!/usr/bin/env python3
"""
live_final_v1.py — LIVE 24/7 TELA PRETA DEFINITIVA
BUGS CORRIGIDOS:
  ✅ Removido amplitude=0.28 (não existe no filtro sine do ffmpeg 7)
  ✅ Volume controlado via filtro volume= após amerge
  ✅ Fallback para sine simples se amerge falhar
  ✅ Tela 100% preta garantida (color=black)
  ✅ Binaural real: L=430Hz R=432Hz (beat 2Hz = delta)
SEO GLOBAL: "tela preta" + "binaural 432hz" + "dark psychology" em 8 idiomas
"""
import os, sys, subprocess, pathlib, shutil, json, urllib.request, urllib.parse, time, math, struct, wave, random
from datetime import datetime, timezone, timedelta

YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
STREAM_KEY       = os.environ.get("YOUTUBE_STREAM_KEY","")
DURATION_H       = int(os.environ.get("DURATION_H","6"))
LANG             = os.environ.get("LANG_CODE","pt")
RTMP_BASE        = "rtmps://a.rtmps.youtube.com/live2"
TMP              = pathlib.Path("/tmp")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERRO: {m}", flush=True, file=sys.stderr)

def ffm():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    for p in [shutil.which("ffmpeg"),"/usr/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists(): return p
    return "ffmpeg"

def get_token():
    data=urllib.parse.urlencode({"client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
        "refresh_token":YT_REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    req=urllib.request.Request("https://oauth2.googleapis.com/token",data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read()).get("access_token","")
    except Exception as e: err(f"Token: {e}"); return ""

# ─── TESTE DO FFMPEG ────────────────────────────────
def testar_ffmpeg():
    """Testa se sine funciona e qual sintaxe usar"""
    ff = ffm()
    # Teste 1: sine com amerge (binaural real)
    r = subprocess.run([ff,"-y","-t","1",
        "-f","lavfi","-i","sine=frequency=430:sample_rate=44100",
        "-f","lavfi","-i","sine=frequency=432:sample_rate=44100",
        "-filter_complex","[0:a][1:a]amerge=inputs=2,volume=0.5[a]",
        "-map","[a]","-c:a","aac","-b:a","64k","-f","null","-"],
        capture_output=True, timeout=15)
    if r.returncode == 0:
        log("✅ Teste binaural amerge: OK")
        return "binaural"
    log(f"❌ Binaural amerge falhou (rc={r.returncode})")
    log(f"   Stderr: {r.stderr.decode()[-200:]}")

    # Teste 2: sine simples (mono)
    r2 = subprocess.run([ff,"-y","-t","1",
        "-f","lavfi","-i","sine=frequency=432:sample_rate=44100",
        "-c:a","aac","-b:a","64k","-f","null","-"],
        capture_output=True, timeout=15)
    if r2.returncode == 0:
        log("✅ Teste sine simples: OK")
        return "sine_mono"
    log(f"❌ Sine mono falhou")

    # Teste 3: anullsrc (silêncio) — garantido funcionar
    log("⚠️  Usando anullsrc (silêncio) como fallback")
    return "anullsrc"

# ─── SEO VIRAL ──────────────────────────────────────
TITULOS = {
    "pt": [
        "🔴 AO VIVO 24H ψ TELA PRETA + Binaural 432Hz Dark Psychology | Dormir Focar Meditar",
        "🔴 LIVE ψ TELA PRETA 24/7 | Binaural Beats 432Hz | Psicologia | @psidanicoelho",
        "🔴 AO VIVO ψ Tela Preta para Dormir | Binaural 432Hz | Dark Psychology | Foco Total",
    ],
    "en": [
        "🔴 LIVE 24H ψ BLACK SCREEN + Binaural 432Hz Dark Psychology | Sleep Focus Meditate",
        "🔴 LIVE ψ BLACK SCREEN 24/7 | Binaural Beats 432Hz | Psychology | @psidanicoelho",
    ],
    "de": ["🔴 LIVE 24H ψ SCHWARZER BILDSCHIRM | Binaural 432Hz | Psychologie | Schlafen Focus"],
    "es": ["🔴 EN VIVO 24H ψ PANTALLA NEGRA | Binaural 432Hz | Psicología Oscura | Dormir"],
    "fr": ["🔴 EN DIRECT 24H ψ ÉCRAN NOIR | Binaural 432Hz | Psychologie | Dormir Focus"],
    "it": ["🔴 IN DIRETTA 24H ψ SCHERMO NERO | Binaural 432Hz | Psicologia | Dormire"],
    "ja": ["🔴 24H LIVE ψ 黒い画面 | バイノーラル432Hz | 心理学 | 睡眠集中瞑想"],
    "ko": ["🔴 24H 라이브 ψ 검은화면 | 바이노럴 432Hz | 심리학 | 수면집중명상"],
}

DESC = """🔴 AO VIVO 24H — ψ TELA PRETA • BINAURAL 432Hz • DARK PSYCHOLOGY

Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho
Baseado em pesquisa científica (Harvard, UCLA, University of Texas)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖤 TELA 100% PRETA — zero distração visual
🎵 BINAURAL 432Hz — 430Hz (esq) + 432Hz (dir) = beat 2Hz DELTA
   Ondas Delta: relaxamento profundo + sono restaurador
   40Hz Gamma: foco e concentração máxima
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ IDEAL PARA: Dormir • Estudar • Meditar • Trabalhar • Focar

🧠 CONTEÚDO DE PSICOLOGIA:
• Narcisismo Encoberto | Trauma de Infância | Ansiedade Social
• Dark Psychology | Apego Ansioso | Gaslighting | Manipulação

📚 FONTES: Harvard Medical School • UCLA • University of Texas

💬 Super Chat: pergunte sobre psicologia!
❤️ Super Thanks: apoie a pesquisa!
🔔 ATIVE O SINO para novos estudos!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 DISPONÍVEL EM 8 IDIOMAS:
BLACK SCREEN • TELA PRETA • PANTALLA NEGRA • ÉCRAN NOIR
SCHWARZER BILDSCHIRM • SCHERMO NERO • 黒い画面 • 검은 화면

#telapreta #blackscreen #binaural432hz #432hz #psicologia
#narcisismo #trauma #darkpsychology #danielacoelho #psidanicoelho
#binauralbeats #sleepmusic #studymusic #focusmusic #terapia
#schwarzerbildschirm #pantallenegra #aovivo #live24h #meditacao
#concentracao #focototal #comportamentohumano #saúdementalimporta"""

TAGS = [
    "tela preta","tela preta para dormir","tela preta 8 horas","tela preta binaural",
    "black screen","black screen sleep","black screen 8 hours","black screen binaural beats",
    "schwarzer bildschirm","pantalla negra","écran noir","schermo nero","黒い画面","검은 화면",
    "binaural beats 432hz","432hz","binaural 432hz","binaural beats","binaural beats sleep",
    "binaural beats focus","binaural beats study","dark psychology","psicologia",
    "narcisismo","trauma","ansiedade","apego","comportamento humano",
    "narcissism","covert narcissist","psychology","mental health",
    "daniela coelho","psidanicoelho","sleep music","study music","focus music",
    "música para dormir","música para estudar","música de foco","meditação",
    "tela preta concentração","black screen study","pantalla negra dormir",
]

def criar_live(token):
    titulo = random.choice(TITULOS.get(LANG, TITULOS["pt"]))
    log(f"Título: {titulo[:80]}")
    now = datetime.now(timezone.utc)
    start = (now + timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ")
    bc_body = json.dumps({
        "snippet":{"title":titulo[:100],"scheduledStartTime":start,
                   "description":DESC[:4900],"categoryId":"22","defaultLanguage":LANG},
        "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False,"madeForKids":False},
        "contentDetails":{"enableAutoStart":True,"enableAutoStop":True}
    }).encode()
    req=urllib.request.Request("https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails",data=bc_body,method="POST")
    req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            bc=json.loads(r.read()); bc_id=bc.get("id",""); assert bc_id
        log(f"Broadcast: {bc_id} ✅")
    except Exception as e: err(f"Broadcast: {e}"); return None, None

    st_body=json.dumps({"snippet":{"title":"psicologia.doc live"},"cdn":{"ingestionType":"rtmp","resolution":"1080p","frameRate":"30fps"}}).encode()
    req2=urllib.request.Request("https://www.googleapis.com/youtube/v3/liveStreams?part=id,snippet,cdn",data=st_body,method="POST")
    req2.add_header("Authorization",f"Bearer {token}"); req2.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req2,timeout=30) as r:
            st=json.loads(r.read())
        info=st["cdn"]["ingestionInfo"]
        rtmp=f"{info['ingestionAddress']}/{info['streamName']}"
        log(f"Stream: {st.get('id','?')} ✅")
    except Exception as e: err(f"Stream: {e}"); return bc_id, None

    req3=urllib.request.Request(f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id&streamId={st.get('id','')}",data=b"{}",method="POST")
    req3.add_header("Authorization",f"Bearer {token}"); req3.add_header("Content-Type","application/json")
    try: urllib.request.urlopen(req3,timeout=15); log("Vinculado ✅")
    except: pass
    return bc_id, rtmp

def thumbnail_psi(bc_id, token):
    try:
        from PIL import Image, ImageDraw, ImageFont
        W,H=1280,720
        img=Image.new("RGB",(W,H),(0,0,0))  # PRETO PURO
        draw=ImageDraw.Draw(img)
        # Gradiente roxo ultra-sutil
        for y in range(H):
            t=(1-abs(y/H-0.5)*2)*0.18
            draw.line([(0,y),(W,y)],fill=(int(80*t),int(15*t),int(160*t)))
        # Círculo fundo
        cx,cy,r=W//2,H//2-10,195
        for i in range(10,0,-1):
            a=i/10*0.45; c=(int(110*a),int(45*a),int(220*a))
            draw.ellipse([(cx-r-i*14,cy-r-i*14),(cx+r+i*14,cy+r+i*14)],fill=c)
        draw.ellipse([(cx-r,cy-r),(cx+r,cy+r)],fill=(40,6,90))
        # ψ BRANCO puro
        try: fnt=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",240)
        except: fnt=ImageFont.load_default()
        for dx,dy in [(-4,-4),(4,-4),(-4,4),(4,4)]:
            draw.text((cx-78+dx,cy-128+dy),"ψ",font=fnt,fill=(120,55,240))
        draw.text((cx-78,cy-128),"ψ",font=fnt,fill=(255,255,255))
        draw.rectangle([(0,H-10),(W,H)],fill=(245,158,11))
        try: fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",26)
        except: fb=ImageFont.load_default()
        draw.rectangle([(22,18),(210,54)],fill=(220,20,60))
        draw.text((32,25),"● AO VIVO 24H",font=fb,fill=(255,255,255))
        draw.rectangle([(220,18),(460,54)],fill=(15,15,190))
        draw.text((230,25),"TELA PRETA",font=fb,fill=(255,255,255))
        draw.rectangle([(470,18),(705,54)],fill=(30,110,15))
        draw.text((480,25),"BINAURAL 432Hz",font=fb,fill=(255,255,255))
        try: ftag=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",30)
        except: ftag=ImageFont.load_default()
        draw.text((cx-155,H-62),"@psidanicoelho",font=ftag,fill=(190,165,255))
        p=TMP/"thumb_live_final.jpg"; img.save(str(p),"JPEG",quality=95)
        log(f"Thumbnail: {p.stat().st_size//1024}KB")
        sz=p.stat().st_size
        req=urllib.request.Request(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={bc_id}&uploadType=media",data=open(str(p),"rb").read(),method="POST")
        req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","image/jpeg"); req.add_header("Content-Length",str(sz))
        with urllib.request.urlopen(req,timeout=60): log(f"Thumbnail ψ → {bc_id} ✅")
    except Exception as e: err(f"Thumbnail: {e}")

def transmitir(rtmp_url, dur_s, modo="binaural"):
    ff=ffm()
    log(f"Transmitindo {dur_s//3600}h | modo={modo}")
    log(f"RTMP: {rtmp_url[:65]}...")

    # TELA 100% PRETA + binaural corrigido (sem amplitude)
    if modo == "binaural":
        cmd = [
            ff, "-y", "-re",
            # VIDEO: tela 100% PRETA
            "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
            # AUDIO L: 430Hz (sem amplitude — inválido no ffmpeg 7)
            "-f","lavfi","-i","sine=frequency=430:sample_rate=44100",
            # AUDIO R: 432Hz
            "-f","lavfi","-i","sine=frequency=432:sample_rate=44100",
            # Merge binaural + controle de volume (SEM amplitude no sine)
            "-filter_complex","[1:a][2:a]amerge=inputs=2,volume=0.55[stereo]",
            "-map","0:v","-map","[stereo]",
            # Video: ultra-low bitrate (tela preta = quase zero dados)
            "-c:v","libx264","-preset","ultrafast","-crf","36",
            "-b:v","150k","-maxrate","200k","-bufsize","400k",
            "-g","50","-r","25","-pix_fmt","yuv420p",
            # Audio: AAC stereo binaural
            "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
            "-f","flv","-t",str(dur_s),
            rtmp_url
        ]
    elif modo == "sine_mono":
        # Fallback: sine simples mono
        cmd = [
            ff, "-y", "-re",
            "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
            "-f","lavfi","-i","sine=frequency=432:sample_rate=44100",
            "-map","0:v","-map","1:a",
            "-c:v","libx264","-preset","ultrafast","-crf","36",
            "-b:v","150k","-maxrate","200k","-bufsize","400k",
            "-g","50","-r","25","-pix_fmt","yuv420p",
            "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
            "-f","flv","-t",str(dur_s),
            rtmp_url
        ]
    else:
        # Último fallback: silêncio (funciona sempre)
        cmd = [
            ff, "-y", "-re",
            "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
            "-f","lavfi","-i","anullsrc=r=44100:cl=stereo",
            "-map","0:v","-map","1:a",
            "-c:v","libx264","-preset","ultrafast","-crf","36",
            "-b:v","150k","-maxrate","200k","-bufsize","400k",
            "-g","50","-r","25","-pix_fmt","yuv420p",
            "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
            "-f","flv","-t",str(dur_s),
            rtmp_url
        ]

    result = subprocess.run(cmd, timeout=dur_s+900, capture_output=False)
    log(f"rc={result.returncode}")
    return result.returncode in (0,255,-2,-15)

def encerrar(token, bc_id):
    if not bc_id or not token: return
    req=urllib.request.Request(f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bc_id}&part=id",data=b"{}",method="POST")
    req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
    try: urllib.request.urlopen(req,timeout=15); log(f"Live {bc_id} encerrada ✅")
    except Exception as e: err(f"Encerrar: {e}")

def main():
    now_utc=datetime.now(timezone.utc)
    log("="*65)
    log(f"LIVE FINAL V1 | {LANG} | {DURATION_H}h | {now_utc:%H:%M} UTC")
    log("FIX: amplitude removido | volume via filter | fallback automático")
    log("="*65)

    token=get_token()
    bc_id=None; rtmp_url=None

    if token:
        bc_id, rtmp_url = criar_live(token)
        if bc_id: thumbnail_psi(bc_id, token)

    if not rtmp_url:
        if STREAM_KEY: rtmp_url=f"{RTMP_BASE}/{STREAM_KEY}"; log(f"Stream key manual")
        else: err("Sem RTMP!"); sys.exit(1)

    # TESTE AUTOMÁTICO do ffmpeg (determina modo)
    log("Testando ffmpeg...")
    modo = testar_ffmpeg()
    log(f"Modo selecionado: {modo}")

    # Transmitir com retry
    dur_s=DURATION_H*3600; inicio=time.time(); tentativas=0
    while time.time()-inicio < dur_s and tentativas < 25:
        restante=int(dur_s-(time.time()-inicio))
        if restante < 15: break
        tentativas+=1
        log(f"[{tentativas}] Transmitindo {restante//3600}h{(restante%3600)//60}m...")
        ok=transmitir(rtmp_url, restante, modo)
        if ok: break
        espera=min(15*tentativas,90); log(f"Retry em {espera}s..."); time.sleep(espera)

    encerrar(token, bc_id)
    log(f"ENCERRADO | {(time.time()-inicio)//60:.0f}min")

if __name__ == "__main__":
    main()
