#!/usr/bin/env python3
"""
live_v5.py — DIAGNÓSTICO + LIVE DEFINITIVO
Testa rtmp:// e rtmps:// e usa o que funcionar
Tela 100% PRETA garantida
Binaural 432Hz via lavfi sem amplitude (ffmpeg 7.0.2)
"""
import os,sys,subprocess,pathlib,shutil,json,urllib.request,urllib.parse,time,random,socket
from datetime import datetime,timezone,timedelta

YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
DURATION_H       = int(os.environ.get("DURATION_H","6"))
LANG             = os.environ.get("LANG_CODE","pt")

# Broadcast e stream existentes — usar diretamente sem criar novos
BC_ID   = "LhAVPY_HK-4"
ST_KEY  = "ewme-91sq-yae7-yj1q-5skw"
# YouTube RTMP endpoints
RTMP_URLS = [
    f"rtmp://a.rtmp.youtube.com/live2/{ST_KEY}",
    f"rtmps://a.rtmps.youtube.com/live2/{ST_KEY}",
    f"rtmp://b.rtmp.youtube.com/live2/{ST_KEY}",
]
TMP = pathlib.Path("/tmp")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}",flush=True)

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
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read()).get("access_token","")
    except Exception as e: log(f"Token erro: {e}"); return ""

def testar_rtmp_porta(host, port):
    """Testa se a porta está acessível"""
    try:
        s=socket.create_connection((host,port),timeout=10)
        s.close(); return True
    except: return False

TITULOS=[
    "🔴 AO VIVO 24H | ψ TELA PRETA • Binaural 432Hz • Dark Psychology | @psidanicoelho",
    "🔴 LIVE | ψ TELA PRETA 24H • Binaural 432Hz • Narcisismo • Foco Total",
    "🔴 AO VIVO | ψ Tela Preta para Dormir • Binaural 432Hz • Psicologia Quântica",
]

DESC="""🔴 AO VIVO 24 HORAS — ψ TELA PRETA • BINAURAL 432Hz • DARK PSYCHOLOGY

Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖤 TELA 100% PRETA — zero distração visual
🎵 BINAURAL 432Hz (430Hz esq + 432Hz dir = beat DELTA 2Hz)
🧠 DARK PSYCHOLOGY — conteúdo científico
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DORMIR  ✅ ESTUDAR  ✅ MEDITAR  ✅ TRABALHAR  ✅ FOCO

FONTES: Harvard • UCLA • van der Kolk • Gottman • Ainsworth
💬 Super Chat: perguntas de psicologia!  🔔 ATIVE O SINO!

BLACK SCREEN • TELA PRETA • SCHWARZER BILDSCHIRM • PANTALLA NEGRA
ÉCRAN NOIR • SCHERMO NERO • 黒い画面 • 검은 화면

#telapreta #blackscreen #binaural432hz #432hz #psicologia
#narcisismo #darkpsychology #danielacoelho #psidanicoelho
#binauralbeats #focototal #sleepmusic #studymusic #concentracao"""

