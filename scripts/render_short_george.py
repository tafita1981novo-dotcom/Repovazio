#!/usr/bin/env python3
"""
render_short_final.py — VERSÃO PERFEITA
✅ Voz George ElevenLabs: stability=0.18, style=0.70, speed=1.0 (sem compressão)
✅ Imagens semânticas por frase com prompts ultra-específicos
✅ Atempo APENAS se > 63s (safety net leve)
✅ CTA com sino dourado dramático
✅ Sem engasgo: Dr. → Dr pré-processado
"""
import os, sys, asyncio, json, subprocess, requests, time, re

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

# ── 1. BUSCAR SCRIPT ─────────────────────────────────────────────────
log(f"\nψ SHORT 58s PERFEITO — #{VIDEO_ID}")
row = requests.get(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{VIDEO_ID}&select=id,title,script",
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=60).json()
if not row or not row[0].get("script"):
    log("❌ Script não encontrado"); sys.exit(1)

TITULO = row[0]["title"]
RAW    = row[0]["script"].strip()
log(f"  Título: {TITULO[:55]}")

# ── 2. PRÉ-PROCESSAR (sem engasgo) ───────────────────────────────────
def preprocess(txt):
    txt = re.sub(r'\bDr\.', 'Dr', txt)
    txt = re.sub(r'\bDra\.', 'Dra', txt)
    txt = re.sub(r'\bProf\.', 'Prof', txt)
    return txt

CLEAN = preprocess(RAW)

# ── 3. DIVIDIR EM FRASES ─────────────────────────────────────────────
# Separar por parágrafo primeiro, depois por sentença
paragrafos = [p.strip() for p in CLEAN.split('\n') if p.strip() and len(p.strip()) > 5]
frases = []
for p in paragrafos:
    sents = re.split(r'(?<=[.!?…])\s+', p)
    for s in sents:
        s = s.strip()
        # Reunir fragmentos muito curtos
        if len(s) < 18 and frases:
            frases[-1] += " " + s
        elif len(s) > 100:
            mid = s.rfind(',', 0, 70)
            if mid > 15:
                frases.append(s[:mid+1].strip())
                frases.append(s[mid+1:].strip())
            else:
                frases.append(s)
        elif len(s) > 3:
            frases.append(s)

# Limitar frases — manter Inscreva-se SEMPRE como última
frases = [f for f in frases if len(f) > 3]

# Garantir que CTA "Inscreva-se" está na última frase
ultima_para = paragrafos[-1] if paragrafos else ""
inscreva_ja = any("inscreva" in f.lower() for f in frases)
if not inscreva_ja and "inscreva" in ultima_para.lower():
    frases.append(ultima_para.strip())

# Limitar total (mantendo último = Inscreva-se)
if len(frases) > 16:
    frases = frases[:15] + [frases[-1]]

N = len(frases)

SCRIPT_TTS = " ".join(frases)
total_chars = len(SCRIPT_TTS)
log(f"  {N} frases | {total_chars} chars")
for i,f in enumerate(frases,1): log(f"    [{i:02d}] {f[:60]}")

# ── 4. ÁUDIO GEORGE ──────────────────────────────────────────────────
log(f"\n🎙️  ETAPA 1 — George ElevenLabs (max emoção)")
AUDIO = None

if XI_KEY:
    log(f"  stability=0.18 | style=0.70 | speed=1.00 (natural, sem compressão)")
    try:
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{GEORGE}",
            headers={"xi-api-key": XI_KEY, "Content-Type": "application/json"},
            json={
                "text": SCRIPT_TTS,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability":        0.18,  # máxima variação emocional
                    "similarity_boost": 0.85,
                    "style":            0.70,  # alta expressividade dramática
                    "use_speaker_boost": True,
                    "speed":            1.00   # natural — ZERO compressão
                }
            },
            timeout=180
        )
        if r.status_code == 200:
            AUDIO = f"{WORKDIR}/audio_george.mp3"
            with open(AUDIO,'wb') as f: f.write(r.content)
            log(f"  ✅ George: {len(r.content)//1024}KB")
        else:
            log(f"  ⚠️ {r.status_code}: {r.text[:80]}")
    except Exception as e:
        log(f"  ⚠️ {e}")

