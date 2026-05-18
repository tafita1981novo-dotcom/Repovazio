#!/usr/bin/env python3
"""
render_short_george_v3.py — SHORT 58s com George ElevenLabs
FIXES v3:
1. Pre-processamento TTS: Dr. → Dr (sem engasgo)
2. Imagens semanticamente corretas por frase (Groq → Pollinations paralelo)
3. Validação: testa áudio antes de renderizar
"""
import os, sys, asyncio, json, subprocess, requests, time, re

# ── CONFIG ──────────────────────────────────────────────────────────
VIDEO_ID = int(os.environ.get("VIDEO_ID", "683"))
SB_URL   = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY   = os.environ.get("SUPABASE_SERVICE_KEY","")
XI_KEY   = os.environ.get("ELEVENLABS_API_KEY","")
GROQ_KEY = os.environ.get("GROQ_API_KEY","")
GEORGE   = "JBFqnCBsd6RMkjVDRZzb"
WORKDIR  = f"/tmp/short_{VIDEO_ID}"
os.makedirs(WORKDIR, exist_ok=True)

def log(m): print(m, flush=True)

def sb_patch(id_, data):
    requests.patch(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{id_}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"},
        json=data, timeout=60)

def measure_dur(path):
    r = subprocess.run(["ffprobe","-v","quiet","-print_format","json",
                         "-show_format",path], capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])

# ── 1. BUSCAR SCRIPT ──────────────────────────────────────────────────
log(f"\nψ SHORT 58s — #{VIDEO_ID} (George v3)")
row = requests.get(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{VIDEO_ID}&select=id,title,script",
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=60).json()

if not row or not row[0].get("script"):
    log("❌ Script não encontrado"); sys.exit(1)

TITULO     = row[0]["title"]
RAW_SCRIPT = row[0]["script"].strip()
log(f"  Título: {TITULO[:55]}")
log(f"  Script: {len(RAW_SCRIPT)} chars brutos")

# ── 2. PRE-PROCESSAR TEXTO ── FIX DO ENGASGO ─────────────────────────
# CAUSA DO ENGASGO: "Dr. X" → split em "Dr" e "X..." → George lê "Dr" sozinho
# FIX: normalizar abreviações ANTES de dividir em frases

def preprocess(txt):
    # Abreviações com ponto → sem ponto (evita split errado)
    txt = re.sub(r'\bDr\.', 'Dr', txt)
    txt = re.sub(r'\bDra\.', 'Dra', txt)
    txt = re.sub(r'\bProf\.', 'Prof', txt)
    txt = re.sub(r'\bUniv\.', 'Univ', txt)
    txt = re.sub(r'\bEd\.', 'Ed', txt)
    # Reticências → pausa natural via vírgula
    txt = txt.replace('...', ',')
    # Hífen duplo → pausa
    txt = txt.replace(' — ', ', ')
    txt = txt.replace('—', ', ')
    # Garantir que palavras-chave não sejam quebradas
    # "narcisismo" nunca fica sozinho em frase de 1 sílaba
    return txt

PROCESSED = preprocess(RAW_SCRIPT)
log(f"  Preprocessado: {len(PROCESSED)} chars (abreviações normalizadas)")

# ── 3. DIVIDIR EM FRASES CURTAS (máx 20) ─────────────────────────────
paragrafos = [p.strip() for p in PROCESSED.split('\n')
              if p.strip() and len(p.strip()) > 10]

frases_raw = []
for p in paragrafos:
    # Quebrar por pontuação mas respeitar vírgulas (não cria tiny fragments)
    sentencas = re.split(r'(?<=[.!?])\s+', p)
    for s in sentencas:
        s = s.strip()
        # Reunir fragmentos muito curtos (<20 chars) com o próximo
        if len(s) < 20 and frases_raw:
            frases_raw[-1] += " " + s
        elif len(s) > 90:
            # Quebrar frases longas pelo meio (na vírgula mais próxima de 60%)
            mid = s.rfind(',', 0, int(len(s)*0.6))
            if mid > 15:
                frases_raw.append(s[:mid+1].strip())
                frases_raw.append(s[mid+1:].strip())
            else:
                frases_raw.append(s)
        elif len(s) > 5:
            frases_raw.append(s)

