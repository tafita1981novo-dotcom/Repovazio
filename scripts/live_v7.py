#!/usr/bin/env python3
"""
live_v7.py — 15 IDIOMAS | DELETE OLD LIVES | SEO GLOBAL
- Apaga TODAS as lives existentes do canal
- Cria NOVA live broadcast
- Descrição em 15 idiomas (EN/DE/FR/ES/PT/JA/KO/ZH/IT/NL/PL/TR/ID/HI/AR)
- Tela 100% preta + binaural 432Hz (430L+432R)
- Thumbnail preta + cérebro branco
- SEO automático por hora UTC → idioma dominante
"""
import os,sys,subprocess,pathlib,shutil,json,urllib.request,urllib.parse
import time,random,math,struct,wave,io
from datetime import datetime,timezone,timedelta

YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
DURATION_H       = int(os.environ.get("DURATION_H","6"))
CHANNEL_ID       = "UCSH63tBfY6wEIdkC4u4zKdg"

ST_KEY = "ewme-91sq-yae7-yj1q-5skw"
RTMP   = f"rtmp://a.rtmp.youtube.com/live2/{ST_KEY}"
TMP    = pathlib.Path("/tmp")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}",flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERR: {m}",flush=True)

def ffm():
    try:
        import imageio_ffmpeg; f=imageio_ffmpeg.get_ffmpeg_exe(); return f
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

def yt_get(token, url):
    req=urllib.request.Request(url)
    req.add_header("Authorization",f"Bearer {token}")
    try:
        with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read())
    except: return {}

def yt_post(token, url, body=None, method="POST"):
    data=json.dumps(body).encode() if body else b"{}"
    req=urllib.request.Request(url,data=data,method=method)
    req.add_header("Authorization",f"Bearer {token}")
    req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            txt=r.read()
            return json.loads(txt) if txt else {}
    except Exception as e: return {"error":str(e)}

def delete_all_broadcasts(token):
    """Apaga TODAS as lives do canal (active + complete + testStarting + ready)"""
    if not token: return
    log("─── DELETANDO todas as lives do canal ───")
    deleted=0
    for status in ["active","complete","created","ready","testStarting","testing"]:
        url=f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet&broadcastStatus={status}&maxResults=50"
        data=yt_get(token,url)
        items=data.get("items",[])
        for item in items:
            bc_id=item["id"]
            title=item.get("snippet",{}).get("title","?")[:50]
            # Se ativa, encerrar primeiro
            if status in ["active","testing"]:
                yt_post(token,f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bc_id}&part=id")
                time.sleep(2)
            # Deletar
            req=urllib.request.Request(
                f"https://www.googleapis.com/youtube/v3/liveBroadcasts?id={bc_id}",
                method="DELETE")
            req.add_header("Authorization",f"Bearer {token}")
            try:
                urllib.request.urlopen(req,timeout=10)
                log(f"  ✅ Deletada: {title} [{bc_id}]")
                deleted+=1
            except Exception as e:
                err(f"  Delete {bc_id}: {e}")
            time.sleep(0.5)
    log(f"  Total deletadas: {deleted}")
    return deleted

