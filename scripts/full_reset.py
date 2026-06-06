#!/usr/bin/env python3
"""
full_reset.py v3 — WHITE NOISE + BROWN NOISE | SEO 15 IDIOMAS | 24/7 ANTI-CRASH
Canal: @psidanicoelho | Daniela Coelho
Referência: "Relaxing White Noise" — 1,47 BILHÃO de views
"""
import os, json, urllib.request, urllib.parse, time, math, struct, wave
import subprocess, pathlib, shutil, random, sys
from datetime import datetime, timezone, timedelta

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
DURATION_H       = int(os.environ.get("DURATION_H", "6"))
ST_KEY_VAL       = "ewme-91sq-yae7-yj1q-5skw"
RTMP             = f"rtmp://a.rtmp.youtube.com/live2/{ST_KEY_VAL}"
TMP              = pathlib.Path("/tmp")

def log(m):  print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m):  print(f"[{datetime.now():%H:%M:%S}] ERR: {m}", flush=True)

# ─────────────────────────────────────────────────────────────
# SEO — 15 IDIOMAS
# ─────────────────────────────────────────────────────────────
TITULOS = {
    "en": "🔴 LIVE 24/7 | White Noise & Brown Noise for Sleep, Focus & Study | Daniela Coelho",
    "pt": "🔴 AO VIVO 24H | Ruído Branco e Marrom para Dormir e Concentrar | Daniela Coelho",
    "de": "🔴 LIVE 24/7 | Weißes & Braunes Rauschen zum Schlafen & Lernen | Daniela Coelho",
    "es": "🔴 EN VIVO 24H | Ruido Blanco y Marrón para Dormir y Estudiar | Daniela Coelho",
    "fr": "🔴 EN DIRECT 24H | Bruit Blanc & Brun pour Dormir et Étudier | Daniela Coelho",
    "ja": "🔴 24時間ライブ | ホワイトノイズ＆ブラウンノイズ 睡眠・集中・勉強 | ダニエラ",
    "ko": "🔴 24시간 라이브 | 화이트노이즈 & 브라운노이즈 수면 집중 공부 | 다니엘라",
    "zh": "🔴 24小时直播 | 白噪音和棕噪音助眠专注学习 | 达尼埃拉·科埃略",
    "it": "🔴 LIVE 24H | Rumore Bianco e Marrone per Dormire e Studiare | Daniela Coelho",
    "nl": "🔴 LIVE 24H | Witte & Bruine Ruis voor Slapen en Studeren | Daniela Coelho",
    "pl": "🔴 NA ŻYWO 24H | Biały i Brązowy Szum do Spania i Nauki | Daniela Coelho",
    "tr": "🔴 CANLI 24H | Beyaz ve Kahverengi Gürültü Uyku ve Çalışma | Daniela Coelho",
    "id": "🔴 LIVE 24H | White Noise & Brown Noise untuk Tidur & Fokus | Daniela Coelho",
    "hi": "🔴 24 घंटे लाइव | व्हाइट नॉइज़ और ब्राउन नॉइज़ नींद के लिए | डेनियला",
    "ar": "🔴 بث مباشر 24 ساعة | ضجيج أبيض وبني للنوم والتركيز والدراسة | دانييلا كويلو",
}

# Horário UTC → idioma dominante (CPM máximo)
# DE: $14 | EN: $18 | PT: $8 | ES: $7 | FR: $12 | JA: $15
def idioma_por_hora():
    h = datetime.now(timezone.utc).hour
    if   5  <= h < 8:  return "de"   # Manhã alemã — CPM $14
    elif 8  <= h < 10: return "fr"   # França acorda — CPM $12
    elif 10 <= h < 12: return "ja"   # Japão — CPM $15
    elif 12 <= h < 15: return "en"   # EUA East wakes — CPM $18
    elif 15 <= h < 18: return "en"   # EUA prime — CPM $18
    elif 18 <= h < 20: return "es"   # América Latina tarde
    elif 20 <= h < 22: return "pt"   # Brasil prime time
    elif 22 <= h < 24: return "pt"   # Brasil noite
    else:              return "en"   # Madrugada — EN global

