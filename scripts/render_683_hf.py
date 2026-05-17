#!/usr/bin/env python3
"""
render_683_hf.py — HUGGING FACE + GEMINI + POLLINATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ordem de geração de imagem (melhor → pior):
  1. HuggingFace FLUX.1-schnell (PRIMARY) ← novo
  2. HuggingFace animagine-xl (fallback HF)
  3. Gemini 2.5 Flash Image              ← fallback
  4. Pollinations Flux enhanced          ← fallback
  5. Pillow chibi pro                    ← último recurso
"""
import os, sys, json, subprocess, requests, time, urllib.parse, base64
from PIL import Image, ImageDraw
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

VIDEO_ID   = 683
SB_URL     = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY     = os.environ.get("SUPABASE_SERVICE_KEY","")
HF_TOKEN   = os.environ.get("HF_TOKEN","")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY","")
W, H       = 1080, 1920
CRF        = 22
WORKDIR    = "/tmp/v683_hf"
os.makedirs(WORKDIR, exist_ok=True)

VERM=(220,50,50); GOLD=(255,210,50); BRAN=(255,255,255); LILAS=(185,170,225)

def log(msg): print(msg, flush=True)

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
log(f"  ψ VÍDEO 1 — HuggingFace FLUX.1 PRIMARY")
log(f"  HF_TOKEN: {'✅ '+HF_TOKEN[:8]+'...' if HF_TOKEN else '❌ AUSENTE'}")
log(f"  GEMINI  : {'✅ '+GEMINI_KEY[:8]+'...' if GEMINI_KEY else '❌ AUSENTE'}")
log(f"  {len(SCRIPT)} chars | {N} cenas")
log(f"{'='*55}\n")

STYLE = ("Psych2Go kawaii chibi anime art style, original character design, "
         "soft cream background #F5F0E8, pastel colors, clean flat illustration, "
         "expressive big chibi eyes, no text, no watermarks, no logos, no real people, "
         "high quality professional animation")

DANIELA = "chibi anime girl, dark bob hair, mint-green blouse, gold psi pin, warm smile"
SARA    = "chibi anime girl, wavy auburn hair, round glasses, yellow cardigan, expressive eyes"
MARCOS  = "chibi anime man, styled dark hair, navy blazer, charming but calculating smile"
JULIA   = "chibi anime girl, curly dark hair, orange sweater, warm caring expression"
ANA     = "chibi anime woman, dark bun, white lab coat, clipboard, authoritative look"

