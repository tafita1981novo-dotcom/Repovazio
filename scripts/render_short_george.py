#!/usr/bin/env python3
"""
render_short_george.py — SHORT 58s com George ElevenLabs
Lê script do Supabase, usa George para voz, Pollinations para imagens.
"""
import os, sys, asyncio, json, subprocess, requests, time, math, re

# ── CONFIG ───────────────────────────────────────────────────────────────
VIDEO_ID = int(os.environ.get("VIDEO_ID", "683"))
SB_URL   = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY   = os.environ.get("SUPABASE_SERVICE_KEY","")
XI_KEY   = os.environ.get("ELEVENLABS_API_KEY","")
GROQ_KEY = os.environ.get("GROQ_API_KEY","")
GEORGE   = "JBFqnCBsd6RMkjVDRZzb"
WORKDIR  = f"/tmp/short_{VIDEO_ID}"
os.makedirs(WORKDIR, exist_ok=True)

def log(m): print(m, flush=True)

def sb_get(q):
    r=requests.get(f"{SB_URL}/rest/v1/{q}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"},timeout=60)
    return r.json()

def sb_patch(id_,data):
    requests.patch(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{id_}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=minimal"},
        json=data,timeout=60)

def measure_dur(path):
    r=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",path],
        capture_output=True,text=True)
    return float(json.loads(r.stdout)["format"]["duration"])

# ── 1. BUSCAR SCRIPT DO SUPABASE ─────────────────────────────────────────
log(f"ψ SHORT 58s — #{ VIDEO_ID}")
row = sb_get(f"content_pipeline?id=eq.{VIDEO_ID}&select=id,title,script,topic")
if not row or not row[0].get("script"):
    log(f"❌ Script não encontrado para #{VIDEO_ID}"); sys.exit(1)

row = row[0]
TITULO = row["title"]
RAW_SCRIPT = row["script"].strip()
log(f"  Título: {TITULO[:50]}")
log(f"  Script: {len(RAW_SCRIPT)} chars")

# ── 2. DIVIDIR SCRIPT EM FRASES CURTAS ──────────────────────────────────
# Dividir por parágrafo/frase, filtrar curtas, manter ~20 frases
paragrafos = [p.strip() for p in RAW_SCRIPT.split('\n') if p.strip() and len(p.strip())>10]
# Quebrar frases longas (>80 chars) em menores
frases_raw = []
for p in paragrafos:
    sentencas = re.split(r'(?<=[.!?])\s+', p)
    for s in sentencas:
        s = s.strip()
        if len(s) > 90:
            # Quebrar em meio
            mid = s.rfind(',', 0, 70)
            if mid > 20:
                frases_raw.append(s[:mid+1].strip())
                frases_raw.append(s[mid+1:].strip())
            else:
                frases_raw.append(s[:65].strip() + '...')
                frases_raw.append('...' + s[65:].strip())
        elif len(s) > 10:
            frases_raw.append(s)

# Limitar a 20 frases (target YouTube Shorts)
frases_raw = [f for f in frases_raw if len(f) > 8]
if len(frases_raw) > 20:
    frases_raw = frases_raw[:20]
elif len(frases_raw) < 10:
    log(f"  ⚠️  Poucas frases ({len(frases_raw)}) — usando parágrafos inteiros")

FRASES = frases_raw
N = len(FRASES)
log(f"  Frases geradas: {N}")
for i, f in enumerate(FRASES, 1):
    log(f"    [{i:02d}] {f[:55]}")

# Script TTS = frases unidas naturalmente (sem ponto duplo)
SCRIPT_TTS = " ".join(FRASES)
total_chars = len(SCRIPT_TTS)
log(f"  SCRIPT_TTS: {total_chars} chars")

# ── 3. GERAR ÁUDIO — GEORGE ou ANTONIO ───────────────────────────────────
log(f"\n🎙️  ETAPA 1 — ÁUDIO")
AUDIO_PATH = None

