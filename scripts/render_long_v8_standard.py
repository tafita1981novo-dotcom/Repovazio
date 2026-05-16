#!/usr/bin/env python3
"""
render_long_v8_standard.py — LONGS | PADRÃO ETERNO psicologia.doc
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UNIVERSO DE 15 PERSONAGENS PERSISTENTE (todos os 200+ vídeos):
  Daniela (host), Lucas, Sara, Dra. Ana, Marcos, Julia, Pedro,
  Clara, Renata, Gui, Maya, Theo, Bia, Rafa, Vó

N_IMGS DINÂMICO — sem limite fixo:
  N_IMGS = max(20, min(int(DUR_AUDIO / 15), 200))
  → 3min = 12  → usa 20 mín
  → 10min = 40 imagens
  → 20min = 80 imagens
  → 45min = 180 imagens
  → sem teto artificial

PALAVRA A PALAVRA:
  ~41 chars por segmento = ~3s/imagem (igual Short #683)
  Caption muda a cada segmento
  Imagens ciclam pelo pool (i // 5) % N_IMGS
"""
import os, sys, json, re, time, base64, asyncio, subprocess, requests, urllib.parse
from PIL import Image, ImageDraw
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── CONFIG ────────────────────────────────────────────────────────
VIDEO_ID    = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("VIDEO_ID","693"))
SB_URL      = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY      = os.environ.get("SUPABASE_SERVICE_KEY","")
GROQ_KEY    = os.environ.get("GROQ_API_KEY","")
GEMINI_KEYS = [k for k in [
    os.environ.get("GEMINI_API_KEY",""),
    os.environ.get("GEMINI_API_KEY_2",""),
] if k]

W, H         = 1080, 1920
CHARS_PER_SEG = 41       # ~3s por segmento (idêntico ao Short #683)
SEGS_PER_IMG  = 5        # quantos segmentos por imagem antes de trocar
CRF          = 22        # qualidade Long
WORKERS      = 6         # workers paralelo

WORKDIR = f"/tmp/vlong_{VIDEO_ID}"
os.makedirs(WORKDIR, exist_ok=True)

# Cores padrão eterno
VERM  = (220,  50,  50)
GOLD  = (255, 210,  50)
BRAN  = (255, 255, 255)
LILAS = (185, 170, 225)

GEMINI_MODELS = ["gemini-2.0-flash-exp","gemini-2.0-flash-exp-image-generation"]

_gkey_idx = [0]
def gemini_key():
    return GEMINI_KEYS[_gkey_idx[0] % len(GEMINI_KEYS)] if GEMINI_KEYS else None
def rotate_key():
    _gkey_idx[0] += 1

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
        data=data, timeout=600)
    r.raise_for_status()
    return f"{SB_URL}/storage/v1/object/public/videos/{path}"

# ── CARREGAR DADOS ────────────────────────────────────────────────
rows = sb_get("content_pipeline",
    f"id=eq.{VIDEO_ID}&select=id,title,script,topic,audio_url")
if not rows: sys.exit(f"❌ Vídeo {VIDEO_ID} não encontrado")

video      = rows[0]
script_tts = video.get("script","").strip()
topic      = video.get("topic", video.get("title","psychology")).lower()

# ── CARREGAR UNIVERSO DE PERSONAGENS DO SUPABASE ──────────────────
def load_characters(topic_hint=""):
    """Carrega os personagens relevantes para este tópico do DB."""
    chars = sb_get("character_universe",
        "select=slug,name,role,visual,personality,topics&order=id.asc")
    # Filtrar relevantes ao tópico + sempre incluir Daniela e Dra. Ana
    must_include = {"daniela", "ana"}
    relevant = []
    for c in chars:
        if c["slug"] in must_include:
            relevant.append(c)
        elif any(t in topic_hint for t in c.get("topics", [])) or "todos" in c.get("topics", []):
            relevant.append(c)
    # Se poucos, completar com os primeiros
    if len(relevant) < 5:
        slugs_added = {c["slug"] for c in relevant}
        for c in chars:
            if c["slug"] not in slugs_added:
                relevant.append(c)
                if len(relevant) >= 8: break
    return relevant[:12]  # máx 12 personagens por vídeo