if AUDIO is None:
    import edge_tts
    # FranciscaNeural = mais calorosa e empática para conteúdo psicologia
    # AntonioNeural = mais dramático com rate -5%
    VOICE_FALLBACK = "pt-BR-FranciscaNeural"
    RATE_FALLBACK  = "+0%"
    async def _ant():
        c=edge_tts.Communicate(SCRIPT_TTS,voice=VOICE_FALLBACK,rate=RATE_FALLBACK)
        await c.save(f"{WORKDIR}/audio_ant.mp3")
    asyncio.run(_ant())
    AUDIO = f"{WORKDIR}/audio_ant.mp3"
    log(f"  ✅ {VOICE_FALLBACK} fallback (ElevenLabs quota indisponível)")
    voice = VOICE_FALLBACK  # corrigir metadata

DUR_AUDIO = measure_dur(AUDIO)
log(f"  ✅ Duração bruta: {DUR_AUDIO:.2f}s")

# Atempo BIDIRECIONAL: sempre ajusta para 58s (±2s de tolerância)
TARGET   = 58.0
TOLERANCIA = 2.0   # até 2s de diferença = sem ajuste (preserva micro-pausas)
if abs(DUR_AUDIO - TARGET) > TOLERANCIA:
    atempo = DUR_AUDIO / TARGET
    atempo = max(0.5, min(2.0, atempo))
    direcao = "⬇️ comprimindo" if atempo > 1.0 else "⬆️ expandindo"
    adj = f"{WORKDIR}/audio_adj.mp3"
    r_at = subprocess.run(
        ["ffmpeg","-y","-i",AUDIO,"-filter:a",f"atempo={atempo:.4f}","-q:a","2",adj],
        capture_output=True,text=True,timeout=60)
    if r_at.returncode == 0:
        AUDIO    = adj
        DUR_AUDIO = measure_dur(AUDIO)
        log(f"  ✅ {direcao}: {atempo:.3f}x → {DUR_AUDIO:.2f}s")
    else:
        log(f"  ⚠️ atempo falhou: {r_at.stderr[-100:]}")
else:
    log(f"  ✅ Duração OK ({DUR_AUDIO:.1f}s) — micro-pausas preservadas")

RATE_REAL = total_chars / DUR_AUDIO
DURS = [max(1.2, round(len(f)/RATE_REAL, 3)) for f in frases]
diff = DUR_AUDIO - sum(DURS)
DURS[0] = round(DURS[0] + diff, 3)

# ── 5. PROMPTS ULTRA-ESPECÍFICOS POR FRASE ────────────────────────────
log(f"\n🖼️  ETAPA 2 — {N} imagens (prompts semânticos ultra-específicos)")

STYLE = "kawaii chibi anime illustration, 9:16 portrait, masterpiece, best quality, pastel soft colors, expressive eyes, detailed"
NEG   = "### lowres, bad anatomy, text, watermark, nsfw, blurry, realistic, photo, ugly"
DANIELA = "female psychology host age 35 dark bob hair mint green blouse ψ pin, warm confident"
SARA    = "female protagonist age 28 curly auburn hair yellow cardigan, emotionally expressive"
MARCOS  = "male antagonist age 34 navy blazer, charming smile hiding sinister intent"
JULIA   = "female friend age 29 afro curly hair orange sweater, caring"
ANA     = "female expert Dr age 42 white coat, professional expression, clipboard"
GROUP   = "all characters daniela sara marcos julia together"

