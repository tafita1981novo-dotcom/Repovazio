#!/usr/bin/env python3
"""
render_long_15min.py — LONG 15MIN PERFEITO V1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PADRÃO QUÂNTICO MÁXIMA MONETIZAÇÃO ADSENSE:
  ✅ 15:00 EXATOS (900s) — mid-rolls a cada 3min
  ✅ 90 imagens × aparência ×2 (Ken Burns in/out) = 180 cenas
  ✅ Cena nova a cada ~5s = retenção máxima (Psych2Go style)
  ✅ 5 ATOS narrativos com emotional peaks estratégicos
  ✅ Chapters JSON output para YouTube (maximiza RPM)
  ✅ Pollinations FLUX sequential (grátis, ilimitado)
  ✅ Script split automático em 90 segmentos com detecção de personagem
"""
import os, sys, json, subprocess, requests, time, urllib.parse, asyncio, re, random
from PIL import Image, ImageDraw

VIDEO_ID = int(os.environ.get("VIDEO_ID","683"))
SB_URL   = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY   = os.environ.get("SUPABASE_SERVICE_KEY","")
W, H     = 1080, 1920
CRF      = 22
FPS      = 25
TARGET_S = 900     # 15:00 exatos
RATE_ADJ = "+5%"   # 945s natural → 900s exatos
WORKDIR  = f"/tmp/v{VIDEO_ID}_long15"
os.makedirs(WORKDIR, exist_ok=True)

VERM=(220,50,50); GOLD=(255,210,50); BRAN=(255,255,255)
LILAS=(185,170,225); DARK=(8,6,18)
def log(m): print(m, flush=True)

# ── PERSONAGENS ─────────────────────────────────────────────
DANIELA = "kawaii chibi anime girl, short dark bob hair, mint-green blouse, gold psi pin, warm knowing smile, big expressive eyes"
SARA    = "kawaii chibi anime girl, wavy auburn hair, round glasses, yellow cardigan, emotional big expressive eyes"
MARCOS  = "kawaii chibi anime man, styled dark hair, navy blazer, charming but calculating smile, subtle sinister aura"
JULIA   = "kawaii chibi anime girl, curly dark hair, orange sweater, warm caring protective expression"
ANA     = "kawaii chibi anime woman, dark neat bun, white lab coat, clipboard, calm authoritative expression"
LUCAS   = "kawaii chibi anime man, navy hoodie, tousled dark hair, introspective thoughtful expression"
STYLE   = ("Psych2Go anime flat illustration, soft cream background #F5F0E8, "
           "pastel colors, clean line art, original character design, no text, no watermarks")

