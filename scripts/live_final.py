#!/usr/bin/env python3
"""
live_final.py — VERSÃO DEFINITIVA CORRIGIDA
Problemas resolvidos:
1. NÃO usa capture_output (fix SIGSEGV ffmpeg7 com pipes)
2. Inicia stream em thread e aguarda conexão antes de transitar broadcast
3. Apaga todas as lives, cria uma unificada, bind correto, stream loop
"""
import os, json, urllib.request, urllib.parse, time, math, struct, wave
import subprocess, pathlib, shutil, threading
from datetime import datetime, timezone, timedelta

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
DURATION_H       = int(os.environ.get("DURATION_H", "6"))

ST_KEY     = "ewme-91sq-yae7-yj1q-5skw"
STREAM_ID  = "SH63tBfY6wEIdkC4u4zKdg1780543868590330"
RTMP       = f"rtmp://a.rtmp.youtube.com/live2/{ST_KEY}"
TMP        = pathlib.Path("/tmp")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERR {m}", flush=True)

# ─── AUTH ─────────────────────────────────────────────────────────
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
    try:
        with urllib.request.urlopen(req, timeout=15) as r: return json.loads(r.read())
    except Exception as e: err(f"GET {url[-50:]}: {e}"); return {}

def yt_post(token, url, body=None, method="POST"):
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            txt = r.read(); return json.loads(txt) if txt else {}
    except Exception as e: err(f"POST {url[-50:]}: {e}"); return {"error": str(e)}

def yt_delete(token, url):
    req = urllib.request.Request(url, method="DELETE")
    req.add_header("Authorization", f"Bearer {token}")
    try: urllib.request.urlopen(req, timeout=10); return True
    except: return False

# ─── DESCRIÇÃO 15 IDIOMAS ─────────────────────────────────────────
TITULO = "🔴 LIVE 24/7 | BLACK SCREEN for Sleep & Focus | Binaural Beats 432Hz | Dark Psychology"

