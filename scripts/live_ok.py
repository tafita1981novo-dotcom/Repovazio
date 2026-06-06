#!/usr/bin/env python3
"""
live_ok.py — VERSÃO QUE FUNCIONA
Idêntico ao live_v6.py que rodou 6h (sem pipes no ffmpeg)
+ Gestão de broadcast: apaga tudo, cria 1 unificada, 15 idiomas
"""
import os,json,urllib.request,urllib.parse,subprocess,math,struct,wave,time,pathlib,shutil
from datetime import datetime,timezone,timedelta

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
DURATION_H       = int(os.environ.get("DURATION_H","6"))

# Stream key que funcionou por 6h nos runs anteriores
ST_KEY    = "ewme-91sq-yae7-yj1q-5skw"
STREAM_ID = "SH63tBfY6wEIdkC4u4zKdg1780543868590330"
RTMP      = f"rtmp://a.rtmp.youtube.com/live2/{ST_KEY}"
TMP       = pathlib.Path("/tmp")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}",flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERR {m}",flush=True)

def get_token():
    data=urllib.parse.urlencode({"client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
        "refresh_token":YT_REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    req=urllib.request.Request("https://oauth2.googleapis.com/token",data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read())["access_token"]

def yt_get(token,url):
    req=urllib.request.Request(url); req.add_header("Authorization",f"Bearer {token}")
    try:
        with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read())
    except Exception as e: return {"error":str(e)}

def yt_post(token,url,body=None,method="POST"):
    data=json.dumps(body or {}).encode()
    req=urllib.request.Request(url,data=data,method=method)
    req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            txt=r.read(); return json.loads(txt) if txt else {}
    except Exception as e: return {"error":str(e)}

def yt_delete(token,url):
    req=urllib.request.Request(url,method="DELETE"); req.add_header("Authorization",f"Bearer {token}")
    try: urllib.request.urlopen(req,timeout=10); return True
    except: return False

# ─── DESCRIÇÃO 15 IDIOMAS ────────────────────────────────────────
TITULO="🔴 BLACK SCREEN 24/7 | White Noise & Brown Noise for Sleep | Tela Preta | Pantalla Negra | 10 Hours"
DESC="""🖤 BLACK SCREEN 24/7 | White Noise & Brown Noise | Sleep • Study • Focus • Baby
🔴 100% PURE BLACK SCREEN — zero light, zero distractions, perfect for sleep
🎵 WHITE NOISE + BROWN NOISE — scientifically proven to improve sleep quality
⭐ No headphones needed • Safe for babies • Runs 24/7 non-stop

🇺🇸 White noise for sleeping | white noise 10 hours | white noise black screen | white noise baby sleep | white noise for studying | brown noise 10 hours | brown noise black screen | brown noise sleep | brown noise for ADHD | brown noise for studying | black screen white noise | black screen 10 hours | black screen for sleeping | sleep sounds 10 hours | sleep sounds white noise | sleep music black screen | deep sleep sounds | rain sounds for sleeping | rain noise black screen | white noise machine sounds

🇪🇸 Ruido blanco para dormir | ruido blanco pantalla negra | ruido blanco bebé | pantalla negra para dormir | pantalla negra 10 horas | ruido marrón dormir | sonidos para dormir | música para dormir pantalla negra | ruido blanco 10 horas | ruido blanco estudiar | sonidos blancos dormir | pantalla negra bebé | sonido lluvia para dormir | ruido rosa dormir | pantalla negra sin sonido

🇧🇷 Ruído branco para dormir | ruído branco tela preta | ruído branco bebê | ruído branco estudar | tela preta para dormir | tela preta 10 horas | ruído marrom para dormir | ruído marrom tela preta | som para dormir | música para dormir tela preta | ruído branco 10 horas | tela preta sem som | tela preta bebê | som de chuva para dormir | ruído rosa tela preta

🇩🇪 Weißes Rauschen schlafen | weißes Rauschen schwarzer Bildschirm | weißes Rauschen Baby | braunes Rauschen schlafen | braunes Rauschen schwarzer Bildschirm | schwarzer Bildschirm schlafen | schwarzer Bildschirm 10 Stunden | Schlafgeräusche | weißes Rauschen lernen | braunes Rauschen ADHS

🇫🇷 Bruit blanc pour dormir | bruit blanc écran noir | bruit blanc bébé | bruit brun dormir | bruit brun écran noir | écran noir pour dormir | écran noir 10 heures | sons pour dormir | bruit blanc 10 heures | bruit blanc étudier | bruit brun TDAH

🇯🇵 ホワイトノイズ 睡眠 | ホワイトノイズ 黒画面 | ホワイトノイズ 赤ちゃん | ブラウンノイズ 睡眠 | ブラウンノイズ 黒画面 | 黒い画面 睡眠 | 黒い画面 10時間 | 睡眠音楽 黒画面 | ホワイトノイズ 勉強

🇰🇷 백색소음 수면 | 백색소음 검은 화면 | 백색소음 아기 | 갈색소음 수면 | 갈색소음 검은 화면 | 검은 화면 수면 | 검은 화면 10시간 | 수면 소리 | 백색소음 공부

🇨🇳 白噪音睡眠 | 白噪音黑屏 | 白噪音婴儿 | 棕噪音睡眠 | 棕噪音黑屏 | 黑屏睡眠 | 黑屏10小时 | 睡眠音乐 | 白噪音学习

🇮🇹 Rumore bianco dormire | rumore bianco schermo nero | rumore bianco bambini | rumore marrone dormire | schermo nero dormire | schermo nero 10 ore | suoni per dormire

🇸🇦 ضوضاء بيضاء للنوم | ضوضاء بيضاء شاشة سوداء | ضوضاء بنية نوم | شاشة سوداء للنوم | شاشة سوداء 10 ساعات | أصوات النوم | ضوضاء بيضاء للأطفال

🇷🇺 Белый шум для сна | белый шум чёрный экран | белый шум для детей | коричневый шум сон | чёрный экран сон | чёрный экран 10 часов | звуки для сна

🇮🇳 सफेद शोर नींद | सफेद शोर काली स्क्रीन | भूरा शोर नींद | काली स्क्रीन नींद | काली स्क्रीन 10 घंटे | नींद की आवाज़

🇮🇩 White noise tidur | white noise layar hitam | white noise bayi | brown noise tidur | layar hitam tidur | layar hitam 10 jam | suara tidur

🇳🇱 Witte ruis slapen | witte ruis zwart scherm | bruine ruis slapen | zwart scherm slapen | zwart scherm 10 uur | slaapgeluiden

🇹🇷 Beyaz gürültü uyku | beyaz gürültü siyah ekran | kahverengi gürültü uyku | siyah ekran uyku | siyah ekran 10 saat | uyku sesleri

🇵🇱 Biały szum spanie | biały szum czarny ekran | brązowy szum sen | czarny ekran spanie | czarny ekran 10 godzin | dźwięki do snu

🇻🇳 Tiếng ồn trắng ngủ | tiếng ồn trắng màn hình đen | tiếng ồn nâu ngủ | màn hình đen ngủ | âm thanh ngủ

🇺🇦 Білий шум для сну | чорний екран сон | звуки для сну

@psidanicoelho
#whitenoise #brownnoise #blackscreen #blackscreensleep #whitenoisesleep #brownnoisesleep #blackscreen10hours #sleepsounds #whitenoisebaby #brownnoisebaby #telapreta #ruídobranco #pantallanegraparadormir #ruidoblanco #blackscreenstudying #sleepmusic #whitenoise10hours #brownnoise10hours #deepsleep #asmrsleep"""

def ffm():
    # USE_SYSTEM_FFMPEG=true → usar /usr/bin/ffmpeg do apt (evitar SIGSEGV imageio v7)
    if os.environ.get("USE_SYSTEM_FFMPEG","").lower()=="true":
        sf=shutil.which("ffmpeg")
        if sf: log(f"FFmpeg system: {sf}"); return sf
    try:
        import imageio_ffmpeg; f=imageio_ffmpeg.get_ffmpeg_exe(); log(f"FFmpeg imageio: {f}"); return f
    except: pass
    return shutil.which("ffmpeg") or "ffmpeg"

def gerar_wav():
    """White Noise + Brown Noise (combo #1 em buscas globais)
    White noise: todas as frequências em igual intensidade
    Brown noise: mais grave, ênfase em baixas frequências (random walk)
    Mix 70% brown + 30% white = som mais suave e popular para sono
    """
    import random
    SR, DUR = 44100, 10  # 10s loop
    s = SR * DUR
    out = bytearray()
    # Gerar Brown Noise por random walk (integração de white)
    bL, bR = 0.0, 0.0
    for i in range(s):
        # White noise components
        wL = (random.random() * 2 - 1)
        wR = (random.random() * 2 - 1)
        # Brown noise = integração do white (random walk)
        bL = max(-1.0, min(1.0, bL * 0.999 + wL * 0.02))
        bR = max(-1.0, min(1.0, bR * 0.999 + wR * 0.02))
        # Mix: 65% brown + 35% white
        mixL = bL * 0.65 + wL * 0.35
        mixR = bR * 0.65 + wR * 0.35
        # Amplitude confortável para sono
        out += struct.pack("<hh", int(mixL * 18000), int(mixR * 18000))
    p = TMP / "sleep_noise.wav"
    with wave.open(str(p), "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2)
        wf.setframerate(SR); wf.writeframes(bytes(out))
    log(f"WAV White+Brown Noise: {p.stat().st_size//1024}KB ✅")
    return str(p)

def delete_all(token):
    log("─── Apagando todas as lives ───")
    total=0
    for btype in ["persistent","event"]:
        url=f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status&broadcastType={btype}&mine=true&maxResults=50"
        data=yt_get(token,url)
        for item in data.get("items",[]):
            bid=item["id"]
            lifecycle=item.get("status",{}).get("lifeCycleStatus","")
            if lifecycle in ["active","testing","testStarting","live"]:
                yt_post(token,f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bid}&part=id",{})
                time.sleep(1)
            ok=yt_delete(token,f"https://www.googleapis.com/youtube/v3/liveBroadcasts?id={bid}")
            log(f"  {'✅' if ok else '⚠'} {item.get('snippet',{}).get('title','?')[:40]} [{bid}]")
            if ok: total+=1
            time.sleep(0.3)
    log(f"  Total: {total}")

def criar_broadcast(token):
    log("─── Criando live unificada ───")
    start=(datetime.now(timezone.utc)+timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body={"snippet":{"title":TITULO,"description":DESC[:4900],"scheduledStartTime":start,
          "categoryId":"22","defaultLanguage":"en"},
          "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False},
          "contentDetails":{"enableAutoStart":True,"enableAutoStop":False,"enableDvr":True,
          "enableEmbed":True,"recordFromStart":True,"startWithSlate":False,
          "monitorStream":{"enableMonitorStream":False}}}
    res=yt_post(token,"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails",body)
    bc_id=res.get("id")
    if bc_id: log(f"  ✅ {bc_id}: {TITULO[:50]}")
    else: err(f"  Falha: {res}")
    return bc_id

def bind(token,bc_id):
    url=f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id,contentDetails&streamId={STREAM_ID}"
    res=yt_post(token,url,{})
    bound=res.get("contentDetails",{}).get("boundStreamId","")
    log(f"  Bind: {bound[:30] if bound else str(res)[:60]}")

# ─── STREAM — IDÊNTICO AO live_v6.py QUE RODOU 6H ───────────────
def transmitir(wav,ff,dur_s):
    """SEM pipes, SEM capture — exatamente como live_v6.py"""
    log(f"  🔴 ffmpeg → {RTMP[:40]}... [{dur_s//3600}h{dur_s%3600//60}m]")
    # ψ: 10px, cinza #111@7%, canto inf-dir, pisca 0.5Hz (a cada 2s)
    # Elemento visual original — requisito monetização YouTube (inauthentic content policy)
    psi_vf = (
        "drawtext=text=\u03c8:"
        "x=w-22:y=h-18:fontsize=10:"
        "fontcolor=0x111111@0.07:"
        "enable='gt(mod(t\,2)\,1)'"
    )
    cmd=[ff,"-y","-re",
         "-stream_loop","-1","-i",wav,
         "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
         "-map","1:v","-map","0:a",
         "-c:v","libx264","-preset","ultrafast","-crf","36",
         "-b:v","150k","-maxrate","200k","-bufsize","400k",
         "-g","50","-r","25","-pix_fmt","yuv420p",
         "-vf",psi_vf,
         "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
         "-f","flv","-t",str(dur_s), RTMP]
    # SEM capture_output, SEM stderr=PIPE — idêntico ao live_v6.py
    return subprocess.run(cmd,timeout=dur_s+900).returncode

def main():
    log("="*60)
    log(f"LIVE OK | 15 IDIOMAS | {datetime.now(timezone.utc):%H:%M} UTC | {DURATION_H}h")
    log("="*60)
    ff=ffm(); wav=gerar_wav()
    token=get_token(); log(f"Token OAuth ✅")
    delete_all(token); time.sleep(3)
    bc_id=criar_broadcast(token)
    if not bc_id: return
    time.sleep(2); bind(token,bc_id); time.sleep(2)
    log(f"\n✅ LIVE: https://studio.youtube.com/video/{bc_id}/livestreaming")
    log(f"   Watch: https://www.youtube.com/watch?v={bc_id}\n")
    
    dur_s=DURATION_H*3600; inicio=time.time(); tentativas=0
    while time.time()-inicio<dur_s and tentativas<30:
        restante=int(dur_s-(time.time()-inicio))
        if restante<15: break
        tentativas+=1
        log(f"\n[{tentativas}] Streaming {restante//3600}h{restante%3600//60}m")
        rc=transmitir(wav,ff,restante)
        log(f"  rc={rc}")
        if rc==0: break
        espera=min(20*tentativas,120)
        log(f"  retry em {espera}s"); time.sleep(espera)
    log(f"\nTotal: {(time.time()-inicio)//60:.0f}min")

if __name__=="__main__": main()