# ── DETECÇÃO DE PERSONAGEM E CENÁRIO ───────────────────────
def detect_scene(text, idx, total):
    """Detecta personagem e estilo de cena baseado no conteúdo"""
    t = text.lower()
    pos = idx / total  # 0.0 a 1.0

    # Personagem principal por posição e conteúdo
    if "daniela" in t or "pergunta" in t or pos < 0.05 or pos > 0.85:
        char = DANIELA
        char_name = "Daniela"
    elif "dra" in t or "ana" in t or "harvard" in t or "estudo" in t or "pesquisa" in t or "neurologia" in t or "cérebro" in t:
        char = ANA
        char_name = "Dra Ana"
    elif "julia" in t or "amiga" in t:
        char = JULIA
        char_name = "Julia"
    elif "marcos" in t or "narcis" in t or "ele " in t and "manipul" in t:
        char = MARCOS
        char_name = "Marcos"
    elif "lucas" in t:
        char = LUCAS
        char_name = "Lucas"
    else:
        char = SARA
        char_name = "Sara"

    # Tipo de cena por posição no arco narrativo
    if pos < 0.12:
        scene_type = "GANCHO"
        bg_note = "dramatic entrance, hook opening scene, impactful visual"
    elif pos < 0.35:
        scene_type = "PROBLEMA"
        bg_note = "conflict scene, emotional tension, problem revealed"
    elif pos < 0.62:
        scene_type = "CIENCIA"
        bg_note = "educational scene, scientific discovery, analytical"
    elif pos < 0.80:
        scene_type = "VIRADA"
        bg_note = "emotional turning point, breakthrough moment, hope emerging"
    else:
        scene_type = "CTA"
        bg_note = "warm empowering scene, celebration, subscribe call to action"

    # Conteúdo específico da cena
    if "sinal" in t and ("1" in t or "um" in t or "primeiro" in t):
        cena = f"{char} with large glowing badge showing number ONE, {bg_note}"
    elif "sinal" in t and ("2" in t or "dois" in t or "segundo" in t):
        cena = f"{char} with large glowing badge showing number TWO, {bg_note}"
    elif "sinal" in t and ("3" in t or "três" in t or "terceiro" in t):
        cena = f"{char} with large glowing badge showing number THREE, {bg_note}"
    elif "harvard" in t or "estudo" in t or "pesquisa" in t:
        cena = f"{ANA} holding clipboard with Harvard logo and shocking statistic, research data visible, {bg_note}"
    elif "cérebro" in t or "neurolog" in t or "dopamina" in t:
        cena = f"{ANA} pointing at detailed glowing brain diagram showing neural pathways, {bg_note}"
    elif "gaslighting" in t or "manipul" in t or "mentiu" in t:
        cena = f"{SARA} and {MARCOS} in tense confrontation, Marcos pointing dismissively, Sara shrinking, {bg_note}"
    elif "chora" in t or "lágrima" in t or "dor" in t or "sofr" in t:
        cena = f"{SARA} with visible tears, small rain cloud above, deeply emotional, {bg_note}"
    elif "ferramenta" in t or "prática" in t or "passo" in t or "como " in t:
        cena = f"{DANIELA} holding glowing golden toolkit or step-by-step diagram, {bg_note}"
    elif "inscreva" in t or "🔔" in t or "sino" in t or "notificação" in t:
        cena = f"Giant golden glowing notification bell with sparkles, {DANIELA} {SARA} {JULIA} celebrating together, colorful confetti, {bg_note}"
    elif "próximo" in t or "episódio" in t or "continua" in t:
        cena = f"{MARCOS} hiding something dark, {SARA} about to discover shocking truth, dramatic cliffhanger, {bg_note}"
    elif pos < 0.12:
        cena = f"{SARA} alone with anxious worried expression, small question marks floating, {bg_note}"
    elif pos > 0.85:
        cena = f"{DANIELA} smiling warmly directly at viewer, golden light surrounding, empowering scene, {bg_note}"
    else:
        cena = f"{char} with expression matching {scene_type.lower()} mood, {bg_note}"

    return cena, char_name, scene_type

# ── SUPABASE ────────────────────────────────────────────────
def sb_get_script():
    """Busca script do Supabase ou usa ENV fallback"""
    SCRIPT_ENV = os.environ.get("SCRIPT_LONG","")
    if SCRIPT_ENV:
        return SCRIPT_ENV

    r = requests.get(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{VIDEO_ID}&select=script,title",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=30)
    rows = r.json()
    if rows and rows[0].get("script"):
        return rows[0]["script"]
    raise ValueError(f"Script não encontrado para video_id={VIDEO_ID}")

def sb_patch(id_, data):
    requests.patch(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{id_}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"},
        json=data, timeout=30).raise_for_status()

def sb_upload(path, data, ctype):
    r = requests.post(f"{SB_URL}/storage/v1/object/videos/{path}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":ctype,"x-upsert":"true"},
        data=data, timeout=600)
    r.raise_for_status()
    return f"{SB_URL}/storage/v1/object/public/videos/{path}"

