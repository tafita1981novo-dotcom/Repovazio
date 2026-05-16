#!/usr/bin/env python3
"""
render_long_v8_standard.py — LONGS 15-25min | PADRÃO ETERNO psicologia.doc
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MELHOR QUE PSYCH2GO:
  ✅ DEZENAS de chibis AI únicos (60 imagens = 3× mais que Psych2Go)
  ✅ Personagens INTERAGINDO: 2-3 chibis por cena, conversando, reagindo
  ✅ Palavra a palavra: caption muda a cada ~3s igual Short #683
  ✅ Groq cria prompt ESPECÍFICO por cena baseado no trecho falado
  ✅ Emoção certa por cena: surpresa, medo, alívio, empatia, conquista...
  ✅ Pool de 60 imagens únicas → cycling inteligente por segmento
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

W, H          = 1080, 1920
N_IMGS        = 60          # 60 chibis únicos AI (dezenas!)
CHARS_PER_SEG = 41          # ~3s por segmento (igual Short #683)
CRF           = 22
WORKERS       = 6           # 6 workers paralelo para gerar 60 imagens mais rápido
WORKDIR       = f"/tmp/vlong_{VIDEO_ID}"
os.makedirs(WORKDIR, exist_ok=True)

# Cores padrão eterno
VERM  = (220,  50,  50)
GOLD  = (255, 210,  50)
BRAN  = (255, 255, 255)
LILAS = (185, 170, 225)

GEMINI_MODELS = [
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash-exp-image-generation",
]

_gkey_idx = [0]
def gemini_key():
    return GEMINI_KEYS[_gkey_idx[0] % len(GEMINI_KEYS)] if GEMINI_KEYS else None
def rotate_key():
    _gkey_idx[0] += 1

print(f"{'='*60}")
print(f"  ψ LONG V8 — #{VIDEO_ID} | {N_IMGS} chibis únicos AI")
print(f"  MELHOR QUE PSYCH2GO — interação + palavra a palavra")
print(f"{'='*60}")

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
topic      = video.get("topic", video.get("title","psychology"))
n_segs     = max(N_IMGS, round(len(script_tts) / CHARS_PER_SEG))

print(f"\n📄 {video.get('title','')}")
print(f"   {len(script_tts)} chars | {n_segs} segmentos | {N_IMGS} imagens únicas")
print(f"   ~{CHARS_PER_SEG} chars/seg = ~3s/imagem (igual Short #683)")

# ── GROQ: 60 PROMPTS COM INTERAÇÃO + N_SEGS CAPTIONS ─────────────
def gerar_prompts_groq():
    """
    Groq gera:
    1. 60 prompts ÚNICOS — cada um com 2-3 personagens INTERAGINDO
       baseado no arco emocional do roteiro (não genérico!)
    2. N_SEGS captions específicas para cada segmento do script
    """
    if not GROQ_KEY:
        return gerar_fallback()

    # Dividir script em seções para contexto emocional
    sec_size = len(script_tts) // 6
    sections = [script_tts[i*sec_size:(i+1)*sec_size] for i in range(6)]

    system = f"""You are a world-class animation director for @psidanielacoelho, a Brazilian psychology YouTube channel.
Your goal: create {N_IMGS} chibi scene prompts that are MORE DYNAMIC and EMOTIONAL than Psych2Go.

CHARACTERS (use consistently throughout):
- DANIELA: "chibi anime girl, short dark bob hair, warm honey eyes, soft professional mint-green blouse, small ψ pin on collar"
- LUCAS: "chibi anime boy, tousled dark hair, expressive dark eyes, casual navy hoodie, slightly slouched posture"
- SARA: "chibi anime girl, long wavy auburn hair, round glasses, anxious expression, pale yellow cardigan"
- EXPERT: "chibi anime professional woman, neat bun, white lab coat, clipboard, calm authoritative expression"

INTERACTION RULES (MUST follow — this is what beats Psych2Go):
- At least 2 characters per scene
- Characters must be PHYSICALLY INTERACTING: touching shoulders, making eye contact, pointing at each other, one comforting other, back-to-back, face-to-face confrontation, one hiding from other
- EMOTIONAL REACTIONS: characters visually reacting to what's being said (shocked, relieved, crying, laughing, determined)
- PROPS that tell the story: shattered heart floating between them, puzzle pieces, invisible wall of glass, puppet strings, mirror showing different reflection, cracked foundation under feet

