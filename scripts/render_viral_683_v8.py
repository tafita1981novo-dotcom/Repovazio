#!/usr/bin/env python3
"""render_viral_683_v8.py
V8 EXTREMA QUALIDADE — GEMINI AI IMAGES + FFCONCAT TIMING
- 21 cenas com imagens AI real (Gemini 2.5 Flash Image / Gemini 3 Pro Image)
- Personagens chibi profissional MELHOR que Psych2Go
- Timing ffconcat por frase (12.77 chars/s George)
- Pillow overlay: lower third + captions
- Fallback Pillow V7 se Gemini falhar
- $0 custo (Google AI Studio free tier)
"""
import os,sys,json,math,time,base64,subprocess,requests
from PIL import Image,ImageDraw,ImageFont
from concurrent.futures import ThreadPoolExecutor,as_completed

SB_URL=os.environ.get("SUPABASE_URL","")
SB_KEY=os.environ.get("SUPABASE_KEY","")
GEMINI_KEY=os.environ.get("GEMINI_API_KEY","")
W,H=1080,1920
os.makedirs("/tmp/v8",exist_ok=True)

# ──── GEMINI AI IMAGE GENERATION ────
GEMINI_MODELS=[
    "gemini-2.5-flash-image",          # rápido, ótima qualidade
    "gemini-3.1-flash-image-preview",   # bom fallback
]

