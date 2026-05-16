#!/usr/bin/env python3
"""
render_683_superior.py — VÍDEO 1 SUPERIOR AO V8 FINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Script dedicado para gerar o vídeo #683 com QUALIDADE MÁXIMA.
Objetivo: superar v683_viral_v8_1778892031.mp4 (6.3MB, 62s).

Melhorias vs V8 Final:
  - Script: 2204 chars (vs 829) = mais cenas = mais variação
  - 33 cenas únicas (vs 20) = mais dinamismo
  - Prompts ultra-detalhados com personagens do universo
  - Pollinations Flux com enhance=true + seed único por cena
  - RATE_REAL dinâmico (igual ao V8 Final)
  - Mesmo lower third e caption badge padrão eterno
"""
import os, sys, json, re, time, base64, asyncio, subprocess, requests, urllib.parse
from PIL import Image, ImageDraw
from concurrent.futures import ThreadPoolExecutor, as_completed

VIDEO_ID   = 683
SB_URL     = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY     = os.environ.get("SUPABASE_SERVICE_KEY","")
GEMINI_KEYS= [k for k in [os.environ.get("GEMINI_API_KEY",""),
              os.environ.get("GEMINI_API_KEY_2","")] if k]

W, H    = 1080, 1920
CRF     = 22        # qualidade máxima (V8 Final usava 25)
WORKDIR = f"/tmp/v683_superior"
os.makedirs(WORKDIR, exist_ok=True)

VERM = (220,50,50); GOLD=(255,210,50); BRAN=(255,255,255); LILAS=(185,170,225)

GEMINI_MODELS = ["gemini-2.0-flash-exp","gemini-2.0-flash-exp-image-generation"]
_gk=[0]
def gkey(): return GEMINI_KEYS[_gk[0]%len(GEMINI_KEYS)] if GEMINI_KEYS else None
def rotk(): _gk[0]+=1

def sb_get(table, qs):
    r=requests.get(f"{SB_URL}/rest/v1/{table}?{qs}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"},timeout=30)
    r.raise_for_status(); return r.json()

def sb_patch(table,id_,data):
    r=requests.patch(f"{SB_URL}/rest/v1/{table}?id=eq.{id_}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"},
        json=data,timeout=30); r.raise_for_status()

def sb_upload(path,data,ctype):
    r=requests.post(f"{SB_URL}/storage/v1/object/videos/{path}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":ctype,"x-upsert":"true"},
        data=data,timeout=360); r.raise_for_status()
    return f"{SB_URL}/storage/v1/object/public/videos/{path}"

# Carregar dados
rows = sb_get("content_pipeline",f"id=eq.{VIDEO_ID}&select=id,title,script,audio_url")
video = rows[0]
script_tts = video["script"].strip()

print(f"{'='*55}")
print(f"  ψ VÍDEO 1 SUPERIOR — #683")
print(f"  {len(script_tts)} chars | objetivo: superar 6.3MB V8 Final")
print(f"{'='*55}\n")

# PROMPTS ULTRA-DETALHADOS por cena (personagens do universo)
# Baseados nos 33 parágrafos do script
DANIELA = "chibi anime girl, short sleek dark bob hair, warm honey-brown eyes, soft professional mint-green blouse, small gold psi pin on collar, warm reassuring dimpled smile"
SARA    = "chibi anime girl, long wavy auburn hair, round thin-framed glasses, pale yellow cardigan, sad expressive eyes gradually becoming stronger"
MARCOS  = "chibi anime man, perfectly styled dark hair swept back, charming calculated smile, expensive dark navy blazer, one eyebrow subtly raised"
JULIA   = "chibi anime girl, bouncy curly dark hair with small flower clip, warm orange knit sweater, bright enthusiastic caring eyes"
ANA     = "chibi anime woman, neat dark bun, white lab coat with name tag, clipboard in hand, calm authoritative warm expression, reading glasses"
STYLE   = "Psych2Go animation style, kawaii chibi flat design, cream warm background #F5F0E8, pastel colors, clean line art, original design not based on any IP, no text, no logos"