STYLE (better than Psych2Go):
- Background: soft cream #F5F0E8 with ONE meaningful prop or color accent
- Chibi style: rounder heads (70% of body), huge shiny eyes, exaggerated expressions
- Dynamic poses: lean-in conversations, dramatic reveals, protective gestures
- NO TEXT in image, NO logos, original characters not based on any IP

STRUCTURE — {N_IMGS} scenes covering the FULL emotional arc:
Scenes 1-10: Hook + Emotional opening (grab attention, show the problem visually)
Scenes 11-20: Recognition + Examples (viewers see themselves in the story)  
Scenes 21-30: Deep truth + Science (expert explains, characters react)
Scenes 31-40: Turning point + Empowerment (characters transform)
Scenes 41-50: Recovery + Growth (healing journey, small victories)
Scenes 51-60: Resolution + CTA (strong ending, hope, subscribe)

Return ONLY valid JSON (no markdown):
{{
  "image_prompts": ["full detailed prompt 1", "full detailed prompt 2", ...  (exactly {N_IMGS} prompts)],
  "captions": ["caption1 PT max 25 chars", ...  (exactly {n_segs} captions)]
}}"""

    user_msg = f"""Topic: {topic}
Total script: {len(script_tts)} chars across {n_segs} segments

Script sections (emotional context for prompts):
Opening: {sections[0][:300]}
Development: {sections[1][:300]}
Core truth: {sections[2][:300]}
Turning point: {sections[3][:300]}
Solution: {sections[4][:300]}
Closing: {sections[5][:300]}

