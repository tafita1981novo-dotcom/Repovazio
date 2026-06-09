#!/usr/bin/env python3
"""
full_reset.py v3 — WHITE NOISE + BROWN NOISE | SEO 15 IDIOMAS | 24/7 ANTI-CRASH
Canal: @psidanicoelho
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
# TÍTULOS — só idiomas com alfabeto latino para o título do broadcast
# JA/KO/ZH/AR/HI ficam SOMENTE na descrição (evita broadcast em japonês/chinês)
TITULO = "🔴 WHITE NOISE & BROWN NOISE 24/7 | Black Screen | Ruido Blanco | Ruído Branco | 白噪音 | Sleep"
# TITULOS: todos fixos em EN para máximo alcance global e CPM em dólar
TITULOS = {lang: TITULO for lang in ["en","pt","de","es","fr","ja","ko","zh","it","nl","pl","tr","id","hi","ar"]}

# Horário UTC → idioma dominante (CPM máximo)
# DE: $14 | EN: $18 | PT: $8 | ES: $7 | FR: $12 | JA: $15
def idioma_por_hora():
    # Só idiomas com títulos em alfabeto latino — JA/KO/ZH/AR/HI removidos
    # (ficam só na descrição multi-idioma)
    h = datetime.now(timezone.utc).hour
    if   5  <= h < 8:  return "de"   # Manhã alemã
    elif 8  <= h < 10: return "fr"   # França acorda
    elif 10 <= h < 14: return "en"   # EN global (era JA 10-12h → corrigido)
    elif 14 <= h < 18: return "en"   # EUA prime — CPM $18
    elif 18 <= h < 20: return "es"   # América Latina tarde
    elif 20 <= h < 24: return "pt"   # Brasil prime time
    else:              return "en"   # Madrugada — EN global

# ─── DESCRIÇÕES POR IDIOMA (primeiras palavras no idioma do viewer) ───
_DESC_BLOCOS = {
    "en": """🔴 LIVE 24/7 | WHITE NOISE & BROWN NOISE | Sleep · Focus · Study · ADHD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Use HEADPHONES for the best experience
🤍 WHITE NOISE — covers all background sounds, perfect for sleep & concentration
🟤 BROWN NOISE — deep, rumbling bass, loved by people with ADHD & anxiety
🌙 Mix: 40% White + 60% Brown — scientifically proven for deep sleep
😴 Deep sleep & insomnia | 🧠 ADHD focus | 📚 Study | 🏢 Productivity | 👶 Baby
🔔 SUBSCRIBE & click the 🔔 Bell — Never miss a 24/7 live! → @psidanicoelho""",
    "pt": """🔴 AO VIVO 24H | RUÍDO BRANCO & MARROM | Dormir · Focar · Estudar
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Use FONES DE OUVIDO para melhor experiência
🤍 RUÍDO BRANCO — cobre todos os barulhos externos, ideal para dormir
🟤 RUÍDO MARROM — grave profundo, amado por pessoas com TDAH e ansiedade
🌙 Mix: 40% Branco + 60% Marrom — comprovado cientificamente para sono profundo
😴 Sono profundo | 🧠 TDAH/foco | 📚 Estudo | 🏢 Produtividade | 👶 Bebê
🔔 INSCREVA-SE e ative o 🔔 sininho — Ao vivo 24h todo dia! → @psidanicoelho""",
    "de": """🔴 LIVE 24H | WEISSES & BRAUNES RAUSCHEN | Schlafen · Lernen · ADHS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Kopfhörer für das beste Erlebnis empfohlen
🤍 WEISSES RAUSCHEN — deckt alle Hintergrundgeräusche ab, ideal zum Schlafen
🟤 BRAUNES RAUSCHEN — tiefer Bass, von Menschen mit ADHS geliebt
🌙 Mix: 40% Weiß + 60% Braun — wissenschaftlich für Tiefschlaf bewiesen
😴 Tiefschlaf | 🧠 ADHS Fokus | 📚 Lernen | 🏢 Produktivität""",
    "es": """🔴 EN VIVO 24H | RUIDO BLANCO & MARRÓN | Dormir · Estudiar · TDAH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Usa AURICULARES para la mejor experiencia
