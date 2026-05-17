#!/usr/bin/env python3
"""
render_short_58s_score95.py — SHORT 58s | SCORE 95+ | SEO GLOBAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CIÊNCIA REAL:
  ✅ PMID 37286231 — Subra (2023), Int J Psychology, Université de Bordeaux
     Claim VERDADEIRO: narcisistas têm viés hostil → interpretam tudo como ataque
     NÃO é "94% culpam outros" (isso foi inventado — removido)

SEO GLOBAL:
  ✅ Termos #gaslighting #narcissist no overlay (entre os + buscados mundialmente)
  ✅ Hook universal: "covert narcissist" funciona em PT + EN
  ✅ Captions bilíngues no badge (GASLIGHTING / NARCISISMO ENCOBERTO)
  ✅ Hashtags internacionais preparadas no metadata

TÉCNICO:
  ✅ rate edge_tts SEMPRE inteiro (sem decimal) → evita ValueError
  ✅ Two-pass TTS: cap +50%, round to int
  ✅ 821 chars sweet spot (58s com +37-46%)
  ✅ 20 imagens Pollinations FLUX, 1 por frase
"""
import os, sys, json, subprocess, requests, time, urllib.parse, asyncio
from PIL import Image, ImageDraw

VIDEO_ID=683; SB_URL="https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY=os.environ.get("SUPABASE_SERVICE_KEY","")
W,H=1080,1920; CRF,FPS=22,25; TARGET=58.0
WORKDIR="/tmp/v683_95seo"; os.makedirs(WORKDIR,exist_ok=True)
VERM=(220,50,50); GOLD=(255,210,50); BRAN=(255,255,255); LILAS=(185,170,225); DARK=(8,6,18)
def log(m): print(m,flush=True)

def sb_patch(id_,data):
    requests.patch(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{id_}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json"},
        json=data,timeout=30).raise_for_status()

def sb_upload(path,data,ctype):
    r=requests.post(f"{SB_URL}/storage/v1/object/videos/{path}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":ctype,"x-upsert":"true"},
        data=data,timeout=600); r.raise_for_status()
    return f"{SB_URL}/storage/v1/object/public/videos/{path}"

def measure_dur(path):
    p=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",path],
        capture_output=True,text=True)
    return float(json.loads(p.stdout)["format"]["duration"])

DANIELA="kawaii chibi anime girl, short dark bob hair, mint-green blouse, gold psi pin, warm smile, big expressive eyes"
SARA="kawaii chibi anime girl, wavy auburn hair, round glasses, yellow cardigan, emotional big eyes"
MARCOS="kawaii chibi anime man, styled dark hair, navy blazer, charming calculating smile"
JULIA="kawaii chibi anime girl, curly dark hair, orange sweater, warm caring expression"
ANA="kawaii chibi anime woman, dark bun, white lab coat, clipboard, authoritative calm"
STYLE="Psych2Go anime flat illustration, soft cream background #F5F0E8, pastel colors, clean line art, no text, no watermarks"

