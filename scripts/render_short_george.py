#!/usr/bin/env python3
"""
NARRAÇÃO HUMANA v2 — Arquitetura de Grupos Semânticos
======================================================
PROBLEMA ANTERIOR: frases isoladas → Chatterbox sem contexto → leitura mecânica
SOLUÇÃO: grupos de 2-3 frases juntas → Chatterbox lê a cena completa → emoção real

Como narrador humano:
  - Lê o parágrafo inteiro antes de falar
  - Usa o contexto anterior para calibrar emoção
  - Faz pausas ENTRE cenas, não entre palavras
  - CAPS = sílaba enfatizada naturalmente
"""
import os, sys, json, subprocess, requests, time, re, asyncio

VIDEO_ID = int(os.environ.get("VIDEO_ID", "683"))
VOICE_VERSION = os.environ.get("VOICE_VERSION", "B")
SB_URL  = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
XI_KEY  = os.environ.get("ELEVENLABS_API_KEY", "")
GEORGE  = "JBFqnCBsd6RMkjVDRZzb"
WORKDIR = f"/tmp/short_{VIDEO_ID}"
os.makedirs(WORKDIR, exist_ok=True)
GEORGE_REF = f"{WORKDIR}/george_ref.wav"
GEORGE_SRC = "https://tpjvalzwkqwttvmszvie.supabase.co/storage/v1/object/public/videos/mp4s/v683_george_1779065193.mp4"

def log(m): print(m, flush=True)
def dur(p):
    r = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",p],
        capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])
def silence(secs, sr, path):
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i",
        f"anullsrc=r={sr}:cl=mono","-t",str(secs),"-ar",str(sr), path],
        capture_output=True)
def sb_patch(id_, data):
    requests.patch(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{id_}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"},
        json=data, timeout=60)

log(f"\nψ NARRAÇÃO HUMANA v2 — #{VIDEO_ID}")

# ── 1. SCRIPT ──────────────────────────────────────────────────────────
row = requests.get(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{VIDEO_ID}&select=id,title,script",
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=60).json()
if not row or not row[0].get("script"):
    log("❌ Script não encontrado"); sys.exit(1)

TITULO = row[0]["title"]
SCRIPT_RAW = row[0]["script"].strip()
log(f"  Título: {TITULO[:55]}")
log(f"  Script: {len(SCRIPT_RAW)} chars")

# ── 2. GRUPOS SEMÂNTICOS POR VÍDEO ─────────────────────────────────────
# Cada grupo = lista de (texto_para_tts, exaggeration, cfg_weight, pausa_depois_s)
# O texto de cada grupo inclui MÚLTIPLAS frases juntas para dar contexto ao Chatterbox
# A pausa é inserida via ffmpeg ENTRE grupos (não dentro)

def montar_grupos(vid, script):
    """Agrupa frases do script em cenas semânticas com parâmetros emocionais."""
    linhas = [l.strip() for l in script.split('\n') if l.strip()]
    
    # Parâmetros base (Versão B: enhanced dramatic)
    P = {
        "HOOK":      (0.88, 0.15, 1.2),   # abertura + twist dramático
        "TENSAO":    (0.85, 0.16, 1.0),   # conflito / manipulação
        "REVELACAO": (0.90, 0.12, 1.1),   # "Isso tem NOME" / virada
        "DESENV":    (0.78, 0.22, 0.7),   # explicação / contexto
        "CTA":       (0.70, 0.30, 0.0),   # call to action (final)
    }
    
    # Padrão: dividir em 4-5 grupos semânticos naturais
    # Hook (1-2 linhas) | Tensão (1-2) | Revelação (1-2) | Desenv (2-3) | CTA (2)
    n = len(linhas)
    
    if n <= 5:
        # Script curto: apenas 3 grupos
        grupos = [
            ("\n".join(linhas[:2]), *P["HOOK"]),
            ("\n".join(linhas[2:n-2]), *P["REVELACAO"]),
            ("\n".join(linhas[n-2:]), *P["CTA"]),
        ]
    elif n <= 7:
        # Script médio: 4 grupos
        grupos = [
            ("\n".join(linhas[:2]), *P["HOOK"]),
            ("\n".join(linhas[2:4]), *P["TENSAO"]),
            ("\n".join(linhas[4:n-2]), *P["REVELACAO"]),
            ("\n".join(linhas[n-2:]), *P["CTA"]),
        ]
    else:
        # Script longo (9+ linhas): 5 grupos
        grupos = [
            ("\n".join(linhas[:2]), *P["HOOK"]),
            ("\n".join(linhas[2:4]), *P["TENSAO"]),
            ("\n".join(linhas[4:5]), *P["REVELACAO"]),
            ("\n".join(linhas[5:n-2]), *P["DESENV"]),
            ("\n".join(linhas[n-2:]), *P["CTA"]),
        ]
    
    # Filtrar grupos vazios
    return [(t.strip(), e, c, p) for (t, e, c, p) in grupos if t.strip()]