🤍 RUIDO BLANCO — cubre todos los sonidos de fondo, perfecto para dormir
🟤 RUIDO MARRÓN — graves profundos, amado por personas con TDAH y ansiedad
🌙 Mix: 40% Blanco + 60% Marrón — científicamente probado para el sueño profundo
😴 Sueño profundo | 🧠 TDAH foco | 📚 Estudio | 👶 Bebé
🔔 SUSCRÍBETE y activa la 🔔 campana — ¡En vivo 24h todos los días! → @psidanicoelho""",
    "fr": """🔴 EN DIRECT 24H | BRUIT BLANC & BRUN | Dormir · Étudier · TDAH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Utilisez des ÉCOUTEURS pour la meilleure expérience
🤍 BRUIT BLANC — couvre tous les bruits de fond, parfait pour dormir
🟤 BRUIT BRUN — basse profonde, adorée des personnes TDAH
🌙 Mix: 40% Blanc + 60% Brun — scientifiquement prouvé pour le sommeil profond
😴 Sommeil profond | 🧠 TDAH | 📚 Études | 🔇 Anti-bruit""",
    "ja": """🔴 24時間ライブ | ホワイトノイズ & ブラウンノイズ | 睡眠·集中·ADHD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 ヘッドフォンで最高の体験を
🤍 ホワイトノイズ — 背景音を全てカバー、睡眠に最適
🟤 ブラウンノイズ — 深いベース、ADHDや不安を持つ人に人気
😴 深い眠り | 🧠 ADHD 集中 | 📚 勉強 | 🔇 遮音""",
    "ko": """🔴 24시간 라이브 | 화이트노이즈 & 브라운노이즈 | 수면·집중·ADHD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 헤드폰으로 최고의 경험을
😴 깊은 수면 | 🧠 ADHD 집중 | 📚 공부 | 🔇 소음 차단""",
    "zh": """🔴 24小时直播 | 白噪音和棕噪音 | 睡眠·专注·学习·ADHD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 建议使用耳机以获得最佳体验
🤍 白噪音 — 覆盖所有背景声音，适合睡眠
🟤 棕噪音 — 深沉低音，ADHD人群最爱
😴 深度睡眠 | 🧠 ADHD专注 | 📚 学习 | 🏢 工作效率""",
    "it": """🔴 LIVE 24H | RUMORE BIANCO & MARRONE | Dormire · Studiare · ADHD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Usa le CUFFIE per la migliore esperienza
😴 Sonno profondo | 🧠 ADHD focus | 📚 Studio | 🔇 Isolamento acustico""",
    "nl": """🔴 LIVE 24H | WITTE & BRUINE RUIS | Slapen · Studeren · ADHD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Gebruik OORDOPJES voor de beste ervaring
😴 Diepe slaap | 🧠 ADHD focus | 📚 Studeren | 🔇 Geluidisolatie""",
    "pl": """🔴 NA ŻYWO 24H | BIAŁY & BRĄZOWY SZUM | Spanie · Nauka · ADHD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Używaj SŁUCHAWEK dla najlepszych wrażeń
😴 Głęboki sen | 🧠 ADHD koncentracja | 📚 Nauka""",
    "tr": """🔴 CANLI 24H | BEYAZ & KAHVERENGİ GÜRÜLTÜ | Uyku · Çalışma · DEHB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