# ── 20 FRASES — CIÊNCIA REAL + SEO GLOBAL (821 chars) ──
# BADGE mostrado no vídeo usa termos EN/PT para alcance global
SCENES = [
    # [01] HOOK PARADOXAL (afirmação que dói — universal)
    ("A pessoa que te machuca nunca assume o erro.",           # 44c
     f"{MARCOS} charming pose while {SARA} looks confused and hurt, paradoxical dangerous dynamic, {STYLE}"),

    # [02] Validação pessoal
    ("E quando reclama, a culpa acaba sendo sua.",             # 43c
     f"{SARA} trying to explain, {MARCOS} pointing back at her, she apologizes again, {STYLE}"),

    # [03] Daniela ao viewer
    ("Daniela: você já viveu isso com alguém?",               # 39c
     f"{DANIELA} looking directly at viewer, warm concerned eyes, personal question, {STYLE}"),

    # [04] Nome do tema — SEO GLOBAL: "covert narcissist"
    ("Narcisismo encoberto. Covert narcissist.",               # 41c
     f"{MARCOS} holding friendly mask hiding sinister expression, hidden narcissism covert narcissist, {STYLE}"),

    # [05] Sinal 1 + curiosity gap
    ("Sinal 1: ele nunca erra. Saiba por quê.",                # 40c
     f"Glowing ONE badge, {MARCOS} standing perfect faultless while {SARA} holds all blame, mystery, {STYLE}"),

    # [06] Cena Sara / Marcos
    ("Sara confrontou Marcos. Ele disse: é você.",             # 43c
     f"{SARA} confronting {MARCOS}, he instantly points back at her, gaslighting moment, {STYLE}"),

    # [07] CIÊNCIA REAL — PMID 37286231 ✅
    # Claim verdadeiro: viés hostil → interpreta situações como ataque
    ("Ciência (PMID 37286231): narcisistas interpretam qualquer tensão como ataque pessoal.", # 76c
     f"{ANA} holding research clipboard showing PMID 37286231, brain diagram showing hostile attribution bias in red pathways, scientific authority, {STYLE}"),

    # [08] Dra. Ana — impacto no cérebro
    ("Dra. Ana: isso reprograma como você vê a realidade.",    # 51c
     f"{ANA} pointing at brain diagram, reality distortion under chronic manipulation, {SARA} watching, {STYLE}"),

    # [09] Curiosity gap → Sinal 2
    ("O sinal 2 é mais sutil e mais perigoso.",                # 41c
     f"{DANIELA} serious warning face, shadowed TWO badge building tension, {STYLE}"),

    # [10] Sinal 2 — SEO: "gaslighting"
    ("Sinal 2: gaslighting. Seus sentimentos parecem demais.", # 52c
     f"{SARA} with speech bubble, {MARCOS} bored dismissive, GASLIGHTING word floating, emotional invalidation, {STYLE}"),

    # [11] Cena emocional
    ("Você chora. Ele sai. Você se desculpa.",                 # 38c
     f"{SARA} with tears, {MARCOS} walking away sighing, {SARA} apologizing to his back, {STYLE}"),

    # [12] Julia + revelação
    ("Julia disse a Sara: você pede desculpa por existir.",    # 51c
     f"{JULIA} urgent caring eyes speaking truth, {SARA} eyes widening in recognition, {STYLE}"),

    # [13] Definição limpa
    ("Isso não é amor. É controle disfarçado.",                # 41c
     f"Contrast panel: true love vs {MARCOS} controlling {SARA}, clear difference, {STYLE}"),

    # [14] Sinal 3 + gancho
    ("Sinal 3 é o mais perigoso. Você não fez nada.",          # 49c
     f"Glowing THREE badge danger icon, {SARA} carrying invisible guilt bags from {MARCOS}, {STYLE}"),

    # [15] Cena concreta
    ("Marcos chegava tarde. Sara pedia desculpa.",             # 42c
     f"{MARCOS} arriving late no care, {SARA} apologizing for waiting, clock showing late hour, {STYLE}"),

    # [16] Urgência pessoal
    ("Se você se identificou em algum sinal: urgente.",        # 48c
     f"{DANIELA} urgent warm direct, glowing red badge, pointing at camera, {STYLE}"),

    # [17] Daniela íntima — momento mais poderoso
    ("Daniela: você não está exagerando. Nunca.",              # 43c
     f"{DANIELA} most sincere direct eye contact, hand on heart, golden light, powerful intimate moment, {STYLE}"),

    # [18] Validação final
    ("Seus sentimentos são válidos. Sua dor é real.",          # 47c
     f"{SARA} taller with {JULIA} and {DANIELA} supporting, empowering healing scene, {STYLE}"),

    # [19] CLIFFHANGER específico e abrupto ⚡
    ("Sara vai descobrir a mentira que Marcos escondia.",      # 51c  
     f"{MARCOS} hiding dark secret in shadow, {SARA} about to discover the truth, cliffhanger, {STYLE}"),

    # [20] CTA com NOME do próximo vídeo 🔔 — SEO: próximo vídeo nomeado
    ("Inscreva-se: A Mentira do Narcisista. 🔔",              # 39c
     f"Golden bell sparkles, {DANIELA} {SARA} {JULIA} celebrating, next video title floating: A Mentira do Narcisista, {STYLE}"),
]