SCENE_PROMPTS = [
    # Cena 1: celular
    f"{SARA} alone at night holding phone with anxious expression, message bubble showing '...' dots waiting, soft blue phone glow, {STYLE}",
    # Cena 2: desculpa
    f"{SARA} reading phone message, face falling in disappointment, small sad cloud above head, {STYLE}",
    # Cena 3: Sara conhece Marcos
    f"{SARA} and {MARCOS} at a party, he is charming with sparkles around him, she looks captivated hopeful, {STYLE}",
    # Cena 4: algo errado
    f"{SARA} looking thoughtful with small question marks floating, {MARCOS} in background with subtle shadow, {STYLE}",
    # Cena 5: Daniela pergunta
    f"{DANIELA} looking directly forward with warm knowing smile, hand gently reaching toward viewer, {STYLE}",
    # Cena 6: sempre errada
    f"{SARA} hunched shoulders, blame arrow floating toward her, {MARCOS} turned away arms crossed in background, {STYLE}",
    # Cena 7: sentimentos exagero
    f"{SARA} with speech bubble being minimized/erased, {MARCOS} waving dismissively, {STYLE}",
    # Cena 8: Harvard pesquisa
    f"{ANA} holding research clipboard with statistic, {DANIELA} beside her pointing at the data, both serious, {STYLE}",
    # Cena 9: nunca parecem narcisistas
    f"{MARCOS} wearing friendly theater mask held up, sinister shadow visible behind it, {SARA} unaware, {STYLE}",
    # Cena 10: Sinal 1
    f"large badge number 1 with {MARCOS} shrugging hands raised innocently, red X over any responsibility, {STYLE}",
    # Cena 11: Sara lembrava
    f"{SARA} touching temple remembering, memory bubble showing happy moment with {MARCOS}, confused expression, {STYLE}",
    # Cena 12: você está exagerando
    f"{MARCOS} with dismissive expression pointing at {SARA}, she is shrinking smaller, {STYLE}",
    # Cena 13: Dra. Ana explica
    f"{ANA} pointing at brain diagram with manipulation effect shown, {SARA} watching realization dawning, {STYLE}",
    # Cena 14: não é fraqueza
    f"{DANIELA} holding shield protection symbol, warm golden light around {SARA}, {STYLE}",
    # Cena 15: Sinal 2
    f"large badge number 2 with {SARA} speech bubble showing emotions, {MARCOS} looking bored, {STYLE}",
    # Cena 16: você chora
    f"{SARA} with tears, {MARCOS} sighing dramatically, gap growing between them, {STYLE}",
    # Cena 17: ansiosa dramática
    f"{MARCOS} using labels floating around {SARA}: dramatic, anxious, difficult, {SARA} confused shrinking, {STYLE}",
    # Cena 18: desculpando por sentir
    f"{SARA} with hands pressed together apologizing, her own feelings becoming small behind her, {STYLE}",
    # Cena 19: Julia notou
    f"{JULIA} looking worried at {SARA} with concerned observant expression, protective hand near {SARA}, {STYLE}",
    # Cena 20: pede desculpa por existir
    f"{JULIA} and {SARA} face to face, {JULIA} speaking with gentle urgency, {SARA} having revelation eyes wide, {STYLE}",
    # Cena 21: erosão da identidade
    f"mirror showing {SARA} original vs faded reflection, {MARCOS} in background causing the fade, {STYLE}",
    # Cena 22: Sinal 3
    f"large badge number 3, {SARA} carrying guilt weights that are not hers, {MARCOS} looking relaxed, {STYLE}",
    # Cena 23: chegava tarde
    f"{MARCOS} arriving late shrugging, {SARA} apologizing with hands out confused, clock showing late hour, {STYLE}",
    # Cena 24: esquecia compromisso
    f"{SARA} with worried hands-to-face gesture, {MARCOS} unconcerned, question mark floating toward {SARA}, {STYLE}",
    # Cena 25: precisa saber
    f"{DANIELA} urgent warm expression directly facing viewer, glowing important badge floating, {STYLE}",
    # Cena 26: só a superfície
    f"iceberg diagram, small visible part labeled 'narcisismo', massive hidden part below, {ANA} pointing, {STYLE}",
    # Cena 27: Dra. Ana ciclo
    f"{ANA} showing cycle diagram: love bomb → devalue → discard arrows, {SARA} recognizing the pattern, {STYLE}",
    # Cena 28: forma de sair
    f"{DANIELA} opening door to bright warm light, {SARA} at threshold about to step through, {STYLE}",
    # Cena 29: Daniela direto pra você
    f"{DANIELA} making eye contact directly with viewer, hand on heart sincere, warm golden light, {STYLE}",
    # Cena 30: sentimentos válidos
    f"{SARA} standing taller, {JULIA} and {DANIELA} on each side arms around shoulders, {STYLE}",
    # Cena 31: próximo vídeo
    f"{MARCOS} hiding something in shadow behind back, {SARA} about to turn and see, dramatic tension, {STYLE}",
    # Cena 32: vai mudar tudo
    f"light bulb moment, {SARA} eyes wide with revelation, everything clicking into place, {STYLE}",
    # Cena 33: inscreva-se
    f"giant golden bell with sparkles, {DANIELA} {SARA} {JULIA} {ANA} arms raised celebrating together, confetti rainbow, {STYLE}",
]