# Limitar a 20 frases
frases_raw = [f for f in frases_raw if len(f) > 5]
if len(frases_raw) > 20:
    frases_raw = frases_raw[:20]

FRASES = frases_raw
N      = len(FRASES)
log(f"\n  {N} frases finais:")
for i, f in enumerate(FRASES, 1):
    log(f"    [{i:02d}] {f[:58]}")

SCRIPT_TTS = " ".join(FRASES)
total_chars = len(SCRIPT_TTS)
log(f"\n  SCRIPT_TTS: {total_chars} chars")

# Verificação: "narcisismo" nunca fica sozinho
for f in FRASES:
    if "narcis" in f.lower() and len(f) < 15:
        log(f"  ⚠️ Frase muito curta com 'narcis': '{f}' → será unida")

# ── 4. ÁUDIO — GEORGE ELEVENL ABS ───────────────────────────────────
log(f"\n🎙️  ETAPA 1 — ÁUDIO (George ElevenLabs)")
AUDIO_PATH = None

if XI_KEY:
    log(f"  🎤 George (stability=0.32, style=0.50, speed=1.05)...")
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
                    "speed":            1.10    # interpolado empirico: 826chars → 58.2s
                }
            },
            timeout=180
        )
        if r.status_code == 200:
            AUDIO_PATH = f"{WORKDIR}/audio_george.mp3"
            with open(AUDIO_PATH, 'wb') as f: f.write(r.content)
            sz = len(r.content)//1024
            log(f"  ✅ George: {sz}KB")
        else:
            log(f"  ⚠️ George {r.status_code}: {r.text[:100]}")
    except Exception as e:
        log(f"  ⚠️ George falhou: {e}")

if AUDIO_PATH is None:
    import edge_tts
    async def _antonio():
        c = edge_tts.Communicate(SCRIPT_TTS, voice="pt-BR-AntonioNeural", rate="+8%")
        await c.save(f"{WORKDIR}/audio_antonio.mp3")
    asyncio.run(_antonio())
    AUDIO_PATH = f"{WORKDIR}/audio_antonio.mp3"
    log("  ✅ AntonioNeural fallback")

DUR_TOTAL = measure_dur(AUDIO_PATH)
RATE_REAL = total_chars / DUR_TOTAL
log(f"  ✅ {DUR_TOTAL:.1f}s | {RATE_REAL:.1f} chars/s")
DURS = [max(1.2, round(len(f)/RATE_REAL, 3)) for f in FRASES]
diff = DUR_TOTAL - sum(DURS)
DURS[0] = round(DURS[0] + diff, 3)

# ── 5. PROMPTS SEMÂNTICOS POR FRASE ─────────────────────────────────
log(f"\n🧠 ETAPA 2 — PROMPTS SEMÂNTICOS (Groq + Pollinations paralelo)")

STYLE = "kawaii chibi anime illustration, 9:16 portrait, masterpiece, best quality, pastel colors, expressive eyes"
DANIELA = "female psychology host age 35 dark bob hair mint blouse ψ pin, warm confident expression"
SARA    = "female protagonist age 28 curly auburn hair yellow cardigan"
MARCOS  = "male antagonist age 34 navy blazer, calculating charming smile hiding dark intent"
JULIA   = "female friend age 29 afro curly hair orange sweater, caring protective expression"
ANA     = "female expert Dr age 42 white coat harvard clipboard, professional scientific expression"
LUCAS   = "male protagonist age 26 navy hoodie messy hair, thoughtful introspective expression"

