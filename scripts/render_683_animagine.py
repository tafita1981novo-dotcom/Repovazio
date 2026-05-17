#!/usr/bin/env python3
"""
render_683_animagine.py — ANIMAGINE XL 4.0 (MELHOR CHIBI GRATUITO 2026)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ordem de tentativa por cena:
  1. HuggingFace Animagine XL 4.0 ← MELHOR para chibi anime (GRÁTIS)
  2. HuggingFace Animagine XL 3.1 ← fallback HF
  3. Pollinations Flux ← fallback externo
  4. Chibi HQ Pillow ← fallback local

Animagine XL 4.0: treinado em 8.4M imagens anime/chibi, tag (chibi:1.4) nativo
CRF=18, 30fps, 192kbps — qualidade máxima
"""
import os, sys, json, subprocess, requests, time, io, base64, warnings
from PIL import Image, ImageDraw
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse
warnings.filterwarnings("ignore")

VIDEO_ID   = 683
SB_URL     = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY     = os.environ.get("SUPABASE_SERVICE_KEY","")
HF_TOKEN   = os.environ.get("HF_TOKEN","")
W, H       = 1080, 1920
CRF        = 18
WORKDIR    = "/tmp/v683_animagine"
os.makedirs(WORKDIR, exist_ok=True)

VERM=(220,50,50); GOLD=(255,210,50); BRAN=(255,255,255); LILAS=(185,170,225)

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

# Carregar script
row = requests.get(
    f"{SB_URL}/rest/v1/content_pipeline?id=eq.{VIDEO_ID}&select=id,script",
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"},
    timeout=30).json()[0]
SCRIPT = row["script"].strip()
PARAS  = [p.strip() for p in SCRIPT.split('\n\n') if p.strip()]
N      = len(PARAS)

print(f"{'='*60}")
print(f"  ψ ANIMAGINE XL 4.0 — Vídeo #683")
print(f"  {N} cenas | HF_TOKEN: {'✅ SET' if HF_TOKEN else '❌ NÃO DEFINIDO'}")
print(f"{'='*60}\n")

# Captions
CAPTIONS = []
for p in PARAS:
    cap = p[:28].split('.')[0].split(',')[0].split('?')[0].strip()
    CAPTIONS.append(cap[:28])
if CAPTIONS: CAPTIONS[-1] = "INSCREVA-SE AGORA 🔔"

# Prompts Animagine (formato otimizado para chibi)
# Animagine usa: "chibi, (chibi:1.4), 1girl/1boy, visual description, style tags"
NEG = ("nsfw, lowres, bad anatomy, bad hands, text, error, missing finger, "
       "extra digit, fewer digit, watermark, signature, realistic, 3d render, "
       "photo, worst quality, low quality, blurry, jpeg artifact")