GRUPOS = montar_grupos(VIDEO_ID, SCRIPT_RAW)

log(f"\n  {len(GRUPOS)} grupos semânticos:")
for i, (txt, exag, cfg, pau) in enumerate(GRUPOS, 1):
    preview = txt.replace('\n', ' / ')[:60]
    log(f"    [{i}] exag={exag:.2f} cfg={cfg:.2f} +{pau:.1f}s | {preview}")

# ── 3. REFERÊNCIA GEORGE ───────────────────────────────────────────────
log(f"\n🎙️  Baixando referência George...")
if not os.path.exists(GEORGE_REF):
    r = requests.get(GEORGE_SRC, timeout=120, headers={"User-Agent":"Mozilla/5.0"})
    if r.status_code == 200:
        src = f"{WORKDIR}/george_src.mp4"
        with open(src, 'wb') as f: f.write(r.content)
        subprocess.run(["ffmpeg","-y","-i",src,"-ss","2","-t","14",
            "-vn","-ar","22050","-ac","1",
            "-af","highpass=f=80,lowpass=f=8000,volume=1.3", GEORGE_REF],
            capture_output=True)
        log(f"  ✅ {dur(GEORGE_REF):.1f}s extraídos")
    else:
        log(f"  ❌ {r.status_code}"); sys.exit(1)
else:
    log("  ✅ Em cache")

# ── 4. VOZ ─────────────────────────────────────────────────────────────
log(f"\n🎤  Gerando narração em {len(GRUPOS)} grupos...")
AUDIO = None
VOICE_USED = "Chatterbox/George_clone_semantic"
SR = 24000  # sample rate Chatterbox

# P1: ElevenLabs George (script completo se disponível)
SCRIPT_TTS = "\n".join(t for t, *_ in GRUPOS)
if XI_KEY:
    log("  [P1] ElevenLabs George...")
    try:
        r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{GEORGE}",
            headers={"xi-api-key":XI_KEY,"Content-Type":"application/json"},
            json={"text":SCRIPT_TTS,"model_id":"eleven_multilingual_v2",
                  "voice_settings":{"stability":0.20,"similarity_boost":0.85,
                                    "style":0.70,"use_speaker_boost":True}},
            timeout=180)
        if r.status_code == 200:
            AUDIO = f"{WORKDIR}/audio_xi.mp3"
            with open(AUDIO,'wb') as f: f.write(r.content)
            log(f"  ✅ ElevenLabs George: {len(r.content)//1024}KB")
            VOICE_USED = "ElevenLabs/George"
        else:
            log(f"  ❌ ElevenLabs {r.status_code}: {r.json().get('detail',{}).get('code','')}")
    except Exception as e: log(f"  ⚠️ {e}")

