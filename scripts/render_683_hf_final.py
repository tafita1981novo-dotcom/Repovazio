#!/usr/bin/env python3
"""
render_683_hf_final.py — HUGGINGFACE ANIMAGINE XL 4.0 CORRETO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Usa huggingface_hub.InferenceClient que:
  ✅ Gerencia cold start automaticamente (polling até modelo ficar pronto)
  ✅ Aguarda sem timeout arbitrário
  ✅ Animagine XL 4.0 → melhor chibi 2026 (8.4M imagens anime)

Pipeline: Animagine XL 4.0 → Pollinations → Chibi HQ
"""
import os, sys, json, subprocess, requests, time, io, warnings
from PIL import Image, ImageDraw
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse
warnings.filterwarnings("ignore")

# Instalar huggingface_hub se necessário
try:
    from huggingface_hub import InferenceClient
except ImportError:
    subprocess.run([sys.executable,"-m","pip","install","huggingface_hub","--quiet"])
    from huggingface_hub import InferenceClient

VIDEO_ID   = 683
SB_URL     = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY     = os.environ.get("SUPABASE_SERVICE_KEY","")
HF_TOKEN   = os.environ.get("HF_TOKEN","")
W, H       = 1080, 1920
CRF        = 18
WORKDIR    = "/tmp/v683_hf"
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
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"},timeout=30).json()[0]
SCRIPT = row["script"].strip()
PARAS  = [p.strip() for p in SCRIPT.split('\n\n') if p.strip()]
N      = len(PARAS)

print(f"{'='*60}")
print(f"  ψ HF ANIMAGINE XL 4.0 FINAL — #683")
print(f"  {N} cenas | HF: {'✅' if HF_TOKEN else '❌'}")
print(f"{'='*60}\n")

CAPTIONS = []
for p in PARAS:
    cap = p[:28].split('.')[0].split(',')[0].split('?')[0].strip()
    CAPTIONS.append(cap[:28])
if CAPTIONS: CAPTIONS[-1] = "INSCREVA-SE AGORA 🔔"

NEG = ("nsfw, lowres, bad anatomy, bad hands, text, error, "
       "watermark, signature, realistic, 3d, photo, "
       "worst quality, low quality, blurry, jpeg artifacts")

