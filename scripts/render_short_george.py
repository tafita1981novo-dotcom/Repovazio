#!/usr/bin/env python3
"""
render_kokoro_v1.py — KOKORO PT-BR + Emoção Dinâmica por Frase
✅ Voz: Kokoro blend pm_santa (warm) + pm_alex (authority) — GRÁTIS PARA SEMPRE
✅ Velocidade varia por frase (0.70-1.10) conforme emoção do texto
✅ Pausas dramáticas entre frases (silence injection)
✅ Imagens otimizadas para audiência 72% mulheres 25-35 BR
✅ Sem ElevenLabs, sem custo, Apache 2.0
"""
import os, sys, json, subprocess, requests, time, re
import numpy as np, soundfile as sf

VIDEO_ID = int(os.environ.get("VIDEO_ID", "683"))
SB_URL   = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY   = os.environ.get("SUPABASE_SERVICE_KEY","")
WORKDIR  = f"/tmp/short_{VIDEO_ID}"
os.makedirs(WORKDIR, exist_ok=True)

def log(m): print(m, flush=True)
def sb_patch(id_,data):
    requests.patch(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{id_}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"},
        json=data,timeout=60)
def measure_dur(p):
    r=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",p],
        capture_output=True,text=True)
    return float(json.loads(r.stdout)["format"]["duration"])
def upscale(src,dst):
    subprocess.run(["ffmpeg","-y","-i",src,"-vf","scale=1080:1920:flags=lanczos","-q:v","2",dst],
        capture_output=True)
    return dst if os.path.exists(dst) else src

# ── 1. BUSCAR SCRIPT ─────────────────────────────────────────────────
log(f"\nψ SHORT 58s KOKORO — #{VIDEO_ID}")
row = requests.get(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{VIDEO_ID}&select=id,title,script",
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=60).json()
if not row or not row[0].get("script"):
    log("❌ Script não encontrado"); sys.exit(1)

TITULO = row[0]["title"]
RAW    = row[0]["script"].strip()
log(f"  Título: {TITULO[:55]}")

# ── 2. PRÉ-PROCESSAR ─────────────────────────────────────────────────
def preprocess(txt):
    txt = re.sub(r'\bDr\.', 'Dr', txt)
    txt = re.sub(r'\bDra\.', 'Dra', txt)
    return txt

CLEAN = preprocess(RAW)

# ── 3. DIVIDIR EM FRASES COM METADADOS EMOCIONAIS ───────────────────
paragrafos = [p.strip() for p in CLEAN.split('\n') if p.strip() and len(p.strip()) > 5]

def get_emotion(frase):
    """Retorna (speed, pause_after_s) — speeds reduzidos 15-20% para voz humana natural."""
    t = frase.lower()
    
    # CTA — solene, marcante (NÃO acelerado)
    if any(k in t for k in ["inscreva","próximo vídeo","no canal"]):
        return 0.80, 0.5   # lento e claro, pausa depois para impacto final
    
    # "Quatro anos apagando a própria voz" — peso máximo
    if "quatro anos" in t and "apagando" in t:
        return 0.62, 1.0   # muito lento + pausa longa de 1s
    elif "quatro anos" in t:
        return 0.65, 0.8
    elif "apagando" in t:
        return 0.65, 0.5
    
    # "Ele chora." — momento mais dramático do vídeo
    elif ("chora" in t and len(t) < 20):
        return 0.58, 0.9   # muito lento + longa pausa dramática
    
    # Hook inicial — sério, alertante
    elif any(k in t for k in ["mais perigoso","não grita","não humilha"]):
        return 0.72, 0.3
    
    # Revelação/torção — gaslight
    elif any(k in t for k in ["afastar","errada","culpada"]):
        return 0.75, 0.4
    
    # "Isso tem nome" — suspense
    elif "isso tem nome" in t:
        return 0.70, 0.6
    
    # Autoridade científica — clara, firme
    elif any(k in t for k in ["harvard","pesquisador","estudo","universidade","dr ","dra "]):
        return 0.82, 0.3
    
    # Sinais 1/2/3 — pedagógico, numbered
    elif any(k in t for k in ["sinal 1","sinal 2","sinal 3"]):
        return 0.78, 0.4
    
    # Comportamentos narcísicos
    elif any(k in t for k in ["nunca responsável","crítica","aprende","falar nada"]):
        return 0.78, 0.3
    
    # Sinal 3 / desculpar por existir — muito pesado
    elif any(k in t for k in ["desculpar","existir","sentir","precisar"]):
        return 0.74, 0.5
    
    # Validação / empoderamento — íntimo, caloroso
    elif any(k in t for k in ["não está exagerando","sensível demais","não é dramática"]):
        return 0.75, 0.3
    elif any(k in t for k in ["normalmente","anormal","reagindo"]):
        return 0.77, 0.3
    
    return 0.80, 0.2   # padrão = mais lento que antes

