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
TITULO="🔴 BLACK SCREEN 24/7 | Tela Preta para Dormir | Binaural Beats 432Hz | Dark Screen Sleep"
DESC="""🖤 BLACK SCREEN 24/7 | Binaural Beats 432Hz | Sleep • Study • Meditation

🔴 PURE BLACK SCREEN — 100% dark. Zero light. Perfect for sleep, focus & meditation.
🎵 TRUE BINAURAL 432Hz — 430Hz (Left) + 432Hz (Right) = 2Hz Delta beat
   ★ Wear HEADPHONES for the binaural effect to work
🧠 Use for: Deep Sleep • Study Session • Meditation • Relax • ASMR • Focus

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🇺🇸 ENGLISH — Black Screen for Sleep
Black screen 10 hours | Black screen for sleeping | Dark screen sleep | Black screen study
Black screen 8 hours | Black screen for baby sleep | Black screen ASMR | 432hz sleep music
Binaural beats 432hz | 432hz frequency | Sleep music 432hz | Solfeggio 432hz

🇧🇷 PORTUGUÊS — Tela Preta para Dormir
Tela preta para dormir | Tela preta 8 horas | Tela preta para estudar | Tela preta bebê
Tela preta meditação | Frequência 432hz | Binaural 432hz | Música para dormir 432hz
Sons binaurais | Frequência de cura 432hz | Meditação profunda | Sono profundo

🇩🇪 DEUTSCH — Schwarzer Bildschirm zum Schlafen
Schwarzer Bildschirm schlafen | 8 Stunden | Baby | lernen | 432hz Schlafmusik
Binaurale Beats 432hz | Tiefschlaf Musik | 432hz Heilfrequenz | Entspannungsmusik

🇫🇷 FRANÇAIS — Écran Noir pour Dormir
Écran noir pour dormir | 8 heures | bébé | étudier | 432hz | Battements binauraux
Méditation profonde | Sommeil profond | Musique relaxante | ASMR écran noir

🇪🇸 ESPAÑOL — Pantalla Negra para Dormir
Pantalla negra para dormir | 8 horas | bebé | estudiar | 432hz dormir
Latidos binaurales 432hz | Meditación profunda | Música relajante | ASMR pantalla negra

🇯🇵 日本語 — 睡眠のためのブラックスクリーン
黒い画面 睡眠 | 8時間 | 勉強 | 赤ちゃん | 432hz 睡眠音楽 | バイノーラルビート
熟睡 音楽 | 瞑想音楽 | 深い眠り | リラックス音楽 | 432hz ヒーリング

🇰🇷 한국어 — 수면을 위한 검은 화면
검은 화면 수면 | 8시간 | 공부 | 아기 | 432hz 수면 음악 | 바이노럴 비트
깊은 수면 음악 | 명상 음악 | 집중 음악 | 432hz 힐링

🇨🇳 中文 — 黑屏睡眠
黑屏睡眠 | 8小时 | 学习 | 冥想 | 432hz睡眠音乐 | 双耳节拍
深度睡眠音乐 | 放松音乐 | 深度冥想 | 白噪音睡眠 | 432hz频率

🇮🇹 ITALIANO — Schermo Nero per Dormire
Schermo nero dormire | 8 ore | bambino | studiare | 432hz dormire
Battiti binaurali 432hz | Meditazione profonda | Musica rilassante | ASMR schermo nero

🇳🇱 NEDERLANDS — Zwart Scherm voor Slapen
Zwart scherm slapen | 8 uur | baby | studeren | 432hz slaap muziek
Binaurale beats 432hz | Diepe slaap muziek | Zwart scherm meditatie

🇵🇱 POLSKI — Czarny Ekran do Spania
Czarny ekran spanie | 8 godzin | nauka | dziecko | 432hz muzyka do snu
Bity binauralne 432hz | Głęboki sen | Czarny ekran medytacja

🇹🇷 TÜRKÇE — Uyumak için Siyah Ekran
Siyah ekran uyku | 8 saat | bebek | ders çalışma | 432hz uyku müziği
İkili vuruşlar 432hz | Derin uyku müziği | Siyah ekran meditasyon

🇮🇩 INDONESIA — Layar Hitam untuk Tidur
Layar hitam tidur | 8 jam | belajar | bayi | 432hz musik tidur
Binaural beats 432hz | Musik tidur dalam | Layar hitam meditasi

🇮🇳 हिन्दी — सोने के लिए काली स्क्रीन
काली स्क्रीन नींद | 8 घंटे | पढ़ाई | बच्चा | 432hz नींद संगीत
बाइनॉरल बीट्स 432hz | गहरी नींद | काली स्क्रीन ध्यान

🇸🇦 العربية — الشاشة السوداء للنوم
شاشة سوداء للنوم | 8 ساعات | دراسة | طفل | موسيقى نوم 432hz
نغمات ثنائية 432hz | نوم عميق | شاشة سوداء تأمل | صوت للنوم

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🖤 HOW 432Hz WORKS:
430Hz (LEFT ear) + 432Hz (RIGHT ear) = 2Hz DELTA brainwave
→ Induces deep sleep, reduces anxiety, promotes healing
→ Use HEADPHONES. Keep volume LOW.

🔔 SUBSCRIBE | 💬 Super Chat questions | @psidanicoelho"""

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
    """430Hz L + 432Hz R = 2Hz delta — sem filtros ffmpeg"""
    SR,DUR=44100,5; s=SR*DUR; out=bytearray()
    for i in range(s):
        t=i/SR
        out+=struct.pack("<hh",int(math.sin(2*math.pi*430*t)*22000),int(math.sin(2*math.pi*432*t)*22000))
    p=TMP/"b432.wav"
    with wave.open(str(p),"wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(bytes(out))
    log(f"WAV binaural 432Hz: {p.stat().st_size//1024}KB ✅")
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
    cmd=[ff,"-y","-re",
         "-stream_loop","-1","-i",wav,
         "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
         "-map","1:v","-map","0:a",
         "-c:v","libx264","-preset","ultrafast","-crf","36",
         "-b:v","150k","-maxrate","200k","-bufsize","400k",
         "-g","50","-r","25","-pix_fmt","yuv420p",
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
