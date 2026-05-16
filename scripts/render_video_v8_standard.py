#!/usr/bin/env python3
"""
render_video_v8_standard.py — PADRÃO ETERNO psicologia.doc
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Baseado no V8 Final Gemini AI (v683_viral_v8_1778892031.mp4 — 6.3MB).
Este é o padrão definitivo para TODOS os vídeos, para sempre.

COMO FUNCIONA:
  1. Groq gera 20 prompts de cena + caption_pt + dur_chars (1 chamada)
  2. Gemini gera 20 imagens chibi AI em paralelo (4 workers)
  3. Pillow adiciona overlay em CADA imagem:
       - Caption badge no TOPO (frase-chave da cena, max 28 chars)
       - Lower third na BASE: psi | Daniela Coelho | Saude Mental | @psidanielacoelho
       - Barra vermelha embaixo
  4. Edge TTS AntonioNeural gera áudio
  5. RATE_REAL = len(script) / dur_audio (NUNCA hardcoded)
  6. Cada cena dura = dur_chars / RATE_REAL (preciso!)
  7. ffconcat monta o vídeo
  8. Upload Supabase + update DB

PADRÃO VISUAL (salvo em memória eterna):
  - Chibi kawaii psych2go style, fundo creme #F5F0E8
  - Lower third SEM Psicóloga até jan/2027
  - 20 cenas = 20 imagens Gemini únicas
  - Última cena SEMPRE: "INSCREVA-SE AGORA"
  - crf=25 = ~3-6MB | pt-BR-AntonioNeural | 25fps

$0/mês — funciona para 200+ vídeos/mês
"""
import os, sys, json, re, time, base64, asyncio, subprocess, requests
from PIL import Image, ImageDraw
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── CONFIG ────────────────────────────────────────────────────────
VIDEO_ID   = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("VIDEO_ID","683"))
SB_URL     = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY     = os.environ.get("SUPABASE_SERVICE_KEY","")
GROQ_KEY   = os.environ.get("GROQ_API_KEY","")
GEMINI_KEYS = [k for k in [
    os.environ.get("GEMINI_API_KEY",""),
    os.environ.get("GEMINI_API_KEY_2",""),
] if k]

W, H   = 1080, 1920
WORKDIR = f"/tmp/v8std_{VIDEO_ID}"
os.makedirs(WORKDIR, exist_ok=True)

# Cores do padrão eterno psicologia.doc
VERM = (220, 50, 50)       # vermelho da borda
GOLD = (255, 210, 50)      # dourado "psi"
BRAN = (255, 255, 255)     # branco
LILAS= (185, 170, 225)     # lilás subtítulo

# Modelos Gemini para imagem — gemini-2.0-flash-exp FUNCIONA sem permissão especial
GEMINI_MODELS = [
    "gemini-2.0-flash-exp",                   # ✅ FREE, funciona com key normal do AI Studio
    "gemini-2.0-flash-exp-image-generation",  # ✅ Alias explícito para imagem
    "gemini-2.5-flash-image",                 # Tenta (pode precisar de permissão especial)
]

_gkey_idx = [0]
def gemini_key():
    return GEMINI_KEYS[_gkey_idx[0] % len(GEMINI_KEYS)] if GEMINI_KEYS else None
def rotate_key():
    _gkey_idx[0] += 1

print(f"{'='*55}")
print(f"  ψ V8 STANDARD — Video #{VIDEO_ID}")
print(f"  Padrão eterno psicologia.doc @psidanielacoelho")
print(f"{'='*55}")

# ── SUPABASE ──────────────────────────────────────────────────────
def sb_get(table, qs):
    r = requests.get(f"{SB_URL}/rest/v1/{table}?{qs}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=30)
    r.raise_for_status(); return r.json()

def sb_patch(table, id_, data):
    r = requests.patch(f"{SB_URL}/rest/v1/{table}?id=eq.{id_}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"},
        json=data, timeout=30)
    r.raise_for_status()

def sb_upload(path, data, ctype):
    r = requests.post(f"{SB_URL}/storage/v1/object/videos/{path}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":ctype,"x-upsert":"true"},
        data=data, timeout=360)
    r.raise_for_status()
    return f"{SB_URL}/storage/v1/object/public/videos/{path}"

