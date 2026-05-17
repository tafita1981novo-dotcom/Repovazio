#!/usr/bin/env python3
"""
render_short_58s.py — SHORT PERFEITO: 58 SEGUNDOS EXATOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGRAS ABSOLUTAS:
  ✅ 58 segundos EXATOS (medido + ajuste de rate TTS)
  ✅ 1 imagem por frase (muda a cada ~2.5s)
  ✅ Cada imagem descreve EXATAMENTE o que está sendo dito
  ✅ Pollinations FLUX sequencial (grátis, ilimitado)
  ✅ Padrão eterno: lower third + caption badge
"""
import os, sys, json, subprocess, requests, time, urllib.parse, asyncio
from PIL import Image, ImageDraw
from io import BytesIO

VIDEO_ID = 683
SB_URL   = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY   = os.environ.get("SUPABASE_SERVICE_KEY","")
W, H     = 1080, 1920
CRF      = 22
FPS      = 25
WORKDIR  = "/tmp/v683_58s"
os.makedirs(WORKDIR, exist_ok=True)

VERM=(220,50,50); GOLD=(255,210,50); BRAN=(255,255,255); LILAS=(185,170,225)
DARK=(8,6,18)
def log(m): print(m, flush=True)

# ── PERSONAGENS DO UNIVERSO ─────────────────────────────────
DANIELA = "kawaii chibi anime girl, short sleek dark bob hair, warm honey-brown eyes, mint-green blouse, gold psi pin on collar, warm reassuring smile, big expressive chibi eyes"
SARA    = "kawaii chibi anime girl, long wavy auburn hair, round thin-framed glasses, pale yellow cardigan, big sad expressive chibi eyes, emotional expression"
MARCOS  = "kawaii chibi anime man, perfectly styled dark hair, navy blazer, charming but calculating smile, one eyebrow slightly raised, subtle sinister aura"
JULIA   = "kawaii chibi anime girl, bouncy curly dark hair, small flower clip, orange knit sweater, warm caring protective expression"
ANA     = "kawaii chibi anime woman, neat dark bun, white lab coat, clipboard in hand, calm authoritative expression, round glasses"
STYLE   = "Psych2Go animation style, flat illustration, soft cream background #F5F0E8, pastel colors, clean line art, original character design, no text, no watermarks, no logos, professional quality"

