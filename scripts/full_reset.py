#!/usr/bin/env python3
"""
full_reset.py — Cria broadcast limpo, bind, SEO 15 idiomas, inicia stream
"""
import os, json, urllib.request, urllib.parse, time, math, struct, wave, subprocess, pathlib, shutil
from datetime import datetime, timezone, timedelta

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
DURATION_H       = int(os.environ.get("DURATION_H","6"))
ST_KEY_VAL       = "ewme-91sq-yae7-yj1q-5skw"
RTMP             = f"rtmp://a.rtmp.youtube.com/live2/{ST_KEY_VAL}"
TMP              = pathlib.Path("/tmp")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERR: {m}", flush=True)

def get_token():
    data=urllib.parse.urlencode({"client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
        "refresh_token":YT_REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    req=urllib.request.Request("https://oauth2.googleapis.com/token",data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req,timeout=15) as r:
        return json.loads(r.read())["access_token"]

def yt_get(token, url):
    req=urllib.request.Request(url)
    req.add_header("Authorization",f"Bearer {token}")
    try:
        with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read())
    except Exception as e: return {"error":str(e)}

def yt_call(token, url, body=None, method="POST"):
    data=json.dumps(body).encode() if body else b"{}"
    req=urllib.request.Request(url,data=data,method=method)
    req.add_header("Authorization",f"Bearer {token}")
    req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            txt=r.read(); return json.loads(txt) if txt else {}
    except Exception as e: return {"error":str(e)}

DESC_15 = """🔴 LIVE 24/7 | BLACK SCREEN | BINAURAL BEATS 432Hz | DARK PSYCHOLOGY
Daniela Coelho — Human Behavior Researcher | @psidanicoelho
🖤 PURE BLACK SCREEN | TRUE BINAURAL 432Hz (430Hz L + 432Hz R = 2Hz DELTA) | Use HEADPHONES
Perfect for: Deep Sleep • Study • Meditation • Work • Focus

🔴 LIVE 24H | SCHWARZER BILDSCHIRM | BINAURAL 432Hz | PSYCHOLOGIE [DE]
Daniela Coelho | @psidanicoelho | 🖤 100% SCHWARZ | Kopfhörer | Schlaf • Lernen • Meditation

🔴 EN DIRECT 24H | ÉCRAN NOIR | BINAURAL 432Hz | PSYCHOLOGIE SOMBRE [FR]
Daniela Coelho | @psidanicoelho | 🖤 ÉCRAN 100% NOIR | Casque | Sommeil • Étude • Méditation

🔴 EN VIVO 24H | PANTALLA NEGRA | BINAURAL 432Hz | PSICOLOGÍA OSCURA [ES]
Daniela Coelho | @psidanicoelho | 🖤 100% NEGRA | Auriculares | Sueño • Estudio • Meditación

🔴 AO VIVO 24H | TELA PRETA | BINAURAL 432Hz | DARK PSYCHOLOGY [PT]
Daniela Coelho | @psidanicoelho | 🖤 100% PRETA | Fones | Sono • Estudo • Meditação

🔴 24時間ライブ | ブラックスクリーン | バイノーラル432Hz | ダーク心理学 [JA]
ダニエラ・コエーリョ | @psidanicoelho | 🖤 完全ブラック | ヘッドフォン | 睡眠・勉強・瞑想

🔴 24시간 라이브 | 검은 화면 | 바이노럴 432Hz | 다크 심리학 [KO]
다니엘라 코에요 | @psidanicoelho | 🖤 100% 검은 | 헤드폰 | 수면 • 공부 • 명상

🔴 24小时直播 | 纯黑屏幕 | 双耳节拍432Hz | 暗黑心理学 [ZH]
达尼埃拉·科埃略 | @psidanicoelho | 🖤 纯黑100% | 耳机 | 睡眠 • 学习 • 冥想

🔴 LIVE 24H | SCHERMO NERO | BINAURAL 432Hz | PSICOLOGIA OSCURA [IT]
Daniela Coelho | @psidanicoelho | 🖤 100% NERO | Cuffie | Sonno • Studio • Meditazione

🔴 LIVE 24/7 | ZWART SCHERM | BINAURAL 432Hz | DONKERE PSYCHOLOGIE [NL]
Daniela Coelho | @psidanicoelho | 🖤 100% ZWART | Koptelefoon | Slaap • Studie • Meditatie

🔴 NA ŻYWO 24H | CZARNY EKRAN | BINAURAL 432Hz | CIEMNA PSYCHOLOGIA [PL]
Daniela Coelho | @psidanicoelho | 🖤 100% CZARNY | Słuchawki | Sen • Nauka • Medytacja

🔴 CANLI 24S | SİYAH EKRAN | BINAURAL 432Hz | KARANLIK PSİKOLOJİ [TR]
Daniela Coelho | @psidanicoelho | 🖤 %100 SİYAH | Kulaklık | Uyku • Çalışma • Meditasyon

🔴 LIVE 24 JAM | LAYAR HITAM | BINAURAL 432Hz | PSIKOLOGI GELAP [ID]
Daniela Coelho | @psidanicoelho | 🖤 100% HITAM | Headphone | Tidur • Belajar • Meditasi

🔴 24 घंटे लाइव | काली स्क्रीन | बाइनॉरल 432Hz | डार्क साइकोलॉजी [HI]
डेनियला कोएल्हो | @psidanicoelho | 🖤 100% काली | हेडफोन | नींद • अध्ययन • ध्यान

🔴 بث مباشر 24 ساعة | شاشة سوداء | نغمات ثنائية 432Hz | علم النفس المظلم [AR]
دانييلا كويلو | @psidanicoelho | 🖤 سوداء 100٪ | سماعات | النوم • الدراسة • التأمل

Research: Harvard • UCLA • van der Kolk • Ainsworth • Gottman
#blackscreen #blackscreenforsleep #binauralbeats432hz #432hz #sleepmusic
#darkpsychology #narcissism #danielacoelho #psidanicoelho
#schwarzerbildschirm #pantallanegraparadormir #telapreta #검은화면 #黑屏幕"""

TITULO = "🔴 LIVE 24/7 | BLACK SCREEN for Sleep | Binaural Beats 432Hz | Dark Psychology | @psidanicoelho"

def get_stream_id(token):
    """Pegar ID do stream resource para ewme-91sq-yae7-yj1q-5skw"""
    data = yt_get(token, "https://www.googleapis.com/youtube/v3/liveStreams?part=id,snippet,cdn&mine=true&maxResults=50")
    for item in data.get("items", []):
        key = item.get("cdn",{}).get("ingestionInfo",{}).get("streamName","")
        if key == ST_KEY_VAL:
            log(f"Stream ID: {item['id']} ({item.get('snippet',{}).get('title','')})")
            return item["id"]
    return None

def criar_broadcast_correto(token):
    """Cria broadcast com scheduledStartTime 5min no futuro"""
    start = (datetime.now(timezone.utc)+timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "snippet": {
            "title": TITULO[:100],
            "description": DESC_15[:4900],
            "scheduledStartTime": start,
            "categoryId": "22",
            "defaultLanguage": "en"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        },
        "contentDetails": {
            "enableAutoStart": True,
            "enableAutoStop": False,
            "enableDvr": True,
            "enableEmbed": True,
            "recordFromStart": True,
            "startWithSlate": False,
            "monitorStream": {"enableMonitorStream": False}
        }
    }
    res = yt_call(token, "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails", body)
    if "id" in res:
        log(f"Broadcast criado: {res['id']}")
        return res["id"]
    else:
        err(f"Criar falhou: {res}")
        return None

def bind_broadcast(token, bc_id, stream_id):
    url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id,contentDetails&streamId={stream_id}"
    res = yt_call(token, url)
    if "error" in str(res.get("error",""))[:5]:
        err(f"Bind erro: {res}")
    else:
        log(f"Bind OK: {bc_id} → {stream_id}")
    return res

def gerar_wav():
    SR,DUR=44100,5; s=SR*DUR; out=bytearray()
    for i in range(s):
        t=i/SR
        out+=struct.pack('<hh',int(math.sin(2*math.pi*430*t)*22000),int(math.sin(2*math.pi*432*t)*22000))
    p=TMP/"b432.wav"
    with wave.open(str(p),'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(bytes(out))
    log(f"WAV binaural: {p.stat().st_size//1024}KB"); return str(p)

def ffm():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    for p in [shutil.which("ffmpeg"),"/usr/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists(): return p
    return "ffmpeg"

def transmitir(wav, ff, dur_s):
    log(f"Stream iniciando: {dur_s//3600}h → {RTMP[:40]}...")
    cmd=[ff,"-y","-re","-stream_loop","-1","-i",wav,
         "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
         "-map","1:v","-map","0:a",
         "-c:v","libx264","-preset","ultrafast","-crf","36",
         "-b:v","150k","-maxrate","200k","-bufsize","400k",
         "-g","50","-r","25","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
         "-f","flv","-t",str(dur_s), RTMP]
    return subprocess.run(cmd, timeout=dur_s+900).returncode

def main():
    log("="*60)
    log(f"FULL RESET | 15 IDIOMAS | {datetime.now(timezone.utc):%H:%M} UTC")
    log("="*60)
    ff = ffm()
    wav = gerar_wav()
    token = get_token()
    log(f"Token OK")
    
    # 1. Pegar stream ID
    stream_id = get_stream_id(token)
    if not stream_id:
        err("Stream não encontrado! Usando key direta."); return
    
    # 2. Deletar TODAS as broadcasts existentes
    log("Deletando broadcasts existentes...")
    deleted = 0
    for status in ["active","complete","created","ready","testStarting","testing","live"]:
        url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status&broadcastStatus={status}&maxResults=50"
        data = yt_get(token, url)
        for item in data.get("items", []):
            bc_id = item["id"]
            title = item.get("snippet",{}).get("title","?")[:40]
            lifecycle = item.get("status",{}).get("lifeCycleStatus","")
            if lifecycle in ["active","testing","testStarting"]:
                yt_call(token, f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bc_id}&part=id", {})
                time.sleep(2)
            req = urllib.request.Request(f"https://www.googleapis.com/youtube/v3/liveBroadcasts?id={bc_id}", method="DELETE")
            req.add_header("Authorization", f"Bearer {token}")
            try:
                urllib.request.urlopen(req, timeout=10)
                log(f"  Deleted: {title}")
                deleted += 1
            except Exception as e:
                err(f"  Skip {bc_id}: {e}")
            time.sleep(0.3)
    log(f"  Total: {deleted} deletadas")
    time.sleep(2)
    
    # 3. Criar novo broadcast
    bc_id = criar_broadcast_correto(token)
    if not bc_id:
        err("Falha criar broadcast"); return
    time.sleep(2)
    
    # 4. Bind
    bind_broadcast(token, bc_id, stream_id)
    time.sleep(2)
    
    # 5. Guardar BC_ID para uso futuro
    log(f"NOVO BC_ID: {bc_id}")
    log(f"Stream ID: {stream_id}")
    
    # 6. Stream
    dur_s = DURATION_H * 3600
    inicio = time.time()
    tentativas = 0
    while time.time()-inicio < dur_s and tentativas < 30:
        restante = int(dur_s - (time.time()-inicio))
        if restante < 15: break
        tentativas += 1
        log(f"[{tentativas}] Streaming {restante//3600}h{restante%3600//60}m")
        rc = transmitir(wav, ff, restante)
        if rc == 0: break
        espera = min(20*tentativas, 120)
        log(f"retry em {espera}s"); time.sleep(espera)
    
    log(f"TOTAL: {(time.time()-inicio)//60:.0f}min")

if __name__ == "__main__":
    main()
