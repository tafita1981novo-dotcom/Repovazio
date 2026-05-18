#!/usr/bin/env python3
"""
render_xtts_george.py — XTTS v2 clonando a voz do George ElevenLabs
✅ Voz masculina idêntica ao George — clonagem de 14s de referência
✅ PT-BR nativo via XTTS v2 (Coqui) — grátis para sempre
✅ Emoção dinâmica por frase via velocidades e pausas
✅ Qualidade 22050Hz → 44100Hz 320k MP3
"""
import os, sys, json, subprocess, requests, time, re
import numpy as np, soundfile as sf

VIDEO_ID = int(os.environ.get("VIDEO_ID", "683"))
SB_URL   = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY   = os.environ.get("SUPABASE_SERVICE_KEY","")
XI_KEY   = os.environ.get("ELEVENLABS_API_KEY","")
GEORGE   = "JBFqnCBsd6RMkjVDRZzb"
WORKDIR  = f"/tmp/short_{VIDEO_ID}"
os.makedirs(WORKDIR, exist_ok=True)

# URL de referência George (vídeo render com voz original)
GEORGE_REF_VIDEO = "https://tpjvalzwkqwttvmszvie.supabase.co/storage/v1/object/public/videos/mp4s/v683_george_1779065193.mp4"
GEORGE_REF_WAV   = f"{WORKDIR}/george_ref.wav"

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

# ── 1. BUSCAR SCRIPT ─────────────────────────────────────────────────
log(f"\nψ SHORT 60s XTTS v2 GEORGE CLONE — #{VIDEO_ID}")
row = requests.get(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{VIDEO_ID}&select=id,title,script",
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=60).json()
if not row or not row[0].get("script"):
    log("❌ Script não encontrado"); sys.exit(1)

TITULO = row[0]["title"]
RAW    = row[0]["script"].strip()
log(f"  Título: {TITULO[:55]}")

# ── 2. EXTRAIR REFERÊNCIA GEORGE ─────────────────────────────────────
log(f"\n🎙️  ETAPA 0 — Extraindo referência de voz George")
if not os.path.exists(GEORGE_REF_WAV):
    log("  Baixando render George original...")
    r = requests.get(GEORGE_REF_VIDEO, timeout=120, headers={"User-Agent":"Mozilla/5.0"})
    if r.status_code == 200:
        src_video = f"{WORKDIR}/george_src.mp4"
        with open(src_video,'wb') as f: f.write(r.content)
        subprocess.run([
            "ffmpeg","-y","-i",src_video,
            "-ss","2","-t","14",
            "-vn","-ar","22050","-ac","1",
            "-af","highpass=f=80,lowpass=f=8000,volume=1.3",
            GEORGE_REF_WAV
        ], capture_output=True)
        dur_ref = measure_dur(GEORGE_REF_WAV)
        log(f"  ✅ Referência George: {dur_ref:.1f}s @ 22050Hz")
    else:
        log(f"  ❌ Falha ao baixar referência: {r.status_code}")
        sys.exit(1)
else:
    log("  ✅ Referência George em cache")

# ── 3. PRÉ-PROCESSAR SCRIPT ─────────────────────────────────────────
def preprocess(txt):
    txt = re.sub(r'\bDr\.', 'Dr', txt)
    txt = re.sub(r'\bDra\.', 'Dra', txt)
    return txt

CLEAN = preprocess(RAW)

# ── 4. DIVIDIR EM FRASES COM EMOÇÃO ─────────────────────────────────
paragrafos = [p.strip() for p in CLEAN.split('\n') if p.strip() and len(p.strip()) > 5]

def get_emotion(frase):
    t = frase.lower()
    if any(k in t for k in ["salva","canal","assistir","mais tarde","depois","inscreva"]):
        return 0.80, 0.5
    if "quatro anos" in t and "apagando" in t: return 0.62, 1.0
    elif "quatro anos" in t: return 0.65, 0.7
    elif "apagando" in t: return 0.65, 0.5
    elif ("chora" in t and len(t) < 20): return 0.60, 0.9
    elif any(k in t for k in ["mais perigoso","não grita","não humilha"]): return 0.72, 0.3
    elif any(k in t for k in ["afastar","errada","culpada"]): return 0.75, 0.4
    elif "isso tem nome" in t: return 0.70, 0.6
    elif any(k in t for k in ["harvard","pesquisador","estudo","dr ","dra "]): return 0.82, 0.3
    elif any(k in t for k in ["sinal 1","sinal 2","sinal 3"]): return 0.78, 0.4
    elif any(k in t for k in ["nunca responsável","crítica","aprende","falar nada"]): return 0.78, 0.3
    elif any(k in t for k in ["desculpar","existir","sentir","precisar"]): return 0.74, 0.5
    elif any(k in t for k in ["não está exagerando","sensível demais","dramática"]): return 0.75, 0.3
    elif any(k in t for k in ["normalmente","anormal","reagindo"]): return 0.77, 0.3
    return 0.80, 0.2

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

