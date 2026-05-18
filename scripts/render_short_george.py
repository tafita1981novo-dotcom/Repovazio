#!/usr/bin/env python3
"""
render_final_v1.py — SHORT 45-52s com AntonioNeural masculino dramático
✅ AntonioNeural PT-BR rate dinâmico por frase (-5% a -25%)
✅ ElevenLabs George como upgrade automático quando quota disponível
✅ Duração natural aceita (37-58s sem atempo forçado)
✅ Imagens semânticas Pollinations + banco por frase
"""
import os, sys, json, subprocess, requests, time, re, asyncio

VIDEO_ID = int(os.environ.get("VIDEO_ID", "683"))
SB_URL   = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY   = os.environ.get("SUPABASE_SERVICE_KEY","")
XI_KEY   = os.environ.get("ELEVENLABS_API_KEY","")
GEORGE   = "JBFqnCBsd6RMkjVDRZzb"
WORKDIR  = f"/tmp/short_{VIDEO_ID}"
os.makedirs(WORKDIR, exist_ok=True)

def log(m): print(m, flush=True)
def measure_dur(p):
    r=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",p],
        capture_output=True,text=True)
    return float(json.loads(r.stdout)["format"]["duration"])
def upscale(src,dst):
    subprocess.run(["ffmpeg","-y","-i",src,"-vf","scale=1080:1920:flags=lanczos","-q:v","2",dst],
        capture_output=True)
    return dst if os.path.exists(dst) else src
def sb_patch(id_,data):
    requests.patch(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{id_}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"},
        json=data,timeout=60)

# ── 1. SCRIPT ───────────────────────────────────────────────────────
log(f"\nψ SHORT TEASER v1 — #{VIDEO_ID}")
row = requests.get(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{VIDEO_ID}&select=id,title,script",
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=60).json()
if not row or not row[0].get("script"):
    log("❌ Script não encontrado"); sys.exit(1)

TITULO = row[0]["title"]
RAW    = row[0]["script"].strip()
log(f"  Título: {TITULO[:55]}")

def preprocess(txt):
    txt = re.sub(r'\bDr\.', 'Dr', txt)
    txt = re.sub(r'\bDra\.', 'Dra', txt)
    return txt

CLEAN = preprocess(RAW)

# ── 2. FRASES + EMOÇÃO ───────────────────────────────────────────────
paragrafos = [p.strip() for p in CLEAN.split('\n') if p.strip() and len(p.strip()) > 5]

def get_emotion(frase):
    t = frase.lower()
    if any(k in t for k in ["salva","canal","assistir","mais tarde","depois","inscreva","vídeo completo"]):
        return 0.80, 0.5
    if "quatro anos" in t and "apagando" in t: return 0.62, 1.0
    elif "quatro anos" in t: return 0.65, 0.7
    elif "apagando" in t: return 0.65, 0.5
    elif ("chora" in t and len(t) < 20): return 0.60, 0.9
    elif any(k in t for k in ["mais perigoso","não grita","não humilha"]): return 0.72, 0.3
    elif any(k in t for k in ["afastar","errada","culpada","negou","nega"]): return 0.75, 0.4
    elif "isso tem nome" in t or "isso se chama" in t: return 0.70, 0.5
    elif any(k in t for k in ["harvard","pesquisador","estudo","dr ","dra "]): return 0.82, 0.3
    elif any(k in t for k in ["sinal 1","sinal 2","sinal 3"]): return 0.78, 0.4
    elif any(k in t for k in ["nunca responsável","crítica","aprende","falar nada"]): return 0.78, 0.3
    elif any(k in t for k in ["desculpar","existir","sentir","precisar"]): return 0.74, 0.5
    elif any(k in t for k in ["não está exagerando","sensível demais","dramática"]): return 0.75, 0.3
    elif any(k in t for k in ["normalmente","anormal","reagindo"]): return 0.77, 0.3
    elif any(k in t for k in ["não era preguiça","não era frescura","não é apego"]): return 0.73, 0.3
    elif any(k in t for k in ["tem medo","medo de ser","medo de falhar"]): return 0.74, 0.4
    return 0.82, 0.15

