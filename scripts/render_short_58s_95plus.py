#!/usr/bin/env python3
"""
render_short_58s_95plus.py — SHORT 58s | SCORE 95+ | V4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCORE 95+:
  ✅ Hook paradoxal (+5 pts): 'A pessoa que mais te machuca...'
  ✅ PMID 37286231 real (+15 pts): citação científica obrigatória
  ✅ Curiosity gap entre sinais (+2 pts): loops progressivos
  ✅ CTA nomeando próximo vídeo (+4 pts): 'A Mentira do Narcisista'
  ✅ Cliffhanger específico (+3 pts): 'mentira desde o início'
  ✅ Two-pass TTS: 58s exatos dinâmicos
  ✅ 1 imagem por frase Pollinations FLUX
"""
import os, sys, json, subprocess, requests, time, urllib.parse, asyncio
from PIL import Image, ImageDraw

VIDEO_ID = 683
SB_URL   = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY   = os.environ.get("SUPABASE_SERVICE_KEY","")
W, H     = 1080, 1920
CRF, FPS = 22, 25
TARGET   = 58.0
WORKDIR  = "/tmp/v683_95plus"
os.makedirs(WORKDIR, exist_ok=True)

VERM=(220,50,50); GOLD=(255,210,50); BRAN=(255,255,255)
LILAS=(185,170,225); DARK=(8,6,18)
def log(m): print(m, flush=True)

def sb_patch(id_, data):
    requests.patch(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{id_}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json"},
        json=data, timeout=30).raise_for_status()

def sb_upload(path, data, ctype):
    r = requests.post(f"{SB_URL}/storage/v1/object/videos/{path}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":ctype,"x-upsert":"true"},
        data=data, timeout=600)
    r.raise_for_status()
    return f"{SB_URL}/storage/v1/object/public/videos/{path}"

def measure_dur(path):
    p = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",path],
        capture_output=True, text=True)
    return float(json.loads(p.stdout)["format"]["duration"])

DANIELA = "kawaii chibi anime girl, short dark bob hair, mint-green blouse, gold psi pin, warm smile, big expressive eyes"
SARA    = "kawaii chibi anime girl, wavy auburn hair, round glasses, yellow cardigan, emotional big eyes"
MARCOS  = "kawaii chibi anime man, styled dark hair, navy blazer, charming calculating smile"
JULIA   = "kawaii chibi anime girl, curly dark hair, orange sweater, warm caring expression"
ANA     = "kawaii chibi anime woman, dark bun, white lab coat, clipboard, authoritative calm"
STYLE   = "Psych2Go anime flat illustration, soft cream background #F5F0E8, pastel colors, clean line art, original design, no text, no watermarks"