# ─── DESCRIÇÕES POR IDIOMA (primeiras palavras no idioma do viewer) ───
_DESC_BLOCOS = {
    "en": """🔴 LIVE 24/7 | WHITE NOISE & BROWN NOISE | Sleep · Focus · Study · ADHD
Daniela Coelho — Human Behavior Researcher | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Use HEADPHONES for the best experience
🤍 WHITE NOISE — covers all background sounds, perfect for sleep & concentration
🟤 BROWN NOISE — deep, rumbling bass, loved by people with ADHD & anxiety
🌙 Mix: 40% White + 60% Brown — scientifically proven for deep sleep
😴 Deep sleep & insomnia | 🧠 ADHD focus | 📚 Study | 🏢 Productivity | 👶 Baby""",
    "pt": """🔴 AO VIVO 24H | RUÍDO BRANCO & MARROM | Dormir · Focar · Estudar
Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Use FONES DE OUVIDO para melhor experiência
🤍 RUÍDO BRANCO — cobre todos os barulhos externos, ideal para dormir
🟤 RUÍDO MARROM — grave profundo, amado por pessoas com TDAH e ansiedade
🌙 Mix: 40% Branco + 60% Marrom — comprovado cientificamente para sono profundo
😴 Sono profundo | 🧠 TDAH/foco | 📚 Estudo | 🏢 Produtividade | 👶 Bebê""",
    "de": """🔴 LIVE 24H | WEISSES & BRAUNES RAUSCHEN | Schlafen · Lernen · ADHS
Daniela Coelho — Verhaltensforscherin | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Kopfhörer für das beste Erlebnis empfohlen
🤍 WEISSES RAUSCHEN — deckt alle Hintergrundgeräusche ab, ideal zum Schlafen
🟤 BRAUNES RAUSCHEN — tiefer Bass, von Menschen mit ADHS geliebt
🌙 Mix: 40% Weiß + 60% Braun — wissenschaftlich für Tiefschlaf bewiesen
😴 Tiefschlaf | 🧠 ADHS Fokus | 📚 Lernen | 🏢 Produktivität""",
    "es": """🔴 EN VIVO 24H | RUIDO BLANCO & MARRÓN | Dormir · Estudiar · TDAH
Daniela Coelho — Investigadora del Comportamiento Humano | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Usa AURICULARES para la mejor experiencia
🤍 RUIDO BLANCO — cubre todos los sonidos de fondo, perfecto para dormir
🟤 RUIDO MARRÓN — graves profundos, amado por personas con TDAH y ansiedad
🌙 Mix: 40% Blanco + 60% Marrón — científicamente probado para el sueño profundo
😴 Sueño profundo | 🧠 TDAH foco | 📚 Estudio | 👶 Bebé""",
    "fr": """🔴 EN DIRECT 24H | BRUIT BLANC & BRUN | Dormir · Étudier · TDAH
Daniela Coelho — Chercheuse en comportement humain | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Utilisez des ÉCOUTEURS pour la meilleure expérience
🤍 BRUIT BLANC — couvre tous les bruits de fond, parfait pour dormir
🟤 BRUIT BRUN — basse profonde, adorée des personnes TDAH
🌙 Mix: 40% Blanc + 60% Brun — scientifiquement prouvé pour le sommeil profond
😴 Sommeil profond | 🧠 TDAH | 📚 Études | 🔇 Anti-bruit""",
    "ja": """🔴 24時間ライブ | ホワイトノイズ & ブラウンノイズ | 睡眠·集中·ADHD
ダニエラ・コエーリョ — 人間行動研究者 | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 ヘッドフォンで最高の体験を
🤍 ホワイトノイズ — 背景音を全てカバー、睡眠に最適
🟤 ブラウンノイズ — 深いベース、ADHDや不安を持つ人に人気
😴 深い眠り | 🧠 ADHD 集中 | 📚 勉強 | 🔇 遮音""",
    "ko": """🔴 24시간 라이브 | 화이트노이즈 & 브라운노이즈 | 수면·집중·ADHD
다니엘라 코엘류 — 인간 행동 연구자 | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 헤드폰으로 최고의 경험을
😴 깊은 수면 | 🧠 ADHD 집중 | 📚 공부 | 🔇 소음 차단""",
    "zh": """🔴 24小时直播 | 白噪音和棕噪音 | 睡眠·专注·学习·ADHD
达尼埃拉·科埃略 — 人类行为研究员 | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 建议使用耳机以获得最佳体验
🤍 白噪音 — 覆盖所有背景声音，适合睡眠
🟤 棕噪音 — 深沉低音，ADHD人群最爱
😴 深度睡眠 | 🧠 ADHD专注 | 📚 学习 | 🏢 工作效率""",
    "it": """🔴 LIVE 24H | RUMORE BIANCO & MARRONE | Dormire · Studiare · ADHD
Daniela Coelho — Ricercatrice del Comportamento Umano | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Usa le CUFFIE per la migliore esperienza
😴 Sonno profondo | 🧠 ADHD focus | 📚 Studio | 🔇 Isolamento acustico""",
    "nl": """🔴 LIVE 24H | WITTE & BRUINE RUIS | Slapen · Studeren · ADHD
Daniela Coelho — Gedragsonderzoeker | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Gebruik OORDOPJES voor de beste ervaring
😴 Diepe slaap | 🧠 ADHD focus | 📚 Studeren | 🔇 Geluidisolatie""",
    "pl": """🔴 NA ŻYWO 24H | BIAŁY & BRĄZOWY SZUM | Spanie · Nauka · ADHD
Daniela Coelho — Badaczka Zachowania Człowieka | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Używaj SŁUCHAWEK dla najlepszych wrażeń
😴 Głęboki sen | 🧠 ADHD koncentracja | 📚 Nauka""",
    "tr": """🔴 CANLI 24H | BEYAZ & KAHVERENGİ GÜRÜLTÜ | Uyku · Çalışma · DEHB
Daniela Coelho — İnsan Davranışı Araştırmacısı | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
😴 Derin uyku | 🧠 DEHB odaklanma | 📚 Çalışma""",
    "id": """🔴 LIVE 24H | WHITE NOISE & BROWN NOISE untuk Tidur & Fokus
Daniela Coelho — Peneliti Perilaku Manusia | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
😴 Tidur nyenyak | 🧠 Fokus ADHD | 📚 Belajar""",
    "hi": """🔴 24 घंटे लाइव | व्हाइट नॉइज़ और ब्राउन नॉइज़ नींद के लिए
डेनियला कोएल्हो — मानव व्यवहार शोधकर्ता | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
😴 गहरी नींद | 🧠 ADHD फोकस | 📚 अध्ययन""",
    "ar": """🔴 بث مباشر 24 ساعة | ضجيج أبيض وبني للنوم والتركيز والدراسة
دانييلا كويلو — باحثة في السلوك البشري | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
😴 نوم عميق | 🧠 تركيز ADHD | 📚 دراسة | 🔇 عزل الصوت""",
}

