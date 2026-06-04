#!/usr/bin/env python3
"""
live_viral_v2.py — DEFINITIVO: tela preta + binaural 432Hz amerge simples
Conecta ao RTMP em <5 segundos. Sem PIL, sem arquivo WAV externo.
SEO viral: "tela preta" + "binaural beats" + "dark psychology" em 8 idiomas
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
        import imageio_ffmpeg; f=imageio_ffmpeg.get_ffmpeg_exe()
        log(f"FFmpeg: {f}"); return f
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

TITULOS = {
    "pt": [
        "🔴 AO VIVO 24H ψ TELA PRETA • Binaural 432Hz • Dark Psychology • Dormir Focar Meditar",
        "🔴 LIVE ψ TELA PRETA 24H • Binaural Beats 432Hz • Psicologia Quântica • @psidanicoelho",
        "🔴 AO VIVO ψ Tela Preta para Dormir • Binaural 432Hz • Narcisismo Dark Psychology",
    ],
    "en": [
        "🔴 LIVE 24H ψ BLACK SCREEN • Binaural Beats 432Hz • Dark Psychology • Sleep Focus",
        "🔴 LIVE ψ BLACK SCREEN 24/7 • 432Hz Binaural • Covert Narcissism • @psidanicoelho",
    ],
    "de": ["🔴 LIVE 24H ψ SCHWARZER BILDSCHIRM • Binaural 432Hz • Psychologie • Schlafen Focus"],
    "es": ["🔴 EN VIVO 24H ψ PANTALLA NEGRA • Binaural 432Hz • Psicología Oscura • Dormir"],
    "fr": ["🔴 EN DIRECT 24H ψ ÉCRAN NOIR • Binaural 432Hz • Psychologie Sombre • Dormir"],
    "it": ["🔴 IN DIRETTA 24H ψ SCHERMO NERO • Binaural 432Hz • Psicologia Oscura"],
    "ja": ["🔴 24H ライブ ψ 黒い画面 • バイノーラル432Hz • 心理学 • 睡眠集中"],
    "ko": ["🔴 24H 라이브 ψ 검은화면 • 바이노럴 432Hz • 심리학 • 수면집중"],
}

DESC_TEMPLATE = """🔴 AO VIVO 24H — ψ TELA PRETA • BINAURAL 432Hz • DARK PSYCHOLOGY

Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖤 TELA 100% PRETA — zero distração visual
🎵 BINAURAL 432Hz — foco profundo + relaxamento
🧠 DARK PSYCHOLOGY — conteúdo científico
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

USO IDEAL:
✅ Dormir com binaural   ✅ Estudar com foco
✅ Meditar              ✅ Trabalhar
✅ Relaxar              ✅ Concentração máxima

FREQUÊNCIAS ATIVAS:
• 430Hz (esq) + 432Hz (dir) = Beat 2Hz DELTA
• Frequência natural 432Hz — harmonia celular

PSICOLOGIA: Narcisismo • Trauma • Ansiedade • Apego
PESQUISA: Harvard • UCLA • van der Kolk

💬 Super Chat: pergunte sobre psicologia!
🔔 ATIVE O SINO!

BLACK SCREEN • TELA PRETA • PANTALLA NEGRA • ÉCRAN NOIR
SCHWARZER BILDSCHIRM • SCHERMO NERO • 黒い画面 • 검은 화면

#telapreta #blackscreen #binaural432hz #432hz #psicologia
#narcisismo #darkpsychology #danielacoelho #psidanicoelho
#binauralbeats #focototal #terapia #meditacao #concentracao
#schwarzerbildschirm #pantallenegra #ecransombre #binaural
#sleepmusic #studymusic #focusmusic #telapretatrablece"""

TAGS = [
    "tela preta","tela preta para dormir","tela preta 8 horas","tela preta binaural",
    "black screen","black screen sleep","black screen 8 hours","black screen binaural beats",
    "schwarzer bildschirm","pantalla negra","écran noir","schermo nero",
    "binaural beats 432hz","432hz","binaural 432hz","binaural beats","binaural beats sleep",
    "binaural beats focus","binaural beats study","frequency 432hz","healing frequency",
    "dark psychology","dark psychology live","dark psychology black screen",
    "psicologia","narcisismo","trauma","ansiedade","apego","comportamento humano",
    "narcissism","covert narcissist","psychology","mental health","daniela coelho",
    "psidanicoelho","sleep music","study music","focus music","meditation music",
    "música para dormir","música para estudar","música de foco","meditação",
]

