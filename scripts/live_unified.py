#!/usr/bin/env python3
"""
live_unified.py — UMA LIVE, PARA SEMPRE, 15 IDIOMAS
- Apaga TODAS as lives do canal
- Cria UMA única live unificada
- Título em inglês (SEO global), descrição nos 15 idiomas
- Tela preta + binaural 432Hz
- Roda para sempre (loop de 6h, cron reinicia)
"""
import os, json, urllib.request, urllib.parse, time, math, struct, wave
import subprocess, pathlib, shutil
from datetime import datetime, timezone, timedelta

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
DURATION_H       = int(os.environ.get("DURATION_H", "6"))

# Stream key fixo que já funcionou 6h
ST_KEY_VAL = "ewme-91sq-yae7-yj1q-5skw"
# Stream resource ID descoberto anteriormente
STREAM_RESOURCE_ID = "SH63tBfY6wEIdkC4u4zKdg1780543868590330"
RTMP = f"rtmp://a.rtmp.youtube.com/live2/{ST_KEY_VAL}"
TMP  = pathlib.Path("/tmp")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERR {m}", flush=True)

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
    except Exception as e: return {"error": str(e)}

def yt_post(token, url, body=None, method="POST"):
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            txt = r.read(); return json.loads(txt) if txt else {}
    except Exception as e: return {"error": str(e)}

def yt_delete(token, url):
    req = urllib.request.Request(url, method="DELETE")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        urllib.request.urlopen(req, timeout=10); return True
    except: return False

# ─── DESCRIÇÃO UNIFICADA EM 15 IDIOMAS ───────────────────────────
TITULO = "🔴 LIVE 24/7 | BLACK SCREEN for Sleep & Focus | Binaural Beats 432Hz | Dark Psychology"

