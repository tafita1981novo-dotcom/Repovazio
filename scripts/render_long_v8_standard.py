#!/usr/bin/env python3
"""
render_long_v8_standard.py — QUANTUM UNIVERSE | psicologia.doc
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IDEIA INOVADORA MUNDIAL: SERIALIZED PSYCHOLOGY UNIVERSE
────────────────────────────────────────────────────────
O que ninguém fez ainda no mundo de conteúdo educacional:
Personagens com ARCOS EMOCIONAIS REAIS que evoluem de vídeo em vídeo.

Sara começa tímida no #692 → reconhece o gaslighting no #693 →
experimenta limites no #695 → completamente transformada no #706.

Os espectadores voltam não pelo tópico — voltam pela SARA.
Isso cria parasocialidade + compulsão de maratona = HIPNOSE VIRAL.

MECANISMOS DE HIPNOSE (baseados em comportamento humano real):
  1. PARASOCIAL BOND — personagens nomeados com histórias reais
  2. ARC SERIALIZADO — cada vídeo avança o arco dos personagens
  3. CLIFFHANGER FINAL — "o que vai acontecer com Sara na semana que vem?"
  4. VISUAL EVOLUTION — o visual muda conforme o personagem cresce
  5. CROSS-REFERENCE — "você viu o que aconteceu com Sara no #693?"
  6. COMMUNITY HOOK — comentários viram sobre os personagens, não o tópico
  7. REVELATION MOMENTS — cenas que viram clips virais e memes

TÉCNICO:
  - N_IMGS dinâmico sem limite (duração ÷ 15s)
  - Personagens carregados do universo Supabase
  - Arc emocional do personagem alimenta os prompts Groq
  - Hooks de cliffhanger gerados automaticamente
  - Viral moments detectados e salvos no DB
  - Caption palavra a palavra = ~3s/imagem (idêntico ao Short #683)
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
CHARS_PER_SEG = 41        # ~3s/segmento (idêntico Short #683)
SEGS_PER_IMG  = 5         # imagem muda a cada 5 segmentos (~15s)
CRF           = 22
WORKERS       = 8         # 8 workers para gerar mais imagens em paralelo
WORKDIR       = f"/tmp/vquantum_{VIDEO_ID}"
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
def rotate_key(): _gkey_idx[0] += 1

# ── SUPABASE ──────────────────────────────────────────────────────
def sb_get(table, qs):
    r = requests.get(f"{SB_URL}/rest/v1/{table}?{qs}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=30)
    r.raise_for_status(); return r.json()

def sb_patch(table, id_, data):
    r = requests.patch(f"{SB_URL}/rest/v1/{table}?id=eq.{id_}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"},
        json=data, timeout=30); r.raise_for_status()

def sb_upsert(table, data):
    r = requests.post(f"{SB_URL}/rest/v1/{table}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"resolution=merge-duplicates"},
        json=data, timeout=30); r.raise_for_status()

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
if not rows: sys.exit(f"❌ {VIDEO_ID} não encontrado")

video      = rows[0]
script_tts = video.get("script","").strip()
topic      = video.get("topic", video.get("title","psychology")).lower()

print(f"\n{'═'*60}")
print(f"  ψ QUANTUM UNIVERSE — #{VIDEO_ID}")
print(f"  {video.get('title','')}")
print(f"  {len(script_tts)} chars")
print(f"{'═'*60}")

# ── CARREGAR UNIVERSO DE PERSONAGENS + MEMÓRIA ────────────────────
def load_universe():
    """Carrega personagens + arcos anteriores + memória do universo."""

    # Personagens completos
    chars = sb_get("character_universe",
        "select=slug,name,role,visual,personality,topics,appearances&order=id.asc")

    # Memória atual do universo
    memory = sb_get("universe_memory",
        "select=character_slug,current_stage,cumulative_arc,visual_evolution")
    mem_map = {m["character_slug"]: m for m in memory}

    # Arcos dos 5 vídeos anteriores
    prev_arcs = sb_get("character_story_arc",
        f"select=character_slug,video_id,emotional_state,story_note,arc_stage"
        f"&order=video_id.desc&limit=50")

    # Filtrar relevantes ao tópico
    must_include = {"daniela", "ana"}
    relevant = [c for c in chars if c["slug"] in must_include or
                any(t in topic for t in c.get("topics",[])) or "todos" in c.get("topics",[])]
    if len(relevant) < 6:
        added = {c["slug"] for c in relevant}
        for c in chars:
            if c["slug"] not in added: relevant.append(c)
            if len(relevant) >= 10: break

    # Enriquecer com memória e arcos
    for c in relevant:
        mem = mem_map.get(c["slug"], {})
        c["current_stage"] = mem.get("current_stage", 1)
        c["cumulative_arc"] = mem.get("cumulative_arc", "")
        c["visual_evolution"] = mem.get("visual_evolution", c["visual"])
        c["prev_arcs"] = [a for a in prev_arcs if a["character_slug"] == c["slug"]][:3]

    # Atualizar aparências
    for c in relevant:
        try:
            requests.patch(f"{SB_URL}/rest/v1/character_universe?slug=eq.{c['slug']}",
                headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                         "Content-Type":"application/json","Prefer":"return=minimal"},
                json={"appearances": c.get("appearances",0) + 1}, timeout=10)
        except: pass

    return relevant[:12]

CHARACTERS = load_universe()
char_slugs = [c["slug"] for c in CHARACTERS]
print(f"\n👥 Personagens: {', '.join(char_slugs)}")

# ── CALCULAR N_IMGS DINÂMICO ──────────────────────────────────────
DUR_EST    = len(script_tts) / 14.5
N_IMGS     = max(20, int(DUR_EST / 15))  # SEM LIMITE MÁXIMO
n_segs     = max(N_IMGS, round(len(script_tts) / CHARS_PER_SEG))

print(f"🎨 N_IMGS QUANTUM: {N_IMGS} (calculado de {DUR_EST:.0f}s estimado)")
print(f"   {n_segs} segmentos | ~3s/imagem | {WORKERS} workers")

# ── BUILD CHAR GUIDE COM ARC HISTORY ─────────────────────────────
def build_quantum_char_guide():
    """Guia completo dos personagens com estado atual e histórico."""
    lines = []
    for c in CHARACTERS:
        stage_desc = {
            1:"início — ainda não percebe o problema",
            2:"percebendo — começa a questionar",
            3:"lutando — reconhece mas tem medo de mudar",
            4:"quebrando — no limite, ponto de virada",
            5:"transformando — tomando decisões difíceis",
            6:"crescendo — aprendendo a se proteger",
            7:"consolidando — praticando os novos padrões",
            8:"healed — exemplo de cura para outros",
            9:"sábia — agora ajuda outros a crescerem",
            10:"completa — arco fechado"
        }.get(c.get("current_stage",1), "em jornada")

        prev = c.get("prev_arcs",[])
        history = " → ".join([f"v{a['video_id']}:{a['emotional_state']}" for a in prev]) or "primeira aparição"

        lines.append(
            f"━ {c['name'].upper()} ({c['role']}) | Estágio {c.get('current_stage',1)}/10: {stage_desc}\n"
            f"  Visual ATUAL: {c.get('visual_evolution', c['visual'])}\n"
            f"  Jornada: {c.get('cumulative_arc','')[:100]}\n"
            f"  Histórico recente: {history}"
        )
    return "\n\n".join(lines)

CHAR_GUIDE = build_quantum_char_guide()

# ── GROQ: QUANTUM PROMPTS + CAPTIONS + HOOKS ─────────────────────
def gerar_quantum_groq():
    """
    Uma chamada Groq gera:
    1. N_IMGS prompts de imagem com INTERAÇÃO + ARC EMOCIONAL
    2. N_SEGS captions (palavra a palavra)
    3. Cliffhanger hook para o próximo vídeo
    4. Momentos virais identificados
    5. Atualizações dos arcos dos personagens
    """
    if not GROQ_KEY: return gerar_quantum_fallback()

    sec = max(1, len(script_tts)//6)
    sections = [script_tts[i*sec:(i+1)*sec][:300] for i in range(6)]

    system = f"""You are the head writer and animation director of @psidanielacoelho,
