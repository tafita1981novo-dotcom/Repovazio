#!/usr/bin/env python3
"""
live_v3.py — DEFINITIVO: tela preta + binaural 432Hz
FIX: sine sem 'amplitude' (não suportado no ffmpeg 7.0.2)
     volume=0.35 aplicado via filtro separado após amerge
TELA: 100% preta (0,0,0) — zero pixel iluminado
SEO: títulos virais por hora+país em 8 idiomas
"""
import os, sys, subprocess, pathlib, shutil, json, urllib.request, urllib.parse, time, random
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

# ─── SEO VIRAL POR HORA E PAÍS ─────────────────────────────────────
def titulo_por_hora(hour_utc):
    """Título rotativo que maximiza CTR no país em horário nobre"""
    # Países em horário nobre agora (09h-22h local)
    offsets={"US":-5,"DE":1,"GB":0,"AU":10,"JP":9,"BR":-3,"ES":1,"FR":1,"MX":-6,"KR":9}
    top=""
    for code,off in offsets.items():
        if 9<=(hour_utc+off)%24<=22: top=code; break

    titulos={
        "pt":[
            f"🔴 AO VIVO 24H | ψ TELA PRETA • Binaural 432Hz • Dark Psychology | @psidanicoelho",
            f"🔴 LIVE | TELA PRETA 24H ψ • Binaural 432Hz • Narcisismo • Foco Total",
            f"🔴 AO VIVO | ψ Tela Preta para Dormir • Binaural 432Hz • Psicologia Quântica",
        ],
        "en":[
            f"🔴 LIVE 24H | ψ BLACK SCREEN • Binaural 432Hz • Dark Psychology | @psidanicoelho",
            f"🔴 LIVE | BLACK SCREEN 24/7 ψ • Binaural Beats 432Hz • Focus & Sleep",
            f"🔴 24H LIVE | ψ Black Screen • Binaural 432Hz • Covert Narcissism Research",
        ],
        "de":[
            f"🔴 LIVE 24H | ψ SCHWARZER BILDSCHIRM • Binaural 432Hz • Psychologie",
        ],
        "es":[
            f"🔴 EN VIVO 24H | ψ PANTALLA NEGRA • Binaural 432Hz • Psicología Oscura",
        ],
        "fr":[
            f"🔴 EN DIRECT 24H | ψ ÉCRAN NOIR • Binaural 432Hz • Psychologie Sombre",
        ],
        "it":[
            f"🔴 IN DIRETTA 24H | ψ SCHERMO NERO • Binaural 432Hz • Psicologia Oscura",
        ],
        "ja":[
            f"🔴 24H ライブ | ψ 黒い画面 • バイノーラル432Hz • 心理学 睡眠 集中",
        ],
        "ko":[
            f"🔴 24H 라이브 | ψ 검은화면 • 바이노럴 432Hz • 심리학 수면 집중",
        ],
    }
    opts=titulos.get(LANG,titulos["pt"])
    return random.choice(opts)

DESC_VIRAL="""🔴 AO VIVO 24 HORAS — ψ TELA PRETA • BINAURAL 432Hz • DARK PSYCHOLOGY

Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖤 TELA 100% PRETA — zero distração visual
🎵 BINAURAL 432Hz (430Hz esq + 432Hz dir = beat 2Hz DELTA)
🧠 DARK PSYCHOLOGY — pesquisa científica aplicada
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Ideal para DORMIR  ✅ ESTUDAR  ✅ MEDITAR  ✅ TRABALHAR

PSICOLOGIA: Narcisismo • Trauma • Ansiedade • Apego
FONTES: Harvard • UCLA • van der Kolk • University of Texas

💬 Super Chat: sua pergunta sobre psicologia!
❤️ Super Thanks: apoie a pesquisa!
🔔 ATIVE O SINO!

🌍 DISPONÍVEL EM 8 IDIOMAS:
PT-BR | ENGLISH | DEUTSCH | ESPAÑOL | FRANÇAIS | ITALIANO | 日本語 | 한국어

BLACK SCREEN • TELA PRETA • SCHWARZER BILDSCHIRM
PANTALLA NEGRA • ÉCRAN NOIR • SCHERMO NERO • 黒い画面 • 검은 화면

#telapreta #blackscreen #binaural432hz #432hz #psicologia
#narcisismo #darkpsychology #danielacoelho #psidanicoelho
#binauralbeats #focototal #meditacao #concentracao #dormir
#schwarzerbildschirm #pantallenegra #binaural #sleepmusic"""