DESCRICAO = """🔴 LIVE 24/7 | BLACK SCREEN | BINAURAL BEATS 432Hz | DARK PSYCHOLOGY
Daniela Coelho — Human Behavior Researcher | @psidanicoelho

🖤 PURE BLACK SCREEN — 100% dark, zero pixels illuminated
🎵 TRUE BINAURAL 432Hz (430Hz Left + 432Hz Right = 2Hz DELTA beat)
🧠 DARK PSYCHOLOGY — Narcissism, Trauma, Anxiety, Attachment Theory
★ Use HEADPHONES for true binaural effect
★ Perfect: Deep Sleep • Study • Meditation • Work • Focus
★ NO logos, NO watermarks, NO brightness — pure black

───────────────────────────────────────────────
🔴 LIVE 24/7 | SCHWARZER BILDSCHIRM | BINAURAL 432Hz | PSYCHOLOGIE [DE]
Daniela Coelho — Verhaltensforscherin | @psidanicoelho
🖤 100% SCHWARZER BILDSCHIRM | ECHTER BINAURAL 432Hz
Kopfhörer empfohlen | Ideal: Schlafen • Lernen • Meditieren • Fokus

🔴 EN DIRECT 24H | ÉCRAN NOIR | BINAURAL 432Hz | PSYCHOLOGIE SOMBRE [FR]
Daniela Coelho — Chercheuse en Comportement | @psidanicoelho
🖤 ÉCRAN 100% NOIR | VRAI BINAURAL 432Hz
Casque recommandé | Idéal: Sommeil • Étude • Méditation • Concentration

🔴 EN VIVO 24H | PANTALLA NEGRA | BINAURAL 432Hz | PSICOLOGÍA OSCURA [ES]
Daniela Coelho — Investigadora del Comportamiento | @psidanicoelho
🖤 PANTALLA 100% NEGRA | BINAURAL REAL 432Hz
Auriculares recomendados | Ideal: Sueño • Estudio • Meditación

🔴 AO VIVO 24H | TELA PRETA | BINAURAL 432Hz | DARK PSYCHOLOGY [PT]
Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho
🖤 TELA 100% PRETA | BINAURAL REAL 432Hz
Fones de ouvido | Ideal: Sono • Estudo • Meditação • Foco

🔴 24時間ライブ | ブラックスクリーン | バイノーラル432Hz | ダーク心理学 [JA]
ダニエラ・コエーリョ — 人間行動研究者 | @psidanicoelho
🖤 完全ブラック画面 | 本物のバイノーラル432Hz
ヘッドフォン推奨 | 最適: 睡眠・勉強・瞑想・集中・作業

🔴 24시간 라이브 | 검은 화면 | 바이노럴 432Hz | 다크 심리학 [KO]
다니엘라 코에요 — 인간 행동 연구자 | @psidanicoelho
🖤 100% 검은 화면 | 진짜 바이노럴 432Hz
헤드폰 권장 | 최적: 수면 • 공부 • 명상 • 집중 • 작업

🔴 24小时直播 | 纯黑屏幕 | 双耳节拍432Hz | 暗黑心理学 [ZH]
达尼埃拉·科埃略 — 人类行为研究者 | @psidanicoelho
🖤 纯黑屏幕100% | 真实双耳节拍432Hz
建议使用耳机 | 最适合: 睡眠 • 学习 • 冥想 • 专注 • 工作

🔴 LIVE 24H | SCHERMO NERO | BINAURAL 432Hz | PSICOLOGIA OSCURA [IT]
Daniela Coelho — Ricercatrice Comportamento Umano | @psidanicoelho
🖤 SCHERMO 100% NERO | BINAURAL VERO 432Hz
Cuffie consigliate | Ideale: Sonno • Studio • Meditazione • Concentrazione

🔴 LIVE 24/7 | ZWART SCHERM | BINAURAL 432Hz | DONKERE PSYCHOLOGIE [NL]
Daniela Coelho — Menselijk Gedragsonderzoeker | @psidanicoelho
🖤 100% ZWART SCHERM | ECHTE BINAURAL 432Hz
Koptelefoon aanbevolen | Ideaal: Slaap • Studie • Meditatie • Focus

🔴 NA ŻYWO 24H | CZARNY EKRAN | BINAURAL 432Hz | CIEMNA PSYCHOLOGIA [PL]
Daniela Coelho — Badaczka Zachowań Ludzkich | @psidanicoelho
🖤 100% CZARNY EKRAN | PRAWDZIWY BINAURAL 432Hz
Słuchawki zalecane | Idealne: Sen • Nauka • Medytacja • Skupienie

🔴 CANLI 24S | SİYAH EKRAN | BINAURAL 432Hz | KARANLIK PSİKOLOJİ [TR]
Daniela Coelho — İnsan Davranışı Araştırmacısı | @psidanicoelho
🖤 %100 SİYAH EKRAN | GERÇEK BİNAURAL 432Hz
Kulaklık önerilir | İdeal: Uyku • Çalışma • Meditasyon • Odaklanma

🔴 LIVE 24 JAM | LAYAR HITAM | BINAURAL 432Hz | PSIKOLOGI GELAP [ID]
Daniela Coelho — Peneliti Perilaku Manusia | @psidanicoelho
🖤 LAYAR 100% HITAM | BINAURAL ASLI 432Hz
Headphone disarankan | Ideal: Tidur • Belajar • Meditasi • Fokus

🔴 24 घंटे लाइव | काली स्क्रीन | बाइनॉरल 432Hz | डार्क साइकोलॉजी [HI]
डेनियला कोएल्हो — मानव व्यवहार शोधकर्ता | @psidanicoelho
🖤 100% काली स्क्रीन | असली बाइनॉरल 432Hz
हेडफोन अनुशंसित | आदर्श: नींद • अध्ययन • ध्यान • एकाग्रता

🔴 بث مباشر 24 ساعة | شاشة سوداء | نغمات ثنائية 432Hz | علم النفس المظلم [AR]
دانييلا كويلو — باحثة في السلوك البشري | @psidanicoelho
🖤 شاشة سوداء 100٪ | ثنائي حقيقي 432Hz
يُنصح بالسماعات | مثالي: النوم • الدراسة • التأمل • التركيز

───────────────────────────────────────────────
Research: Harvard • UCLA • van der Kolk • Ainsworth • Gottman • Beck
💬 Super Chat: ask psychology questions LIVE!
🔔 SUBSCRIBE + BELL for 24/7 access!

#blackscreen #blackscreenforsleep #blackscreen8hours #blackscreen10hours
#binauralbeats432hz #432hz #432hzmusic #sleepmusic #studymusic #focusmusic
#darkpsychology #narcissism #trauma #anxiety #attachment #danielacoelho
#psidanicoelho #schwarzerbildschirm #pantallanegraparadormir #telapreta"""