a Brazilian psychology YouTube channel building the world's first SERIALIZED EDUCATIONAL UNIVERSE.

THE INNOVATION: Unlike generic psychology videos, our characters have REAL EMOTIONAL ARCS
that evolve across 200+ videos. Viewers come back not for the topic — they come back for SARA.
This creates parasocial bonds → compulsive watching → viral word of mouth.

CURRENT CHARACTER UNIVERSE (use their EXACT visual descriptions and emotional stages):

{CHAR_GUIDE}

QUANTUM RULES FOR THIS VIDEO (#{VIDEO_ID}):
1. Every image shows 2-3 characters PHYSICALLY INTERACTING in a way that advances their arc
2. Emotions must match their CURRENT ARC STAGE — Sara in stage 1 looks lost, stage 5 looks determined
3. Visual changes must be SUBTLE but consistent — Sara's posture improves as arc advances
4. Each scene must feel like it MATTERS to the story, not generic stock illustration
5. Include one VIRAL MOMENT: a scene so emotionally resonant viewers screenshot/share it

Return ONLY valid JSON:
{{
  "image_prompts": ["(exactly {N_IMGS} detailed interaction prompts)"],
  "captions": ["(exactly {n_segs} PT-BR captions max 25 chars each)"],
  "cliffhanger_hook": "texto do cliffhanger do final do vídeo (max 100 chars PT-BR)",
  "viral_moment": {{
    "prompt_index": 0,
    "description": "descrição da cena viral",
    "caption": "legenda viral sugerida"
  }},
  "arc_updates": [
    {{
      "character_slug": "sara",
      "new_stage": 2,
      "emotional_state": "awakening",
      "story_note": "Sara percebeu o padrão pela primeira vez",
      "visual_change": "Sara começa a usar o cabelo levemente mais solto"
    }}
  ]
}}"""

    user_msg = f"""Topic: {topic}
Script: {len(script_tts)} chars → {n_segs} segments → {N_IMGS} unique images

Script sections:
ABERTURA: {sections[0]}
DESENVOLVIMENTO: {sections[1]}
APROFUNDAMENTO: {sections[2]}
VIRADA: {sections[3]}
SOLUÇÃO: {sections[4]}
FECHAMENTO: {sections[5]}

Generate {N_IMGS} interaction prompts advancing character arcs.
Generate {n_segs} PT-BR captions (palavra a palavra, max 25 chars each).
Last caption: "INSCREVA-SE AGORA 🔔"
Identify the most viral-potential moment."""

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
                    hook     = data.get("cliffhanger_hook","")
                    viral    = data.get("viral_moment",{})
                    arc_ups  = data.get("arc_updates",[])

                    # Garantir tamanhos
                    while len(prompts)  < N_IMGS: prompts.append(prompts[-1] if prompts else "chibi psychology interaction")
                    while len(captions) < n_segs: captions.append(captions[len(captions)%max(1,len(captions))] if captions else "...")
                    prompts  = prompts[:N_IMGS]
                    captions = captions[:n_segs]
                    captions[-1] = "INSCREVA-SE AGORA 🔔"

                    print(f"   ✅ Groq Quantum: {len(prompts)} prompts + {len(captions)} captions")
                    print(f"   🎬 Hook: {hook[:60]}...")
                    print(f"   ⭐ Viral: {viral.get('description','')[:60]}")
                    return prompts, captions, hook, viral, arc_ups
        except Exception as e:
            print(f"   Groq tentativa {attempt+1}: {e}")
            time.sleep(8)

    return gerar_quantum_fallback()

def gerar_quantum_fallback():
    STYLE = "cream background #F5F0E8, no text, original design, not based on any IP"
    d = next((c for c in CHARACTERS if c["slug"]=="daniela"), CHARACTERS[0])
    s = next((c for c in CHARACTERS if c["slug"]=="sara"), CHARACTERS[1] if len(CHARACTERS)>1 else CHARACTERS[0])
    a = next((c for c in CHARACTERS if c["slug"]=="ana"), None)
    m = next((c for c in CHARACTERS if c["slug"]=="marcos"), None)

    dv = d["visual"]; sv = s["visual"]
    av = a["visual"] if a else "chibi woman lab coat"
    mv = m["visual"] if m else "chibi man dark suit"

    templates = [
        f"{dv} and {sv} sitting close, {sv} showing {dv} something on phone worried expression, {STYLE}",
        f"{dv} direct gaze viewer warm knowing smile hand on chest 'I see you', {STYLE}",
        f"{sv} and {mv} at table, {mv} charming smile but shadow behind him, {sv} uncertain, {STYLE}",
        f"{dv} and {av} side by side {av} showing brain diagram {dv} nodding seriously, {STYLE}",
        f"{sv} looking in mirror reflection shows stronger version {dv} behind her smiling proud, {STYLE}",
        f"{sv} hands shaking {dv} gently holding them steady eye contact 'you can do this', {STYLE}",
        f"{mv} puppet strings above head invisible {sv} finally seeing them horrified, {STYLE}",
        f"{dv} {sv} {av} three together arms around shoulders community warmth golden light, {STYLE}",
        f"{sv} cutting invisible strings fist raised {dv} celebrating beside her confetti, {STYLE}",
        f"giant golden bell confetti {dv} {sv} arms raised subscribe celebrate together, {STYLE}",
    ] * (N_IMGS // 10 + 2)

    cap_bank = [
        "Você reconhece?","E com você?","Olha isso","Deixa eu contar","Isso muda tudo",
        "Você sabia?","Aqui está a chave","O sinal","Cuidado!","A ciência explica",
        "Seu cérebro","É real","Você pode!","Proteja-se","A máscara caiu",
        "Crescendo","Você decide","Compartilha","Você merece","INSCREVA-SE AGORA 🔔"
    ]

    captions = [cap_bank[i % len(cap_bank)] for i in range(n_segs)]
    captions[-1] = "INSCREVA-SE AGORA 🔔"
    hook = "Na semana que vem, Sara vai descobrir algo que vai mudar tudo..."
    viral = {"prompt_index":4, "description":"Sara vê reflexo mais forte", "caption":"Você já se viu assim?"}
    arc_ups = [{"character_slug":"sara","new_stage":2,"emotional_state":"awakening",
                "story_note":"Sara começou a perceber o padrão","visual_change":"Postura levemente mais ereta"}]

    return templates[:N_IMGS], captions, hook, viral, arc_ups

print(f"\n🧠 Groq Quantum: {N_IMGS} prompts + {n_segs} captions + hooks...")
t_groq = time.time()
IMAGE_PROMPTS, CAPTIONS, CLIFFHANGER_HOOK, VIRAL_MOMENT, ARC_UPDATES = gerar_quantum_groq()
print(f"   {time.time()-t_groq:.1f}s")

# ── GERAÇÃO DE IMAGENS QUANTUM ────────────────────────────────────
def gen_image(prompt, idx):
    full_prompt = (
        "Psych2Go inspired chibi animation style, TWO OR MORE kawaii anime characters "
        "with emotionally resonant interaction, clear facial expressions matching the emotion, "
        f"dynamic body language telling the story. Scene: {prompt}. "
        "Original character designs not based on any existing franchise or IP, "
        "no text, no words, no logos, no watermarks, high quality chibi flat design art, "
        "cream warm background #F5F0E8."
    )

    # 1. Pollinations.ai Flux + enhance
    try:
        enc = urllib.parse.quote(full_prompt)
        seed = 500 + idx * 13
        url = (f"https://image.pollinations.ai/prompt/{enc}"
               f"?width=576&height=1024&seed={seed}&nologo=true&model=flux&enhance=true")
        r = requests.get(url, timeout=100)
        if r.status_code == 402: time.sleep(25); r = requests.get(url, timeout=100)
        if r.status_code == 200 and r.headers.get('content-type','').startswith('image'):
            tmp = f"{WORKDIR}/raw_{idx:04d}.jpg"
            with open(tmp,"wb") as f: f.write(r.content)
            img = Image.open(tmp).convert("RGB").resize((W,H),Image.LANCZOS)
            out = f"{WORKDIR}/pool_{idx:04d}.jpg"
            img.save(out,"JPEG",quality=93); return out, "pollinations"
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
                                img.save(out,"JPEG",quality=93); return out, "gemini"
            except Exception: continue

    # 3. Pillow — 2 personagens com personalidade visual
    chars = CHARACTERS
    c1 = chars[idx % len(chars)]; c2 = chars[(idx+3) % len(chars)]
    cores = [(130,80,200),(80,130,200),(200,80,130),(80,200,130),(200,150,80),
             (160,80,200),(80,160,200),(200,80,160),(80,200,160),(200,160,80),
             (100,180,200),(200,100,180),(180,200,100),(120,120,200),(200,120,120)]
    img = Image.new("RGB",(W,H),(245,240,232))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t=y/H; rv=int(245+(232-245)*t); gv=int(240+(225-240)*t); bv=int(232+(218-232)*t)
        draw.line([(0,y),(W,y)],fill=(rv,gv,bv))
    # Chibi 1
    x1=W//3; cy=H//2
    c1_color=cores[idx%len(cores)]
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
    x2=2*W//3; c2_color=cores[(idx+4)%len(cores)]
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
    draw.text((x1-25,cy+255),c1["name"][:8].upper(),fill=(255,255,255))
    draw.text((x2-25,cy+255),c2["name"][:8].upper(),fill=(255,255,255))
    out = f"{WORKDIR}/pool_{idx:04d}.jpg"; img.save(out,"JPEG",quality=85)
    return out, "pillow"

# ── OVERLAY PADRÃO ETERNO ─────────────────────────────────────────
def add_base_overlay(img_path):
    img = Image.open(img_path).convert("RGB"); draw = ImageDraw.Draw(img)
    lt_h = 95
    draw.rectangle([0,H-lt_h,W,H],fill=(8,6,18))
    draw.rectangle([0,H-lt_h,5,H],fill=VERM)
    draw.text((22,H-lt_h+12),"psi",fill=GOLD)
    draw.text((62,H-lt_h+10),"Daniela Coelho",fill=BRAN)
    draw.text((62,H-lt_h+40),"Saude Mental  |  @psidanielacoelho",fill=LILAS)
    draw.rectangle([0,H-4,W,H],fill=VERM)
    img.save(img_path,"JPEG",quality=95); return img_path

def make_frame(pool_path, caption, seg_idx, is_viral=False):
    frame_path = f"{WORKDIR}/frame_{seg_idx:05d}.jpg"
    img = Image.open(pool_path).convert("RGB"); draw = ImageDraw.Draw(img)
    if caption:
        cap = caption[:28].upper()
        cap_w = min(len(cap)*14+44, W-60)
        cx = W//2; cap_y = 56
        # Moldura especial para momentos virais
        fill_col = (255,235,235) if is_viral else (245,245,255)
        border_col = (220,50,50) if is_viral else (200,200,220)
        draw.rounded_rectangle([cx-cap_w//2,cap_y-24,cx+cap_w//2,cap_y+24],
                                radius=15, fill=fill_col)
        draw.rounded_rectangle([cx-cap_w//2,cap_y-24,cx+cap_w//2,cap_y+24],
                                radius=15, outline=border_col, width=2 if not is_viral else 3)
        draw.text((cx-cap_w//2+22,cap_y-10), cap, fill=(20,15,45))
    img.save(frame_path,"JPEG",quality=90); return frame_path

# GERAR POOL (8 workers)
print(f"\n🎨 Gerando {N_IMGS} chibis únicos ({WORKERS} workers)...")
t0 = time.time()
POOL = [None]*N_IMGS
counts = {"pollinations":0,"gemini":0,"pillow":0}
viral_idx = VIRAL_MOMENT.get("prompt_index", N_IMGS-1) if VIRAL_MOMENT else N_IMGS-1

def gen_pool_img(args):
    i, prompt = args
    path, src = gen_image(prompt, i)
    add_base_overlay(path)
    sz = os.path.getsize(path)//1024
    icon = "✅" if src != "pillow" else "⚠️"
    viral_tag = " ⭐VIRAL" if i == viral_idx else ""
    print(f"   [{i+1:03d}/{N_IMGS}] {icon} {src} ({sz}KB){viral_tag}")
    return path, src

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(gen_pool_img,(i,p)):i for i,p in enumerate(IMAGE_PROMPTS)}
    for fut in as_completed(futures):
        i = futures[fut]
        path, src = fut.result()
        POOL[i] = path
        counts[src] = counts.get(src,0) + 1
        time.sleep(0.5)

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
    ar = requests.get(video["audio_url"], timeout=120); ar.raise_for_status()
    with open(f"{WORKDIR}/audio.mp3","wb") as f: f.write(ar.content)
    print("   Usando áudio existente...")
else:
    asyncio.run(_tts())

probe = subprocess.run(["ffprobe","-v","quiet","-print_format","json",
    "-show_format",f"{WORKDIR}/audio.mp3"],capture_output=True,text=True)
DUR_AUDIO = float(json.loads(probe.stdout)["format"]["duration"])
RATE_REAL = len(script_tts) / DUR_AUDIO
N_IMGS_REAL = max(20, int(DUR_AUDIO / 15))
print(f"   {DUR_AUDIO:.1f}s ({DUR_AUDIO/60:.1f}min) | RATE_REAL={RATE_REAL:.3f}")
if N_IMGS_REAL != N_IMGS:
    print(f"   Ajuste N_IMGS: {N_IMGS}→{N_IMGS_REAL} (áudio real)")

# ── TIMING + FRAMES ───────────────────────────────────────────────
seg_size = max(1, len(script_tts) // n_segs)
durs = [max(0.5, round(max(1,seg_size)/RATE_REAL, 3)) for _ in range(n_segs)]
pool_size = len([p for p in POOL if p])

print(f"\n🖼️  Gerando {n_segs} frames (palavra a palavra)...")
FRAMES = []
for i in range(n_segs):
    pool_idx = (i // SEGS_PER_IMG) % pool_size
    caption  = CAPTIONS[i] if i < len(CAPTIONS) else ""
    is_viral = (i // SEGS_PER_IMG) == viral_idx
    frame    = make_frame(POOL[pool_idx], caption, i, is_viral)
    FRAMES.append(frame)
    if (i+1) % 100 == 0: print(f"   {i+1}/{n_segs}...")
print(f"   ✅ {len(FRAMES)} frames")

# ── FFCONCAT + RENDER ─────────────────────────────────────────────
concat_file = f"{WORKDIR}/concat.txt"
with open(concat_file,"w") as f:
    for frame,dur in zip(FRAMES,durs): f.write(f"file '{frame}'\nduration {dur:.3f}\n")
    if FRAMES: f.write(f"file '{FRAMES[-1]}'\n")

print(f"\n🎬 Renderizando (crf={CRF})...")
ts = int(time.time())
out_mp4 = f"{WORKDIR}/v{VIDEO_ID}_quantum_{ts}.mp4"

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

# ── UPLOAD ────────────────────────────────────────────────────────
print(f"\n☁️  Upload...")
if not video.get("audio_url"):
    with open(f"{WORKDIR}/audio.mp3","rb") as f: adata = f.read()
    audio_url = sb_upload(f"audios/v{VIDEO_ID}_quantum_{ts}.mp3",adata,"audio/mpeg")
    sb_patch("content_pipeline",VIDEO_ID,{"audio_url":audio_url})

with open(out_mp4,"rb") as f: vdata = f.read()
video_url = None
for attempt in range(5):
    try:
        video_url = sb_upload(f"mp4s/v{VIDEO_ID}_quantum_{ts}.mp4",vdata,"video/mp4")
        print("   ✅ Upload OK"); break
    except Exception as e: print(f"   Tentativa {attempt+1}: {e}"); time.sleep(12)

# ── SALVAR ARCOS + HOOKS + VIRAL NO DB ───────────────────────────
print(f"\n💾 Salvando arcos + hooks no universo...")

# Salvar arcos dos personagens
for arc in ARC_UPDATES:
    try:
        sb_upsert("character_story_arc", {
            "character_slug": arc.get("character_slug"),
            "video_id": VIDEO_ID,
            "emotional_state": arc.get("emotional_state","neutral"),
            "arc_stage": arc.get("new_stage",1),
            "story_note": arc.get("story_note",""),
            "visible_change": arc.get("visual_change",""),
        })
        # Atualizar memória do universo
        requests.patch(
            f"{SB_URL}/rest/v1/universe_memory?character_slug=eq.{arc.get('character_slug')}",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                     "Content-Type":"application/json","Prefer":"return=minimal"},
            json={"current_stage": arc.get("new_stage",1),
                  "last_video_id": VIDEO_ID,
                  "visual_evolution": arc.get("visual_change",""),
                  "updated_at": "now()"},
            timeout=10)
    except Exception as e: print(f"   Arc save error: {e}")

# Salvar cliffhanger hook
if CLIFFHANGER_HOOK:
    try:
        requests.post(f"{SB_URL}/rest/v1/episode_hooks",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                     "Content-Type":"application/json","Prefer":"return=minimal"},
            json={"video_id":VIDEO_ID,"hook_type":"end_teaser",
                  "hook_text":CLIFFHANGER_HOOK,
                  "visual_prompt":IMAGE_PROMPTS[-2] if len(IMAGE_PROMPTS)>=2 else ""},
            timeout=10)
        print(f"   ✅ Hook: {CLIFFHANGER_HOOK[:60]}...")
    except Exception as e: print(f"   Hook save error: {e}")

# Salvar momento viral
if VIRAL_MOMENT:
    try:
        requests.post(f"{SB_URL}/rest/v1/viral_moments",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                     "Content-Type":"application/json","Prefer":"return=minimal"},
            json={"video_id":VIDEO_ID,"moment_type":"revelation",
                  "description":VIRAL_MOMENT.get("description",""),
                  "caption_text":VIRAL_MOMENT.get("caption",""),
                  "clip_potential":8},
            timeout=10)
        print(f"   ✅ Viral moment salvo")
    except Exception as e: print(f"   Viral moment error: {e}")

# ── UPDATE DB PRINCIPAL ───────────────────────────────────────────
if video_url:
    sb_patch("content_pipeline",VIDEO_ID,{
        "video_url": video_url, "status": "pending_credentials",
        "metadata": json.dumps({
            "render_version": "v8_quantum_universe",
            "n_imgs": N_IMGS, "n_ai": ai_total,
            "n_segments": n_segs,
            "characters": char_slugs,
            "cliffhanger": CLIFFHANGER_HOOK,
            "viral_moment": VIRAL_MOMENT.get("description",""),
            "arc_updates": len(ARC_UPDATES),
            "audio_dur_min": round(DUR_AUDIO/60,1),
            "video_dur_min": round(dur2/60,1),
            "file_mb": round(sz/1024/1024,1),
            "crf": CRF, "rate_real": round(RATE_REAL,3),
        })
    })

print(f"\n{'═'*60}")
print(f"  ✅ QUANTUM UNIVERSE — #{VIDEO_ID}")
print(f"  {ai_total}/{N_IMGS} AI chibi | {sz//1024//1024}MB | {dur2/60:.1f}min")
print(f"  Arcos salvos: {len(ARC_UPDATES)} | Hook: {bool(CLIFFHANGER_HOOK)}")
print(f"  🎬 {video_url}")
print(f"{'═'*60}\n")
