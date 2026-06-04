#!/usr/bin/env python3
"""
live_v6.py — DEFINITIVO FINAL
- WAV binaural Python (fix SIGSEGV amerge ffmpeg7)
- Tela 100% PRETA garantida
- SEO dominante em inglês para superar canal mais views do mundo
- Todos os títulos em inglês + keywords multilíngues
"""
import os,sys,subprocess,pathlib,shutil,json,urllib.request,urllib.parse
import time,random,math,struct,wave
from datetime import datetime,timezone,timedelta

YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
DURATION_H       = int(os.environ.get("DURATION_H","6"))
LANG             = os.environ.get("LANG_CODE","en")  # inglês como padrão

# IDs existentes — não criar novos broadcasts
BC_ID = "LhAVPY_HK-4"
ST_KEY = "ewme-91sq-yae7-yj1q-5skw"
RTMP  = f"rtmp://a.rtmp.youtube.com/live2/{ST_KEY}"
TMP   = pathlib.Path("/tmp")

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
    """Gera 5s de binaural 430Hz(L)+432Hz(R) em Python — sem ffmpeg, sem SIGSEGV"""
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
    log(f"WAV binaural: {p.stat().st_size//1024}KB | 430Hz(L)+432Hz(R) | beat=2Hz DELTA ✅")
    return str(p)

# ─── SEO DOMINANTE — superar os canais com mais views do mundo ──
TITULOS_EN = [
    "🔴 LIVE 24/7 | BLACK SCREEN for Sleep 8 Hours | Binaural Beats 432Hz | Dark Psychology",
    "🔴 LIVE 24H | BLACK SCREEN Sleep Music | Binaural Beats 432Hz | Psychology Research",
    "🔴 LIVE | BLACK SCREEN 10 Hours | Binaural Beats 432Hz | Sleep Study Meditation Focus",
    "🔴 24/7 LIVE | BLACK SCREEN for Insomnia | Binaural 432Hz | Dark Psychology Channel",
]

DESC_EN = """🔴 LIVE 24 HOURS — BLACK SCREEN | BINAURAL BEATS 432Hz | DARK PSYCHOLOGY
Daniela Coelho — Human Behavior Researcher | @psidanicoelho

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖤 PURE BLACK SCREEN — 100% dark, zero pixels illuminated
🎵 TRUE BINAURAL BEATS 432Hz (430Hz Left + 432Hz Right = 2Hz Delta)
🧠 DARK PSYCHOLOGY — Narcissism, Trauma, Anxiety, Attachment Theory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

★ USE WITH HEADPHONES for true binaural effect
★ Black screen = zero visual distraction = deeper sleep & focus
★ 100% pure black — NO logos, NO watermarks, NO brightness

PERFECT FOR:
→ Deep Sleep & Insomnia Treatment
→ Intense Study Sessions & Focus
→ Guided Meditation & Mindfulness
→ Relaxation & Stress Relief
→ Work Concentration

🔬 SOURCES: Harvard • UCLA • van der Kolk • Ainsworth • Gottman

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 SUPER CHAT — Your psychology question answered LIVE!
❤️ SUPER THANKS — Support this research!
🔔 SUBSCRIBE + BELL for daily psychology insights!

🌍 GLOBAL: EN 🇺🇸 PT 🇧🇷 DE 🇩🇪 ES 🇪🇸 FR 🇫🇷 IT 🇮🇹 JA 🇯🇵 KO 🇰🇷

#blackscreen #blackscreenforsleep #blackscreen8hours #blackscreen10hours
#blackscreensleep #binauralbeats #binauralbeats432hz #432hz #sleepmusic
#deepsleepmusic #studymusic #focusmusic #meditationmusic #darkpsychology
#narcissism #trauma #anxiety #psychology #danielacoelho #psidanicoelho
#schwarzerbildschirm #pantallenegra #telapreta #ecransombre #schermosero"""

