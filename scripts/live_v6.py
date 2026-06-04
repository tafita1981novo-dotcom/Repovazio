#!/usr/bin/env python3
"""
live_v6.py — VERSÃO FINAL
- Tela 100% PRETA pura (zero overlay, zero pixels iluminados)
- WAV binaural 430Hz/432Hz em loop (fix SIGSEGV amerge ffmpeg7)
- Thumbnail: preta + cérebro branco do canal (sem ψ roxo)
- SEO automático por idioma (muda por horário/país)
- Idioma padrão: INGLÊS (en)
"""
import os,sys,subprocess,pathlib,shutil,json,urllib.request,urllib.parse
import time,random,math,struct,wave,io
from datetime import datetime,timezone,timedelta

YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
DURATION_H       = int(os.environ.get("DURATION_H","6"))

BC_ID  = "LhAVPY_HK-4"
ST_KEY = "ewme-91sq-yae7-yj1q-5skw"
RTMP   = f"rtmp://a.rtmp.youtube.com/live2/{ST_KEY}"
TMP    = pathlib.Path("/tmp")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}",flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERR: {m}",flush=True)

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

def gerar_wav():
    """430Hz L + 432Hz R = beat 2Hz Delta — sem ffmpeg filter (fix SIGSEGV)"""
    SR,DUR=44100,5; s=SR*DUR; out=bytearray()
    for i in range(s):
        t=i/SR
        out+=struct.pack('<hh',int(math.sin(2*math.pi*430*t)*22000),int(math.sin(2*math.pi*432*t)*22000))
    p=TMP/"b432.wav"
    with wave.open(str(p),'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(bytes(out))
    log(f"WAV binaural: {p.stat().st_size//1024}KB ✅"); return str(p)

# ─── SEO POR IDIOMA — muda automaticamente baseado no horário ────
# Lógica: hora UTC → idioma dominante (CPM máximo naquele momento)
TITULOS={
    "en":["🔴 LIVE 24/7 | BLACK SCREEN for Sleep 8 Hours | Binaural Beats 432Hz | Dark Psychology",
          "🔴 LIVE | BLACK SCREEN 10 Hours | Binaural Beats 432Hz | Sleep Study Meditation Focus",
          "🔴 24/7 LIVE | BLACK SCREEN for Insomnia | Binaural 432Hz | Dark Psychology Research",
          "🔴 LIVE | PURE BLACK SCREEN | Binaural Beats 432Hz | Dark Psychology Channel"],
    "de":["🔴 LIVE 24/7 | SCHWARZER BILDSCHIRM 8 Stunden Schlafen | Binaural 432Hz | Psychologie",
          "🔴 LIVE | SCHWARZER BILDSCHIRM 10 Stunden | Binaural 432Hz | Schlaf Fokus Meditation"],
    "es":["🔴 EN VIVO 24H | PANTALLA NEGRA 8 Horas Dormir | Binaural 432Hz | Psicología Oscura",
          "🔴 EN VIVO | PANTALLA NEGRA 10 Horas | Binaural 432Hz | Sueño Estudio Meditación"],
    "fr":["🔴 EN DIRECT 24H | ÉCRAN NOIR 8 Heures Dormir | Binaural 432Hz | Psychologie Sombre"],
    "pt":["🔴 AO VIVO 24H | TELA PRETA para Dormir 8 Horas | Binaural 432Hz | Dark Psychology",
          "🔴 LIVE | TELA PRETA 10 Horas | Binaural 432Hz | Sono Estudo Meditação"],
    "ja":["🔴 24時間ライブ | 真っ黒画面 8時間 睡眠 | バイノーラル432Hz | ダーク心理学"],
    "ko":["🔴 24시간 라이브 | 검은 화면 8시간 수면 | 바이노럴 432Hz | 다크 심리학"],
}
DESCS={
    "en":"""🔴 LIVE 24 HOURS — BLACK SCREEN | BINAURAL BEATS 432Hz | DARK PSYCHOLOGY
Daniela Coelho — Human Behavior Researcher | @psidanicoelho

🖤 PURE BLACK SCREEN — 100% dark, zero pixels illuminated
🎵 TRUE BINAURAL 432Hz (430Hz Left + 432Hz Right = 2Hz DELTA beat)
🧠 DARK PSYCHOLOGY — Narcissism, Trauma, Anxiety, Attachment Theory

★ Use HEADPHONES for true binaural effect
★ Perfect: Deep Sleep • Study • Meditation • Work • Focus
★ NO logos, NO watermarks, NO brightness — pure black

Research: Harvard • UCLA • van der Kolk • Ainsworth • Gottman
💬 Super Chat: psychology questions LIVE!
🔔 SUBSCRIBE + BELL!

#blackscreen #blackscreenforsleep #blackscreen8hours #binauralbeats432hz
#432hz #sleepmusic #studymusic #darkpsychology #narcissism #danielacoelho""",
    "de":"""🔴 LIVE 24 STUNDEN — SCHWARZER BILDSCHIRM | BINAURAL 432Hz | PSYCHOLOGIE
Daniela Coelho — Verhaltensforscherin | @psidanicoelho
🖤 100% SCHWARZER BILDSCHIRM | ECHTER BINAURAL 432Hz
★ Kopfhörer empfohlen | Ideal: Schlaf • Lernen • Meditation
#schwarzerbildschirm #binauralbeats432hz #432hz #psychologie #danielacoelho""",
    "pt":"""🔴 AO VIVO 24 HORAS — TELA PRETA | BINAURAL 432Hz | DARK PSYCHOLOGY
Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho
🖤 TELA 100% PRETA | BINAURAL REAL 432Hz
★ Use fones de ouvido | Ideal: Sono • Estudo • Meditação
#telapreta #binaural432hz #432hz #psicologia #narcisismo #danielacoelho""",
}

def lang_por_hora():
    """Idioma com maior CPM/audiência baseado na hora UTC"""
    h=datetime.now(timezone.utc).hour
    # 00-04 BR/PT noite → pt
    if 0<=h<5:   return "pt"
    # 05-11 Europa acordando → DE (€14-18 CPM)
    elif 5<=h<12: return "de"
    # 12-19 EUA (maior CPM $18) → EN
    elif 12<=h<20: return "en"
    # 20-23 BR prime time → pt
    else: return "pt"

def atualizar_seo(token):
    if not token: return
    lang=lang_por_hora()
    titulo=random.choice(TITULOS.get(lang, TITULOS["en"]))
    desc=DESCS.get(lang, DESCS["en"])
    log(f"SEO [{lang.upper()}] {datetime.now(timezone.utc).hour}h UTC: {titulo[:60]}")
    start=(datetime.now(timezone.utc)+timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        body=json.dumps({"id":BC_ID,"snippet":{"title":titulo[:100],"description":desc[:4900],
            "scheduledStartTime":start,"categoryId":"22","defaultLanguage":"en"}}).encode()
        req=urllib.request.Request("https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet",
            data=body,method="PUT")
        req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
        with urllib.request.urlopen(req,timeout=15): log(f"SEO ✅")
    except Exception as e: err(f"SEO: {e}")

def thumbnail(token):
    """Thumbnail 100% PRETA com cérebro BRANCO do canal — sem ψ, sem roxo"""
    if not token: return
    try:
        from PIL import Image,ImageDraw,ImageFont,ImageEnhance
        W,H=1280,720
        img=Image.new("RGB",(W,H),(0,0,0))  # PRETO ABSOLUTO
        draw=ImageDraw.Draw(img)
        
        # Baixar e processar avatar do canal (cérebro)
        try:
            av_url="https://yt3.ggpht.com/4NDK-JaBRi0uMyCCeOz-imtfhs6zHuQ2sxUn3d2gCjY_NyS_Z50OCENLFZrS_RjY5wOwKXch=s800-c-k-c0x00ffffff-no-rj"
            req_a=urllib.request.Request(av_url); req_a.add_header("User-Agent","Mozilla/5.0")
            chunks=[]
            with urllib.request.urlopen(req_a,timeout=30) as r:
                while True:
                    chunk=r.read(8192)
                    if not chunk: break
                    chunks.append(chunk)
            brain=Image.open(io.BytesIO(b"".join(chunks))).convert("RGB")
            brain2=ImageEnhance.Brightness(brain).enhance(2.0)
            brain3=ImageEnhance.Contrast(brain2).enhance(2.0)
            bw2,bh2=brain.size
            gray=Image.new("L",(bw2,bh2)); p_in=brain3.load(); p_out=gray.load()
            for y2 in range(bh2):
                for x2 in range(bw2):
                    r2,g2,b2=p_in[x2,y2]; lum=(r2+g2+b2)//3
                    p_out[x2,y2]=min(255,int(lum*1.4)) if lum>30 else 0
            brain_rgb=Image.merge("RGB",[gray,gray,gray])
            target=460
            brain_r=brain_rgb.resize((target,target),Image.LANCZOS)
            bx=W//2-target//2; by=H//2-target//2-10
            img.paste(brain_r,(bx,by))
        except Exception as e: err(f"Avatar: {e}")
        
        # Badges em inglês
        try: fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",26)
        except: fb=ImageFont.load_default()
        try: ft=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",32)
        except: ft=ImageFont.load_default()
        
        draw.rectangle([(14,14),(155,50)],fill=(220,20,60))
        draw.text((20,18),"● LIVE 24/7",font=fb,fill=(255,255,255))
        draw.rectangle([(160,14),(395,50)],fill=(0,0,0),outline=(255,255,255),width=1)
        draw.text((166,18),"BLACK SCREEN",font=fb,fill=(255,255,255))
        draw.rectangle([(400,14),(640,50)],fill=(22,101,52))
        draw.text((406,18),"BINAURAL 432Hz",font=fb,fill=(255,255,255))
        draw.text((W-285,H-48),"@psidanicoelho",font=ft,fill=(200,200,200))
        draw.rectangle([(0,0),(W,2)],fill=(255,255,255))
        draw.rectangle([(0,H-2),(W,H)],fill=(255,255,255))
        
        p=TMP/"thumb.jpg"; img.save(str(p),"JPEG",quality=95)
        req2=urllib.request.Request(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={BC_ID}&uploadType=media",
            data=open(str(p),"rb").read(),method="POST")
        req2.add_header("Authorization",f"Bearer {token}"); req2.add_header("Content-Type","image/jpeg")
        req2.add_header("Content-Length",str(p.stat().st_size))
        with urllib.request.urlopen(req2,timeout=60): log("Thumbnail preta+cérebro ✅")
    except Exception as e: err(f"Thumb: {e}")

def transmitir(wav,ff,dur_s):
    log(f"Transmitindo {dur_s//3600}h → {RTMP[:45]}...")
    cmd=[ff,"-y","-re",
         "-stream_loop","-1","-i",wav,
         "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
         "-map","1:v","-map","0:a",
         "-c:v","libx264","-preset","ultrafast","-crf","36",
         "-b:v","150k","-maxrate","200k","-bufsize","400k",
         "-g","50","-r","25","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
         "-f","flv","-t",str(dur_s), RTMP]
    rc=subprocess.run(cmd,timeout=dur_s+900).returncode
    log(f"rc={rc}"); return rc

def main():
    log("="*65)
    log(f"LIVE V6 FINAL | {datetime.now(timezone.utc):%H:%M} UTC | {DURATION_H}h")
    log(f"Tela: 100% PRETA | Audio: WAV binaural 432Hz | SEO: auto-idioma")
    log("="*65)
    ff=ffm(); wav=gerar_wav()
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
        espera=min(20*tentativas,120); log(f"retry em {espera}s..."); time.sleep(espera)
    if token:
        try:
            req=urllib.request.Request(f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={BC_ID}&part=id",data=b"{}",method="POST")
            req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
            urllib.request.urlopen(req,timeout=15); log("Encerrado ✅")
        except: pass
    log(f"TOTAL: {(time.time()-inicio)//60:.0f}min")

if __name__=="__main__":
    main()
