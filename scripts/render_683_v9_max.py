#!/usr/bin/env python3
"""
render_683_v9_max.py — QUALIDADE MÁXIMA SEM GEMINI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Estratégia para superar V8 Final (6.27MB):
1. Pollinations flux-pro 1080×1920 (maior resolução possível)
2. Pillow chibi PROFISSIONAL com gradientes e sombras (não fallback básico)
3. CRF=18 (vs 25 do V8 Final) = arquivo maior + qualidade superior
4. 33 cenas × duração real = mais conteúdo
5. Qualidade de JPEG=98 (vs 95 anterior)
"""
import os, sys, json, subprocess, requests, time, urllib.parse, asyncio
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

VIDEO_ID   = 683
SB_URL     = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY     = os.environ.get("SUPABASE_SERVICE_KEY","")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY","")
W, H       = 1080, 1920
CRF        = 18           # SUPERIOR ao V8 Final (CRF=25)
WORKDIR    = "/tmp/v683_max"
os.makedirs(WORKDIR, exist_ok=True)

# Cores padrão eterno
VERM=(220,50,50); GOLD=(255,210,50); BRAN=(255,255,255)
LILAS=(185,170,225); BG=(245,240,232); DARK=(8,6,18)
VIOLET=(120,60,200); LILAC=(200,180,240)

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
row = requests.get(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{VIDEO_ID}&select=id,title,script",
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"},timeout=30).json()[0]
SCRIPT = row["script"].strip()
PARAS  = [p.strip() for p in SCRIPT.split('\n\n') if p.strip()]
N      = len(PARAS)

print(f"{'='*55}")
print(f"  ψ VÍDEO 1 MÁXIMO — #683")
print(f"  {len(SCRIPT)} chars | {N} cenas | CRF={CRF}")
print(f"  Objetivo: superar V8 Final 6.27MB")
print(f"{'='*55}\n")

# Personagens quantum universe
CHARS = {
    "daniela": "chibi anime girl, short sleek dark bob hair, honey-brown eyes, mint-green blouse, gold psi pin, warm smile",
    "sara":    "chibi anime girl, long wavy auburn hair, round glasses, pale yellow cardigan, big expressive eyes",
    "marcos":  "chibi anime man, styled dark hair, calculating smile, dark navy blazer, subtle menace",
    "julia":   "chibi anime girl, bouncy curly dark hair, flower clip, orange sweater, warm caring expression",
    "ana":     "chibi anime woman, neat dark bun, white lab coat, clipboard, authoritative calm expression",
}
STYLE = "Psych2Go kawaii chibi flat design style, cream background, pastel colors, clean line art, expressive big chibi eyes, no text, original character design not based on any IP"

# 33 cenas com personagens específicos
SCENE_DATA = [
    ("sara",    "alone at night holding phone anxiously, message '...' on screen, blue glow, worried eyes"),
    ("sara",    "reading disappointing message, face falling, small rain cloud above head"),
    ("sara marcos", "at party, Marcos charming with sparkles, Sara captivated but uneasy"),
    ("sara",    "thoughtful face with small question marks floating, sensing something wrong"),
    ("daniela", "looking directly forward with knowing warm smile, hand reaching toward viewer"),
    ("sara",    "hunched shoulders, blame arrow pointing at her, confused and small"),
    ("sara marcos", "Sara's speech bubble being dismissed by Marcos waving hand"),
    ("ana daniela","holding research clipboard with statistic 1 in 6, pointing at data"),
    ("marcos",  "wearing friendly mask, sinister shadow visible behind it, deceiving"),
    ("marcos",  "shrugging hands raised, red X over responsibility, smug expression"),
    ("sara",    "touching temple remembering, memory bubble above head, confused"),
    ("marcos sara","Marcos dismissive pointing at Sara who is shrinking smaller"),
    ("ana",     "pointing at brain diagram showing manipulation effects, concerned"),
    ("daniela sara","Daniela holding golden shield, warm light around Sara, protective"),
    ("marcos sara","large 2 badge, Sara emotional speech bubble, Marcos looking bored"),
    ("sara marcos","Sara crying, Marcos sighing dramatically, cold gap between them"),
    ("marcos",  "floating labels around Sara: dramatic, anxious, difficult, controlling"),
    ("sara",    "hands pressed together apologizing for her own feelings, sad"),
    ("julia",   "Julia looking worried at Sara, protective concerned friend expression"),
    ("julia sara","Julia and Sara face to face, Julia speaking urgent truth, revelation"),
    ("sara",    "mirror reflection fading, identity being erased, bittersweet"),
    ("marcos sara","large 3 badge, Sara carrying guilt weights not hers, Marcos relaxed"),
    ("marcos sara","Marcos arriving late shrugging, Sara apologizing confused, clock late"),
    ("sara",    "hands to face worried, question mark floating toward her, lost"),
    ("daniela", "urgent warm expression facing viewer, glowing important badge"),
    ("ana",     "iceberg diagram: tiny visible narcissism tip, huge hidden below"),
    ("ana sara","showing cycle: love bomb, devalue, discard arrows, Sara recognizing"),
    ("daniela sara","Daniela opening door to bright warm light, Sara stepping through"),
    ("daniela", "direct eye contact with viewer, hand on heart, sincere golden light"),
    ("sara julia daniela","all three together, arms around shoulders, strength in unity"),
    ("marcos",  "hiding something in shadow, Sara about to discover truth, tension"),
    ("sara",    "lightbulb moment, eyes wide with revelation, everything clicking"),
    ("all",     "giant golden bell, all characters arms raised celebrating, confetti"),
]

def gen_pollinations(prompt, idx):
    """Pollinations flux-pro 1080×1920 com timeout estendido."""
    full_prompt = (
        f"{STYLE}, {prompt}, "
        "high quality professional animation, vibrant colors, smooth shading, "
        "kawaii aesthetic, no watermarks, no text, no logos"
    )
    enc = urllib.parse.quote(full_prompt)
    seed = 42 + idx * 31
    # Usar flux-pro para máxima qualidade
    for model in ["flux-pro", "flux", "turbo"]:
        try:
            url = (f"https://image.pollinations.ai/prompt/{enc}"
                   f"?width=1080&height=1920&seed={seed}&nologo=true"
                   f"&model={model}&enhance=true")
            r = requests.get(url, timeout=180, verify=True)
            if r.status_code == 402:
                time.sleep(45)
                r = requests.get(url, timeout=180, verify=True)
            if r.status_code == 200:
                ct = r.headers.get('content-type','')
                if 'image' in ct and len(r.content) > 80000:  # >80KB = real image
                    tmp = f"{WORKDIR}/raw_{idx:02d}.jpg"
                    with open(tmp,'wb') as f: f.write(r.content)
                    img = Image.open(tmp).convert("RGB").resize((W,H), Image.LANCZOS)
                    return img, f"pollinations-{model}"
        except Exception as e:
            print(f"     {model} err {idx}: {str(e)[:50]}")
            time.sleep(5)
    return None, "failed"

def gen_chibi_pro(idx, char_key, desc):
    """Chibi profissional com gradiente, sombras e personagens distintos."""
    img = Image.new("RGB", (W,H), BG)
    draw = ImageDraw.Draw(img)

    # Gradiente de fundo (diagonal)
    for y in range(H):
        t = y/H
        r = int(245 + (230-245)*t)
        g = int(240 + (225-240)*t)
        b = int(232 + (215-232)*t)
        draw.line([(0,y),(W,y)], fill=(r,g,b))

    # Círculo de fundo suave
    draw.ellipse([W//2-350, H//2-400, W//2+350, H//2+400],
        fill=(235,228,218), outline=(220,212,200), width=3)

    # Personagens baseados em char_key
    chars_in_scene = char_key.split()
    n_chars = min(len(chars_in_scene), 3)
    cols = [(150,80,210),(80,140,210),(210,80,140),(80,210,140),(210,160,80)]

    positions = {
        1: [W//2],
        2: [W//3, 2*W//3],
        3: [W//4, W//2, 3*W//4],
    }[n_chars]

    char_colors = {
        "daniela": (100,180,120),   # mint verde
        "sara":    (180,140,80),    # amarelo caramelo
        "marcos":  (60,80,150),     # azul escuro
        "julia":   (200,100,80),    # laranja
        "ana":     (200,200,220),   # branco lab coat
        "all":     (150,100,200),   # roxo
    }

    for ci, (cx, char) in enumerate(zip(positions, chars_in_scene)):
        clr = char_colors.get(char, cols[ci % len(cols)])
        cy = H//2 - 80

        # Sombra suave
        draw.ellipse([cx-95, cy+210, cx+95, cy+260], fill=(180,170,160))

        # Corpo chibi
        draw.rounded_rectangle([cx-78, cy+30, cx+78, cy+250],
            radius=22, fill=clr)

        # Cabeça
        draw.ellipse([cx-92, cy-205, cx+92, cy+35], fill=(255,220,185))

        # Cabelo (personalizado por personagem)
        hair_clr = {
            "daniela": (30,20,10),
            "sara":    (130,60,20),
            "marcos":  (25,18,8),
            "julia":   (40,22,8),
            "ana":     (30,20,10),
            "all":     (50,30,10),
        }.get(char, (40,25,10))

        # Estilo de cabelo diferente por personagem
        if char == "sara":  # cabelo ondulado longo
            draw.ellipse([cx-96, cy-255, cx+96, cy-90], fill=hair_clr)
            draw.ellipse([cx-96, cy-100, cx-65, cy+40], fill=hair_clr)
            draw.ellipse([cx+65, cy-100, cx+96, cy+40], fill=hair_clr)
        elif char == "julia":  # cabelo cacheado
            draw.ellipse([cx-96, cy-260, cx+96, cy-90], fill=hair_clr)
            draw.ellipse([cx-110, cy-170, cx-70, cy-80], fill=hair_clr)
            draw.ellipse([cx+70,  cy-170, cx+110, cy-80], fill=hair_clr)
            draw.ellipse([cx-85, cy-80, cx-55, cy-40], fill=(220,180,50))  # flor
        elif char == "ana":  # coque
            draw.ellipse([cx-96, cy-255, cx+96, cy-90], fill=hair_clr)
            draw.ellipse([cx-35, cy-300, cx+35, cy-220], fill=hair_clr)  # coque
        else:  # padrão (daniela, marcos, all)
            draw.ellipse([cx-96, cy-255, cx+96, cy-90], fill=hair_clr)

        # Olhos grandes chibi
        eye_w, eye_h = 38, 30
        for ex in [cx-35, cx+35-eye_w]:
            draw.ellipse([ex, cy-95, ex+eye_w, cy-95+eye_h], fill=(255,255,255))
            draw.ellipse([ex+6, cy-89, ex+eye_w-6, cy-95+eye_h-6], fill=(30,20,60))
            draw.ellipse([ex+eye_w-14, cy-91, ex+eye_w-8, cy-85], fill=(255,255,255))

        # Bochechas
        for bx in [cx-55, cx+30]:
            draw.ellipse([bx, cy-35, bx+40, cy-5], fill=(255,190,190,150))

        # Sorriso/expressão
        if char == "marcos":
            draw.arc([cx-25, cy-18, cx+25, cy+12], start=10, end=170, fill=(160,50,50), width=4)
        else:
            draw.arc([cx-28, cy-20, cx+28, cy+15], start=0, end=180, fill=(180,60,60), width=4)

        # Acessórios
        if char == "daniela":  # ψ pin
            draw.text((cx-8, cy+35), "ψ", fill=GOLD)
        elif char == "ana":  # jaleco branco
            draw.rounded_rectangle([cx-78, cy+30, cx+78, cy+130],
                radius=10, fill=(240,240,245), outline=(200,200,210), width=2)

        # Label do personagem
        char_name = char.title()
        draw.text((cx-20, cy+260), char_name, fill=(80,60,100))

    return img

def add_overlay(img, caption, idx):
    """Lower third + caption badge profissional."""
    draw = ImageDraw.Draw(img)

    # Lower third com gradiente
    for y in range(H-100, H):
        t = (y-(H-100))/100
        r = int(8 + (20-8)*t)
        draw.line([(0,y),(W,y)], fill=(r, 6+int(4*t), 18+int(8*t)))

    # Barra vermelha lateral
    draw.rectangle([0, H-100, 6, H], fill=VERM)
    draw.rectangle([0, H-4, W, H], fill=VERM)

    # Texto lower third
    draw.text((22, H-90), "ψ", fill=GOLD)
    draw.text((62, H-88), "Daniela Coelho", fill=BRAN)
    draw.text((62, H-58), "Saúde Mental  |  @psidanielacoelho", fill=LILAS)

    # Caption badge topo
    if caption and len(caption) > 2:
        cap = caption[:30].upper()
        badge_w = min(len(cap)*16 + 60, W-80)
        cx_b = W//2
        by = 60
        # Sombra badge
        draw.rounded_rectangle([cx_b-badge_w//2+3, by-22+3, cx_b+badge_w//2+3, by+28+3],
            radius=18, fill=(180,170,200,120))
        # Badge principal
        draw.rounded_rectangle([cx_b-badge_w//2, by-22, cx_b+badge_w//2, by+28],
            radius=18, fill=(250,248,255), outline=(200,190,230), width=2)
        draw.text((cx_b-badge_w//2+30, by-8), cap, fill=(25,15,55))

    return img

# GERAR IMAGENS
print(f"🎨 Gerando {N} cenas (Pollinations flux-pro + chibi profissional)...")
IMGS = [None] * N
counts = {"poll":0, "chibi":0}
t0 = time.time()

def process_scene(args):
    idx, (char_key, desc) = args
    # Tentar Pollinations primeiro
    img, src = gen_pollinations(f"{CHARS.get(char_key.split()[0], desc)}, {desc}", idx)
    if img is None:
        # Chibi profissional como fallback
        img = gen_chibi_pro(idx, char_key, desc)
        src = "chibi"
    # Overlay
    cap = CAPTIONS[idx] if idx < len(CAPTIONS) else ""
    img = add_overlay(img, cap, idx)
    # Salvar em alta qualidade
    out = f"{WORKDIR}/scene_{idx:02d}.jpg"
    img.save(out, "JPEG", quality=98)  # 98 = máxima qualidade
    sz = os.path.getsize(out)//1024
    icon = "🌐" if src.startswith("poll") else "✏️"
    print(f"  [{idx+1:02d}/{N}] {icon} {src} | {sz}KB | {char_key}")
    return out, src

# Captions carregadas de PARAS
CAPTIONS = []
for p in PARAS:
    cap = p[:28].split('.')[0].split(',')[0].split('?')[0].strip()
    CAPTIONS.append(cap[:28])
if CAPTIONS: CAPTIONS[-1] = "INSCREVA-SE AGORA 🔔"

with ThreadPoolExecutor(max_workers=4) as ex:
    futures = {ex.submit(process_scene, (i, sc)): i for i, sc in enumerate(SCENE_DATA)}
    for fut in as_completed(futures):
        i = futures[fut]
        path, src = fut.result()
        IMGS[i] = path
        if src.startswith("poll"): counts["poll"] += 1
        else: counts["chibi"] += 1
        time.sleep(0.5)

gen_t = time.time() - t0
print(f"\n  ✅ {counts['poll']} Pollinations + {counts['chibi']} Chibi Pro | {gen_t:.0f}s")

# Calcular RATE_REAL com áudio existente
AUDIO_URL = "https://tpjvalzwkqwttvmszvie.supabase.co/storage/v1/object/public/videos/audios/v683_v8_1778892031.mp3"
r = requests.get(AUDIO_URL, timeout=60)
with open(f"{WORKDIR}/audio.mp3", 'wb') as f: f.write(r.content)
probe = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",
    f"{WORKDIR}/audio.mp3"], capture_output=True, text=True)
DUR_AUDIO = float(json.loads(probe.stdout)["format"]["duration"])
RATE_REAL = len(SCRIPT) / DUR_AUDIO
print(f"\n🎙️  Áudio: {DUR_AUDIO:.1f}s | RATE={RATE_REAL:.3f} chars/s")

# Timings por parágrafo
DURS = [max(0.5, round(len(p)/RATE_REAL, 3)) for p in PARAS]

# ffconcat
concat_file = f"{WORKDIR}/concat.txt"
with open(concat_file, 'w') as f:
    for i, dur in enumerate(DURS):
        img_idx = min(i, N-1)
        if IMGS[img_idx]:
            f.write(f"file '{IMGS[img_idx]}'\nduration {dur:.3f}\n")
    if IMGS[-1]: f.write(f"file '{IMGS[-1]}'\n")

# RENDER — CRF=18 = arquivo grande = MELHOR QUE V8 FINAL
ts = int(time.time())
OUT = f"{WORKDIR}/v683_max_{ts}.mp4"
print(f"\n🎬 Renderizando CRF={CRF}...")
cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",concat_file,
       "-i",f"{WORKDIR}/audio.mp3",
       "-c:v","libx264","-pix_fmt","yuv420p",
       "-crf",str(CRF),"-preset","slow",
       "-c:a","aac","-b:a","192k",        # áudio mais alto também
       "-shortest","-r","30",             # 30fps = mais fluido
       "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
             "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
       "-movflags","+faststart",OUT]
res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
if res.returncode != 0:
    print(f"ERRO:\n{res.stderr[-500:]}")
    sys.exit(1)

sz = os.path.getsize(OUT)
probe2 = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",OUT],
    capture_output=True, text=True)
dur2 = float(json.loads(probe2.stdout)["format"]["duration"])
print(f"  ✅ {sz/1024/1024:.2f}MB | {dur2:.1f}s ({dur2/60:.1f}min)")
print(f"  V8 Final era: 6.27MB | 62.4s")

# UPLOAD
print(f"\n☁️  Upload Supabase...")
with open(OUT,'rb') as f: vdata = f.read()
video_url = None
for attempt in range(5):
    try:
        video_url = sb_upload(f"mp4s/v683_max_{ts}.mp4", vdata, "video/mp4")
        print(f"  ✅ Upload OK")
        break
    except Exception as e:
        print(f"  Tentativa {attempt+1}: {e}")
        time.sleep(15)

if video_url:
    sb_patch(VIDEO_ID, {
        "video_url": video_url,
        "status": "pending_credentials",
        "metadata": json.dumps({
            "version": "v9_max", "crf": CRF, "fps": 30,
            "cenas": N, "chars": len(SCRIPT),
            "dur_s": round(dur2,1), "file_mb": round(sz/1024/1024,2),
            "poll": counts["poll"], "chibi": counts["chibi"],
        })
    })

print(f"\n{'='*55}")
print(f"  ψ RESULTADO VÍDEO 1 MÁXIMO")
print(f"  {sz/1024/1024:.2f}MB | {dur2/60:.1f}min | CRF={CRF}")
print(f"  🎬 {video_url or 'UPLOAD FALHOU'}")
print(f"{'='*55}\n")