ANIMAGINE_PROMPTS = [
    "chibi, (chibi:1.4), 1girl, original character, auburn wavy hair, round glasses, yellow cardigan, sitting alone at night, holding smartphone anxiously, worried expression, blue light glow, cream background, simple background, kawaii, masterpiece, best quality, absurdres",
    "chibi, (chibi:1.4), 1girl, original character, auburn wavy hair, round glasses, yellow cardigan, reading message on phone, disappointed expression, small rain cloud above head, cream background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 1girl 1boy, original characters, auburn hair glasses yellow cardigan AND dark styled hair navy blazer, meeting at party, sparkle effects around boy, girl looks captivated, warm lighting, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original character, auburn wavy hair, round glasses, yellow cardigan, thoughtful expression, floating question marks around her, uneasy feeling, cream background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 1girl, original character, short dark bob hair, mint green blouse, small psi symbol pin, warm smile, looking directly at viewer, soft golden glow, cream background, kawaii, masterpiece, best quality, absurdres",
    "chibi, (chibi:1.4), 1girl, original character, auburn wavy hair, round glasses, yellow cardigan, hunched posture, sad expression, blame arrow pointing at her, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1boy, original characters, auburn hair AND dark navy blazer, dismissive gesture from boy, girl shrinking, emotional scene, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1woman, original character, neat dark bun, white lab coat, holding clipboard, pointing at research data, authoritative expression, cream background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 1boy, original character, dark styled hair, navy blazer, holding theater mask with friendly smile, dark shadow behind him, dramatic mood, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1boy, original character, dark styled hair, navy blazer, large number 1 badge floating, shrugging innocently, red X mark, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original character, auburn wavy hair, round glasses, yellow cardigan, touching temple while remembering, glowing memory bubble above head, confused expression, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1boy, original characters, auburn hair AND dark navy blazer, finger pointing at girl dismissively, girl shrinking smaller, power imbalance visual, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1woman 1girl, original characters, white lab coat dark bun AND auburn hair glasses, pointing at brain diagram with glowing highlights, realization expression, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original character, short dark bob hair, mint green blouse, holding golden shield, warm protective golden light, hopeful expression, cream background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 1girl 1boy, original characters, large number 2 badge, auburn hair glasses AND navy blazer, emotional speech bubble from girl, boy looking bored, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1boy, original characters, auburn hair glasses yellow cardigan AND dark navy blazer, girl crying, boy sighing dramatically, cold gap between them, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1boy, original character, dark navy blazer, floating negative labels around 1girl with auburn hair, dramatic dominating scene, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original character, auburn wavy hair, round glasses, yellow cardigan, apologizing gesture with hands pressed together, sad small expression, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original character, curly dark hair, flower hair clip, orange sweater, worried protective expression toward another girl, cream background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 2girls, original characters, curly dark hair orange sweater AND auburn hair glasses, face to face serious conversation, revelation expression, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original character, auburn wavy hair, round glasses, yellow cardigan, mirror showing fading reflection, identity erosion visual, melancholy mood, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1boy, original characters, large number 3 badge, auburn hair carrying heavy guilt weights labeled not hers, boy relaxing carefree, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1boy, original characters, auburn hair glasses yellow cardigan AND dark navy blazer, boy arriving late casual shrug, girl apologizing confused, wall clock showing late, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original character, auburn wavy hair, round glasses, yellow cardigan, hands to face worried, question mark floating unfairly toward her, lost expression, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original character, short dark bob hair, mint green blouse, psi symbol pin, urgent warm expression facing viewer directly, glowing important badge, cream background, kawaii, masterpiece, absurdres",
    "chibi, (chibi:1.4), 1woman, original character, neat dark bun, white lab coat, pointing at iceberg diagram, small narcissism tip above water, massive structure below, cream background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 1woman 1girl, original characters, white lab coat dark bun AND auburn hair glasses, showing cycle flowchart with arrows, shock recognition expression, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1girl, original characters, short dark bob mint blouse AND auburn hair glasses, opening bright glowing door to warm freedom light, hopeful scene, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original character, short dark bob hair, mint green blouse, psi symbol pin, direct eye contact with viewer, hand on heart, sincere warm golden light, cream background, kawaii, masterpiece, absurdres, best quality",
    "chibi, (chibi:1.4), 3girls, original characters, dark bob mint blouse AND auburn hair glasses AND curly dark hair orange sweater, arms around each other shoulders, unity strength warm scene, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1boy, original character, dark styled hair, navy blazer, hiding something important in shadow behind back, dramatic tension, 1girl about to discover the truth, cream background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original character, auburn wavy hair, round glasses, yellow cardigan, lightbulb revelation moment, eyes wide with understanding, everything clicking into place, cream background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 4girls, original characters, celebration scene, giant golden bell with sparkles, confetti rainbow colors, arms raised joyfully, festive mood, cream background, kawaii, masterpiece, best quality, absurdres",
]

HF_MODELS = [
    "cagliostrolab/animagine-xl-4.0",
    "cagliostrolab/animagine-xl-3.1",
]

counts = {"animagine":0, "pollinations":0, "chibi":0}

def try_animagine(prompt, idx):
    """HuggingFace Animagine XL — melhor chibi gratuito 2026."""
    if not HF_TOKEN:
        return None, None

    for model in HF_MODELS:
        url = f"https://api-inference.huggingface.co/models/{model}"
        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": NEG,
                "width": 576, "height": 1024,
                "guidance_scale": 7,
                "num_inference_steps": 25,
                "seed": 42 + idx * 17
            }
        }
        headers = {"Authorization": f"Bearer {HF_TOKEN}",
                   "Content-Type": "application/json"}
        for attempt in range(2):
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=150)
                if r.status_code == 200 and 'image' in r.headers.get('content-type',''):
                    img = Image.open(io.BytesIO(r.content)).convert("RGB")
                    img = img.resize((W, H), Image.LANCZOS)
                    out = f"{WORKDIR}/ai_{idx:02d}.jpg"
                    img.save(out, "JPEG", quality=97)
                    return out, f"animagine/{model.split('/')[1][:8]}"
                elif r.status_code == 503:
                    # Cold start — aguardar e tentar novamente
                    wait = int(r.json().get("estimated_time", 25)) if r.headers.get('content-type','').startswith('application/json') else 25
                    wait = min(wait, 45)
                    print(f"  [{idx+1:02d}] ⏳ {model.split('/')[1]} cold start, aguardando {wait}s...")
                    time.sleep(wait)
                    continue
                elif r.status_code == 429:
                    time.sleep(15)
                    continue
                elif r.status_code == 401:
                    print(f"  ❌ HF token inválido")
                    return None, None
                else:
                    break
            except Exception as e:
                print(f"  [{idx+1:02d}] 💥 HF {str(e)[:50]}")
                break
        time.sleep(2)
    return None, None