if XI_KEY:
    log(f"  🎤 George ElevenLabs (stability=0.32,style=0.50,speed=0.92)...")
    try:
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{GEORGE}",
            headers={"xi-api-key": XI_KEY, "Content-Type": "application/json"},
            json={
                "text": SCRIPT_TTS,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability":        0.32,
                    "similarity_boost": 0.85,
                    "style":            0.50,
                    "use_speaker_boost": True,
                    "speed":            1.05    # 882 chars → ~59s (target 58-60s)
                }
            },
            timeout=180
        )
        if r.status_code == 200:
            AUDIO_PATH = f"{WORKDIR}/audio_george.mp3"
            with open(AUDIO_PATH,'wb') as f: f.write(r.content)
            sz = len(r.content)//1024
            log(f"  ✅ George: {sz}KB")
        else:
            log(f"  ⚠️  George erro {r.status_code}: {r.text[:120]}")
    except Exception as e:
        log(f"  ⚠️  George falhou: {e}")

if AUDIO_PATH is None:
    log("  🎙️  AntonioNeural (+8% rate — fallback)...")
    import edge_tts
    async def _antonio():
        c=edge_tts.Communicate(SCRIPT_TTS,voice="pt-BR-AntonioNeural",rate="+8%")
        await c.save(f"{WORKDIR}/audio_antonio.mp3")
    asyncio.run(_antonio())
    AUDIO_PATH = f"{WORKDIR}/audio_antonio.mp3"
    log(f"  ✅ AntonioNeural OK")

DUR_TOTAL = measure_dur(AUDIO_PATH)
RATE_REAL = total_chars / DUR_TOTAL
log(f"  ✅ Duração: {DUR_TOTAL:.2f}s | taxa: {RATE_REAL:.1f} chars/s")

# Duração de cada frase proporcional ao número de chars
DURS = [max(1.5, round(len(f)/RATE_REAL, 3)) for f in FRASES]
# Ajustar para somar exatamente DUR_TOTAL
diff = DUR_TOTAL - sum(DURS)
DURS[0] += diff  # ajuste no primeiro frame

# ── 4. GERAR PROMPTS (Groq) E IMAGENS (Pollinations) ────────────────────
# Personagens
STYLE   = "kawaii chibi anime illustration, 9:16 vertical portrait, masterpiece, best quality, pastel colors, detailed expressive eyes, no text"
DANIELA = "female psychology host age 35 dark bob hair mint blouse ψ pin"
SARA    = "female protagonist age 28 curly auburn hair yellow cardigan"
MARCOS  = "male antagonist age 34 navy blazer calculating smile"
JULIA   = "female friend age 29 afro curly hair orange sweater"
ANA     = "female expert Dr age 42 white coat harvard clipboard"

# Mapear personagens por conteúdo da frase
def get_char(frase):
    t = frase.lower()
    if any(k in t for k in ["daniela","pergunta","inscreva","próximo","você está","você não"]):
        return DANIELA
    elif any(k in t for k in ["dr.","dra.","ana","pesquisa","harvard","estudo","ciência","neurologia","córtex"]):
        return ANA
    elif any(k in t for k in ["julia","amiga","disse a sara","disse pra sara"]):
        return JULIA
    elif any(k in t for k in ["marcos","narcis","ele chegava","ele disse","sinal 1","sinal 2","sinal 3"]):
        return MARCOS
    else:
        return SARA