# 33 prompts otimizados para Animagine XL (formato correto)
PROMPTS = [
    "chibi, (chibi:1.4), 1girl, original, auburn wavy hair, round glasses, yellow cardigan, holding smartphone, worried expression at night, blue glow, white background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 1girl, original, auburn hair, round glasses, reading phone message, disappointed face, small rain cloud, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1boy, original, auburn hair glasses yellow cardigan, dark styled hair navy blazer, meeting at party, sparkle effects, white background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 1girl, original, auburn hair, round glasses, yellow cardigan, thoughtful, question marks floating, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original, short dark bob hair, mint green blouse, small psi pin, warm smile, looking at viewer, white background, kawaii, masterpiece, best quality, absurdres",
    "chibi, (chibi:1.4), 1girl, original, auburn hair, round glasses, yellow cardigan, sad expression, hunched posture, blame arrow, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1boy, original, auburn hair glasses, dark navy blazer, dismissive gesture from boy, girl looking small, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original, dark bun, white lab coat, clipboard, pointing at research data, authoritative, white background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 1boy, original, dark styled hair, navy blazer, holding friendly theater mask, dark shadow behind, dramatic, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1boy, original, dark hair navy blazer, shrugging innocently, number 1 badge floating, red X mark, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original, auburn hair, round glasses, yellow cardigan, touching temple, glowing memory bubble, confused, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1boy, original, auburn hair glasses, dark navy blazer, finger pointing dismissively, girl shrinking, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1girl, original, white lab coat dark bun, auburn hair glasses, brain diagram with glowing highlights, realization, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original, short dark bob hair, mint green blouse, holding golden shield, warm protective light, white background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 1girl 1boy, original, number 2 badge, auburn hair glasses, navy blazer, emotional speech bubble from girl, boy bored, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1boy, original, auburn hair glasses yellow cardigan, dark navy blazer, girl crying, boy sighing dramatically, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1boy, original, auburn hair, dark navy blazer, negative label tags floating, dramatic domination, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original, auburn hair, round glasses, yellow cardigan, apologizing hands pressed together, sad, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original, curly dark hair, flower clip, orange sweater, worried protective expression, white background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 2girls, original, curly dark hair orange sweater, auburn hair glasses, face to face conversation, revelation expression, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original, auburn hair, round glasses, yellow cardigan, mirror with fading reflection, identity erosion, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1boy, original, number 3 badge, auburn hair carrying guilt weights, boy relaxing, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1boy, original, auburn hair glasses yellow cardigan, dark navy blazer, boy casual late shrug, girl apologizing, clock, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original, auburn hair, round glasses, yellow cardigan, hands to face worried, question mark floating unfairly, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original, short dark bob hair, mint green blouse, psi pin, urgent expression facing viewer, golden glow, white background, kawaii, masterpiece, absurdres",
    "chibi, (chibi:1.4), 1girl, original, dark bun, white lab coat, iceberg diagram, narcissism tip above water, white background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 1girl 1girl, original, white lab coat dark bun, auburn hair glasses, cycle flowchart arrows, shock expression, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl 1girl, original, short dark bob mint blouse, auburn hair glasses, bright door to freedom, hopeful, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original, short dark bob hair, mint green blouse, psi pin, direct eye contact, hand on heart, golden light, white background, kawaii, masterpiece, absurdres, best quality",
    "chibi, (chibi:1.4), 3girls, original, dark bob mint blouse, auburn hair glasses, curly dark hair orange sweater, arms around each other, unity, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1boy, original, dark styled hair navy blazer, hiding something in shadow, dramatic tension, white background, kawaii, masterpiece",
    "chibi, (chibi:1.4), 1girl, original, auburn hair, round glasses, yellow cardigan, lightbulb moment, eyes wide with revelation, white background, kawaii, masterpiece, best quality",
    "chibi, (chibi:1.4), 4girls, original, celebration scene, giant golden bell, sparkles, confetti, arms raised joyfully, colorful, white background, kawaii, masterpiece, best quality, absurdres",
]

# Criar cliente HF
hf_client = None
if HF_TOKEN:
    try:
        hf_client = InferenceClient(
            model="cagliostrolab/animagine-xl-4.0",
            token=HF_TOKEN,
            timeout=180  # 3 minutos de timeout (cold start pode demorar)
        )
        print(f"✅ InferenceClient Animagine XL 4.0 pronto\n")
    except Exception as e:
        print(f"❌ Erro InferenceClient: {e}\n")

counts = {"animagine":0, "pollinations":0, "chibi":0}

def try_animagine_client(prompt, idx):
    """HF InferenceClient — gerencia cold start automaticamente."""
    if not hf_client:
        return None
    for attempt in range(2):
        try:
            result = hf_client.text_to_image(
                prompt=prompt,
                negative_prompt=NEG,
                width=576, height=1024,
                guidance_scale=7,
                num_inference_steps=25,
            )
            if result:
                out = f"{WORKDIR}/ai_{idx:02d}.jpg"
                result.save(out, "JPEG", quality=97)
                return out
        except Exception as e:
            err = str(e)
            if "loading" in err.lower() or "503" in err or "cold" in err.lower():
                print(f"  [{idx+1:02d}] ⏳ Animagine warm-up, aguardando 60s...")
                time.sleep(60)
            else:
                print(f"  [{idx+1:02d}] 💥 HF: {err[:70]}")
                break
    return None