# Gerar imagens com Pollinations (alta qualidade)
def gen_image(prompt, idx):
    """Pollinations Flux com enhance=true para qualidade máxima."""
    full = (
        "Psych2Go anime style illustration, kawaii chibi characters, "
        "soft warm cream background #F5F0E8, high quality flat design, "
        f"expressive big eyes, clean lines, {prompt}, "
        "original character design, no text, no watermarks, no logos, "
        "professional illustration quality"
    )
    
    # 1. Pollinations Flux enhanced
    try:
        enc = urllib.parse.quote(full)
        seed = 777 + idx * 17
        url = (f"https://image.pollinations.ai/prompt/{enc}"
               f"?width=576&height=1024&seed={seed}&nologo=true"
               f"&model=flux&enhance=true")
        r = requests.get(url, timeout=120)
        if r.status_code == 402:
            time.sleep(30); r = requests.get(url, timeout=120)
        if r.status_code == 200 and r.headers.get('content-type','').startswith('image'):
            raw = r.content
            if len(raw) > 50000:  # pelo menos 50KB = imagem real
                tmp = f"{WORKDIR}/raw_{idx:02d}.jpg"
                with open(tmp,'wb') as f: f.write(raw)
                img = Image.open(tmp).convert("RGB").resize((W,H),Image.LANCZOS)
                out = f"{WORKDIR}/ai_{idx:02d}.jpg"
                img.save(out,"JPEG",quality=95)
                return out, "pollinations"
    except Exception as e:
        print(f"     Poll err {idx}: {e}")

    # 2. Gemini fallback
    key = gkey()
    if key:
        for model in GEMINI_MODELS:
            try:
                url2 = (f"https://generativelanguage.googleapis.com/v1beta"
                        f"/models/{model}:generateContent?key={key}")
                r2 = requests.post(url2,
                    json={"contents":[{"parts":[{"text":full}]}],
                          "generationConfig":{"responseModalities":["IMAGE","TEXT"]}},
                    timeout=90)
                if r2.status_code==429: rotk(); time.sleep(5); continue
                if r2.status_code==200:
                    for cand in r2.json().get("candidates",[]):
                        for part in cand.get("content",{}).get("parts",[]):
                            if "inlineData" in part:
                                raw = base64.b64decode(part["inlineData"]["data"])
                                tmp = f"{WORKDIR}/raw_{idx:02d}.jpg"
                                with open(tmp,'wb') as f: f.write(raw)
                                img = Image.open(tmp).convert("RGB")
                                aw,ah = img.size; t=9/16
                                if aw/ah>t:
                                    nw=int(ah*t); img=img.crop(((aw-nw)//2,0,(aw+nw)//2,ah))
                                elif aw/ah<t:
                                    nh=int(aw/t); img=img.crop((0,(ah-nh)//2,aw,(ah+nh)//2))
                                img=img.resize((W,H),Image.LANCZOS)
                                out=f"{WORKDIR}/ai_{idx:02d}.jpg"
                                img.save(out,"JPEG",quality=95)
                                return out,"gemini"
            except Exception: continue

    # 3. Pillow chibi variado (fallback digno)
    img = Image.new("RGB",(W,H),(245,240,232))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t=y/H; r=int(245+(232-245)*t); g=int(240+(225-240)*t); b=int(232+(218-232)*t)
        draw.line([(0,y),(W,y)],fill=(r,g,b))
    # 2 personagens por cena
    cores = [(130,80,200),(80,130,200),(200,80,130),(80,200,130),(200,150,80),
             (160,80,200),(80,160,200),(200,80,160),(80,200,160),(200,160,80)]
    c1=cores[idx%len(cores)]; c2=cores[(idx+4)%len(cores)]
    cx,cy=W//2,H//2
    # Char 1
    x1=W//3
    draw.ellipse([x1-90,cy-200,x1+90,cy+30],fill=(255,220,180))
    draw.ellipse([x1-95,cy-250,x1+95,cy-90],fill=(50,35,15))
    draw.ellipse([x1-45,cy-95,x1-15,cy-60],fill=(20,15,8))
    draw.ellipse([x1+15,cy-95,x1+45,cy-60],fill=(20,15,8))
    draw.ellipse([x1-40,cy-90,x1-32,cy-82],fill=(255,255,255))
    draw.ellipse([x1+20,cy-90,x1+28,cy-82],fill=(255,255,255))
    draw.arc([x1-30,cy-20,x1+30,cy+15],start=0,end=180,fill=(190,70,70),width=4)
    draw.rounded_rectangle([x1-75,cy+30,x1+75,cy+240],radius=18,fill=c1)
    draw.ellipse([x1-80,cy-50,x1-45,cy-15],fill=(255,175,175))
    draw.ellipse([x1+45,cy-50,x1+80,cy-15],fill=(255,175,175))
    # Char 2
    x2=2*W//3
    draw.ellipse([x2-90,cy-200,x2+90,cy+30],fill=(255,210,175))
    draw.ellipse([x2-95,cy-250,x2+95,cy-90],fill=(80,50,20))
    draw.ellipse([x2-45,cy-95,x2-15,cy-60],fill=(20,15,8))
    draw.ellipse([x2+15,cy-95,x2+45,cy-60],fill=(20,15,8))
    draw.ellipse([x2-40,cy-90,x2-32,cy-82],fill=(255,255,255))
    draw.ellipse([x2+20,cy-90,x2+28,cy-82],fill=(255,255,255))
    draw.arc([x2-30,cy-20,x2+30,cy+15],start=0,end=180,fill=(180,60,60),width=4)
    draw.rounded_rectangle([x2-75,cy+30,x2+75,cy+240],radius=18,fill=c2)
    draw.ellipse([x2-80,cy-50,x2-45,cy-15],fill=(255,165,165))
    draw.ellipse([x2+45,cy-50,x2+80,cy-15],fill=(255,165,165))
    out=f"{WORKDIR}/ai_{idx:02d}.jpg"
    img.save(out,"JPEG",quality=90)
    return out,"pillow"

def add_overlay(img_path, caption):
    """Padrão eterno: lower third + caption badge."""
    img=Image.open(img_path).convert("RGB")
    draw=ImageDraw.Draw(img)
    # Lower third
    lt_h=95
    draw.rectangle([0,H-lt_h,W,H],fill=(8,6,18))
    draw.rectangle([0,H-lt_h,5,H],fill=VERM)
    draw.text((22,H-lt_h+12),"psi",fill=GOLD)
    draw.text((62,H-lt_h+10),"Daniela Coelho",fill=BRAN)
    draw.text((62,H-lt_h+40),"Saude Mental  |  @psidanielacoelho",fill=LILAS)
    draw.rectangle([0,H-4,W,H],fill=VERM)
    # Caption badge
    if caption:
        cap=caption[:28].upper()
        cap_w=min(len(cap)*14+44,W-60)
        cx_=W//2; cap_y=56
        draw.rounded_rectangle([cx_-cap_w//2,cap_y-24,cx_+cap_w//2,cap_y+24],radius=15,fill=(245,245,255))
        draw.rounded_rectangle([cx_-cap_w//2,cap_y-24,cx_+cap_w//2,cap_y+24],radius=15,outline=(200,200,220),width=2)
        draw.text((cx_-cap_w//2+22,cap_y-10),cap,fill=(20,15,45))
    img.save(img_path,"JPEG",quality=97)
    return img_path

# Captions por cena (extraídas do script)
paras = [p.strip() for p in script_tts.split('\n\n') if p.strip() and len(p.strip())>5]
CAPTIONS = []
for p in paras:
    cap = p[:25].split('.')[0].split(',')[0].split('?')[0].strip()
    if len(cap) < 4: cap = p[:20].strip()
    CAPTIONS.append(cap[:25])
if CAPTIONS: CAPTIONS[-1] = "INSCREVA-SE AGORA 🔔"

N = len(SCENE_PROMPTS)
print(f"🎨 Gerando {N} imagens únicas (Pollinations Flux enhanced)...")
t0=time.time()
IMGS=[None]*N; counts={"pollinations":0,"gemini":0,"pillow":0}

def gen_scene(args):
    i,prompt=args
    path,src=gen_image(prompt,i)
    cap=CAPTIONS[i] if i<len(CAPTIONS) else ""
    add_overlay(path,cap)
    sz=os.path.getsize(path)//1024
    icon="✅" if src!="pillow" else "⚠️"
    print(f"  [{i+1:02d}/{N}] {icon} {src} ({sz}KB)")
    return path,src

with ThreadPoolExecutor(max_workers=5) as ex:
    futures={ex.submit(gen_scene,(i,p)):i for i,p in enumerate(SCENE_PROMPTS)}
    for fut in as_completed(futures):
        i=futures[fut]; path,src=fut.result()
        IMGS[i]=path; counts[src]=counts.get(src,0)+1
        time.sleep(1.5)

gen_t=time.time()-t0
ai_total=counts.get("pollinations",0)+counts.get("gemini",0)
print(f"\n  ✅ {ai_total}/{N} AI | {counts.get('pillow',0)} Pillow | {gen_t:.1f}s")

# ÁUDIO Edge TTS
print(f"\n🎙️  Edge TTS AntonioNeural...")
async def _tts():
    import edge_tts
    c=edge_tts.Communicate(script_tts,voice="pt-BR-AntonioNeural")
    await c.save(f"{WORKDIR}/audio.mp3")

asyncio.run(_tts())

probe=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",
    f"{WORKDIR}/audio.mp3"],capture_output=True,text=True)
DUR_AUDIO=float(json.loads(probe.stdout)["format"]["duration"])
RATE_REAL=len(script_tts)/DUR_AUDIO
print(f"  {DUR_AUDIO:.1f}s ({DUR_AUDIO/60:.1f}min) | RATE={RATE_REAL:.3f}")

# Timing por parágrafo (RATE_REAL dinâmico)
durs=[]
for p in paras:
    durs.append(max(0.5,round(len(p)/RATE_REAL,3)))

# FFCONCAT — cada parágrafo usa sua imagem correspondente
concat_file=f"{WORKDIR}/concat.txt"
with open(concat_file,"w") as f:
    for i,(dur) in enumerate(durs):
        img_idx=min(i,N-1)
        if IMGS[img_idx]: f.write(f"file '{IMGS[img_idx]}'\nduration {dur:.3f}\n")
    if IMGS[-1]: f.write(f"file '{IMGS[-1]}'\n")

# RENDER
print(f"\n🎬 Renderizando (crf={CRF})...")
ts=int(time.time())
out_mp4=f"{WORKDIR}/v683_superior_{ts}.mp4"
cmd=["ffmpeg","-y","-f","concat","-safe","0","-i",concat_file,
     "-i",f"{WORKDIR}/audio.mp3",
     "-c:v","libx264","-pix_fmt","yuv420p",
     "-c:a","aac","-b:a","128k",
     "-shortest","-r","25","-crf",str(CRF),
     "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
           "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
     "-movflags","+faststart",out_mp4]
res=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
if res.returncode!=0: print(f"ERRO:\n{res.stderr[-1000:]}"); sys.exit(1)

sz=os.path.getsize(out_mp4)
probe2=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",out_mp4],
    capture_output=True,text=True)
dur2=float(json.loads(probe2.stdout)["format"]["duration"])
print(f"  ✅ {sz//1024//1024:.1f}MB ({sz//1024}KB) | {dur2:.1f}s ({dur2/60:.1f}min)")

# UPLOAD
print(f"\n☁️  Upload Supabase...")
with open(out_mp4,"rb") as f: vdata=f.read()
video_url=None
for att in range(5):
    try:
        video_url=sb_upload(f"mp4s/v683_superior_{ts}.mp4",vdata,"video/mp4")
        print("  ✅ Upload OK"); break
    except Exception as e: print(f"  Tentativa {att+1}: {e}"); time.sleep(10)

if video_url:
    sb_patch("content_pipeline",VIDEO_ID,{
        "video_url":video_url,"audio_url":None,"status":"pending_credentials",
        "metadata":json.dumps({
            "version":"superior_v8_plus","cenas":N,"ai_imgs":ai_total,
            "chars":len(script_tts),"dur_s":round(dur2,1),"file_mb":round(sz/1024/1024,1),
            "crf":CRF,"rate_real":round(RATE_REAL,3)
        })
    })

print(f"\n{'='*55}")
print(f"  ✅ VÍDEO 1 SUPERIOR — #683")
print(f"  {ai_total}/{N} AI | {sz//1024//1024:.1f}MB | {dur2/60:.1f}min")
print(f"  🎬 {video_url}")
print(f"  V8 Final era: 6.3MB | 62s")
print(f"{'='*55}\n")