DESC = """🔴 LIVE 24/7 | BLACK SCREEN | BINAURAL BEATS 432Hz | DARK PSYCHOLOGY
Daniela Coelho — Human Behavior Researcher | @psidanicoelho
🖤 PURE BLACK SCREEN — 100% dark, zero pixels illuminated
🎵 TRUE BINAURAL 432Hz (430Hz Left + 432Hz Right = 2Hz DELTA beat)
🧠 DARK PSYCHOLOGY — Narcissism, Trauma, Anxiety, Attachment Theory
★ Use HEADPHONES for true binaural effect
★ Perfect: Deep Sleep • Study • Meditation • Work • Focus
★ NO logos, NO watermarks, NO brightness — pure black

🔴 LIVE | SCHWARZER BILDSCHIRM | BINAURAL 432Hz | PSYCHOLOGIE [DE]
Daniela Coelho — Verhaltensforscherin | @psidanicoelho
🖤 100% SCHWARZ | ECHTER BINAURAL 432Hz | Kopfhörer empfohlen
Ideal: Schlafen • Lernen • Meditieren • Fokus

🔴 EN DIRECT | ÉCRAN NOIR | BINAURAL 432Hz | PSYCHOLOGIE SOMBRE [FR]
Daniela Coelho — Chercheuse en Comportement | @psidanicoelho
🖤 100% NOIR | VRAI BINAURAL 432Hz | Casque recommandé
Idéal: Sommeil • Étude • Méditation • Concentration

🔴 EN VIVO | PANTALLA NEGRA | BINAURAL 432Hz | PSICOLOGÍA OSCURA [ES]
Daniela Coelho — Investigadora del Comportamiento | @psidanicoelho
🖤 100% NEGRA | BINAURAL REAL 432Hz | Auriculares recomendados
Ideal: Sueño • Estudio • Meditación • Enfoque

🔴 AO VIVO | TELA PRETA | BINAURAL 432Hz | DARK PSYCHOLOGY [PT]
Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho
🖤 100% PRETA | BINAURAL REAL 432Hz | Fones de ouvido
Ideal: Sono • Estudo • Meditação • Foco

🔴 24時間ライブ | ブラックスクリーン | バイノーラル432Hz | ダーク心理学 [JA]
ダニエラ・コエーリョ — 人間行動研究者 | @psidanicoelho
🖤 完全ブラック | 本物のバイノーラル432Hz | ヘッドフォン推奨
最適: 睡眠・勉強・瞑想・集中

🔴 24시간 라이브 | 검은 화면 | 바이노럴 432Hz | 다크 심리학 [KO]
다니엘라 코에요 — 인간 행동 연구자 | @psidanicoelho
🖤 100% 검은 | 진짜 바이노럴 432Hz | 헤드폰 권장
최적: 수면 • 공부 • 명상 • 집중

🔴 24小时直播 | 纯黑屏幕 | 双耳节拍432Hz | 暗黑心理学 [ZH]
达尼埃拉·科埃略 — 人类行为研究者 | @psidanicoelho
🖤 纯黑100% | 真实双耳节拍432Hz | 建议使用耳机
最适合: 睡眠 • 学习 • 冥想 • 专注

🔴 LIVE | SCHERMO NERO | BINAURAL 432Hz | PSICOLOGIA OSCURA [IT]
Daniela Coelho — Ricercatrice Comportamento | @psidanicoelho
🖤 100% NERO | BINAURAL VERO 432Hz | Cuffie consigliate
Ideale: Sonno • Studio • Meditazione • Concentrazione

🔴 LIVE | ZWART SCHERM | BINAURAL 432Hz | DONKERE PSYCHOLOGIE [NL]
Daniela Coelho — Gedragsonderzoeker | @psidanicoelho
🖤 100% ZWART | ECHTE BINAURAL 432Hz | Koptelefoon aanbevolen
Ideaal: Slaap • Studie • Meditatie • Focus

🔴 NA ŻYWO | CZARNY EKRAN | BINAURAL 432Hz | CIEMNA PSYCHOLOGIA [PL]
Daniela Coelho — Badaczka Zachowań | @psidanicoelho
🖤 100% CZARNY | PRAWDZIWY BINAURAL 432Hz | Słuchawki zalecane
Idealne: Sen • Nauka • Medytacja • Skupienie

🔴 CANLI | SİYAH EKRAN | BINAURAL 432Hz | KARANLIK PSİKOLOJİ [TR]
Daniela Coelho — Davranış Araştırmacısı | @psidanicoelho
🖤 100% SİYAH | GERÇEK BİNAURAL 432Hz | Kulaklık önerilir
İdeal: Uyku • Çalışma • Meditasyon • Odaklanma

🔴 LIVE | LAYAR HITAM | BINAURAL 432Hz | PSIKOLOGI GELAP [ID]
Daniela Coelho — Peneliti Perilaku | @psidanicoelho
🖤 100% HITAM | BINAURAL ASLI 432Hz | Headphone disarankan
Ideal: Tidur • Belajar • Meditasi • Fokus

🔴 लाइव | काली स्क्रीन | बाइनॉरल 432Hz | डार्क साइकोलॉजी [HI]
डेनियला कोएल्हो — शोधकर्ता | @psidanicoelho
🖤 100% काली | असली बाइनॉरल 432Hz | हेडफोन अनुशंसित
आदर्श: नींद • अध्ययन • ध्यान • एकाग्रता

🔴 مباشر | شاشة سوداء | نغمات ثنائية 432Hz | علم النفس المظلم [AR]
دانييلا كويلو — باحثة | @psidanicoelho
🖤 سوداء 100٪ | ثنائي حقيقي 432Hz | سماعات مطلوبة
مثالي: النوم • الدراسة • التأمل • التركيز

Research: Harvard • UCLA • van der Kolk • Ainsworth • Gottman • Beck
💬 Super Chat: ask psychology questions LIVE! | 🔔 SUBSCRIBE + BELL!

#blackscreen #blackscreenforsleep #blackscreen8hours #blackscreen10hours
#binauralbeats432hz #432hz #sleepmusic #studymusic #focusmusic #meditationmusic
#darkpsychology #narcissism #trauma #anxiety #danielacoelho #psidanicoelho
#schwarzerbildschirm #pantallanegraparadormir #telapreta #검은화면 #黑屏幕"""

# ─── FFMPEG ───────────────────────────────────────────────────────
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
    with wave.open(str(p), 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2)
        wf.setframerate(SR); wf.writeframes(bytes(out))
    log(f"WAV binaural 432Hz: {p.stat().st_size//1024}KB ✅")
    return str(p)

# ─── YOUTUBE OPERATIONS ───────────────────────────────────────────
def delete_all(token):
    log("─── APAGANDO todas as lives ───")
    total = 0
    for status in ["active","complete","created","ready","testStarting","testing","live","all"]:
        url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status&broadcastStatus={status}&mine=true&maxResults=50"
        data = yt_get(token, url)
        for item in data.get("items", []):
            bid = item["id"]
            title = item.get("snippet",{}).get("title","?")[:40]
            lifecycle = item.get("status",{}).get("lifeCycleStatus","")
            # Tentar encerrar se ativa
            if lifecycle in ["active","testing","testStarting","live"]:
                yt_post(token, f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bid}&part=id", {})
                time.sleep(1)
            ok = yt_delete(token, f"https://www.googleapis.com/youtube/v3/liveBroadcasts?id={bid}")
            log(f"  {'✅' if ok else '⚠'} {title} [{bid}]")
            if ok: total += 1
            time.sleep(0.3)
    log(f"  Total removidas: {total}")