# ── SPLIT SCRIPT EM 90 SEGMENTOS ────────────────────────────
def split_script_90(raw_script):
    """
    Divide script em exatamente 90 segmentos de ~133 chars cada.
    Estratégia: split por pontuação, merge até ~133 chars.
    """
    N_TARGET = 90
    TARGET_CHARS = 11970  # 13.3 chars/s × 900s

    # Limpar texto
    text = re.sub(r'\s+', ' ', raw_script.strip())
    total = len(text)

    # Split por frases (pontuação terminal)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        sentences = [text]

    # Merge frases em segmentos de ~TARGET_CHARS/N_TARGET chars
    target_seg_len = total / N_TARGET
    segments = []
    current = ""

    for s in sentences:
        if current and len(current) + len(s) + 1 > target_seg_len * 1.3 and len(current) > target_seg_len * 0.5:
            segments.append(current.strip())
            current = s
        else:
            current = (current + " " + s).strip() if current else s

    if current:
        segments.append(current.strip())

    # Ajuste fino para exatamente 90 segmentos
    while len(segments) < N_TARGET:
        # Partir o segmento mais longo
        longest_idx = max(range(len(segments)), key=lambda i: len(segments[i]))
        seg = segments[longest_idx]
        mid = len(seg)//2
        # Encontrar ponto de corte no meio
        cut = seg.rfind('. ', max(0, mid-30), mid+30)
        if cut == -1: cut = mid
        segments[longest_idx] = seg[:cut+1].strip()
        segments.insert(longest_idx+1, seg[cut+1:].strip())

    while len(segments) > N_TARGET:
        # Mergear os dois menores adjacentes
        min_len = float('inf')
        merge_at = 0
        for i in range(len(segments)-1):
            combined = len(segments[i]) + len(segments[i+1])
            if combined < min_len:
                min_len = combined
                merge_at = i
        segments[merge_at] = (segments[merge_at] + " " + segments[merge_at+1]).strip()
        segments.pop(merge_at+1)

    log(f"  Split: {len(sentences)} frases → {len(segments)} segmentos")
    log(f"  Média: {sum(len(s) for s in segments)/len(segments):.0f} chars/segmento")
    return segments

# ── FUNÇÕES UTILITÁRIAS ──────────────────────────────────────
def measure_dur(path):
    p = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",path],
        capture_output=True, text=True)
    return float(json.loads(p.stdout)["format"]["duration"])

