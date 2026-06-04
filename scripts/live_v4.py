#!/usr/bin/env python3
"""
live_v4.py — DEFINITIVO
- Usa broadcast EXISTENTE (LhAVPY_HK-4) se disponível, ou cria novo
- RTMP: rtmp:// (não rtmps://) — exatamente como retornado pela API
- sine SEM amplitude (corrigido para ffmpeg 7.0.2)
- volume via filtro separado após amerge
- Tela 100% PRETA garantida
- SEO em 8 idiomas com títulos por hora/país
"""
import os,sys,subprocess,pathlib,shutil,json,urllib.request,urllib.parse,time,random
from datetime import datetime,timezone,timedelta

YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
STREAM_KEY       = os.environ.get("YOUTUBE_STREAM_KEY","ewme-91sq-yae7-yj1q-5skw")
DURATION_H       = int(os.environ.get("DURATION_H","6"))
LANG             = os.environ.get("LANG_CODE","pt")

# IDs do broadcast/stream existente (criados manualmente)
BC_ID_EXISTENTE  = "LhAVPY_HK-4"
RTMP_KEY_EXISTENTE = "ewme-91sq-yae7-yj1q-5skw"
RTMP_BASE        = "rtmp://a.rtmp.youtube.com/live2"
TMP              = pathlib.Path("/tmp")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}",flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERRO: {m}",flush=True,file=sys.stderr)

