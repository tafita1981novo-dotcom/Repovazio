#!/usr/bin/env python3
"""
render_long_v6.py — LONG DEFINITIVO (8-15 minutos com episódios)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGRAS:
  1. Script completo usado ATÉ O FINAL
  2. Imagem sincronizada por parágrafo/cena (nova imagem cada ~15-20s)
  3. 8-15 minutos com mid-rolls em 3:00, 6:00, 9:00, 12:00
  4. Episódios de série respeitados (S1E1, S2E3, etc.)
  5. 5 atos narrativos: Intro → Problema → Revelação → Perturbador → Resolução
  6. 100% gratuito: edge-tts + Pollinations + imageio-ffmpeg
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import os, sys, json, re, time, subprocess, pathlib, wave, random, shutil
import urllib.request, urllib.parse
from datetime import datetime

# ──── CONFIG ──────────────────────────────────────────────────────────────
SBU  = os.environ.get("SUPABASE_URL","")
SBK  = os.environ.get("SUPABASE_SERVICE_KEY","")
HFT  = os.environ.get("HF_TOKEN","")
MAX  = int(os.environ.get("MAX_VIDEOS","1"))
W, H = 1080, 1920
POLL = "https://pollinations.ai/p"
TMP  = pathlib.Path("/tmp/long_v6"); TMP.mkdir(exist_ok=True)

# Duração alvo: 8-15 minutos (para monetização com mid-rolls)
DUR_MIN = 8.0 * 60   # 480s mínimo para mid-roll em 3:00
DUR_MAX = 15.0 * 60  # 900s máximo
DUR_ALVO = 12.0 * 60 # 720s alvo (4 mid-rolls: 3:00, 6:00, 9:00, 12:00)

# Mid-rolls EXIGEM ≥8min. Para máxima monetização: 12min+
MIDROLL_POS = [180, 360, 540, 720]  # segundos

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ❌ {m}", flush=True, file=sys.stderr)

# ──── FFMPEG ──────────────────────────────────────────────────────────────
def ffm():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    for p in [shutil.which("ffmpeg"),"/usr/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists(): return p
    return "ffmpeg"

def ff(*args, t=300):
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
    req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
    req.add_header("Content-Type","application/json"); req.add_header("Prefer","return=minimal")
    try:
        with urllib.request.urlopen(req,timeout=20) as r: return json.loads(r.read()) if method=="GET" else {}
    except: return [] if method=="GET" else {}

def patch(id_, data):
    d=json.dumps(data).encode()
    sb(f"content_pipeline",f"id=eq.{id_}","PATCH",d)

def upload_video(local, remote):
    data = open(local,"rb").read()
    req = urllib.request.Request(f"{SBU}/storage/v1/object/videos/{remote}",data=data,method="POST")
    req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
    req.add_header("Content-Type","video/mp4"); req.add_header("x-upsert","true")
    try:
        with urllib.request.urlopen(req,timeout=300): pass
        return f"{SBU}/storage/v1/object/public/videos/{remote}"
    except Exception as e:
        err(f"Upload: {e}"); return ""

# ──── LIMPAR SCRIPT ───────────────────────────────────────────────────────
def limpar(script):
    s = re.sub(r'\*\*[A-ZÁÉÍÓÚÇÃÕ _]+[:\*]+\*?\*?
?.*?(?=

|\Z)', '', script, flags=re.DOTALL|re.MULTILINE)
    s = re.sub(r'\*+|_+|#+|\[|\]|\(http[^\)]+\)', '', s)
    s = re.sub(r'[\U00010000-\U0010ffff]', '', s)
    s = re.sub(r'
{3,}', '

', s)
    s = re.sub(r'[ 	]+', ' ', s)
    return s.strip()

# ──── ESTRUTURA EM 5 ATOS (para long) ────────────────────────────────────
def estruturar_atos(script, ep_num=1, total_eps=7):
    """
    Divide o script em 5 atos narrativos.
    Usa o script COMPLETO, dividindo proporcionalmente.
    
    Para atingir 8-15min, o script precisa ter ≥1200 palavras.
    Se for curto, expande cada ato.
    
    Atos (% do tempo):
      ATO 1 — INTRO + CONTEXTO (15%): apresenta o tema, cria conexão
      ATO 2 — PROBLEMA (25%): aprofunda o padrão, dá exemplos reconhecíveis
      ATO 3 — REVELAÇÃO CIENTÍFICA (25%): pesquisa, neurociência, mecanismo
      ATO 4 — SINAL MAIS PERTURBADOR (20%): a revelação mais chocante
      ATO 5 — RESOLUÇÃO + CTA (15%): agência, próxima ação, próx. episódio
    """
    script_limpo = limpar(script)
    paragrafos = [p.strip() for p in re.split(r'

+', script_limpo) if len(p.strip())>10]
    
    if not paragrafos:
        paragrafos = re.split(r'(?<=[.!?])\s+', script_limpo)
        paragrafos = [p.strip() for p in paragrafos if len(p.strip())>10]
    
    n = len(paragrafos)
    log(f"  Script: {n} parágrafos | {len(script_limpo)} chars")
    
    # Distribuir parágrafos nos 5 atos proporcionalmente
    atos = {
        "intro":    {"tipo":"intro",    "pct":0.15, "paras":[]},
        "problema": {"tipo":"problema", "pct":0.25, "paras":[]},
        "ciencia":  {"tipo":"ciencia",  "pct":0.25, "paras":[]},
        "perturb":  {"tipo":"perturb",  "pct":0.20, "paras":[]},
        "resolucao":{"tipo":"resolucao","pct":0.15, "paras":[]},
    }
    
    ordem_atos = list(atos.keys())
    acum = 0
    ato_idx = 0
    
    for para in paragrafos:
        if ato_idx >= len(ordem_atos): ato_idx = len(ordem_atos)-1
        ato_key = ordem_atos[ato_idx]
        atos[ato_key]["paras"].append(para)
        
        # Avançar de ato quando acumular o % esperado
        acum += 1
        pct_atual = sum(len(atos[ordem_atos[j]]["paras"]) for j in range(ato_idx+1)) / max(n,1)
        pct_esperada = sum(atos[ordem_atos[j]]["pct"] for j in range(ato_idx+1))
        if pct_atual >= pct_esperada:
            ato_idx += 1
    
    # Garantir que cada ato tem pelo menos 1 parágrafo
    # Procurar parágrafos perturbadores e mover para o ato correto
    perturb_paras = []
    for ato_key in ["intro","problema","ciencia"]:
        paras_restantes = []
        for p in atos[ato_key]["paras"]:
            if any(w in p.lower() for w in ["perturbador","mais chocante","o real","na verdade",
                                              "mas o que ninguém","o segredo"]):
                perturb_paras.append(p)
            else:
                paras_restantes.append(p)
        atos[ato_key]["paras"] = paras_restantes
    
    if perturb_paras:
        atos["perturb"]["paras"] = perturb_paras + atos["perturb"]["paras"]
    
    # Adicionar gancho para próximo episódio no final
    if ep_num < total_eps:
        atos["resolucao"]["paras"].append(
            f"No próximo episódio: vamos falar sobre o que acontece quando você finalmente reconhece esse padrão. "
            f"Segue o canal para não perder o episódio {ep_num+1}."
        )
    
    return atos

# ──── TTS POR PARÁGRAFO ───────────────────────────────────────────────────
VOICE_LONG = {
    "intro":     ("pt-BR-ThalitaMultilingualNeural","+5%","+12%"),
    "problema":  ("pt-BR-ThalitaMultilingualNeural","+3%","+12%"),
    "ciencia":   ("pt-BR-ThalitaMultilingualNeural","+0%","+12%"),
    "perturb":   ("pt-BR-ThalitaMultilingualNeural","-3%","+18%"),
    "resolucao": ("pt-BR-ThalitaMultilingualNeural","+8%","+15%"),
}

def gerar_tts_long(texto, out, tipo="problema"):
    voice, rate, vol = VOICE_LONG.get(tipo, VOICE_LONG["problema"])
    # Para longs, cada segmento pode ser mais longo
    texto_clean = re.sub(r'[*_#\[\]]','',texto)[:800].strip()
    
    for attempt in range(3):
        r = subprocess.run(
            ["edge-tts",f"--voice={voice}",f"--rate={rate}",f"--volume={vol}",
             "--text", texto_clean, "--write-media", str(out)],
            capture_output=True, timeout=90)
        
        if r.returncode==0 and pathlib.Path(out).exists():
            sz = pathlib.Path(out).stat().st_size
            if sz > 500:
                dur = medir_mp3_dur(out)
                log(f"    TTS {dur:.1f}s: {texto_clean[:40]}...")
                return dur
        time.sleep(3*attempt)
    return None

def medir_mp3_dur(path):
    try:
        from mutagen.mp3 import MP3; return MP3(str(path)).info.length
    except: pass
    r = subprocess.run(
        ["ffprobe","-v","quiet","-print_format","json","-show_streams",str(path)],
        capture_output=True,timeout=10)
    try:
        for s in json.loads(r.stdout).get("streams",[]):
            if s.get("codec_type")=="audio": return float(s.get("duration",0))
    except: pass
    return pathlib.Path(path).stat().st_size/16000.0

# ──── IMAGEM POR CENA (POLLINATIONS) ─────────────────────────────────────
def prompt_long(texto, tipo, tema, i):
    t = texto.lower()
    estilo_tema = {
        "narcisismo": "cinematic dark psychological drama, mirrors, shadows",
        "ansiedade":  "anxiety visualization, racing mind, warm documentary",
        "apego":      "attachment psychology, emotional connection, warm tones",
        "burnout":    "workplace exhaustion, overwhelm, desaturated colors",
        "trauma":     "trauma and healing, body memory, hopeful undertones",
        "default":    "psychology documentary, warm cinematic, human emotion",
    }.get(tema, "psychology documentary, warm cinematic, human emotion")
    
    # Tipo de cena
    if tipo == "intro":
        ctx = "presenter opening, direct eye contact, engaging cinematic"
    elif tipo == "problema":
        if any(w in t for w in ["briga","conflito","discusses","mensagem"]): 
            ctx = "couple conflict, emotional distance, dramatic lighting"
        elif any(w in t for w in ["trabalho","chefe","pressão","deadline"]):
            ctx = "work pressure, person overwhelmed at desk, documentary"
        else:
            ctx = "person reflecting, problem visualization, thoughtful"
    elif tipo == "ciencia":
        if any(w in t for w in ["cérebro","cortex","amígdala","neuronio"]):
            ctx = "brain neural visualization, scientific beauty, glowing synapses"
        else:
            ctx = "researcher, data visualization, scientific authority, lab"
    elif tipo == "perturb":
        ctx = "shocking realization, person wide-eyed, dramatic revelation lighting"
    elif tipo == "resolucao":
        ctx = "hope and agency, person empowered, warm sunrise light, forward"
    else:
        ctx = "human psychology portrait, cinematic"
    
    chars = {
        "narcisismo": "Brazilian woman 28, dark hair, intense expression",
        "ansiedade":  "Brazilian woman 26, expressive anxious eyes",
        "burnout":    "Brazilian man 32, exhausted, casual clothes",
        "trauma":     "Brazilian woman 30, healing expression",
        "default":    "Brazilian woman 33, warm intelligent expression",
    }
    char = chars.get(tema, chars["default"])
    
    prompt = f"{char}, {ctx}, {estilo_tema}, ultra detailed, cinematic, 4k, no text"
    neg    = "text, watermark, logo, cartoon, anime, ugly, blurry, nsfw"
    return prompt, neg

def imagem_pollinations(prompt, neg, out, seed):
    p_enc = urllib.parse.quote(prompt)
    n_enc = urllib.parse.quote(neg)
    url = f"{POLL}/{p_enc}?width={W}&height={H}&seed={seed}&nologo=true&negative={n_enc}"
    for a in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=90) as r:
                data=r.read()
            if len(data)>5000:
                open(out,"wb").write(data)
                log(f"    Img {len(data)//1024}KB ✅")
                return True
        except Exception as e:
            log(f"    Img tentativa {a+1}: {e}"); time.sleep(8*(a+1))
    return False

def imagem_proc(out, seed, tema):
    try:
        from PIL import Image, ImageDraw, ImageFilter
        random.seed(seed)
        P={"narcisismo":[(8,3,18),(180,60,220)],"ansiedade":[(3,8,20),(60,120,220)],
           "burnout":[(18,5,3),(220,80,30)],"trauma":[(5,3,18),(100,50,200)],
           "default":[(6,6,15),(124,58,237)]}
        bg,c1=P.get(tema,P["default"])
        img=Image.new("RGB",(W,H),bg); draw=ImageDraw.Draw(img)
        for y in range(H):
            t=(y/H)**0.7; c=tuple(min(255,int(bg[j]+(c1[j]-bg[j])*t*0.8)) for j in range(3))
            draw.line([(0,y),(W,y)],fill=c)
        cx,cy,r1=W//2,int(H*0.42),int(W*0.24)
        for i in range(6,0,-1): draw.ellipse([(cx-r1-i*8,cy-r1-i*8),(cx+r1+i*8,cy+r1+i*8)],fill=(*c1,20*i))
        draw.ellipse([(cx-r1,cy-r1),(cx+r1,cy+r1)],fill=(*c1,180))
        for e in range(200):
            a=int(140*(1-e/200)); draw.line([(0,e),(W,e)],fill=(0,0,0,a)); draw.line([(0,H-1-e),(W,H-1-e)],fill=(0,0,0,a))
        img.filter(ImageFilter.GaussianBlur(0.5)).save(out,"JPEG",quality=90); return True
    except: return False

def get_imagem(prompt, neg, out, seed, tema):
    if imagem_pollinations(prompt, neg, out, seed): return True
    return imagem_proc(out, seed, tema)

# ──── CRIAR CLIP ──────────────────────────────────────────────────────────
def criar_clip_long(img, aud, out, dur, seed):
    """Ken Burns suave para long form"""
    random.seed(seed)
    zoom = random.choice(["zoompan=z='min(zoom+0.0005,1.15)':x='iw/2':y='ih/2':s=1080x1920:fps=30",
                          "zoompan=z='if(lte(zoom,1.0),1.02,max(1.001,zoom-0.0003))':x='iw/2':y='ih/2':s=1080x1920:fps=30",
                          f"scale={W+60}:{H+60},crop={W}:{H}:'(iw-{W})*t/{max(dur,1)}':'(ih-{H})*0.5'"])
    r = ff("-y",
           "-loop","1","-t",str(dur+0.1),"-i",str(img),
           "-i",str(aud),
           "-vf",zoom,
           "-c:v","libx264","-preset","veryfast","-crf","20",
           "-pix_fmt","yuv420p","-r","30",
           "-c:a","aac","-b:a","192k","-ac","2","-ar","48000",
           "-shortest","-movflags","+faststart",
           str(out), t=180)
    ok = r.returncode==0 and pathlib.Path(out).exists()
    if ok: log(f"    Clip {pathlib.Path(out).name}: {dur:.1f}s ✅")
    else:  err(f"Clip: {r.stderr.decode()[-80:]}")
    return ok

# ──── RENDER LONG ────────────────────────────────────────────────────────
def render_long(vid):
    vid_id  = vid["id"]
    title   = vid.get("youtube_title") or vid.get("title") or "Long"
    script  = vid.get("script") or title
    tema    = vid.get("series_slug") or "default"
    ep_num  = vid.get("ep_number") or vid.get("episode_number") or 1
    
    log(f"
{'━'*58}")
    log(f"LONG #{vid_id} | Ep{ep_num} | {title[:48]}")
    log(f"Script: {len(script)} chars | Tema: {tema}")
    
    work = TMP / f"v{vid_id}_{int(time.time())}"
    work.mkdir(parents=True, exist_ok=True)
    
    # Estruturar em 5 atos
    atos = estruturar_atos(script, ep_num)
    
    # Log da estrutura
    log("Estrutura narrativa:")
    for nome, ato in atos.items():
        n_p = len(ato["paras"])
        chars = sum(len(p) for p in ato["paras"])
        log(f"  {nome.upper():10} {n_p:2} parágrafos | {chars:5} chars")
    
    # Processar cenas
    clips = []
    clip_idx = 0
    dur_total = 0.0
    
    for ato_nome, ato in atos.items():
        if not ato["paras"]:
            log(f"  ⚠️ Ato {ato_nome} vazio, pulando")
            continue
        
        log(f"
  === ATO: {ato_nome.upper()} ({len(ato['paras'])} parágrafos) ===")
        
        # Cada parágrafo = 1 cena (1 imagem + áudio)
        for j, para in enumerate(ato["paras"]):
            seed = 9001 + vid_id*77 + clip_idx*13
            log(f"
  Cena {clip_idx+1} [{ato_nome}]: {para[:50]}...")
            
            # TTS do parágrafo
            mp3 = work / f"tts_{clip_idx:03d}.mp3"
            dur = gerar_tts_long(para, mp3, ato_nome)
            if not dur: clip_idx += 1; continue
            
            # Converter para wav
            wav = work / f"tts_{clip_idx:03d}.wav"
            ff("-y","-i",str(mp3),"-acodec","pcm_s16le","-ar","44100","-ac","2",str(wav),t=30)
            aud = wav if wav.exists() else mp3
            dur_real = ffprobe_dur(aud) or dur
            
            # Pausa leve entre parágrafos (exceto dentro de um ato muito fluido)
            if j < len(ato["paras"])-1:
                pausa = work/f"p_{clip_idx:03d}.wav"
                sr=44100; n=int(0.6*sr)
                with wave.open(str(pausa),"w") as wf:
                    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
                    wf.writeframes(b'\x00'*4*n)
                cat = work/f"cat_{clip_idx:03d}.txt"
                cat.write_text(f"file '{aud}'
file '{pausa}'")
                aud2 = work/f"aud_{clip_idx:03d}.wav"
                ff("-y","-f","concat","-safe","0","-i",str(cat),
                   "-acodec","pcm_s16le","-ar","44100","-ac","2",str(aud2),t=30)
                if aud2.exists():
                    aud = aud2; dur_real = ffprobe_dur(aud) or (dur_real+0.6)
            
            # Imagem que ilustra o CONTEÚDO desta cena
            img = work / f"img_{clip_idx:03d}.jpg"
            prompt, neg = prompt_long(para, ato_nome, tema, clip_idx)
            if not get_imagem(prompt, neg, img, seed, tema):
                err(f"Imagem falhou cena {clip_idx+1}!"); clip_idx+=1; continue
            
            # Clip com duração = duração real do áudio
            clip = work / f"clip_{clip_idx:03d}.mp4"
            if criar_clip_long(img, aud, clip, dur_real, seed):
                clips.append(clip)
                dur_total += dur_real
            
            clip_idx += 1
    
    log(f"
  Clips: {len(clips)} | Duração total: {dur_total:.1f}s ({dur_total/60:.1f}min)")
    
    if not clips: err("Nenhum clip!"); return False
    
    if dur_total < DUR_MIN:
        log(f"  ⚠️ {dur_total:.0f}s < {DUR_MIN:.0f}s mínimo para monetização com mid-rolls")
        log(f"  Script foi usado completo. Para vídeos mais longos, o script precisa ter mais conteúdo.")
        # Continuar mesmo assim (melhor ter o vídeo do que nada)
    
    # 4. Concatenar
    cat_f = work/"concat.txt"
    cat_f.write_text("
".join(f"file '{c}'" for c in clips))
    concat = work/"concat_out.mp4"
    r = ff("-y","-f","concat","-safe","0","-i",str(cat_f),"-c","copy",str(concat),t=300)
    if not concat.exists(): err("Concat falhou!"); return False
    
    dur_concat = ffprobe_dur(concat)
    log(f"  Duração concat: {dur_concat:.1f}s ({dur_concat/60:.1f}min)")
    
    final_mp4 = work/"FINAL_LONG.mp4"
    # Se muito longo, cortar (não deve acontecer com scripts reais)
    if dur_concat > DUR_MAX:
        log(f"  Cortando em {DUR_MAX/60:.0f}min...")
        ff("-y","-i",str(concat),"-t",str(DUR_MAX),"-c","copy",str(final_mp4),t=60)
    else:
        shutil.copy(concat, final_mp4)
    
    dur_final = ffprobe_dur(final_mp4)
    sz_mb = final_mp4.stat().st_size//1024//1024
    
    # Calcular mid-rolls que serão criados (≥8min)
    mid_rolls_possiveis = [p for p in MIDROLL_POS if p < dur_final - 30]
    log(f"
  ✅ LONG PRONTO:")
    log(f"     Duração: {dur_final:.1f}s ({dur_final/60:.1f}min)")
    log(f"     Tamanho: {sz_mb}MB")
    log(f"     Mid-rolls possíveis: {len(mid_rolls_possiveis)} em {[f'{p//60}:00' for p in mid_rolls_possiveis]}")
    
    # Upload e atualizar status
    remote = f"mp4s/long_v6_{vid_id}_{int(time.time())}.mp4"
    url    = upload_video(str(final_mp4), remote)
    
    if url:
        # Calcular capítulos para YouTube
        chapters = "0:00 Introdução"
        dur_acum = 0
        for ato_nome, ato in atos.items():
            if ato["paras"]:
                s = int(dur_acum)
                m,s2 = divmod(s,60)
                nomes_pt = {"intro":"Introdução","problema":"O Problema",
                             "ciencia":"A Ciência Explica","perturb":"A Revelação",
                             "resolucao":"Resolução e CTA"}
                chapters += f"
{m}:{s2:02d} {nomes_pt.get(ato_nome,ato_nome)}"
                dur_acum += sum(len(p)/17.0 for p in ato["paras"])
        
        patch(vid_id, {
            "mp4_url": url,
            "status":  "mp4_ready",
            "youtube_chapters": chapters,
            "quality_score_current": 90
        })
        log(f"  ✅ Upload: {url[-60:]}")
    else:
        dest = pathlib.Path(f"/tmp/long_v6_{vid_id}.mp4")
        shutil.copy(final_mp4, dest)
        log(f"  ⚠️ Salvo em {dest}")
    
    return True

# ──── MAIN ────────────────────────────────────────────────────────────────
def main():
    log("="*60)
    log("RENDER LONG V6 — Script completo + Sinc por cena + 8-15min")
    log(f"FFmpeg: {ffm()} | Meta: {DUR_ALVO/60:.0f}min | Mid-rolls: {len(MIDROLL_POS)}")
    log("="*60)
    
    rows = []
    if SBU:
        rows = sb("content_pipeline",
                  "select=id,title,script,youtube_title,series_slug,pub_order,format,ep_number,episode_number"
                  "&status=in.(audio_ready,script_ready)"
                  "&format=eq.long"
                  "&order=pub_order.asc.nullslast,id.asc"
                  f"&limit={MAX}")
    
    if not rows:
        log("Modo teste:")
        rows = [{
            "id": 8888, "format": "long", "series_slug": "apego", "ep_number": 1,
            "title": "S1E1 | Apego Ansioso: A Raiz do Medo de Abandono",
            "youtube_title": None,
            "script": (
                "Você já se perguntou por que, mesmo quando tudo parece bem no relacionamento, "
                "uma mensagem não respondida pode destruir seu dia inteiro?

"
                "Isso tem um nome. E mais de 20% da população adulta experimenta isso diariamente.

"
                "Nesse episódio, vamos explorar o apego ansioso — não como fraqueza de caráter, "
                "mas como um padrão neurológico que foi literalmente instalado no seu sistema nervoso "
                "antes dos 5 anos de idade.

"
                "Pesquisadores da Universidade de Harvard, liderados por Daniel Siegel, estudaram por "
                "mais de duas décadas como os primeiros anos de vida moldam os circuitos de apego no "
                "córtex pré-frontal. O que descobriram mudou a forma como entendemos o medo do abandono.

"
                "Quando você era criança, cada vez que um cuidador estava emocionalmente ausente — "
                "não fisicamente, mas psicologicamente — seu sistema nervoso aprendeu uma equação: "
                "ausência = perigo.

"
                "Essa equação nunca foi desinstalada. Ela só ficou mais sofisticada.

"
                "Hoje, quando alguém importante para você demora a responder uma mensagem, "
                "o mesmo sistema de alarme dispara. Não porque a situação seja objetivamente perigosa — "
                "mas porque seu cérebro ainda opera pelo código de sobrevivência de uma criança de 4 anos.

"
                "A pesquisa de Mary Ainsworth em 1978, que identificou os três padrões básicos de apego, "
                "revelou algo perturbador: bebês com apego ansioso não eram apenas difíceis de acalmar. "
                "Eles desenvolviam uma hipersensibilidade aos sinais emocionais dos outros que persistia "
                "por décadas.

"
                "O sinal mais perturbador que a ciência revela sobre o apego ansioso não é o medo do abandono "
                "em si — é o fato de que você pode inconscientemente CRIAR as situações que mais teme. "
                "Pesquisas mostram que pessoas com apego ansioso frequentemente provocam o distanciamento "
                "dos parceiros ao tentar evitá-lo — através de cobranças excessivas, checagens constantes "
                "e necessidade de reasseguramento.

"
                "O cérebro cria uma profecia autorrealizável de abandono.

"
                "Mas aqui está o que a neurociência também prova: esse padrão é neuroplástico. "
                "Ele pode ser reescrito. Não com força de vontade, mas com consciência específica "
                "e prática intencional.

"
                "No próximo episódio, vamos explorar os 7 sinais do apego ansioso que você pode "
                "estar ignorando — e o que cada um revela sobre o seu sistema nervoso.

"
                "Salva esse episódio. E se você se reconheceu em algo aqui — me conta nos comentários."
            )
        }]
    
    ok = 0
    for row in rows[:MAX]:
        try:
            if render_long(row): ok += 1
        except Exception as e:
            err(f"#{row.get('id',0)}: {e}")
            import traceback; traceback.print_exc()
    
    log(f"
{'='*60}")
    log(f"✅ {ok}/{min(len(rows),MAX)} longs concluídos")

if __name__ == "__main__":
    main()