# Garantir CTA final
ultima = paragrafos[-1] if paragrafos else ""
if "salva" in ultima.lower() and (not frases or "salva" not in frases[-1].lower()):
    frases.append(ultima.strip())
    emocoes.append(get_emotion(ultima))
if len(frases) > 16:
    frases = frases[:15] + [frases[-1]]
    emocoes = emocoes[:15] + [emocoes[-1]]

N = len(frases)
log(f"\n  {N} frases com emoção dinâmica:")
for i,(f,(spd,pau)) in enumerate(zip(frases,emocoes),1):
    log(f"    [{i:02d}] speed={spd:.2f} +{pau:.1f}s | {f[:50]}")

SCRIPT_TTS = " ".join(frases)

# ── 5. XTTS v2 — CLONAR VOZ GEORGE ──────────────────────────────────
log(f"\n🎙️  ETAPA 1 — XTTS v2 Voice Clone (George PT)")
AUDIO = None
VOICE_USED = "XTTS_v2/George_clone"

# Tentar ElevenLabs primeiro (se quota disponível)
if XI_KEY:
    log("  Tentando ElevenLabs George...")
    try:
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{GEORGE}",
            headers={"xi-api-key": XI_KEY, "Content-Type": "application/json"},
            json={"text": SCRIPT_TTS, "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability":0.20,"similarity_boost":0.85,"style":0.70,
                                     "use_speaker_boost":True,"speed":1.00}},
            timeout=180
        )
        if r.status_code == 200:
            AUDIO = f"{WORKDIR}/audio_george.mp3"
            with open(AUDIO,'wb') as f: f.write(r.content)
            log(f"  ✅ ElevenLabs George: {len(r.content)//1024}KB")
            VOICE_USED = "ElevenLabs/George"
        else:
            log(f"  ⚠️ ElevenLabs {r.status_code} — usando XTTS v2")
    except Exception as e:
        log(f"  ⚠️ {e} — usando XTTS v2")