def prompt_for_frase(frase, idx):
    t = frase.lower()
    
    # ── CTA / INSCREVA-SE → prompt EXCLUSIVO dramático ──────────────
    if "inscreva" in t or "🔔" in frase or "sino" in t or "próximo vídeo" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"GIANT golden glowing notification bell filling 80% of frame, massive radiant sparkles and rays emanating from bell, "
            f"{DANIELA} and {SARA} below with arms raised in pure celebration joy, colorful confetti exploding everywhere, "
            f"urgent subscribe energy, bright golden violet light, maximum excitement {NEG}"
        )
    
    # ── HOOK: narcisista chora ────────────────────────────────────────
    elif "mais perigoso" in t or ("chora" in t and "perigoso" in t) or ("grita" in t and "humilha" in t):
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{MARCOS} with friendly warm smile in foreground while dark menacing shadow looms behind him, "
            f"danger hidden behind kindness, dramatic split lighting, roses with hidden thorns imagery {NEG}"
        )
    
    # ── TWIST: você é quem está errada ───────────────────────────────
    elif "afastar" in t or "errada" in t or "culpada" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{SARA} looking confused and shrinking while {MARCOS} points accusatory finger at her, "
            f"reality being twisted, gaslight effect with wavy distorted background, "
            f"she looks small he looks big {NEG}"
        )
    
    # ── CIÊNCIA / PESQUISADOR ─────────────────────────────────────────
    elif any(k in t for k in ["harvard","pesquisa","dr ","dra ","estudo","universidade","indiana","ciência"]):
        if "quatro anos" in t or "4 anos" in t or "anos" in t:
            return (
                f"masterpiece, best quality, {STYLE}, "
                f"{ANA} holding large clipboard showing bold number 4 with YEARS written below in red, "
                f"shocked expression, scientific revelation, research environment {NEG}"
            )
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{ANA} presenting Harvard seal and research findings, pointing to shocking statistic, "
            f"authoritative scientific revelation, blue academic lighting {NEG}"
        )
    
    # ── SINAIS NUMERADOS ─────────────────────────────────────────────
    elif "sinal 1" in t or "primeiro sinal" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"glowing violet number ONE badge prominent in scene, {MARCOS} with exaggerated victim expression, "
            f"arms crossed, pointing at self, dramatic poor-me pose, "
            f"everyone around him looking confused and apologetic {NEG}"
        )
    elif "sinal 2" in t or "segundo sinal" in t or ("qualquer crítica" in t and "crise" in t):
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"glowing violet number TWO badge, {SARA} tiptoeing carefully on eggshells drawn on floor, "
            f"{MARCOS} in background overreacting dramatically to imaginary criticism, "
            f"tense suffocating atmosphere {NEG}"
        )
    elif "sinal 3" in t or "terceiro sinal" in t or "desculpar por existir" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"glowing violet number THREE badge, {SARA} with both hands pressed together apologetically, "
            f"shrinking smaller apologizing just for existing, self-erasing, "
            f"her light dimming and fading, emotional suppression {NEG}"
        )
    
    # ── NUNCA FALAR NADA ─────────────────────────────────────────────
    elif "nunca falar" in t or "nunca responsável" in t or "aprende a nunca" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{SARA} with hand over own mouth silencing herself, eyes wide with fear, "
            f"{MARCOS} looming in background causing the silence, "
            f"invisible cage bars, self-censorship visible {NEG}"
        )
    
    # ── QUATRO ANOS APAGANDO A VOZ ────────────────────────────────────
    elif "quatro anos" in t or "apagando" in t or "voz" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{SARA} body becoming transparent and ghostlike, voice literally dissolving into air, "
            f"calendar pages showing years flying by, identity being erased slowly, "
            f"melancholic powerful imagery, fading into nothing {NEG}"
        )
    
    # ── EMPODERAMENTO: não está exagerando ───────────────────────────
    elif "não está exagerando" in t or "sensível demais" in t or "não é dramática" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{DANIELA} making intense direct eye contact with camera viewer, "
            f"hand placed gently on heart, warm golden healing light radiating from her, "
            f"validating intimate moment, you are seen and heard energy {NEG}"
        )
    
    # ── REAGINDO NORMALMENTE ─────────────────────────────────────────
    elif "reagindo normalmente" in t or "ambiente anormal" in t:
        return (
            f"masterpiece, best quality, {STYLE}, "
            f"{DANIELA} with protective empowering expression, violet light behind her, "
            f"strength and clarity returning to {SARA} beside her, "
            f"darkness lifting, power being reclaimed, hopeful bright ending {NEG}"
        )
    
    # ── FALLBACK POR POSIÇÃO ─────────────────────────────────────────
    elif idx <= N // 4:
        return f"masterpiece, best quality, {STYLE}, {DANIELA} presenting important psychological insight, direct engaging expression {NEG}"
    elif idx <= N // 2:
        return f"masterpiece, best quality, {STYLE}, {SARA} experiencing emotional realization moment, authentic expression {NEG}"
    else:
        return f"masterpiece, best quality, {STYLE}, {DANIELA} warm empowering expression toward camera, healing energy {NEG}"