# ── CARREGAR DADOS ────────────────────────────────────────────────
rows = sb_get("content_pipeline",
    f"id=eq.{VIDEO_ID}&select=id,title,script,topic,audio_url")
if not rows: sys.exit(f"❌ Vídeo {VIDEO_ID} não encontrado")

video      = rows[0]
script_tts = video.get("script","").strip()
topic      = video.get("topic", video.get("title","psychology"))

print(f"\n📄 {video.get('title','')}")
print(f"   {len(script_tts)} chars | topic: {topic}")

if len(script_tts) < 50:
    sys.exit(f"Script curto demais ({len(script_tts)} chars)")

# ── GROQ: 20 PROMPTS CONTEXTUAIS ─────────────────────────────────
def gerar_prompts_groq():
    """
    Uma chamada Groq gera 20 prompts de cena:
    - frase_pt: trecho do roteiro desta cena
    - dur_chars: quantos chars esta cena representa (para timing preciso)
    - prompt: prompt inglês para Gemini gerar chibi
    - caption_pt: frase-chave curta para o badge no topo da imagem (max 25 chars)
    """
    if not GROQ_KEY:
        return gerar_prompts_fallback()

    system = """You are a creative director for a Brazilian psychology YouTube channel (@psidanielacoelho).
Generate exactly 20 image scene prompts for a chibi kawaii animation video.
Each prompt must be in English and describe ONE scene.

Rules for EVERY prompt:
- Style: "chibi anime flat design illustration, kawaii psychology animation, vertical 9:16 portrait, clean line art"  
- Background: "soft warm cream white background #F5F0E8 with subtle pastel decorations"
- NO text in image: "no text, no words, no letters, no logos"
- Copyright safe: "original character design not based on any existing IP or trademark, no text"
- Characters: Use "chibi anime girl with short dark hair and professional casual outfit" for the female host
- Make each scene visually reflect the specific phrase/emotion/concept
- Last scene MUST be subscribe CTA: golden bell, confetti, girl celebrating

Return ONLY a JSON array with exactly 20 objects:
[{"frase_pt":"phrase in portuguese","dur_chars":N,"prompt":"english gemini prompt","caption_pt":"SHORT PT max 25 chars"}]"""

    frases = re.split(r'(?<=[.!?])\s+|\n', script_tts.strip())
    frases = [f.strip() for f in frases if len(f.strip()) > 5]

    user_msg = f"""Script topic: {topic}
Script (PT-BR, {len(script_tts)} chars):
{script_tts}

Divide into exactly 20 scenes proportional to content length.
The dur_chars for each scene must sum approximately to {len(script_tts)}.
The last scene MUST end with subscribe CTA (Inscreva-se agora).
Return JSON array of 20 objects."""

    for attempt in range(3):
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
                json={"model":"llama-3.3-70b-versatile",
                      "messages":[{"role":"system","content":system},
                                   {"role":"user","content":user_msg}],
                      "temperature":0.7,"max_tokens":4000,
                      "response_format":{"type":"json_object"}},
                timeout=45)
            if r.status_code == 200:
                data = json.loads(r.json()["choices"][0]["message"]["content"])
                scenes = data if isinstance(data, list) else next(
                    (v for v in data.values() if isinstance(v, list)), None)
                if scenes:
                    while len(scenes) < 20: scenes.append(scenes[-1].copy())
                    scenes = scenes[:20]
                    scenes[-1]["caption_pt"] = "INSCREVA-SE AGORA 🔔"
                    print(f"   ✅ Groq gerou {len(scenes)} prompts")
                    return scenes
        except Exception as e:
            print(f"   Groq tentativa {attempt+1}: {e}")
            time.sleep(3)

    print("   ⚠️ Groq falhou → usando prompts fallback")
    return gerar_prompts_fallback()