def try_animagine_raw(prompt, idx):
    """Fallback: chamada direta à API HF."""
    if not HF_TOKEN:
        return None
    for model in ["cagliostrolab/animagine-xl-4.0","cagliostrolab/animagine-xl-3.1"]:
        url = f"https://api-inference.huggingface.co/models/{model}"
        payload = {"inputs": prompt,
                   "parameters":{"negative_prompt":NEG,"width":576,"height":1024,
                                  "guidance_scale":7,"num_inference_steps":25}}
        for att in range(3):
            try:
                r = requests.post(url,
                    headers={"Authorization":f"Bearer {HF_TOKEN}"},
                    json=payload, timeout=180)
                if r.status_code == 200 and 'image' in r.headers.get('content-type',''):
                    img = Image.open(io.BytesIO(r.content)).convert("RGB")
                    img = img.resize((W,H), Image.LANCZOS)
                    out = f"{WORKDIR}/ai_{idx:02d}.jpg"
                    img.save(out,"JPEG",quality=97)
                    return out
                elif r.status_code == 503:
                    data = {}
                    try: data = r.json()
                    except: pass
                    wait = min(data.get("estimated_time",60), 120)
                    print(f"  [{idx+1:02d}] ⏳ HF cold start ({wait}s)...")
                    time.sleep(wait)
                elif r.status_code == 429:
                    time.sleep(30)
                else:
                    break
            except Exception as e:
                print(f"  [{idx+1:02d}] raw err: {str(e)[:50]}")
                break
    return None

def try_pollinations(idx):
    prompt = PROMPTS[idx][:150]
    full = f"chibi anime kawaii psych2go style, {prompt}, cream background, flat design, no text"
    enc = urllib.parse.quote(full)
    seed = 100 + idx * 23
    for model in ["flux","turbo"]:
        try:
            url = (f"https://image.pollinations.ai/prompt/{enc}"
                   f"?width=576&height=1024&seed={seed}&nologo=true"
                   f"&model={model}&enhance=true")
            r = requests.get(url, timeout=90, verify=False)
            if r.status_code==200 and 'image' in r.headers.get('content-type','') and len(r.content)>40000:
                img = Image.open(io.BytesIO(r.content)).convert("RGB").resize((W,H),Image.LANCZOS)
                out = f"{WORKDIR}/ai_{idx:02d}.jpg"
                img.save(out,"JPEG",quality=97)
                return out
        except: pass
        time.sleep(1)
    return None