TAGS=[
    "tela preta","tela preta para dormir","tela preta binaural","tela preta 8 horas",
    "black screen","black screen sleep","black screen binaural beats","black screen 8 hours",
    "schwarzer bildschirm","pantalla negra","écran noir","schermo nero","黒い画面","검은 화면",
    "binaural beats 432hz","432hz","binaural 432hz","binaural beats","binaural beats sleep",
    "binaural beats focus","binaural beats study","432hz sleep","432hz focus",
    "dark psychology","dark psychology live","dark psychology black screen",
    "psicologia","narcisismo","trauma","ansiedade","comportamento humano",
    "narcissism","covert narcissist","psychology","daniela coelho","psidanicoelho",
    "sleep music","study music","focus music","música para dormir","música para estudar",
    "meditação","meditation","concentração","foco","binaural meditação",
]

def criar_live(token, hour_utc):
    titulo=titulo_por_hora(hour_utc)
    log(f"Título: {titulo[:80]}")
    start=(datetime.now(timezone.utc)+timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ")
    bc_body=json.dumps({
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
    except Exception as e: err(f"Broadcast: {e}"); return None,None
    st_body=json.dumps({"snippet":{"title":"psicologia.doc live"},"cdn":{"ingestionType":"rtmp","resolution":"1080p","frameRate":"30fps"}}).encode()
    req2=urllib.request.Request("https://www.googleapis.com/youtube/v3/liveStreams?part=id,snippet,cdn",data=st_body,method="POST")
    req2.add_header("Authorization",f"Bearer {token}"); req2.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req2,timeout=30) as r:
            st=json.loads(r.read()); info=st["cdn"]["ingestionInfo"]
            rtmp=f"{info['ingestionAddress']}/{info['streamName']}"; log(f"Stream: {st.get('id','?')} ✅")
    except Exception as e: err(f"Stream: {e}"); return bc_id,None
    req3=urllib.request.Request(f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id&streamId={st.get('id','')}",data=b"{}",method="POST")
    req3.add_header("Authorization",f"Bearer {token}"); req3.add_header("Content-Type","application/json")
    try: urllib.request.urlopen(req3,timeout=15); log("Vinculado ✅")
    except: pass
    try:
        upd=json.dumps({"id":bc_id,"snippet":{"title":titulo[:100],"scheduledStartTime":start,"description":DESC_VIRAL[:4900],"categoryId":"22","defaultLanguage":LANG}}).encode()
        req4=urllib.request.Request("https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet",data=upd,method="PUT")
        req4.add_header("Authorization",f"Bearer {token}"); req4.add_header("Content-Type","application/json")
        urllib.request.urlopen(req4,timeout=15); log("SEO aplicado ✅")
    except: pass
    return bc_id,rtmp

def thumbnail(bc_id,token):
    try:
        from PIL import Image,ImageDraw,ImageFont
        W,H=1280,720
        img=Image.new("RGB",(W,H),(0,0,0))
        draw=ImageDraw.Draw(img)
        # Gradiente roxo sutil
        for y in range(H):
            t=(1-abs(y/H-0.5)*2)*0.18
            draw.line([(0,y),(W,y)],fill=(int(80*t),int(10*t),int(170*t)))
        # Círculo roxo
        cx,cy,r=W//2,H//2-15,195
        for i in range(10,0,-1):
            a=i/10*0.5; c=(int(120*a),int(45*a),int(225*a))
            draw.ellipse([(cx-r-i*15,cy-r-i*15),(cx+r+i*15,cy+r+i*15)],fill=c)
        draw.ellipse([(cx-r,cy-r),(cx+r,cy+r)],fill=(45,8,100))
        # ψ
        try: fnt=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",240)
        except: fnt=ImageFont.load_default()
        for dx,dy in [(-4,-4),(4,-4),(-4,4),(4,4)]: draw.text((cx-78+dx,cy-128+dy),"ψ",font=fnt,fill=(120,55,240))
        draw.text((cx-78,cy-128),"ψ",font=fnt,fill=(255,255,255))
        # Badges
        try: fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",26)
        except: fb=ImageFont.load_default()
        draw.rectangle([(25,20),(215,57)],fill=(220,20,60)); draw.text((35,27),"● AO VIVO 24H",font=fb,fill=(255,255,255))
        draw.rectangle([(225,20),(465,57)],fill=(20,20,190)); draw.text((235,27),"TELA PRETA 100%",font=fb,fill=(255,255,255))
        draw.rectangle([(475,20),(720,57)],fill=(40,130,20)); draw.text((485,27),"BINAURAL 432Hz",font=fb,fill=(255,255,255))
        try: ftag=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",34)
        except: ftag=ImageFont.load_default()
        draw.text((cx-165,H-65),"@psidanicoelho",font=ftag,fill=(200,175,255))
        draw.rectangle([(0,H-10),(W,H)],fill=(245,158,11))
        p=TMP/"thumb.jpg"; img.save(str(p),"JPEG",quality=95)
        sz=p.stat().st_size
        req=urllib.request.Request(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={bc_id}&uploadType=media",data=open(str(p),"rb").read(),method="POST")
        req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","image/jpeg"); req.add_header("Content-Length",str(sz))
        with urllib.request.urlopen(req,timeout=60): log(f"Thumbnail ψ ✅")
    except Exception as e: err(f"Thumb: {e}")

def transmitir(rtmp_url, dur_s):
    """
    Tela 100% PRETA + binaural 432Hz
    FIX: sine SEM 'amplitude' (não existe no ffmpeg 7.0.2)
    volume aplicado via filtro separado
    """
    ff=ffm()
    log(f"Transmitindo {dur_s//3600}h {dur_s%3600//60}m → RTMP...")
    cmd=[
        ff,"-y","-re",
        # VIDEO: tela 100% preta (color=black)
        "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
        # AUDIO L: 430Hz (sem amplitude)
        "-f","lavfi","-i","sine=frequency=430:sample_rate=44100",
        # AUDIO R: 432Hz (sem amplitude)
        "-f","lavfi","-i","sine=frequency=432:sample_rate=44100",
        # Merge: L=430Hz R=432Hz + volume controlado
        "-filter_complex","[1:a][2:a]amerge=inputs=2,volume=0.35[stereo]",
        "-map","0:v","-map","[stereo]",
        # Video: ultrafast, bitrate mínimo (tela preta = quase 0 dados)
        "-c:v","libx264","-preset","ultrafast","-crf","36",
        "-b:v","150k","-maxrate","200k","-bufsize","400k",
        "-g","50","-r","25","-pix_ft","yuv420p",
        # Audio: AAC stereo binaural
        "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
        "-f","flv","-t",str(dur_s),
        rtmp_url
    ]
    # Fix typo: -pix_ft → -pix_fmt
    cmd=[c if c!="-pix_ft" else "-pix_fmt" for c in cmd]
    result=subprocess.run(cmd,timeout=dur_s+900)
    log(f"rc={result.returncode}")
    return result.returncode in (0,255,-2,-15)

def encerrar(token,bc_id):
    if not bc_id or not token: return
    req=urllib.request.Request(f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bc_id}&part=id",data=b"{}",method="POST")
    req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
    try: urllib.request.urlopen(req,timeout=15); log(f"Live {bc_id} encerrada ✅")
    except Exception as e: err(f"Encerrar: {e}")

def main():
    now_utc=datetime.now(timezone.utc); hour=now_utc.hour
    log("="*65)
    log(f"LIVE V3 DEFINITIVO | {LANG} | {DURATION_H}h | {now_utc:%H:%M} UTC")
    log("TELA PRETA 100% + BINAURAL 432Hz (sem amplitude) + SEO VIRAL")
    log("="*65)
    token=get_token()
    bc_id=None; rtmp_url=None
    if token:
        bc_id,rtmp_url=criar_live(token,hour)
    if not rtmp_url:
        if STREAM_KEY: rtmp_url=f"{RTMP_BASE}/{STREAM_KEY}"; log(f"Fallback stream key")
        else: err("Sem RTMP!"); sys.exit(1)
    if bc_id and token:
        try: thumbnail(bc_id,token)
        except: pass
    dur_s=DURATION_H*3600; inicio=time.time(); tentativas=0
    while time.time()-inicio<dur_s and tentativas<30:
        restante=int(dur_s-(time.time()-inicio))
        if restante<15: break
        tentativas+=1
        log(f"[{tentativas}] {restante//3600}h{restante%3600//60}m restantes")
        ok=transmitir(rtmp_url,restante)
        if ok: break
        espera=min(20*tentativas,120); log(f"Retry em {espera}s..."); time.sleep(espera)
    encerrar(token,bc_id)
    log(f"ENCERRADO após {(time.time()-inicio)//60:.0f}min")

if __name__=="__main__":
    main()
