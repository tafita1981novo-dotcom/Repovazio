#!/usr/bin/env python3
"""DIAGNÓSTICO: testar conexão RTMP + criar live corretamente"""
import os, json, urllib.request, urllib.parse, subprocess, math, struct, wave, time
import pathlib, shutil
from datetime import datetime, timezone, timedelta

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
DURATION_H       = int(os.environ.get("DURATION_H","6"))

ST_KEY = "ewme-91sq-yae7-yj1q-5skw"
STREAM_ID = "SH63tBfY6wEIdkC4u4zKdg1780543868590330"
RTMP = f"rtmp://a.rtmp.youtube.com/live2/{ST_KEY}"
TMP = pathlib.Path("/tmp")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)

def get_token():
    data = urllib.parse.urlencode({
        "client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())["access_token"]

def yt_get(token, url):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=15) as r: return json.loads(r.read())

def yt_post(token, url, body=None, method="POST"):
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as r:
        txt = r.read(); return json.loads(txt) if txt else {}

def yt_delete(token, url):
    req = urllib.request.Request(url, method="DELETE")
    req.add_header("Authorization", f"Bearer {token}")
    try: urllib.request.urlopen(req, timeout=10); return True
    except: return False

def ffm():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    return shutil.which("ffmpeg") or "ffmpeg"

def gerar_wav():
    SR, DUR = 44100, 5; s = SR*DUR; out = bytearray()
    for i in range(s):
        t = i/SR
        out += struct.pack('<hh',
            int(math.sin(2*math.pi*430*t)*22000),
            int(math.sin(2*math.pi*432*t)*22000))
    p = TMP/"b432.wav"
    with wave.open(str(p),'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2)
        wf.setframerate(SR); wf.writeframes(bytes(out))
    return str(p)

DESC_15 = """🔴 LIVE 24/7 | BLACK SCREEN | BINAURAL BEATS 432Hz | DARK PSYCHOLOGY
Daniela Coelho — Human Behavior Researcher | @psidanicoelho
🖤 PURE BLACK SCREEN — 100% dark, zero pixels illuminated
🎵 TRUE BINAURAL 432Hz (430Hz Left + 432Hz Right = 2Hz DELTA beat)
🧠 DARK PSYCHOLOGY — Narcissism, Trauma, Anxiety, Attachment Theory
★ Use HEADPHONES for true binaural effect | Perfect: Sleep • Study • Meditation

🔴 LIVE | SCHWARZER BILDSCHIRM | BINAURAL 432Hz | PSYCHOLOGIE [DE]
Daniela Coelho | @psidanicoelho | 🖤 100% SCHWARZ | Kopfhörer empfohlen

🔴 EN DIRECT | ÉCRAN NOIR | BINAURAL 432Hz | PSYCHOLOGIE SOMBRE [FR]
Daniela Coelho | @psidanicoelho | 🖤 100% NOIR | Casque recommandé

🔴 EN VIVO | PANTALLA NEGRA | BINAURAL 432Hz | PSICOLOGÍA OSCURA [ES]
Daniela Coelho | @psidanicoelho | 🖤 100% NEGRA | Auriculares recomendados

🔴 AO VIVO | TELA PRETA | BINAURAL 432Hz | DARK PSYCHOLOGY [PT]
Daniela Coelho | @psidanicoelho | 🖤 100% PRETA | Fones de ouvido

🔴 ライブ | ブラックスクリーン | バイノーラル432Hz | ダーク心理学 [JA]
ダニエラ・コエーリョ | @psidanicoelho | 🖤 完全ブラック | ヘッドフォン推奨

🔴 라이브 | 검은 화면 | 바이노럴 432Hz | 다크 심리학 [KO]
다니엘라 코에요 | @psidanicoelho | 🖤 100% 검은 화면 | 헤드폰 권장

🔴 直播 | 纯黑屏幕 | 双耳节拍432Hz | 暗黑心理学 [ZH]
达尼埃拉 | @psidanicoelho | 🖤 纯黑100% | 耳机建议使用

🔴 LIVE | SCHERMO NERO | BINAURAL 432Hz | PSICOLOGIA OSCURA [IT]
Daniela Coelho | @psidanicoelho | 🖤 100% NERO | Cuffie consigliate

🔴 LIVE | ZWART SCHERM | BINAURAL 432Hz | DONKERE PSYCHOLOGIE [NL]
Daniela Coelho | @psidanicoelho | 🖤 100% ZWART | Koptelefoon aanbevolen

🔴 NA ŻYWO | CZARNY EKRAN | BINAURAL 432Hz | CIEMNA PSYCHOLOGIA [PL]
Daniela Coelho | @psidanicoelho | 🖤 100% CZARNY | Słuchawki zalecane

🔴 CANLI | SİYAH EKRAN | BINAURAL 432Hz | KARANLIK PSİKOLOJİ [TR]
Daniela Coelho | @psidanicoelho | 🖤 100% SİYAH | Kulaklık önerilir

🔴 LIVE | LAYAR HITAM | BINAURAL 432Hz | PSIKOLOGI GELAP [ID]
Daniela Coelho | @psidanicoelho | 🖤 100% HITAM | Headphone disarankan

🔴 लाइव | काली स्क्रीन | बाइनॉरल 432Hz | डार्क साइकोलॉजी [HI]
डेनियला कोएल्हो | @psidanicoelho | 🖤 100% काली | हेडफोन अनुशंसित

🔴 مباشر | شاشة سوداء | نغمات ثنائية 432Hz | علم النفس المظلم [AR]
دانييلا كويلو | @psidanicoelho | 🖤 سوداء 100٪ | سماعات مطلوبة

Research: Harvard • UCLA • van der Kolk • Ainsworth • Gottman
#blackscreen #binauralbeats432hz #432hz #sleepmusic #darkpsychology #danielacoelho"""

TITULO = "🔴 LIVE 24/7 | BLACK SCREEN for Sleep & Focus | Binaural Beats 432Hz | Dark Psychology"

def main():
    log("="*65)
    log(f"LIVE UNIFICADA FINAL | {datetime.now(timezone.utc):%H:%M} UTC")
    log("="*65)
    
    ff = ffm()
    log(f"FFmpeg: {ff}")
    
    # Teste rápido de conectividade RTMP (5 segundos)
    log("\n--- TESTE RTMP (5s) ---")
    wav = gerar_wav()
    test_cmd = [ff, "-y", "-re",
                "-stream_loop", "-1", "-i", wav,
                "-f", "lavfi", "-i", "color=black:size=1280x720:rate=25",
                "-map", "1:v", "-map", "0:a",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "36",
                "-b:v", "150k", "-c:a", "aac", "-b:a", "128k",
                "-f", "flv", "-t", "5", RTMP]
    
    import subprocess
    result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
    log(f"RTMP test rc={result.returncode}")
    if result.returncode != 0:
        log("RTMP STDERR (últimas 10 linhas):")
        for l in result.stderr.split("\n")[-10:]: 
            if l.strip(): log(f"  {l}")
    else:
        log("RTMP test OK! Conexão funciona.")
    
    # OAuth
    token = get_token()
    log(f"\nToken OAuth OK")
    
    # Listar broadcasts existentes
    data = yt_get(token, "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status&broadcastStatus=all&mine=true&maxResults=50")
    items = data.get("items", [])
    log(f"Broadcasts existentes: {len(items)}")
    for item in items:
        log(f"  {item['id']}: [{item.get('status',{}).get('lifeCycleStatus')}] {item.get('snippet',{}).get('title','')[:50]}")
    
    # Apagar todos
    log("\nApagando broadcasts...")
    for item in items:
        bid = item["id"]
        lifecycle = item.get("status",{}).get("lifeCycleStatus","")
        if lifecycle in ["active","testing","testStarting","live"]:
            try: yt_post(token, f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bid}&part=id", {})
            except: pass
            time.sleep(1)
        ok = yt_delete(token, f"https://www.googleapis.com/youtube/v3/liveBroadcasts?id={bid}")
        log(f"  {'OK' if ok else 'SKIP'}: {item.get('snippet',{}).get('title','')[:40]}")
        time.sleep(0.3)
    
    time.sleep(2)
    
    # Criar broadcast
    log("\nCriando broadcast unificado...")
    start = (datetime.now(timezone.utc)+timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "snippet": {
            "title": TITULO,
            "description": DESC_15[:4900],
            "scheduledStartTime": start,
            "categoryId": "22",
            "defaultLanguage": "en"
        },
        "status": {"privacyStatus":"public","selfDeclaredMadeForKids":False},
        "contentDetails": {
            "enableAutoStart":True,"enableAutoStop":False,
            "enableDvr":True,"enableEmbed":True,"recordFromStart":True,
            "startWithSlate":False,"monitorStream":{"enableMonitorStream":False}
        }
    }
    res = yt_post(token, "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails", body)
    bc_id = res.get("id")
    log(f"Broadcast criado: {bc_id}")
    
    if not bc_id:
        log(f"ERRO: {res}"); return
    
    # Bind
    time.sleep(2)
    bind_url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id,contentDetails&streamId={STREAM_ID}"
    bind_res = yt_post(token, bind_url, {})
    log(f"Bind: {bind_res.get('id','ERRO')} | {bind_res.get('error','OK')}")
    
    # Confirmar estado do broadcast
    time.sleep(2)
    bc_data = yt_get(token, f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails&id={bc_id}")
    for item in bc_data.get("items",[]):
        log(f"Broadcast final:")
        log(f"  ID: {item['id']}")
        log(f"  Status: {item.get('status',{}).get('lifeCycleStatus')}")
        log(f"  AutoStart: {item.get('contentDetails',{}).get('enableAutoStart')}")
        log(f"  Título: {item.get('snippet',{}).get('title','')[:60]}")
        bd = item.get("contentDetails",{}).get("boundStreamId","")
        log(f"  BoundStream: {bd}")
    
    log(f"\n✅ PRONTO: https://studio.youtube.com/video/{bc_id}/livestreaming")
    log(f"\nIniciando stream...")
    
    # Stream em loop
    dur_s = DURATION_H * 3600
    inicio = time.time()
    tentativas = 0
    while time.time()-inicio < dur_s and tentativas < 50:
        restante = int(dur_s-(time.time()-inicio))
        if restante < 15: break
        tentativas += 1
        log(f"[{tentativas}] Streaming {restante//3600}h{restante%3600//60}m")
        
        cmd = [ff,"-y","-re",
               "-stream_loop","-1","-i",wav,
               "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
               "-map","1:v","-map","0:a",
               "-c:v","libx264","-preset","ultrafast","-crf","36",
               "-b:v","150k","-maxrate","200k","-bufsize","400k",
               "-g","50","-r","25","-pix_fmt","yuv420p",
               "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
               "-f","flv","-t",str(restante), RTMP]
        
        result2 = subprocess.run(cmd, capture_output=True, text=True, timeout=restante+900)
        rc = result2.returncode
        log(f"  rc={rc}")
        if rc != 0:
            log("  STDERR (últimas 5 linhas):")
            for l in result2.stderr.split("\n")[-5:]:
                if l.strip(): log(f"    {l}")
        if rc == 0: break
        espera = min(20*tentativas, 120)
        log(f"  retry em {espera}s"); time.sleep(espera)

if __name__=="__main__": main()