CHARACTERS = load_characters(topic)
char_slugs = [c["slug"] for c in CHARACTERS]
print(f"\n📄 {video.get('title','')}")
print(f"   {len(script_tts)} chars | topic: {topic}")
print(f"   Personagens: {', '.join(char_slugs)}")

# Atualizar aparências no DB
for c in CHARACTERS:
    try:
        requests.patch(f"{SB_URL}/rest/v1/character_universe?slug=eq.{c['slug']}",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                     "Content-Type":"application/json","Prefer":"return=minimal"},
            json={"appearances": c.get("appearances",0) + 1}, timeout=10)
    except Exception: pass

# ── CALCULAR N_IMGS DINÂMICO ──────────────────────────────────────
# Baseado na duração do áudio — sem limite fixo
# Para calcular, precisamos estimar a duração antes do áudio
# Estimativa: ~14.5 chars/s (AntonioNeural médio)
DUR_ESTIMATE = len(script_tts) / 14.5
N_IMGS = max(20, min(int(DUR_ESTIMATE / 15), 200))
n_segs = max(N_IMGS, round(len(script_tts) / CHARS_PER_SEG))

print(f"\n🎨 N_IMGS DINÂMICO:")
print(f"   Duração estimada: {DUR_ESTIMATE:.0f}s ({DUR_ESTIMATE/60:.1f}min)")
print(f"   N_IMGS = {N_IMGS} (sem limite fixo, calculado por duração)")
print(f"   N_SEGS = {n_segs} (~3s/segmento, palavra a palavra)")
print(f"   Imagens únicas: {N_IMGS} | Cycling a cada {SEGS_PER_IMG} segmentos")

# Texto de personagens para o Groq
def build_char_guide():
    lines = []
    for c in CHARACTERS:
        lines.append(f"- {c['name'].upper()} ({c['role']}): {c['visual']}")
        lines.append(f"  Personality: {c['personality']}")
    return "\n".join(lines)

CHAR_GUIDE = build_char_guide()

# ── GROQ: N_IMGS PROMPTS + N_SEGS CAPTIONS ───────────────────────
def gerar_prompts_groq():
    if not GROQ_KEY:
        return gerar_fallback()

    # Secções do script para contexto emocional
    sec = max(1, len(script_tts) // 6)
    sections = [script_tts[i*sec:(i+1)*sec][:250] for i in range(6)]

    system = f"""You are a world-class animation director for @psidanielacoelho, a Brazilian psychology YouTube channel.

PERSISTENT UNIVERSE — These exact characters appear across ALL 200+ videos of this channel.
ALWAYS use their specific visual descriptions to maintain consistency:

{CHAR_GUIDE}

Generate exactly {N_IMGS} unique chibi scene prompts for this video.
Each prompt MUST:
1. Feature 2-3 named characters from the universe ABOVE (use their exact visual descriptions)
2. Show them PHYSICALLY INTERACTING: touching shoulders, eye contact, pointing, comforting, back-to-back, confronting, one hiding from other, sharing objects
3. Show a CLEAR EMOTIONAL REACTION matching the script moment
4. Include ONE meaningful prop that tells the story (floating heart, broken glass, puppet strings, brain diagram, shield, etc.)
5. End with: "cream warm background #F5F0E8, no text, no logos, original design, not based on any existing IP"

Also generate {n_segs} short PT-BR captions (max 25 chars each) for each speech segment.
Last caption: "INSCREVA-SE AGORA 🔔"

Return ONLY valid JSON (no markdown, no preamble):
{{
  "image_prompts": ["full detailed interaction prompt 1", ... (exactly {N_IMGS})],
  "captions": ["caption PT 1", ... (exactly {n_segs})]
}}"""

    user_msg = f"""Topic: {topic}
Script: {len(script_tts)} chars, {n_segs} speech segments

Script sections:
Abertura: {sections[0]}
Desenvolvimento: {sections[1]}
Aprofundamento: {sections[2]}
Virada: {sections[3]}
Solução: {sections[4]}
Fechamento: {sections[5]}

Generate {N_IMGS} interaction prompts using the PERSISTENT UNIVERSE characters.
Generate {n_segs} PT-BR captions.
Each prompt must use at least 2 named characters from the universe with their EXACT visual descriptions."""

    for attempt in range(4):
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
                json={"model":"llama-3.3-70b-versatile",
                      "messages":[{"role":"system","content":system},
                                   {"role":"user","content":user_msg}],
                      "temperature":0.85,"max_tokens":8000},
                timeout=120)
            if r.status_code == 200:
                text = r.json()["choices"][0]["message"]["content"]
                match = re.search(r'\{[\s\S]*\}', text)
                if match:
                    data = json.loads(match.group())
                    prompts  = data.get("image_prompts",[])
                    captions = data.get("captions",[])
                    # Garantir tamanhos corretos
                    while len(prompts) < N_IMGS: prompts.append(prompts[-1] if prompts else "chibi psychology scene")
                    while len(captions) < n_segs: captions.append(captions[len(captions)%max(1,len(captions))] if captions else "...")
                    prompts  = prompts[:N_IMGS]
                    captions = captions[:n_segs]
                    captions[-1] = "INSCREVA-SE AGORA 🔔"
                    print(f"   ✅ Groq: {len(prompts)} prompts + {len(captions)} captions")
                    return prompts, captions
        except Exception as e:
            print(f"   Groq tentativa {attempt+1}: {e}")
            time.sleep(8)

    return gerar_fallback()