😴 Derin uyku | 🧠 DEHB odaklanma | 📚 Çalışma""",
    "id": """🔴 LIVE 24H | WHITE NOISE & BROWN NOISE untuk Tidur & Fokus
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
😴 Tidur nyenyak | 🧠 Fokus ADHD | 📚 Belajar""",
    "hi": """🔴 24 घंटे लाइव | व्हाइट नॉइज़ और ब्राउन नॉइज़ नींद के लिए
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
😴 गहरी नींद | 🧠 ADHD फोकस | 📚 अध्ययन""",
    "ar": """🔴 بث مباشر 24 ساعة | ضجيج أبيض وبني للنوم والتركيز والدراسة
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
😴 نوم عميق | 🧠 تركيز ADHD | 📚 دراسة | 🔇 عزل الصوت""",
}

_HASHTAGS = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#whitenoise #brownnoise #ASMR #blackscreen #sleep #lofi #meditation
#whitenoiseforsleep #brownnoiseforsleep #tinnitus #babysleep
#sleepmusic #studymusic #focusmusic #adhdfocus #adhdmusic
#meditationmusic #ambientnoise #studywithme #concentrationmusic
#psidanicoelho #ruidobranco #ruidoblanco
#白噪音 #백색소음 #ホワイトノイズ #telapreta #pantallanegra #live24hours"""

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
    # SEMPRE tenta reutilizar um broadcast existente ANTES de criar novo
    # Evita múltiplos broadcasts/duplicatas
    try:
        existing = broadcast_ativo(token)
        if existing and existing[0]:
            log(f"Reutilizando broadcast existente: {existing[0]}")
            return existing[0]
    except Exception as e:
        log(f"Verificação existente: {e}")
    # SEMPRE cria em EN — título rotaciona via atualizar_broadcast a cada hora
    # Evita broadcast em japonês/coreano/árabe que confunde o YouTube
    lang = "en"
    titulo = TITULOS["en"]
    start = (datetime.now(timezone.utc) + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "snippet": {
            "title": titulo[:100],
            "description": get_descricao(lang)[:4900],
            "scheduledStartTime": start,
            "defaultLanguage": "en",
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
        bc_id = res["id"]
        log(f"Broadcast criado [{lang}]: {bc_id} → {titulo[:60]}")
        # Definir categoria Music (categoryId=10) e defaultAudioLanguage=en
        # para CPM máximo em dólar — sem categoria = CPM ~30% menor
        try:
            vid_body = {
                "id": bc_id,
                "snippet": {
                    "title": titulo[:100],
                    "description": get_descricao(lang)[:4900],
                    "categoryId": "10",
                    "defaultAudioLanguage": "en"
                }
            }
            yt_call(token, "https://www.googleapis.com/youtube/v3/videos?part=snippet", vid_body, method="PUT")
            log(f"✅ Categoria Music (10) + defaultAudioLanguage=en aplicados")
        except Exception as e:
            log(f"  Categoria ignorada (não crítico): {e}")
        return bc_id
    err(f"Falha criar broadcast: {res}")
    return None

def bind_broadcast(token, bc_id, stream_id):
    url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id,contentDetails&streamId={stream_id}"
    res = yt_call(token, url)
    log(f"Bind: {bc_id} → {stream_id}")
    return res

def atualizar_broadcast(token, bc_id):
    """Atualiza título e descrição do broadcast para o idioma atual"""
    lang   = idioma_por_hora()
    titulo = TITULOS.get(lang, TITULOS["en"])
    desc   = get_descricao(lang)
    # NOTA: não incluir scheduledStartTime em broadcasts já live — causa erro 400
    body = {
        "id": bc_id,
        "snippet": {
            "title": titulo[:100],
            "description": desc[:4900],
            "defaultLanguage": lang if lang in ["en","pt","de","es","fr","it"] else "en",
        }
    }
    res = yt_call(token,
        "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet",
        body, method="PUT")
    if "id" in res:
        log(f"✅ Broadcast atualizado [{lang}]: {titulo[:60]}")
    elif "error" in res:
        # Tentar sem defaultLanguage se der erro
        body["snippet"].pop("defaultLanguage", None)
        res2 = yt_call(token,
            "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet",
            body, method="PUT")
        if "id" in res2:
            log(f"✅ Broadcast atualizado [{lang}] (sem defaultLanguage): {titulo[:60]}")
        else:
            log(f"  Aviso update: {str(res2)[:80]}")
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
# PNG COM ψ EMBUTIDO — Python puro, sem PIL, SEM depender de drawtext
# O ψ é gravado no próprio pixel (#111111 ≈ 6% brilho) → presença
# GARANTIDA em qualquer ffmpeg. Monetização nunca cai por "ψ OFF".
# ─────────────────────────────────────────────────────────────
def _psi_pixels(w, h):
    """Coordenadas (x,y) do glifo ψ centralizado, discreto."""
    # Canto inferior direito — mais discreto para usuário dormindo
    GW, GH = 28, 36
    x0, y0 = w - GW - 8, h - GH - 8
    px = set()
    for y in range(0, 38):                       # haste esquerda
        for x in range(0, 4):           px.add((x0 + x, y0 + y))
    for y in range(0, 38):                       # haste direita
        for x in range(GW - 4, GW):     px.add((x0 + x, y0 + y))
    for y in range(0, GH):                        # haste central (toda altura)
        for x in range(GW//2 - 2, GW//2 + 2): px.add((x0 + x, y0 + y))
    for y in range(34, 38):                       # base do U
        for x in range(0, GW):          px.add((x0 + x, y0 + y))
    return px

def criar_png_psi(path, w=1280, h=720, com_psi=True):
    """PNG preto com ψ embutido em #111111 (imperceptível ao olho)."""
    import struct, zlib
    def chunk(tag, d):
        crc = zlib.crc32(tag + d) & 0xFFFFFFFF
        return struct.pack('>I', len(d)) + tag + d + struct.pack('>I', crc)
    sig  = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    BLACK, PSI = b'\x00\x00\x00', b'\x11\x11\x11'
    rows = {}
    if com_psi:
        for (x, y) in _psi_pixels(w, h):
            rows.setdefault(y, set()).add(x)
    black_row = b'\x00' + BLACK * w
    raw = bytearray()
    for y in range(h):
        if y in rows:
            xs = rows[y]; r = bytearray(b'\x00')
            for x in range(w):
                r += PSI if x in xs else BLACK
            raw += r
        else:
            raw += black_row
    idat = chunk(b'IDAT', zlib.compress(bytes(raw), 6))
    with open(path, 'wb') as f:
        f.write(sig + ihdr + idat + chunk(b'IEND', b''))

# ─────────────────────────────────────────────────────────────
# FFMPEG
# ─────────────────────────────────────────────────────────────
def get_ffmpeg():
    for p in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg", "ffmpeg"]:
        try:
            if subprocess.run([p, "-version"], capture_output=True, timeout=5).returncode == 0:
                log(f"ffmpeg: {p}"); return p
        except Exception:
            pass
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe(); log(f"ffmpeg imageio: {p}"); return p
    except Exception:
        return "ffmpeg"

def preparar_fonte_video(ff):
    """Gera loop.mp4 (4s, ψ pisca 2s ON / 2s OFF) de 2 PNGs com ψ embutido.
       Retorna ('video', mp4). Se a render falhar → ('image', png_on) com ψ
       SEMPRE visível. ψ garantido nos dois casos (zero dependência de drawtext)."""
    png_on  = str(TMP / "psi_0.png")     # ψ visível
    png_off = str(TMP / "psi_1.png")     # tela preta
    criar_png_psi(png_on,  com_psi=True)
    criar_png_psi(png_off, com_psi=False)
    log("PNGs ψ ok (on/off, #111111 embutido no pixel)")

    loop_mp4 = str(TMP / "loop.mp4")
    # image2 a 0.5fps → cada PNG dura 2s → 2 frames = 4s de piscar
    cmd = [ff, "-y", "-framerate", "0.5", "-i", str(TMP / "psi_%d.png"),
           "-t", "4", "-r", "2", "-pix_fmt", "yuv420p",
           "-c:v", "libx264", "-preset", "ultrafast", "-crf", "51",
           "-b:v", "120k", "-maxrate", "160k", "-bufsize", "300k", "-g", "4",
           loop_mp4]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=60)
        if r.returncode == 0 and pathlib.Path(loop_mp4).exists() \
           and pathlib.Path(loop_mp4).stat().st_size > 1000:
            kb = pathlib.Path(loop_mp4).stat().st_size // 1024
            log(f"loop.mp4 ok: ψ PISCANDO 2s/2s ({kb}KB)")
            return ("video", loop_mp4)
        err(f"loop.mp4 falhou (rc={r.returncode}) — fallback PNG ψ fixo")
    except Exception as e:
        err(f"loop.mp4 exception: {e} — fallback PNG ψ fixo")
    return ("image", png_on)             # ψ sempre visível mesmo no fallback

def transmitir(modo, src, wav_path, ff, dur_s):
    lang = idioma_por_hora()
    if modo == "video":
        v_in = ["-re", "-stream_loop", "-1", "-i", src]
        psi = "ON (piscando, embutido)"
    else:
        v_in = ["-loop", "1", "-i", src]
        psi = "ON (fixo, embutido)"
    log(f"[{lang.upper()}] Stream {dur_s//3600}h{dur_s%3600//60}m | ψ={psi}")

    cmd = [ff, "-y"] + v_in + [
        "-re", "-stream_loop", "-1", "-i", wav_path,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "51",
        "-b:v", "120k", "-maxrate", "160k", "-bufsize", "300k",
        "-g", "4", "-r", "2", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "96k", "-ac", "2", "-ar", "44100",
        "-t", str(dur_s), "-f", "flv", RTMP,
    ]
    log(f"CMD: {' '.join(cmd[:14])}...")
    try:
        return subprocess.run(cmd, timeout=dur_s + 300).returncode
    except subprocess.TimeoutExpired:
        return -1
    except Exception as e:
        err(f"ffmpeg exception: {e}"); return -2

# ─────────────────────────────────────────────────────────────
# MAIN — ANTI-CRASH LOOP
# ─────────────────────────────────────────────────────────────
def broadcast_ativo(token):
    """Retorna qualquer broadcast reutilizável — live, ready ou upcoming."""
    for status in ["live", "active", "all"]:
        try:
            url = (f"https://www.googleapis.com/youtube/v3/liveBroadcasts"
                   f"?part=id,snippet,status&broadcastStatus={status}&maxResults=10")
            data = yt_get(token, url)
            for item in data.get("items", []):
                lc = item["status"]["lifeCycleStatus"]
                # Aceita qualquer estado ativo ou pronto para uso
                if lc in ["live", "testing", "testStarting", "liveStarting",
                           "ready", "created", "revoked"]:
                    return item["id"], item["snippet"]["title"][:60]
        except Exception:
            pass
    return None, None


def main():
    log("=" * 65)
    log(f"FULL RESET v5-STABLE | WHITE+BROWN NOISE | {datetime.now(timezone.utc):%H:%M} UTC")
    log("=" * 65)

    ff  = get_ffmpeg()

    # Gerar assets — ψ embutido no vídeo (piscando) + noise
    wav = str(TMP / "white_brown_noise.wav")
    gerar_noise_wav(wav, duration_s=30)
    modo_v, fonte_v = preparar_fonte_video(ff)
    log(f"Fonte de vídeo: modo={modo_v}")

    token = get_token()
    log("Token OK")

    stream_id = get_stream_id(token)
    if not stream_id:
        err("Stream key não encontrado!"); sys.exit(1)

    # ── POLÍTICA: 1 BROADCAST ETERNO ──────────────────────────────
    bc_id, bc_title = broadcast_ativo(token)

    if bc_id:
        log(f"✅ Broadcast já ativo: {bc_id} | {bc_title}")
        atualizar_broadcast(token, bc_id)
    else:
        log("Criando broadcast...")
        deletar_broadcasts(token, max_seconds=90)
        time.sleep(2)
        bc_id = criar_broadcast(token)
        if not bc_id:
            err("Falha criar broadcast!"); sys.exit(1)
        time.sleep(2)
        bind_broadcast(token, bc_id, stream_id)
        time.sleep(2)
        log(f"Broadcast criado: {bc_id}")

    # ── LOOP PERPÉTUO ─────────────────────────────────────────────
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

        rc = transmitir(modo_v, fonte_v, wav, ff, restante)

        if rc == 0:
            log("Stream encerrado normalmente"); break

        falhas += 1
        err(f"ffmpeg saiu com código {rc} (falha #{falhas})")

        # Renovar token a cada 10 falhas
        if falhas % 10 == 0:
            try: token = get_token(); log("Token renovado")
            except Exception as e: err(f"Token err: {e}")

        # Verificar broadcast a cada 5 falhas
        if falhas % 5 == 0:
            bc_id2, title2 = broadcast_ativo(token)
            if bc_id2:
                log(f"  Broadcast OK: {bc_id2}")
            else:
                log("  Broadcast encerrado — recriando...")
                try:
                    deletar_broadcasts(token, max_seconds=60)
                    time.sleep(2)
                    bc_id = criar_broadcast(token)
                    if bc_id:
                        time.sleep(2)
                        bind_broadcast(token, bc_id, stream_id)
                        log(f"  Novo broadcast: {bc_id}")
                except Exception as e:
                    err(f"Recriar falhou: {e}")

        espera = min(10 * falhas, 60)
        log(f"Retry em {espera}s..."); time.sleep(espera)

    log(f"TOTAL: {(time.time()-inicio)/60:.1f}min | {tentativa} tentativas | {falhas} falhas")


if __name__ == "__main__":
    main()