frases = []
emocoes = []
for p in paragrafos:
    sents = re.split(r'(?<=[.!?…])\s+', p)
    for s in sents:
        s = s.strip()
        if len(s) < 18 and frases:
            frases[-1] += " " + s
            emocoes[-1] = get_emotion(frases[-1])
        elif len(s) > 3:
            frases.append(s)
            emocoes.append(get_emotion(s))

ultima = paragrafos[-1] if paragrafos else ""
if any(k in ultima.lower() for k in ["salva","canal","assistir"]) and \
   (not frases or "salva" not in frases[-1].lower()):
    frases.append(ultima.strip())
    emocoes.append(get_emotion(ultima))
if len(frases) > 16:
    frases = frases[:15] + [frases[-1]]
    emocoes = emocoes[:15] + [emocoes[-1]]

N = len(frases)
SCRIPT_TTS = " ".join(frases)
log(f"  {N} frases | {len(SCRIPT_TTS)} chars")
for i,(f,(spd,pau)) in enumerate(zip(frases,emocoes),1):
    log(f"    [{i:02d}] spd={spd:.2f} +{pau:.1f}s | {f[:52]}")

# ── 3. VOZ ───────────────────────────────────────────────────────────
log(f"\n🎤  ETAPA 1 — VOZ")
AUDIO = None
VOICE_USED = "AntonioNeural/dynamic"

# Tentar ElevenLabs George
if XI_KEY:
    try:
        r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{GEORGE}",
            headers={"xi-api-key":XI_KEY,"Content-Type":"application/json"},
            json={"text":SCRIPT_TTS,"model_id":"eleven_multilingual_v2",
                  "voice_settings":{"stability":0.20,"similarity_boost":0.85,
                                    "style":0.70,"use_speaker_boost":True,"speed":1.00}},
            timeout=180)
        if r.status_code == 200:
            AUDIO = f"{WORKDIR}/audio_george.mp3"
            with open(AUDIO,'wb') as f: f.write(r.content)
            log(f"  ✅ George ElevenLabs: {len(r.content)//1024}KB")
            VOICE_USED = "ElevenLabs/George"
        else:
            log(f"  ⚠️ ElevenLabs {r.status_code}")
    except Exception as e:
        log(f"  ⚠️ {e}")

# AntonioNeural por frase com rate dinâmico
if AUDIO is None:
    import edge_tts
    log("  🎤 AntonioNeural rate dinâmico por frase...")

    def get_rate(speed):
        pct = int((speed - 1.0) * 100)
        return f"{max(-30,min(-5,pct))}%"

    seg_paths = []

    async def gen_all():
        for idx,(frase,(speed,pause_s)) in enumerate(zip(frases,emocoes),1):
            rate = get_rate(speed)
            sp = f"{WORKDIR}/seg_{idx:03d}.mp3"
            try:
                c2 = edge_tts.Communicate(frase, voice="pt-BR-AntonioNeural", rate=rate)
                await c2.save(sp)
                d = measure_dur(sp)
                log(f"  [{idx:02d}/{N}] ✅ {d:.1f}s rate={rate} | {frase[:45]}")
                seg_paths.append(sp)
                if pause_s > 0:
                    sil = f"{WORKDIR}/sil_{idx:03d}.mp3"
                    subprocess.run(["ffmpeg","-y","-f","lavfi",
                        "-i",f"anullsrc=r=44100:cl=mono",
                        "-t",str(pause_s),"-b:a","128k",sil],capture_output=True)
                    if os.path.exists(sil): seg_paths.append(sil)
            except Exception as e:
                log(f"  [{idx:02d}/{N}] ❌ {e}")

    asyncio.run(gen_all())

    if seg_paths:
        ct = f"{WORKDIR}/cat_audio.txt"
        with open(ct,'w') as f:
            for sp in seg_paths: f.write(f"file '{sp}'\n")
        AUDIO = f"{WORKDIR}/audio_antonio.mp3"
        subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",ct,
            "-codec:a","libmp3lame","-b:a","192k",AUDIO],capture_output=True)
    else:
        async def _full():
            c3=edge_tts.Communicate(SCRIPT_TTS,voice="pt-BR-AntonioNeural",rate="-15%")
            await c3.save(f"{WORKDIR}/audio_full.mp3")
        asyncio.run(_full())
        AUDIO=f"{WORKDIR}/audio_full.mp3"

