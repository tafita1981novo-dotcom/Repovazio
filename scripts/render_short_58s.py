#!/usr/bin/env python3
"""
render_short_58s_final.py — SHORT 58s PERFEITO V3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORREÇÕES V3:
✅ SCRIPT ultra-curto: 836 chars → ~63s natural → +8% rate → 58s
✅ 20 frases × ~42 chars = ~2.9-3.5s por imagem (PERFEITO para Shorts)
✅ TTS joined com '. ' (SEM newlines = SEM pausas longas)
✅ rate="+8%" (levemente mais rápido, soa natural)
✅ RATE_REAL dinâmico medido do áudio final
✅ 1 imagem Pollinations por frase
✅ Padrão eterno: lower third + caption badge
"""
import os, sys, json, subprocess, requests, time, urllib.parse, asyncio
from PIL import Image, ImageDraw

VIDEO_ID = 683
SB_URL   = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY   = os.environ.get("SUPABASE_SERVICE_KEY","")
W, H     = 1080, 1920
CRF      = 22
FPS      = 25
TARGET   = 58.0
WORKDIR  = "/tmp/v683_58final"
os.makedirs(WORKDIR, exist_ok=True)

VERM=(220,50,50); GOLD=(255,210,50); BRAN=(255,255,255)
LILAS=(185,170,225); DARK=(8,6,18)
def log(m): print(m, flush=True)

# ── SUPABASE ────────────────────────────────────────────
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

# ── PERSONAGENS ─────────────────────────────────────────
DANIELA = "kawaii chibi anime girl, short dark bob hair, mint-green blouse, gold psi pin, warm smile, big expressive eyes"
SARA    = "kawaii chibi anime girl, wavy auburn hair, round glasses, yellow cardigan, emotional big eyes"
MARCOS  = "kawaii chibi anime man, styled dark hair, navy blazer, charming calculating smile"
JULIA   = "kawaii chibi anime girl, curly dark hair, orange sweater, warm caring expression"
ANA     = "kawaii chibi anime woman, dark bun, white lab coat, clipboard, authoritative calm expression"
STYLE   = "Psych2Go anime flat illustration, soft cream background #F5F0E8, pastel colors, clean line art, original design, no text, no watermarks"