# XTTS v2 clonagem de voz
if AUDIO is None:
    log("  🔬 XTTS v2 — clonando voz George...")
    try:
        # Aceitar ToS automaticamente
        os.environ['COQUI_TOS_AGREED'] = '1'
        from TTS.api import TTS

        log("  Carregando modelo XTTS v2 (~750MB, pode demorar 1a vez)...")
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
        log("  ✅ Modelo carregado")

        # Gerar frase por frase com speeds diferentes
        seg_files = []
        SR = 24000

        for idx, (frase, (speed, pause_s)) in enumerate(zip(frases, emocoes), 1):
            seg_path = f"{WORKDIR}/seg_{idx:03d}.wav"
            try:
                # XTTS v2: sem parâmetro speed — aplicar atempo via ffmpeg depois
                tts.tts_to_file(
                    text=frase,
                    speaker_wav=GEORGE_REF_WAV,
                    language="pt",
                    file_path=seg_path
                )

                if not os.path.exists(seg_path) or os.path.getsize(seg_path) < 1000:
                    log(f"  [{idx:02d}/{N}] ⚠️ segmento vazio")
                    continue

                seg_dur = measure_dur(seg_path)

                # Aplicar velocidade via ffmpeg atempo (0.5-2.0)
                # speed < 1.0 = mais lento; speed > 1.0 = mais rápido
                if abs(speed - 1.0) > 0.05:
                    seg_adj = seg_path.replace('.wav','_adj.wav')
                    atempo_seg = speed  # speed 0.72 = falar 72% da velocidade = mais lento
                    # atempo inverte: 0.8 = 80% da velocidade original = mais lento
                    subprocess.run([
                        "ffmpeg","-y","-i",seg_path,
                        "-filter:a",f"atempo={atempo_seg:.3f}",
                        "-ar",str(SR),seg_adj
                    ], capture_output=True)
                    if os.path.exists(seg_adj) and os.path.getsize(seg_adj) > 500:
                        seg_dur_adj = measure_dur(seg_adj)
                        seg_files.append(seg_adj)
                        log(f"  [{idx:02d}/{N}] ✅ {seg_dur:.1f}s→{seg_dur_adj:.1f}s (speed={speed}) | {frase[:40]}")
                    else:
                        seg_files.append(seg_path)
                        log(f"  [{idx:02d}/{N}] ✅ {seg_dur:.1f}s (natural) | {frase[:40]}")
                else:
                    seg_files.append(seg_path)
                    log(f"  [{idx:02d}/{N}] ✅ {seg_dur:.1f}s | {frase[:40]}")

                # Silêncio pós-frase para pausas dramáticas
                if pause_s > 0:
                    sil_path = f"{WORKDIR}/sil_{idx:03d}.wav"
                    subprocess.run([
                        "ffmpeg","-y","-f","lavfi",
                        "-i",f"anullsrc=r={SR}:cl=mono",
                        "-t",str(pause_s),"-ar",str(SR),sil_path
                    ], capture_output=True)
                    if os.path.exists(sil_path):
                        seg_files.append(sil_path)

            except Exception as e:
                log(f"  [{idx:02d}/{N}] ⚠️ {e}")

        if seg_files:
            concat_txt = f"{WORKDIR}/concat_xtts.txt"
            with open(concat_txt,'w') as f:
                for sf_ in seg_files: f.write(f"file '{sf_}'\n")

            raw_wav = f"{WORKDIR}/audio_xtts_raw.wav"
            mp3_out = f"{WORKDIR}/audio_xtts.mp3"

            subprocess.run([
                "ffmpeg","-y","-f","concat","-safe","0","-i",concat_txt,
                "-ar","44100","-ac","1","-af","volume=1.2",raw_wav
            ], capture_output=True)

            subprocess.run([
                "ffmpeg","-y","-i",raw_wav,
                "-codec:a","libmp3lame","-b:a","320k",mp3_out
            ], capture_output=True)

            AUDIO = mp3_out
            log(f"  ✅ XTTS v2 George clone: {measure_dur(AUDIO):.2f}s @ 44100Hz/320k")
        else:
            raise RuntimeError("Nenhum segmento gerado")

    except Exception as e:
        log(f"  ⚠️ XTTS v2 falhou: {e}")
        log("  🔄 Fallback: AntonioNeural")
        import asyncio, edge_tts
        async def _gen():
            c = edge_tts.Communicate(SCRIPT_TTS, voice="pt-BR-AntonioNeural", rate="-12%")
            await c.save(f"{WORKDIR}/audio_fallback.mp3")
        asyncio.run(_gen())
        AUDIO = f"{WORKDIR}/audio_fallback.mp3"
        VOICE_USED = "AntonioNeural"

DUR_AUDIO = measure_dur(AUDIO)
log(f"  Total áudio: {DUR_AUDIO:.2f}s")

# Atempo bidirecional — alvo 60s (YouTube Shorts max)
TARGET = 60.0
TOLERANCIA = 3.0
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
        direcao = "⬇️" if atempo > 1 else "⬆️"
        log(f"  {direcao} atempo={atempo:.3f}x → {DUR_AUDIO:.2f}s")
else:
    log(f"  ✅ Duração natural OK ({DUR_AUDIO:.1f}s) — sem compressão")

RATE_REAL = len(SCRIPT_TTS) / DUR_AUDIO
DURS = [max(1.2, round(len(f)/RATE_REAL, 3)) for f in frases]
diff = DUR_AUDIO - sum(DURS)
DURS[0] = round(DURS[0] + diff, 3)

# ── 6-7. IMAGENS + RENDER (mesmo sistema anterior) ─────────────────
# [copiado do render_kokoro_v2.py — seção de imagens e ffmpeg]
log(f"\n🖼️  ETAPA 2 — Imagens semânticas")

STYLE = ("kawaii chibi anime illustration, 9:16 portrait, "
         "masterpiece, best quality, vivid expressive colors, "
         "Brazilian woman characters, relatable authentic emotions, "
         "detailed backgrounds, cinematic lighting")
NEG  = "### lowres, bad anatomy, text, watermark, nsfw, ugly, blurry, realistic"

DANIELA = ("female psychology host age 35 dark straight bob hair mint blouse ψ pin, "
           "confident warm authoritative expression, direct eye contact, empowering")
SARA    = ("female protagonist age 28 curly dark brown hair warm olive skin, "
           "everyday clothes yellow cardigan, expressive eyes, relatable Brazilian woman")
MARCOS  = ("male antagonist age 34 well-dressed navy blazer, "
           "charming smile hiding manipulative intent, handsome but cold calculating eyes")
ANA     = ("female expert Dr age 42 white coat reading glasses, "
           "Brazilian professional appearance, scientific authority, clipboard")