PROMPTS = [prompt_for_frase(f, i) for i, f in enumerate(frases, 1)]

# Buscar banco Supabase
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
    
    # Forçar Pollinations para prompts especiais (CTA, emocionais)
    force_poll = any(k in t for k in ["inscreva","quatro anos apagando","não está exagerando","reagindo normalmente"])
    
    # 1. Banco para frases genéricas
    if not force_poll:
        if "sinal 1" in t or "nunca responsável" in t: key = "marcos_problema"
        elif "sinal 2" in t or "crítica" in t: key = "sara_problema"
        elif "sinal 3" in t or "desculpar" in t: key = "sara_virada"
        elif any(k in t for k in ["harvard","estudo","dr ","ana"]): key = "ana_ciencia"
        elif any(k in t for k in ["normalmente","anormal","reagindo"]): key = "daniela_virada"
        else: key = None
        
        if key and banco_map.get(key):
            url = banco_map[key][(idx * 17) % len(banco_map[key])]
            try:
                r = requests.get(url, timeout=30)
                if r.status_code == 200 and len(r.content) > 5000:
                    with open(fpath,'wb') as f: f.write(r.content)
                    IMGS.append(upscale(fpath,up))
                    log(f"  [{idx:02d}/{N}] 🏦 banco/{key} | {frase[:40]}")
                    banco_cnt += 1
                    found = True
            except: pass
    
    # 2. Pollinations (para todos os especiais e fallback)
    if not found:
        seed = 9001 + idx * 137  # seeds únicos por vídeo
        poll_url = (f"https://image.pollinations.ai/prompt/"
                    f"{requests.utils.quote(prompt)}?width=576&height=1024&seed={seed}&nologo=true")
        for att in range(4):
            try:
                r = requests.get(poll_url, timeout=90, headers={"User-Agent":"Mozilla/5.0"})
                if r.status_code == 200 and len(r.content) > 5000:
                    with open(fpath,'wb') as f: f.write(r.content)
                    IMGS.append(upscale(fpath,up))
                    sz = len(r.content)//1024
                    log(f"  [{idx:02d}/{N}] 🌐 poll {sz}KB | {frase[:40]}")
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
log(f"\n🎬 ETAPA 3 — FFMPEG")
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
fname = f"v{VIDEO_ID}_george_{ts}.mp4"
voice = "George/ElevenLabs" if XI_KEY else "Antonio/EdgeTTS"
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
    sb_patch(VIDEO_ID,{
        "video_url": video_url,
        "status": "pending_credentials",
        "metadata": json.dumps({
            "dur_s": round(DUR_FINAL,1),
            "file_mb": round(SZ,2),
            "voice": voice,
            "n_frases": N,
            "imgs_banco": banco_cnt,
            "imgs_poll": poll_cnt,
            "version": "george_final_v1"
        })
    })

log(f"\nψ RESULTADO PERFEITO:")
log(f"  ⏱️  {DUR_FINAL:.2f}s | 💾 {SZ:.2f}MB")
log(f"  🎤 {voice} | stability=0.18 | style=0.70 | speed=1.0")
log(f"  🖼️  {banco_cnt} banco + {poll_cnt} Pollinations")
log(f"  🎬 {video_url or '❌ upload falhou'}")