def atualizar_seo(token):
    if not token: return
    titulo=random.choice(TITULOS_EN)
    log(f"Título EN: {titulo[:70]}")
    start=(datetime.now(timezone.utc)+timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        body=json.dumps({"id":BC_ID,"snippet":{"title":titulo[:100],"description":DESC_EN[:4900],
            "scheduledStartTime":start,"categoryId":"22","defaultLanguage":"en"}}).encode()
        req=urllib.request.Request("https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet",
            data=body,method="PUT")
        req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
        with urllib.request.urlopen(req,timeout=15): log("SEO EN dominante ✅")
    except Exception as e: err(f"SEO: {e}")

def thumbnail(token):
    if not token: return
    try:
        from PIL import Image,ImageDraw,ImageFont
        W,H=1280,720
        img=Image.new("RGB",(W,H),(0,0,0))  # PRETO ABSOLUTO
        draw=ImageDraw.Draw(img)
        # Gradiente mínimo
        for y in range(H):
            t=(1-abs(y/H-0.5)*2)*0.12
            draw.line([(0,y),(W,y)],fill=(int(50*t),int(5*t),int(120*t)))
        # Círculo
        cx,cy,r=W//2,H//2-15,195
        for i in range(10,0,-1):
            a=i/10*0.4; c=(int(100*a),int(35*a),int(200*a))
            draw.ellipse([(cx-r-i*15,cy-r-i*15),(cx+r+i*15,cy+r+i*15)],fill=c)
        draw.ellipse([(cx-r,cy-r),(cx+r,cy+r)],fill=(35,5,80))
        # ψ branco
        try: fnt=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",240)
        except: fnt=ImageFont.load_default()
        for dx,dy in [(-4,-4),(4,-4),(-4,4),(4,4)]: draw.text((cx-78+dx,cy-128+dy),"ψ",font=fnt,fill=(90,30,190))
        draw.text((cx-78,cy-128),"ψ",font=fnt,fill=(255,255,255))
        # Badges
        try: fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",26)
        except: fb=ImageFont.load_default()
        draw.rectangle([(25,20),(220,57)],fill=(220,20,60)); draw.text((35,27),"● LIVE 24/7",font=fb,fill=(255,255,255))
        draw.rectangle([(230,20),(470,57)],fill=(0,0,0),outline=(255,255,255),width=1); draw.text((240,27),"BLACK SCREEN 100%",font=fb,fill=(255,255,255))
        draw.rectangle([(480,20),(720,57)],fill=(40,120,20)); draw.text((490,27),"BINAURAL 432Hz",font=fb,fill=(255,255,255))
        try: ftag=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",34)
        except: ftag=ImageFont.load_default()
        draw.text((cx-165,H-65),"@psidanicoelho",font=ftag,fill=(200,175,255))
        draw.rectangle([(0,H-10),(W,H)],fill=(255,255,255))  # linha branca embaixo
        p=TMP/"thumb.jpg"; img.save(str(p),"JPEG",quality=95)
        req=urllib.request.Request(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={BC_ID}&uploadType=media",
            data=open(str(p),"rb").read(),method="POST")
        req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","image/jpeg")
        req.add_header("Content-Length",str(p.stat().st_size))
        with urllib.request.urlopen(req,timeout=60): log("Thumbnail ✅")
    except Exception as e: err(f"Thumb: {e}")

def transmitir(wav_path,ff,dur_s):
    log(f"Transmitindo {dur_s//3600}h → {RTMP[:50]}...")
    cmd=[
        ff,"-y","-re",
        "-stream_loop","-1","-i",wav_path,  # WAV binaural em loop
        "-f","lavfi","-i","color=black:size=1920x1080:rate=25",  # tela preta
        "-map","1:v","-map","0:a",  # video da lavfi, audio do WAV
        "-c:v","libx264","-preset","ultrafast","-crf","36",
        "-b:v","150k","-maxrate","200k","-bufsize","400k",
        "-g","50","-r","25","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
        "-f","flv","-t",str(dur_s), RTMP
    ]
    result=subprocess.run(cmd,timeout=dur_s+900)
    log(f"rc={result.returncode}")
    return result.returncode

def main():
    log("="*65)
    log(f"LIVE V6 | SEO DOMINANTE EN | {DURATION_H}h | {datetime.now(timezone.utc):%H:%M} UTC")
    log(f"Broadcast: {BC_ID} | RTMP: {RTMP[:50]}")
    log("="*65)
    ff=ffm()
    wav=gerar_wav_binaural()
    token=get_token()
    atualizar_seo(token)
    thumbnail(token)
    dur_s=DURATION_H*3600; inicio=time.time(); tentativas=0
    while time.time()-inicio<dur_s and tentativas<30:
        restante=int(dur_s-(time.time()-inicio))
        if restante<15: break
        tentativas+=1
        log(f"[{tentativas}] {restante//3600}h{restante%3600//60}m restantes")
        rc=transmitir(wav,ff,restante)
        if rc==0: break
        espera=min(20*tentativas,120); log(f"rc={rc} retry em {espera}s..."); time.sleep(espera)
    # Encerrar
    if token:
        try:
            req=urllib.request.Request(f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={BC_ID}&part=id",data=b"{}",method="POST")
            req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
            urllib.request.urlopen(req,timeout=15); log("Encerrado ✅")
        except: pass
    log(f"ENCERRADO | {(time.time()-inicio)//60:.0f}min")

if __name__=="__main__":
    main()