def prompt_for_frase(frase, idx, N):
    t = frase.lower()
    if any(k in t for k in ["salva","canal","assistir","mais tarde","depois","inscreva"]):
        return (f"masterpiece, best quality, {STYLE}, "
                f"{DANIELA} in warm inviting pose hand extended toward viewer beckoning, "
                "soft glowing portal showing more content beyond, curious hopeful expression, "
                "violet golden warm light, come watch more energy, FOMO desire to continue {NEG}")
    elif "mais perigoso" in t or ("grita" in t and "humilha" in t):
        return (f"masterpiece, best quality, {STYLE}, "
                f"{MARCOS} split-frame friendly warm smile in bright light vs sinister cold shadow-self, "
                "beautiful flowers hiding thorns, danger disguised as love {NEG}")
    elif ("chora" in t and len(t) < 20):
        return (f"masterpiece, best quality, {STYLE}, "
                f"{MARCOS} exaggerated fake theatrical crying, manipulative victim act, "
                "eyes remain cold calculating, performance of pain not real pain {NEG}")
    elif "afastar" in t or "errada" in t:
        return (f"masterpiece, best quality, {STYLE}, "
                f"{SARA} backing away {MARCOS} pointing accusatory finger, "
                "wavy distorted gaslighting background, reality twisted, self-doubt {NEG}")
    elif "isso tem nome" in t or "narcisismo encoberto" in t:
        return (f"masterpiece, best quality, {STYLE}, "
                f"{ANA} holding open book psychological term highlighted bold, "
                "revelation moment, naming the invisible threat {NEG}")
    elif "sinal 1" in t:
        return (f"masterpiece, best quality, {STYLE}, "
                "large glowing violet number ONE, "
                f"{MARCOS} dramatic victim pose hands clutched chest, playing wounded {NEG}")
    elif "sinal 2" in t or "crítica" in t or "crise" in t:
        return (f"masterpiece, best quality, {STYLE}, "
                "large glowing violet number TWO, "
                f"{SARA} tiptoeing on literal eggshells floor, tense suffocating atmosphere {NEG}")
    elif "sinal 3" in t or "desculpar" in t or ("sentir" in t and "precisar" in t):
        return (f"masterpiece, best quality, {STYLE}, "
                "large glowing violet number THREE, "
                f"{SARA} deeply apologetic bent forward apologizing for existing, self-erasure {NEG}")
    elif "nunca falar" in t or "falar nada" in t or "aprende" in t:
        return (f"masterpiece, best quality, {STYLE}, "
                f"{SARA} hands pressed over own mouth silencing herself, "
                "invisible cage bars, self-censorship visible {NEG}")
    elif "quatro anos" in t or "apagando" in t:
        return (f"masterpiece, best quality, {STYLE}, "
                f"{SARA} body becoming translucent ghostlike, "
                "voice dissolving into air, 4 calendar years fading, identity erased {NEG}")
    elif any(k in t for k in ["harvard","pesquisador","estudo","dr ","dra "]):
        return (f"masterpiece, best quality, {STYLE}, "
                f"{ANA} pointing dramatically to large statistic on board, "
                "shocked authoritative expression, scientific validation moment {NEG}")
    elif "não está exagerando" in t or "sensível demais" in t or "dramática" in t:
        return (f"masterpiece, best quality, {STYLE}, "
                f"{DANIELA} intense direct eye contact with camera viewer, "
                "hand on heart deep compassion, warm golden healing light, YOU ARE SEEN {NEG}")
    elif "normalmente" in t or "anormal" in t:
        return (f"masterpiece, best quality, {STYLE}, "
                f"{DANIELA} powerful protective presence violet golden light, "
                f"{SARA} strength returning, darkness lifting, empowering {NEG}")
    elif idx <= 2:
        return f"masterpiece, best quality, {STYLE}, {DANIELA} presenting urgent psychological warning {NEG}"
    elif idx <= N//2:
        return f"masterpiece, best quality, {STYLE}, {SARA} emotional recognition moment, authentic Brazilian {NEG}"
    else:
        return f"masterpiece, best quality, {STYLE}, {DANIELA} warm empowering expression healing golden light {NEG}"

PROMPTS = [prompt_for_frase(f,i,N) for i,f in enumerate(frases,1)]

banco_map = {}
try:
    rb = requests.get(f"{SB_URL}/rest/v1/image_bank?select=character_slug,scene_type,image_url&limit=300",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=60)
    for img in rb.json():
        k = f"{img['character_slug']}_{img['scene_type']}"
        banco_map.setdefault(k, []).append(img['image_url'])
    log(f"  🏦 Banco: {sum(len(v) for v in banco_map.values())} imagens")
except Exception as e: log(f"  ⚠️ Banco: {e}")