def criar_broadcast(token):
    """Cria nova live broadcast persistente"""
    if not token: return None
    log("─── CRIANDO nova live broadcast ───")
    start=(datetime.now(timezone.utc)+timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body={
        "snippet":{
            "title":"🔴 LIVE 24/7 | BLACK SCREEN for Sleep | Binaural Beats 432Hz | Dark Psychology",
            "description":DESC_15_LANGS,
            "scheduledStartTime":start,
            "categoryId":"22"
        },
        "status":{
            "privacyStatus":"public",
            "selfDeclaredMadeForKids":False
        },
        "contentDetails":{
            "enableAutoStart":True,
            "enableAutoStop":False,
            "enableDvr":True,
            "enableEmbed":True,
            "recordFromStart":True,
            "startWithSlate":False
        }
    }
    res=yt_post(token,"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails",body)
    if "id" in res:
        bc_id=res["id"]
        log(f"  ✅ Nova live: {bc_id}")
        # Bindar ao stream key
        bind_url=f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id&streamId={ST_KEY}"
        yt_post(token,bind_url,{})
        return bc_id
    else:
        err(f"  Falha criar: {res}")
        return None

def gerar_wav():
    SR,DUR=44100,5; s=SR*DUR; out=bytearray()
    for i in range(s):
        t=i/SR
        out+=struct.pack('<hh',int(math.sin(2*math.pi*430*t)*22000),int(math.sin(2*math.pi*432*t)*22000))
    p=TMP/"b432.wav"
    with wave.open(str(p),'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(bytes(out))
    log(f"WAV binaural 432Hz: {p.stat().st_size//1024}KB ✅"); return str(p)

# ─── 15 IDIOMAS: títulos rotativos por hora UTC ───────────────────
TITULOS={
    "en":[
        "🔴 LIVE 24/7 | BLACK SCREEN for Sleep 8 Hours | Binaural Beats 432Hz | Dark Psychology",
        "🔴 LIVE | BLACK SCREEN 10 Hours | Binaural Beats 432Hz | Sleep Study Meditation",
        "🔴 24/7 LIVE | BLACK SCREEN for Insomnia | Binaural 432Hz | Dark Psychology Research",
    ],
    "de":[
        "🔴 LIVE 24/7 | SCHWARZER BILDSCHIRM 8 Stunden | Binaural 432Hz | Psychologie",
        "🔴 LIVE | SCHWARZER BILDSCHIRM 10 Stunden Schlafen | Binaural 432Hz | Schlaf Meditation",
    ],
    "fr":[
        "🔴 EN DIRECT 24H | ÉCRAN NOIR 8 Heures Dormir | Binaural 432Hz | Psychologie Sombre",
        "🔴 LIVE | ÉCRAN NOIR 10 Heures | Binaural 432Hz | Sommeil Étude Méditation",
    ],
    "es":[
        "🔴 EN VIVO 24H | PANTALLA NEGRA 8 Horas Dormir | Binaural 432Hz | Psicología Oscura",
        "🔴 EN VIVO | PANTALLA NEGRA 10 Horas | Binaural 432Hz | Sueño Estudio Meditación",
    ],
    "pt":[
        "🔴 AO VIVO 24H | TELA PRETA para Dormir 8 Horas | Binaural 432Hz | Dark Psychology",
        "🔴 LIVE | TELA PRETA 10 Horas | Binaural 432Hz | Sono Estudo Meditação",
    ],
    "ja":[
        "🔴 24時間ライブ | 真っ黒画面 8時間 睡眠 | バイノーラル432Hz | ダーク心理学",
        "🔴 ライブ | ブラックスクリーン 10時間 | バイノーラル432Hz | 睡眠 勉強 瞑想",
    ],
    "ko":[
        "🔴 24시간 라이브 | 검은 화면 8시간 수면 | 바이노럴 432Hz | 다크 심리학",
        "🔴 라이브 | 검은화면 10시간 | 바이노럴 432Hz | 수면 공부 명상",
    ],
    "zh":[
        "🔴 24小时直播 | 纯黑屏幕 睡眠8小时 | 双耳节拍432Hz | 暗黑心理学",
        "🔴 直播 | 黑屏 10小时 | 双耳节拍432Hz | 睡眠 学习 冥想",
    ],
    "it":[
        "🔴 LIVE 24H | SCHERMO NERO 8 Ore Dormire | Binaural 432Hz | Psicologia Oscura",
        "🔴 LIVE | SCHERMO NERO 10 Ore | Binaural 432Hz | Sonno Studio Meditazione",
    ],
    "nl":[
        "🔴 LIVE 24/7 | ZWART SCHERM 8 Uur Slapen | Binaural 432Hz | Donkere Psychologie",
        "🔴 LIVE | ZWART SCHERM 10 Uur | Binaural 432Hz | Slaap Studie Meditatie",
    ],
    "pl":[
        "🔴 NA ŻYWO 24H | CZARNY EKRAN 8 Godzin Sen | Binaural 432Hz | Ciemna Psychologia",
        "🔴 LIVE | CZARNY EKRAN 10 Godzin | Binaural 432Hz | Sen Nauka Medytacja",
    ],
    "tr":[
        "🔴 CANLI 24S | SİYAH EKRAN 8 Saat Uyku | Binaural 432Hz | Karanlık Psikoloji",
        "🔴 CANLI | SİYAH EKRAN 10 Saat | Binaural 432Hz | Uyku Çalışma Meditasyon",
    ],
    "id":[
        "🔴 LIVE 24 JAM | LAYAR HITAM 8 Jam Tidur | Binaural 432Hz | Psikologi Gelap",
        "🔴 LIVE | LAYAR HITAM 10 Jam | Binaural 432Hz | Tidur Belajar Meditasi",
    ],
    "hi":[
        "🔴 24 घंटे लाइव | काली स्क्रीन 8 घंटे नींद | बाइनॉरल 432Hz | डार्क साइकोलॉजी",
        "🔴 लाइव | काली स्क्रीन 10 घंटे | बाइनॉरल 432Hz | नींद अध्ययन ध्यान",
    ],
    "ar":[
        "🔴 بث مباشر 24 ساعة | شاشة سوداء 8 ساعات نوم | نغمات ثنائية 432Hz | علم النفس المظلم",
        "🔴 مباشر | شاشة سوداء 10 ساعات | ثنائي 432Hz | نوم دراسة تأمل",
    ],
}

# ─── DESCRIÇÃO MEGA-SEO em 15 IDIOMAS ────────────────────────────
DESC_15_LANGS = """🔴 LIVE 24/7 | BLACK SCREEN | BINAURAL BEATS 432Hz | DARK PSYCHOLOGY
Daniela Coelho — Human Behavior Researcher | @psidanicoelho

🖤 PURE BLACK SCREEN — 100% dark, zero pixels illuminated
🎵 TRUE BINAURAL 432Hz (430Hz Left + 432Hz Right = 2Hz DELTA beat)
🧠 DARK PSYCHOLOGY — Narcissism, Trauma, Anxiety, Attachment Theory
★ Use HEADPHONES for true binaural effect
★ Perfect: Deep Sleep • Study • Meditation • Work • Focus

🔴 LIVE 24H | SCHWARZER BILDSCHIRM | BINAURAL 432Hz | PSYCHOLOGIE [DE]
Daniela Coelho — Verhaltensforscherin | @psidanicoelho
🖤 100% SCHWARZ | ECHTER BINAURAL 432Hz | Kopfhörer empfohlen
Ideal: Schlafen • Lernen • Meditation • Fokus • Arbeit

🔴 EN DIRECT 24H | ÉCRAN NOIR | BINAURAL 432Hz | PSYCHOLOGIE SOMBRE [FR]
Daniela Coelho — Chercheuse en Comportement | @psidanicoelho
🖤 ÉCRAN 100% NOIR | VRAI BINAURAL 432Hz | Casque recommandé
Idéal: Sommeil • Étude • Méditation • Concentration

🔴 EN VIVO 24H | PANTALLA NEGRA | BINAURAL 432Hz | PSICOLOGÍA OSCURA [ES]
Daniela Coelho — Investigadora Comportamiento Humano | @psidanicoelho
🖤 PANTALLA 100% NEGRA | BINAURAL REAL 432Hz | Usar auriculares
Ideal: Sueño • Estudio • Meditación • Trabajo • Enfoque

🔴 AO VIVO 24H | TELA PRETA | BINAURAL 432Hz | DARK PSYCHOLOGY [PT]
Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho
🖤 TELA 100% PRETA | BINAURAL REAL 432Hz | Use fones de ouvido
Ideal: Sono • Estudo • Meditação • Trabalho • Foco

🔴 24時間ライブ | ブラックスクリーン | バイノーラル432Hz | ダーク心理学 [JA]
ダニエラ・コエーリョ — 人間行動研究者 | @psidanicoelho
🖤 完全ブラック画面 | 本物のバイノーラル432Hz | ヘッドフォン推奨
最適: 睡眠・勉強・瞑想・集中・作業

🔴 24시간 라이브 | 검은 화면 | 바이노럴 432Hz | 다크 심리학 [KO]
다니엘라 코에요 — 인간 행동 연구자 | @psidanicoelho
🖤 100% 검은 화면 | 진짜 바이노럴 432Hz | 헤드폰 사용 권장
최적: 수면 • 공부 • 명상 • 집중 • 작업

🔴 24小时直播 | 纯黑屏幕 | 双耳节拍432Hz | 暗黑心理学 [ZH]
达尼埃拉·科埃略 — 人类行为研究者 | @psidanicoelho
🖤 纯黑屏幕100% | 真实双耳节拍432Hz | 建议使用耳机
最适合：睡眠 • 学习 • 冥想 • 专注 • 工作

🔴 LIVE 24H | SCHERMO NERO | BINAURAL 432Hz | PSICOLOGIA OSCURA [IT]
Daniela Coelho — Ricercatrice Comportamento Umano | @psidanicoelho
🖤 SCHERMO 100% NERO | BINAURAL VERO 432Hz | Cuffie raccomandate
Ideale: Sonno • Studio • Meditazione • Concentrazione

🔴 LIVE 24/7 | ZWART SCHERM | BINAURAL 432Hz | DONKERE PSYCHOLOGIE [NL]
Daniela Coelho — Menselijk Gedragsonderzoeker | @psidanicoelho
🖤 100% ZWART SCHERM | ECHTE BINAURAL 432Hz | Koptelefoon aanbevolen
Ideaal: Slaap • Studie • Meditatie • Focus • Werk

🔴 NA ŻYWO 24H | CZARNY EKRAN | BINAURAL 432Hz | CIEMNA PSYCHOLOGIA [PL]
Daniela Coelho — Badaczka Zachowań Ludzkich | @psidanicoelho
🖤 100% CZARNY EKRAN | PRAWDZIWY BINAURAL 432Hz | Słuchawki zalecane
Idealne: Sen • Nauka • Medytacja • Skupienie • Praca

🔴 CANLI 24S | SİYAH EKRAN | BINAURAL 432Hz | KARANLIK PSİKOLOJİ [TR]
Daniela Coelho — İnsan Davranışı Araştırmacısı | @psidanicoelho
🖤 %100 SİYAH EKRAN | GERÇEK BİNAURAL 432Hz | Kulaklık önerilir
İdeal: Uyku • Çalışma • Meditasyon • Odaklanma

🔴 LIVE 24 JAM | LAYAR HITAM | BINAURAL 432Hz | PSIKOLOGI GELAP [ID]
Daniela Coelho — Peneliti Perilaku Manusia | @psidanicoelho
🖤 LAYAR 100% HITAM | BINAURAL ASLI 432Hz | Gunakan headphone
Ideal: Tidur • Belajar • Meditasi • Fokus • Kerja

🔴 24 घंटे लाइव | काली स्क्रीन | बाइनॉरल 432Hz | डार्क साइकोलॉजी [HI]
डेनियला कोएल्हो — मानव व्यवहार शोधकर्ता | @psidanicoelho
🖤 100% काली स्क्रीन | असली बाइनॉरल 432Hz | हेडफोन अनुशंसित
आदर्श: नींद • अध्ययन • ध्यान • एकाग्रता • काम

🔴 بث مباشر 24 ساعة | شاشة سوداء | نغمات ثنائية 432Hz | علم النفس المظلم [AR]
دانييلا كويلو — باحثة في السلوك البشري | @psidanicoelho
🖤 شاشة سوداء 100٪ | ثنائي حقيقي 432Hz | يُنصح بالسماعات
مثالي: النوم • الدراسة • التأمل • التركيز • العمل

─────────────────────────────────────────────────
Research: Harvard • UCLA • van der Kolk • Ainsworth • Gottman • Beck
🔔 SUBSCRIBE + BELL | 💬 Super Chat: psychology questions LIVE!

#blackscreen #blackscreenforsleep #blackscreen8hours #blackscreen10hours
#binauralbeats432hz #432hz #432hzmusic #sleepmusic #studymusic
#darkpsychology #narcissism #trauma #anxiety #danielacoelho #psidanicoelho
#schwarzerbildschirm #ecrannoirdormir #pantallanegraparadormir
#telaprreta #shiroiscreen #검은화면 #黑屏幕 #schhermonero #zwartscherm"""

# ─── LÓGICA DE IDIOMA POR HORA UTC (máximo CPM) ──────────────────
LANG_SCHEDULE = {
    0: "pt",   # 00h BR meia-noite
    1: "pt",   # 01h BR
    2: "ar",   # 02h Oriente Médio manhã
    3: "ar",   # 03h Árabe
    4: "ar",   # 04h
    5: "de",   # 05h Europa acorda (DE maior CPM)
    6: "de",   # 06h Alemanha manhã
    7: "nl",   # 07h Holanda (alto CPM)
    8: "fr",   # 08h França manhã
    9: "it",   # 09h Itália
    10:"pl",   # 10h Polônia
    11:"es",   # 11h Espanha
    12:"en",   # 12h EUA EDT acorda ($18-25)
    13:"en",   # 13h EUA prime
    14:"en",   # 14h EUA alto CPM
    15:"en",   # 15h EUA pico
    16:"en",   # 16h EUA pico
    17:"en",   # 17h EUA pico
    18:"pt",   # 18h BR prime time
    19:"pt",   # 19h BR noite
    20:"ja",   # 20h Japão manhã
    21:"ja",   # 21h Japão
    22:"ko",   # 22h Coreia
    23:"zh",   # 23h China
}

def lang_por_hora():
    h=datetime.now(timezone.utc).hour
    return LANG_SCHEDULE.get(h,"en")

def atualizar_seo(token, bc_id):
    if not token or not bc_id: return
    lang=lang_por_hora()
    titulo=random.choice(TITULOS.get(lang, TITULOS["en"]))
    log(f"SEO [{lang.upper()}] {datetime.now(timezone.utc).hour}h UTC: {titulo[:60]}")
    start=(datetime.now(timezone.utc)+timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body={"id":bc_id,"snippet":{
        "title":titulo[:100],
        "description":DESC_15_LANGS[:4900],
        "scheduledStartTime":start,
        "categoryId":"22",
        "defaultLanguage":"en"
    }}
    res=yt_post(token,
        "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet",
        body, "PUT")
    if "error" not in str(res)[:20]: log("SEO ✅")
    else: err(f"SEO: {res}")

def thumbnail(token, bc_id):
    if not token or not bc_id: return
    try:
        from PIL import Image,ImageDraw,ImageFont,ImageEnhance
        W,H=1280,720
        img=Image.new("RGB",(W,H),(0,0,0))
        draw=ImageDraw.Draw(img)
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
        req2=urllib.request.Request(
            f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={bc_id}&uploadType=media",
            data=open(str(p),"rb").read(),method="POST")
        req2.add_header("Authorization",f"Bearer {token}")
        req2.add_header("Content-Type","image/jpeg")
        req2.add_header("Content-Length",str(p.stat().st_size))
        with urllib.request.urlopen(req2,timeout=60): log("Thumbnail ✅")
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
    log(f"LIVE V7 | 15 IDIOMAS | DELETE+RECRIAR | {datetime.now(timezone.utc):%H:%M} UTC")
    log("="*65)
    ff=ffm(); wav=gerar_wav()
    token=get_token()
    if not token:
        log("⚠️  Sem OAuth — stream sem gerenciamento de broadcast")
    else:
        # 1. Deletar todas as lives existentes
        delete_all_broadcasts(token)
        time.sleep(3)
        # 2. Criar nova broadcast
        bc_id=criar_broadcast(token)
        time.sleep(3)
        # 3. SEO + thumbnail
        if bc_id:
            atualizar_seo(token, bc_id)
            thumbnail(token, bc_id)
    # 4. Stream
    dur_s=DURATION_H*3600; inicio=time.time(); tentativas=0
    while time.time()-inicio<dur_s and tentativas<30:
        restante=int(dur_s-(time.time()-inicio))
        if restante<15: break
        tentativas+=1
        log(f"[{tentativas}] {restante//3600}h{restante%3600//60}m restantes")
        rc=transmitir(wav,ff,restante)
        if rc==0: break
        espera=min(20*tentativas,120); log(f"retry em {espera}s..."); time.sleep(espera)
    log(f"TOTAL: {(time.time()-inicio)//60:.0f}min")

if __name__=="__main__":
    main()