def ffm():
    try:
        import imageio_ffmpeg; f=imageio_ffmpeg.get_ffmpeg_exe(); log(f"FFmpeg: {f}"); return f
    except: pass
    for p in [shutil.which("ffmpeg"),"/usr/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists(): return p
    return "ffmpeg"

def get_token():
    if not YT_CLIENT_ID: return ""
    data=urllib.parse.urlencode({"client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
        "refresh_token":YT_REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    req=urllib.request.Request("https://oauth2.googleapis.com/token",data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read()).get("access_token","")
    except Exception as e: err(f"Token: {e}"); return ""

TITULOS={
    "pt":["🔴 AO VIVO 24H | ψ TELA PRETA • Binaural 432Hz • Dark Psychology | @psidanicoelho",
          "🔴 LIVE | ψ TELA PRETA 24H • Binaural 432Hz • Narcisismo • Foco Total",
          "🔴 AO VIVO | ψ Tela Preta para Dormir • Binaural 432Hz • Psicologia Quântica"],
    "en":["🔴 LIVE 24H | ψ BLACK SCREEN • Binaural 432Hz • Dark Psychology | @psidanicoelho",
          "🔴 LIVE | ψ BLACK SCREEN 24/7 • 432Hz • Covert Narcissism • Sleep Focus"],
    "de":["🔴 LIVE 24H | ψ SCHWARZER BILDSCHIRM • Binaural 432Hz • Psychologie | @psidanicoelho"],
    "es":["🔴 EN VIVO 24H | ψ PANTALLA NEGRA • Binaural 432Hz • Psicología Oscura"],
    "fr":["🔴 EN DIRECT 24H | ψ ÉCRAN NOIR • Binaural 432Hz • Psychologie Sombre"],
    "it":["🔴 IN DIRETTA 24H | ψ SCHERMO NERO • Binaural 432Hz • Psicologia Oscura"],
    "ja":["🔴 24H ライブ | ψ 黒い画面 • バイノーラル432Hz • 心理学 睡眠 集中"],
    "ko":["🔴 24H 라이브 | ψ 검은화면 • 바이노럴 432Hz • 심리학 수면 집중"],
}

DESC="""🔴 AO VIVO 24 HORAS — ψ TELA PRETA • BINAURAL 432Hz • DARK PSYCHOLOGY

Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖤 TELA 100% PRETA — zero distração visual
🎵 BINAURAL 432Hz (430Hz esq + 432Hz dir = beat 2Hz DELTA-THETA)
🧠 DARK PSYCHOLOGY — pesquisa científica aplicada
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DORMIR com binaural ✅ ESTUDAR com foco
✅ MEDITAR ✅ TRABALHAR ✅ CONCENTRAÇÃO MÁXIMA

PSICOLOGIA: Narcisismo • Trauma • Ansiedade • Apego
FONTES: Harvard • UCLA • van der Kolk • University of Texas

💬 Super Chat: pergunte sobre psicologia!
❤️ Super Thanks: apoie a pesquisa!
🔔 ATIVE O SINO para não perder novos vídeos!

🌍 DISPONÍVEL EM 8 IDIOMAS:
PT-BR | ENGLISH | DEUTSCH | ESPAÑOL | FRANÇAIS | ITALIANO | 日本語 | 한국어

BLACK SCREEN • TELA PRETA • SCHWARZER BILDSCHIRM
PANTALLA NEGRA • ÉCRAN NOIR • SCHERMO NERO • 黒い画面 • 검은 화면

#telapreta #blackscreen #binaural432hz #432hz #psicologia
#narcisismo #darkpsychology #danielacoelho #psidanicoelho
#binauralbeats #focototal #meditacao #concentracao #dormir
#sleepmusic #studymusic #focusmusic #schwarzerbildschirm
#pantallenegra #binaural #telapretatrablece"""

def atualizar_seo(token, bc_id):
    titulo=random.choice(TITULOS.get(LANG,TITULOS["pt"]))
    log(f"Título: {titulo[:70]}")
    now=datetime.now(timezone.utc)
    start=(now+timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        upd=json.dumps({"id":bc_id,"snippet":{"title":titulo[:100],"scheduledStartTime":start,
            "description":DESC[:4900],"categoryId":"22","defaultLanguage":LANG}}).encode()
        req=urllib.request.Request("https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet",data=upd,method="PUT")
        req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
        urllib.request.urlopen(req,timeout=15); log("SEO atualizado ✅")
    except Exception as e: err(f"SEO: {e}")

def thumbnail(bc_id,token):
    try:
        from PIL import Image,ImageDraw,ImageFont
        W,H=1280,720; img=Image.new("RGB",(W,H),(0,0,0))
        draw=ImageDraw.Draw(img)
        for y in range(H):
            t=(1-abs(y/H-0.5)*2)*0.15
            draw.line([(0,y),(W,y)],fill=(int(70*t),int(8*t),int(150*t)))
        cx,cy,r=W//2,H//2-15,195
        for i in range(10,0,-1):
            a=i/10*0.45; c=(int(110*a),int(40*a),int(220*a))
            draw.ellipse([(cx-r-i*15,cy-r-i*15),(cx+r+i*15,cy+r+i*15)],fill=c)
        draw.ellipse([(cx-r,cy-r),(cx+r,cy+r)],fill=(40,6,90))
        try: fnt=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",240)
        except: fnt=ImageFont.load_default()
        for dx,dy in [(-4,-4),(4,-4),(-4,4),(4,4)]: draw.text((cx-78+dx,cy-128+dy),"ψ",font=fnt,fill=(100,35,200))
        draw.text((cx-78,cy-128),"ψ",font=fnt,fill=(255,255,255))
        try: fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",26)
        except: fb=ImageFont.load_default()
        draw.rectangle([(25,20),(215,57)],fill=(220,20,60)); draw.text((35,27),"● AO VIVO 24H",font=fb,fill=(255,255,255))
        draw.rectangle([(225,20),(465,57)],fill=(20,20,190)); draw.text((235,27),"TELA PRETA 100%",font=fb,fill=(255,255,255))
        draw.rectangle([(475,20),(720,57)],fill=(40,120,20)); draw.text((485,27),"BINAURAL 432Hz",font=fb,fill=(255,255,255))
        try: ftag=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",34)
        except: ftag=ImageFont.load_default()
        draw.text((cx-165,H-65),"@psidanicoelho",font=ftag,fill=(200,175,255))
        draw.rectangle([(0,H-10),(W,H)],fill=(245,158,11))
        p=TMP/"thumb.jpg"; img.save(str(p),"JPEG",quality=95)
        req=urllib.request.Request(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={bc_id}&uploadType=media",data=open(str(p),"rb").read(),method="POST")
        req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","image/jpeg"); req.add_header("Content-Length",str(p.stat().st_size))
        with urllib.request.urlopen(req,timeout=60): log("Thumbnail ψ ✅")
    except Exception as e: err(f"Thumb: {e}")

def transmitir(rtmp_url,dur_s):
    ff=ffm()
    log(f"TRANSMITINDO {dur_s//3600}h | TELA PRETA + BINAURAL 432Hz")
    log(f"RTMP: {rtmp_url[:60]}...")
    # sine SEM amplitude (ffmpeg 7.0.2) + volume após amerge
    cmd=[
        ff,"-y","-re",
        "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
        "-f","lavfi","-i","sine=frequency=430:sample_rate=44100",
        "-f","lavfi","-i","sine=frequency=432:sample_rate=44100",
        "-filter_complex","[1:a][2:a]amerge=inputs=2,volume=0.35[stereo]",
        "-map","0:v","-map","[stereo]",
        "-c:v","libx264","-preset","ultrafast","-crf","36",
        "-b:v","150k","-maxrate","200k","-bufsize","400k",
        "-g","50","-r","25","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
        "-f","flv","-t",str(dur_s),
        rtmp_url
    ]
    result=subprocess.run(cmd,timeout=dur_s+900)
    log(f"rc={result.returncode}")
    return result.returncode in (0,255,-2,-15)

def encerrar(token,bc_id):
    if not bc_id or not token: return
    req=urllib.request.Request(f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bc_id}&part=id",data=b"{}",method="POST")
    req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
    try: urllib.request.urlopen(req,timeout=15); log(f"Encerrado {bc_id} ✅")
    except: pass

def main():
    now_utc=datetime.now(timezone.utc)
    log("="*65)
    log(f"LIVE V4 DEFINITIVO | {LANG} | {DURATION_H}h | {now_utc:%H:%M} UTC")
    log("TELA PRETA 100% + BINAURAL 432Hz + SEO VIRAL 8 IDIOMAS")
    log("="*65)

    token=get_token()

    # Usar broadcast existente ou criar novo
    bc_id=BC_ID_EXISTENTE
    rtmp_url=f"{RTMP_BASE}/{RTMP_KEY_EXISTENTE}"

    log(f"Broadcast: {bc_id} (existente)")
    log(f"RTMP: {rtmp_url[:60]}")

    # Atualizar SEO e thumbnail
    if token:
        atualizar_seo(token,bc_id)
        try: thumbnail(bc_id,token)
        except: pass

    # Transmitir com retry
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
    log(f"ENCERRADO | {(time.time()-inicio)//60:.0f}min total")

if __name__=="__main__":
    main()