IMGS = []
banco_cnt = poll_cnt = 0

for idx, (frase, prompt) in enumerate(zip(frases, PROMPTS), 1):
    fpath = f"{WORKDIR}/img_{idx:02d}.jpg"
    up    = f"{WORKDIR}/img_up_{idx:02d}.jpg"
    found = False
    t = frase.lower()
    force_poll = any(k in t for k in ["salva","canal","mais tarde","não está exagerando","normalmente","chora","mais perigoso","afastar","errada","quatro anos"])

    if not force_poll:
        if "sinal 1" in t or "nunca responsável" in t: key = "marcos_problema"
        elif "sinal 2" in t or "crítica" in t: key = "sara_problema"
        elif "sinal 3" in t or "desculpar" in t: key = "sara_virada"
        elif any(k in t for k in ["harvard","estudo","pesquisador","universidade"]): key = "ana_ciencia"
        elif any(k in t for k in ["normalmente","anormal"]): key = "daniela_virada"
        else: key = None
        if key and banco_map.get(key):
            url = banco_map[key][(idx*17) % len(banco_map[key])]
            try:
                r = requests.get(url, timeout=30)
                if r.status_code == 200 and len(r.content) > 5000:
                    with open(fpath,'wb') as f: f.write(r.content)
                    IMGS.append(upscale(fpath,up))
                    log(f"  [{idx:02d}/{N}] 🏦 {key} | {frase[:35]}")
                    banco_cnt += 1
                    found = True
            except: pass

    if not found:
        seed = 7777 + idx*191 + VIDEO_ID
        poll_url = (f"https://image.pollinations.ai/prompt/"
                    f"{requests.utils.quote(prompt)}?width=576&height=1024&seed={seed}&nologo=true")
        for att in range(4):
            try:
                r = requests.get(poll_url, timeout=90, headers={"User-Agent":"Mozilla/5.0"})
                if r.status_code == 200 and len(r.content) > 5000:
                    with open(fpath,'wb') as f: f.write(r.content)
                    IMGS.append(upscale(fpath,up))
                    log(f"  [{idx:02d}/{N}] 🌐 {len(r.content)//1024}KB | {frase[:35]}")
                    poll_cnt += 1
                    found = True
                    break
            except: pass
            time.sleep(4)
    if not found:
        IMGS.append(IMGS[-1] if IMGS else None)
        log(f"  [{idx:02d}/{N}] ⚠️ fallback")

log(f"  ✅ {banco_cnt} banco | {poll_cnt} poll | {banco_cnt+poll_cnt}/{N}")

# RENDER FFMPEG
log(f"\n🎬 ETAPA 3 — Render")
OVERLAY = ("drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
           "text='ψ @psidanielacoelho':fontcolor=white:fontsize=26:"
           "borderw=2:bordercolor=black:x=20:y=h-48")
concat_txt = f"{WORKDIR}/concat.txt"
with open(concat_txt,'w') as f:
    for img,dur in zip(IMGS,DURS):
        if img and os.path.exists(img):
            f.write(f"file '{img}'\nduration {dur:.3f}\n")
    if IMGS[-1] and os.path.exists(IMGS[-1]): f.write(f"file '{IMGS[-1]}'\n")

OUT = f"{WORKDIR}/output.mp4"
r = subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat_txt,
    "-i",AUDIO,"-vf",f"{OVERLAY},format=yuv420p",
    "-c:v","libx264","-crf","22","-preset","fast",
    "-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart","-r","25",OUT],
    capture_output=True,text=True,timeout=300)
if r.returncode != 0: log(f"❌ {r.stderr[-300:]}"); sys.exit(1)

DUR_FINAL = measure_dur(OUT)
SZ = os.path.getsize(OUT)/1024/1024
log(f"  ✅ {DUR_FINAL:.2f}s | {SZ:.2f}MB")

# UPLOAD
log(f"\n☁️  ETAPA 4 — Upload")
ts = int(time.time())
fname = f"v{VIDEO_ID}_xtts_{ts}.mp4"
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
    time.sleep(15)

if video_url:
    sb_patch(VIDEO_ID,{"video_url":video_url,"status":"pending_credentials",
        "metadata":json.dumps({"dur_s":round(DUR_FINAL,1),"file_mb":round(SZ,2),
            "voice":VOICE_USED,"n_frases":N,"version":"xtts_george_clone_v1"})})

log(f"\nψ RESULTADO:")
log(f"  ⏱️  {DUR_FINAL:.2f}s | 💾 {SZ:.2f}MB | 🎤 {VOICE_USED}")
log(f"  🎬 {video_url or '❌'}")