# P2: Chatterbox Multilingual — grupos semânticos
if AUDIO is None:
    log("  [P2] Chatterbox Multilingual — grupos semânticos PT-BR...")
    try:
        import torchaudio
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        log("  Carregando modelo...")
        model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
        SR = model.sr
        log(f"  ✅ Modelo pronto | SR={SR}Hz")

        seg_files = []
        for idx, (txt, exag, cfg, pau) in enumerate(GRUPOS, 1):
            seg_path = f"{WORKDIR}/grp_{idx:02d}.wav"
            sil_path = f"{WORKDIR}/sil_{idx:02d}.wav"
            preview = txt.replace('\n', ' / ')[:50]
            log(f"  [{idx}/{len(GRUPOS)}] exag={exag:.2f} cfg={cfg:.2f} | {preview}")
            
            # Gerar áudio do grupo completo (contexto preservado)
            wav = model.generate(
                txt,
                audio_prompt_path=GEORGE_REF,
                language_id="pt",
                exaggeration=exag,
                cfg_weight=cfg
            )
            torchaudio.save(seg_path, wav, SR)
            d = dur(seg_path)
            log(f"    ✅ {d:.1f}s gerado")
            seg_files.append(seg_path)

            # Pausa dramática ENTRE grupos (não dentro)
            if pau > 0 and idx < len(GRUPOS):
                silence(pau, SR, sil_path)
                seg_files.append(sil_path)

        # Filtrar apenas arquivos que realmente existem e têm tamanho > 0
        seg_files = [sp for sp in seg_files
                     if os.path.exists(sp) and os.path.getsize(sp) > 100]
        
        if seg_files:
            # Concatenar todos os grupos
            concat_f = f"{WORKDIR}/concat.txt"
            with open(concat_f,'w') as f:
                for sp in seg_files: f.write(f"file '{sp}'\n")
            log(f"  Concatenando {len(seg_files)} segmentos...")
            raw = f"{WORKDIR}/audio_raw.wav"
            mp3 = f"{WORKDIR}/audio_cb.mp3"
            r_cat = subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat_f,
                "-ar","44100","-ac","1","-af","volume=1.1", raw],
                capture_output=True, text=True)
            if r_cat.returncode != 0:
                log(f"  ⚠️ ffmpeg concat: {r_cat.stderr[-200:]}")
                # Tentar sem silêncios
                seg_only = [sp for sp in seg_files if 'sil_' not in sp]
                with open(concat_f,'w') as f:
                    for sp in seg_only: f.write(f"file '{sp}'\n")
                subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat_f,
                    "-ar","44100","-ac","1","-af","volume=1.1", raw], capture_output=True)
            subprocess.run(["ffmpeg","-y","-i",raw,"-codec:a","libmp3lame",
                "-b:a","256k", mp3], capture_output=True)
            AUDIO = mp3
            log(f"  ✅ Chatterbox: {dur(AUDIO):.2f}s @ 44100Hz/256kbps")
        else:
            raise RuntimeError("Nenhum grupo gerado")

    except Exception as e:
        log(f"  ⚠️ Chatterbox falhou: {type(e).__name__}: {str(e)[:200]}")
        VOICE_USED = "AntonioNeural/fallback"

# P3: AntonioNeural fallback
if AUDIO is None:
    log("  [P3] AntonioNeural fallback...")
    async def _gen():
        import edge_tts
        c = edge_tts.Communicate(SCRIPT_TTS, voice="pt-BR-AntonioNeural", rate="-12%")
        await c.save(f"{WORKDIR}/audio_ant.mp3")
    asyncio.run(_gen())
    AUDIO = f"{WORKDIR}/audio_ant.mp3"
    log(f"  ✅ AntonioNeural: {dur(AUDIO):.2f}s")

DUR_AUDIO = dur(AUDIO)
log(f"\n  ✅ Narração final: {DUR_AUDIO:.2f}s | {VOICE_USED}")

# Safety cap 62s (sem atempo normal — só em caso extremo)
if DUR_AUDIO > 62.0:
    at = DUR_AUDIO / 60.0
    cap = f"{WORKDIR}/audio_cap.mp3"
    subprocess.run(["ffmpeg","-y","-i",AUDIO,"-filter:a",f"atempo={at:.4f}",
        "-q:a","2", cap], capture_output=True, timeout=60)
    if os.path.exists(cap): AUDIO=cap; DUR_AUDIO=dur(AUDIO)
    log(f"  ⬇️ Cap aplicado: {DUR_AUDIO:.1f}s")

RATE_REAL = len(SCRIPT_TTS.replace('\n',' ')) / DUR_AUDIO
linhas_all = [l for l in SCRIPT_RAW.split('\n') if l.strip()]
DURS = [max(1.2, round(len(l)/RATE_REAL, 3)) for l in linhas_all]
diff = DUR_AUDIO - sum(DURS); DURS[0] = round(DURS[0]+diff, 3)
frases = linhas_all   # alias para compatibilidade com seção de imagens
N = len(frases)


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
fname = f"v{VIDEO_ID}_cb_v{VOICE_VERSION}_{ts}.mp4"
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