SCENE_PROMPTS = [
    f"{SARA} alone at night holding phone anxiously, message bubbles waiting, blue glow, {STYLE}",
    f"{SARA} reading disappointing message on phone, sad drooping eyes, rain cloud above, {STYLE}",
    f"{SARA} meeting {MARCOS} at party, sparkles around him, she looks hopeful but uneasy, {STYLE}",
    f"{SARA} with question marks floating around her head, sensing something wrong, {STYLE}",
    f"{DANIELA} looking warmly and directly at viewer, hand extended in welcome, {STYLE}",
    f"{SARA} hunched with blame arrows pointing at her, {MARCOS} turned away dismissively, {STYLE}",
    f"{MARCOS} waving hand dismissively at {SARA}'s speech bubble, minimizing her feelings, {STYLE}",
    f"{ANA} holding clipboard with Harvard research data, {DANIELA} pointing at statistic, {STYLE}",
    f"{MARCOS} holding friendly mask hiding sinister shadow behind him, deceptive, {STYLE}",
    f"large badge number 1, {MARCOS} shrugging with innocent expression, no responsibility, {STYLE}",
    f"{SARA} touching temple, memory bubble above showing past argument, confused, {STYLE}",
    f"{MARCOS} pointing accusingly at shrinking smaller {SARA}, gaslighting, {STYLE}",
    f"{ANA} pointing at brain diagram showing manipulation effects, {SARA} realizing, {STYLE}",
    f"{DANIELA} holding golden shield glowing, protective warm light around {SARA}, {STYLE}",
    f"large badge number 2, {SARA} emotional speech bubble, {MARCOS} looking bored, {STYLE}",
    f"{SARA} crying with tears, {MARCOS} dramatically sighing, cold emotional gap, {STYLE}",
    f"{MARCOS} floating negative labels around {SARA}: anxious dramatic difficult, {STYLE}",
    f"{SARA} hands pressed together apologizing for her own feelings, sad and small, {STYLE}",
    f"{JULIA} looking worried watching {SARA}, protective hand near friend, concerned, {STYLE}",
    f"{JULIA} and {SARA} face to face, Julia speaking urgent truth, revelation, {STYLE}",
    f"mirror showing {SARA} original reflection fading, identity being erased slowly, {STYLE}",
    f"large badge number 3, {SARA} carrying heavy guilt weights, {MARCOS} relaxed, {STYLE}",
    f"{MARCOS} arriving late shrugging, {SARA} confused apologizing, clock showing late, {STYLE}",
    f"{SARA} with worried hands-to-face gesture, question mark floating toward her, lost, {STYLE}",
    f"{DANIELA} urgent warm expression facing viewer directly, glowing important badge, {STYLE}",
    f"{ANA} showing iceberg: tiny visible narcissism tip, massive hidden danger below, {STYLE}",
    f"{ANA} showing cycle diagram: love bomb devalue discard, {SARA} recognizing pattern, {STYLE}",
    f"{DANIELA} opening bright doorway to light, {SARA} stepping toward hope, {STYLE}",
    f"{DANIELA} sincere eye contact with viewer, hand on heart, golden warm light, {STYLE}",
    f"{SARA} {JULIA} {DANIELA} together arms around shoulders, strength in unity, {STYLE}",
    f"{MARCOS} hiding something in shadow behind back, {SARA} about to discover truth, {STYLE}",
    f"{SARA} with lightbulb moment, eyes wide with revelation, everything clicking, {STYLE}",
    f"giant golden notification bell with sparkles, all characters celebrating, confetti, {STYLE}",
]

# Captions
CAPTIONS = []
for p in PARAS:
    cap = p[:28].split('.')[0].split(',')[0].split('?')[0].strip()
    CAPTIONS.append(cap[:28])
if CAPTIONS: CAPTIONS[-1] = "INSCREVA-SE AGORA 🔔"

# ── GERAÇÃO HuggingFace ─────────────────────────────
def gen_hf(prompt, idx):
    """HuggingFace InferenceClient — FLUX.1-schnell via fal-ai (PRIMARY)."""
    if not HF_TOKEN:
        return None, "no_hf_token"
    try:
        from huggingface_hub import InferenceClient
        from io import BytesIO
        full_prompt = (
            f"masterpiece, best quality, kawaii chibi anime style, {prompt}, "
            "Psych2Go animation style, pastel colors, cream background, "
            "expressive big eyes, clean line art, no text, no watermark"
        )
        # Usar provider=auto (HF seleciona fal-ai, replicate, etc automaticamente)
        client = InferenceClient(api_key=HF_TOKEN)
        pil_img = client.text_to_image(
            prompt=full_prompt,
            model="black-forest-labs/FLUX.1-schnell",
            provider="auto",
        )
        if pil_img:
            img = pil_img.convert("RGB").resize((W, H), Image.LANCZOS)
            out = f"{WORKDIR}/ai_{idx:02d}.jpg"
            img.save(out, "JPEG", quality=96)
            return out, "hf/FLUX.1-schnell"
    except Exception as e:
        log(f"     [{idx+1}] HF err: {str(e)[:80]}")
    return None, "hf_failed"