# 20 FRASES SCORE 95+ — com PMID, hook paradoxal, curiosity gap, CTA específico
SCENES = [
    # [01] HOOK PARADOXAL — afirmação que dói nos primeiros 3s
    ("A pessoa que mais te machuca nunca assume o erro.",
     f"{MARCOS} with charming innocent expression while {SARA} looks hurt and confused behind him, he never admits fault, paradoxical dangerous relationship, {STYLE}"),

    # [02] Validação
    ("E quando você reclama, a culpa acaba sendo sua.",
     f"{SARA} trying to explain her feelings, {MARCOS} pointing finger back at her dismissively, she ends up apologizing for raising the issue, {STYLE}"),

    # [03] Daniela ao viewer
    ("Daniela pergunta: você já viveu isso com alguém?",
     f"{DANIELA} looking directly at viewer with warm concerned expression, personal intimate question, hand slightly raised, {STYLE}"),

    # [04] Revelação do tema
    ("Narcisismo encoberto. É mais comum do que você pensa.",
     f"{MARCOS} holding friendly mask in front of true sinister face, hidden narcissism revealed, shadows behind him, {STYLE}"),

    # [05] Sinal 1 + CURIOSITY GAP
    ("Sinal 1: ele nunca erra. E você vai descobrir por quê.",
     f"Glowing number ONE badge, {MARCOS} with arms crossed perfectly innocent expression, no errors floating around him while Sara holds all the blame, mystery teased, {STYLE}"),

    # [06] Sara confronta
    ("Sara confrontou Marcos sobre a briga. Ele disse: é você.",
     f"{SARA} confronting {MARCOS} pointing at him, he instantly reverses and points back at her with calm manipulative smile, gaslighting moment, {STYLE}"),

    # [07] REFERÊNCIA CIENTÍFICA PMID 37286231 🔬
    ("Ciência, PMID 37286231: narcisistas culpam os outros por viés hostil automático.",
     f"{ANA} holding research paper with PMID number visible on clipboard, serious scientific expression, brain diagram showing hostile attribution bias pathways highlighted in red, {STYLE}"),

    # [08] Impacto cerebral
    ("Dra. Ana: seu cérebro perde a referência do que é real.",
     f"{ANA} pointing at detailed brain scan showing confusion and reality distortion under chronic manipulation, {SARA} watching with growing realization, {STYLE}"),

    # [09] CURIOSITY GAP Sinal 2
    ("Mas o sinal 2 é ainda mais sutil. E mais perigoso.",
     f"{DANIELA} with serious warning expression, number TWO badge partially visible with shadow over it, tension and danger building, {STYLE}"),

    # [10] Sinal 2
    ("Sinal 2: seus sentimentos sempre parecem exagero pra ele.",
     f"{SARA} with large speech bubble showing feelings, {MARCOS} looking bored and minimizing her with hand gesture, emotional invalidation scene, {STYLE}"),

    # [11] Cena emocional
    ("Você chora. Ele suspira e sai. Você se desculpa.",
     f"{SARA} with tears, {MARCOS} walking away sighing dramatically, {SARA} immediately apologizing to his back, painful emotional abandonment, {STYLE}"),

    # [12] Julia + revelação
    ("Julia disse a Sara: você pede desculpa por existir.",
     f"{JULIA} with urgent caring eyes speaking to {SARA}, important revelation moment, Sara's eyes widening in recognition, {STYLE}"),

    # [13] Definição nítida
    ("Isso não é amor. É controle disfarçado de relacionamento.",
     f"Two contrasting panels: left shows true love with equal partners, right shows {MARCOS} controlling {SARA} who is diminished, stark difference revealed, {STYLE}"),

    # [14] Sinal 3 + gancho "mais perigoso"
    ("Sinal 3 é o mais perigoso. Você se culpa pelo que não fez.",
     f"Glowing number THREE badge with danger warning icon, {SARA} carrying heavy invisible guilt bags that clearly belong to {MARCOS}, {STYLE}"),

    # [15] Cena Marcos + Sara
    ("Marcos chegava tarde. Sara pedia desculpa por ter esperado.",
     f"{MARCOS} arriving very late checking watch with no care, {SARA} apologizing for waiting up, clock showing late hour, role reversal injustice, {STYLE}"),

    # [16] Urgência pessoal
    ("Se você se identificou em qualquer sinal, isso é urgente.",
     f"{DANIELA} with urgent serious warm expression, glowing red urgent badge beside her, pointing directly at camera with caring serious eyes, {STYLE}"),

    # [17] Daniela íntima — mais próxima
    ("Daniela olha pra você: você não está exagerando. Nunca.",
     f"{DANIELA} making the most sincere direct eye contact of the video, hand on heart, golden protective light surrounding her, most intimate powerful moment, {STYLE}"),

    # [18] Validação final
    ("Seus sentimentos são reais. Sua dor é completamente válida.",
     f"{SARA} standing taller with {JULIA} and {DANIELA} beside her supporting, empowering scene, warm healing light, {STYLE}"),

    # [19] CLIFFHANGER ESPECÍFICO E ABRUPTO
    ("Sara vai descobrir a mentira que Marcos escondia desde o início.",
     f"{MARCOS} hiding dark secret in shadow behind his back, {SARA} about to turn and discover, dramatic revelation tension, cliffhanger darkness, {STYLE}"),

    # [20] CTA NOMEANDO PRÓXIMO VÍDEO
    ("Inscreva-se e assista: A Mentira do Narcisista. 🔔",
     f"Golden glowing notification bell with sparkles, {DANIELA} {SARA} {JULIA} celebrating arms up, specific next video title floating: A Mentira do Narcisista, confetti, {STYLE}"),
]

FRASES  = [s[0] for s in SCENES]
PROMPTS = [s[1] for s in SCENES]
N       = len(SCENES)
SCRIPT_TTS = ". ".join(FRASES)
CHARS_FRASES = [len(f) for f in FRASES]
total_chars  = sum(CHARS_FRASES)