DUR_AUDIO = measure_dur(AUDIO)
log(f"  ✅ {DUR_AUDIO:.2f}s | {VOICE_USED}")

# Atempo leve apenas se fora de 37-58s
if DUR_AUDIO < 37.0:
    at = DUR_AUDIO/37.0
    adj=f"{WORKDIR}/audio_adj.mp3"
    subprocess.run(["ffmpeg","-y","-i",AUDIO,"-filter:a",f"atempo={at:.4f}","-q:a","2",adj],
        capture_output=True,timeout=60)
    if os.path.exists(adj): AUDIO=adj; DUR_AUDIO=measure_dur(AUDIO); log(f"  ⬆️ expandido: {DUR_AUDIO:.1f}s")
elif DUR_AUDIO > 58.0:
    at = DUR_AUDIO/58.0
    adj=f"{WORKDIR}/audio_adj.mp3"
    subprocess.run(["ffmpeg","-y","-i",AUDIO,"-filter:a",f"atempo={at:.4f}","-q:a","2",adj],
        capture_output=True,timeout=60)
    if os.path.exists(adj): AUDIO=adj; DUR_AUDIO=measure_dur(AUDIO); log(f"  ⬇️ comprimido: {DUR_AUDIO:.1f}s")
else:
    log(f"  ✅ Duração OK ({DUR_AUDIO:.1f}s) — sem compressão")

RATE_REAL = len(SCRIPT_TTS)/DUR_AUDIO
DURS=[max(1.2,round(len(f)/RATE_REAL,3)) for f in frases]
diff=DUR_AUDIO-sum(DURS); DURS[0]=round(DURS[0]+diff,3)

# ── 5. PROMPTS OTIMIZADOS PARA AUDIÊNCIA 72% MULHERES 25-35 BR ─────
log(f"\n🖼️  ETAPA 2 — Imagens (prompts audiência mulheres BR 25-35)")

STYLE = ("kawaii chibi anime illustration, 9:16 portrait, "
         "masterpiece, best quality, vivid expressive colors, "
         "Brazilian woman characters, relatable authentic emotions, "
         "detailed backgrounds, cinematic lighting")
NEG  = "### lowres, bad anatomy, text, watermark, nsfw, ugly, blurry, realistic, western cartoon"

# Sara otimizada para audiência BR feminina 25-35
SARA = ("female protagonist age 28, curly dark brown hair, warm olive skin, "
        "everyday clothes — yellow cardigan or simple white blouse, "
        "expressive eyes showing confusion/pain, relatable Brazilian woman look")
DANIELA = ("female psychology host age 35, dark straight bob hair, mint blouse, "
           "ψ psychology pin, confident warm authoritative expression, "
           "direct eye contact with viewer, empowering presence")
MARCOS  = ("male antagonist age 34, well-dressed navy blazer, "
           "charming disarming smile hiding manipulative intent, "
           "handsome but with cold calculating eyes, deceptive warmth")
ANA     = ("female expert Dr age 42, white coat, reading glasses, "
           "Brazilian professional appearance, scientific authority, clipboard")

