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
TITULO="🔴 LIVE 24/7 | BLACK SCREEN for Sleep & Focus | Binaural Beats 432Hz | Dark Psychology"
DESC="""🔴 LIVE 24/7 | BLACK SCREEN | BINAURAL BEATS 432Hz | DARK PSYCHOLOGY
Daniela Coelho — Human Behavior Researcher | @psidanicoelho
🖤 PURE BLACK SCREEN — 100% dark, zero pixels illuminated
🎵 TRUE BINAURAL 432Hz (430Hz Left + 432Hz Right = 2Hz DELTA beat)
🧠 DARK PSYCHOLOGY — Narcissism, Trauma, Anxiety, Attachment Theory
★ Use HEADPHONES for true binaural effect
★ Perfect: Deep Sleep • Study • Meditation • Work • Focus

🔴 LIVE | SCHWARZER BILDSCHIRM | BINAURAL 432Hz | PSYCHOLOGIE [DE]
Daniela Coelho | @psidanicoelho | 🖤 100% SCHWARZ | Kopfhörer | Schlafen • Lernen • Meditieren

🔴 EN DIRECT | ÉCRAN NOIR | BINAURAL 432Hz | PSYCHOLOGIE SOMBRE [FR]
Daniela Coelho | @psidanicoelho | 🖤 100% NOIR | Casque | Sommeil • Étude • Méditation

🔴 EN VIVO | PANTALLA NEGRA | BINAURAL 432Hz | PSICOLOGÍA OSCURA [ES]
Daniela Coelho | @psidanicoelho | 🖤 100% NEGRA | Auriculares | Sueño • Estudio • Meditación

🔴 AO VIVO | TELA PRETA | BINAURAL 432Hz | DARK PSYCHOLOGY [PT]
Daniela Coelho | @psidanicoelho | 🖤 100% PRETA | Fones | Sono • Estudo • Meditação

🔴 24時間ライブ | ブラックスクリーン | バイノーラル432Hz | ダーク心理学 [JA]
ダニエラ・コエーリョ | @psidanicoelho | 🖤 完全ブラック | ヘッドフォン | 睡眠・勉強・瞑想

🔴 24시간 라이브 | 검은 화면 | 바이노럴 432Hz | 다크 심리학 [KO]
다니엘라 코에요 | @psidanicoelho | 🖤 100% 검은 | 헤드폰 | 수면 • 공부 • 명상

🔴 24小时直播 | 纯黑屏幕 | 双耳节拍432Hz | 暗黑心理学 [ZH]
达尼埃拉·科埃略 | @psidanicoelho | 🖤 纯黑100% | 耳机 | 睡眠 • 学习 • 冥想

🔴 LIVE | SCHERMO NERO | BINAURAL 432Hz | PSICOLOGIA OSCURA [IT]
Daniela Coelho | @psidanicoelho | 🖤 100% NERO | Cuffie | Sonno • Studio • Meditazione

🔴 LIVE | ZWART SCHERM | BINAURAL 432Hz | DONKERE PSYCHOLOGIE [NL]
Daniela Coelho | @psidanicoelho | 🖤 100% ZWART | Koptelefoon | Slaap • Studie • Meditatie

🔴 NA ŻYWO | CZARNY EKRAN | BINAURAL 432Hz | CIEMNA PSYCHOLOGIA [PL]
Daniela Coelho | @psidanicoelho | 🖤 100% CZARNY | Słuchawki | Sen • Nauka • Medytacja

🔴 CANLI | SİYAH EKRAN | BINAURAL 432Hz | KARANLIK PSİKOLOJİ [TR]
Daniela Coelho | @psidanicoelho | 🖤 100% SİYAH | Kulaklık | Uyku • Çalışma • Meditasyon

🔴 LIVE | LAYAR HITAM | BINAURAL 432Hz | PSIKOLOGI GELAP [ID]
Daniela Coelho | @psidanicoelho | 🖤 100% HITAM | Headphone | Tidur • Belajar • Meditasi

🔴 लाइव | काली स्क्रीन | बाइनॉरल 432Hz | डार्क साइकोलॉजी [HI]
डेनियला कोएल्हो | @psidanicoelho | 🖤 100% काली | हेडफोन | नींद • अध्ययन • ध्यान

🔴 مباشر | شاشة سوداء | نغمات ثنائية 432Hz | علم النفس المظلم [AR]
دانييلا كويلو | @psidanicoelho | 🖤 سوداء 100٪ | سماعات | النوم • الدراسة • التأمل

Research: Harvard • UCLA • van der Kolk • Ainsworth • Gottman • Beck
💬 Super Chat: psychology LIVE! 🔔 SUBSCRIBE + BELL!

#blackscreen #blackscreenforsleep #blackscreen8hours #blackscreen10hours
#binauralbeats432hz #432hz #432hzmusic #sleepmusic #studymusic #focusmusic
#darkpsychology #narcissism #trauma #anxiety #danielacoelho #psidanicoelho
#schwarzerbildschirm #pantallanegraparadormir #telapreta #검은화면 #黑屏幕"""

def ffm():
    try:
        import imageio_ffmpeg; f=imageio_ffmpeg.get_ffmpeg_exe(); log(f"FFmpeg: {f}"); return f
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
    for status in ["active","complete","created","ready","testStarting","testing","live"]:
        url=f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status&broadcastStatus={status}&mine=true&maxResults=50"
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