def atualizar_live(token):
    if not token: return
    titulo=random.choice(TITULOS)
    log(f"Título: {titulo[:70]}")
    now=datetime.now(timezone.utc)
    start=(now+timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        body=json.dumps({"id":BC_ID,"snippet":{"title":titulo[:100],"scheduledStartTime":start,
            "description":DESC[:4900],"categoryId":"22","defaultLanguage":"pt"}}).encode()
        req=urllib.request.Request("https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet",
            data=body,method="PUT")
        req.add_header("Authorization",f"Bearer {token}")
        req.add_header("Content-Type","application/json")
        with urllib.request.urlopen(req,timeout=15): log("SEO ✅")
    except Exception as e: log(f"SEO erro: {e}")

def thumbnail_psi(token):
    if not token: return
    try:
        from PIL import Image,ImageDraw,ImageFont
        W,H=1280,720; img=Image.new("RGB",(W,H),(0,0,0))
        draw=ImageDraw.Draw(img)
        for y in range(H):
            t=(1-abs(y/H-0.5)*2)*0.15
            draw.line([(0,y),(W,y)],fill=(int(70*t),int(8*t),int(155*t)))
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
        draw.rectangle([(25,20),(220,57)],fill=(220,20,60)); draw.text((35,27),"● AO VIVO 24H",font=fb,fill=(255,255,255))
        draw.rectangle([(230,20),(475,57)],fill=(20,20,190)); draw.text((240,27),"TELA PRETA 100%",font=fb,fill=(255,255,255))
        draw.rectangle([(485,20),(730,57)],fill=(40,120,20)); draw.text((495,27),"BINAURAL 432Hz",font=fb,fill=(255,255,255))
        try: ftag=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",34)
        except: ftag=ImageFont.load_default()
        draw.text((cx-165,H-65),"@psidanicoelho",font=ftag,fill=(200,175,255))
        draw.rectangle([(0,H-10),(W,H)],fill=(245,158,11))
        p=TMP/"thumb.jpg"; img.save(str(p),"JPEG",quality=95)
        req=urllib.request.Request(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={BC_ID}&uploadType=media",
            data=open(str(p),"rb").read(),method="POST")
        req.add_header("Authorization",f"Bearer {token}")
        req.add_header("Content-Type","image/jpeg")
        req.add_header("Content-Length",str(p.stat().st_size))
        with urllib.request.urlopen(req,timeout=60): log("Thumbnail ψ ✅")
    except Exception as e: log(f"Thumb: {e}")

def transmitir(rtmp_url, dur_s, ff):
    log(f"ffmpeg → {rtmp_url[:55]}...")
    cmd=[
        ff,"-y","-re",
        # TELA PRETA 100%
        "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
        # BINAURAL: sine sem amplitude + volume após amerge
        "-f","lavfi","-i","sine=frequency=430:sample_rate=44100",
        "-f","lavfi","-i","sine=frequency=432:sample_rate=44100",
        "-filter_complex","[1:a][2:a]amerge=inputs=2,volume=0.35[stereo]",
        "-map","0:v","-map","[stereo]",
        # Video mínimo (tela preta)
        "-c:v","libx264","-preset","ultrafast","-crf","36",
        "-b:v","150k","-maxrate","200k","-bufsize","400k",
        "-g","50","-r","25","-pix_fmt","yuv420p",
        # Audio binaural
        "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
        # Output
        "-f","flv","-t",str(dur_s), rtmp_url
    ]
    result=subprocess.run(cmd,timeout=dur_s+900)
    log(f"rc={result.returncode}")
    return result.returncode

def main():
    log("="*65)
    log(f"LIVE V5 DIAGNÓSTICO+DEFINITIVO | {LANG} | {DURATION_H}h")
    log(f"Broadcast: {BC_ID} | Stream key: {ST_KEY[:12]}...")
    log("="*65)

    ff=ffm()

    # Diagnóstico: testar portas
    log("=== DIAGNÓSTICO DE REDE ===")
    for host,port in [("a.rtmp.youtube.com",1935),("a.rtmps.youtube.com",443),("youtube.com",443)]:
        ok=testar_rtmp_porta(host,port)
        log(f"  {host}:{port} → {'✅ OK' if ok else '❌ BLOQUEADA'}")

    # Token e SEO
    token=get_token()
    if token: log(f"Token: ...{token[-8:]}")
    else: log("Token: sem credenciais (usando stream key direta)")
    atualizar_live(token)
    thumbnail_psi(token)

    # Selecionar URL RTMP funcional
    rtmp_url=None
    log("=== TESTANDO RTMP URLs ===")
    for url in RTMP_URLS:
        host=url.split("//")[1].split("/")[0]
        port=443 if "rtmps://" in url else 1935
        ok=testar_rtmp_porta(host,port)
        log(f"  {url[:45]} → porta {'✅' if ok else '❌'}")
        if ok and rtmp_url is None: rtmp_url=url

    if not rtmp_url:
        log("AVISO: nenhuma porta acessível via socket — tentando RTMP mesmo assim")
        rtmp_url=RTMP_URLS[0]

    log(f"RTMP selecionado: {rtmp_url[:55]}")

    # Transmitir com retry automático
    dur_s=DURATION_H*3600; inicio=time.time(); tentativas=0
    while time.time()-inicio<dur_s and tentativas<30:
        restante=int(dur_s-(time.time()-inicio))
        if restante<15: break
        tentativas+=1
        log(f"[{tentativas}] {restante//3600}h{restante%3600//60}m restantes → transmitindo...")
        rc=transmitir(rtmp_url,restante,ff)
        if rc in (0,): break
        espera=min(20*tentativas,120); log(f"rc={rc} — retry em {espera}s..."); time.sleep(espera)

    log(f"ENCERRADO | {(time.time()-inicio)//60:.0f}min total")

if __name__=="__main__":
    main()