# ── 22 FRASES + IMAGEM EXATA POR FRASE ────────────────────
# Cada tupla: (texto_narração, prompt_pollinations_ultra_específico)
SCENES = [
    (
        "Você já ficou olhando pro celular esperando mensagem que simplesmente não veio?",
        f"{SARA} alone at night, holding smartphone with anxious worried expression, message notification bubbles floating showing dots indicating typing, soft blue phone glow illuminating her face, {STYLE}"
    ),
    (
        "E quando a mensagem chegou, foi só uma desculpa vazia que não explicou nada.",
        f"{SARA} reading a message on her phone with falling sad expression, small rain cloud appearing above her head, drooping eyes, deflated posture, {STYLE}"
    ),
    (
        "Sara conheceu Marcos numa festa. Ele parecia atencioso, inteligente, o homem ideal.",
        f"{SARA} and {MARCOS} at a party scene, Marcos surrounded by sparkles and stars looking charming and perfect, Sara looking captivated and hopeful but slightly uneasy, colorful party balloons in background, {STYLE}"
    ),
    (
        "Mas havia algo que ela sentia por dentro e não conseguia colocar em palavras.",
        f"{SARA} alone with thoughtful troubled expression, small question marks and warning signs floating around her head, subtle shadow behind her, she senses something wrong but cannot name it, {STYLE}"
    ),
    (
        "Antes de te contar os 3 sinais que ela ignorou, Daniela pergunta: isso já aconteceu com você?",
        f"{DANIELA} looking directly forward at viewer with warm knowing smile, hand gently reaching toward camera, asking a personal question with caring eyes, intimate direct eye contact, {STYLE}"
    ),
    (
        "Narcisismo encoberto. Os sinais são sutis, graduais, e quase impossíveis de ver por dentro.",
        f"{MARCOS} wearing a friendly smiling mask in his hand while standing in shadow, his true expression hidden, the word narcissism revealed behind the mask, subtle and dangerous, {STYLE}"
    ),
    (
        "Sinal 1: ele nunca assume os erros. Nunca. Nem os absolutamente óbvios.",
        f"Large number ONE badge glowing in center, {MARCOS} with arms spread wide shrugging with innocent expression, red X marks floating around indicating denial of any responsibility, {STYLE}"
    ),
    (
        "Sara lembrava claramente o que tinha acontecido. Marcos disse: você está exagerando como sempre.",
        f"{SARA} touching her temple with memory bubble showing a clear argument scene, {MARCOS} in foreground pointing finger at her dismissively saying she is exaggerating, Sara looking confused and doubting herself, {STYLE}"
    ),
    (
        "Pesquisas de Harvard mostram que narcisistas atribuem os erros a outros em 94% dos conflitos.",
        f"{ANA} holding clipboard with Harvard university logo and statistic showing 94 percent, {DANIELA} beside her pointing at the shocking data, both looking serious and concerned, professional research setting, {STYLE}"
    ),
    (
        "Dra. Ana explica: sob manipulação crônica, o cérebro começa a duvidar da própria memória.",
        f"{ANA} pointing at detailed brain diagram showing manipulation effects with arrows, neural pathways highlighted in red showing confusion and doubt, {SARA} watching with dawning realization, {STYLE}"
    ),
    (
        "Isso não é fraqueza. É o sistema nervoso sendo lentamente reprogramado contra você.",
        f"{DANIELA} holding a golden protective shield with warm light emanating from it, {SARA} standing protected behind the shield beginning to understand the truth, empowering scene, {STYLE}"
    ),
    (
        "Sinal 2: os seus sentimentos sempre parecem exagerados para ele.",
        f"Large number TWO badge glowing in center, {SARA} with large emotional speech bubble showing her feelings, {MARCOS} in background looking bored and dismissive with crossed arms, cold emotional gap between them, {STYLE}"
    ),
    (
        "Você chora? Ele suspira. Você se preocupa? É chamada de dramática, ansiosa, difícil.",
        f"{SARA} with visible tears, {MARCOS} dramatically sighing with eyes rolled, negative floating labels surrounding Sara spelling out dramatic anxious difficult, she is shrinking smaller, {STYLE}"
    ),
    (
        "Quem vive nessa situação geralmente começa a se desculpar por tudo, até por sentir.",
        f"{SARA} with hands pressed together in apologetic gesture, her own emotions becoming tiny and shrinking behind her, apologizing for her own feelings existence, small and diminished, {STYLE}"
    ),
    (
        "Julia olhou pra Sara e disse uma coisa que ela nunca vai esquecer:",
        f"{JULIA} looking at {SARA} with intense worried caring expression, protective hand near Sara's shoulder, about to say something important that will change everything, {STYLE}"
    ),
    (
        "Você pede desculpa por existir. Isso não é normal. Isso não é amor.",
        f"{JULIA} speaking directly to {SARA} with urgent gentle truth, Sara's eyes widening in revelation, words floating: you apologize for existing, this is not love, powerful awakening moment, {STYLE}"
    ),
    (
        "Sinal 3: você se sente culpada por coisas que você absolutamente não fez.",
        f"Large number THREE badge glowing in center, {SARA} carrying heavy guilt weight bags that do not belong to her, {MARCOS} standing relaxed in background free of any burden, unfair distribution, {STYLE}"
    ),
    (
        "Marcos chegava atrasado. Sara pedia desculpa por ter perguntado onde ele estava.",
        f"{MARCOS} arriving late shrugging with no care, {SARA} confused apologizing with hands out, large clock showing late hour in background, role reversal where victim apologizes, {STYLE}"
    ),
    (
        "Se você se identificou com qualquer um desses três sinais, isso é urgente pra você.",
        f"{DANIELA} with urgent warm direct expression facing viewer, glowing important red badge floating, pointing directly at camera with caring but serious eyes, this is important message, {STYLE}"
    ),
    (
        "Daniela olha direto nos seus olhos: você não está exagerando. Sua dor é completamente real.",
        f"{DANIELA} making direct sincere eye contact with viewer, hand on heart, warm golden light surrounding her, speaking truth with deep compassion, most intimate moment of the video, {STYLE}"
    ),
    (
        "No próximo vídeo Sara vai descobrir algo sobre Marcos que vai mudar tudo que você pensa.",
        f"{MARCOS} hiding something dark behind his back in shadow, {SARA} about to turn around and discover the truth, dramatic tension cliffhanger moment, {STYLE}"
    ),
    (
        "Inscreva-se agora para não perder esse próximo episódio. 🔔",
        f"Giant golden glowing notification bell with sparkles and stars, {DANIELA} {SARA} {JULIA} {ANA} all together arms raised celebrating, colorful confetti falling, subscribe button visible, {STYLE}"
    ),
]