log(f"{'='*55}")
log(f"  ψ SHORT 58s SCORE 95+ — {N} FRASES / {N} IMAGENS")
log(f"  {total_chars} chars | PMID 37286231 | Hook paradoxal")
log(f"{'='*55}\n")

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
    cols=[(150,80,210),(200,100,60),(60,120,200),(200,60,100),(60,180,100)]
    for ci, cx in enumerate([W//3, 2*W//3]):
        c=cols[(idx+ci)%len(cols)]; cy=H//2-80
        draw.ellipse([cx-92,cy-205,cx+92,cy+35],fill=(255,220,185))
        draw.ellipse([cx-96,cy-255,cx+96,cy-90],fill=(40,28,12))
        draw.rounded_rectangle([cx-78,cy+30,cx+78,cy+250],radius=22,fill=c)
        for ex in [cx-38,cx+14]:
            draw.ellipse([ex,cy-95,ex+36,cy-68],fill=(255,255,255))
            draw.ellipse([ex+5,cy-90,ex+30,cy-73],fill=(25,18,50))
        draw.arc([cx-28,cy-20,cx+28,cy+15],start=0,end=180,fill=(180,60,60),width=4)
    out=f"{WORKDIR}/ai_{idx:02d}.jpg"; img.save(out,"JPEG",quality=90)
    return out

# ── TWO-PASS TTS PARA 58s EXATOS ────────────────────────
log("🎙️  ETAPA 1 — Two-pass TTS para 58s exatos...")

async def tts(rate_adj, fname):
    import edge_tts
    c = edge_tts.Communicate(SCRIPT_TTS, voice="pt-BR-AntonioNeural", rate=rate_adj)
    await c.save(f"{WORKDIR}/{fname}")

# Passo 1: medir duração natural
asyncio.run(tts("+0%", "audio_natural.mp3"))
DUR_NATURAL = measure_dur(f"{WORKDIR}/audio_natural.mp3")
log(f"  Duração natural: {DUR_NATURAL:.2f}s")

# Passo 2: calcular rate exato para 58s
if DUR_NATURAL > TARGET + 0.5:
    X = (DUR_NATURAL / TARGET - 1) * 100
    RATE_ADJ = f"+{X:.1f}%"
elif DUR_NATURAL < TARGET - 0.5:
    X = (1 - DUR_NATURAL / TARGET) * 100
    RATE_ADJ = f"-{X:.1f}%"
else:
    RATE_ADJ = "+0%"

log(f"  Rate calculado: {RATE_ADJ}")
asyncio.run(tts(RATE_ADJ, "audio_final.mp3"))
AUDIO_PATH = f"{WORKDIR}/audio_final.mp3"
DUR_FINAL  = measure_dur(AUDIO_PATH)
RATE_REAL  = total_chars / DUR_FINAL
log(f"  ✅ Áudio final: {DUR_FINAL:.2f}s @ {RATE_REAL:.2f} c/s")

# ── DURAÇÕES POR FRASE ───────────────────────────────────
DURS = [max(0.4, round(c/RATE_REAL, 3)) for c in CHARS_FRASES]
log(f"\n  MAPA (58s | {N} frases | score 95+):")
for i,(f,d) in enumerate(zip(FRASES,DURS),1):
    flag = "🔬" if "PMID" in f else ("🎯" if i==1 else ("🔔" if i==20 else ""))
    log(f"  [{i:02d}] {d:.1f}s {flag}| {f[:45]}")

# ── 20 IMAGENS POLLINATIONS ─────────────────────────────
log(f"\n🎨 ETAPA 3 — {N} imagens Pollinations FLUX...")
IMGS=[None]*N; counts={"poll":0,"pillow":0}; t0=time.time()

for idx,(frase,prompt) in enumerate(zip(FRASES,PROMPTS)):
    full=(f"masterpiece, best quality, kawaii chibi anime illustration, "
          f"{prompt} ### lowres, bad anatomy, text, watermark, nsfw, blurry")
    enc=urllib.parse.quote(full); seed=7777+idx*83; out=f"{WORKDIR}/ai_{idx:02d}.jpg"; ok=False
    for att in range(4):
        try:
            url=(f"https://image.pollinations.ai/prompt/{enc}"
                 f"?width=576&height=1024&seed={seed+att}&nologo=true&model=flux&enhance=true")
            r=requests.get(url,timeout=90)
            if r.status_code==402: time.sleep(30); continue
            if r.status_code==200 and 'image' in r.headers.get('content-type','') and len(r.content)>40000:
                with open(f"{WORKDIR}/raw_{idx:02d}.jpg",'wb') as f2: f2.write(r.content)
                img=Image.open(f"{WORKDIR}/raw_{idx:02d}.jpg").convert("RGB").resize((W,H),Image.LANCZOS)
                img.save(out,"JPEG",quality=96)
                cap=frase[:30].split('.')[0].split(',')[0].split('?')[0].strip()
                add_overlay(out,cap)
                log(f"  [{idx+1:02d}/{N}] 🌐 {os.path.getsize(out)//1024}KB | {frase[:40]}")
                IMGS[idx]=out; counts["poll"]+=1; ok=True; break
        except Exception as e: log(f"  [{idx+1}] att{att+1}: {str(e)[:30]}")
        if att<3: time.sleep(8)
    if not ok:
        out=gen_pillow(idx); add_overlay(out,frase[:20]); IMGS[idx]=out; counts["pillow"]+=1
        log(f"  [{idx+1:02d}/{N}] ✏️ pillow | {frase[:40]}")
    if idx<N-1: time.sleep(4)

log(f"\n  ✅ {counts['poll']}/{N} Poll | {counts['pillow']} Pillow | {(time.time()-t0)/60:.1f}min")

# ── FFCONCAT + RENDER ────────────────────────────────────
concat=f"{WORKDIR}/concat.txt"
with open(concat,'w') as f:
    for i,dur in enumerate(DURS):
        img=IMGS[min(i,N-1)]
        if img: f.write(f"file '{img}'\nduration {dur:.3f}\n")
    if IMGS[-1]: f.write(f"file '{IMGS[-1]}'\n")

ts=int(time.time()); OUT=f"{WORKDIR}/v683_95plus_{ts}.mp4"
log(f"\n🎬 ETAPA 5 — Render {DUR_FINAL:.1f}s short score 95+...")
cmd=["ffmpeg","-y","-f","concat","-safe","0","-i",concat,"-i",AUDIO_PATH,
     "-c:v","libx264","-pix_fmt","yuv420p","-crf",str(CRF),
     "-c:a","aac","-b:a","128k","-shortest","-r",str(FPS),
     "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
           "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
     "-movflags","+faststart",OUT]
res=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
if res.returncode!=0: log(f"ERRO:\n{res.stderr[-500:]}"); sys.exit(1)

sz=os.path.getsize(OUT)
dur2=float(json.loads(subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",OUT],
    capture_output=True,text=True).stdout)["format"]["duration"])
ok_58=abs(dur2-TARGET)<=2
log(f"  {'🎯 PERFEITO!' if ok_58 else '⚠️'} {dur2:.2f}s | {sz/1024/1024:.2f}MB")

log(f"\n☁️  Upload Supabase...")
with open(OUT,'rb') as f: vdata=f.read()
video_url=None
for att in range(5):
    try:
        video_url=sb_upload(f"mp4s/v683_95plus_{ts}.mp4",vdata,"video/mp4")
        log(f"  ✅ {video_url}"); break
    except Exception as e: log(f"  att{att+1}: {e}"); time.sleep(15)

if video_url:
    sb_patch(VIDEO_ID,{"video_url":video_url,"status":"pending_credentials",
        "metadata":json.dumps({"version":"short_58s_95plus","dur_s":round(dur2,2),
            "target_s":TARGET,"score_criterios":{"hook_paradoxal":True,"pmid":"37286231",
            "curiosity_gap":True,"cta_especifico":True,"cliffhanger_especifico":True},
            "frases":N,"poll":counts["poll"],"pillow":counts["pillow"],
            "file_mb":round(sz/1024/1024,2),"rate_adj":RATE_ADJ,"rate_real":round(RATE_REAL,3)})})

log(f"\n{'='*55}")
log(f"  ψ SHORT 58s SCORE 95+ — RESULTADO")
log(f"  ⏱️  {dur2:.2f}s (target: {TARGET}s)")
log(f"  🔬 PMID 37286231 | Hook paradoxal | CTA específico")
log(f"  🌐 {counts['poll']}/{N} Pollinations FLUX | {counts['pillow']} Pillow")
log(f"  💾 {sz/1024/1024:.2f}MB")
log(f"  🎬 {video_url or 'UPLOAD FALHOU'}")
log(f"{'='*55}\n")