def prompt_for_frase(frase, idx, N):
    t = frase.lower()
    
    # ── CTA — Teaser para vídeo completo
    if any(k in t for k in ["salva", "vídeo", "canal", "assistir", "inscreva", "mais tarde", "depois"]):
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{DANIELA} in warm inviting pose, hand extended toward viewer beckoning them closer, "
            "soft glowing screen or portal showing more content beyond, "
            "curious hopeful expression, violet golden warm light, "
            "come watch more energy, FOMO and desire to continue watching, "
            "save for later bookmark symbol subtly present "
            f"{NEG}"
        )
    
    # ── HOOK: narcisista perigoso ──
    elif "mais perigoso" in t or ("grita" in t and "humilha" in t):
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{MARCOS} shown in split-frame: left side warm friendly charming smile in bright light, "
            "right side reveals sinister cold calculating shadow-self, "
            "beautiful flowers on one side with hidden thorns revealed on other, "
            "danger disguised as love, dramatic split lighting "
            f"{NEG}"
        )
    
    # ── "Ele chora" — momento mais impactante ──
    elif "ele chora" in t or (t.strip().endswith("chora.") and len(t) < 25):
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{MARCOS} with exaggerated fake tears streaming down face, "
            "dramatic theatrical crying pose, manipulative victim act, "
            "but eyes remain cold and watching, calculating tears, "
            "performance of pain not real pain, manipulation in action "
            f"{NEG}"
        )
    
    # ── "Você é quem está errada" ──
    elif "afastar" in t or "errada" in t or "culpada" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{SARA} backing away with {MARCOS} pointing accusatory finger directly at her, "
            "wavy distorted gaslighting background effect, "
            "reality being twisted, her expression shows confusion and self-doubt, "
            "she appears smaller, he appears larger, power imbalance visible "
            f"{NEG}"
        )
    
    # ── Isso tem nome ──
    elif "isso tem nome" in t or "narcisismo encoberto" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{ANA} in research setting, "
            "holding open book with psychological term highlighted in bold, "
            "Harvard or university seal visible, revelation moment, "
            "bright discovery lighting, naming the invisible threat "
            f"{NEG}"
        )
    
    # ── Sinal 1 ──
    elif "sinal 1" in t or "nunca responsável" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            "large glowing violet number ONE floating prominently, "
            f"{MARCOS} in dramatic victim pose — hands clutched to chest, eyes wide, "
            "playing wounded, everyone around looks confused and apologetic, "
            "theatrical victimhood performance "
            f"{NEG}"
        )
    
    # ── Sinal 2 ──
    elif "sinal 2" in t or "crítica" in t or "vira crise" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            "large glowing violet number TWO floating prominently, "
            f"{SARA} carefully tiptoeing over literal eggshells drawn on floor, "
            f"{MARCOS} in background mid-dramatic-overreaction to smallest criticism, "
            "tense suffocating atmosphere, walking on eggshells literally "
            f"{NEG}"
        )
    
    # ── Nunca falar nada ──
    elif "nunca falar" in t or "magoá" in t or "aprende a" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{SARA} pressing both hands firmly over own mouth, "
            "silencing herself, eyes wide with learned fear, "
            "invisible muzzle or cage bars suggestion, self-censorship, "
            f"{MARCOS} looming in shadows causing the silence "
            f"{NEG}"
        )
    
    # ── Sinal 3 / desculpar por existir ──
    elif "sinal 3" in t or "desculpar" in t or ("sentir" in t and "precisar" in t):
        return (
            f"masterpiece, best quality, {STYLE}, "
            "large glowing violet number THREE floating prominently, "
            f"{SARA} in deeply apologetic posture — bent forward, hands pressed together, "
            "apologizing for existing, for feeling, for needing, "
            "her light visibly dimming and her presence shrinking, "
            "self-erasure in progress "
            f"{NEG}"
        )
    
    # ── Quatro anos / apagando a voz ──
    elif "quatro anos" in t or "apagando" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{SARA} body becoming translucent and ghostlike, "
            "identity slowly dissolving like watercolor washing away, "
            "4 calendar years visible in background fading into gray, "
            "voice literally shown as sound waves disappearing into nothing, "
            "years of self-erasure, maximum emotional impact "
            f"{NEG}"
        )
    
    # ── Pesquisador / dado científico ──
    elif any(k in t for k in ["harvard","pesquisador","estudo","universidade","indiana"]):
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{ANA} dramatically pointing to large statistic on board or clipboard, "
            "shocked-but-authoritative expression, research data revealed, "
            "university crest visible, blue academic lighting, "
            "scientific validation moment "
            f"{NEG}"
        )
    
    # ── Você não está exagerando ──
    elif "não está exagerando" in t or "sensível demais" in t or "dramática" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{DANIELA} in intimate close-up, making intense direct eye contact with camera viewer, "
            "hand placed gently on heart with deep compassion, "
            "warm golden healing light emanating from her presence, "
            "YOU ARE SEEN AND HEARD energy, validation and recognition moment "
            f"{NEG}"
        )
    
    # ── Reagindo normalmente ──
    elif "normalmente" in t or "anormal" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{DANIELA} with powerful protective presence, "
            "violet and golden light breaking through dark background, "
            f"{SARA} beside her with strength visibly returning, "
            "darkness lifting, identity being reclaimed, "
            "empowering hopeful healing energy "
            f"{NEG}"
        )
    
    # Fallback por posição
    elif idx <= 2:
        return f"masterpiece, best quality, {STYLE}, {DANIELA} presenting urgent psychological warning, serious direct gaze {NEG}"
    elif idx <= N//2:
        return f"masterpiece, best quality, {STYLE}, {SARA} experiencing painful emotional recognition moment, authentic Brazilian woman look {NEG}"
    else:
        return f"masterpiece, best quality, {STYLE}, {DANIELA} warm empowering expression toward camera, healing golden light {NEG}"