def gen_gemini(prompt, idx):
    """Gemini 2.5 Flash Image — fallback."""
    if not GEMINI_KEY:
        return None, "no_gemini"
    models = ["gemini-2.5-flash-image-preview","gemini-3.1-flash-image-preview"]
    full = f"Create a kawaii chibi anime illustration: {prompt}"
    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
            r = requests.post(url, json={"contents":[{"parts":[{"text":full}]}],
                "generationConfig":{"responseModalities":["IMAGE","TEXT"]}}, timeout=120)
            if r.status_code == 200:
                for cand in r.json().get("candidates",[]):
                    for part in cand.get("content",{}).get("parts",[]):
                        if "inlineData" in part:
                            raw = base64.b64decode(part["inlineData"]["data"])
                            tmp = f"{WORKDIR}/raw_gem_{idx:02d}.jpg"
                            with open(tmp,'wb') as f: f.write(raw)
                            img = Image.open(tmp).convert("RGB").resize((W,H),Image.LANCZOS)
                            out = f"{WORKDIR}/ai_{idx:02d}.jpg"
                            img.save(out,"JPEG",quality=95)
                            return out, "gemini"
        except Exception as e:
            log(f"     [{idx+1}] Gemini err: {str(e)[:50]}")
    return None, "gemini_failed"

def gen_pollinations(prompt, idx):
    """Pollinations Flux — fallback."""
    try:
        enc = urllib.parse.quote(f"kawaii chibi anime, {prompt}, no text")
        url = (f"https://image.pollinations.ai/prompt/{enc}"
               f"?width=576&height=1024&seed={42+idx*31}&nologo=true"
               f"&model=flux&enhance=true")
        r = requests.get(url, timeout=90)
        if r.status_code == 200 and 'image' in r.headers.get('content-type',''):
            if len(r.content) > 50000:
                tmp = f"{WORKDIR}/raw_poll_{idx:02d}.jpg"
                with open(tmp,'wb') as f: f.write(r.content)
                img = Image.open(tmp).convert("RGB").resize((W,H),Image.LANCZOS)
                out = f"{WORKDIR}/ai_{idx:02d}.jpg"
                img.save(out,"JPEG",quality=95)
                return out, "pollinations"
    except: pass
    return None, "poll_failed"

def gen_pillow(idx):
    """Pillow chibi — último recurso."""
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
    return out, "pillow"