Generate {N_IMGS} interaction-rich chibi prompts covering this emotional arc.
Generate {n_segs} short PT-BR captions (max 25 chars each) for each segment.
Last caption must be: "INSCREVA-SE AGORA 🔔"
"""

    print(f"   Chamando Groq ({N_IMGS} prompts + {n_segs} captions)...")
    for attempt in range(4):
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
                json={"model":"llama-3.3-70b-versatile",
                      "messages":[{"role":"system","content":system},
                                   {"role":"user","content":user_msg}],
                      "temperature":0.8,"max_tokens":8000},
                timeout=120)
            if r.status_code == 200:
                text = r.json()["choices"][0]["message"]["content"]
                # Extrair JSON
                match = re.search(r'\{[\s\S]*\}', text)
                if match:
                    data = json.loads(match.group())
                    prompts  = data.get("image_prompts",[])
                    captions = data.get("captions",[])
                    if len(prompts) >= N_IMGS and len(captions) >= n_segs:
                        prompts  = prompts[:N_IMGS]
                        captions = captions[:n_segs]
                        captions[-1] = "INSCREVA-SE AGORA 🔔"
                        print(f"   ✅ Groq: {len(prompts)} prompts + {len(captions)} captions")
                        return prompts, captions
                    # Preencher se incompleto
                    while len(prompts) < N_IMGS:
                        prompts.append(prompts[-1] if prompts else "chibi psychology scene")
                    while len(captions) < n_segs:
                        captions.append(captions[len(captions)%30] if captions else "...")
                    captions[-1] = "INSCREVA-SE AGORA 🔔"
                    print(f"   ✅ Groq (preenchido): {len(prompts)} prompts + {len(captions)} captions")
                    return prompts[:N_IMGS], captions[:n_segs]
        except Exception as e:
            print(f"   Groq tentativa {attempt+1}: {e}")
            time.sleep(8)

    print("   ⚠️ Groq falhou → fallback")
    return gerar_fallback()

def gerar_fallback():
    """60 prompts de interação chibi — fallback rico em cenas."""
    STYLE = "chibi anime flat design, kawaii psychology, cream background #F5F0E8, no text, original character not based on any IP"
    DANIELA = "chibi girl short dark bob hair mint-green blouse warm smile"
    LUCAS   = "chibi boy tousled dark hair navy hoodie anxious posture"
    SARA    = "chibi girl long auburn hair round glasses pale yellow cardigan worried"
    EXPERT  = "chibi professional woman neat bun white lab coat clipboard confident"

    prompts = []
    # Bloco 1: Hook (10)
    prompts += [
        f"{DANIELA} and {LUCAS} facing each other shocked expressions floating question marks between them, {STYLE}",
        f"{DANIELA} pointing at viewer direct eye contact urgent warm expression large thought bubble, {STYLE}",
        f"{LUCAS} hiding face behind hands {SARA} reaching out concern shadow person behind him, {STYLE}",
        f"Three chibi silhouettes one highlighted with subtle sinister golden glow others unaware, {STYLE}",
        f"{DANIELA} and {SARA} sitting close one whispering secret into other's ear wide eyes, {STYLE}",
        f"{LUCAS} smiling charming puppet strings above head invisible to him {DANIELA} noticing horrified, {STYLE}",
        f"Large cracked heart floating center {DANIELA} on left sad {LUCAS} on right turned away, {STYLE}",
        f"{SARA} looking in mirror reflection shows different sadder version of herself {DANIELA} watching concerned, {STYLE}",
        f"{DANIELA} holding magnifying glass revealing hidden truth {LUCAS} shocked hands on cheeks, {STYLE}",
        f"{EXPERT} and {DANIELA} side by side {EXPERT} pointing at brain diagram {DANIELA} nodding seriously, {STYLE}",
    ]
    # Bloco 2: Reconhecimento (10)
    prompts += [
        f"{LUCAS} speaking empty speech bubble {SARA}'s voice being erased mid-air frustrated expression, {STYLE}",
        f"{DANIELA} showing numbered list on clipboard {SARA} reading it slowly recognition dawning, {STYLE}",
        f"{LUCAS} standing tall {SARA} shrinking smaller beside him invisible weight pressing down, {STYLE}",
        f"{SARA} and {DANIELA} sitting cross-legged facing each other deep conversation tea cups, {STYLE}",
        f"Invisible glass wall between {LUCAS} and {DANIELA} both pressing hands against it, {STYLE}",
        f"{SARA} holding red flag {LUCAS} ignoring it walking away {DANIELA} watching helplessly, {STYLE}",
        f"{DANIELA} drawing timeline on whiteboard {SARA} pointing at moment of recognition, {STYLE}",
        f"Three stages: {SARA} confused → {SARA} recognizing → {SARA} determined standing tall, {STYLE}",
        f"{LUCAS} wearing theatre mask friendly outside {DANIELA} seeing dark shadow behind, {STYLE}",
        f"{SARA} building protective bubble {DANIELA} supporting her from outside warmly, {STYLE}",
    ]
    # Bloco 3: Ciência (10)
    prompts += [
        f"{EXPERT} pointing at glowing brain diagram both {DANIELA} and {SARA} leaning in fascinated, {STYLE}",
        f"Chibi brain with highlighted stress zones {EXPERT} explaining {DANIELA} taking notes, {STYLE}",
        f"{EXPERT} showing iceberg diagram {LUCAS} visible small part underwater huge hidden truth, {STYLE}",
        f"DNA strand with psychology trauma patterns {EXPERT} and {DANIELA} examining together, {STYLE}",
        f"{SARA} head showing thought spiral {EXPERT} gently placing hand on shoulder reassuring, {STYLE}",
        f"Scientific journal open {EXPERT} reading key finding {DANIELA} and {SARA} beside her amazed, {STYLE}",
        f"Cause-effect diagram arrows {EXPERT} explaining {LUCAS} shocked at revelation, {STYLE}",
        f"Timeline childhood to adult {DANIELA} tracing path {SARA} recognizing herself in it, {STYLE}",
        f"{EXPERT} neuron synapse glow healing {DANIELA} and {SARA} watching hopeful, {STYLE}",
        f"Research screen showing patterns {EXPERT} pointing {DANIELA} {SARA} taking notes together, {STYLE}",
    ]
    # Bloco 4: Virada (10)
    prompts += [
        f"{DANIELA} and {SARA} standing back-to-back strong confident determined poses, {STYLE}",
        f"{SARA} cutting invisible puppet strings above her head {DANIELA} cheering hands raised, {STYLE}",
        f"Shield heart shape {DANIELA} handing to {SARA} who holds it up strong, {STYLE}",
        f"{LUCAS} offering hand {SARA} choosing to step back set boundary respectfully, {STYLE}",
        f"{DANIELA} drawing clear boundary line {SARA} standing confidently on her side, {STYLE}",
        f"Checklist healing steps {DANIELA} and {SARA} checking items together smiling, {STYLE}",
        f"{SARA} looking in mirror now seeing strong confident reflection {DANIELA} beside her proud, {STYLE}",
        f"Plant growing from dark soil into sunlight {DANIELA} and {SARA} watching it together, {STYLE}",
        f"{SARA} journal writing {DANIELA} sitting nearby supportive warm light, {STYLE}",
        f"Before-after: {SARA} hunched alone → {SARA} upright {DANIELA} beside her smiling, {STYLE}",
    ]
    # Bloco 5: Recuperação (10)
    prompts += [
        f"{DANIELA} {SARA} {EXPERT} three together arms around shoulders community, {STYLE}",
        f"Golden sunrise {DANIELA} and {SARA} walking toward it side by side hopeful, {STYLE}",
        f"{SARA} hands open releasing dark cloud floating away {DANIELA} watching relief on face, {STYLE}",
        f"Support circle five chibis holding hands warmth golden light, {STYLE}",
        f"{DANIELA} holding glowing heart lantern {SARA} receiving it tearful happy, {STYLE}",
        f"{SARA} small victory fist pump {DANIELA} celebrating beside her confetti, {STYLE}",
        f"Repair kit toolbox {DANIELA} and {SARA} fixing cracked heart together, {STYLE}",
        f"{EXPERT} {DANIELA} {SARA} three generations of healing timeline, {STYLE}",
        f"{SARA} reading book self-help {DANIELA} recommended it sits beside her, {STYLE}",
        f"Bridge being built {DANIELA} and {SARA} each building from their side meeting middle, {STYLE}",
    ]
    # Bloco 6: Conclusão + CTA (10)
    prompts += [
        f"{DANIELA} direct eye contact viewer warm knowing smile hand on chest sincere, {STYLE}",
        f"{DANIELA} and {SARA} both turning to viewer together united message, {STYLE}",
        f"Phone screen showing channel {DANIELA} pointing at it excitedly {SARA} beside her, {STYLE}",
        f"{DANIELA} holding heart toward viewer offering emotional support empathy, {STYLE}",
        f"Five star rating floating {DANIELA} {SARA} thumbs up together, {STYLE}",
        f"{DANIELA} megaphone announcement sharing important message {SARA} amplifying, {STYLE}",
        f"Comment bubbles floating {DANIELA} reading them smiling touched, {STYLE}",
        f"{DANIELA} and {SARA} waving goodbye warmly safe cozy atmosphere, {STYLE}",
        f"Eye symbol ear symbol heart symbol {DANIELA} gesturing I see you I hear you, {STYLE}",
        f"Giant golden bell confetti rainbow {DANIELA} {SARA} {EXPERT} arms raised subscribe celebrate, {STYLE}",
    ]

    cap_bank = [
        "Você reconhece?","Isso acontece com você?","Preste atenção","Deixa eu te contar",
        "Você sabia?","Isso muda tudo","Olha isso...","Aqui está a chave",
        "Sinal 1","Sinal 2","Sinal 3","Você não está só",
        "A ciência explica","Seu cérebro sabe","Pesquisas comprovam","É real",
        "Como reconhecer?","O que você sente","Isso faz sentido?","Sim, é isso",
        "Você pode sair disso","Primeiro passo","Sua força interior","Você decide",
        "Proteja-se assim","Uma coisa por vez","Você está crescendo","Percebeu?",
        "Isso é cura","Cada dia melhor","Você merece paz","Continue assim",
        "Compartilha isso","Alguém precisa ver","Marca um amigo","Isso salva vidas",
        "Muito obrigada","Você importa pra mim","Até o próximo","Cuide-se",
        "INSCREVA-SE AGORA 🔔"
    ]

    captions = [cap_bank[i % len(cap_bank)] for i in range(n_segs)]
    captions[-1] = "INSCREVA-SE AGORA 🔔"
    return prompts[:N_IMGS], captions

print(f"\n🧠 Groq: {N_IMGS} prompts interação + {n_segs} captions...")
t_groq = time.time()
IMAGE_PROMPTS, CAPTIONS = gerar_prompts_groq()
print(f"   Groq concluído em {time.time()-t_groq:.1f}s")

# ── GERAR IMAGENS: Pollinations → Gemini → Pillow ─────────────────
def gen_image(prompt, idx):
    """
    Gera imagem chibi de ALTA QUALIDADE com 2-3 personagens interagindo.
    Primary: Pollinations.ai Flux (melhor qualidade, grátis)
    Fallback: Gemini 2.0 Flash Exp
    Último: Pillow programático variado
    """
    full_prompt = (
        "Psych2Go inspired chibi animation style, TWO OR MORE kawaii anime characters "
        "interacting dynamically, expressive faces showing clear emotions, "
        "cream warm background #F5F0E8 with single meaningful prop, "
        f"clean minimal flat design illustration. Scene: {prompt}. "
        "Original character designs not based on any existing IP or franchise, "
        "no text, no words, no logos, no watermarks, high quality chibi art."
    )

    # 1. Pollinations.ai Flux
    try:
        enc = urllib.parse.quote(full_prompt)
        seed = 300 + idx * 7  # seed único por imagem
        url = (f"https://image.pollinations.ai/prompt/{enc}"
               f"?width=576&height=1024&seed={seed}&nologo=true&model=flux&enhance=true")
        r = requests.get(url, timeout=100)
        if r.status_code == 402:
            time.sleep(25)
            r = requests.get(url, timeout=100)
        if r.status_code == 200 and r.headers.get('content-type','').startswith('image'):
            tmp = f"{WORKDIR}/raw_{idx:03d}.jpg"
            with open(tmp,"wb") as f: f.write(r.content)
            img = Image.open(tmp).convert("RGB").resize((W,H),Image.LANCZOS)
            out = f"{WORKDIR}/pool_{idx:03d}.jpg"
            img.save(out,"JPEG",quality=93)
            return out, "pollinations"
    except Exception:
        pass

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
                                tmp = f"{WORKDIR}/raw_{idx:03d}.jpg"
                                with open(tmp,"wb") as f: f.write(raw)
                                img = Image.open(tmp).convert("RGB")
                                aw,ah = img.size; t = 9/16
                                if aw/ah > t:
                                    nw=int(ah*t); img=img.crop(((aw-nw)//2,0,(aw+nw)//2,ah))
                                elif aw/ah < t:
                                    nh=int(aw/t); img=img.crop((0,(ah-nh)//2,aw,(ah+nh)//2))
                                img = img.resize((W,H),Image.LANCZOS)
                                out = f"{WORKDIR}/pool_{idx:03d}.jpg"
                                img.save(out,"JPEG",quality=93)
                                return out, "gemini"
            except Exception:
                continue

    # 3. Pillow fallback — chibi com interação (2 personagens)
    img = Image.new("RGB",(W,H),(245,240,232))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t=y/H; rv=int(245+(232-245)*t); gv=int(240+(225-240)*t); bv=int(232+(218-232)*t)
        draw.line([(0,y),(W,y)],fill=(rv,gv,bv))

    # Personagem 1 (esquerda)
    cores = [(130,80,200),(80,130,200),(200,80,130),(80,200,130),(200,150,80),
             (160,80,200),(80,160,200),(200,80,160),(80,200,160),(200,160,80)]
    c1 = cores[idx % len(cores)]
    c2 = cores[(idx+3) % len(cores)]

    # Chibi 1 — esquerda
    x1 = W//3
    cy = H//2
    draw.ellipse([x1-90,cy-200,x1+90,cy+30],fill=(255,220,180))
    draw.ellipse([x1-95,cy-250,x1+95,cy-90],fill=(50,35,15))
    draw.ellipse([x1-45,cy-95,x1-15,cy-60],fill=(20,15,8))
    draw.ellipse([x1+15,cy-95,x1+45,cy-60],fill=(20,15,8))
    draw.ellipse([x1-40,cy-90,x1-32,cy-82],fill=(255,255,255))
    draw.ellipse([x1+20,cy-90,x1+28,cy-82],fill=(255,255,255))
    draw.arc([x1-30,cy-20,x1+30,cy+15],start=0,end=180,fill=(190,70,70),width=4)
    draw.rounded_rectangle([x1-75,cy+30,x1+75,cy+240],radius=18,fill=c1)
    draw.ellipse([x1-140,cy+50,x1-55,cy+160],fill=c1)
    draw.ellipse([x1+55,cy+50,x1+140,cy+160],fill=c1)
    draw.ellipse([x1-85,cy-50,x1-45,cy-15],fill=(255,175,175))
    draw.ellipse([x1+45,cy-50,x1+85,cy-15],fill=(255,175,175))

    # Chibi 2 — direita
    x2 = 2*W//3
    draw.ellipse([x2-90,cy-200,x2+90,cy+30],fill=(255,210,175))
    draw.ellipse([x2-95,cy-250,x2+95,cy-90],fill=(80,50,20))
    draw.ellipse([x2-45,cy-95,x2-15,cy-60],fill=(20,15,8))
    draw.ellipse([x2+15,cy-95,x2+45,cy-60],fill=(20,15,8))
    draw.ellipse([x2-40,cy-90,x2-32,cy-82],fill=(255,255,255))
    draw.ellipse([x2+20,cy-90,x2+28,cy-82],fill=(255,255,255))
    draw.arc([x2-30,cy-20,x2+30,cy+15],start=0,end=180,fill=(180,60,60),width=4)
    draw.rounded_rectangle([x2-75,cy+30,x2+75,cy+240],radius=18,fill=c2)
    draw.ellipse([x2-140,cy+50,x2-55,cy+160],fill=c2)
    draw.ellipse([x2+55,cy+50,x2+140,cy+160],fill=c2)
    draw.ellipse([x2-85,cy-50,x2-45,cy-15],fill=(255,165,165))
    draw.ellipse([x2+45,cy-50,x2+85,cy-15],fill=(255,165,165))

    # Elemento de interação no centro (coração, seta, etc.)
    cx = W//2
    mid_props = ['❤', '↔', '?!', '☀', '★']
    prop = mid_props[idx % len(mid_props)]
    draw.ellipse([cx-30,cy-80,cx+30,cy-20],fill=(255,240,230))
    draw.text((cx-10,cy-70),prop,fill=VERM)

    out = f"{WORKDIR}/pool_{idx:03d}.jpg"
    img.save(out,"JPEG",quality=85)
    return out, "pillow"

# ── OVERLAY PADRÃO ETERNO ─────────────────────────────────────────
def add_base_overlay(img_path):
    """Lower third permanente idêntico ao Short."""
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
    """Frame final com caption palavra a palavra."""
    frame_path = f"{WORKDIR}/frame_{seg_idx:04d}.jpg"
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

# GERAR POOL (6 workers paralelo)
print(f"\n🎨 Gerando {N_IMGS} chibis únicos AI ({WORKERS} workers)...")
t0 = time.time()
POOL = [None]*N_IMGS
counts = {"pollinations":0,"gemini":0,"pillow":0}

def gen_pool_img(args):
    i, prompt = args
    path, src = gen_image(prompt, i)
    add_base_overlay(path)
    sz = os.path.getsize(path)//1024
    icon = "✅" if src != "pillow" else "⚠️"
    print(f"   [{i+1:02d}/{N_IMGS}] {icon} {src} ({sz}KB)")
    return path, src

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(gen_pool_img,(i,p)):i
               for i,p in enumerate(IMAGE_PROMPTS)}
    for fut in as_completed(futures):
        i = futures[fut]
        path, src = fut.result()
        POOL[i] = path
        counts[src] = counts.get(src,0) + 1
        time.sleep(1.5)

gen_t = time.time()-t0
ai_total = counts.get("pollinations",0) + counts.get("gemini",0)
print(f"\n   ✅ {ai_total}/{N_IMGS} AI  ({counts.get('pollinations',0)} Pollinations + {counts.get('gemini',0)} Gemini)")
print(f"   ⚠️  {counts.get('pillow',0)} Pillow fallback | {gen_t:.1f}s total")

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
print(f"   {DUR_AUDIO:.1f}s ({DUR_AUDIO/60:.1f}min) | RATE_REAL={RATE_REAL:.3f}")

# ── TIMING DINÂMICO ───────────────────────────────────────────────
seg_size = len(script_tts) // n_segs
durs = []
for i in range(n_segs):
    chars = seg_size if i < n_segs-1 else len(script_tts) - i*seg_size
    durs.append(max(0.5, round(chars/RATE_REAL, 3)))

print(f"   {n_segs} segmentos | ~{sum(durs)/n_segs:.1f}s/seg | soma={sum(durs):.1f}s")

# ── GERAR FRAMES COM CYCLING INTELIGENTE ─────────────────────────
# Cycling não é puro i%60 — usa padrão que agrupa cenas similares
# Blocos de 6 segmentos compartilham a mesma imagem base (naturalmente)
# Mas avançam para imagem diferente a cada bloco
print(f"\n🖼️  Gerando {n_segs} frames (cycling inteligente de {N_IMGS} imagens)...")
FRAMES = []
for i in range(n_segs):
    # Avança para nova imagem a cada ~6 segmentos (~18s)
    # mas nunca repete a mesma imagem consecutivamente
    pool_idx = (i // 6) % N_IMGS
    caption = CAPTIONS[i] if i < len(CAPTIONS) else ""
    frame = make_frame(POOL[pool_idx], caption, i)
    FRAMES.append(frame)
    if (i+1) % 100 == 0:
        print(f"   {i+1}/{n_segs} frames...")

print(f"   ✅ {len(FRAMES)} frames | pool cycling ~6 segs/imagem")

# ── FFCONCAT ─────────────────────────────────────────────────────
concat_file = f"{WORKDIR}/concat.txt"
with open(concat_file,"w") as f:
    for frame, dur in zip(FRAMES, durs):
        f.write(f"file '{frame}'\nduration {dur:.3f}\n")
    if FRAMES: f.write(f"file '{FRAMES[-1]}'\n")

# ── RENDER ────────────────────────────────────────────────────────
print(f"\n🎬 Renderizando (crf={CRF})...")
ts = int(time.time())
out_mp4 = f"{WORKDIR}/v{VIDEO_ID}_long_v8_{ts}.mp4"

cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",concat_file,
       "-i",f"{WORKDIR}/audio.mp3",
       "-c:v","libx264","-pix_fmt","yuv420p",
       "-c:a","aac","-b:a","128k",
       "-shortest","-r","25","-crf",str(CRF),
       "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
             "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
       "-movflags","+faststart", out_mp4]
res = subprocess.run(cmd,capture_output=True,text=True,timeout=3600)
if res.returncode != 0:
    print(f"ERRO FFMPEG:\n{res.stderr[-2000:]}"); sys.exit(1)

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
    except Exception as e:
        print(f"   Tentativa {attempt+1}: {e}"); time.sleep(12)

if video_url:
    sb_patch("content_pipeline",VIDEO_ID,{
        "video_url": video_url, "status": "pending_credentials",
        "metadata": json.dumps({
            "render_version": "v8_long_60imgs",
            "n_imgs_pool": N_IMGS,
            "n_ai_imgs": ai_total,
            "n_segments": n_segs,
            "audio_dur_min": round(DUR_AUDIO/60,1),
            "video_dur_min": round(dur2/60,1),
            "file_mb": round(sz/1024/1024,1),
            "crf": CRF,
            "pollinations": counts.get("pollinations",0),
            "gemini": counts.get("gemini",0),
            "pillow": counts.get("pillow",0),
        })
    })

print(f"\n{'='*60}")
print(f"  ✅ LONG V8 60-IMGS — #{VIDEO_ID}")
print(f"  {ai_total}/{N_IMGS} AI chibi | {sz//1024//1024}MB | {dur2/60:.1f}min")
print(f"  🎬 {video_url}")
print(f"{'='*60}\n")