def gerar_fallback():
    """Fallback com personagens do universo embutidos."""
    STYLE = "cream background #F5F0E8, no text, original design, not based on any IP"
    prompts = []
    # Usa os personagens carregados do DB para os prompts fallback
    chars_visual = {c["slug"]: c["visual"] for c in CHARACTERS}
    d  = chars_visual.get("daniela","chibi girl mint blouse dark bob")
    l  = chars_visual.get("lucas","chibi boy navy hoodie dark hair")
    s  = chars_visual.get("sara","chibi girl auburn wavy hair glasses")
    a  = chars_visual.get("ana","chibi woman white lab coat neat bun")
    m  = chars_visual.get("marcos","chibi man charming dark suit")
    j  = chars_visual.get("julia","chibi girl curly hair orange sweater")
    gu = chars_visual.get("gui","chibi man wavy light brown hair plaid")

    scene_templates = [
        f"{d} and {l} facing each other shocked, large question mark floating between them, {STYLE}",
        f"{d} pointing toward viewer direct eye contact, speech bubble with ellipsis, {STYLE}",
        f"{l} hiding behind hands {s} reaching out concern, shadow figure behind him, {STYLE}",
        f"{m} puppet strings above head invisible to him, {d} noticing horrified, {STYLE}",
        f"{s} and {d} sitting close whispering secrets wide eyes, tea cups beside them, {STYLE}",
        f"cracked heart floating center {l} on left turned away {s} on right sad, {STYLE}",
        f"{s} looking in mirror reflection shows sadder version, {d} watching concerned, {STYLE}",
        f"{a} and {d} side by side {a} pointing at brain diagram both serious, {STYLE}",
        f"{l} speech bubble empty being erased, {s} frustrated hands raised, {STYLE}",
        f"invisible glass wall between {m} and {s} both pressing hands against it, {STYLE}",
        f"{a} showing iceberg diagram {l} shocked seeing what's below surface, {STYLE}",
        f"{j} and {s} back to back strong poses fists raised empowerment, {STYLE}",
        f"{s} cutting invisible puppet strings {d} cheering beside her confetti, {STYLE}",
        f"{d} drawing boundary line {s} standing confident on safe side, {STYLE}",
        f"shield heart shape {d} handing to {s} who holds it up strong glowing, {STYLE}",
        f"{l} and {gu} face to face emotional conversation tears and understanding, {STYLE}",
        f"{a} {d} {s} three together arms around shoulders community warmth, {STYLE}",
        f"plant growing dark soil into sunlight {d} and {l} watching hopeful, {STYLE}",
        f"{d} warm direct eye contact viewer hand on chest sincere genuine, {STYLE}",
        f"golden bell confetti {d} {s} {a} arms raised celebrate subscribe together, {STYLE}",
    ]
    # Gerar N_IMGS prompts ciclando os templates
    for i in range(N_IMGS):
        prompts.append(scene_templates[i % len(scene_templates)])

    cap_bank = [
        "Você reconhece?","Isso acontece com você?","Olha isso","Deixa eu contar",
        "Você sabia?","Isso muda tudo","Aqui está","Preste atenção",
        "Sinal 1","Sinal 2","Sinal 3","Você não está só",
        "A ciência explica","Seu cérebro","Comprovado","É real",
        "Como reconhecer?","O que você sente","Faz sentido?","Sim, é isso",
        "Você pode!","Primeiro passo","Sua força","Você decide",
        "Proteja-se","Uma coisa por vez","Crescendo","Percebeu?",
        "Isso é cura","Cada dia","Você merece paz","Continue",
        "Compartilha","Alguém precisa","Marca alguém","Salva vidas",
        "Obrigada","Você importa","Até o próximo","Cuide-se",
        "INSCREVA-SE AGORA 🔔"
    ]
    captions = [cap_bank[i % len(cap_bank)] for i in range(n_segs)]
    captions[-1] = "INSCREVA-SE AGORA 🔔"
    return prompts, captions