# ── 20 FRASES + CENA EXATA (total ~836 chars → 63s → +8% = 58s) ──
SCENES = [
    # frase (curta ~40 chars), prompt pollinations (ultra específico)
    ("Você já esperou mensagem que não veio?",
     f"{SARA} alone at night holding phone with anxious expression, message notification '...' bubble floating, soft blue glow illuminating sad face, {STYLE}"),

    ("E quando veio foi só uma desculpa.",
     f"{SARA} reading phone message with disappointed falling expression, small rain cloud above head, drooping sad eyes, {STYLE}"),

    ("Daniela pergunta: isso acontece com você?",
     f"{DANIELA} looking directly at viewer with warm knowing smile, hand reaching toward camera asking personal question, intimate direct eye contact, {STYLE}"),

    ("Narcisismo encoberto. Você precisa saber.",
     f"{MARCOS} holding friendly smiling mask while sinister shadow lurks behind him, dangerous hidden truth revealed, {STYLE}"),

    ("Sinal 1: ele nunca assume os erros.",
     f"Large glowing number ONE badge, {MARCOS} shrugging both hands raised with exaggerated innocent expression, red X marks around denying responsibility, {STYLE}"),

    ("Sara confrontou Marcos. Ele disse: é você.",
     f"{SARA} confronting {MARCOS}, he points finger dismissively at her, she shrinks smaller and looks confused and doubtful, {STYLE}"),

    ("Harvard: narcisistas culpam outros em 94%.",
     f"{ANA} holding clipboard showing Harvard logo and 94 percent statistic, {DANIELA} beside her pointing at shocking data with serious expression, {STYLE}"),

    ("Dra. Ana: seu cérebro perde a realidade.",
     f"{ANA} pointing at brain diagram showing confusion and doubt effects under manipulation, neural pathways shown in red, {SARA} watching with dawning realization, {STYLE}"),

    ("Sinal 2: seus sentimentos parecem demais.",
     f"Large glowing number TWO badge, {SARA} with large emotional speech bubble, {MARCOS} looking bored and dismissive in background with cold gap between them, {STYLE}"),

    ("Você chora? Ele suspira e sai da sala.",
     f"{SARA} crying with visible tears, {MARCOS} dramatically sighing rolling eyes and leaving, cold emotional distance between them, {STYLE}"),

    ("Quem vive isso acaba se desculpando por existir.",
     f"{SARA} with hands pressed together in apologetic gesture, her own emotions shrinking behind her, apologizing for her very existence, {STYLE}"),

    ("Julia disse a Sara: você pede desculpa por existir.",
     f"{JULIA} speaking urgently and gently to {SARA}, Sara's eyes widening in revelation, words floating between them, important truth being revealed, {STYLE}"),

    ("Isso não é amor. Isso é controle.",
     f"Mirror showing {SARA} original bright self vs faded reflection, {MARCOS} causing the fade in background, identity being erased, {STYLE}"),

    ("Sinal 3: você se culpa por coisas que não fez.",
     f"Large glowing number THREE badge, {SARA} carrying heavy guilt weight bags clearly not hers, {MARCOS} relaxed and unburdened in background, {STYLE}"),

    ("Marcos chegava tarde. Sara pedia desculpa.",
     f"{MARCOS} arriving late shrugging carelessly, {SARA} confused apologizing with hands out, clock showing very late hour in background, {STYLE}"),

    ("Se você se identificou isso é urgente pra você.",
     f"{DANIELA} with urgent warm direct expression facing viewer, glowing important badge beside her, pointing at camera with caring serious eyes, {STYLE}"),

    ("Daniela olha pra você: você não está exagerando.",
     f"{DANIELA} making sincere direct eye contact with viewer, hand on heart, warm golden light surrounding her, most intimate moment of the video, {STYLE}"),

    ("Seus sentimentos são válidos. Sua dor é real.",
     f"{SARA} standing stronger and taller, {JULIA} and {DANIELA} on each side with arms around her shoulders, empowering unity scene, {STYLE}"),

    ("No próximo vídeo Sara descobre tudo sobre Marcos.",
     f"{MARCOS} hiding dark secret behind his back in shadow, {SARA} about to turn and discover the shocking truth, dramatic cliffhanger tension, {STYLE}"),

    ("Inscreva-se agora pra não perder. 🔔",
     f"Giant golden glowing notification bell with sparkles and stars, {DANIELA} {SARA} {JULIA} {ANA} all raising arms celebrating together, colorful confetti, {STYLE}"),
]

FRASES  = [s[0] for s in SCENES]
PROMPTS = [s[1] for s in SCENES]
N       = len(SCENES)
# TTS usa ". " sem newlines (evita pausas longas)
SCRIPT_TTS = ". ".join(FRASES)
# Para cálculo de RATE_REAL: usa chars reais por frase
CHARS_FRASES = [len(f) for f in FRASES]

total_chars = sum(CHARS_FRASES)
log(f"{'='*55}")
log(f"  ψ SHORT 58s FINAL — {N} FRASES / {N} IMAGENS")
log(f"  {total_chars} chars | rate +8% → 58s")
log(f"  1 imagem por frase | ~2.9s por imagem")
log(f"{'='*55}\n")

# ── FUNÇÕES UTILITÁRIAS ──────────────────────────────────
def measure_dur(path):
    p = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",path],
        capture_output=True, text=True)
    return float(json.loads(p.stdout)["format"]["duration"])