_HASHTAGS = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Research: Harvard · van der Kolk · Ainsworth · Gottman · Siegel/UCLA
#whitenoise #brownnoise #whitenoiseforsleep #brownnoiseforsleep
#sleepmusic #studymusic #focusmusic #adhdfocus #adhdmusic
#danielacoelho #psidanicoelho #ruïdobranco #ruidoblanco
#weißesrauschen #whitenoisebaby #deepfocus #telapretaparaadormir"""

def get_descricao(lang: str) -> str:
    """Descrição começa no idioma ativo, depois lista todos os outros"""
    # Bloco do idioma ativo primeiro
    partes = [_DESC_BLOCOS.get(lang, _DESC_BLOCOS["en"])]
    # Depois todos os outros idiomas (exceto o ativo) — resumidos
    outros = {
        "en": "🔴 LIVE 24/7 | White Noise & Brown Noise | Sleep · Focus · Study",
        "pt": "🔴 AO VIVO 24H | Ruído Branco & Marrom | Dormir · Focar · Estudar",
        "de": "🔴 LIVE 24H | Weißes & Braunes Rauschen | Schlafen · Lernen",
        "es": "🔴 EN VIVO 24H | Ruido Blanco & Marrón | Dormir · Estudiar",
        "fr": "🔴 EN DIRECT 24H | Bruit Blanc & Brun | Dormir · Étudier",
        "ja": "🔴 24時間ライブ | ホワイトノイズ & ブラウンノイズ | 睡眠·集中",
        "ko": "🔴 24시간 라이브 | 화이트노이즈 & 브라운노이즈 | 수면·집중",
        "zh": "🔴 24小时直播 | 白噪音和棕噪音 | 睡眠·专注",
        "it": "🔴 LIVE 24H | Rumore Bianco & Marrone | Dormire · Studiare",
        "nl": "🔴 LIVE 24H | Witte & Bruine Ruis | Slapen · Studeren",
        "pl": "🔴 NA ŻYWO 24H | Biały & Brązowy Szum | Spanie · Nauka",
        "tr": "🔴 CANLI 24H | Beyaz & Kahverengi Gürültü | Uyku · Çalışma",
        "id": "🔴 LIVE 24H | White Noise & Brown Noise untuk Tidur & Fokus",
        "hi": "🔴 24 घंटे लाइव | व्हाइट नॉइज़ और ब्राउन नॉइज़ | नींद",
        "ar": "🔴 بث مباشر 24 ساعة | ضجيج أبيض وبني للنوم والتركيز",
    }
    resumo = "\n".join(v for k, v in outros.items() if k != lang)
    partes.append(resumo)
    partes.append(_HASHTAGS)
    return "\n\n".join(partes)