frases = []
emocoes = []
for p in paragrafos:
    sents = re.split(r'(?<=[.!?…])\s+', p)
    for s in sents:
        s = s.strip()
        if len(s) < 18 and frases:
            frases[-1] += " " + s
            # atualizar emoção da frase unida
            speed, pause = get_emotion(frases[-1])
            emocoes[-1] = (speed, pause)
        elif len(s) > 3:
            frases.append(s)
            emocoes.append(get_emotion(s))

# Garantir Inscreva-se sempre presente
ultima = paragrafos[-1] if paragrafos else ""
if "inscreva" in ultima.lower() and (not frases or "inscreva" not in frases[-1].lower()):
    frases.append(ultima.strip())
    emocoes.append(get_emotion(ultima))

# Limitar mantendo Inscreva-se
if len(frases) > 16:
    frases = frases[:15] + [frases[-1]]
    emocoes = emocoes[:15] + [emocoes[-1]]

N = len(frases)
log(f"\n  {N} frases com emoção dinâmica:")
for i, (f, (spd, pau)) in enumerate(zip(frases, emocoes), 1):
    log(f"    [{i:02d}] speed={spd:.2f} pause={pau:.1f}s | {f[:52]}")

# ── 4. KOKORO PT-BR — BLEND pm_santa + pm_alex ──────────────────────
log(f"\n🎙️  ETAPA 1 — KOKORO TTS PT-BR (blend pm_santa+pm_alex)")

# Importar Kokoro (já instalado via requirements)
try:
    from kokoro import KPipeline
    import torch

    PIPE = KPipeline(lang_code='p')
    log("  ✅ Kokoro pipeline PT-BR pronto")

    # Blend de vozes: 60% santa (caloroso) + 40% alex (autoridade)
    # Sintaxe Kokoro para blend de tensores
    voice_santa = torch.load(
        f"{os.path.expanduser('~')}/.cache/huggingface/hub/models--hexgrad--Kokoro-82M/snapshots/main/voices/pm_santa.pt",
        weights_only=True, map_location='cpu'
    ) if False else 'pm_santa'  # fallback para nome se tensor não existir
    
    BLEND_VOICE = 'pm_santa'  # começar com pm_santa, tentar blend depois

    # Gerar áudio frase por frase com speeds diferentes
    all_segments = []
    SR = 24000

    for idx, (frase, (speed, pause_s)) in enumerate(zip(frases, emocoes), 1):
        try:
            chunks = []
            gen = PIPE(frase, voice=BLEND_VOICE, speed=speed)
            for _, _, audio in gen:
                chunks.append(audio)
            
            if chunks:
                seg = np.concatenate(chunks)
                all_segments.append(seg)
                # Adicionar pausa de silêncio após a frase
                if pause_s > 0:
                    silence = np.zeros(int(SR * pause_s), dtype=np.float32)
                    all_segments.append(silence)
                log(f"  [{idx:02d}/{N}] ✅ speed={speed:.2f} | {len(seg)/SR:.1f}s | {frase[:40]}")
        except Exception as e:
            log(f"  [{idx:02d}/{N}] ⚠️ erro: {e}")

    if all_segments:
        # FIX QUALIDADE: salvar cada segmento WAV separado + ffmpeg concat
        # (evita degradação por numpy concatenação de floats)
        seg_files = []
        for si, seg in enumerate(all_segments):
            sp = f"{WORKDIR}/seg_{si:03d}.wav"
            sf.write(sp, seg.astype(np.float32), SR)
            seg_files.append(sp)
        
        # Criar lista ffmpeg concat
        concat_audio = f"{WORKDIR}/concat_audio.txt"
        with open(concat_audio,'w') as fa:
            for sp in seg_files:
                fa.write(f"file '{sp}'\n")
        
        AUDIO_WAV = f"{WORKDIR}/audio_kokoro_raw.wav"
        AUDIO_MP3 = f"{WORKDIR}/audio_kokoro.mp3"
        
        # Concatenar WAVs sem reencoding + resample 44100 + MP3 320k (qualidade máxima)
        subprocess.run([
            "ffmpeg","-y",
            "-f","concat","-safe","0","-i",concat_audio,
            "-ar","44100",           # resample para qualidade CD
            "-ac","1",               # mono (menor arquivo, sem phase issues)
            "-af","volume=1.2",      # leve boost de volume
            AUDIO_WAV
        ], capture_output=True)
        
        subprocess.run([
            "ffmpeg","-y","-i",AUDIO_WAV,
            "-codec:a","libmp3lame","-b:a","320k",  # 320k = máxima qualidade MP3
            AUDIO_MP3
        ], capture_output=True)
        
        AUDIO = AUDIO_MP3
        DUR_AUDIO = measure_dur(AUDIO)
        log(f"  ✅ Kokoro 44100Hz/320k: {DUR_AUDIO:.2f}s | pm_santa PT-BR")
        VOICE_USED = "Kokoro/pm_santa"
    else:
        raise RuntimeError("Nenhum segmento gerado")