def criar_broadcast(token):
    log("─── CRIANDO live unificada ───")
    start = (datetime.now(timezone.utc)+timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "snippet": {
            "title": TITULO,
            "description": DESC[:4900],
            "scheduledStartTime": start,
            "categoryId": "22",
            "defaultLanguage": "en"
        },
        "status": {"privacyStatus":"public","selfDeclaredMadeForKids":False},
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
    res = yt_post(token, "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails", body)
    bc_id = res.get("id")
    if bc_id:
        log(f"  ✅ Criado: {bc_id}")
    else:
        err(f"  Falha: {res}")
    return bc_id

def bind(token, bc_id):
    log(f"─── BIND {bc_id} → stream ───")
    url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id,contentDetails&streamId={STREAM_ID}"
    res = yt_post(token, url, {})
    bound = res.get("contentDetails",{}).get("boundStreamId","")
    if bound:
        log(f"  ✅ Bound: {bound[:30]}")
    else:
        log(f"  Bind res: {str(res)[:100]}")
    return res

def transitar(token, bc_id, status_target):
    url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus={status_target}&id={bc_id}&part=id,status"
    res = yt_post(token, url, {})
    new_status = res.get("status",{}).get("lifeCycleStatus","")
    log(f"  Transição → {status_target}: {new_status or str(res)[:80]}")
    return res

# ─── STREAM ───────────────────────────────────────────────────────
# Variável global para sinalizar que ffmpeg conectou
ffmpeg_connected = threading.Event()
bc_id_global = None

def stream_loop(wav, ff, dur_s):
    """Loop de stream — NÃO usa capture_output (fix SIGSEGV)"""
    inicio = time.time()
    tentativas = 0
    while time.time()-inicio < dur_s and tentativas < 50:
        restante = int(dur_s-(time.time()-inicio))
        if restante < 15: break
        tentativas += 1
        log(f"[{tentativas}] 🔴 Streaming {restante//3600}h{restante%3600//60}m → RTMP")
        
        cmd = [ff, "-y", "-re",
               "-stream_loop", "-1", "-i", wav,
               "-f", "lavfi", "-i", "color=black:size=1920x1080:rate=25",
               "-map", "1:v", "-map", "0:a",
               "-c:v", "libx264", "-preset", "ultrafast", "-crf", "36",
               "-b:v", "150k", "-maxrate", "200k", "-bufsize", "400k",
               "-g", "50", "-r", "25", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "44100",
               "-f", "flv", "-t", str(restante), RTMP]
        
        # SEM capture_output — saída vai direto para logs do GitHub Actions
        proc = subprocess.Popen(cmd)
        
        # Sinalizar que ffmpeg começou (em 5s assume conectado)
        time.sleep(5)
        ffmpeg_connected.set()
        
        rc = proc.wait(timeout=restante+900)
        log(f"  ffmpeg rc={rc}")
        
        if rc == 0: break
        espera = min(20*tentativas, 120)
        log(f"  retry em {espera}s"); time.sleep(espera)

def main():
    log("="*65)
    log(f"LIVE FINAL | 15 IDIOMAS | {datetime.now(timezone.utc):%H:%M} UTC | {DURATION_H}h")
    log("="*65)
    
    ff = ffm()
    log(f"FFmpeg: {ff}")
    wav = gerar_wav()
    
    token = get_token()
    log(f"Token OAuth ✅")
    
    # 1. Apagar tudo
    delete_all(token)
    time.sleep(3)
    
    # 2. Criar broadcast
    bc_id = criar_broadcast(token)
    if not bc_id: return
    time.sleep(2)
    
    # 3. Bind
    bind(token, bc_id)
    time.sleep(2)
    
    log(f"\n✅ LIVE UNIFICADA: https://studio.youtube.com/video/{bc_id}/livestreaming")
    log(f"   Watch: https://www.youtube.com/watch?v={bc_id}\n")
    
    # 4. Iniciar stream em thread separada
    dur_s = DURATION_H * 3600
    t = threading.Thread(target=stream_loop, args=(wav, ff, dur_s), daemon=True)
    t.start()
    
    # 5. Aguardar ffmpeg conectar e então transitar para "live"
    log("Aguardando ffmpeg conectar (30s)...")
    ffmpeg_connected.wait(timeout=30)
    time.sleep(25)  # dar tempo para YouTube receber os primeiros pacotes
    
    # Tentar transitar para testing e depois live
    token2 = get_token()  # token fresco
    res_t = transitar(token2, bc_id, "testing")
    time.sleep(5)
    res_l = transitar(token2, bc_id, "live")
    
    log(f"\n🔴 LIVE ATIVA: https://www.youtube.com/watch?v={bc_id}")
    
    # 6. Aguardar stream terminar
    t.join(timeout=dur_s+900)
    log(f"\nFinalizado.")

if __name__ == "__main__":
    main()