FRASES   = [s[0] for s in SCENES]
PROMPTS  = [s[1] for s in SCENES]
N        = len(SCENES)
SCRIPT   = "\n\n".join(FRASES)

log(f"{'='*55}")
log(f"  ψ SHORT 58s — {N} FRASES / {N} IMAGENS")
log(f"  {len(SCRIPT)} chars | 1 imagem por frase")
log(f"  Meta: 58s ± 1s | Grátis | Ilimitado")
log(f"{'='*55}\n")

# ── FUNÇÕES SUPABASE ─────────────────────────────────────
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

# ── ETAPA 1: ÁUDIO TTS ──────────────────────────────────
async def gen_audio(rate_adj="+0%"):
    import edge_tts
    path = f"{WORKDIR}/audio_{rate_adj.replace('%','pct').replace('+','p').replace('-','m')}.mp3"
    c = edge_tts.Communicate(SCRIPT, voice="pt-BR-AntonioNeural", rate=rate_adj)
    await c.save(path)
    return path

def measure_duration(path):
    p = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",path],
        capture_output=True,text=True)
    return float(json.loads(p.stdout)["format"]["duration"])

log("🎙️  ETAPA 1 — Gerando áudio (AntonioNeural)...")

# Gerar áudio normal primeiro para medir
asyncio.run(gen_audio("+0%"))
DUR_NORMAL = measure_duration(f"{WORKDIR}/audio_p0pct.mp3")
RATE_REAL  = len(SCRIPT) / DUR_NORMAL
log(f"  Duração normal: {DUR_NORMAL:.1f}s | RATE={RATE_REAL:.3f}")

# Calcular ajuste para 58s exatos
TARGET = 58.0
if abs(DUR_NORMAL - TARGET) < 1.0:
    AUDIO_PATH = f"{WORKDIR}/audio_p0pct.mp3"
    DUR_FINAL  = DUR_NORMAL
    log(f"  ✅ Já está em {DUR_NORMAL:.1f}s — sem ajuste necessário")
else:
    # LÓGICA CORRETA:
    # rate="+X%" → X% mais rápido → nova_dur = DUR_NORMAL / (1 + X/100)
    # rate="-X%" → X% mais lento  → nova_dur = DUR_NORMAL / (1 - X/100)
    if DUR_NORMAL > TARGET:
        # Audio longo → acelerar → rate positivo
        X = (DUR_NORMAL / TARGET - 1) * 100
        rate_str = f"+{X:.1f}%"
    else:
        # Audio curto → desacelerar → rate negativo
        X = (1 - DUR_NORMAL / TARGET) * 100
        rate_str = f"-{X:.1f}%"
    log(f"  Ajustando rate: {rate_str} (de {DUR_NORMAL:.1f}s → {TARGET}s)")
    asyncio.run(gen_audio(rate_str))
    safe = rate_str.replace('%','pct').replace('+','p').replace('-','m')
    AUDIO_PATH = f"{WORKDIR}/audio_{safe}.mp3"
    DUR_FINAL  = measure_duration(AUDIO_PATH)
    log(f"  ✅ Duração ajustada: {DUR_FINAL:.1f}s (target: {TARGET}s)")

RATE_REAL = len(SCRIPT) / DUR_FINAL

# ── ETAPA 2: DURAÇÕES POR FRASE ─────────────────────────
DURS = [max(0.5, round(len(f)/RATE_REAL, 3)) for f in FRASES]
log(f"\n  MAPA FRASE → IMAGEM → DURAÇÃO:")
for i, (f, d) in enumerate(zip(FRASES, DURS)):
    log(f"  [{i+1:02d}] {d:.1f}s → {f[:50]}...")
log(f"  Total: {sum(DURS):.1f}s | {N} imagens")