PROMPTS = [prompt_for_frase(f, i, N) for i, f in enumerate(frases, 1)]

# Buscar banco
banco_map = {}
try:
    rb = requests.get(f"{SB_URL}/rest/v1/image_bank?select=character_slug,scene_type,image_url&limit=300",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=60)
    for img in rb.json():
        k = f"{img['character_slug']}_{img['scene_type']}"
        banco_map.setdefault(k, []).append(img['image_url'])
    log(f"  🏦 Banco: {sum(len(v) for v in banco_map.values())} imagens")
except Exception as e:
    log(f"  ⚠️ Banco: {e}")

IMGS = []
banco_cnt = poll_cnt = 0

for idx, (frase, prompt) in enumerate(zip(frases, PROMPTS), 1):
    fpath = f"{WORKDIR}/img_{idx:02d}.jpg"
    up    = f"{WORKDIR}/img_up_{idx:02d}.jpg"
    found = False
    t = frase.lower()
    
    # Forçar Pollinations para cenas emocionais chave
    force_poll = any(k in t for k in [
        "salva","canal","assistir","mais tarde","depois",
        "inscreva","não está exagerando",
        "ele chora","mais perigoso","afastar","errada"
    ])
    
    if not force_poll:
        if "sinal 1" in t or "nunca responsável" in t: key = "marcos_problema"
        elif "sinal 2" in t or "crítica" in t: key = "sara_problema"
        elif "sinal 3" in t or "desculpar" in t: key = "sara_virada"
        elif any(k in t for k in ["harvard","estudo","pesquisador","universidade"]): key = "ana_ciencia"
        elif any(k in t for k in ["normalmente","anormal"]): key = "daniela_virada"
        else: key = None
        
        if key and banco_map.get(key):
            url = banco_map[key][(idx * 17) % len(banco_map[key])]
            try:
                r = requests.get(url, timeout=30)
                if r.status_code == 200 and len(r.content) > 5000:
                    with open(fpath,'wb') as f: f.write(r.content)
                    IMGS.append(upscale(fpath,up))
                    log(f"  [{idx:02d}/{N}] 🏦 banco/{key} | {frase[:35]}")
                    banco_cnt += 1
                    found = True
            except: pass
    
    if not found:
        seed = 7777 + idx * 191 + VIDEO_ID
        poll_url = (f"https://image.pollinations.ai/prompt/"
                    f"{requests.utils.quote(prompt)}?width=576&height=1024&seed={seed}&nologo=true")
        for att in range(4):
            try:
                r = requests.get(poll_url, timeout=90, headers={"User-Agent":"Mozilla/5.0"})
                if r.status_code == 200 and len(r.content) > 5000:
                    with open(fpath,'wb') as f: f.write(r.content)
                    IMGS.append(upscale(fpath,up))
                    log(f"  [{idx:02d}/{N}] 🌐 poll {len(r.content)//1024}KB | {frase[:35]}")
                    poll_cnt += 1
                    found = True
                    break
            except: pass
            time.sleep(4)
    
    if not found:
        IMGS.append(IMGS[-1] if IMGS else None)
        log(f"  [{idx:02d}/{N}] ⚠️ fallback")