print(f"\n🧠 Groq: {N_IMGS} prompts + {n_segs} captions...")
t_groq = time.time()
IMAGE_PROMPTS, CAPTIONS = gerar_prompts_groq()
print(f"   {time.time()-t_groq:.1f}s")

# ── GERAÇÃO DE IMAGEM ─────────────────────────────────────────────
def gen_image(prompt, idx):
    full_prompt = (
        "Psych2Go inspired chibi animation style, TWO OR MORE kawaii anime characters "
        "interacting dynamically, expressive faces showing clear emotions, "
        f"clean minimal flat design illustration. {prompt}. "
        "Original character designs not based on any existing IP or franchise, "
        "no text, no words, no logos, no watermarks, high quality chibi art."
    )

    # 1. Pollinations.ai Flux
    try:
        enc = urllib.parse.quote(full_prompt)
        seed = 400 + idx * 11
        url = (f"https://image.pollinations.ai/prompt/{enc}"
               f"?width=576&height=1024&seed={seed}&nologo=true&model=flux&enhance=true")
        r = requests.get(url, timeout=100)
        if r.status_code == 402: time.sleep(25); r = requests.get(url, timeout=100)
        if r.status_code == 200 and r.headers.get('content-type','').startswith('image'):
            tmp = f"{WORKDIR}/raw_{idx:04d}.jpg"
            with open(tmp,"wb") as f: f.write(r.content)
            img = Image.open(tmp).convert("RGB").resize((W,H),Image.LANCZOS)
            out = f"{WORKDIR}/pool_{idx:04d}.jpg"
            img.save(out,"JPEG",quality=93)
            return out, "pollinations"
    except Exception: pass

    # 2. Gemini
    key = gemini_key()
    if key:
        for model in GEMINI_MODELS:
            try:
                url2 = (f"https://generativelanguage.googleapis.com/v1beta"
                        f"/models/{model}:generateContent?key={key}")
                r2 = requests.post(url2,
                    json={"contents":[{"parts":[{"text":full_prompt}]}],
                          "generationConfig":{"responseModalities":["IMAGE","TEXT"]}},
                    timeout=90)
                if r2.status_code == 429: rotate_key(); time.sleep(5); continue
                if r2.status_code == 200:
                    for cand in r2.json().get("candidates",[]):
                        for part in cand.get("content",{}).get("parts",[]):
                            if "inlineData" in part:
                                raw = base64.b64decode(part["inlineData"]["data"])
                                tmp = f"{WORKDIR}/raw_{idx:04d}.jpg"
                                with open(tmp,"wb") as f: f.write(raw)
                                img = Image.open(tmp).convert("RGB")
                                aw,ah = img.size; t = 9/16
                                if aw/ah > t:
                                    nw=int(ah*t); img=img.crop(((aw-nw)//2,0,(aw+nw)//2,ah))
                                elif aw/ah < t:
                                    nh=int(aw/t); img=img.crop((0,(ah-nh)//2,aw,(ah+nh)//2))
                                img = img.resize((W,H),Image.LANCZOS)
                                out = f"{WORKDIR}/pool_{idx:04d}.jpg"
                                img.save(out,"JPEG",quality=93)
                                return out, "gemini"
            except Exception: continue

    # 3. Pillow — 2 personagens por slug variado
    chars = CHARACTERS
    c1 = chars[idx % len(chars)]
    c2 = chars[(idx+3) % len(chars)]
    cores = [(130,80,200),(80,130,200),(200,80,130),(80,200,130),(200,150,80),
             (160,80,200),(80,160,200),(200,80,160),(80,200,160),(200,160,80),
             (100,180,200),(200,100,180),(180,200,100),(100,100,200),(200,100,100)]
    img = Image.new("RGB",(W,H),(245,240,232))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t=y/H; rv=int(245+(232-245)*t); gv=int(240+(225-240)*t); bv=int(232+(218-232)*t)
        draw.line([(0,y),(W,y)],fill=(rv,gv,bv))
    c1_color = cores[idx % len(cores)]
    c2_color = cores[(idx+4) % len(cores)]
    # Chibi 1
    x1=W//3; cy=H//2
    draw.ellipse([x1-90,cy-200,x1+90,cy+30],fill=(255,220,180))
    draw.ellipse([x1-95,cy-250,x1+95,cy-90],fill=(50,35,15))
    draw.ellipse([x1-45,cy-95,x1-15,cy-60],fill=(20,15,8))
    draw.ellipse([x1+15,cy-95,x1+45,cy-60],fill=(20,15,8))
    draw.ellipse([x1-40,cy-90,x1-32,cy-82],fill=(255,255,255))
    draw.ellipse([x1+20,cy-90,x1+28,cy-82],fill=(255,255,255))
    draw.arc([x1-30,cy-20,x1+30,cy+15],start=0,end=180,fill=(190,70,70),width=4)
    draw.rounded_rectangle([x1-75,cy+30,x1+75,cy+240],radius=18,fill=c1_color)
    draw.ellipse([x1-80,cy-50,x1-45,cy-15],fill=(255,175,175))
    draw.ellipse([x1+45,cy-50,x1+80,cy-15],fill=(255,175,175))
    # Chibi 2
    x2=2*W//3
    draw.ellipse([x2-90,cy-200,x2+90,cy+30],fill=(255,210,175))
    draw.ellipse([x2-95,cy-250,x2+95,cy-90],fill=(80,50,20))
    draw.ellipse([x2-45,cy-95,x2-15,cy-60],fill=(20,15,8))
    draw.ellipse([x2+15,cy-95,x2+45,cy-60],fill=(20,15,8))
    draw.ellipse([x2-40,cy-90,x2-32,cy-82],fill=(255,255,255))
    draw.ellipse([x2+20,cy-90,x2+28,cy-82],fill=(255,255,255))
    draw.arc([x2-30,cy-20,x2+30,cy+15],start=0,end=180,fill=(180,60,60),width=4)
    draw.rounded_rectangle([x2-75,cy+30,x2+75,cy+240],radius=18,fill=c2_color)
    draw.ellipse([x2-80,cy-50,x2-45,cy-15],fill=(255,165,165))
    draw.ellipse([x2+45,cy-50,x2+80,cy-15],fill=(255,165,165))
    # Nome dos personagens como indicador visual
    draw.text((x1-30,cy+260),c1["name"][:8].upper(),fill=(255,255,255))
    draw.text((x2-30,cy+260),c2["name"][:8].upper(),fill=(255,255,255))
    out = f"{WORKDIR}/pool_{idx:04d}.jpg"
    img.save(out,"JPEG",quality=85)
    return out, "pillow"

# ── OVERLAY PADRÃO ETERNO ─────────────────────────────────────────
def add_base_overlay(img_path):
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    lt_h = 95
    draw.rectangle([0,H-lt_h,W,H],fill=(8,6,18))
    draw.rectangle([0,H-lt_h,5,H],fill=VERM)
    draw.text((22,H-lt_h+12),"psi",fill=GOLD)
    draw.text((62,H-lt_h+10),"Daniela Coelho",fill=BRAN)
    draw.text((62,H-lt_h+40),"Saude Mental  |  @psidanielacoelho",fill=LILAS)
    draw.rectangle([0,H-4,W,H],fill=VERM)
    img.save(img_path,"JPEG",quality=95)
    return img_path

def make_frame(pool_path, caption, seg_idx):
    frame_path = f"{WORKDIR}/frame_{seg_idx:05d}.jpg"
    img = Image.open(pool_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    if caption:
        cap = caption[:28].upper()
        cap_w = min(len(cap)*14+44, W-60)
        cx = W//2; cap_y = 56
        draw.rounded_rectangle([cx-cap_w//2,cap_y-24,cx+cap_w//2,cap_y+24],
                                radius=15, fill=(245,245,255))
        draw.rounded_rectangle([cx-cap_w//2,cap_y-24,cx+cap_w//2,cap_y+24],
                                radius=15, outline=(200,200,220), width=2)
        draw.text((cx-cap_w//2+22,cap_y-10), cap, fill=(20,15,45))
    img.save(frame_path,"JPEG",quality=90)
    return frame_path

# GERAR POOL (N workers paralelo)
print(f"\n🎨 Gerando {N_IMGS} imagens únicas ({WORKERS} workers paralelo)...")
t0 = time.time()
POOL = [None]*N_IMGS
counts = {"pollinations":0,"gemini":0,"pillow":0}

def gen_pool_img(args):
    i, prompt = args
    path, src = gen_image(prompt, i)
    add_base_overlay(path)
    sz = os.path.getsize(path)//1024
    icon = "✅" if src != "pillow" else "⚠️"
    print(f"   [{i+1:03d}/{N_IMGS}] {icon} {src} ({sz}KB)")
    return path, src

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(gen_pool_img,(i,p)):i for i,p in enumerate(IMAGE_PROMPTS)}
    for fut in as_completed(futures):
        i = futures[fut]
        path, src = fut.result()
        POOL[i] = path
        counts[src] = counts.get(src,0) + 1
        time.sleep(1)

gen_t = time.time()-t0
ai_total = counts.get("pollinations",0)+counts.get("gemini",0)
print(f"\n   ✅ {ai_total}/{N_IMGS} AI | {counts.get('pillow',0)} Pillow | {gen_t:.1f}s")

# ── ÁUDIO ─────────────────────────────────────────────────────────
print(f"\n🎙️  Áudio...")
async def _tts():
    import edge_tts
    c = edge_tts.Communicate(script_tts, voice="pt-BR-AntonioNeural")
    await c.save(f"{WORKDIR}/audio.mp3")

if video.get("audio_url"):
    print("   Usando áudio existente...")
    ar = requests.get(video["audio_url"], timeout=120)
    ar.raise_for_status()
    with open(f"{WORKDIR}/audio.mp3","wb") as f: f.write(ar.content)
else:
    asyncio.run(_tts())

probe = subprocess.run(["ffprobe","-v","quiet","-print_format","json",
    "-show_format",f"{WORKDIR}/audio.mp3"],capture_output=True,text=True)
DUR_AUDIO = float(json.loads(probe.stdout)["format"]["duration"])
RATE_REAL = len(script_tts) / DUR_AUDIO

# Recalcular N_IMGS com duração real (mais preciso)
N_IMGS_REAL = max(20, min(int(DUR_AUDIO / 15), 200))
if N_IMGS_REAL != N_IMGS:
    print(f"   Ajuste N_IMGS: {N_IMGS}→{N_IMGS_REAL} (áudio real: {DUR_AUDIO:.1f}s)")

print(f"   {DUR_AUDIO:.1f}s ({DUR_AUDIO/60:.1f}min) | RATE_REAL={RATE_REAL:.3f} | "
      f"~{DUR_AUDIO/max(1,len(POOL)):.1f}s/img")

# ── TIMING ────────────────────────────────────────────────────────
seg_size = max(1, len(script_tts) // n_segs)
durs = []
for i in range(n_segs):
    chars_count = seg_size if i < n_segs-1 else len(script_tts)-i*seg_size
    durs.append(max(0.5, round(max(1,chars_count)/RATE_REAL, 3)))
print(f"   {n_segs} segs | ~{sum(durs)/n_segs:.1f}s/seg | soma={sum(durs):.1f}s")

# ── FRAMES: cycling pool pelo segmento ───────────────────────────
print(f"\n🖼️  Gerando {n_segs} frames (caption muda a cada segmento)...")
FRAMES = []
pool_size = len([p for p in POOL if p])
for i in range(n_segs):
    pool_idx = (i // SEGS_PER_IMG) % pool_size
    caption  = CAPTIONS[i] if i < len(CAPTIONS) else ""
    frame    = make_frame(POOL[pool_idx], caption, i)
    FRAMES.append(frame)
    if (i+1) % 100 == 0:
        print(f"   {i+1}/{n_segs}...")
print(f"   ✅ {len(FRAMES)} frames")

# ── FFCONCAT + RENDER ─────────────────────────────────────────────
concat_file = f"{WORKDIR}/concat.txt"
with open(concat_file,"w") as f:
    for frame,dur in zip(FRAMES,durs): f.write(f"file '{frame}'\nduration {dur:.3f}\n")
    if FRAMES: f.write(f"file '{FRAMES[-1]}'\n")

print(f"\n🎬 Renderizando (crf={CRF})...")
ts = int(time.time())
out_mp4 = f"{WORKDIR}/v{VIDEO_ID}_long_v8_{ts}.mp4"

cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",concat_file,
       "-i",f"{WORKDIR}/audio.mp3",
       "-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
       "-shortest","-r","25","-crf",str(CRF),
       "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
             "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
       "-movflags","+faststart", out_mp4]
res = subprocess.run(cmd,capture_output=True,text=True,timeout=3600)
if res.returncode != 0: print(f"ERRO:\n{res.stderr[-2000:]}"); sys.exit(1)

sz = os.path.getsize(out_mp4)
probe2 = subprocess.run(["ffprobe","-v","quiet","-print_format","json",
    "-show_format",out_mp4],capture_output=True,text=True)
dur2 = float(json.loads(probe2.stdout)["format"]["duration"])
print(f"   ✅ {sz//1024//1024}MB | {dur2/60:.1f}min")

# ── UPLOAD + DB ───────────────────────────────────────────────────
print(f"\n☁️  Upload...")
if not video.get("audio_url"):
    with open(f"{WORKDIR}/audio.mp3","rb") as f: adata = f.read()
    audio_url = sb_upload(f"audios/v{VIDEO_ID}_long_{ts}.mp3",adata,"audio/mpeg")
    sb_patch("content_pipeline",VIDEO_ID,{"audio_url":audio_url})

with open(out_mp4,"rb") as f: vdata = f.read()
video_url = None
for attempt in range(5):
    try:
        video_url = sb_upload(f"mp4s/v{VIDEO_ID}_long_v8_{ts}.mp4",vdata,"video/mp4")
        print("   ✅ Upload OK"); break
    except Exception as e: print(f"   Tentativa {attempt+1}: {e}"); time.sleep(12)

if video_url:
    sb_patch("content_pipeline",VIDEO_ID,{
        "video_url": video_url, "status": "pending_credentials",
        "metadata": json.dumps({
            "render_version": "v8_long_universe",
            "n_imgs": N_IMGS,
            "n_ai": ai_total,
            "n_segs": n_segs,
            "chars_per_seg": CHARS_PER_SEG,
            "characters": char_slugs,
            "audio_dur_min": round(DUR_AUDIO/60,1),
            "video_dur_min": round(dur2/60,1),
            "file_mb": round(sz/1024/1024,1),
            "crf": CRF, "rate_real": round(RATE_REAL,3),
        })
    })

print(f"\n{'='*60}")
print(f"  ✅ LONG V8 UNIVERSE — #{VIDEO_ID}")
print(f"  {ai_total}/{N_IMGS} AI | {sz//1024//1024}MB | {dur2/60:.1f}min")
print(f"  Personagens: {', '.join(char_slugs[:5])}...")
print(f"  🎬 {video_url}")
print(f"{'='*60}\n")