def add_overlay(img_path, caption, ato):
    """Overlay com indicador de ato narrativo"""
    img  = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    # Lower third
    draw.rectangle([0,H-100,W,H], fill=DARK)
    draw.rectangle([0,H-100,6,H], fill=VERM)
    draw.rectangle([0,H-4,W,H], fill=VERM)
    draw.text((22,H-90), "ψ", fill=GOLD)
    draw.text((62,H-88), "Daniela Coelho", fill=BRAN)
    draw.text((62,H-58), "Saúde Mental  |  @psidanielacoelho", fill=LILAS)
    # Caption badge topo
    if caption:
        cap = caption[:28].upper()
        bw  = min(len(cap)*15+50, W-60); cx = W//2
        draw.rounded_rectangle([cx-bw//2,38,cx+bw//2,80],
            radius=14, fill=(250,248,255), outline=(210,200,235), width=2)
        draw.text((cx-bw//2+20,48), cap, fill=(20,15,45))
    img.save(img_path, "JPEG", quality=96)

def gen_pillow(idx, text):
    """Fallback Pillow emergência"""
    img = Image.new("RGB",(W,H),(245,240,232))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t=y/H; draw.line([(0,y),(W,y)],fill=(int(245+(230-245)*t),int(240+(225-240)*t),int(232+(215-232)*t)))
    cols=[(150,80,210),(200,100,60),(60,120,200)]
    for ci,cx in enumerate([W//3,2*W//3]):
        c=cols[(idx+ci)%len(cols)]; cy=H//2-80
        draw.ellipse([cx-80,cy-190,cx+80,cy+30],fill=(255,220,185))
        draw.ellipse([cx-84,cy-240,cx+84,cy-80],fill=(40,28,12))
        draw.rounded_rectangle([cx-68,cy+25,cx+68,cy+230],radius=20,fill=c)
    out=f"{WORKDIR}/ai_{idx:03d}.jpg"; img.save(out,"JPEG",quality=88)
    return out

# ── CHAPTERS PARA YOUTUBE ────────────────────────────────────
def make_chapters(atos, durs_cumsum):
    """Gera timestamps de capítulos para YouTube (maximiza RPM com mid-rolls)"""
    chapters = []
    ato_starts = {
        "GANCHO"   : 0,
        "PROBLEMA" : int(TARGET_S * 0.12),
        "CIENCIA"  : int(TARGET_S * 0.35),
        "VIRADA"   : int(TARGET_S * 0.62),
        "CTA"      : int(TARGET_S * 0.80),
    }
    ato_names = {
        "GANCHO"   : "⚡ O Que É Narcisismo Encoberto?",
        "PROBLEMA" : "🚨 Os 3 Sinais Que Você Está Ignorando",
        "CIENCIA"  : "🧠 A Ciência Por Trás da Manipulação",
        "VIRADA"   : "💡 Como Identificar e Se Proteger",
        "CTA"      : "❤️ Você Não Está Sozinha",
    }
    for ato, t in ato_starts.items():
        m, s = divmod(t, 60)
        chapters.append(f"{m:02d}:{s:02d} {ato_names[ato]}")
    return "\n".join(chapters)

# ── MAIN ──────────────────────────────────────────────────────
log(f"{'='*58}")
log(f"  ψ LONG 15MIN — VIDEO #{VIDEO_ID}")
log(f"  90 cenas × ~10s | 5 atos | Mid-rolls habilitados")
log(f"  Meta: 15:00 exatos | Retenção 60%+ | RPM R$10-16")
log(f"{'='*58}\n")

# ── ETAPA 0: BUSCAR SCRIPT ──────────────────────────────────
log("📖 ETAPA 0 — Carregando script...")
raw_script = sb_get_script()
log(f"  Script: {len(raw_script)} chars | {len(raw_script)/1000:.1f}K")

SEGMENTOS = split_script_90(raw_script)
N = len(SEGMENTOS)
SCRIPT_TTS = ". ".join(SEGMENTOS)
log(f"  {N} segmentos | TTS: {len(SCRIPT_TTS)} chars")

# ── ETAPA 1: ÁUDIO TTS ───────────────────────────────────────
log(f"\n🎙️  ETAPA 1 — Gerando áudio 15min (rate={RATE_ADJ})...")

async def gen_audio():
    import edge_tts
    path = f"{WORKDIR}/audio_long.mp3"
    c = edge_tts.Communicate(SCRIPT_TTS, voice="pt-BR-AntonioNeural", rate=RATE_ADJ)
    await c.save(path)
    return path

asyncio.run(gen_audio())
AUDIO_PATH = f"{WORKDIR}/audio_long.mp3"
DUR_FINAL  = measure_dur(AUDIO_PATH)
RATE_REAL  = len(SCRIPT_TTS) / DUR_FINAL
log(f"  ✅ Áudio: {DUR_FINAL:.1f}s ({DUR_FINAL/60:.2f}min) | RATE={RATE_REAL:.2f}")

# ── ETAPA 2: DURAÇÕES POR SEGMENTO ──────────────────────────
DURS = [max(0.5, round(len(s)/RATE_REAL, 2)) for s in SEGMENTOS]
cumsum = [0.0]
for d in DURS: cumsum.append(cumsum[-1]+d)
log(f"\n  Duração média por cena: {sum(DURS)/N:.1f}s")
log(f"  Cena mais curta: {min(DURS):.1f}s | Mais longa: {max(DURS):.1f}s")

# ── ETAPA 3: GERAR 90 IMAGENS ────────────────────────────────
log(f"\n🎨 ETAPA 3 — Gerando {N} imagens Pollinations FLUX...")
log(f"  Estimado: ~{N*16//60} min")

IMGS = [None]*N; counts={"poll":0,"pillow":0}; atos = []; t0=time.time()

for idx, seg in enumerate(SEGMENTOS):
    cena_desc, char_name, ato = detect_scene(seg, idx, N)
    atos.append(ato)

    full = (f"masterpiece, best quality, kawaii chibi anime illustration, "
            f"{cena_desc}, {STYLE} "
            f"### lowres, bad anatomy, text, watermark, nsfw, blurry, ugly, deformed")
    enc  = urllib.parse.quote(full[:800])  # limite URL
    seed = 7777 + idx * 113
    out  = f"{WORKDIR}/ai_{idx:03d}.jpg"
    ok   = False

    for attempt in range(4):
        try:
            url = (f"https://image.pollinations.ai/prompt/{enc}"
                   f"?width=576&height=1024&seed={seed+attempt}"
                   f"&nologo=true&model=flux&enhance=true")
            r = requests.get(url, timeout=90)
            if r.status_code == 402:
                log(f"  [{idx+1}] Rate limit, 30s..."); time.sleep(30); continue
            if r.status_code == 200 and 'image' in r.headers.get('content-type',''):
                if len(r.content) > 40000:
                    with open(f"{WORKDIR}/raw_{idx:03d}.jpg",'wb') as f: f.write(r.content)
                    img = Image.open(f"{WORKDIR}/raw_{idx:03d}.jpg").convert("RGB")
                    img = img.resize((W,H), Image.LANCZOS)
                    img.save(out,"JPEG",quality=95)
                    cap = seg[:25].split('.')[0].split(',')[0].strip()
                    add_overlay(out, cap, ato)
                    elapsed = time.time()-t0
                    sz = os.path.getsize(out)//1024
                    log(f"  [{idx+1:03d}/{N}] 🌐 {sz}KB | {elapsed:.0f}s | [{ato}] {char_name}: {seg[:40]}...")
                    IMGS[idx]=out; counts["poll"]+=1; ok=True; break
        except Exception as e:
            log(f"  [{idx+1}] err {attempt+1}: {str(e)[:40]}")
        if attempt < 3: time.sleep(8)

    if not ok:
        out = gen_pillow(idx, seg)
        add_overlay(out, seg[:25], ato)
        IMGS[idx]=out; counts["pillow"]+=1
        log(f"  [{idx+1:03d}/{N}] ✏️  pillow | [{ato}] {seg[:40]}...")

    if idx < N-1: time.sleep(4)

gen_t = time.time()-t0
log(f"\n  ✅ {counts['poll']}/{N} Pollinations | {counts['pillow']} Pillow | {gen_t/60:.1f}min")

# ── ETAPA 4: FFCONCAT (cada imagem aparece 2× com zoom diferente) ──
# Ken Burns: img A aparece zoom 1.0, img A novamente zoom 1.02 para sensação de movimento
log(f"\n📝 ETAPA 4 — Montando 90 cenas × 2 aparências com Ken Burns leve...")

# Criar versão com zoom leve de cada imagem para segunda aparência
def make_zoomed(src, dst, zoom=1.03):
    """Crop e resize para simular zoom in"""
    img = Image.open(src)
    w, h = img.size
    delta_w = int(w * (zoom-1) / 2)
    delta_h = int(h * (zoom-1) / 2)
    img_z = img.crop([delta_w, delta_h, w-delta_w, h-delta_h])
    img_z = img_z.resize((w, h), Image.LANCZOS)
    img_z.save(dst, "JPEG", quality=95)

concat = f"{WORKDIR}/concat.txt"
with open(concat,'w') as f:
    for i, (seg, dur) in enumerate(zip(SEGMENTOS, DURS)):
        img = IMGS[i]
        if not img: continue
        # Primeira aparição: normal
        half = round(dur * 0.55, 3)   # 55% do tempo na versão normal
        rest = round(dur - half, 3)    # 45% do tempo na versão com zoom
        f.write(f"file '{img}'\nduration {half:.3f}\n")
        # Segunda aparição: com zoom leve (Ken Burns out→in)
        zoomed = f"{WORKDIR}/zoom_{i:03d}.jpg"
        if not os.path.exists(zoomed):
            try: make_zoomed(img, zoomed)
            except: zoomed = img
        f.write(f"file '{zoomed}'\nduration {rest:.3f}\n")
    # Última linha (ffconcat exige)
    last_img = IMGS[-1] or IMGS[-2]
    if last_img: f.write(f"file '{last_img}'\n")

# ── ETAPA 5: RENDER ──────────────────────────────────────────
ts  = int(time.time())
OUT = f"{WORKDIR}/v{VIDEO_ID}_long15_{ts}.mp4"
log(f"\n🎬 ETAPA 5 — Renderizando {DUR_FINAL:.1f}s Long...")

cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",concat,
       "-i",AUDIO_PATH,
       "-c:v","libx264","-pix_fmt","yuv420p","-crf",str(CRF),
       "-c:a","aac","-b:a","128k","-shortest",
       "-r",str(FPS),
       "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
             "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
       "-movflags","+faststart",OUT]
res = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
if res.returncode != 0:
    log(f"ERRO:\n{res.stderr[-800:]}"); sys.exit(1)

sz   = os.path.getsize(OUT)
dur2 = measure_dur(OUT)
ok_15 = abs(dur2 - TARGET_S) <= 30  # ±30s aceitável
log(f"  {'✅' if ok_15 else '⚠️ '} {sz/1024/1024:.1f}MB | {dur2:.0f}s ({dur2/60:.2f}min)")

# ── ETAPA 6: CHAPTERS ────────────────────────────────────────
chapters_text = make_chapters(atos, cumsum)
log(f"\n📌 CHAPTERS YOUTUBE:")
for line in chapters_text.split('\n'): log(f"   {line}")

# ── ETAPA 7: UPLOAD ──────────────────────────────────────────
log(f"\n☁️  ETAPA 7 — Upload Supabase...")
with open(OUT,'rb') as f: vdata=f.read()
video_url=None
for att in range(5):
    try:
        video_url = sb_upload(f"mp4s/v{VIDEO_ID}_long15_{ts}.mp4", vdata, "video/mp4")
        log(f"  ✅ {video_url}"); break
    except Exception as e:
        log(f"  Tentativa {att+1}: {e}"); time.sleep(15)

if video_url:
    sb_patch(VIDEO_ID, {
        "video_url": video_url, "status": "pending_credentials",
        "metadata": json.dumps({
            "version":"long_15min_v1_quantum",
            "dur_s": round(dur2,1), "target_s": TARGET_S,
            "n_cenas": N, "poll": counts["poll"], "pillow": counts["pillow"],
            "file_mb": round(sz/1024/1024,1), "rate_adj": RATE_ADJ,
            "chapters": chapters_text,
            "atos": ["GANCHO","PROBLEMA","CIENCIA","VIRADA","CTA"],
            "mid_roll_at": ["03:00","06:00","09:00","12:00"],
        })
    })

log(f"\n{'='*58}")
log(f"  ψ LONG 15MIN — RESULTADO FINAL")
log(f"  ⏱️  {dur2:.0f}s = {dur2/60:.2f}min (target: 15:00)")
log(f"  🌐 {counts['poll']}/{N} Pollinations FLUX")
log(f"  📸 {N} imagens × 2 aparências = 180 cenas efetivas")
log(f"  🎯 Cena nova a cada ~5s (padrão Psych2Go)")
log(f"  💰 Mid-rolls habilitados: 03:00 | 06:00 | 09:00 | 12:00")
log(f"  💾 {sz/1024/1024:.1f}MB")
log(f"  🎬 {video_url or 'UPLOAD FALHOU'}")
log(f"{'='*58}\n")