log(f"  ✅ {banco_cnt} banco | {poll_cnt} poll | {banco_cnt+poll_cnt}/{N}")

# ── 6. RENDER ────────────────────────────────────────────────────────
log(f"\n🎬 ETAPA 3 — FFMPEG render")
OVERLAY = (
    "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
    "text='ψ @psidanielacoelho':fontcolor=white:fontsize=26:"
    "borderw=2:bordercolor=black:x=20:y=h-48"
)
concat_txt = f"{WORKDIR}/concat.txt"
with open(concat_txt,'w') as f:
    for img, dur in zip(IMGS, DURS):
        if img and os.path.exists(img):
            f.write(f"file '{img}'\nduration {dur:.3f}\n")
    if IMGS[-1] and os.path.exists(IMGS[-1]):
        f.write(f"file '{IMGS[-1]}'\n")

OUT = f"{WORKDIR}/output.mp4"
r = subprocess.run([
    "ffmpeg","-y",
    "-f","concat","-safe","0","-i",concat_txt,
    "-i",AUDIO,
    "-vf",f"{OVERLAY},format=yuv420p",
    "-c:v","libx264","-crf","22","-preset","fast",
    "-c:a","aac","-b:a","128k",
    "-shortest","-movflags","+faststart","-r","25",OUT
], capture_output=True,text=True,timeout=300)
if r.returncode != 0:
    log(f"❌ ffmpeg: {r.stderr[-300:]}"); sys.exit(1)

DUR_FINAL = measure_dur(OUT)
SZ = os.path.getsize(OUT)/1024/1024
log(f"  ✅ {DUR_FINAL:.2f}s | {SZ:.2f}MB")

# ── 7. UPLOAD ────────────────────────────────────────────────────────
log(f"\n☁️  ETAPA 4 — Upload")
ts = int(time.time())
fname = f"v{VIDEO_ID}_kokoro_{ts}.mp4"
with open(OUT,'rb') as f: data=f.read()
video_url = None
for att in range(5):
    r = requests.post(f"{SB_URL}/storage/v1/object/videos/mp4s/{fname}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"video/mp4","x-upsert":"true"},
        data=data,timeout=300)
    if r.status_code in (200,201):
        video_url = f"{SB_URL}/storage/v1/object/public/videos/mp4s/{fname}"
        log(f"  ✅ {video_url}")
        break
    log(f"  Att {att+1}: {r.status_code}"); time.sleep(15)

if video_url:
    sb_patch(VIDEO_ID, {
        "video_url": video_url, "status": "pending_credentials",
        "metadata": json.dumps({
            "dur_s": round(DUR_FINAL,1), "file_mb": round(SZ,2),
            "voice": VOICE_USED,
            "n_frases": N, "imgs_banco": banco_cnt, "imgs_poll": poll_cnt,
            "version": "kokoro_v1_dynamic_emotion",
            "audience": "72pct_women_25_35_BR"
        })
    })

log(f"\nψ RESULTADO PERFEITO:")
log(f"  ⏱️  {DUR_FINAL:.2f}s | 💾 {SZ:.2f}MB")
log(f"  🎤 {VOICE_USED} | emoção dinâmica por frase")
log(f"  🖼️  {banco_cnt} banco + {poll_cnt} Pollinations")
log(f"  🎬 {video_url or '❌ upload falhou'}")
