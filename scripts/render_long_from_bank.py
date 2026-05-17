#!/usr/bin/env python3
"""
render_long_from_bank.py — LONG 15MIN COM BANCO DE IMAGENS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANTI-TIMEOUT: Busca imagens do banco (pré-geradas)
- Se achou no banco: download direto (2s por imagem)
- Se não achou: gera via Pollinations (16s)
- 100 imgs × 2s = 3min (vs 27min antes!)
- Total estimado: ~12-15min (bem dentro de 90min)
"""
import os, sys, json, subprocess, requests, time, urllib.parse, asyncio, re
from PIL import Image, ImageDraw

VIDEO_ID = int(os.environ.get("VIDEO_ID","683"))
SB_URL   = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY   = os.environ.get("SUPABASE_SERVICE_KEY","")
W, H     = 1080, 1920
CRF, FPS = 25, 25  # 25=~35MB (vs 22=59MB, Supabase limit)
TARGET_S = 900
IMG_INT  = 3
N_APPEAR = TARGET_S // IMG_INT  # 300
N_UNIQUE = N_APPEAR // 3        # 100
RATE_ADJ = "+32%"  # 1189s natural → 900s = 15min exatos
WORKDIR  = f"/tmp/v{VIDEO_ID}_long15"
os.makedirs(WORKDIR, exist_ok=True)

VERM=(220,50,50); GOLD=(255,210,50); BRAN=(255,255,255)
LILAS=(185,170,225); DARK=(8,6,18)
def log(m): print(m, flush=True)

# ── PERSONAGENS ──────────────────────────────────────────────
DANIELA = "kawaii chibi anime girl, short dark bob hair, mint-green blouse, gold psi pin, warm knowing smile, big expressive eyes"
SARA    = "kawaii chibi anime girl, wavy auburn hair, round glasses, yellow cardigan, emotional big expressive eyes"
MARCOS  = "kawaii chibi anime man, styled dark hair, navy blazer, charming calculating smile, subtle sinister aura"
JULIA   = "kawaii chibi anime girl, curly dark hair, orange sweater, warm caring protective expression"
ANA     = "kawaii chibi anime woman, dark bun, white lab coat, clipboard, authoritative calm expression"
STYLE   = "Psych2Go anime flat illustration, soft cream background #F5F0E8, pastel colors, clean line art, original design, no text, no watermarks"