def criar_live(token):
    titulo = random.choice(TITULOS.get(LANG, TITULOS["pt"]))
    log(f"Título: {titulo[:80]}")
    now = datetime.now(timezone.utc)
    start = (now + timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ")
    bc_body = json.dumps({
        "snippet":{"title":titulo[:100],"scheduledStartTime":start},
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
        log(f"Stream: {st.get('id','?')} | RTMP OK ✅")
    except Exception as e: err(f"Stream: {e}"); return bc_id, None
    req3=urllib.request.Request(f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id&streamId={st.get('id','')}",data=b"{}",method="POST")
    req3.add_header("Authorization",f"Bearer {token}"); req3.add_header("Content-Type","application/json")
    try: urllib.request.urlopen(req3,timeout=15); log("Vinculado ✅")
    except: pass
    # Update desc
    try:
        upd=json.dumps({"id":bc_id,"snippet":{"title":titulo[:100],"scheduledStartTime":start,"description":DESC_TEMPLATE[:4900],"categoryId":"22","defaultLanguage":LANG}}).encode()
        req4=urllib.request.Request("https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet",data=upd,method="PUT")
        req4.add_header("Authorization",f"Bearer {token}"); req4.add_header("Content-Type","application/json")
        urllib.request.urlopen(req4,timeout=15); log("SEO desc aplicado ✅")
    except: pass
    return bc_id, rtmp

def thumbnail_psi(bc_id, token):
    try:
        from PIL import Image, ImageDraw, ImageFont
        W,H=1280,720
        img=Image.new("RGB",(W,H),(0,0,0))
        draw=ImageDraw.Draw(img)
        for y in range(H):
            t=(1-abs(y/H-0.5)*2)*0.22
            draw.line([(0,y),(W,y)],fill=(int(90*t),int(15*t),int(180*t)))
        cx,cy,r=W//2,H//2-15,195
        for i in range(10,0,-1):
            a=i/10*0.5; c=(int(120*a),int(50*a),int(230*a))
            draw.ellipse([(cx-r-i*15,cy-r-i*15),(cx+r+i*15,cy+r+i*15)],fill=c)
        draw.ellipse([(cx-r,cy-r),(cx+r,cy+r)],fill=(48,8,105))
        try: fnt=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",240)
        except: fnt=ImageFont.load_default()
        for dx,dy in [(-4,-4),(4,-4),(-4,4),(4,4)]: draw.text((cx-78+dx,cy-128+dy),"ψ",font=fnt,fill=(130,65,250))
        draw.text((cx-78,cy-128),"ψ",font=fnt,fill=(255,255,255))
        draw.rectangle([(0,H-12),(W,H)],fill=(245,158,11))
        try: fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",28)
        except: fb=ImageFont.load_default()
        draw.rectangle([(25,20),(215,58)],fill=(220,20,60)); draw.text((35,27),"● AO VIVO 24H",font=fb,fill=(255,255,255))
        draw.rectangle([(225,20),(460,58)],fill=(20,20,200)); draw.text((235,27),"TELA PRETA",font=fb,fill=(255,255,255))
        draw.rectangle([(470,20),(680,58)],fill=(40,120,20)); draw.text((480,27),"BINAURAL 432Hz",font=fb,fill=(255,255,255))
        try: ftag=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",32)
        except: ftag=ImageFont.load_default()
        draw.text((cx-165,H-65),"@psidanicoelho",font=ftag,fill=(200,175,255))
        p=TMP/"thumb_live.jpg"; img.save(str(p),"JPEG",quality=95)
        sz=p.stat().st_size
        req=urllib.request.Request(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={bc_id}&uploadType=media",data=open(str(p),"rb").read(),method="POST")
        req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","image/jpeg"); req.add_header("Content-Length",str(sz))
        with urllib.request.urlopen(req,timeout=60): log(f"Thumbnail ψ uploaded ✅")
    except Exception as e: err(f"Thumbnail: {e}")

def transmitir(rtmp_url, dur_s):
    """Tela preta + binaural amerge (comando mais simples possível)"""
    ff=ffm()
    log(f"TRANSMITINDO {dur_s//3600}h tela preta + binaural 430/432Hz...")
    log(f"RTMP: {rtmp_url[:65]}...")
    cmd = [
        ff, "-y", "-re",
        # Video: tela preta
        "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
        # Audio L: 430Hz
        "-f","lavfi","-i","sine=frequency=430:amplitude=0.28:sample_rate=44100",
        # Audio R: 432Hz  
        "-f","lavfi","-i","sine=frequency=432:amplitude=0.28:sample_rate=44100",
        # Merge: L=430Hz, R=432Hz (binaural real)
        "-filter_complex","[1:a][2:a]amerge=inputs=2[stereo]",
        "-map","0:v","-map","[stereo]",
        # Video: mínimo (tela preta = quase zero bits)
        "-c:v","libx264","-preset","ultrafast","-crf","36",
        "-b:v","150k","-maxrate","200k","-bufsize","400k",
        "-g","50","-r","25","-pix_fmt","yuv420p",
        # Audio: AAC stereo binaural
        "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
        "-f","flv","-t",str(dur_s),
        rtmp_url
    ]
    result=subprocess.run(cmd, timeout=dur_s+900)
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
    log(f"LIVE VIRAL V2 DEFINITIVO | {LANG} | {DURATION_H}h | {now_utc:%H:%M} UTC")
    log("TELA PRETA PURA + BINAURAL 432Hz + SEO VIRAL GLOBAL")
    log("="*65)
    token=get_token()
    bc_id=None; rtmp_url=None
    if token:
        bc_id, rtmp_url = criar_live(token)
    if not rtmp_url:
        if STREAM_KEY: rtmp_url=f"{RTMP_BASE}/{STREAM_KEY}"; log(f"Stream key manual")
        else: err("Sem RTMP!"); sys.exit(1)
    # Thumbnail em background (não bloqueia ffmpeg)
    if bc_id and token:
        try: thumbnail_psi(bc_id, token)
        except: pass
    # Transmitir com retry
    dur_s=DURATION_H*3600; inicio=time.time(); tentativas=0
    while time.time()-inicio < dur_s and tentativas < 25:
        restante=int(dur_s-(time.time()-inicio))
        if restante < 15: break
        tentativas+=1
        log(f"[{tentativas}] {restante//3600}h{(restante%3600)//60}m restantes")
        ok=transmitir(rtmp_url, restante)
        if ok: break
        espera=min(15*tentativas,90); log(f"Retry em {espera}s..."); time.sleep(espera)
    encerrar(token, bc_id)
    log(f"ENCERRADO | {(time.time()-inicio)//60:.0f}min total")

if __name__ == "__main__":
    main()