def gen_gemini(prompt, scene_idx, model=None):
    """Gera imagem AI via Gemini. Retorna path da imagem ou None."""
    if not GEMINI_KEY:
        return None
    models = [model] if model else GEMINI_MODELS
    for mdl in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent?key={GEMINI_KEY}"
        payload = {
            "contents":[{"parts":[{"text":prompt}]}],
            "generationConfig":{"responseModalities":["IMAGE","TEXT"]}
        }
        try:
            r = requests.post(url, json=payload, timeout=60)
            if r.status_code == 200:
                for cand in r.json().get("candidates",[]):
                    for part in cand.get("content",{}).get("parts",[]):
                        if "inlineData" in part:
                            raw = base64.b64decode(part["inlineData"]["data"])
                            # Salva e resize para 1080x1920
                            tmp = f"/tmp/v8/ai_raw_{scene_idx:02d}.jpg"
                            with open(tmp,"wb") as f: f.write(raw)
                            img = Image.open(tmp).convert("RGB")
                            # Crop/resize para 9:16
                            aw,ah = img.size
                            if aw/ah > 9/16:  # muito largo
                                nw = int(ah*9/16)
                                img = img.crop(((aw-nw)//2,0,(aw+nw)//2,ah))
                            elif aw/ah < 9/16:  # muito alto
                                nh = int(aw*16/9)
                                img = img.crop((0,(ah-nh)//2,aw,(ah+nh)//2))
                            img = img.resize((W,H),Image.LANCZOS)
                            out = f"/tmp/v8/ai_{scene_idx:02d}.jpg"
                            img.save(out,"JPEG",quality=93)
                            return out
            elif r.status_code == 429:
                time.sleep(8)  # rate limit
        except Exception as e:
            pass
    return None

# ──── LOWER THIRD E CAPTIONS (Pillow overlay) ────
VERM=(220,50,50);AM=(255,210,50);BR=(255,255,255);ES=(10,8,8)

def overlay_lt(img_path, caption_text=None):
    """Adiciona lower third e caption opcional em cima da imagem AI."""
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    lt_h = 95
    # Fundo lower third direto (sem fromarray)
    draw.rectangle([0,H-lt_h,W,H],fill=(8,6,18))
    draw.rectangle([0,H-lt_h,5,H],fill=VERM)
    draw.text((22,H-lt_h+12),"psi",fill=AM)
    draw.text((62,H-lt_h+10),"Daniela Coelho",fill=BR)
    draw.text((62,H-lt_h+40),"Saude Mental  |  @psidanielacoelho",fill=(185,170,225))
    draw.rectangle([0,H-4,W,H],fill=VERM)
    
    # Badge caption no topo com texto preto em fundo semi-branco
    if caption_text:
        cap_words = caption_text[:32]
        cap_w = min(len(cap_words)*14+44, W-60)
        cx = W//2; cap_y = 56
        draw.rounded_rectangle([cx-cap_w//2,cap_y-24,cx+cap_w//2,cap_y+24],
                                 radius=15,fill=(245,245,255))
        draw.rounded_rectangle([cx-cap_w//2,cap_y-24,cx+cap_w//2,cap_y+24],
                                 radius=15,outline=(200,200,220),width=2)
        draw.text((cx-cap_w//2+22,cap_y-10),cap_words,fill=(20,15,45))
    
    img.save(img_path,"JPEG",quality=95)
    return img_path

# ──── FALLBACK PILLOW ────
def make_pillow_fallback(idx, pal_idx, caption):
    """Fallback Pillow melhorado se Gemini falhar"""
    from PIL import Image, ImageDraw
    
    PALS=[(15,12,30),(200,20,20),(8,18,75),(220,100,20),(55,8,8),
          (200,160,10),(160,30,30),(35,35,75),(0,130,120),(65,15,95),
          (15,150,70),(220,170,0)]
    ct = PALS[pal_idx % len(PALS)]
    cb = tuple(max(0,c-40) for c in ct)
    
    img = Image.new("RGB",(W,H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t=y/H; c=tuple(int(ct[i]*(1-t)+cb[i]*t) for i in range(3))
        draw.line([(0,y),(W,y)],fill=c)
    
    # Personagem simples central
    cx,cy=W//2,int(H*0.65)
    sc=2.2
    hr=int(55*sc);bw=int(88*sc);bh=int(115*sc)
    pr=(222,175,132);cr=(140,90,40);ro=(220,80,100)
    draw.rounded_rectangle([cx-bw//2,cy-bh,cx+bw//2,cy],radius=20,fill=ro)
    draw.ellipse([cx-hr,cy-bh-hr*2+15,cx+hr,cy-bh+15],fill=pr)
    draw.ellipse([cx-hr-5,cy-bh-hr*2+5,cx+hr+5,cy-bh-int(hr*0.22)],fill=cr)
    
    # Caption
    draw.text((W//2-80,int(H*0.20)),caption[:20],fill=BR)
    out=f"/tmp/v8/fallback_{idx:02d}.jpg"
    img.save(out,"JPEG",quality=85)
    return out

# ──── 21 CENAS COM PROMPTS GEMINI ────
BASE_RENATA = "chibi anime girl, short brown hair bob cut, warm beige skin tone, pink blouse, large expressive brown eyes, rosy cheeks, kawaii flat design illustration, psychology animation style, vertical 9:16 portrait, clean line art, soft warm cream white background with pastel decorations, no text, no words, no letters"
BASE_LUCAS  = "chibi anime boy, slick dark hair, light skin, navy blue shirt, charming smile, large eyes, kawaii flat design illustration, psychology animation style, vertical 9:16 portrait, clean line art, soft warm cream white background with pastel decorations, no text, no words, no letters"

CENAS=[
  # (idx, frase, dur_s, palette, prompt_gemini, caption_badge)
  (1, "Voce acha que reconheceria um narcisista?", 3.29, 0,
   f"{BASE_RENATA}, shocked surprised expression, hands on cheeks, large white question mark floating above head, sparkle elements, concerned wide eyes",
   "VOCÊ SABERIA RECONHECER?"),

  (2, "9 em 10 pessoas nao reconhecem.", 2.51, 1,
   "three chibi anime people standing in a row on cream background, one person on the right has dark circle highlight around them with a subtle sinister smile, the others look normal and unaware, kawaii flat design psychology, no text, no words, vertical 9:16",
   "9 EM 10 NÃO PERCEBEM"),

  (3, "O narcisismo encoberto nao grita.", 2.59, 2,
   "large megaphone with a big red X crossing it out, no sound waves, silence symbol, soft blue-gray cream background, kawaii flat design illustration, centered composition, vertical 9:16, no text, no words",
   "NÃO GRITA..."),

  (4, "Ele sussurra.", 1.02, 2,
   f"{BASE_LUCAS}, finger to lips shushing gesture, small subtle speech bubble with tiny whisper lines, dark blue-gray background with soft glow, sneaky expression",
   "...ELE SUSSURRA"),

  (5, "Renata, 34, designer, casada com Lucas.", 3.13, 3,
   "two chibi anime characters side by side, left: chibi girl short brown hair pink blouse warm expression, right: chibi boy dark hair navy shirt charming smile, golden wedding ring between them, subtle cracked heart behind them, warm orange-peach cream background, kawaii flat design, vertical 9:16, no text",
   "RENATA E LUCAS"),

  (6, "Por fora perfeito.", 1.41, 3,
   f"{BASE_LUCAS}, smug perfect confident smile, golden sparkling stars orbiting around him, sunburst rays in warm gold, trophy sparkles, appearing flawless, yellow-gold warm background",
   "POR FORA: PERFEITO"),

  (7, "Por dentro ela enlouquecia.", 2.11, 4,
   f"{BASE_RENATA}, dizzy confused expression with spiral eyes, chaotic swirling red and purple lines around head, dark wine-red background with stress elements, overwhelmed pose",
   "POR DENTRO: CAOS"),

  (8, "Aguarda. Isso e mais comum do que parece.", 3.21, 5,
   "large STOP hand gesture in center, multiple chibi silhouettes behind it in amber-gold light, warning feel, kawaii flat design psychology illustration, amber warm background, no text, vertical 9:16",
   "ISSO É MAIS COMUM"),

  (9, "Sinal 1: Ele esquece tudo que voce fala", 3.13, 5,
   f"red badge with number 1 at top reading SINAL, {BASE_RENATA}, talking animatedly with speech bubble above her, but the speech bubble is completely empty erased, confused expression, golden amber background",
   "⚠️ SINAL 1"),

  (10, "mas lembra quando precisa te culpar.", 2.82, 1,
   f"chibi anime boy turned away with arms crossed, pointing finger accusingly back toward chibi girl who looks sad and small, red blame arrow pointing at girl, dark red cream background, kawaii flat design psychology, vertical 9:16, no text",
   "CULPA É SEMPRE SUA"),

  (11, "Sinal 2: Suas conquistas viram historia dele.", 3.60, 6,
   f"orange badge with number 2, large golden trophy in center, {BASE_LUCAS} smugly placing hand on trophy claiming it, small sad chibi girl beside him looking down, warm orange background, kawaii flat, no text",
   "⚠️ SINAL 2"),

  (12, "Sinal 3: Voce sai exausta e sempre sentindo que errou.", 4.31, 7,
   f"purple badge with number 3, {BASE_RENATA}, exhausted drooping posture, heavy grey weights pressing down on shoulders, dark circles under eyes, lavender purple background with stress swirls, kawaii flat design",
   "⚠️ SINAL 3"),

  (13, "Dr. Ramani - UCLA: dreno emocional sistematico.", 3.76, 8,
   "professional chibi woman in white lab coat, calm authoritative expression, brain illustration beside her with energy draining out via downward arrows, scientific diagram feel, teal mint background, kawaii flat design psychology, vertical 9:16, no text",
   "DR. RAMANI | UCLA"),

  (14, "E real. Nao e exagero.", 1.80, 8,
   f"large bold green checkmark circle in center with glowing light, {BASE_RENATA} raising fist empowerment beside it, validation symbol, mint teal background, kawaii flat design, vertical 9:16, no text",
   "É REAL. É SÉRIO."),

  (15, "Isso nao e amor dificil.", 1.88, 9,
   "large red heart with thick black X crossing through it, surrounded by scattered broken heart pieces, dark violet-purple background, kawaii flat design illustration, vertical 9:16, no text",
   "ISSO NÃO É AMOR"),

  (16, "E manipulacao com rosto gentil.", 2.43, 9,
   f"{BASE_LUCAS}, holding a smiling theater mask in front of face, one charming eye visible behind, dark sinister shadow behind him contrasting with the friendly mask, violet-dark background, kawaii flat design",
   "MÁSCARA DE GENTILEZA"),

  (17, "Manda esse video pra quem precisa.", 2.66, 2,
   "chibi hands holding smartphone with glowing screen showing a heart and share arrow, blue glow emanating, send motion lines, speech bubble with forward arrow, dark navy blue background, kawaii flat design, vertical 9:16, no text",
   "MANDA PRA ALGUÉM"),

  (18, "Inscreva-se.", 0.94, 11,
   "giant golden bell with musical notes floating around it, rainbow confetti celebration, subscribe ribbon banner below bell (no text on ribbon), vibrant golden orange background, kawaii flat design celebration, vertical 9:16, no text",
   "🔔 INSCREVA-SE"),

  (19, "Voce merece um amor que nao esgota.", 2.82, 10,
   f"{BASE_RENATA}, joyful happy expression, arms wide open, surrounded by floating pink and red hearts of various sizes, warm soft green background with flower petals, celebratory empowering mood",
   "VOCÊ MERECE AMOR"),

  (20, "Um amor que te ve e te ouve.", 3.68, 10,
   "chibi anime girl with warm loving expression, one gentle eye symbol and one ear symbol glowing with golden light beside her, rays of golden warmth, soft green mint background, kawaii flat design psychology, vertical 9:16, no text",
   "QUE TE VÊ E OUVE"),

  (21, "Proximo episodio — inscreva-se agora", 5.39, 11,
   f"{BASE_RENATA}, big warm welcoming smile, arms slightly open inviting, golden bell beside her, star sparkles around, rich warm golden background, cheerful celebratory mood, subscribe energy",
   "PRÓXIMO EPISÓDIO →"),
]

print(f"=== RENDER V8: GEMINI AI + FFCONCAT | 21 CENAS ===")

# ──── GERAÇÃO PARALELA DAS IMAGENS ────
def generate_scene(scene_def):
    idx, frase, dur, pal, prompt, caption = scene_def
    print(f"  Gerando cena {idx:02d}...")
    
    # Tentar Gemini
    ai_path = gen_gemini(prompt, idx)
    
    if ai_path:
        # Adicionar lower third e caption
        overlay_lt(ai_path, caption)
        print(f"  ✅ [{idx:02d}] AI GEMINI: {os.path.getsize(ai_path)//1024}KB")
        return ai_path, dur
    else:
        # Fallback Pillow
        fb = make_pillow_fallback(idx, pal, caption)
        overlay_lt(fb, caption)
        print(f"  ⚠️ [{idx:02d}] FALLBACK PILLOW")
        return fb, dur

# Geração com 4 workers paralelos
t0 = time.time()
imgs = [None] * len(CENAS)
with ThreadPoolExecutor(max_workers=4) as ex:
    futures = {ex.submit(generate_scene, c): i for i, c in enumerate(CENAS)}
    for future in as_completed(futures):
        i = futures[future]
        imgs[i] = future.result()

gen_time = time.time()-t0
n_ai = sum(1 for p,d in imgs if p and "ai_" in p)
print(f"\n{n_ai}/{len(CENAS)} imagens AI em {gen_time:.1f}s")

# ──── AUDIO ────
r=requests.get(f"{SB_URL}/rest/v1/content_pipeline",params={"select":"audio_url","id":"eq.683"},
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"})
audio_url=r.json()[0]["audio_url"]
r2=requests.get(audio_url,headers={"apikey":SB_KEY},timeout=90)
with open("/tmp/v8/audio.mp3","wb") as f: f.write(r2.content)
probe=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",
    "/tmp/v8/audio.mp3"],capture_output=True,text=True)
ADU=float(json.loads(probe.stdout)["format"]["duration"])
print(f"Audio: {ADU:.1f}s")

# ──── FFCONCAT ────
with open("/tmp/v8/concat.txt","w") as f:
    for img_path,dur in imgs:
        f.write(f"file '{img_path}'\nduration {dur:.3f}\n")
    f.write(f"file '{imgs[-1][0]}'\n")
print("ffconcat pronto")

# ──── RENDER ────
print("Renderizando...")
cmd=["ffmpeg","-y",
     "-f","concat","-safe","0","-i","/tmp/v8/concat.txt",
     "-i","/tmp/v8/audio.mp3",
     "-c:v","libx264","-pix_fmt","yuv420p",
     "-c:a","aac","-b:a","128k",
     "-t","58",
     "-r","25","-crf","18",
     "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1",
     "-movflags","+faststart",
     "/tmp/v8/viral_v8.mp4"]
res=subprocess.run(cmd,capture_output=True,text=True,timeout=480)
if res.returncode!=0:
    print("ERRO FFMPEG:"); print(res.stderr[-3000:]); sys.exit(1)

sz=os.path.getsize("/tmp/v8/viral_v8.mp4")
probe2=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",
    "/tmp/v8/viral_v8.mp4"],capture_output=True,text=True)
dur2=float(json.loads(probe2.stdout)["format"]["duration"])
print(f"MP4: {sz//1024}KB | {dur2:.1f}s")

# ──── UPLOAD ────
fname=f"mp4s/v683_viral_v8_{int(time.time())}.mp4"
with open("/tmp/v8/viral_v8.mp4","rb") as f: data=f.read()
mp4_url=None
for t in range(6):
    r3=requests.post(f"{SB_URL}/storage/v1/object/videos/{fname}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"video/mp4","x-upsert":"true"},
        data=data,timeout=420)
    if r3.status_code in[200,201]:
        mp4_url=f"{SB_URL}/storage/v1/object/public/videos/{fname}"
        print(f"Upload OK"); break
    print(f"  upload {t+1}: {r3.status_code}"); time.sleep(6)

if mp4_url:
    r4=requests.patch(f"{SB_URL}/rest/v1/content_pipeline?id=eq.683",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"},
        data=json.dumps({"mp4_url":mp4_url,"status":"pending_credentials",
                         "metadata":{"render_version":"v8_gemini_ai_extrema",
                                     "n_ai_cenas":n_ai,"gemini_model":"gemini-2.5-flash-image",
                                     "gen_time_s":round(gen_time,1)}}),timeout=30)
    print(f"DB: {r4.status_code} — {mp4_url[-55:]}")
print("=== CONCLUIDO V8 ===")