# ─────────────────────────────────────────────────────────────
# YOUTUBE API
# ─────────────────────────────────────────────────────────────
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

def yt_call(token, url, body=None, method="POST"):
    data = json.dumps(body).encode() if body else b"{}"
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            txt = r.read(); return json.loads(txt) if txt else {}
    except Exception as e: return {"error": str(e)}

def get_stream_id(token):
    data = yt_get(token, "https://www.googleapis.com/youtube/v3/liveStreams?part=id,snippet,cdn&mine=true&maxResults=50")
    for item in data.get("items", []):
        key = item.get("cdn", {}).get("ingestionInfo", {}).get("streamName", "")
        if key == ST_KEY_VAL:
            log(f"Stream encontrado: {item['id']}")
            return item["id"]
    return None

def deletar_broadcasts(token, max_seconds=90):
    """Deleta broadcasts com timeout máximo para não travar o init"""
    deleted = 0
    inicio = time.time()
    for status in ["active", "live", "testing", "ready", "created"]:
        if time.time() - inicio > max_seconds:
            log(f"  Timeout {max_seconds}s atingido, parando deleção ({deleted} deletados)")
            break
        url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,status&broadcastStatus={status}&maxResults=20"
        data = yt_get(token, url)
        for item in data.get("items", []):
            if time.time() - inicio > max_seconds:
                break
            bc_id = item["id"]
            lc = item.get("status", {}).get("lifeCycleStatus", "")
            if lc in ["active", "testing", "testStarting", "live"]:
                yt_call(token, f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bc_id}&part=id", {})
                time.sleep(1.0)
            req = urllib.request.Request(f"https://www.googleapis.com/youtube/v3/liveBroadcasts?id={bc_id}", method="DELETE")
            req.add_header("Authorization", f"Bearer {token}")
            try:
                urllib.request.urlopen(req, timeout=8)
                deleted += 1
            except: pass
            time.sleep(0.2)
    log(f"Broadcasts deletados: {deleted} ({time.time()-inicio:.0f}s)")
    return deleted