# ── BUSCA NO BANCO DE IMAGENS ────────────────────────────────
def search_image_bank(char_slug, scene_type, keywords=[]):
    """Busca imagem pré-gerada no banco Supabase"""
    params = f"character_slug=eq.{char_slug}&scene_type=eq.{scene_type}&order=times_used.asc&limit=1"
    r = requests.get(f"{SB_URL}/rest/v1/image_bank?{params}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=10)
    if r.status_code == 200 and r.json():
        row = r.json()[0]
        # Incrementar counter
        requests.patch(f"{SB_URL}/rest/v1/image_bank?id=eq.{row['id']}",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json"},
            json={"times_used": row.get("times_used",0)+1}, timeout=5)
        return row["image_url"]
    return None

def download_bank_image(url, out_path):
    """Baixa imagem do banco e redimensiona para 1080×1920"""
    r = requests.get(url, timeout=30)
    if r.status_code == 200 and len(r.content) > 10000:
        img = Image.open(__import__('io').BytesIO(r.content)).convert("RGB")
        img = img.resize((W,H), Image.LANCZOS)
        img.save(out_path, "JPEG", quality=95)
        return True
    return False

# ── DETECÇÃO DE PERSONAGEM ───────────────────────────────────
def detect_char_scene(text, pos):
    t = text.lower()
    if any(k in t for k in ["daniela","pergunta","você está"]):
        return "daniela", "gancho" if pos < 0.15 else "cta"
    elif any(k in t for k in ["dra","ana ","harvard","estudo","neurolog","cérebro"]):
        return "ana", "ciencia"
    elif any(k in t for k in ["julia","amiga "]):
        return "julia", "virada"
    elif any(k in t for k in ["marcos","narcis","manipul"]):
        return "marcos", "problema"
    elif any(k in t for k in ["lucas"]):
        return "lucas", "virada"
    elif pos < 0.12:
        return "sara", "gancho"
    elif pos > 0.85:
        return "daniela", "cta"
    else:
        return "sara", "problema" if pos < 0.6 else "virada"

# ── SUPABASE ─────────────────────────────────────────────────
def sb_get_script():
    SCRIPT_ENV = os.environ.get("SCRIPT_LONG","")
    if SCRIPT_ENV and len(SCRIPT_ENV) > 500: return SCRIPT_ENV
    r = requests.get(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{VIDEO_ID}&select=script",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=30)
    rows = r.json()
    if rows and rows[0].get("script"): return rows[0]["script"]
    raise ValueError(f"Script não encontrado para id={VIDEO_ID}")

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

# ── SPLIT 300 SEGMENTOS ──────────────────────────────────────
def split_300(raw):
    text = re.sub(r'\s+', ' ', raw.strip())
    sentences = re.split(r'(?<=[.!?])\s+', text)
    fine = []
    target = len(text)/N_APPEAR
    for s in sentences:
        if len(s) > target*1.8:
            fine.extend([p.strip() for p in re.split(r'(?<=,)\s+', s) if p.strip()])
        else: fine.append(s)
    segs = []; cur = ""
    for s in fine:
        if cur and len(cur)+len(s)+1 > target*1.4 and len(cur) > target*0.4:
            segs.append(cur.strip()); cur = s
        else: cur = (cur+" "+s).strip() if cur else s
    if cur: segs.append(cur.strip())
    while len(segs) < N_APPEAR:
        li = max(range(len(segs)),key=lambda i:len(segs[i]))
        m=len(segs[li])//2; c=segs[li].rfind(' ',max(0,m-20),m+20)
        if c<1: c=m
        segs[li],_ = segs[li][:c].strip(), None
        segs.insert(li+1, segs[li][c:].strip() if _ else segs[li][c:])
        segs[li] = segs[li][:c].strip()
    while len(segs) > N_APPEAR:
        mi=float('inf'); at=0
        for i in range(len(segs)-1):
            if len(segs[i])+len(segs[i+1]) < mi: mi=len(segs[i])+len(segs[i+1]); at=i
        segs[at]=(segs[at]+" "+segs[at+1]).strip(); segs.pop(at+1)
    return segs

def measure_dur(path):
    p = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",path],
        capture_output=True,text=True)
    return float(json.loads(p.stdout)["format"]["duration"])

def add_overlay(img_path, caption):
    img=Image.open(img_path).convert("RGB"); draw=ImageDraw.Draw(img)
    draw.rectangle([0,H-100,W,H],fill=DARK)
    draw.rectangle([0,H-100,6,H],fill=VERM)
    draw.rectangle([0,H-4,W,H],fill=VERM)
    draw.text((22,H-90),"ψ",fill=GOLD)
    draw.text((62,H-88),"Daniela Coelho",fill=BRAN)
    draw.text((62,H-58),"Saúde Mental  |  @psidanielacoelho",fill=LILAS)
    if caption:
        cap=caption[:28].upper(); bw=min(len(cap)*14+50,W-60); cx=W//2
        draw.rounded_rectangle([cx-bw//2,38,cx+bw//2,80],radius=14,fill=(250,248,255),outline=(210,200,235),width=2)
        draw.text((cx-bw//2+20,48),cap,fill=(20,15,45))
    img.save(img_path,"JPEG",quality=95)

def gen_pillow(idx):
    img=Image.new("RGB",(W,H),(245,240,232)); draw=ImageDraw.Draw(img)
    cols=[(150,80,210),(200,100,60),(60,120,200)]
    for ci,cx in enumerate([W//3,2*W//3]):
        c=cols[(idx+ci)%len(cols)]; cy=H//2-80
        draw.ellipse([cx-80,cy-190,cx+80,cy+30],fill=(255,220,185))
        draw.ellipse([cx-84,cy-240,cx+84,cy-80],fill=(40,28,12))
        draw.rounded_rectangle([cx-68,cy+25,cx+68,cy+230],radius=20,fill=c)
    out=f"{WORKDIR}/ai_{idx:03d}.jpg"; img.save(out,"JPEG",quality=88)
    return out

def make_variants(src, idx):
    orig=Image.open(src).convert("RGB"); w,h=orig.size; vs=[src]
    for zoom in [0.04,0.08]:
        dw=int(w*zoom/2); dh=int(h*zoom/2)
        cr=orig.crop([dw,dh,w-dw,h-dh]).resize((w,h),Image.LANCZOS)
        vp=f"{WORKDIR}/vz{idx:03d}_{int(zoom*100)}.jpg"; cr.save(vp,"JPEG",quality=93)
        vs.append(vp)
    return vs

def gen_pollinations(prompt, seed, out):
    full=f"masterpiece, best quality, kawaii chibi anime illustration, {prompt}, {STYLE} ### lowres, bad anatomy, text, watermark, nsfw, blurry"
    enc=urllib.parse.quote(full[:800])
    for attempt in range(3):
        try:
            url=(f"https://image.pollinations.ai/prompt/{enc}?width=576&height=1024"
                 f"&seed={seed+attempt}&nologo=true&model=flux&enhance=true")
            r=requests.get(url,timeout=90)
            if r.status_code==200 and 'image' in r.headers.get('content-type','') and len(r.content)>40000:
                with open(f"{WORKDIR}/raw_{seed}.jpg",'wb') as f: f.write(r.content)
                img=Image.open(f"{WORKDIR}/raw_{seed}.jpg").convert("RGB").resize((W,H),Image.LANCZOS)
                img.save(out,"JPEG",quality=95); return True
        except: pass
        if attempt<2: time.sleep(8)
    return False

# ── MAIN ──────────────────────────────────────────────────────
log(f"{'='*58}")
log(f"  ψ LONG 15MIN BANCO — VIDEO #{VIDEO_ID}")
log(f"  300 cenas × 3s | 100 imgs | Banco primeiro → Pollinations fallback")
log(f"  Anti-timeout: estimado ~12-18min (vs 60min anterior)")
log(f"{'='*58}\n")

# ETAPA 0: SCRIPT
log("📖 ETAPA 0 — Script...")
raw = sb_get_script()
segs = split_300(raw)
SCRIPT_TTS = ". ".join(segs)
log(f"  {len(segs)} segmentos | {len(SCRIPT_TTS)} chars")

# ETAPA 1: ÁUDIO
log(f"\n🎙️  ETAPA 1 — Áudio (AntonioNeural {RATE_ADJ})...")
async def gen_audio():
    import edge_tts
    c=edge_tts.Communicate(SCRIPT_TTS,voice="pt-BR-AntonioNeural",rate=RATE_ADJ)
    await c.save(f"{WORKDIR}/audio.mp3")
asyncio.run(gen_audio())
DUR=measure_dur(f"{WORKDIR}/audio.mp3")
RATE_REAL=len(SCRIPT_TTS)/DUR
log(f"  ✅ {DUR:.0f}s = {DUR/60:.2f}min | RATE={RATE_REAL:.2f}")
DURS=[max(0.2,round(len(s)/RATE_REAL,3)) for s in segs]

# ETAPA 2: IMAGENS (banco primeiro!)
log(f"\n🎨 ETAPA 2 — {N_UNIQUE} imagens (banco→Pollinations)...")
IMGS=[None]*N_UNIQUE; counts={"bank":0,"poll":0,"pillow":0}; t0=time.time()

for idx in range(N_UNIQUE):
    seg=segs[idx*3+1]  # segmento do meio do grupo
    char,scene=detect_char_scene(seg, idx/N_UNIQUE)
    out=f"{WORKDIR}/ai_{idx:03d}.jpg"

    # 1. Tentar banco de imagens
    bank_url=search_image_bank(char,scene)
    if bank_url and download_bank_image(bank_url,out):
        cap=seg[:25].split('.')[0].strip(); add_overlay(out,cap)
        log(f"  [{idx+1:03d}/{N_UNIQUE}] 🏦 banco | {char}/{scene} | {seg[:35]}...")
        counts["bank"]+=1
    else:
        # 2. Gerar via Pollinations
        from_chars = {"daniela":DANIELA,"sara":SARA,"marcos":MARCOS,"julia":JULIA,"ana":ANA}
        char_desc=from_chars.get(char,SARA)
        prompt=f"{char_desc} in {scene} scene, emotional expression matching narrative"
        if gen_pollinations(prompt, 5555+idx*43, out):
            cap=seg[:25].split('.')[0].strip(); add_overlay(out,cap)
            log(f"  [{idx+1:03d}/{N_UNIQUE}] 🌐 poll | {char}/{scene} | {seg[:35]}...")
            counts["poll"]+=1; time.sleep(4)
        else:
            out=gen_pillow(idx); cap=seg[:25].strip(); add_overlay(out,cap)
            counts["pillow"]+=1
            log(f"  [{idx+1:03d}/{N_UNIQUE}] ✏️  pillow | {seg[:35]}...")

    IMGS[idx]=out

gen_t=time.time()-t0
log(f"\n  ✅ {counts['bank']} banco | {counts['poll']} Pollinations | {counts['pillow']} Pillow | {gen_t/60:.1f}min")

# ETAPA 3: VARIANTES KEN BURNS
log(f"\n📝 ETAPA 3 — Ken Burns variants...")
VARIANTS=[]
for idx,src in enumerate(IMGS):
    if src: VARIANTS.append(make_variants(src,idx))
    else: VARIANTS.append([IMGS[0]]*3)

# ETAPA 4: FFCONCAT
concat=f"{WORKDIR}/concat.txt"
with open(concat,'w') as f:
    for si,(seg,dur) in enumerate(zip(segs,DURS)):
        ii=si//3; vi=si%3
        fp=VARIANTS[ii][vi] if ii<len(VARIANTS) else VARIANTS[-1][0]
        f.write(f"file '{fp}'\nduration {dur:.3f}\n")
    f.write(f"file '{VARIANTS[-1][0]}'\n")

# ETAPA 5: RENDER
ts=int(time.time()); OUT=f"{WORKDIR}/v{VIDEO_ID}_long_{ts}.mp4"
log(f"\n🎬 ETAPA 5 — Render {DUR:.0f}s...")
cmd=["ffmpeg","-y","-f","concat","-safe","0","-i",concat,
     "-i",f"{WORKDIR}/audio.mp3",
     "-c:v","libx264","-pix_fmt","yuv420p","-crf",str(CRF),
     "-c:a","aac","-b:a","128k","-shortest","-r",str(FPS),
     "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
     "-movflags","+faststart",OUT]
res=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
if res.returncode!=0: log(f"ERRO:\n{res.stderr[-500:]}"); sys.exit(1)
sz=os.path.getsize(OUT); dur2=measure_dur(OUT)
log(f"  ✅ {sz/1024/1024:.1f}MB | {dur2:.0f}s = {dur2/60:.2f}min")

# ETAPA 6: UPLOAD
log(f"\n☁️  ETAPA 6 — Upload...")
with open(OUT,'rb') as f: vdata=f.read()
video_url=None
for att in range(5):
    try:
        video_url=sb_upload(f"mp4s/v{VIDEO_ID}_long_{ts}.mp4",vdata,"video/mp4")
        log(f"  ✅ {video_url}"); break
    except Exception as e: log(f"  Att {att+1}: {e}"); time.sleep(15)

if video_url:
    sb_patch(VIDEO_ID,{"video_url":video_url,"status":"pending_credentials",
        "metadata":json.dumps({"version":"long_15min_bank_v1","dur_s":round(dur2,1),
            "n_unique":N_UNIQUE,"bank":counts["bank"],"poll":counts["poll"],
            "file_mb":round(sz/1024/1024,1),"img_interval_s":IMG_INT})})

log(f"\n{'='*58}")
log(f"  ψ RESULTADO: {dur2:.0f}s | {counts['bank']} banco | {counts['poll']} poll | {sz/1024/1024:.1f}MB")
log(f"{'='*58}\n")
