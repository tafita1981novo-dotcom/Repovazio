#!/usr/bin/env python3
"""
render_683_poll_seq.py — POLLINATIONS SEQUENCIAL (GRÁTIS + ILIMITADO)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pollinations.ai = grátis, sem chave, ilimitado.
O erro anterior: 33 requests PARALELOS → rate limit → falha.
Solução: SEQUENCIAL + delay 4s + 3 retries por imagem.
33 imagens × ~12s = ~6 min → dentro do timeout de 90min.

Resultado esperado: 33/33 Pollinations FLUX
Tamanho esperado: 5-9MB (supera V8 Final 6.27MB)
"""
import os, sys, json, subprocess, requests, time, urllib.parse
from PIL import Image, ImageDraw
import traceback

VIDEO_ID = 683
SB_URL   = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY   = os.environ.get("SUPABASE_SERVICE_KEY","")
W, H     = 1080, 1920
CRF      = 22
WORKDIR  = "/tmp/v683_poll"
os.makedirs(WORKDIR, exist_ok=True)

VERM=(220,50,50); GOLD=(255,210,50); BRAN=(255,255,255); LILAS=(185,170,225)
def log(m): print(m, flush=True)

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

# Carregar dados
row = requests.get(
    f"{SB_URL}/rest/v1/content_pipeline?id=eq.{VIDEO_ID}&select=id,title,script",
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"},timeout=30
).json()[0]
SCRIPT = row["script"].strip()
PARAS  = [p.strip() for p in SCRIPT.split('\n\n') if p.strip()]
N      = len(PARAS)

log(f"{'='*55}")
log(f"  ψ POLLINATIONS SEQUENCIAL — GRÁTIS + ILIMITADO")
log(f"  {len(SCRIPT)} chars | {N} cenas | CRF={CRF}")
log(f"  Strategy: 1 por vez + 4s delay + 3 retries")
log(f"{'='*55}\n")

# Personagens do universo
STYLE = (
    "Psych2Go kawaii chibi anime art style, original character design, "
    "soft cream background color F5F0E8, pastel warm colors, "
    "expressive big chibi eyes, clean flat illustration, "
    "professional animation quality, no text, no watermark, no logos"
)
DANIELA = "chibi anime girl with dark bob hair and mint green blouse and gold psi pin, warm smile"
SARA    = "chibi anime girl with wavy auburn hair and round glasses and yellow cardigan"
MARCOS  = "chibi anime man with styled dark hair and navy blazer, charming calculating smile"
JULIA   = "chibi anime girl with curly dark hair and orange sweater, caring warm expression"
ANA     = "chibi anime woman with dark bun and white lab coat and clipboard"

SCENES = [
    f"{SARA} alone at night holding phone anxiously with message bubbles and blue glow, {STYLE}",
    f"{SARA} reading disappointing message on phone with sad drooping eyes, {STYLE}",
    f"{SARA} meeting {MARCOS} at party with sparkles around him, she looks hopeful but uneasy, {STYLE}",
    f"{SARA} with question marks floating around her head sensing something wrong, {STYLE}",
    f"{DANIELA} looking warmly and directly at viewer with hand extended in welcome, {STYLE}",
    f"{SARA} hunched with blame arrows pointing at her and {MARCOS} turned away, {STYLE}",
    f"{MARCOS} waving hand dismissively at {SARA} speech bubble minimizing her feelings, {STYLE}",
    f"{ANA} holding clipboard with research data and {DANIELA} pointing at statistic, {STYLE}",
    f"{MARCOS} holding friendly mask hiding sinister shadow behind him, {STYLE}",
    f"large badge number one and {MARCOS} shrugging with innocent expression no responsibility, {STYLE}",
    f"{SARA} touching temple with memory bubble above showing past argument confused, {STYLE}",
    f"{MARCOS} pointing accusingly at shrinking smaller {SARA} gaslighting, {STYLE}",
    f"{ANA} pointing at brain diagram showing manipulation effects and {SARA} realizing, {STYLE}",
    f"{DANIELA} holding golden shield glowing with protective warm light around {SARA}, {STYLE}",
    f"large badge number two and {SARA} emotional speech bubble and {MARCOS} looking bored, {STYLE}",
    f"{SARA} crying with tears and {MARCOS} dramatically sighing with cold emotional gap, {STYLE}",
    f"{MARCOS} with floating negative labels around {SARA} saying anxious dramatic difficult, {STYLE}",
    f"{SARA} with hands pressed together apologizing for her own feelings sad and small, {STYLE}",
    f"{JULIA} looking worried watching {SARA} with protective hand near friend, {STYLE}",
    f"{JULIA} and {SARA} face to face with Julia speaking urgent truth revelation moment, {STYLE}",
    f"mirror showing {SARA} original reflection fading and identity being erased slowly, {STYLE}",
    f"large badge number three and {SARA} carrying heavy guilt weights and {MARCOS} relaxed, {STYLE}",
    f"{MARCOS} arriving late shrugging and {SARA} confused apologizing with clock showing late, {STYLE}",
    f"{SARA} with worried hands to face gesture with question mark floating toward her lost, {STYLE}",
    f"{DANIELA} with urgent warm expression facing viewer directly with glowing badge, {STYLE}",
    f"{ANA} showing iceberg with tiny visible narcissism tip and massive hidden danger below, {STYLE}",
    f"{ANA} showing cycle diagram love bomb devalue discard and {SARA} recognizing pattern, {STYLE}",
    f"{DANIELA} opening bright doorway to light and {SARA} stepping toward hope, {STYLE}",
    f"{DANIELA} making sincere eye contact with viewer with hand on heart and golden warm light, {STYLE}",
    f"{SARA} and {JULIA} and {DANIELA} together with arms around shoulders strength in unity, {STYLE}",
    f"{MARCOS} hiding something in shadow behind back and {SARA} about to discover truth, {STYLE}",
    f"{SARA} with lightbulb moment and eyes wide with revelation and everything clicking, {STYLE}",
    f"giant golden notification bell with sparkles and all characters celebrating confetti, {STYLE}",
]