def add_overlay(img_path, caption):
    img  = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0,H-100,W,H], fill=DARK)
    draw.rectangle([0,H-100,6,H], fill=VERM)
    draw.rectangle([0,H-4,W,H], fill=VERM)
    draw.text((22,H-90), "ψ", fill=GOLD)
    draw.text((62,H-88), "Daniela Coelho", fill=BRAN)
    draw.text((62,H-58), "Saúde Mental  |  @psidanielacoelho", fill=LILAS)
    if caption and len(caption) > 2:
        cap = caption[:32].upper()
        bw  = min(len(cap)*14+50, W-60); cx = W//2
        draw.rounded_rectangle([cx-bw//2,38,cx+bw//2,82],
            radius=16, fill=(250,248,255), outline=(210,200,235), width=2)
        draw.text((cx-bw//2+24,50), cap, fill=(20,15,45))
    img.save(img_path, "JPEG", quality=97)

def gen_pillow(idx):
    img  = Image.new("RGB",(W,H),(245,240,232))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t=y/H; draw.line([(0,y),(W,y)],fill=(int(245+(230-245)*t),int(240+(225-240)*t),int(232+(215-232)*t)))
    cols=[(150,80,210),(200,100,60),(60,120,200),(200,60,100),(60,180,100)]
    for ci, cx in enumerate([W//3, 2*W//3]):
        c=cols[(idx+ci)%len(cols)]; cy=H//2-80
        draw.ellipse([cx-92,cy-205,cx+92,cy+35],fill=(255,220,185))
        draw.ellipse([cx-96,cy-255,cx+96,cy-90],fill=(40,28,12))
        draw.rounded_rectangle([cx-78,cy+30,cx+78,cy+250],radius=22,fill=c)
        for ex in [cx-38, cx+14]:
            draw.ellipse([ex,cy-95,ex+36,cy-68],fill=(255,255,255))
            draw.ellipse([ex+5,cy-90,ex+30,cy-73],fill=(25,18,50))
        draw.arc([cx-28,cy-20,cx+28,cy+15],start=0,end=180,fill=(180,60,60),width=4)
    out=f"{WORKDIR}/ai_{idx:02d}.jpg"; img.save(out,"JPEG",quality=90)
    return out

# ── ETAPA 1: ÁUDIO TTS ──────────────────────────────────
log("🎙️  ETAPA 1 — Gerando áudio (AntonioNeural +8% = 58s)...")

# RATE FIXO +8% → leve aceleração, soa natural, dá ~58s
RATE_ADJ = "+8%"

async def gen_audio():
    import edge_tts
    path = f"{WORKDIR}/audio_final.mp3"
    c = edge_tts.Communicate(SCRIPT_TTS, voice="pt-BR-AntonioNeural", rate=RATE_ADJ)
    await c.save(path)
    return path

asyncio.run(gen_audio())
AUDIO_PATH = f"{WORKDIR}/audio_final.mp3"
DUR_FINAL  = measure_dur(AUDIO_PATH)
RATE_REAL  = total_chars / DUR_FINAL

log(f"  ✅ Áudio: {DUR_FINAL:.2f}s @ rate={RATE_ADJ}")
if abs(DUR_FINAL - TARGET) <= 2:
    log(f"  🎯 PERFEITO! {DUR_FINAL:.2f}s ≈ {TARGET}s")
else:
    log(f"  ⚠️  {DUR_FINAL:.2f}s (diff: {DUR_FINAL-TARGET:+.1f}s)")

# ── ETAPA 2: DURAÇÕES POR FRASE ─────────────────────────
DURS = [max(0.4, round(c/RATE_REAL, 3)) for c in CHARS_FRASES]
log(f"\n  MAPA FRASE → IMAGEM → DURAÇÃO ({DUR_FINAL:.1f}s total):")
for i, (f, d) in enumerate(zip(FRASES, DURS), 1):
    log(f"  [{i:02d}] {d:.1f}s → {f}")

# ── ETAPA 3: 20 IMAGENS SEQUENCIAIS POLLINATIONS ────────
log(f"\n🎨 ETAPA 3 — Gerando {N} imagens (Pollinations FLUX)...")
IMGS = [None]*N; counts={"poll":0,"pillow":0}; t0=time.time()

for idx, (frase, prompt) in enumerate(zip(FRASES, PROMPTS)):
    full = (f"masterpiece, best quality, kawaii chibi anime illustration, "
            f"{prompt} ### lowres, bad anatomy, text, watermark, nsfw, blurry")
    enc  = urllib.parse.quote(full)
    seed = 9001 + idx * 77
    out  = f"{WORKDIR}/ai_{idx:02d}.jpg"
    ok   = False

    for attempt in range(4):
        try:
            url = (f"https://image.pollinations.ai/prompt/{enc}"
                   f"?width=576&height=1024&seed={seed+attempt}"
                   f"&nologo=true&model=flux&enhance=true")
            r = requests.get(url, timeout=90)
            if r.status_code == 402:
                log(f"  [{idx+1}] Rate limit, aguardando 30s...")
                time.sleep(30); continue
            if r.status_code == 200 and 'image' in r.headers.get('content-type',''):
                if len(r.content) > 40000:
                    with open(f"{WORKDIR}/raw_{idx:02d}.jpg",'wb') as f: f.write(r.content)
                    img = Image.open(f"{WORKDIR}/raw_{idx:02d}.jpg").convert("RGB")
                    img = img.resize((W,H), Image.LANCZOS)
                    img.save(out,"JPEG",quality=96)
                    cap = frase[:30].split('.')[0].split(',')[0].split('?')[0].strip()
                    add_overlay(out, cap)
                    elapsed = time.time()-t0
                    sz = os.path.getsize(out)//1024
                    log(f"  [{idx+1:02d}/{N}] 🌐 {sz}KB | {elapsed:.0f}s | {frase}")
                    IMGS[idx]=out; counts["poll"]+=1; ok=True; break
        except Exception as e:
            log(f"  [{idx+1}] tentativa {attempt+1}: {str(e)[:40]}")
        if attempt < 3: time.sleep(8)

    if not ok:
        out = gen_pillow(idx)
        cap = frase[:30].split('.')[0].strip()
        add_overlay(out, cap)
        IMGS[idx]=out; counts["pillow"]+=1
        log(f"  [{idx+1:02d}/{N}] ✏️  pillow | {frase}")

    if idx < N-1: time.sleep(4)

gen_t = time.time()-t0
log(f"\n  ✅ {counts['poll']}/{N} Pollinations | {counts['pillow']} Pillow | {gen_t/60:.1f}min")

# ── ETAPA 4: FFCONCAT ────────────────────────────────────
concat = f"{WORKDIR}/concat.txt"
with open(concat,'w') as f:
    for i, dur in enumerate(DURS):
        img = IMGS[min(i,N-1)]
        if img: f.write(f"file '{img}'\nduration {dur:.3f}\n")
    if IMGS[-1]: f.write(f"file '{IMGS[-1]}'\n")

# ── ETAPA 5: RENDER ─────────────────────────────────────
ts  = int(time.time())
OUT = f"{WORKDIR}/v683_58final_{ts}.mp4"
log(f"\n🎬 ETAPA 5 — Renderizando {DUR_FINAL:.1f}s short...")
cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",concat,
       "-i",AUDIO_PATH,
       "-c:v","libx264","-pix_fmt","yuv420p","-crf",str(CRF),
       "-c:a","aac","-b:a","128k","-shortest",
       "-r",str(FPS),
       "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
             "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
       "-movflags","+faststart", OUT]
res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
if res.returncode != 0:
    log(f"ERRO:\n{res.stderr[-500:]}"); sys.exit(1)

sz   = os.path.getsize(OUT)
dur2 = float(json.loads(subprocess.run(
    ["ffprobe","-v","quiet","-print_format","json","-show_format",OUT],
    capture_output=True,text=True).stdout)["format"]["duration"])

log(f"  ✅ {sz/1024/1024:.2f}MB | {dur2:.2f}s")
ok_58 = abs(dur2 - TARGET) <= 2
log(f"  {'🎯 PERFEITO!' if ok_58 else '⚠️  Revisar'} {dur2:.2f}s (target: {TARGET}s)")

# ── ETAPA 6: UPLOAD ─────────────────────────────────────
log(f"\n☁️  ETAPA 6 — Upload Supabase...")
with open(OUT,'rb') as f: vdata=f.read()
video_url = None
for att in range(5):
    try:
        video_url = sb_upload(f"mp4s/v683_58final_{ts}.mp4", vdata, "video/mp4")
        log(f"  ✅ {video_url}"); break
    except Exception as e:
        log(f"  Tentativa {att+1}: {e}"); time.sleep(15)

if video_url:
    sb_patch(VIDEO_ID, {
        "video_url": video_url, "status": "pending_credentials",
        "metadata": json.dumps({
            "version":"short_58s_v3_final",
            "dur_s": round(dur2,2), "target_s": TARGET,
            "frases": N, "poll": counts["poll"], "pillow": counts["pillow"],
            "file_mb": round(sz/1024/1024,2), "rate_adj": RATE_ADJ,
            "img_per_phrase": True, "rate_real": round(RATE_REAL,3),
        })
    })

log(f"\n{'='*55}")
log(f"  ψ SHORT 58s — RESULTADO")
log(f"  ⏱️  {dur2:.2f}s | target: {TARGET}s")
log(f"  🌐 {counts['poll']}/{N} Pollinations FLUX")
log(f"  📸 {N} imagens únicas, 1 por frase")
log(f"  💾 {sz/1024/1024:.2f}MB")
log(f"  🎬 {video_url or 'UPLOAD FALHOU'}")
log(f"{'='*55}\n")