def make_prompt(frase, idx):
    char = get_char(frase)
    t = frase.lower()
    # Cena contextual
    if "sinal 1" in t or "sinal 2" in t or "sinal 3" in t:
        n = frase[6] if len(frase) > 6 and frase[5] == ' ' else "1"
        scene = f"large glowing number {n} badge floating, {MARCOS} with typical narcissistic expression"
    elif "inscreva" in t or "🔔" in frase or "próximo vídeo" in t:
        scene = f"giant golden glowing notification bell with sparkles, {DANIELA} {SARA} celebrating together, colorful confetti"
    elif "harvard" in t or "pesquisa" in t or "estudo" in t or "%" in frase:
        num = re.findall(r'\d+%?', frase)
        stat = num[0] if num else "important"
        scene = f"{ANA} holding clipboard showing {stat} statistic, professional research environment"
    elif "cérebro" in t or "neurologia" in t or "córtex" in t:
        scene = f"{ANA} pointing at glowing brain diagram, neural pathways illuminated, scientific explanation"
    elif "chora" in t or "chorar" in t:
        scene = f"{SARA} with visible tears, emotional expression, soft sad lighting"
    elif "culpa" in t or "desculpa" in t:
        scene = f"{SARA} in apologetic pose, guilty expression, heavy weight on shoulders"
    elif "normal" in t or "válido" in t or "não está exagerando" in t:
        scene = f"{DANIELA} making direct eye contact with viewer, warm golden light, hand on heart, empowering"
    else:
        scene = f"{char} in emotional scene related to: {frase[:40]}"
    
    return f"masterpiece, best quality, kawaii chibi anime illustration, {scene} ### lowres, bad anatomy, text, watermark, nsfw, blurry, realistic"

PROMPTS = [make_prompt(f, i) for i, f in enumerate(FRASES, 1)]

# ── ETAPA 2: IMAGENS — banco Supabase (rápido) → fallback Pollinations ──────
log(f"\n🎨 ETAPA 2 — {N} IMAGENS (banco → Pollinations fallback)")

def upscale(src, dst):
    subprocess.run(["ffmpeg","-y","-i",src,"-vf","scale=1080:1920:flags=lanczos","-q:v","2",dst],
        capture_output=True)
    return dst