def gerar_prompts_fallback():
    """20 prompts chibi psych2go para narcisismo/psicologia."""
    chars_por_cena = max(1, len(script_tts) // 20)
    STYLE = ("chibi anime flat design illustration, kawaii psychology animation, "
             "vertical 9:16, soft cream white background #F5F0E8, "
             "no text, no words, original character not based on any existing IP")
    GIRL  = "chibi anime girl short dark hair professional casual blouse warm smile"
    BOY   = "chibi anime boy dark hair navy shirt confident charming expression"

    prompts_base = [
        f"{GIRL} shocked surprised hands on cheeks large question mark floating, {STYLE}",
        f"three chibi characters one highlighted with subtle sinister glow, {STYLE}",
        f"large megaphone with big red X silence symbol whisper gesture, {STYLE}",
        f"{BOY} finger to lips shushing whisper speech bubbles secrets, {STYLE}",
        f"{GIRL} and {BOY} side by side subtle cracked heart between them, {STYLE}",
        f"{BOY} smug smile golden star sparkles perfect flawless, {STYLE}",
        f"{GIRL} dizzy confused spiral swirling stress lines around head, {STYLE}",
        f"large STOP hand gesture warning sign multiple chibi silhouettes, {STYLE}",
        f"red badge number 1 {GIRL} talking speech bubble completely empty erased, {STYLE}",
        f"{BOY} turned away arms crossed blame arrow toward sad {GIRL}, {STYLE}",
        f"orange badge number 2 golden trophy {BOY} claiming smugly sad {GIRL}, {STYLE}",
        f"purple badge number 3 {GIRL} exhausted heavy weights pressing down, {STYLE}",
        f"professional chibi woman white lab coat brain diagram energy draining, {STYLE}",
        f"large bold green checkmark {GIRL} raising fist empowerment liberation, {STYLE}",
        f"large red heart thick black X broken heart pieces scattered, {STYLE}",
        f"{BOY} holding smiling theater mask sinister shadow behind friendly mask, {STYLE}",
        f"chibi hands holding glowing smartphone share arrow send motion, {STYLE}",
        f"{GIRL} joyful arms wide open floating pink hearts flower petals, {STYLE}",
        f"chibi girl warm loving eye symbol ear symbol golden protective light, {STYLE}",
        f"giant golden bell musical notes rainbow confetti {GIRL} arms raised subscribe, {STYLE}",
    ]

    captions = [
        "Você reconheceria?", "O que é narcisismo?", "Sinal invisível",
        "Ele sussurra...", "Parecia perfeito", "Nunca erra?",
        "Por que você se perde?", "Cuidado!", "Sinal 1: Suas palavras",
        "Ele te culpa", "Sinal 2: Conquistas dele", "Sinal 3: Você se cansa",
        "A ciência explica", "Você merece mais", "Isso não é amor",
        "A máscara gentil", "Compartilha com alguém", "Você merece amor real",
        "Te vê. Te ouve.", "INSCREVA-SE AGORA 🔔"
    ]

    return [{"frase_pt": f"Cena {i+1}", "dur_chars": chars_por_cena,
             "prompt": prompts_base[i], "caption_pt": captions[i]}
            for i in range(20)]

print(f"\n🧠 Groq: gerando 20 prompts de cena...")
SCENES = gerar_prompts_groq()

# ── GEMINI: GERAR IMAGENS AI ──────────────────────────────────────
def gen_gemini_image(prompt, idx):
    """
    Gera imagem chibi com Gemini.
    Usa gemini-2.0-flash-exp (funciona sem permissão especial).
    Recorta para 9:16 e salva como JPEG 92.
    """
    key = gemini_key()
    if not key: return None

    full_prompt = (
        "Psych2Go animation style, kawaii chibi anime character, "
        "cream white background #F5F0E8, pastel warm colors, "
        f"round big expressive eyes, clean soft lines. {prompt}. "
        "Original character design not based on any existing IP, "
        "no text, no logos, no watermarks, no brand marks."
    )

    for model in GEMINI_MODELS:
        url = (f"https://generativelanguage.googleapis.com/v1beta"
               f"/models/{model}:generateContent?key={key}")
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE","TEXT"]}
        }
        try:
            r = requests.post(url, json=payload, timeout=90)
            if r.status_code == 429:
                rotate_key(); time.sleep(5); continue
            if r.status_code == 200:
                for cand in r.json().get("candidates",[]):
                    for part in cand.get("content",{}).get("parts",[]):
                        if "inlineData" in part:
                            raw = base64.b64decode(part["inlineData"]["data"])
                            tmp = f"{WORKDIR}/raw_{idx:02d}.jpg"
                            with open(tmp,"wb") as f: f.write(raw)
                            # Recortar para 9:16 e redimensionar para 1080×1920
                            img = Image.open(tmp).convert("RGB")
                            aw, ah = img.size
                            target = 9/16
                            if aw/ah > target:  # muito largo → cortar lados
                                nw = int(ah * target)
                                img = img.crop(((aw-nw)//2, 0, (aw+nw)//2, ah))
                            elif aw/ah < target:  # muito alto → cortar topo/base
                                nh = int(aw / target)
                                img = img.crop((0, (ah-nh)//2, aw, (ah+nh)//2))
                            img = img.resize((W, H), Image.LANCZOS)
                            out = f"{WORKDIR}/ai_{idx:02d}.jpg"
                            img.save(out, "JPEG", quality=92)
                            return out
        except Exception:
            continue
    return None

# ── PILLOW FALLBACK ───────────────────────────────────────────────
def pillow_fallback(idx, caption):
    """Chibi psych2go fallback em Pillow se Gemini falhar."""
    # Fundo creme com gradiente suave (padrão psych2go)
    img = Image.new("RGB", (W, H), (245, 240, 232))  # #F5F0E8
    draw = ImageDraw.Draw(img)
    # Gradiente sutil
    for y in range(H):
        t = y/H
        r_val = int(245 + (235-245)*t)
        g_val = int(240 + (228-240)*t)
        b_val = int(232 + (220-232)*t)
        draw.line([(0,y),(W,y)], fill=(r_val, g_val, b_val))
    # Personagem chibi simplificado no centro
    cx, cy = W//2, H//2
    # Cabeça
    draw.ellipse([cx-120, cy-220, cx+120, cy+40], fill=(255, 220, 180))
    # Cabelo escuro
    draw.ellipse([cx-125, cy-270, cx+125, cy-100], fill=(60, 40, 20))
    # Olhos
    draw.ellipse([cx-60, cy-100, cx-20, cy-60], fill=(30, 20, 10))
    draw.ellipse([cx+20, cy-100, cx+60, cy-60], fill=(30, 20, 10))
    # Brilho olhos
    draw.ellipse([cx-55, cy-95, cx-45, cy-85], fill=(255,255,255))
    draw.ellipse([cx+25, cy-95, cx+35, cy-85], fill=(255,255,255))
    # Boca sorrisão
    draw.arc([cx-40, cy-30, cx+40, cy+20], start=0, end=180, fill=(200,80,80), width=5)
    # Corpo
    draw.rounded_rectangle([cx-100, cy+40, cx+100, cy+300], radius=20, fill=(150, 100, 200))
    # Braços
    draw.ellipse([cx-180, cy+60, cx-80, cy+180], fill=(150, 100, 200))
    draw.ellipse([cx+80, cy+60, cx+180, cy+180], fill=(150, 100, 200))
    # Bochecha rosa
    draw.ellipse([cx-110, cy-60, cx-60, cy-20], fill=(255, 180, 180))
    draw.ellipse([cx+60, cy-60, cx+110, cy-20], fill=(255, 180, 180))
    out = f"{WORKDIR}/fb_{idx:02d}.jpg"
    img.save(out, "JPEG", quality=85)
    return out

# ── PILLOW OVERLAY (PADRÃO ETERNO) ───────────────────────────────
def add_overlay(img_path, caption_pt):
    """
    Adiciona overlays PADRÃO ETERNO em cada imagem:
    
    TOPO: Badge com caption_pt (frase-chave da cena, max 28 chars)
           → fundo branco com borda sutil, texto escuro
    
    BASE: Lower third com:
           → fundo escuro #08060E
           → barra vermelha lateral esquerda
           → "psi" em dourado
           → "Daniela Coelho" em branco
           → "Saude Mental  |  @psidanielacoelho" em lilás
           → barra vermelha embaixo (4px)
    
    SEM Psicóloga no lower third até jan/2027.
    """
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── LOWER THIRD (base) ──────────────────────────────────────
    lt_h = 95
    draw.rectangle([0, H-lt_h, W, H], fill=(8, 6, 18))        # fundo escuro
    draw.rectangle([0, H-lt_h, 5, H], fill=VERM)               # barra vermelha lateral
    draw.text((22, H-lt_h+12), "psi", fill=GOLD)               # logo "psi" dourado
    draw.text((62, H-lt_h+10), "Daniela Coelho", fill=BRAN)    # nome em branco
    draw.text((62, H-lt_h+40),                                  # subtítulo SEM Psicóloga
              "Saude Mental  |  @psidanielacoelho", fill=LILAS)
    draw.rectangle([0, H-4, W, H], fill=VERM)                  # borda vermelha final

    # ── CAPTION BADGE (topo) ────────────────────────────────────
    if caption_pt:
        cap = caption_pt[:28].upper()
        # Estimativa de largura do texto
        cap_w = min(len(cap) * 14 + 44, W - 60)
        cx = W // 2
        cap_y = 56
        # Badge branco arredondado
        draw.rounded_rectangle(
            [cx-cap_w//2, cap_y-24, cx+cap_w//2, cap_y+24],
            radius=15, fill=(245, 245, 255))
        # Borda sutil
        draw.rounded_rectangle(
            [cx-cap_w//2, cap_y-24, cx+cap_w//2, cap_y+24],
            radius=15, outline=(200, 200, 220), width=2)
        # Texto escuro
        draw.text((cx-cap_w//2+22, cap_y-10), cap, fill=(20, 15, 45))

    img.save(img_path, "JPEG", quality=95)
    return img_path

# ── GERAR CENAS (4 workers paralelo) ─────────────────────────────
def generate_scene(args):
    i, scene = args
    prompt   = scene.get("prompt","")
    caption  = scene.get("caption_pt","")
    print(f"   [{i+1:02d}/20] Gemini...")
    path = gen_gemini_image(prompt, i)
    if path:
        add_overlay(path, caption)
        sz = os.path.getsize(path)//1024
        print(f"   [{i+1:02d}/20] ✅ Gemini AI ({sz}KB)")
        return path, True
    else:
        fb = pillow_fallback(i, caption)
        add_overlay(fb, caption)
        print(f"   [{i+1:02d}/20] ⚠️  Fallback chibi")
        return fb, False

print(f"\n🎨 Gerando 20 imagens chibi (4 workers paralelo)...")
t0 = time.time()
imgs  = [None]*20
n_ai  = 0
n_fb  = 0

with ThreadPoolExecutor(max_workers=4) as ex:
    futures = {ex.submit(generate_scene, (i, s)): i
               for i, s in enumerate(SCENES)}
    for fut in as_completed(futures):
        i = futures[fut]
        path, is_ai = fut.result()
        imgs[i] = path
        if is_ai: n_ai += 1
        else: n_fb += 1

gen_t = time.time() - t0
print(f"\n   ✅ {n_ai}/20 Gemini AI | {n_fb} fallback | {gen_t:.1f}s")

# ── EDGE TTS: ÁUDIO ───────────────────────────────────────────────
print(f"\n🎙️  Edge TTS pt-BR-AntonioNeural...")

async def _tts():
    import edge_tts
    c = edge_tts.Communicate(script_tts, voice="pt-BR-AntonioNeural")
    await c.save(f"{WORKDIR}/audio.mp3")

# Usar áudio existente se disponível (economiza tempo)
if video.get("audio_url"):
    print(f"   Usando áudio existente do DB...")
    ar = requests.get(video["audio_url"], timeout=60)
    ar.raise_for_status()
    with open(f"{WORKDIR}/audio.mp3","wb") as f: f.write(ar.content)
else:
    asyncio.run(_tts())

probe = subprocess.run(
    ["ffprobe","-v","quiet","-print_format","json","-show_format",
     f"{WORKDIR}/audio.mp3"],
    capture_output=True, text=True)
DUR_AUDIO = float(json.loads(probe.stdout)["format"]["duration"])

# RATE_REAL: NUNCA hardcoded — calculado do áudio real
RATE_REAL = len(script_tts) / DUR_AUDIO
print(f"   {DUR_AUDIO:.1f}s | RATE_REAL={RATE_REAL:.3f} chars/s")

# ── TIMING DINÂMICO ───────────────────────────────────────────────
# Cada cena dura proporcional ao número de chars que representa
durs = []
for scene in SCENES:
    chars = scene.get("dur_chars", len(script_tts)//20)
    dur   = max(0.5, round(chars / RATE_REAL, 3))
    durs.append(dur)

soma = sum(durs)
print(f"   Soma cenas: {soma:.1f}s | Gap: {DUR_AUDIO-soma:.1f}s")

# ── FFCONCAT ─────────────────────────────────────────────────────
concat_file = f"{WORKDIR}/concat.txt"
with open(concat_file,"w") as f:
    for img, dur in zip(imgs, durs):
        if img:
            f.write(f"file '{img}'\nduration {dur:.3f}\n")
    if imgs[-1]:
        f.write(f"file '{imgs[-1]}'\n")  # última imagem sem duração

# ── RENDER FFMPEG ─────────────────────────────────────────────────
print(f"\n🎬 Renderizando (crf=25, ~3-6MB)...")
ts      = int(time.time())
out_mp4 = f"{WORKDIR}/v{VIDEO_ID}_v8std_{ts}.mp4"

cmd = [
    "ffmpeg","-y",
    "-f","concat","-safe","0","-i",concat_file,
    "-i",f"{WORKDIR}/audio.mp3",
    "-c:v","libx264","-pix_fmt","yuv420p",
    "-c:a","aac","-b:a","128k",
    "-shortest","-r","25","-crf","25",
    "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
          "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
    "-movflags","+faststart",
    out_mp4
]
res = subprocess.run(cmd, capture_output=True, text=True, timeout=480)
if res.returncode != 0:
    print(f"ERRO FFMPEG:\n{res.stderr[-2000:]}")
    sys.exit(1)

sz    = os.path.getsize(out_mp4)
probe2 = subprocess.run(
    ["ffprobe","-v","quiet","-print_format","json","-show_format", out_mp4],
    capture_output=True, text=True)
dur2  = float(json.loads(probe2.stdout)["format"]["duration"])
print(f"   ✅ {sz//1024}KB | {dur2:.1f}s")

# ── UPLOAD SUPABASE ───────────────────────────────────────────────
print(f"\n☁️  Upload Supabase Storage...")

# Áudio (se foi gerado agora)
if not video.get("audio_url"):
    with open(f"{WORKDIR}/audio.mp3","rb") as f: adata = f.read()
    audio_url = sb_upload(f"audios/v{VIDEO_ID}_v8std_{ts}.mp3", adata, "audio/mpeg")
    sb_patch("content_pipeline", VIDEO_ID, {"audio_url": audio_url})

# Vídeo
with open(out_mp4,"rb") as f: vdata = f.read()
mp4_fname = f"mp4s/v{VIDEO_ID}_v8std_{ts}.mp4"
video_url = None
for attempt in range(5):
    try:
        video_url = sb_upload(mp4_fname, vdata, "video/mp4")
        print(f"   ✅ Upload OK")
        break
    except Exception as e:
        print(f"   Tentativa {attempt+1}: {e}")
        time.sleep(6)

# ── UPDATE DB ─────────────────────────────────────────────────────
if video_url:
    sb_patch("content_pipeline", VIDEO_ID, {
        "video_url": video_url,
        "status": "pending_credentials",
        "metadata": json.dumps({
            "render_version": "v8_standard",
            "n_ai_scenes": n_ai,
            "n_fallback_scenes": n_fb,
            "audio_dur_s": round(DUR_AUDIO, 1),
            "video_dur_s": round(dur2, 1),
            "file_kb": sz//1024,
            "rate_real": round(RATE_REAL, 3),
            "gen_time_s": round(gen_t, 1),
            "lower_third": "Daniela Coelho | Saude Mental | @psidanielacoelho",
            "gemini_model": "gemini-2.0-flash-exp",
        })
    })

print(f"\n{'='*55}")
print(f"  ✅ V8 STANDARD — #{VIDEO_ID}")
print(f"  🎬 {video_url}")
print(f"  {n_ai}/20 Gemini AI | {sz//1024}KB | {dur2:.1f}s")
print(f"{'='*55}\n")