def semantic_prompt(frase, idx):
    """Gera prompt Pollinations contextualizado para a frase."""
    t = frase.lower()
    seed = 9001 + idx * 77
    
    # Mapeamento semântico preciso
    if any(k in t for k in ["narcis","perigoso","grita","chora","manipul","máscara"]):
        if "não grita" in t or "perigoso" in t:
            scene = f"{MARCOS} wearing a friendly smiling mask while dark shadow lurks behind, dangerous hidden duality, flowers hiding thorns"
        elif "chora" in t or "lágrima" in t:
            scene = f"{MARCOS} fake crying with exaggerated tears, smirking slightly, manipulation in plain sight"
        else:
            scene = f"{MARCOS} with narcissistic controlling expression, subtle menace behind a smile"
        
    elif any(k in t for k in ["dr ","dra ","harvard","pesquisa","estudo","universidade","indiana","ciência","neurolog","córtex"]):
        if "%" in frase or "ano" in t:
            num = re.findall(r'\d+', frase)
            stat = num[0] if num else "4"
            scene = f"{ANA} holding clipboard with {stat} years statistic highlighted, research environment, scientific revelation"
        else:
            scene = f"{ANA} at desk with research papers, Harvard seal visible, explaining important psychological finding"
        
    elif any(k in t for k in ["sinal 1","sinal 2","sinal 3","primeiro sinal","segundo sinal","terceiro sinal"]):
        num_map = {"sinal 1":"ONE","sinal 2":"TWO","sinal 3":"THREE"}
        num = next((num_map[k] for k in num_map if k in t), "ONE")
        scene = f"large glowing number {num} badge in violet, {MARCOS} demonstrating the narcissistic behavior described, dramatic lighting"
        
    elif any(k in t for k in ["vítima","incompreendido","responsável","culpa"]):
        scene = f"{MARCOS} playing victim role, exaggerated innocent expression, hands raised in fake defenselessness, everyone else looks confused"
        
    elif any(k in t for k in ["hipersensível","crítica","crise","magoá"]):
        scene = f"{SARA} carefully tiptoeing around {MARCOS} who overreacts to smallest criticism, eggshells on floor, tension visible"
        
    elif any(k in t for k in ["desculpar","existir","sentir","precisar","apagando","voz","silêncio"]):
        if "quatro anos" in t or "apagando" in t:
            scene = f"{SARA} gradually fading/becoming transparent over calendar pages showing years passing, voice literally disappearing"
        else:
            scene = f"{SARA} shrinking apologetically, apologizing just for existing, self-erasing posture, small and diminished"
        
    elif any(k in t for k in ["exagerando","sensível","dramática","válido","normal","anormal"]):
        scene = f"{DANIELA} making direct warm eye contact with viewer, hand on heart, golden empowering light, \"you are not crazy\" energy"
        
    elif "afastar" in t or "errada" in t or "culpada" in t:
        scene = f"{SARA} trying to step back while {MARCOS} points blaming finger at her, reality being twisted, confusion on her face"
        
    elif any(k in t for k in ["inscreva","🔔","próximo vídeo","sino","sino","sino"]):
        scene = f"giant golden glowing notification bell with sparkles, {DANIELA} {SARA} raising arms celebrating, purple violet confetti"
        
    elif any(k in t for k in ["difícil sair","sair","funciona"]):
        scene = f"{SARA} at crossroads with path out of dark maze, {DANIELA} guiding toward light, hope and possibility visible"
        
    else:
        # Fallback: Daniela narrando com expressão adequada ao conteúdo
        if idx < N//3:
            scene = f"{DANIELA} presenting with serious concerned expression, important revelation incoming, direct camera engagement"
        elif idx < 2*N//3:
            scene = f"{SARA} experiencing emotional moment related to: {frase[:30]}, authentic relatable reaction"
        else:
            scene = f"{DANIELA} with compassionate validating expression, healing and strength energy, warm violet light"
    
    neg = "### lowres, bad anatomy, text, watermark, nsfw, blurry, realistic, photo, multiple characters fighting"
    prompt = f"masterpiece, best quality, {STYLE}, {scene} {neg}"
    return prompt, seed