# Buscar imagens do banco Supabase
CHARS_CYCLE = ["daniela","sara","marcos","julia","ana","lucas","group"]
banco_imgs = {}
try:
    r_banco = requests.get(f"{SB_URL}/rest/v1/image_bank?select=character_slug,scene_type,image_url&limit=200",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"},timeout=60)
    banco = r_banco.json()
    # Organizar por char+scene
    from collections import defaultdict
    banco_map = defaultdict(list)
    for img in banco:
        k = f"{img['character_slug']}_{img['scene_type']}"
        banco_map[k].append(img['image_url'])
    log(f"  🏦 Banco: {len(banco)} imagens disponíveis")
except Exception as e:
    log(f"  ⚠️ Banco falhou: {e}")
    banco_map = {}

def get_char_scene_for_frase(frase, idx):
    char = CHARS_CYCLE[idx % len(CHARS_CYCLE)]
    t = frase.lower()
    if "inscreva" in t or "🔔" in frase: scene = "cta"
    elif "sinal 1" in t or "sinal 2" in t or "sinal 3" in t: scene = "problema"
    elif "harvard" in t or "pesquisa" in t or "dra." in t or "dr." in t: scene = "ciencia"
    elif "não está" in t or "você está" in t or "normalmente" in t: scene = "virada"
    else: scene = ["gancho","problema","ciencia","virada"][idx % 4]
    return char, scene

IMGS = []
banco_used = 0
poll_used  = 0

for idx, (frase, prompt) in enumerate(zip(FRASES, PROMPTS), 1):
    char, scene = get_char_scene_for_frase(frase, idx-1)
    fpath = f"{WORKDIR}/img_{idx:02d}.jpg"
    up    = f"{WORKDIR}/img_up_{idx:02d}.jpg"

    # 1. Tentar banco
    found = False
    for key in [f"{char}_{scene}", f"sara_{scene}", f"daniela_{scene}"]:
        urls = banco_map.get(key, [])
        if urls:
            url = urls[(idx * 7) % len(urls)]
            try:
                r=requests.get(url,timeout=30)
                if r.status_code==200 and len(r.content)>5000:
                    with open(fpath,'wb') as f_: f_.write(r.content)
                    IMGS.append(upscale(fpath, up))
                    sz = len(r.content)//1024
                    log(f"  [{idx:02d}/{N}] 🏦 {sz}KB banco/{char}/{scene} | {frase[:35]}")
                    banco_used += 1
                    found = True
                    break
            except: pass

    # 2. Fallback Pollinations (apenas se banco falhou)
    if not found:
        seed = 9001 + idx * 77
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=576&height=1024&seed={seed}&nologo=true"
        try:
            r=requests.get(url,timeout=90,headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code==200 and len(r.content)>5000:
                with open(fpath,'wb') as f_: f_.write(r.content)
                IMGS.append(upscale(fpath, up))
                sz = len(r.content)//1024
                log(f"  [{idx:02d}/{N}] 🌐 {sz}KB poll | {frase[:35]}")
                poll_used += 1
                found = True
        except Exception as e:
            log(f"  [{idx:02d}/{N}] ❌ {e}")

    if not found and IMGS:
        IMGS.append(IMGS[-1])  # reusar última

log(f"  ✅ {banco_used} banco | {poll_used} Pollinations | total {len(IMGS)}")

# Usar imagem placeholder para falhas
IMGS = [p or IMGS[0] for p in IMGS]

# ── 5. RENDER FFMPEG ───────────────────────────────────────────────────────
log(f"\n🎬 ETAPA 3 — FFMPEG render")
# Overlay: ψ badge + @psidanielacoelho
OVERLAY = (
    "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
    "text='ψ @psidanielacoelho':"
    "fontcolor=white:fontsize=28:borderw=2:bordercolor=black:"
    "x=20:y=h-50"
)

# ffconcat
concat_txt = f"{WORKDIR}/concat.txt"
with open(concat_txt,'w') as f_:
    for img, dur in zip(IMGS, DURS):
        f_.write(f"file '{img}'\n")
        f_.write(f"duration {dur:.3f}\n")
    f_.write(f"file '{IMGS[-1]}'\n")

OUT = f"{WORKDIR}/output.mp4"
r = subprocess.run([
    "ffmpeg","-y",
    "-f","concat","-safe","0","-i",concat_txt,
    "-i",AUDIO_PATH,
    "-vf",f"{OVERLAY},format=yuv420p",
    "-c:v","libx264","-crf","22","-preset","fast",
    "-c:a","aac","-b:a","128k",
    "-shortest","-movflags","+faststart",
    "-r","25",OUT
], capture_output=True, text=True, timeout=300)

if r.returncode!=0:
    log(f"❌ ffmpeg erro: {r.stderr[-300:]}")
    sys.exit(1)

DUR_FINAL = measure_dur(OUT)
SZ = os.path.getsize(OUT)/1024/1024
log(f"  ✅ {DUR_FINAL:.2f}s | {SZ:.2f}MB")

# ── 6. UPLOAD SUPABASE ────────────────────────────────────────────────────
log(f"\n☁️  ETAPA 4 — Upload")
ts = int(time.time())
fname = f"v{VIDEO_ID}_george_{ts}.mp4"
with open(OUT,'rb') as f_: data=f_.read()

for att in range(5):
    r=requests.post(f"{SB_URL}/storage/v1/object/videos/mp4s/{fname}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"video/mp4","x-upsert":"true"},
        data=data,timeout=300)
    if r.status_code in (200,201):
        video_url = f"{SB_URL}/storage/v1/object/public/videos/mp4s/{fname}"
        log(f"  ✅ {video_url}")
        break
    log(f"  Att {att+1}: {r.status_code}")
    time.sleep(15)

sb_patch(VIDEO_ID,{
    "video_url": video_url,
    "status": "pending_credentials",
    "metadata": json.dumps({
        "dur_s":DUR_TOTAL,"file_mb":round(SZ,2),
        "voice":"George/ElevenLabs" if XI_KEY else "Antonio/EdgeTTS",
        "n_frases":N,"version":"george_v1"
    })
})

log(f"\nψ RESULTADO FINAL:")
log(f"  Duração: {DUR_FINAL:.2f}s | Tamanho: {SZ:.2f}MB")
log(f"  Voz: {'George ElevenLabs ✨' if XI_KEY else 'AntonioNeural +8%'}")
log(f"  🎬 {video_url}")