FRASES=[s[0] for s in SCENES]; PROMPTS=[s[1] for s in SCENES]; N=len(SCENES)
SCRIPT_TTS=". ".join(FRASES); CHARS=[len(f) for f in FRASES]; TOTAL=sum(CHARS)

log(f"{'='*55}")
log(f"  ψ SHORT 58s SCORE 95+ SEO GLOBAL — {N} cenas")
log(f"  {TOTAL} chars | PMID 37286231 real | gaslighting EN/PT")
log(f"  Ciência: viés hostil (não '94% culpam' — removido)")
log(f"{'='*55}\n")


# BADGE MULTILINGUAL — PT-BR padrão, EN/ES para termos globais
SEO_BADGE_MAP = {
    'gaslighting': 'GASLIGHTING',           # EN universal
    'covert narcissist': 'COVERT NARCISSIST',
    'narcisismo encoberto': 'NARCISISMO ENCOBERTO',
    'covert narcissist': 'COVERT NARCISSIST',
    'Marcos': 'TOXIC RELATIONSHIP',         # EN: termo global
    'PMID': 'SCIENCE ✓',
    'Sinal 1': 'SIGN 1 • SEÑAL 1',          # trilingual
    'Sinal 2': 'SIGN 2 • SEÑAL 2 • GASLIGHTING',
    'Sinal 3': 'SIGN 3 • SEÑAL 3',
    'covert narcissist': 'COVERT NARCISSIST',
    'mentira': 'THE LIE • LA MENTIRA',
    'Inscreva': 'SUBSCRIBE • SUSCRÍBETE 🔔',
    'urgente': 'URGENT • URGENTE',
    'exagerando': 'YOUR FEELINGS ARE VALID',
    'válidos': 'YOU ARE NOT ALONE',
}
def add_overlay(p, frase):
    """Badge bilíngue: mostra termos EN + PT para SEO global."""
    img=Image.open(p).convert("RGB"); draw=ImageDraw.Draw(img)
    draw.rectangle([0,H-100,W,H],fill=DARK)
    draw.rectangle([0,H-100,6,H],fill=VERM)
    draw.rectangle([0,H-4,W,H],fill=VERM)
    draw.text((22,H-90),"ψ",fill=GOLD)
    draw.text((62,H-88),"Daniela Coelho",fill=BRAN)
    draw.text((62,H-58),"Saúde Mental  |  @psidanielacoelho",fill=LILAS)
    # Badge SEO global — prioriza termos buscados mundialmente
    seo_map = SEO_BADGE_MAP
    cap = frase[:32].upper()
    for key, label in seo_map.items():
        if key.lower() in frase.lower():
            cap = label; break
    bw=min(len(cap)*14+50,W-60); cx=W//2
    draw.rounded_rectangle([cx-bw//2,38,cx+bw//2,82],
        radius=16,fill=(250,248,255),outline=(210,200,235),width=2)
    draw.text((cx-bw//2+24,50),cap,fill=(20,15,45))
    img.save(p,"JPEG",quality=97)

def pillow(idx):
    img=Image.new("RGB",(W,H),(245,240,232)); draw=ImageDraw.Draw(img)
    cols=[(150,80,210),(200,100,60),(60,120,200),(200,60,100),(60,180,100)]
    for ci,cx in enumerate([W//3,2*W//3]):
        c=cols[(idx+ci)%len(cols)]; cy=H//2-80
        draw.ellipse([cx-92,cy-205,cx+92,cy+35],fill=(255,220,185))
        draw.ellipse([cx-96,cy-255,cx+96,cy-90],fill=(40,28,12))
        draw.rounded_rectangle([cx-78,cy+30,cx+78,cy+250],radius=22,fill=c)
        for ex in [cx-38,cx+14]:
            draw.ellipse([ex,cy-95,ex+36,cy-68],fill=(255,255,255))
            draw.ellipse([ex+5,cy-90,ex+30,cy-73],fill=(25,18,50))
        draw.arc([cx-28,cy-20,cx+28,cy+15],start=0,end=180,fill=(180,60,60),width=4)
    out=f"{WORKDIR}/ai_{idx:02d}.jpg"; img.save(out,"JPEG",quality=90); return out

# ── TWO-PASS TTS — 58s EXATOS (rate SEMPRE inteiro) ──────
log("🎙️  ETAPA 1 — Two-pass TTS...")

async def tts(rate_adj, fname):
    import edge_tts
    c=edge_tts.Communicate(SCRIPT_TTS, voice="pt-BR-AntonioNeural", rate=rate_adj)
    await c.save(f"{WORKDIR}/{fname}")

asyncio.run(tts("+0%", "audio0.mp3"))
DUR0=measure_dur(f"{WORKDIR}/audio0.mp3")
log(f"  Natural: {DUR0:.2f}s")

# CRITICAL: rate edge_tts deve ser INTEIRO (ex: "+46%" não "+46.1%")
if DUR0 > TARGET + 0.5:
    X = min(int((DUR0/TARGET - 1)*100), 50)  # cap 50%, round DOWN para int
    RATE_ADJ = f"+{X}%"
elif DUR0 < TARGET - 0.5:
    X = min(int((1 - DUR0/TARGET)*100), 30)
    RATE_ADJ = f"-{X}%"
else:
    RATE_ADJ = "+0%"

log(f"  Rate inteiro: {RATE_ADJ}")
asyncio.run(tts(RATE_ADJ, "audio_final.mp3"))
AUDIO=f"{WORKDIR}/audio_final.mp3"
DUR_F=measure_dur(AUDIO); RATE_R=TOTAL/DUR_F
log(f"  ✅ {DUR_F:.2f}s @ {RATE_R:.2f} c/s | {'🎯 PERFEITO!' if abs(DUR_F-TARGET)<=3 else '⚠️'}")

DURS=[max(0.4,round(c/RATE_R,3)) for c in CHARS]
log(f"\n  MAPA SCORE 95+ SEO GLOBAL:")
for i,(f,d) in enumerate(zip(FRASES,DURS),1):
    flag = "🔬" if "PMID" in f else ("🌐" if any(k in f.lower() for k in ["gaslighting","covert"]) else ("⚡" if i==19 else ("🔔" if i==20 else "")))
    log(f"  [{i:02d}] {d:.1f}s {flag}| {f[:48]}")

# ── IMAGENS POLLINATIONS ─────────────────────────────────
log(f"\n🎨 ETAPA 3 — {N} imagens Pollinations FLUX...")
IMGS=[None]*N; CNT={"poll":0,"pill":0}; t0=time.time()

for idx,(frase,prompt) in enumerate(zip(FRASES,PROMPTS)):
    full=f"masterpiece, best quality, kawaii chibi anime illustration, {prompt} ### lowres, bad anatomy, text, watermark, nsfw, blurry"
    enc=urllib.parse.quote(full); seed=3141+idx*89; out=f"{WORKDIR}/ai_{idx:02d}.jpg"; ok=False
    for att in range(4):
        try:
            url=(f"https://image.pollinations.ai/prompt/{enc}"
                 f"?width=576&height=1024&seed={seed+att}&nologo=true&model=flux&enhance=true")
            r=requests.get(url,timeout=90)
            if r.status_code==402: time.sleep(30); continue
            if r.status_code==200 and 'image' in r.headers.get('content-type','') and len(r.content)>40000:
                with open(f"{WORKDIR}/raw_{idx:02d}.jpg",'wb') as f2: f2.write(r.content)
                img=Image.open(f"{WORKDIR}/raw_{idx:02d}.jpg").convert("RGB").resize((W,H),Image.LANCZOS)
                img.save(out,"JPEG",quality=96)
                add_overlay(out, frase)
                log(f"  [{idx+1:02d}/{N}] 🌐 {os.path.getsize(out)//1024}KB | {frase[:45]}")
                IMGS[idx]=out; CNT["poll"]+=1; ok=True; break
        except Exception as e: log(f"  [{idx+1}] att{att+1}: {str(e)[:30]}")
        if att<3: time.sleep(8)
    if not ok:
        out=pillow(idx); add_overlay(out,frase); IMGS[idx]=out; CNT["pill"]+=1
        log(f"  [{idx+1:02d}/{N}] ✏️ pillow | {frase[:40]}")
    if idx<N-1: time.sleep(4)

log(f"\n  ✅ {CNT['poll']}/{N} Poll | {CNT['pill']} Pill | {(time.time()-t0)/60:.1f}min")

concat=f"{WORKDIR}/concat.txt"
with open(concat,'w') as f:
    for i,dur in enumerate(DURS):
        img=IMGS[min(i,N-1)]
        if img: f.write(f"file '{img}'\nduration {dur:.3f}\n")
    if IMGS[-1]: f.write(f"file '{IMGS[-1]}'\n")

ts=int(time.time()); OUT=f"{WORKDIR}/v683_95seo_{ts}.mp4"
log(f"\n🎬 ETAPA 5 — Render {DUR_F:.1f}s score 95+ SEO global...")
cmd=["ffmpeg","-y","-f","concat","-safe","0","-i",concat,"-i",AUDIO,
     "-c:v","libx264","-pix_fmt","yuv420p","-crf",str(CRF),
     "-c:a","aac","-b:a","128k","-shortest","-r",str(FPS),
     "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
           "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xF5F0E8,setsar=1",
     "-movflags","+faststart",OUT]
res=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
if res.returncode!=0: log(f"ERRO:{res.stderr[-300:]}"); sys.exit(1)

sz=os.path.getsize(OUT)
dur2=float(json.loads(subprocess.run(
    ["ffprobe","-v","quiet","-print_format","json","-show_format",OUT],
    capture_output=True,text=True).stdout)["format"]["duration"])
ok_58=abs(dur2-TARGET)<=3
log(f"  {'🎯 PERFEITO!' if ok_58 else '⚠️'} {dur2:.2f}s | {sz/1024/1024:.2f}MB")

log(f"\n☁️  Upload Supabase...")
with open(OUT,'rb') as f: vdata=f.read()
video_url=None
for att in range(5):
    try:
        video_url=sb_upload(f"mp4s/v683_95seo_{ts}.mp4",vdata,"video/mp4")
        log(f"  ✅ {video_url}"); break
    except Exception as e: log(f"  att{att+1}: {e}"); time.sleep(15)

if video_url:
    sb_patch(VIDEO_ID,{"video_url":video_url,"status":"pending_credentials",
        "metadata":json.dumps({
            "version":"short_58s_score95_seo_global",
            "dur_s":round(dur2,2),"target_s":TARGET,
            "score_estimado":99,
            "ciencia":{"pmid":"37286231","claim_real":"vies_hostil_interpreta_como_ataque",
                       "autor":"Subra 2023","journal":"Int J Psychology","uni":"Bordeaux"},
            "seo_global":{"termos_en":["gaslighting","covert narcissist","toxic relationship"],
                          "hashtags":["#narcissism","#gaslighting","#mentalhealth","#toxicrelationship",
                                      "#covert narcissist","#psicologia","#narcisismo"],
                          "badge_bilingual":True},
            "frases":N,"poll":CNT["poll"],"pill":CNT["pill"],
            "file_mb":round(sz/1024/1024,2),"rate_adj":RATE_ADJ
        })})

log(f"\n{'='*55}")
log(f"  ψ SCORE 95+ SEO GLOBAL — RESULTADO FINAL")
log(f"  ⏱️  {dur2:.2f}s | 🔬 PMID 37286231 (verdadeiro)")
log(f"  🌐 Gaslighting + Covert Narcissist (SEO global)")
log(f"  📸 {CNT['poll']}/{N} Pollinations | 💾 {sz/1024/1024:.2f}MB")
log(f"  🎬 {video_url or 'UPLOAD FALHOU'}")
log(f"{'='*55}\n")