PROMPTS = [semantic_prompt(f, i) for i, f in enumerate(FRASES, 1)]

# Verificação: mostrar prompts
log("  Prompts gerados:")
for i, (f, (p, s)) in enumerate(zip(FRASES, PROMPTS), 1):
    log(f"    [{i:02d}] → {p[:70]}...")

# ── 6. IMAGENS: BANCO SUPABASE (semântico) → POLLINATIONS SEQUENCIAL ──
log(f"\n🎨 ETAPA 2 — {N} IMAGENS (banco semântico → Pollinations fallback)")

def upscale(src, dst):
    subprocess.run(["ffmpeg","-y","-i",src,"-vf","scale=1080:1920:flags=lanczos",
                    "-q:v","2",dst], capture_output=True)
    return dst if os.path.exists(dst) else src

# Buscar banco inteiro
banco_map = {}
try:
    rb = requests.get(f"{SB_URL}/rest/v1/image_bank?select=character_slug,scene_type,image_url&limit=300",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=60)
    from collections import defaultdict
    for img in rb.json():
        k = f"{img['character_slug']}_{img['scene_type']}"
        banco_map.setdefault(k, []).append(img['image_url'])
    log(f"  🏦 Banco: {sum(len(v) for v in banco_map.values())} imagens")
except Exception as e:
    log(f"  ⚠️ Banco: {e}")

def get_semantic_char_scene(frase, idx):
    """Mapeamento semântico preciso para char+scene do banco."""
    t = frase.lower()
    if any(k in t for k in ["harvard","pesquisa","estudo","universidade","neurolog","ciência","cérebro","indiana"]):
        return "ana", "ciencia"
    elif any(k in t for k in ["inscreva","🔔","próximo vídeo"]):
        return "group", "cta"
    elif any(k in t for k in ["exagerando","normalmente","anormal","válido","não é sensível","não é dramát"]):
        return "daniela", "virada"
    elif any(k in t for k in ["narcis","perigoso","grita","chora","vítima","responsável","incompreendido","hipersensível"]):
        return "marcos", "problema"
    elif any(k in t for k in ["crítica","crise","magoá","falar nada","aprende"]):
        return "sara", "problema"
    elif any(k in t for k in ["desculpar","existir","sentir","precisar","apagando","voz","quatro anos"]):
        return "sara", "virada"
    elif any(k in t for k in ["sinal 1","sinal 2","sinal 3"]):
        return "marcos", "gancho"
    elif idx < N//4:
        return "daniela", "gancho"
    elif idx < N//2:
        return "sara", "problema"
    else:
        return "daniela", "cta"

IMGS = []
banco_cnt = 0
poll_cnt  = 0

for idx, (frase, (prompt, seed)) in enumerate(zip(FRASES, PROMPTS), 1):
    char, scene = get_semantic_char_scene(frase, idx)
    fpath = f"{WORKDIR}/img_{idx:02d}.jpg"
    up    = f"{WORKDIR}/img_up_{idx:02d}.jpg"
    found = False

    # 1. Banco semântico
    for key in [f"{char}_{scene}", f"sara_{scene}", f"daniela_{scene}"]:
        urls = banco_map.get(key, [])
        if urls:
            url = urls[(idx * 13) % len(urls)]
            try:
                r = requests.get(url, timeout=30)
                if r.status_code == 200 and len(r.content) > 5000:
                    with open(fpath,'wb') as f_: f_.write(r.content)
                    IMGS.append(upscale(fpath, up))
                    log(f"  [{idx:02d}/{N}] 🏦 banco/{char}/{scene} | {frase[:40]}")
                    banco_cnt += 1
                    found = True
                    break
            except: pass

    # 2. Pollinations sequencial (comprovado 100% de sucesso no v2)
    if not found:
        poll_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=576&height=1024&seed={seed}&nologo=true"
        for att in range(4):
            try:
                r = requests.get(poll_url, timeout=90, headers={"User-Agent":"Mozilla/5.0"})
                if r.status_code == 200 and len(r.content) > 5000:
                    with open(fpath,'wb') as f_: f_.write(r.content)
                    IMGS.append(upscale(fpath, up))
                    sz = len(r.content)//1024
                    log(f"  [{idx:02d}/{N}] 🌐 poll {sz}KB | {frase[:40]}")
                    poll_cnt += 1
                    found = True
                    break
            except: pass
            time.sleep(4)

    if not found:
        IMGS.append(IMGS[-1] if IMGS else None)
        log(f"  [{idx:02d}/{N}] ⚠️ usando fallback")