def add_overlay(img_path, caption):
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    DARK=(8,6,18)
    draw.rectangle([0,H-100,W,H],fill=DARK)
    draw.rectangle([0,H-100,6,H],fill=VERM)
    draw.rectangle([0,H-4,W,H],fill=VERM)
    draw.text((22,H-90),"ψ",fill=GOLD)
    draw.text((62,H-88),"Daniela Coelho",fill=BRAN)
    draw.text((62,H-58),"Saúde Mental  |  @psidanielacoelho",fill=LILAS)
    if caption and len(caption) > 2:
        cap=caption[:30].upper()
        bw=min(len(cap)*15+60,W-80); cx=W//2
        draw.rounded_rectangle([cx-bw//2,38,cx+bw//2,82],radius=18,fill=(250,248,255),outline=(210,200,235),width=2)
        draw.text((cx-bw//2+28,50),cap,fill=(20,15,45))
    img.save(img_path,"JPEG",quality=97)
    return img_path

# ── GERAR IMAGENS ────────────────────────────────────
log(f"🎨 Gerando {N} cenas — HF FLUX.1 → Gemini → Pollinations → Pillow...")
IMGS=[None]*N
counts={"hf":0,"gemini":0,"poll":0,"pillow":0}
t0=time.time()

def process(args):
    idx, prompt = args
    # 1. HuggingFace FLUX
    path, src = gen_hf(prompt, idx)
    if path is None:
        # 2. Gemini
        path, src = gen_gemini(prompt, idx)
    if path is None:
        # 3. Pollinations
        path, src = gen_pollinations(prompt, idx)
    if path is None:
        # 4. Pillow
        path, src = gen_pillow(idx)
    cap = CAPTIONS[idx] if idx < len(CAPTIONS) else ""
    add_overlay(path, cap)
    sz = os.path.getsize(path)//1024
    icon = "🌟" if "hf" in src else "💫" if "gemini" in src else "🌐" if "poll" in src else "✏️"
    log(f"  [{idx+1:02d}/{N}] {icon} {src} ({sz}KB)")
    return path, src

with ThreadPoolExecutor(max_workers=4) as ex:
    futures={ex.submit(process,(i,p)):i for i,p in enumerate(SCENE_PROMPTS)}
    for fut in as_completed(futures):
        i=futures[fut]; path,src=fut.result()
        IMGS[i]=path
        k="hf" if "hf" in src else "gemini" if "gemini" in src else "poll" if "poll" in src else "pillow"
        counts[k]=counts.get(k,0)+1
        time.sleep(0.3)

gen_t=time.time()-t0
log(f"\n  🌟{counts['hf']} HF | 💫{counts['gemini']} Gemini | 🌐{counts['poll']} Poll | ✏️{counts['pillow']} Pillow | {gen_t:.0f}s")

# ── ÁUDIO ────────────────────────────────────────────
log(f"\n🎙️  Baixando áudio V8 Final...")
r = requests.get("https://tpjvalzwkqwttvmszvie.supabase.co/storage/v1/object/public/videos/audios/v683_v8_1778892031.mp3",timeout=60)
with open(f"{WORKDIR}/audio.mp3",'wb') as f: f.write(r.content)
probe=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",f"{WORKDIR}/audio.mp3"],capture_output=True,text=True)
DUR=float(json.loads(probe.stdout)["format"]["duration"])
RATE=len(SCRIPT)/DUR
DURS=[max(0.5,round(len(p)/RATE,3)) for p in PARAS]
log(f"  {DUR:.1f}s | RATE={RATE:.3f}")

# ── FFCONCAT ─────────────────────────────────────────
concat=f"{WORKDIR}/concat.txt"
with open(concat,'w') as f:
    for i,dur in enumerate(DURS):
        img=IMGS[min(i,N-1)]
        if img: f.write(f"file '{img}'\nduration {dur:.3f}\n")
    if IMGS[-1]: f.write(f"file '{IMGS[-1]}'\n")

# ── RENDER ───────────────────────────────────────────
ts=int(time.time())
OUT=f"{WORKDIR}/v683_hf_{ts}.mp4"
log(f"\n🎬 Renderizando CRF={CRF}...")
cmd=["ffmpeg","-y","-f","concat","-safe","0","-i",concat,
     "-i",f"{WORKDIR}/audio.mp3",
     "-c:v","libx264","-pix_fmt","yuv420p","-crf",str(CRF),
     "-c:a","aac","-b:a","128k","-shortest","-r","25",
     "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
           "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
     "-movflags","+faststart",OUT]
res=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
if res.returncode!=0: log(f"ERRO:\n{res.stderr[-500:]}"); sys.exit(1)

sz=os.path.getsize(OUT)
dur2=float(json.loads(subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",OUT],capture_output=True,text=True).stdout)["format"]["duration"])
log(f"  ✅ {sz/1024/1024:.2f}MB | {dur2:.1f}s ({dur2/60:.1f}min)")

# ── UPLOAD ───────────────────────────────────────────
log(f"\n☁️  Upload Supabase...")
with open(OUT,'rb') as f: vdata=f.read()
video_url=None
for att in range(5):
    try:
        video_url=sb_upload(f"mp4s/v683_hf_{ts}.mp4",vdata,"video/mp4")
        log(f"  ✅ {video_url}"); break
    except Exception as e:
        log(f"  Tentativa {att+1}: {e}"); time.sleep(15)

if video_url:
    sb_patch(VIDEO_ID,{"video_url":video_url,"status":"pending_credentials",
        "metadata":json.dumps({"version":"hf_primary","hf":counts['hf'],
        "gemini":counts['gemini'],"poll":counts['poll'],"pillow":counts['pillow'],
        "file_mb":round(sz/1024/1024,2),"dur_s":round(dur2,1),"cenas":N})})

log(f"\n{'='*55}")
log(f"  ψ RESULTADO — HuggingFace PRIMARY")
log(f"  🌟{counts['hf']} HF | 💫{counts['gemini']} Gem | 🌐{counts['poll']} Poll | ✏️{counts['pillow']} Pillow")
log(f"  {sz/1024/1024:.2f}MB | {dur2/60:.1f}min")
log(f"  V8 Final era: 6.27MB | 62s")
log(f"  {'🏆 SUPEROU!' if sz/1024/1024 > 6.27 else '📈 Progresso!'}")
log(f"{'='*55}\n")