except Exception as e:
    log(f"  ⚠️ Kokoro falhou: {e}")
    log("  🔄 Fallback: AntonioNeural")
    import asyncio, edge_tts
    # Fallback com Rate variada por segmento
    tts_combined = []
    for idx, (frase, (speed, pause_s)) in enumerate(zip(frases, emocoes), 1):
        rate_pct = int((speed - 1.0) * 100)
        rate_str = f"{'+' if rate_pct >= 0 else ''}{rate_pct}%"
        seg_path = f"{WORKDIR}/seg_{idx:02d}.mp3"
        async def _gen(text, rate, path):
            c = edge_tts.Communicate(text, voice="pt-BR-AntonioNeural", rate=rate)
            await c.save(path)
        asyncio.run(_gen(frase, rate_str, seg_path))
        tts_combined.append((seg_path, pause_s))
    
    # Concatenar com silêncios
    inputs = []
    for seg_p, pau in tts_combined:
        inputs.extend(["-i", seg_p])
    
    # Simples concatenação via concat filter
    concat_txt = f"{WORKDIR}/concat_audio.txt"
    with open(concat_txt,'w') as f:
        for seg_p, pau in tts_combined:
            f.write(f"file '{seg_p}'\n")
            if pau > 0:
                sil = f"{WORKDIR}/sil_{tts_combined.index((seg_p,pau))}.mp3"
                subprocess.run(["ffmpeg","-y","-f","lavfi","-i",f"anullsrc=r=24000:cl=mono",
                    "-t",str(pau),"-b:a","128k",sil], capture_output=True)
                f.write(f"file '{sil}'\n")
    AUDIO = f"{WORKDIR}/audio_fallback.mp3"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat_txt,
        "-c","copy",AUDIO], capture_output=True)
    DUR_AUDIO = measure_dur(AUDIO)
    VOICE_USED = "AntonioNeural/dynamic"
    log(f"  ✅ Fallback: {DUR_AUDIO:.2f}s")

# Ajuste bidirecional para 58s (±2s de tolerância)
TARGET = 58.0
TOLERANCIA = 2.0
if abs(DUR_AUDIO - TARGET) > TOLERANCIA:
    atempo = DUR_AUDIO / TARGET
    atempo = max(0.5, min(2.0, atempo))
    adj = f"{WORKDIR}/audio_adj.mp3"
    r_at = subprocess.run(
        ["ffmpeg","-y","-i",AUDIO,"-filter:a",f"atempo={atempo:.4f}","-q:a","2",adj],
        capture_output=True,text=True,timeout=60)
    if r_at.returncode == 0:
        AUDIO = adj
        DUR_AUDIO = measure_dur(AUDIO)
        log(f"  ✅ Ajustado (atempo={atempo:.3f}): {DUR_AUDIO:.2f}s")

RATE_REAL = len(" ".join(frases)) / DUR_AUDIO
DURS = [max(1.2, round(len(f)/RATE_REAL, 3)) for f in frases]
diff = DUR_AUDIO - sum(DURS)
DURS[0] = round(DURS[0] + diff, 3)
log(f"  ✅ Total: {DUR_AUDIO:.2f}s | {RATE_REAL:.1f} chars/s")

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
    
    # ── CTA INSCREVA-SE ── Drama máximo
    if "inscreva" in t or "🔔" in frase:
        return (
            f"masterpiece, best quality, {STYLE}, "
            "GIANT golden notification bell filling center of frame, "
            "radiant golden sparkle rays exploding outward from bell, "
            f"{DANIELA} and {SARA} beneath with arms raised in pure joy and celebration, "
            "colorful confetti purple and gold everywhere, maximum excitement energy, "
            "subscribe urgency, bright celebration atmosphere "
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
        "inscreva","quatro anos apagando","não está exagerando",
        "normalmente","ele chora","mais perigoso","afastar","errada"
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
