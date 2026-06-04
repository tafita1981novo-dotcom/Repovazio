#!/usr/bin/env python3
"""
live_v6.py — DEFINITIVO FINAL
FIX PRINCIPAL: amerge=inputs=2 (dois sine) causa SIGSEGV no ffmpeg 7.0.2
SOLUÇÃO: gerar WAV binaural em Python (430Hz L + 432Hz R)
          usar -stream_loop -1 para loop infinito sem filtros
Tela 100% PRETA garantida
"""
import os,sys,subprocess,pathlib,shutil,json,urllib.request,urllib.parse
import time,random,math,struct,wave
from datetime import datetime,timezone,timedelta

YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
DURATION_H       = int(os.environ.get("DURATION_H","6"))
LANG             = os.environ.get("LANG_CODE","pt")

BC_ID   = "LhAVPY_HK-4"
ST_KEY  = "ewme-91sq-yae7-yj1q-5skw"
RTMP    = f"rtmp://a.rtmp.youtube.com/live2/{ST_KEY}"
TMP     = pathlib.Path("/tmp")

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
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read()).get("access_token","")
    except Exception as e: err(f"Token: {e}"); return ""

def gerar_wav_binaural():
    """Gera 5s de binaural 430Hz (L) + 432Hz (R) em Python puro — sem ffmpeg"""
    SR,DUR=44100,5; samples=SR*DUR
    out=bytearray()
    for i in range(samples):
        t=i/SR
        L=int(math.sin(2*math.pi*430*t)*22000)
        R=int(math.sin(2*math.pi*432*t)*22000)
        out+=struct.pack('<hh',L,R)
    p=TMP/"binaural_432hz.wav"
    with wave.open(str(p),'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(bytes(out))
    log(f"WAV binaural: {p.stat().st_size//1024}KB | 430Hz(L)+432Hz(R) beat=2Hz ✅")
    return str(p)

TITULOS=[
    "🔴 AO VIVO 24H | ψ TELA PRETA • Binaural 432Hz • Dark Psychology | @psidanicoelho",
    "🔴 LIVE | ψ TELA PRETA 24H • Binaural 432Hz • Narcisismo • Foco Total",
    "🔴 AO VIVO | ψ Tela Preta para Dormir • Binaural 432Hz • Psicologia Quântica",
    "🔴 LIVE 24H | ψ BLACK SCREEN • Binaural 432Hz • Dark Psychology | @psidanicoelho",
]

DESC="""🔴 AO VIVO 24 HORAS — ψ TELA PRETA • BINAURAL 432Hz • DARK PSYCHOLOGY

Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖤 TELA 100% PRETA — zero distração visual
🎵 BINAURAL REAL 432Hz (430Hz esq + 432Hz dir = beat 2Hz DELTA-THETA)
🧠 DARK PSYCHOLOGY — conteúdo baseado em pesquisa científica
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

USO IDEAL:
✅ Dormir profundamente    ✅ Estudar com foco máximo
✅ Meditar                ✅ Trabalhar concentrado
✅ Relaxar                ✅ Reduzir ansiedade

COMO USAR: tela preta = zero distração. Binaural = fones de ouvido.

PSICOLOGIA: Narcisismo • Trauma • Ansiedade • Apego • Dark Psychology
PESQUISA: Harvard • UCLA • van der Kolk • Ainsworth • Gottman

💬 Super Chat: sua dúvida de psicologia ao vivo!
❤️ Super Thanks: apoie a pesquisa!
🔔 ATIVE O SINO para não perder nada!

🌍 DISPONÍVEL EM 8 IDIOMAS:
PT-BR | ENGLISH | DEUTSCH | ESPAÑOL | FRANÇAIS | ITALIANO | 日本語 | 한국어

BLACK SCREEN • TELA PRETA • SCHWARZER BILDSCHIRM • PANTALLA NEGRA
ÉCRAN NOIR • SCHERMO NERO • 黒い画面 • 검은 화면

#telapreta #blackscreen #binaural432hz #432hz #psicologia
#narcisismo #trauma #ansiedade #darkpsychology #danielacoelho
#psidanicoelho #binauralbeats #focototal #concentracao #dormir
#sleepmusic #studymusic #schwarzerbildschirm #pantallenegra"""

def atualizar_seo(token):
    if not token: return
    titulo=random.choice(TITULOS)
    log(f"Título: {titulo[:70]}")
    start=(datetime.now(timezone.utc)+timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        body=json.dumps({"id":BC_ID,"snippet":{"title":titulo[:100],"scheduledStartTime":start,
            "description":DESC[:4900],"categoryId":"22","defaultLanguage":"pt"}}).encode()
        req=urllib.request.Request("https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet",data=body,method="PUT")
        req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
        with urllib.request.urlopen(req,timeout=15): log("SEO ✅")
    except Exception as e: err(f"SEO: {e}")

def thumbnail(token):
    if not token: return
    try:
        from PIL import Image,ImageDraw,ImageFont
        W,H=1280,720; img=Image.new("RGB",(W,H),(0,0,0))
        draw=ImageDraw.Draw(img)
        for y in range(H):
            t=(1-abs(y/H-0.5)*2)*0.14
            draw.line([(0,y),(W,y)],fill=(int(65*t),int(8*t),int(150*t)))
        cx,cy,r=W//2,H//2-15,195
        for i in range(10,0,-1):
            a=i/10*0.43; c=(int(108*a),int(38*a),int(215*a))
            draw.ellipse([(cx-r-i*15,cy-r-i*15),(cx+r+i*15,cy+r+i*15)],fill=c)
        draw.ellipse([(cx-r,cy-r),(cx+r,cy+r)],fill=(38,5,88))
        try: fnt=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",240)
        except: fnt=ImageFont.load_default()
        for dx,dy in [(-4,-4),(4,-4),(-4,4),(4,4)]:
            draw.text((cx-78+dx,cy-128+dy),"ψ",font=fnt,fill=(100,35,200))
        draw.text((cx-78,cy-128),"ψ",font=fnt,fill=(255,255,255))
        try: fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",26)
        except: fb=ImageFont.load_default()
        draw.rectangle([(25,20),(220,57)],fill=(220,20,60))
        draw.text((35,27),"● AO VIVO 24H",font=fb,fill=(255,255,255))
        draw.rectangle([(230,20),(475,57)],fill=(20,20,190))
        draw.text((240,27),"TELA PRETA 100%",font=fb,fill=(255,255,255))
        draw.rectangle([(485,20),(730,57)],fill=(40,120,20))
        draw.text((495,27),"BINAURAL 432Hz",font=fb,fill=(255,255,255))
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
    except Exception as e: err(f"Thumb: {e}")

def transmitir(wav_path, ff, dur_s):
    """
    DEFINITIVO: WAV binaural loop infinito + tela preta
    SEM amerge (causa SIGSEGV no ffmpeg 7.0.2)
    """
    log(f"Transmitindo {dur_s//3600}h → {RTMP[:50]}...")
    cmd=[
        ff,"-y","-re",
        # AUDIO: WAV binaural em loop (-stream_loop ANTES do -i)
        "-stream_loop","-1","-i",wav_path,
        # VIDEO: tela 100% preta
        "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
        # Map: audio do WAV, video da cor preta
        "-map","1:v","-map","0:a",
        # Video: ultrafast, bitrate mínimo
        "-c:v","libx264","-preset","ultrafast","-crf","36",
        "-b:v","150k","-maxrate","200k","-bufsize","400k",
        "-g","50","-r","25","-pix_fmt","yuv420p",
        # Audio: AAC stereo binaural direto do WAV
        "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
        # Output RTMP
        "-f","flv","-t",str(dur_s),
        RTMP
    ]
    result=subprocess.run(cmd,timeout=dur_s+900)
    log(f"rc={result.returncode}")
    return result.returncode

def main():
    log("="*65)
    log(f"LIVE V6 DEFINITIVO | {LANG} | {DURATION_H}h")
    log(f"FIX: WAV binaural loop (sem amerge SIGSEGV)")
    log(f"Broadcast: {BC_ID} | RTMP: {RTMP[:50]}")
    log("="*65)

    ff=ffm()

    # Gerar WAV binaural (rápido, <1s)
    wav=gerar_wav_binaural()

    # Token e SEO
    token=get_token()
    atualizar_seo(token)
    thumbnail(token)

    # Transmitir com retry
    dur_s=DURATION_H*3600; inicio=time.time(); tentativas=0
    while time.time()-inicio<dur_s and tentativas<30:
        restante=int(dur_s-(time.time()-inicio))
        if restante<15: break
        tentativas+=1
        log(f"[{tentativas}] {restante//3600}h{restante%3600//60}m restantes")
        rc=transmitir(wav,ff,restante)
        if rc==0: break
        espera=min(20*tentativas,120); log(f"rc={rc} — retry em {espera}s..."); time.sleep(espera)

    # Encerrar broadcast
    if token:
        try:
            req=urllib.request.Request(f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={BC_ID}&part=id",data=b"{}",method="POST")
            req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
            urllib.request.urlopen(req,timeout=15); log("Broadcast encerrado ✅")
        except Exception as e: err(f"Encerrar: {e}")

    log(f"ENCERRADO | {(time.time()-inicio)//60:.0f}min total")

if __name__=="__main__":
    main()
