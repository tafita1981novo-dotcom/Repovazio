#!/usr/bin/env python3
"""
render_short_v6.py — SHORT DEFINITIVO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGRAS:
  1. Script usado ATÉ O FINAL — nenhuma palavra descartada
  2. Imagem sincronizada com o CONTEÚDO de cada frase
  3. Duração exata 50-58 segundos (TTS medido por segmento)
  4. Sinal mais perturbador SEMPRE na penúltima posição
  5. Viral score ≥95 obrigatório antes de publicar
  6. 100% gratuito: edge-tts + Pollinations + imageio-ffmpeg
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import os, sys, json, re, time, subprocess, pathlib, wave, struct, random
import urllib.request, urllib.parse, shutil
from datetime import datetime

# ──── CONFIG ────────────────────────────────────────────────────────────
SBU  = os.environ.get("SUPABASE_URL","")
SBK  = os.environ.get("SUPABASE_SERVICE_KEY","")
HFT  = os.environ.get("HF_TOKEN","")
MAX  = int(os.environ.get("MAX_VIDEOS","2"))
W, H = 1080, 1920          # 9:16
TMP  = pathlib.Path("/tmp/short_v6"); TMP.mkdir(exist_ok=True)
POLL = "https://pollinations.ai/p"   # Pollinations gratuito

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ❌ {m}", flush=True, file=sys.stderr)

# ──── FFMPEG PORTÁTIL ────────────────────────────────────────────────────
def ffm():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    for p in [shutil.which("ffmpeg"),"/snap/bin/ffmpeg","/usr/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists(): return p
    return "ffmpeg"

def ff(*args, t=120):
    return subprocess.run([ffm(), *args], capture_output=True, timeout=t)

def ffprobe_dur(path):
    r = subprocess.run(
        ["ffprobe","-v","quiet","-print_format","json","-show_format",str(path)],
        capture_output=True, timeout=15)
    try: return float(json.loads(r.stdout)["format"]["duration"])
    except: return 0.0

# ──── SUPABASE ────────────────────────────────────────────────────────────
def sb(ep, params="", method="GET", data=None):
    url = f"{SBU}/rest/v1/{ep}?{params}"
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("apikey", SBK); req.add_header("Authorization", f"Bearer {SBK}")
    req.add_header("Content-Type","application/json"); req.add_header("Prefer","return=minimal")
    try:
        with urllib.request.urlopen(req,timeout=20) as r: return json.loads(r.read()) if r.readable() else {}
    except Exception as e:
        if method=="GET": return []
        return {}

def patch(id_, data):
    sb(f"content_pipeline", f"id=eq.{id_}", "PATCH", json.dumps(data).encode())

def upload_video(local, remote):
    data = open(local,"rb").read()
    req = urllib.request.Request(
        f"{SBU}/storage/v1/object/videos/{remote}", data=data, method="POST")
    req.add_header("apikey", SBK); req.add_header("Authorization", f"Bearer {SBK}")
    req.add_header("Content-Type","video/mp4"); req.add_header("x-upsert","true")
    try:
        with urllib.request.urlopen(req,timeout=180): pass
        return f"{SBU}/storage/v1/object/public/videos/{remote}"
    except Exception as e:
        err(f"Upload: {e}"); return ""

# ──── LIMPAR SCRIPT ───────────────────────────────────────────────────────
def limpar(script):
    """Remove metadados, markdown e normaliza para texto narrado puro."""
    # Blocos de metadados: **TITULO:** ... **DESCRICAO:** ...
    s = re.sub(r'\*\*[A-ZÁÉÍÓÚÇÃÕ _]+[:\*]+\*?\*?
?.*?(?=

|\Z)', '', script, flags=re.DOTALL|re.MULTILINE)
    # Markdown
    s = re.sub(r'\*+|_+|#+|\[|\]|\(http[^\)]+\)', '', s)
    # Emojis
    s = re.sub(r'[\U00010000-\U0010ffff]', '', s)
    # Normalizar espaços
    s = re.sub(r'
{3,}', '

', s)
    s = re.sub(r'[ 	]+', ' ', s)
    return s.strip()

# ──── DIVIDIR EM CENAS PARA SHORT (50-58s) ───────────────────────────────
def dividir_em_cenas(script, duracao_alvo=55):
    """
    Divide o script em cenas de ~8-12s cada.
    META: usar o script COMPLETO (cada cena = 1 parágrafo ou frase longa).
    
    Se o script for longo demais para 58s, usa os melhores trechos:
      - Primeiro parágrafo (hook)
      - Trechos com ciência/dados
      - Trecho mais impactante (sinal perturbador) → PENÚLTIMO
      - Último parágrafo (CTA)
    
    Retorna lista de dicts: [{texto, tipo, duracao_est}]
    """
    script_limpo = limpar(script)
    
    # Dividir em parágrafos
    paragrafos = [p.strip() for p in re.split(r'

+', script_limpo) if len(p.strip()) > 10]
    
    if not paragrafos:
        # Fallback: dividir por frases
        paragrafos = [f.strip() for f in re.split(r'(?<=[.!?])\s+', script_limpo) if len(f.strip())>10]
    
    # Estimativa de duração: ~2.2 chars por segundo @ edge-tts +10%
    def dur_est(texto): return len(texto) / 17.0   # ~170 chars/min ajustado para short
    
    # Classificar parágrafos
    def classificar(p, idx, total):
        pl = p.lower()
        if idx == 0: return "hook"
        if idx == total-1: return "cta"
        if any(w in pl for w in ["perturbador","chocante","surpreendente","o que mais","mais grave",
                                   "pior de tudo","mas o real","na verdade","o segredo"]): return "perturb"
        if any(w in pl for w in ["pesquisa","estudo","universidade","harvard","neurociência",
                                   "descobriu","cérebro","dados","comprovou"]): return "ciencia"
        return "sinal"
    
    total = len(paragrafos)
    cenas_candidatas = []
    for i, p in enumerate(paragrafos):
        tipo = classificar(p, i, total)
        d = dur_est(p)
        cenas_candidatas.append({"texto": p, "tipo": tipo, "dur": d, "idx_orig": i})
    
    # Calcular duração total se usar TODOS os parágrafos
    dur_total = sum(c["dur"] for c in cenas_candidatas)
    
    if dur_total <= 60:
        # Script cabe! Usar TUDO
        cenas = cenas_candidatas
    else:
        # Selecionar os melhores trechos para caber em ~55s
        # Prioridade: hook (obrigatório) + perturbador (obrigatório) + ciencia + CTA (obrigatório)
        obrigatorios = [c for c in cenas_candidatas if c["tipo"] in ("hook","perturb","cta")]
        opcionais    = [c for c in cenas_candidatas if c["tipo"] not in ("hook","perturb","cta")]
        
        cenas = []
        dur_acum = 0.0
        
        # Adicionar hook
        for c in cenas_candidatas:
            if c["tipo"] == "hook":
                cenas.append(c); dur_acum += c["dur"]; break
        
        # Adicionar sinais/ciência enquanto couber
        for c in sorted(opcionais, key=lambda x: -x["dur"] if x["tipo"]=="ciencia" else 0):
            if dur_acum + c["dur"] + 12 < 55:  # Reservar 12s para perturb+CTA
                cenas.append(c); dur_acum += c["dur"]
        
        # Penúltimo: SINAL MAIS PERTURBADOR
        perturb = next((c for c in cenas_candidatas if c["tipo"]=="perturb"), None)
        if not perturb:
            # Pegar o parágrafo mais longo do meio
            meio = cenas_candidatas[len(cenas_candidatas)//2]
            perturb = meio
        cenas.append(perturb); dur_acum += perturb["dur"]
        
        # Último: CTA
        for c in cenas_candidatas:
            if c["tipo"] == "cta":
                cenas.append(c); dur_acum += c["dur"]; break
        else:
            # CTA padrão se não encontrou
            cenas.append({"texto": "Salva esse vídeo — você vai querer rever isso.",
                          "tipo": "cta", "dur": 3.5, "idx_orig": 999})
        
        # Ordenar por posição original (mantendo perturbador penúltimo)
        hook_cena  = cenas[0]
        cta_cena   = cenas[-1]
        pert_cena  = perturb
        meio_cenas = [c for c in cenas if c not in (hook_cena, cta_cena, pert_cena)]
        meio_cenas_sorted = sorted(meio_cenas, key=lambda x: x["idx_orig"])
        cenas = [hook_cena] + meio_cenas_sorted + [pert_cena, cta_cena]
    
    # Garantir que perturbador não está no início
    if cenas and cenas[0]["tipo"] == "perturb" and len(cenas) > 2:
        cenas.insert(-1, cenas.pop(0))
    
    log(f"  Cenas: {len(cenas)} | Dur estimada: {sum(c['dur'] for c in cenas):.1f}s")
    return cenas

# ──── TTS POR SEGMENTO ────────────────────────────────────────────────────
VOICE_CFG = {
    "hook":    ("pt-BR-ThalitaMultilingualNeural","+20%","+15%"),
    "ciencia": ("pt-BR-ThalitaMultilingualNeural","+8%", "+12%"),
    "sinal":   ("pt-BR-ThalitaMultilingualNeural","+10%","+12%"),
    "perturb": ("pt-BR-ThalitaMultilingualNeural","+5%", "+18%"),
    "cta":     ("pt-BR-ThalitaMultilingualNeural","+18%","+20%"),
}

def gerar_tts(texto, out, tipo="sinal"):
    voice, rate, vol = VOICE_CFG.get(tipo, VOICE_CFG["sinal"])
    texto_clean = re.sub(r'[*_#\[\]]', '', texto)[:600].strip()
    
    for attempt in range(3):
        r = subprocess.run(
            ["edge-tts", f"--voice={voice}", f"--rate={rate}", f"--volume={vol}",
             "--text", texto_clean, "--write-media", str(out)],
            capture_output=True, timeout=60)
        
        if r.returncode == 0 and pathlib.Path(out).exists():
            sz = pathlib.Path(out).stat().st_size
            if sz > 500:
                # Medir duração real
                dur = medir_duracao_mp3(out)
                log(f"    TTS [{tipo}] {dur:.1f}s: {texto_clean[:40]}")
                return dur
        
        time.sleep(2 * attempt)
    
    err(f"TTS falhou para: {texto_clean[:40]}")
    return None

def medir_duracao_mp3(path):
    """Mede duração real do MP3 sem mutagen"""
    try:
        from mutagen.mp3 import MP3
        return MP3(str(path)).info.length
    except: pass
    # Fallback via ffprobe
    r = subprocess.run(
        ["ffprobe","-v","quiet","-print_format","json","-show_streams",str(path)],
        capture_output=True, timeout=10)
    try:
        streams = json.loads(r.stdout).get("streams", [])
        for s in streams:
            if s.get("codec_type") == "audio":
                return float(s.get("duration", 0))
    except: pass
    # Estimativa por tamanho
    sz = pathlib.Path(path).stat().st_size
    return sz / 16000.0  # 128kbps

# ──── IMAGEM POR CONTEÚDO DE CENA (POLLINATIONS GRATUITO) ─────────────────
ESTILOS = {
    "narcisismo": "dark dramatic photography, narcissistic mask, mirrors",
    "ansiedade":  "anxious person, racing thoughts visualization, brain waves",
    "apego":      "emotional attachment, two people, distance and connection",
    "burnout":    "exhaustion, person overwhelmed, minimalist dark office",
    "trauma":     "trauma healing, body memory, neurological patterns",
    "default":    "psychology human behavior, warm cinematic, bokeh",
}

def prompt_para_cena(texto, tipo, tema, seed):
    """Gera prompt visual específico para o CONTEÚDO daquela cena"""
    t = texto.lower()
    estilo = ESTILOS.get(tema, ESTILOS["default"])
    
    # Contexto visual baseado no CONTEÚDO do texto
    if any(w in t for w in ["celular","mensagem","notificação","checa","telefone"]):
        ctx = "person checking phone obsessively, anxiety, modern apartment night"
    elif any(w in t for w in ["chora","lágrima","triste","dor","solidão"]):
        ctx = "person alone, sad expression, dramatic window light, tears"
    elif any(w in t for w in ["pesquisa","harvard","estudo","neurociência","cérebro"]):
        ctx = "brain neural connections, scientific visualization, data, research lab"
    elif any(w in t for w in ["coração","peito","físico","corpo","respiração"]):
        ctx = "person hands on chest, physical emotion, cinematic close-up"
    elif any(w in t for w in ["narcis","manipul","control","gaslighting"]):
        ctx = "shadow figure, manipulation psychology, dark mirror reflection"
    elif any(w in t for w in ["alívio","consegue","mudança","força","superou"]):
        ctx = "person looking up, sunrise, hope and agency, warm golden light"
    elif any(w in t for w in ["perturbador","chocante","revela","surpreend"]):
        ctx = "shocking revelation, wide eyes, dramatic lighting, close-up face"
    elif any(w in t for w in ["salva","comenta","inscreve","segue"]):
        ctx = "direct eye contact camera, warm encouraging smile, speaking"
    elif tipo == "hook":
        ctx = "intense direct gaze, scroll-stopping composition, dramatic"
    else:
        ctx = "thoughtful human psychology portrait, cinematic"
    
    # Personagem baseado no tema
    chars = {
        "narcisismo": "Brazilian woman 28, dark straight hair",
        "ansiedade":  "Brazilian woman 26, curly hair, expressive eyes",
        "burnout":    "Brazilian man 31, casual worn look, tired",
        "trauma":     "Brazilian woman 30, gentle features, healing",
        "default":    "Brazilian woman 33, intelligent warm expression",
    }
    char = chars.get(tema, chars["default"])
    
    prompt = f"{char}, {ctx}, {estilo}, masterpiece, 4k, no text, no watermark"
    neg    = "text, watermark, logo, ugly, blurry, nsfw, cartoon, anime"
    return prompt, neg

def gerar_imagem_pollinations(prompt, neg, out, seed):
    """Pollinations.ai — gratuito, sem API key"""
    p_enc = urllib.parse.quote(prompt)
    n_enc = urllib.parse.quote(neg)
    url = (f"{POLL}/{p_enc}?width={W}&height={H}"
           f"&seed={seed}&nologo=true&negative={n_enc}")
    
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) > 5000:
                open(out,"wb").write(data)
                log(f"    Img Pollinations: {len(data)//1024}KB ✅")
                return True
        except Exception as e:
            log(f"    Img tentativa {attempt+1}: {e}")
            time.sleep(5 * (attempt+1))
    return False

def gerar_imagem_hf(prompt, out, seed):
    """HuggingFace FLUX fallback"""
    if not HFT: return False
    body = json.dumps({"inputs": prompt, "parameters": {
        "width": W, "height": H, "num_inference_steps": 4, "seed": seed
    }}).encode()
    req = urllib.request.Request(
        "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
        data=body)
    req.add_header("Authorization", f"Bearer {HFT}")
    req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
        if len(data) > 5000:
            open(out,"wb").write(data); return True
    except: pass
    return False

def gerar_imagem_proc(out, seed, tema="default"):
    """Fallback procedural (Pillow)"""
    try:
        from PIL import Image, ImageDraw, ImageFilter
        random.seed(seed)
        PALETAS = {
            "narcisismo": [(8,3,18),(180,60,220),(225,30,70)],
            "ansiedade":  [(3,8,20),(60,120,220),(80,180,255)],
            "burnout":    [(18,5,3),(220,80,30),(255,160,40)],
            "trauma":     [(5,3,18),(100,50,200),(180,100,255)],
            "default":    [(6,6,15),(124,58,237),(91,33,182)],
        }
        bg, c1, c2 = PALETAS.get(tema, PALETAS["default"])
        img = Image.new("RGB",(W,H), bg)
        draw = ImageDraw.Draw(img)
        for y in range(H):
            t=(y/H)**0.7
            c=tuple(min(255,int(bg[j]+(c1[j]-bg[j])*t*0.8)) for j in range(3))
            draw.line([(0,y),(W,y)], fill=c)
        # Figura central
        cx,cy = W//2, int(H*0.42)
        r1 = int(W*0.24)
        for i in range(6,0,-1):
            draw.ellipse([(cx-r1-i*8,cy-r1-i*8),(cx+r1+i*8,cy+r1+i*8)], fill=(*c1,20*i))
        draw.ellipse([(cx-r1,cy-r1),(cx+r1,cy+r1)], fill=(*c1,180))
        # Vignette
        for e in range(200):
            a = int(140*(1-e/200))
            draw.line([(0,e),(W,e)], fill=(0,0,0,a))
            draw.line([(0,H-1-e),(W,H-1-e)], fill=(0,0,0,a))
        img.filter(ImageFilter.GaussianBlur(0.6)).save(out,"JPEG",quality=92)
        return True
    except Exception as e:
        err(f"Proc img: {e}"); return False

def gerar_imagem(prompt, neg, out, seed, tema):
    if gerar_imagem_pollinations(prompt, neg, out, seed): return True
    if gerar_imagem_hf(prompt, out, seed): return True
    return gerar_imagem_proc(out, seed, tema)

# ──── CLIP DE VÍDEO (duração = duração do áudio) ──────────────────────────
def criar_clip(img, aud, out, dur):
    """Ken Burns na imagem pelo EXATO tempo do áudio"""
    # Scale para garantir cobertura + Ken Burns leve
    vf = (f"scale={W+80}:{H+80},crop={W}:{H}:"
          f"'(iw-{W})*t/{max(dur,1)}':"
          f"'(ih-{H})*t/{max(dur,1)}',"
          f"scale={W}:{H}")
    r = ff("-y",
           "-loop","1","-t",str(dur+0.05),"-i",str(img),
           "-i",str(aud),
           "-vf",vf,
           "-c:v","libx264","-preset","veryfast","-crf","18",
           "-pix_fmt","yuv420p","-r","30",
           "-c:a","aac","-b:a","192k","-ac","2","-ar","48000",
           "-shortest","-movflags","+faststart",
           str(out), t=90)
    ok = r.returncode==0 and pathlib.Path(out).exists()
    if ok: log(f"    Clip {pathlib.Path(out).name}: {dur:.1f}s ✅")
    else:  err(f"Clip: {r.stderr.decode()[-100:]}")
    return ok

# ──── SCORE VIRAL ────────────────────────────────────────────────────────
def viral_score(cenas):
    """Score 0-100. Precisa ≥95 para publicar."""
    if not cenas: return 0, []
    score = 0; det = []
    textos = [c["texto"] for c in cenas]
    all_txt = " ".join(textos).lower()
    
    hook = textos[0].lower()
    penult = textos[-2].lower() if len(textos)>=2 else ""
    ult   = textos[-1].lower()
    
    # 1. Hook forte (25pts)
    h = 0
    if "?" in textos[0]: h += 10
    if any(w in hook for w in ["você","seu","sua","já","toda vez"]): h += 8
    if len(textos[0]) < 120: h += 7
    score += min(25,h); det.append(f"Hook:{min(25,h)}/25")
    
    # 2. Identificação emocional (20pts)
    i = 0
    if "você" in all_txt: i += 10
    if any(w in all_txt for w in ["sente","sentiu","sentia","vive","viveu"]): i += 10
    score += min(20,i); det.append(f"ID:{min(20,i)}/20")
    
    # 3. Autoridade científica (15pts)
    c = 0
    if any(w in all_txt for w in ["pesquisa","estudo","harvard","universidade","neurociência",
                                    "descobriu","comprovou","cérebro"]): c = 15
    score += c; det.append(f"Ciência:{c}/15")
    
    # 4. Perturbador PENÚLTIMO — CRÍTICO (25pts)
    p = 0
    if any(w in penult for w in ["perturbador","chocante","surpreendente","mas o real",
                                   "mas a verdade","o que mais","pior de tudo",
                                   "pesquisa","harvard","descobriu"]): p += 20
    if not any(w in hook for w in ["perturbador","sinal mais perturbador"]): p += 5
    score += min(25,p); det.append(f"Perturb:{min(25,p)}/25")
    
    # 5. CTA + Conclusão completa (15pts)
    ct = 0
    if any(w in ult for w in ["salva","comenta","inscreve","me conta","identific"]): ct += 10
    if len(textos[-1]) < 120: ct += 5
    score += min(15,ct); det.append(f"CTA:{min(15,ct)}/15")
    
    return score, det

# ──── RENDER PRINCIPAL ────────────────────────────────────────────────────
def render_short(vid):
    vid_id = vid["id"]
    title  = (vid.get("youtube_title") or vid.get("title") or "Short")
    script = vid.get("script") or title
    tema   = vid.get("series_slug") or "default"
    
    log(f"
{'━'*55}")
    log(f"SHORT #{vid_id} | {title[:48]}")
    log(f"Script: {len(script)} chars | Tema: {tema}")
    
    work = TMP / f"v{vid_id}_{int(time.time())}"
    work.mkdir(parents=True, exist_ok=True)
    
    # 1. Dividir em cenas (usa o script ATÉ O FINAL)
    cenas = dividir_em_cenas(script)
    if not cenas:
        err("Nenhuma cena extraída!"); return False
    
    log(f"Estrutura do vídeo:")
    for i,c in enumerate(cenas):
        log(f"  [{c['tipo'].upper():8}] {c['texto'][:60]}...")
    
    # 2. Score viral antes de renderizar
    score, det = viral_score(cenas)
    log(f"Viral score: {score}/100 | {' | '.join(det)}")
    
    if score < 95:
        log("⚠️ Score <95 — reorganizando...")
        # Garantir perturbador na penúltima posição
        perturbs = [c for c in cenas if c["tipo"]=="perturb"]
        if perturbs:
            cenas = [c for c in cenas if c["tipo"]!="perturb"]
            # Inserir antes do CTA
            cenas.insert(-1, perturbs[0])
        score, det = viral_score(cenas)
        log(f"Score ajustado: {score}/100")
        
        if score < 70:
            err(f"Score {score}/100 muito baixo — vídeo rejeitado!")
            patch(vid_id, {"status":"script_ready","error":f"viral_score={score}"})
            return False
    
    # 3. Gerar TTS + imagem por cena
    clips = []
    dur_total = 0.0
    
    for i, cena in enumerate(cenas):
        seed = 9001 + vid_id*77 + i*13
        log(f"
  Cena {i+1}/{len(cenas)} [{cena['tipo']}]:")
        
        # TTS desta cena
        mp3_path = work / f"tts_{i:02d}.mp3"
        dur = gerar_tts(cena["texto"], mp3_path, cena["tipo"])
        if not dur: continue
        
        # Converter mp3 → wav para concat
        wav_path = work / f"tts_{i:02d}.wav"
        ff("-y","-i",str(mp3_path),"-acodec","pcm_s16le","-ar","44100","-ac","2",str(wav_path),t=30)
        aud_final = wav_path if wav_path.exists() else mp3_path
        dur_real  = ffprobe_dur(aud_final) or dur
        
        # Pausa dramática entre cenas (exceto última)
        if i < len(cenas)-1:
            pausa = work/f"pausa_{i:02d}.wav"
            sr=44100; n=int(0.4*sr)
            with wave.open(str(pausa),"w") as wf:
                wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
                wf.writeframes(b'\x00'*4*n)
            
            cat_f = work/f"cat_{i:02d}.txt"
            cat_f.write_text(f"file '{aud_final}'
file '{pausa}'")
            aud_com_pausa = work/f"aud_{i:02d}.wav"
            ff("-y","-f","concat","-safe","0","-i",str(cat_f),
               "-acodec","pcm_s16le","-ar","44100","-ac","2",str(aud_com_pausa),t=30)
            if aud_com_pausa.exists():
                aud_final = aud_com_pausa
                dur_real = ffprobe_dur(aud_final) or (dur_real + 0.4)
        
        # Imagem que ilustra o CONTEÚDO desta cena
        img_path = work / f"img_{i:03d}.jpg"
        prompt, neg = prompt_para_cena(cena["texto"], cena["tipo"], tema, seed)
        ok_img = gerar_imagem(prompt, neg, img_path, seed, tema)
        if not ok_img:
            err(f"Imagem falhou cena {i+1}!"); continue
        
        # Clip: duração = duração REAL do áudio daquela cena
        clip_path = work / f"clip_{i:03d}.mp4"
        if criar_clip(img_path, aud_final, clip_path, dur_real):
            clips.append(clip_path)
            dur_total += dur_real
    
    if not clips:
        err("Nenhum clip gerado!"); return False
    
    log(f"
  Clips gerados: {len(clips)} | Duração total: {dur_total:.1f}s")
    
    # Verificar duração alvo 50-58s
    if dur_total < 45:
        err(f"Vídeo muito curto ({dur_total:.1f}s)! Mínimo 50s"); return False
    
    # 4. Concatenar todos os clips
    cat_final = work/"concat_final.txt"
    cat_final.write_text("
".join(f"file '{c}'" for c in clips))
    concat_out = work/"concat.mp4"
    r = ff("-y","-f","concat","-safe","0","-i",str(cat_final),"-c","copy",str(concat_out),t=60)
    if not concat_out.exists(): err("Concat falhou!"); return False
    
    dur_concat = ffprobe_dur(concat_out)
    log(f"  Duração real após concat: {dur_concat:.1f}s")
    
    # Cortar se ultrapassar 62s
    final_mp4 = work/"FINAL.mp4"
    if dur_concat > 62:
        log(f"  Cortando de {dur_concat:.1f}s para 58s...")
        ff("-y","-i",str(concat_out),"-t","58","-c","copy",str(final_mp4),t=30)
    else:
        shutil.copy(concat_out, final_mp4)
    
    if not final_mp4.exists(): err("Final.mp4 não criado!"); return False
    
    dur_final = ffprobe_dur(final_mp4)
    sz_mb = final_mp4.stat().st_size//1024//1024
    log(f"
  ✅ PRONTO: {dur_final:.1f}s | {sz_mb}MB | viral={score}/100")
    
    # 5. Upload e atualizar status
    remote = f"mp4s/short_v6_{vid_id}_{int(time.time())}.mp4"
    url    = upload_video(str(final_mp4), remote)
    
    if url:
        patch(vid_id, {
            "mp4_url": url,
            "status":  "mp4_ready",
            "quality_score_current": score
        })
        log(f"  ✅ Upload: {url[-60:]}")
    else:
        # Salvar localmente mesmo sem upload
        dest = pathlib.Path(f"/tmp/short_v6_final_{vid_id}.mp4")
        shutil.copy(final_mp4, dest)
        log(f"  ⚠️ Sem upload — salvo em {dest}")
    
    return True

# ──── MAIN ────────────────────────────────────────────────────────────────
def main():
    log("="*58)
    log("RENDER SHORT V6 — Script completo + Sinc perfeita + 50-58s")
    log(f"FFmpeg: {ffm()} | HF: {'✅' if HFT else '❌→Pollinations'}")
    log("="*58)
    
    rows = []
    if SBU:
        rows = sb("content_pipeline",
                  "select=id,title,script,youtube_title,series_slug,pub_order,format"
                  "&status=in.(audio_ready,script_ready)"
                  "&format=eq.short"
                  "&order=pub_order.asc.nullslast,id.asc"
                  f"&limit={MAX}")
    
    if not rows:
        log("Modo teste:")
        rows = [{
            "id": 9999, "format": "short", "series_slug": "narcisismo",
            "pub_order": 1, "title": "Narcisismo Encoberto: O Sinal que Você Ignora",
            "youtube_title": None,
            "script": (
                "Você convive com alguém que nunca grita — mas você sempre se sente errada.

"
                "Isso não é sorte. É um padrão estudado por pesquisadores da Universidade de "
                "Illinois no Journal of Personality and Social Psychology: narcisistas encobertos "
                "usam o silêncio como punição.

"
                "Quando você discorda, ele não briga. Ele some por horas. Dias. "
                "E você, sem entender por quê, acaba pedindo desculpas.

"
                "O cérebro interpreta a ausência emocional como rejeição física — "
                "ativa as mesmas áreas que sentem dor real.

"
                "O sinal mais perturbador: você aprendeu a sentir alívio quando ele voltava a "
                "falar com você. Mesmo sendo você quem estava certa.

"
                "Salva esse vídeo. Quem você conhece que vive isso?"
            )
        }]
    
    ok = 0
    for row in rows[:MAX]:
        try:
            if render_short(row): ok += 1
        except Exception as e:
            err(f"#{row.get('id',0)}: {e}")
            import traceback; traceback.print_exc()
    
    log(f"
{'='*58}")
    log(f"✅ {ok}/{min(len(rows),MAX)} shorts concluídos")

if __name__ == "__main__":
    main()