def gen_chibi(idx):
    img = Image.new("RGB",(W,H),(245,240,232))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t=y/H; r=int(245+(228-245)*t); g=int(240+(222-240)*t); b=int(232+(215-232)*t)
        draw.line([(0,y),(W,y)],fill=(r,g,b))
    draw.ellipse([W//2-320,H//2-380,W//2+320,H//2+380],fill=(238,230,218))
    clrs=[(100,185,130),(80,130,200),(200,90,130),(130,180,80),(200,150,70)]
    clr=clrs[idx%len(clrs)]; cx=W//2; cy=H//2-100
    draw.ellipse([cx-80,cy+220,cx+80,cy+265],fill=(175,165,155))
    draw.rounded_rectangle([cx-82,cy+25,cx+82,cy+255],radius=25,fill=clr)
    draw.ellipse([cx-95,cy-215,cx+95,cy+40],fill=(255,220,185))
    draw.ellipse([cx-98,cy-265,cx+98,cy-90],fill=(35,22,8))
    for ex in [cx-38,cx+22]:
        draw.ellipse([ex,cy-100,ex+38,cy-64],fill=(255,255,255))
        draw.ellipse([ex+5,cy-95,ex+33,cy-69],fill=(30,20,60))
        draw.ellipse([ex+26,cy-97,ex+34,cy-89],fill=(255,255,255))
    for bx in [cx-58,cx+22]: draw.ellipse([bx,cy-40,bx+44,cy-10],fill=(255,185,185))
    draw.arc([cx-28,cy-25,cx+28,cy+12],start=0,end=180,fill=(180,55,55),width=4)
    draw.text((cx-8,cy+32),"ψ",fill=GOLD)
    out=f"{WORKDIR}/ai_{idx:02d}.jpg"; img.save(out,"JPEG",quality=97)
    return out

def add_overlay(img_path, caption):
    img=Image.open(img_path).convert("RGB"); draw=ImageDraw.Draw(img)
    for y in range(H-105,H):
        t=(y-(H-105))/105
        draw.line([(0,y),(W,y)],fill=(int(8+12*t),int(6+8*t),int(18+15*t)))
    draw.rectangle([0,H-105,5,H],fill=VERM); draw.rectangle([0,H-4,W,H],fill=VERM)
    draw.text((22,H-95),"ψ",fill=GOLD); draw.text((60,H-90),"Daniela Coelho",fill=BRAN)
    draw.text((60,H-55),"Saúde Mental  |  @psidanielacoelho",fill=LILAS)
    if caption and len(caption)>2:
        cap=caption[:30].upper(); bw=min(len(cap)*15+60,W-80); bcx=W//2; by=60
        draw.rounded_rectangle([bcx-bw//2+3,by-22+3,bcx+bw//2+3,by+26+3],radius=16,fill=(180,170,200))
        draw.rounded_rectangle([bcx-bw//2,by-22,bcx+bw//2,by+26],radius=16,fill=(252,250,255),outline=(210,200,235),width=2)
        draw.text((bcx-bw//2+26,by-9),cap,fill=(25,15,55))
    img.save(img_path,"JPEG",quality=98)

def process_scene(args):
    idx, prompt = args
    cap = CAPTIONS[idx] if idx<len(CAPTIONS) else ""

    # 1. Animagine InferenceClient
    path = try_animagine_client(prompt, idx)
    if path:
        add_overlay(path, cap)
        sz=os.path.getsize(path)//1024
        print(f"  [{idx+1:02d}] 🎨 Animagine XL 4.0 | {sz}KB ← ANIME AI REAL")
        return path, "animagine"

    # 2. Animagine raw API
    path = try_animagine_raw(prompt, idx)
    if path:
        add_overlay(path, cap)
        sz=os.path.getsize(path)//1024
        print(f"  [{idx+1:02d}] 🎨 Animagine raw | {sz}KB")
        return path, "animagine"

    # 3. Pollinations
    path = try_pollinations(idx)
    if path:
        add_overlay(path, cap)
        sz=os.path.getsize(path)//1024
        print(f"  [{idx+1:02d}] 🌐 Pollinations | {sz}KB")
        return path, "pollinations"

    # 4. Chibi local
    path = gen_chibi(idx)
    add_overlay(path, cap)
    print(f"  [{idx+1:02d}] ✏️  Chibi HQ | {os.path.getsize(path)//1024}KB")
    return path, "chibi"

# PRÉ-AQUECER Animagine com 1 imagem primeiro
print("🔥 Pré-aquecendo Animagine XL 4.0 (cold start pode levar 2-3 min)...")
warmup_path = try_animagine_client(PROMPTS[4], 99)  # Cena 5: Daniela
if warmup_path:
    print(f"  ✅ Animagine aquecido! ({os.path.getsize(warmup_path)//1024}KB)")
    os.rename(warmup_path, f"{WORKDIR}/warmup.jpg")
else:
    print(f"  ⚠️ Warmup falhou — usando Pollinations como backup")

print(f"\n🎨 Gerando {N} cenas...\n")
IMGS = [None]*N
t0 = time.time()

with ThreadPoolExecutor(max_workers=3) as ex:
    futures = {ex.submit(process_scene,(i,p)):i for i,p in enumerate(PROMPTS)}
    for fut in as_completed(futures):
        i=futures[fut]; path,src=fut.result()
        IMGS[i]=path; counts[src if src in counts else "chibi"]+=1
        time.sleep(0.3)

# Recuperar cena 5 do warmup se necessário
if os.path.exists(f"{WORKDIR}/warmup.jpg") and not IMGS[4]:
    img=Image.open(f"{WORKDIR}/warmup.jpg").convert("RGB").resize((W,H),Image.LANCZOS)
    out=f"{WORKDIR}/ai_04.jpg"; img.save(out,"JPEG",quality=97)
    add_overlay(out, CAPTIONS[4])
    IMGS[4]=out; counts["animagine"]+=1

gen_t=time.time()-t0
ai=counts.get("animagine",0)
print(f"\n  Animagine:{ai} | Poll:{counts.get('pollinations',0)} | Chibi:{counts.get('chibi',0)} | {gen_t:.0f}s\n")

# Áudio
print("🎙️  Baixando áudio V8 Final...")
ar=requests.get(f"{SB_URL}/storage/v1/object/public/videos/audios/v683_v8_1778892031.mp3",timeout=60)
with open(f"{WORKDIR}/audio.mp3",'wb') as f: f.write(ar.content)
probe=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",
    f"{WORKDIR}/audio.mp3"],capture_output=True,text=True)
DUR=float(json.loads(probe.stdout)["format"]["duration"])
RATE=len(SCRIPT)/DUR; DURS=[max(0.5,round(len(p)/RATE,3)) for p in PARAS]
print(f"  {DUR:.1f}s | RATE={RATE:.3f}")

# Concat + render
concat=f"{WORKDIR}/concat.txt"
with open(concat,'w') as f:
    for i,dur in enumerate(DURS):
        img=IMGS[min(i,N-1)]
        if img: f.write(f"file '{img}'\nduration {dur:.3f}\n")
    if IMGS[-1]: f.write(f"file '{IMGS[-1]}'\n")

ts=int(time.time()); OUT=f"{WORKDIR}/v683_hf_{ts}.mp4"
print(f"\n🎬 Renderizando CRF={CRF}...")
cmd=["ffmpeg","-y","-f","concat","-safe","0","-i",concat,
     "-i",f"{WORKDIR}/audio.mp3",
     "-c:v","libx264","-pix_fmt","yuv420p","-crf",str(CRF),"-preset","slow",
     "-c:a","aac","-b:a","192k","-shortest","-r","30",
     "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
           "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
     "-movflags","+faststart",OUT]
res=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
if res.returncode!=0: print(f"ERRO:{res.stderr[-400:]}"); sys.exit(1)

sz=os.path.getsize(OUT)
probe2=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",OUT],
    capture_output=True,text=True)
dur2=float(json.loads(probe2.stdout)["format"]["duration"])
print(f"  ✅ {sz/1024/1024:.2f}MB | {dur2:.1f}s | Animagine:{ai}/{N}")

# Upload
print(f"\n☁️  Upload...")
with open(OUT,'rb') as f: vdata=f.read()
video_url=None
for att in range(5):
    try:
        video_url=sb_upload(f"mp4s/v683_hf_{ts}.mp4",vdata,"video/mp4"); break
    except: time.sleep(15)

if video_url:
    sb_patch(VIDEO_ID,{"video_url":video_url,"status":"pending_credentials",
        "metadata":json.dumps({"version":"animagine_xl_4","crf":CRF,"fps":30,
            "animagine":ai,"pollinations":counts.get("pollinations",0),
            "chibi":counts.get("chibi",0),"dur_s":round(dur2,1),"file_mb":round(sz/1024/1024,2)})})

print(f"\n{'='*60}")
print(f"  ψ RESULTADO FINAL")
print(f"  Animagine AI: {ai}/{N} ({ai*100//N if N else 0}%)")
print(f"  {sz/1024/1024:.2f}MB | {dur2/60:.1f}min | CRF={CRF}")
print(f"  V8 Final era: 6.27MB")
print(f"  🎬 {video_url or 'ERRO'}")
print(f"{'='*60}\n")