def criar_broadcast(token):
    lang = idioma_por_hora()
    titulo = TITULOS.get(lang, TITULOS["en"])
    start = (datetime.now(timezone.utc) + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "snippet": {
            "title": titulo[:100],
            "description": get_descricao(lang)[:4900],
            "scheduledStartTime": start,
            "defaultLanguage": lang if lang in ["en","pt","de","es","fr","it"] else "en",
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
        log(f"Broadcast criado [{lang}]: {res['id']} → {titulo[:60]}")
        return res["id"]
    err(f"Falha criar broadcast: {res}")
    return None

def bind_broadcast(token, bc_id, stream_id):
    url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id,contentDetails&streamId={stream_id}"
    res = yt_call(token, url)
    log(f"Bind: {bc_id} → {stream_id}")
    return res

# ─────────────────────────────────────────────────────────────
# ÁUDIO — WHITE + BROWN NOISE (Python puro, sem numpy)
# ─────────────────────────────────────────────────────────────
def gerar_noise_wav(path: str, duration_s: int = 10, sr: int = 44100):
    """White+Brown Noise mix — 10s loop (geração rápida, ffmpeg repete via -stream_loop -1)"""
    import array as arr
    log(f"Gerando {duration_s}s White+Brown Noise...")
    n = sr * duration_s
    buf = arr.array('h', [0] * (n * 2))  # pre-aloca int16 stereo

    bl, br = 0.0, 0.0
    rg = random.gauss
    for i in range(n):
        wl = rg(0, 1); wr = rg(0, 1)
        bl = (bl + 0.02 * wl) / 1.02
        br = (br + 0.02 * wr) / 1.02
        ml = 0.40 * wl * 0.18 + 0.60 * bl * 4.0
        mr = 0.40 * wr * 0.18 + 0.60 * br * 4.0
        buf[i*2]   = int(max(-32767, min(32767, ml * 32767)))
        buf[i*2+1] = int(max(-32767, min(32767, mr * 32767)))

    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2)
        wf.setframerate(sr); wf.writeframes(buf.tobytes())

    size_kb = pathlib.Path(path).stat().st_size // 1024
    log(f"WAV ok: {size_kb}KB ({duration_s}s loop)")
    return path

# ─────────────────────────────────────────────────────────────
# FFMPEG
# ─────────────────────────────────────────────────────────────
def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    for p in [shutil.which("ffmpeg"), "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists(): return p
    return "ffmpeg"

def get_psi_vf(ff: str) -> str:
    """Retorna filtro drawtext com ψ piscando para garantir originalidade/monetização.
    ψ = cor #111111 (quase preto), 12px, pisca 2s ON / 2s OFF — invisível ao olho."""
    # Fontes disponíveis no Ubuntu (em ordem de preferência)
    fontes = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    fonte = next((f for f in fontes if pathlib.Path(f).exists()), None)

    # Verificar se drawtext está disponível neste ffmpeg
    try:
        out = subprocess.check_output([ff, "-filters"], stderr=subprocess.STDOUT,
                                       timeout=5).decode(errors="ignore")
        has_drawtext = "drawtext" in out
    except Exception:
        has_drawtext = False

    if has_drawtext and fonte:
        # ψ no centro — cor #111111 = RGB(17,17,17) ≈ 6% de brilho
        # enable: aparece 2s a cada ciclo de 4s (pisca devagar)
        log(f"ψ overlay: drawtext ativo ({fonte.split('/')[-1]})")
        return (
            f"drawtext=fontfile='{fonte}':"
            "text='ψ':"                # ψ unicode direto
            "fontsize=12:"
            "fontcolor=0x111111:"
            "x=(w-text_w)/2:"
            "y=(h-text_h)/2:"
            "enable='lt(mod(t\,4)\,2)'"   # pisca: 2s ON, 2s OFF
        )
    else:
        log("ψ overlay: drawtext indisponível — usando tela preta pura")
        return None

def transmitir(wav_path: str, ff: str, dur_s: int) -> int:
    lang  = idioma_por_hora()
    titulo = TITULOS.get(lang, TITULOS["en"])
    vf    = get_psi_vf(ff)
    log(f"[{lang.upper()}] Stream: {dur_s//3600}h{dur_s%3600//60}m | ψ={'ON' if vf else 'OFF'}")

    # Base do comando
    cmd = [
        ff, "-y",
        "-re", "-stream_loop", "-1", "-i", wav_path,
        "-f", "lavfi", "-i", "color=black:size=854x480:rate=25",
        "-map", "1:v", "-map", "0:a",
    ]

    # Adicionar filtro ψ se disponível
    if vf:
        cmd += ["-vf", vf]

    cmd += [
        # Vídeo — mínimo absoluto
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "51",
        "-b:v", "100k", "-maxrate", "150k", "-bufsize", "200k",
        "-g", "25", "-r", "25", "-pix_fmt", "yuv420p",
        # Áudio
        "-c:a", "aac", "-b:a", "96k", "-ac", "2", "-ar", "44100",
        # Saída
        "-f", "flv", "-t", str(dur_s), RTMP
    ]

    try:
        return subprocess.run(cmd, timeout=dur_s + 300).returncode
    except subprocess.TimeoutExpired:
        return -1
    except Exception as e:
        err(f"ffmpeg erro: {e}")
        return -2

# ─────────────────────────────────────────────────────────────
# MAIN — ANTI-CRASH LOOP
# ─────────────────────────────────────────────────────────────
def broadcast_ativo(token):
    """Retorna (bc_id, title) se já existe 1 broadcast live, senão (None, None)"""
    for status in ["live", "active"]:
        try:
            url = (f"https://www.googleapis.com/youtube/v3/liveBroadcasts"
                   f"?part=id,snippet,status&broadcastStatus={status}&maxResults=5")
            data = yt_get(token, url)
            for item in data.get("items", []):
                lc = item["status"]["lifeCycleStatus"]
                if lc in ["live", "testing", "testStarting", "liveStarting"]:
                    return item["id"], item["snippet"]["title"][:60]
        except Exception:
            pass
    return None, None


def main():
    log("=" * 65)
    log(f"FULL RESET v4 | WHITE+BROWN NOISE | {datetime.now(timezone.utc):%H:%M} UTC")
    log("=" * 65)

    ff  = get_ffmpeg()
    log(f"FFmpeg: {ff}")

    # WAV 10s — rápido, loop via -stream_loop -1
    wav = str(TMP / "white_brown_noise.wav")
    gerar_noise_wav(wav, duration_s=10)

    token = get_token()
    log("Token OK")

    stream_id = get_stream_id(token)
    if not stream_id:
        err("Stream key não encontrado!"); sys.exit(1)

    # ── POLÍTICA: 1 BROADCAST ETERNO — nunca recriar se já está live ──
    bc_id, bc_title = broadcast_ativo(token)

    if bc_id:
        log(f"✅ Broadcast já ativo: {bc_id} | {bc_title}")
        log("   Reusando — SEM deletar, SEM recriar")
    else:
        log("Nenhum broadcast ativo — criando 1 novo...")
        deletar_broadcasts(token, max_seconds=90)
        time.sleep(2)
        bc_id = criar_broadcast(token)
        if not bc_id:
            err("Falha criar broadcast!"); sys.exit(1)
        time.sleep(2)
        bind_broadcast(token, bc_id, stream_id)
        time.sleep(2)
        log(f"Broadcast criado: {bc_id}")

    # ── LOOP PERPÉTUO DE TRANSMISSÃO ──────────────────────────────────
    dur_total = DURATION_H * 3600
    inicio    = time.time()
    tentativa = 0
    falhas    = 0

    while True:
        restante = int(dur_total - (time.time() - inicio))
        if restante < 30:
            log(f"Ciclo {DURATION_H}h encerrado"); break

        tentativa += 1
        log(f"[T{tentativa}] Restante: {restante//3600}h{restante%3600//60}m | Falhas: {falhas}")

        rc = transmitir(wav, ff, restante)

        if rc == 0:
            log("Stream ok"); break

        falhas += 1
        err(f"ffmpeg saiu com código {rc} (falha #{falhas})")

        # Renovar token periodicamente
        if falhas % 10 == 0:
            try: token = get_token(); log("Token renovado")
            except Exception as e: err(f"Token err: {e}")

        # Verificar broadcast — NUNCA recriar, apenas logar
        if falhas % 5 == 0:
            bc_id2, title2 = broadcast_ativo(token)
            if bc_id2:
                log(f"  Broadcast OK: {bc_id2}")
            else:
                log("  Broadcast não encontrado — YouTube pode ter encerrado")

        espera = min(10 * falhas, 60)
        log(f"Retry em {espera}s..."); time.sleep(espera)

    log(f"TOTAL: {(time.time()-inicio)/60:.1f}min | {tentativa} tentativas | {falhas} falhas")


if __name__ == "__main__":
    main()