def try_pollinations(prompt_base, idx):
    """Pollinations como segundo fallback."""
    full = (f"chibi anime kawaii style, {prompt_base}, "
            f"cream background, pastel colors, flat design, no text, original character")
    enc  = urllib.parse.quote(full)
    seed = 100 + idx * 23
    for model in ["flux", "turbo"]:
        try:
            url = (f"https://image.pollinations.ai/prompt/{enc}"
                   f"?width=576&height=1024&seed={seed}&nologo=true"
                   f"&model={model}&enhance=true")
            r = requests.get(url, timeout=90, verify=False)
            if r.status_code == 200 and 'image' in r.headers.get('content-type',''):
                if len(r.content) > 40000:
                    img = Image.open(io.BytesIO(r.content)).convert("RGB").resize((W,H), Image.LANCZOS)
                    out = f"{WORKDIR}/ai_{idx:02d}.jpg"
                    img.save(out, "JPEG", quality=97)
                    return out, f"poll/{model}"
        except:
            pass
        time.sleep(1)
    return None, None

def gen_chibi_hq(idx):
    """Chibi Pillow profissional."""
    img = Image.new("RGB", (W,H), (245,240,232))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y/H; r=int(245+(228-245)*t); g=int(240+(222-240)*t); b=int(232+(215-232)*t)
        draw.line([(0,y),(W,y)], fill=(r,g,b))
    draw.ellipse([W//2-320,H//2-380,W//2+320,H//2+380], fill=(238,230,218))
    paletas = [(100,185,130),(80,130,200),(200,90,130),(130,180,80),(200,150,70)]
    clr = paletas[idx % len(paletas)]
    cx = W//2; cy = H//2 - 100
    draw.ellipse([cx-80,cy+220,cx+80,cy+265], fill=(175,165,155))
    draw.rounded_rectangle([cx-82,cy+25,cx+82,cy+255], radius=25, fill=clr)
    draw.ellipse([cx-95,cy-215,cx+95,cy+40], fill=(255,220,185))
    draw.ellipse([cx-98,cy-265,cx+98,cy-90], fill=(35,22,8))
    for ex in [cx-38, cx+22]:
        draw.ellipse([ex,cy-100,ex+38,cy-64], fill=(255,255,255))
        draw.ellipse([ex+5,cy-95,ex+33,cy-69], fill=(30,20,60))
        draw.ellipse([ex+26,cy-97,ex+34,cy-89], fill=(255,255,255))
    for bx in [cx-58, cx+22]: draw.ellipse([bx,cy-40,bx+44,cy-10], fill=(255,185,185))
    draw.arc([cx-28,cy-25,cx+28,cy+12], start=0, end=180, fill=(180,55,55), width=4)
    draw.text((cx-8,cy+32), "ψ", fill=GOLD)
    out = f"{WORKDIR}/ai_{idx:02d}.jpg"
    img.save(out, "JPEG", quality=97)
    return out, "chibi"

def add_overlay(img_path, caption):
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    for y in range(H-105, H):
        t=(y-(H-105))/105
        draw.line([(0,y),(W,y)], fill=(int(8+12*t),int(6+8*t),int(18+15*t)))
    draw.rectangle([0,H-105,5,H], fill=VERM)
    draw.rectangle([0,H-4,W,H], fill=VERM)
    draw.text((22,H-95), "ψ", fill=GOLD)
    draw.text((60,H-90), "Daniela Coelho", fill=BRAN)
    draw.text((60,H-55), "Saúde Mental  |  @psidanielacoelho", fill=LILAS)
    if caption and len(caption) > 2:
        cap = caption[:30].upper()
        bw = min(len(cap)*15+60, W-80); bcx=W//2; by=60
        draw.rounded_rectangle([bcx-bw//2+3,by-22+3,bcx+bw//2+3,by+26+3], radius=16, fill=(180,170,200))
        draw.rounded_rectangle([bcx-bw//2,by-22,bcx+bw//2,by+26], radius=16, fill=(252,250,255), outline=(210,200,235), width=2)
        draw.text((bcx-bw//2+26,by-9), cap, fill=(25,15,55))
    img.save(img_path, "JPEG", quality=98)

def process_scene(args):
    idx, prompt = args
    cap = CAPTIONS[idx] if idx < len(CAPTIONS) else ""

    # 1. Animagine XL 4.0 (melhor chibi 2026)
    path, src = try_animagine(prompt, idx)
    if path:
        add_overlay(path, cap)
        sz = os.path.getsize(path)//1024
        print(f"  [{idx+1:02d}] 🎨 {src} | {sz}KB | ✅ ANIME AI")
        return path, "animagine"

    # 2. Pollinations
    path, src = try_pollinations(prompt[:100], idx)
    if path:
        add_overlay(path, cap)
        sz = os.path.getsize(path)//1024
        print(f"  [{idx+1:02d}] 🌐 {src} | {sz}KB")
        return path, "pollinations"

    # 3. Chibi HQ
    path, src = gen_chibi_hq(idx)
    add_overlay(path, cap)
    sz = os.path.getsize(path)//1024
    print(f"  [{idx+1:02d}] ✏️  chibi | {sz}KB")
    return path, "chibi"

print(f"🎨 Gerando {N} cenas com Animagine XL 4.0...\n")
IMGS = [None]*N
t0 = time.time()

# Paralelo com 4 workers (respeitar rate limit do HF)
with ThreadPoolExecutor(max_workers=4) as ex:
    futures = {ex.submit(process_scene,(i,p)):i for i,p in enumerate(ANIMAGINE_PROMPTS)}
    for fut in as_completed(futures):
        i = futures[fut]; path, src = fut.result()
        IMGS[i] = path; counts[src if src in counts else "chibi"] += 1
        time.sleep(0.5)

gen_t = time.time()-t0
ai = counts.get("animagine",0)
print(f"\n  {'='*40}")
print(f"  Animagine:{ai} | Poll:{counts.get('pollinations',0)} | Chibi:{counts.get('chibi',0)} | {gen_t:.0f}s")
print(f"  {'='*40}\n")

# Áudio
print("🎙️  Baixando áudio V8 Final...")
ar = requests.get(
    f"{SB_URL}/storage/v1/object/public/videos/audios/v683_v8_1778892031.mp3",
    timeout=60)
with open(f"{WORKDIR}/audio.mp3",'wb') as f: f.write(ar.content)
probe = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",
    f"{WORKDIR}/audio.mp3"], capture_output=True, text=True)
DUR = float(json.loads(probe.stdout)["format"]["duration"])
RATE = len(SCRIPT)/DUR
print(f"  {DUR:.1f}s | RATE={RATE:.3f}")
DURS = [max(0.5, round(len(p)/RATE, 3)) for p in PARAS]

# ffconcat
concat = f"{WORKDIR}/concat.txt"
with open(concat,'w') as f:
    for i, dur in enumerate(DURS):
        img = IMGS[min(i,N-1)]
        if img: f.write(f"file '{img}'\nduration {dur:.3f}\n")
    if IMGS[-1]: f.write(f"file '{IMGS[-1]}'\n")

# Render
ts = int(time.time())
OUT = f"{WORKDIR}/v683_animagine_{ts}.mp4"
print(f"\n🎬 Renderizando CRF={CRF} 30fps...")
cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",concat,
       "-i",f"{WORKDIR}/audio.mp3",
       "-c:v","libx264","-pix_fmt","yuv420p","-crf",str(CRF),"-preset","slow",
       "-c:a","aac","-b:a","192k","-shortest","-r","30",
       "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
             "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
       "-movflags","+faststart",OUT]
res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
if res.returncode != 0:
    print(f"ERRO:\n{res.stderr[-500:]}"); sys.exit(1)

sz = os.path.getsize(OUT)
probe2 = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",OUT],
    capture_output=True, text=True)
dur2 = float(json.loads(probe2.stdout)["format"]["duration"])
print(f"  ✅ {sz/1024/1024:.2f}MB | {dur2:.1f}s ({dur2/60:.1f}min)")
print(f"  V8 Final: 6.27MB")

# Upload
print(f"\n☁️  Upload Supabase...")
with open(OUT,'rb') as f: vdata = f.read()
video_url = None
for att in range(5):
    try:
        video_url = sb_upload(f"mp4s/v683_animagine_{ts}.mp4", vdata, "video/mp4"); break
    except Exception as e: time.sleep(15)

if video_url:
    sb_patch(VIDEO_ID, {
        "video_url": video_url, "status": "pending_credentials",
        "metadata": json.dumps({
            "version":"animagine_xl_4", "crf":CRF, "fps":30, "cenas":N,
            "animagine":ai, "pollinations":counts.get("pollinations",0),
            "chibi":counts.get("chibi",0), "dur_s":round(dur2,1),
            "file_mb":round(sz/1024/1024,2)
        })
    })

print(f"\n{'='*60}")
print(f"  ψ RESULTADO — ANIMAGINE XL 4.0")
print(f"  Anime AI: {ai}/{N} ({ai*100//N}%)")
print(f"  {sz/1024/1024:.2f}MB | {dur2/60:.1f}min | CRF={CRF}")
print(f"  🎬 {video_url or 'ERRO NO UPLOAD'}")
print(f"{'='*60}\n")