# Captions
CAPTIONS = []
for p in PARAS:
    cap = p[:28].split('.')[0].split(',')[0].split('?')[0].strip()
    CAPTIONS.append(cap[:28])
if CAPTIONS: CAPTIONS[-1] = "INSCREVA-SE AGORA 🔔"

def add_overlay(img_path, caption):
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    DARK = (8,6,18)
    draw.rectangle([0,H-100,W,H], fill=DARK)
    draw.rectangle([0,H-100,6,H], fill=VERM)
    draw.rectangle([0,H-4,W,H], fill=VERM)
    draw.text((22,H-90), "ψ", fill=GOLD)
    draw.text((62,H-88), "Daniela Coelho", fill=BRAN)
    draw.text((62,H-58), "Saúde Mental  |  @psidanielacoelho", fill=LILAS)
    if caption and len(caption) > 2:
        cap = caption[:30].upper()
        bw  = min(len(cap)*15+60, W-80); cx = W//2
        draw.rounded_rectangle([cx-bw//2,38,cx+bw//2,82], radius=18,
            fill=(250,248,255), outline=(210,200,235), width=2)
        draw.text((cx-bw//2+28,50), cap, fill=(20,15,45))
    img.save(img_path, "JPEG", quality=97)
    return img_path

def gen_pillow(idx):
    img = Image.new("RGB",(W,H),(245,240,232))
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

# ── GERAÇÃO SEQUENCIAL ─────────────────────────────────────────
log(f"🎨 Gerando {N} cenas SEQUENCIALMENTE (Pollinations grátis/ilimitado)...")
log(f"   ~{N*12//60}min estimado — pace: 1 cena/12s\n")

IMGS = [None]*N
counts = {"poll":0, "pillow":0}
t0 = time.time()

for idx, (scene, caption) in enumerate(zip(SCENES, CAPTIONS)):
    # Construir prompt otimizado para chibi anime
    prompt = (
        f"masterpiece best quality kawaii chibi anime style illustration, "
        f"{scene}, "
        f"Psych2Go style, pastel colors, cream background, expressive big eyes, "
        f"clean line art, no text no watermark"
    )
    enc = urllib.parse.quote(prompt)
    seed = 1337 + idx * 42

    success = False
    for attempt in range(4):  # 4 tentativas por cena
        try:
            # Modelo flux com enhance=true para máxima qualidade
            url = (f"https://image.pollinations.ai/prompt/{enc}"
                   f"?width=576&height=1024&seed={seed+attempt}"
                   f"&nologo=true&model=flux&enhance=true"
                   f"&negative=text,watermark,low%20quality,blurry")
            
            r = requests.get(url, timeout=90)
            
            if r.status_code == 402:
                log(f"  [{idx+1:02d}] Rate limit, aguardando 30s...")
                time.sleep(30)
                continue
            
            if r.status_code == 200:
                ct = r.headers.get("content-type","")
                if "image" in ct and len(r.content) > 40000:
                    tmp = f"{WORKDIR}/raw_{idx:02d}.jpg"
                    with open(tmp,'wb') as f: f.write(r.content)
                    # Redimensionar para 1080×1920
                    img = Image.open(tmp).convert("RGB").resize((W,H),Image.LANCZOS)
                    out = f"{WORKDIR}/ai_{idx:02d}.jpg"
                    img.save(out,"JPEG",quality=96)
                    add_overlay(out, caption)
                    sz = os.path.getsize(out)//1024
                    elapsed = time.time()-t0
                    log(f"  [{idx+1:02d}/{N}] 🌐 pollinations ({sz}KB) | {elapsed:.0f}s total")
                    IMGS[idx] = out
                    counts["poll"] += 1
                    success = True
                    break
            else:
                log(f"  [{idx+1:02d}] HTTP {r.status_code} (tentativa {attempt+1})")
        except Exception as e:
            log(f"  [{idx+1:02d}] Erro tentativa {attempt+1}: {str(e)[:50]}")
        
        if attempt < 3:
            time.sleep(8)  # delay entre tentativas
    
    if not success:
        # Pillow como último recurso
        out = gen_pillow(idx)
        add_overlay(out, caption)
        sz = os.path.getsize(out)//1024
        log(f"  [{idx+1:02d}/{N}] ✏️  pillow ({sz}KB)")
        IMGS[idx] = out
        counts["pillow"] += 1
    
    # Delay entre cenas (evita rate limit)
    if idx < N-1:
        time.sleep(4)

gen_t = time.time()-t0
log(f"\n  ✅ {counts['poll']}/{N} Pollinations | {counts['pillow']} Pillow | {gen_t:.0f}s ({gen_t/60:.1f}min)")

# ── ÁUDIO ─────────────────────────────────────────────────────
log(f"\n🎙️  Baixando áudio V8 Final...")
r = requests.get(
    "https://tpjvalzwkqwttvmszvie.supabase.co"
    "/storage/v1/object/public/videos/audios/v683_v8_1778892031.mp3",
    timeout=60)
with open(f"{WORKDIR}/audio.mp3",'wb') as f: f.write(r.content)
probe = subprocess.run(
    ["ffprobe","-v","quiet","-print_format","json","-show_format",f"{WORKDIR}/audio.mp3"],
    capture_output=True,text=True)
DUR  = float(json.loads(probe.stdout)["format"]["duration"])
RATE = len(SCRIPT)/DUR
DURS = [max(0.5, round(len(p)/RATE,3)) for p in PARAS]
log(f"  {DUR:.1f}s | RATE={RATE:.3f}")

# ── FFCONCAT ──────────────────────────────────────────────────
concat = f"{WORKDIR}/concat.txt"
with open(concat,'w') as f:
    for i,dur in enumerate(DURS):
        img = IMGS[min(i,N-1)]
        if img: f.write(f"file '{img}'\nduration {dur:.3f}\n")
    if IMGS[-1]: f.write(f"file '{IMGS[-1]}'\n")

# ── RENDER ────────────────────────────────────────────────────
ts  = int(time.time())
OUT = f"{WORKDIR}/v683_poll_{ts}.mp4"
log(f"\n🎬 Renderizando CRF={CRF} 25fps...")
cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",concat,
       "-i",f"{WORKDIR}/audio.mp3",
       "-c:v","libx264","-pix_fmt","yuv420p","-crf",str(CRF),
       "-c:a","aac","-b:a","128k","-shortest","-r","25",
       "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
             "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
       "-movflags","+faststart",OUT]
res = subprocess.run(cmd,capture_output=True,text=True,timeout=600)
if res.returncode != 0:
    log(f"ERRO:\n{res.stderr[-500:]}"); sys.exit(1)

sz   = os.path.getsize(OUT)
dur2 = float(json.loads(subprocess.run(
    ["ffprobe","-v","quiet","-print_format","json","-show_format",OUT],
    capture_output=True,text=True).stdout)["format"]["duration"])
log(f"  ✅ {sz/1024/1024:.2f}MB | {dur2:.1f}s ({dur2/60:.1f}min)")

# ── UPLOAD ────────────────────────────────────────────────────
log(f"\n☁️  Upload Supabase...")
with open(OUT,'rb') as f: vdata = f.read()
video_url = None
for att in range(5):
    try:
        video_url = sb_upload(f"mp4s/v683_poll_{ts}.mp4", vdata, "video/mp4")
        log(f"  ✅ {video_url}"); break
    except Exception as e:
        log(f"  Tentativa {att+1}: {e}"); time.sleep(15)

if video_url:
    sb_patch(VIDEO_ID, {
        "video_url": video_url, "status": "pending_credentials",
        "metadata": json.dumps({
            "version": "pollinations_sequential",
            "poll": counts['poll'], "pillow": counts['pillow'],
            "file_mb": round(sz/1024/1024,2), "dur_s": round(dur2,1),
            "cenas": N, "rate_real": round(RATE,3)
        })
    })

log(f"\n{'='*55}")
log(f"  ψ RESULTADO — POLLINATIONS SEQUENCIAL")
log(f"  🌐 {counts['poll']}/{N} Pollinations | ✏️ {counts['pillow']} Pillow")
log(f"  {sz/1024/1024:.2f}MB | {dur2/60:.1f}min")
log(f"  V8 Final era: 6.27MB | 62s")
if sz/1024/1024 >= 6.27:
    log(f"  🏆 SUPEROU O V8 FINAL!")
else:
    log(f"  📈 {sz/1024/1024/6.27*100:.0f}% do V8 Final")
log(f"{'='*55}\n")