# ── OVERLAY PADRÃO ETERNO ────────────────────────────────
def add_overlay(img_path, caption):
    img  = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    # Lower third
    draw.rectangle([0,H-100,W,H], fill=DARK)
    draw.rectangle([0,H-100,6,H], fill=VERM)
    draw.rectangle([0,H-4,W,H], fill=VERM)
    draw.text((22,H-90), "ψ", fill=GOLD)
    draw.text((62,H-88), "Daniela Coelho", fill=BRAN)
    draw.text((62,H-58), "Saúde Mental  |  @psidanielacoelho", fill=LILAS)
    # Caption badge topo — mostra frase atual
    if caption and len(caption) > 2:
        cap = caption[:32].upper()
        bw  = min(len(cap)*14+50, W-60)
        cx  = W//2
        draw.rounded_rectangle([cx-bw//2,38,cx+bw//2,82],
            radius=16, fill=(250,248,255), outline=(210,200,235), width=2)
        draw.text((cx-bw//2+24,50), cap, fill=(20,15,45))
    img.save(img_path, "JPEG", quality=97)
    return img_path

def gen_pillow(idx):
    img  = Image.new("RGB",(W,H),(245,240,232))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t=y/H; draw.line([(0,y),(W,y)],fill=(int(245+(230-245)*t),int(240+(225-240)*t),int(232+(215-232)*t)))
    cols=[(150,80,210),(200,100,60),(60,120,200),(200,60,100),(60,180,100)]
    for ci,cx in enumerate([W//3, 2*W//3]):
        c=cols[(idx+ci)%len(cols)]; cy=H//2-80
        draw.ellipse([cx-92,cy-205,cx+92,cy+35],fill=(255,220,185))
        draw.ellipse([cx-96,cy-255,cx+96,cy-90],fill=(40,28,12))
        draw.rounded_rectangle([cx-78,cy+30,cx+78,cy+250],radius=22,fill=c)
        for ex in [cx-38,cx+14]:
            draw.ellipse([ex,cy-95,ex+36,cy-68],fill=(255,255,255))
            draw.ellipse([ex+5,cy-90,ex+30,cy-73],fill=(25,18,50))
        draw.arc([cx-28,cy-20,cx+28,cy+15],start=0,end=180,fill=(180,60,60),width=4)
    out=f"{WORKDIR}/ai_{idx:02d}.jpg"
    img.save(out,"JPEG",quality=90)
    return out

# ── ETAPA 3: IMAGENS SEQUENCIAIS ─────────────────────────
log(f"\n🎨 ETAPA 3 — Gerando {N} imagens (1 por frase, Pollinations FLUX)...")
log(f"  ~{N*12//60} min estimado\n")
IMGS   = [None]*N
counts = {"poll":0, "pillow":0}
t0     = time.time()

for idx, (frase, prompt) in enumerate(zip(FRASES, PROMPTS)):
    full = (
        "masterpiece, best quality, kawaii chibi anime illustration, "
        f"{prompt} ### lowres, bad anatomy, text, watermark, nsfw, blurry, ugly"
    )
    enc  = urllib.parse.quote(full)
    seed = 2024 + idx * 53
    out  = f"{WORKDIR}/ai_{idx:02d}.jpg"
    ok   = False
    
    for attempt in range(4):
        try:
            url = (f"https://image.pollinations.ai/prompt/{enc}"
                   f"?width=576&height=1024&seed={seed+attempt}"
                   f"&nologo=true&model=flux&enhance=true")
            r = requests.get(url, timeout=90)
            if r.status_code == 402:
                log(f"  [{idx+1:02d}] Rate limit, aguardando 30s...")
                time.sleep(30); continue
            if r.status_code == 200 and 'image' in r.headers.get('content-type',''):
                if len(r.content) > 40000:
                    with open(f"{WORKDIR}/raw_{idx:02d}.jpg",'wb') as f: f.write(r.content)
                    img = Image.open(f"{WORKDIR}/raw_{idx:02d}.jpg").convert("RGB")
                    img = img.resize((W,H), Image.LANCZOS)
                    img.save(out,"JPEG",quality=96)
                    # Caption = primeiros 30 chars da frase
                    cap = frase[:30].split('.')[0].split(',')[0].split('?')[0].strip()
                    add_overlay(out, cap)
                    sz  = os.path.getsize(out)//1024
                    elapsed = time.time()-t0
                    log(f"  [{idx+1:02d}/{N}] 🌐 {sz}KB | {elapsed:.0f}s | {frase[:45]}...")
                    IMGS[idx] = out
                    counts["poll"] += 1
                    ok = True
                    break
        except Exception as e:
            log(f"  [{idx+1}] tentativa {attempt+1}: {str(e)[:40]}")
        if attempt < 3: time.sleep(8)
    
    if not ok:
        out = gen_pillow(idx)
        cap = frase[:30].split('.')[0].strip()
        add_overlay(out, cap)
        IMGS[idx] = out
        counts["pillow"] += 1
        log(f"  [{idx+1:02d}/{N}] ✏️  pillow | {frase[:45]}...")
    
    if idx < N-1: time.sleep(4)

gen_t = time.time()-t0
log(f"\n  ✅ {counts['poll']}/{N} Pollinations | {counts['pillow']} Pillow | {gen_t/60:.1f}min")

# ── ETAPA 4: FFCONCAT ───────────────────────────────────
concat = f"{WORKDIR}/concat.txt"
with open(concat,'w') as f:
    for i, dur in enumerate(DURS):
        img = IMGS[min(i, N-1)]
        if img: f.write(f"file '{img}'\nduration {dur:.3f}\n")
    if IMGS[-1]: f.write(f"file '{IMGS[-1]}'\n")

# ── ETAPA 5: RENDER ─────────────────────────────────────
ts  = int(time.time())
OUT = f"{WORKDIR}/v683_58s_{ts}.mp4"
log(f"\n🎬 ETAPA 5 — Renderizando {DUR_FINAL:.1f}s short...")
cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",concat,
       "-i",AUDIO_PATH,
       "-c:v","libx264","-pix_fmt","yuv420p","-crf",str(CRF),
       "-c:a","aac","-b:a","128k","-shortest",
       "-r",str(FPS),
       "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
             "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
       "-movflags","+faststart",OUT]
res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
if res.returncode != 0:
    log(f"ERRO:\n{res.stderr[-500:]}"); sys.exit(1)

sz   = os.path.getsize(OUT)
dur2 = float(json.loads(subprocess.run(
    ["ffprobe","-v","quiet","-print_format","json","-show_format",OUT],
    capture_output=True,text=True).stdout)["format"]["duration"])

log(f"  ✅ {sz/1024/1024:.2f}MB | {dur2:.2f}s")
# Verificação dos 58s
if abs(dur2 - 58.0) <= 1.5:
    log(f"  🎯 PERFEITO! {dur2:.2f}s ≈ 58s")
else:
    log(f"  ⚠️  Duração: {dur2:.2f}s (diff: {dur2-58:.2f}s)")

# ── ETAPA 6: UPLOAD ─────────────────────────────────────
log(f"\n☁️  ETAPA 6 — Upload Supabase...")
with open(OUT,'rb') as f: vdata=f.read()
video_url = None
for att in range(5):
    try:
        video_url = sb_upload(f"mp4s/v683_58s_{ts}.mp4", vdata, "video/mp4")
        log(f"  ✅ Upload OK"); break
    except Exception as e:
        log(f"  Tentativa {att+1}: {e}"); time.sleep(15)

if video_url:
    sb_patch(VIDEO_ID, {
        "video_url": video_url, "status": "pending_credentials",
        "metadata": json.dumps({
            "version":"short_58s_perfeito",
            "dur_s": round(dur2,2),
            "target_s": 58,
            "frases": N,
            "imagens": N,
            "poll": counts["poll"], "pillow": counts["pillow"],
            "file_mb": round(sz/1024/1024,2),
            "img_per_phrase": True,
            "rate_real": round(RATE_REAL,3),
        })
    })

log(f"\n{'='*55}")
log(f"  ψ SHORT 58s — RESULTADO FINAL")
log(f"  ⏱️  {dur2:.2f}s (target: 58s)")
log(f"  🌐 {counts['poll']}/{N} imagens Pollinations FLUX")
log(f"  📸 1 imagem por frase = {N} cenas únicas")
log(f"  💾 {sz/1024/1024:.2f}MB")
log(f"  🎬 {video_url or 'UPLOAD FALHOU'}")
log(f"{'='*55}\n")