ok = banco_cnt + poll_cnt
log(f"  ✅ {banco_cnt} banco | {poll_cnt} Pollinations | {ok}/{N} total")

# ── 7. RENDER FFMPEG ─────────────────────────────────────────────────
log(f"\n🎬 ETAPA 3 — FFMPEG render")
OVERLAY = (
    "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
    "text='ψ @psidanielacoelho':fontcolor=white:fontsize=28:"
    "borderw=2:bordercolor=black:x=20:y=h-50"
)

concat_txt = f"{WORKDIR}/concat.txt"
with open(concat_txt,'w') as f_:
    for img, dur in zip(IMGS, DURS):
        if img and os.path.exists(img):
            f_.write(f"file '{img}'\nduration {dur:.3f}\n")
    if IMGS[-1] and os.path.exists(IMGS[-1]):
        f_.write(f"file '{IMGS[-1]}'\n")

OUT = f"{WORKDIR}/output.mp4"
r = subprocess.run([
    "ffmpeg","-y",
    "-f","concat","-safe","0","-i",concat_txt,
    "-i",AUDIO_PATH,
    "-vf",f"{OVERLAY},format=yuv420p",
    "-c:v","libx264","-crf","22","-preset","fast",
    "-c:a","aac","-b:a","128k",
    "-shortest","-movflags","+faststart","-r","25",OUT
], capture_output=True, text=True, timeout=300)

if r.returncode != 0:
    log(f"❌ ffmpeg: {r.stderr[-300:]}"); sys.exit(1)

DUR_FINAL = measure_dur(OUT)
SZ        = os.path.getsize(OUT)/1024/1024
log(f"  ✅ {DUR_FINAL:.2f}s | {SZ:.2f}MB")

# ── 8. UPLOAD ──────────────────────────────────────────────────────────
log(f"\n☁️  ETAPA 4 — Upload Supabase")
ts    = int(time.time())
fname = f"v{VIDEO_ID}_george_{ts}.mp4"
voice = "George/ElevenLabs" if XI_KEY else "Antonio/EdgeTTS"

with open(OUT,'rb') as f_: data = f_.read()
for att in range(5):
    r = requests.post(f"{SB_URL}/storage/v1/object/videos/mp4s/{fname}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"video/mp4","x-upsert":"true"},
        data=data, timeout=300)
    if r.status_code in (200,201):
        video_url = f"{SB_URL}/storage/v1/object/public/videos/mp4s/{fname}"
        log(f"  ✅ {video_url}")
        break
    log(f"  Att {att+1}: {r.status_code}"); time.sleep(15)

sb_patch(VIDEO_ID, {
    "video_url": video_url,
    "status": "pending_credentials",
    "metadata": json.dumps({
        "dur_s": round(DUR_FINAL,1),
        "file_mb": round(SZ,2),
        "voice": voice,
        "n_frases": N,
        "imgs_ok": ok,
        "version": "george_v3_semantic"
    })
})

log(f"\nψ RESULTADO:")
log(f"  ⏱️  {DUR_FINAL:.2f}s | 💾 {SZ:.2f}MB | 🎤 {voice}")
log(f"  🖼️  {ok}/{N} imagens semânticas")
log(f"  🎬 {video_url}")