def delete_all_live_broadcasts(token):
    """Apaga TUDO — broadcasts, vídeos agendados como live, etc."""
    log("─── APAGANDO todas as lives ───")
    total = 0
    # Tentar todos os status possíveis
    for status in ["active", "complete", "created", "ready", "testStarting", "testing", "live"]:
        url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status&broadcastStatus={status}&mine=true&maxResults=50"
        data = yt_get(token, url)
        for item in data.get("items", []):
            bid = item["id"]
            title = item.get("snippet", {}).get("title", "?")[:50]
            lifecycle = item.get("status", {}).get("lifeCycleStatus", "")
            # Encerrar se ativa
            if lifecycle in ["active", "testing", "testStarting", "live"]:
                yt_post(token, f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bid}&part=id", {})
                time.sleep(1)
            ok = yt_delete(token, f"https://www.googleapis.com/youtube/v3/liveBroadcasts?id={bid}")
            log(f"  {'✅' if ok else '⚠'} [{lifecycle}] {title} ({bid})")
            if ok: total += 1
            time.sleep(0.3)
    log(f"  Total removidas: {total}")
    return total

def criar_live_unificada(token):
    """Cria UMA live broadcast unificada com 15 idiomas"""
    log("─── CRIANDO live unificada 15 idiomas ───")
    start = (datetime.now(timezone.utc) + timedelta(minutes=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "snippet": {
            "title": TITULO,
            "description": DESCRICAO[:4900],
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
    res = yt_post(token, "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails", body)
    if "id" in res:
        bc_id = res["id"]
        log(f"  ✅ Live criada: {bc_id}")
        log(f"  Título: {TITULO[:60]}")
        return bc_id
    else:
        err(f"  Falha: {res}")
        return None

def bind_live(token, bc_id):
    """Bind correto usando stream resource ID"""
    log(f"─── BIND {bc_id} → {STREAM_RESOURCE_ID[:30]} ───")
    url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id,contentDetails&streamId={STREAM_RESOURCE_ID}"
    res = yt_post(token, url, {})
    if "error" in str(res.get("error", ""))[:10]:
        err(f"  Bind: {res}")
    else:
        log(f"  ✅ Bind OK")
    return res

def thumbnail_preta_cerebro(token, bc_id):
    """Thumbnail preta + cérebro branco do canal"""
    if not token or not bc_id: return
    try:
        import io as _io
        from PIL import Image, ImageDraw, ImageFont, ImageEnhance
        W, H = 1280, 720
        img = Image.new("RGB", (W, H), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Avatar do canal
        try:
            av_url = "https://yt3.ggpht.com/4NDK-JaBRi0uMyCCeOz-imtfhs6zHuQ2sxUn3d2gCjY_NyS_Z50OCENLFZrS_RjY5wOwKXch=s800-c-k-c0x00ffffff-no-rj"
            req_a = urllib.request.Request(av_url)
            req_a.add_header("User-Agent", "Mozilla/5.0")
            chunks = []
            with urllib.request.urlopen(req_a, timeout=30) as r:
                while True:
                    chunk = r.read(8192)
                    if not chunk: break
                    chunks.append(chunk)
            brain = Image.open(_io.BytesIO(b"".join(chunks))).convert("RGB")
            brain2 = ImageEnhance.Brightness(brain).enhance(2.0)
            brain3 = ImageEnhance.Contrast(brain2).enhance(2.0)
            bw, bh = brain.size
            gray = Image.new("L", (bw, bh))
            p_in = brain3.load(); p_out = gray.load()
            for y in range(bh):
                for x in range(bw):
                    r2, g2, b2 = p_in[x, y]; lum = (r2+g2+b2)//3
                    p_out[x, y] = min(255, int(lum*1.4)) if lum > 30 else 0
            brain_rgb = Image.merge("RGB", [gray, gray, gray])
            target = 460
            brain_r = brain_rgb.resize((target, target), Image.LANCZOS)
            img.paste(brain_r, (W//2 - target//2, H//2 - target//2 - 10))
        except Exception as e: err(f"Avatar: {e}")
        # Badges
        try: fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        except: fb = ImageFont.load_default()
        try: ft = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except: ft = ImageFont.load_default()
        draw.rectangle([(14,14),(155,50)], fill=(220,20,60))
        draw.text((20,18), "● LIVE 24/7", font=fb, fill=(255,255,255))
        draw.rectangle([(160,14),(395,50)], fill=(0,0,0), outline=(255,255,255), width=1)
        draw.text((166,18), "BLACK SCREEN", font=fb, fill=(255,255,255))
        draw.rectangle([(400,14),(640,50)], fill=(22,101,52))
        draw.text((406,18), "BINAURAL 432Hz", font=fb, fill=(255,255,255))
        draw.text((W-285, H-48), "@psidanicoelho", font=ft, fill=(200,200,200))
        draw.rectangle([(0,0),(W,2)], fill=(255,255,255))
        draw.rectangle([(0,H-2),(W,H)], fill=(255,255,255))
        p = TMP / "thumb.jpg"; img.save(str(p), "JPEG", quality=95)
        req2 = urllib.request.Request(
            f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={bc_id}&uploadType=media",
            data=open(str(p), "rb").read(), method="POST")
        req2.add_header("Authorization", f"Bearer {token}")
        req2.add_header("Content-Type", "image/jpeg")
        req2.add_header("Content-Length", str(p.stat().st_size))
        with urllib.request.urlopen(req2, timeout=60): log("  ✅ Thumbnail preta+cérebro")
    except Exception as e: err(f"Thumb: {e}")

def gerar_wav():
    SR, DUR = 44100, 5; s = SR * DUR; out = bytearray()
    for i in range(s):
        t = i / SR
        out += struct.pack('<hh',
            int(math.sin(2*math.pi*430*t)*22000),
            int(math.sin(2*math.pi*432*t)*22000))
    p = TMP / "b432.wav"
    with wave.open(str(p), 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2)
        wf.setframerate(SR); wf.writeframes(bytes(out))
    log(f"  WAV binaural 432Hz: {p.stat().st_size//1024}KB ✅")
    return str(p)

def ffm():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    for p in [shutil.which("ffmpeg"), "/usr/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists(): return p
    return "ffmpeg"

def transmitir(wav, ff, dur_s):
    log(f"🔴 Transmitindo {dur_s//3600}h{dur_s%3600//60}m → RTMP...")
    cmd = [ff, "-y", "-re",
           "-stream_loop", "-1", "-i", wav,
           "-f", "lavfi", "-i", "color=black:size=1920x1080:rate=25",
           "-map", "1:v", "-map", "0:a",
           "-c:v", "libx264", "-preset", "ultrafast", "-crf", "36",
           "-b:v", "150k", "-maxrate", "200k", "-bufsize", "400k",
           "-g", "50", "-r", "25", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "44100",
           "-f", "flv", "-t", str(dur_s), RTMP]
    return subprocess.run(cmd, timeout=dur_s + 900).returncode

def main():
    log("=" * 65)
    log(f"LIVE UNIFICADA | 15 IDIOMAS | {datetime.now(timezone.utc):%H:%M} UTC | {DURATION_H}h")
    log("=" * 65)
    ff = ffm()
    wav = gerar_wav()
    token = get_token()
    log(f"Token OAuth ✅")

    # 1. Apagar TODAS as lives
    delete_all_live_broadcasts(token)
    time.sleep(3)

    # 2. Criar UMA live unificada
    bc_id = criar_live_unificada(token)
    if not bc_id:
        err("CRIAÇÃO FALHOU"); return
    time.sleep(2)

    # 3. Bind ao stream correto
    bind_live(token, bc_id)
    time.sleep(2)

    # 4. Thumbnail
    thumbnail_preta_cerebro(token, bc_id)

    log(f"\n✅ LIVE PRONTA: https://www.youtube.com/watch?v={bc_id}")
    log(f"   Studio: https://studio.youtube.com/video/{bc_id}/livestreaming\n")

    # 5. Stream em loop
    dur_s = DURATION_H * 3600
    inicio = time.time()
    tentativas = 0
    while time.time() - inicio < dur_s and tentativas < 30:
        restante = int(dur_s - (time.time() - inicio))
        if restante < 15: break
        tentativas += 1
        log(f"[{tentativas}] Streaming {restante//3600}h{restante%3600//60}m restantes")
        rc = transmitir(wav, ff, restante)
        log(f"  ffmpeg rc={rc}")
        if rc == 0: break
        espera = min(20 * tentativas, 120)
        log(f"  retry em {espera}s..."); time.sleep(espera)

    log(f"TOTAL: {(time.time()-inicio)//60:.0f}min")

if __name__ == "__main__":
    main()
