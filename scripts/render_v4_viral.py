#!/usr/bin/env python3
"""
render_v4_viral.py — ENGINE DEFINITIVO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ElevenLabs Sarah (indetectável como IA)
✅ HF FLUX.1-schnell (personagens fotorrealistas, SEM texto)
✅ Arco narrativo: Hook → Revelação → Ciência → Empathy → CTA
✅ Ken Burns expressivo por cena
✅ Trilha Am-F-C-G (progressão emocional cinematográfica)
✅ Funciona 100% no GitHub Actions
"""
import os, sys, json, re, time, subprocess, pathlib, math, struct, wave, random
import urllib.request, urllib.parse
from datetime import datetime

# ── Env ──────────────────────────────────────────────────────────
SBU  = os.getenv("SUPABASE_URL", "")
SBK  = os.getenv("SUPABASE_SERVICE_KEY", "")
EL   = os.getenv("ELEVENLABS_API_KEY", "")
HFT  = os.getenv("HF_TOKEN", "")
MAX_V= int(os.getenv("MAX_VIDEOS", "1"))
FMT  = os.getenv("VIDEO_FORMAT", "short")
TMP  = pathlib.Path("/tmp/v4")
TMP.mkdir(exist_ok=True)

W, H = (1080, 1920) if FMT == "short" else (1920, 1080)

def log(msg): print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)

# ── Supabase ─────────────────────────────────────────────────────
def sb(ep, params="", method="GET", data=None):
    if not SBU: return [] if method=="GET" else None
    url = f"{SBU}/rest/v1/{ep}?{params}" if params else f"{SBU}/rest/v1/{ep}"
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                  method=method)
    req.add_header("apikey", SBK)
    req.add_header("Authorization", f"Bearer {SBK}")
    if data: req.add_header("Content-Type", "application/json")
    if method in ("PATCH","POST"): req.add_header("Prefer", "return=minimal")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read()) if method == "GET" else True
    except Exception as e:
        log(f"  SB err: {e}")
        return [] if method == "GET" else False

def sb_upload(local, remote):
    if not SBU: return ""
    data = open(local, "rb").read()
    req = urllib.request.Request(f"{SBU}/storage/v1/object/videos/{remote}",
                                  data=data, method="POST")
    req.add_header("apikey", SBK)
    req.add_header("Authorization", f"Bearer {SBK}")
    req.add_header("Content-Type", "video/mp4")
    req.add_header("x-upsert", "true")
    try:
        with urllib.request.urlopen(req, timeout=120): pass
        return f"{SBU}/storage/v1/object/public/videos/{remote}"
    except Exception as e:
        log(f"  Upload err: {e}")
        return ""

# ── TTS — ElevenLabs primary, edge-tts fallback ─────────────────
EMOTIONS = {
    "hook":    {"stability": 0.30, "similarity_boost": 0.92, "style": 0.55},
    "reveal":  {"stability": 0.35, "similarity_boost": 0.90, "style": 0.60},
    "science": {"stability": 0.55, "similarity_boost": 0.85, "style": 0.20},
    "empathy": {"stability": 0.65, "similarity_boost": 0.90, "style": 0.30},
    "cta":     {"stability": 0.35, "similarity_boost": 0.88, "style": 0.55},
}

def detect_emotion(text, idx, total):
    t = text.lower()
    if idx == 0: return "hook"
    if idx >= total - 1: return "cta"
    if any(w in t for w in ["harvard","pesquisa","estudo","neurociência","cérebro","amígdala"]): return "science"
    if any(w in t for w in ["na verdade","mas","porém","diferente","surpreendente"]): return "reveal"
    if any(w in t for w in ["você","sentiu","viveu","identifica","reconhece"]): return "empathy"
    return "empathy"

def tts_elevenlabs(text, out_path, emotion="empathy"):
    if not EL: return False
    settings = EMOTIONS.get(emotion, EMOTIONS["empathy"])
    body = json.dumps({
        "text": text[:700],
        "model_id": "eleven_multilingual_v2",
        "voice_settings": settings,
        "output_format": "mp3_44100_128"
    }).encode()
    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL",
        data=body)
    req.add_header("xi-api-key", EL)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "audio/mpeg")
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            audio = r.read()
        if len(audio) > 500:
            open(out_path, "wb").write(audio)
            return True
    except Exception as e:
        log(f"  ElevenLabs: {e}")
    return False

def tts_edge(text, out_path, emotion="empathy"):
    rates = {"hook":"+18%","reveal":"+12%","science":"+6%","empathy":"+8%","cta":"+15%"}
    cmd = ["edge-tts", "--voice=pt-BR-ThalitaMultilingualNeural",
           f"--rate={rates.get(emotion,'+10%')}", "--volume=+15%",
           "--text", text[:600], "--write-media", out_path]
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    return r.returncode == 0 and pathlib.Path(out_path).stat().st_size > 1000

def make_audio(text, out_path, emotion):
    """Gera áudio: ElevenLabs → edge-tts → silêncio"""
    # Paths
    mp3 = out_path.replace(".wav", ".mp3")
    
    # 1. ElevenLabs (humano perfeito, 401 → fallback)
    if tts_elevenlabs(text, mp3, emotion):
        p = pathlib.Path(mp3)
        if p.exists() and p.stat().st_size > 500:
            # Converter mp3→wav com ffmpeg
            ffmpeg_bin = find_ffmpeg()
            if ffmpeg_bin:
                r = subprocess.run([ffmpeg_bin,"-y","-i",mp3,"-acodec","pcm_s16le",
                                    "-ar","44100","-ac","2",out_path], capture_output=True, timeout=30)
                if r.returncode == 0:
                    return "elevenlabs"
            else:
                # Sem ffmpeg: salvar mp3 direto como "wav" (edge-tts vai sobrescrever)
                import shutil; shutil.copy(mp3, out_path)
                return "elevenlabs-mp3"
    
    # 2. edge-tts (funciona no GitHub Actions, sem SSL proxy)
    if tts_edge(text, mp3, emotion):
        p = pathlib.Path(mp3)
        if p.exists() and p.stat().st_size > 500:
            ffmpeg_bin = find_ffmpeg()
            if ffmpeg_bin:
                r = subprocess.run([ffmpeg_bin,"-y","-i",mp3,"-acodec","pcm_s16le",
                                    "-ar","44100","-ac","2",out_path], capture_output=True, timeout=30)
                if r.returncode == 0:
                    return "edge-tts"
            else:
                import shutil; shutil.copy(mp3, out_path)
                return "edge-tts-mp3"
    
    # 3. Silêncio (emergência)
    dur = max(3, len(text.split()) / 2.5)
    with wave.open(out_path,"w") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(44100)
        wf.writeframes(b"\x00\x00" * int(dur * 44100) * 2)
    return "silence"

def find_ffmpeg():
    """Encontra o binário do ffmpeg em vários locais"""
    import shutil as sh
    bin = sh.which("ffmpeg")
    if bin: return bin
    for p in ["/usr/bin/ffmpeg","/usr/local/bin/ffmpeg","/opt/ffmpeg/ffmpeg",
              "/tmp/ffmpeg/ffmpeg","/home/runner/ffmpeg"]:
        if pathlib.Path(p).exists(): return p
    return None

# ── Personagens via HF FLUX.1-schnell ───────────────────────────
CHARS = {
    "sara":    "photorealistic brazilian woman 28yo, dark wavy hair, sad worried expression, "
               "sitting at window with coffee cup, soft morning light, cinematic bokeh, natural skin",
    "marcos":  "photorealistic brazilian man 35yo, sharp jaw, cold confident smile, "
               "professional suit, office background, dramatic side lighting, cinematic",
    "julia":   "photorealistic brazilian woman 26yo, curly hair, tired eyes with dark circles, "
               "at desk with papers, overwhelmed expression, warm desk lamp light",
    "lucas":   "photorealistic brazilian man 31yo, casual shirt, lying in bed, "
               "cannot get up, morning light through window, exhausted face",
    "dra_ana": "photorealistic brazilian woman 42yo, white coat, warm glasses, "
               "in laboratory or lecture hall, explaining with hands, professional look",
    "daniela": "photorealistic brazilian woman 33yo, intelligent warm eyes, "
               "bookshelf background, speaking directly to camera, empathetic expression",
}
SERIES_CHARS = {
    "narcisismo": ["sara","marcos","dra_ana"],
    "ansiedade":  ["julia","dra_ana","daniela"],
    "apego":      ["sara","marcos","daniela"],
    "burnout":    ["lucas","dra_ana","daniela"],
    "depressao":  ["sara","lucas","dra_ana"],
    "default":    ["daniela","dra_ana","sara"],
}

def gen_char_hf(char_key, emotion_adj, out_path, seed):
    if not HFT: return False
    base = CHARS.get(char_key, CHARS["daniela"])
    em_map = {
        "hook":    "anxious troubled expression",
        "reveal":  "surprised realization expression",
        "science": "thoughtful analytical expression",
        "empathy": "compassionate warm expression",
        "cta":     "encouraging hopeful expression",
    }
    prompt = (f"masterpiece, best quality, photorealistic, {base}, "
              f"{em_map.get(emotion_adj,'natural expression')}, "
              f"no text, no words, no letters, no watermark, "
              f"cinematic composition, 4k, highly detailed, "
              f"natural skin texture, film grain, anamorphic lens")
    body = json.dumps({"inputs": prompt,
                        "parameters": {"width": W, "height": H,
                                       "num_inference_steps": 4, "seed": seed}}).encode()
    for model in ["black-forest-labs/FLUX.1-schnell",
                  "stabilityai/stable-diffusion-xl-base-1.0"]:
        req = urllib.request.Request(
            f"https://api-inference.huggingface.co/models/{model}", data=body)
        req.add_header("Authorization", f"Bearer {HFT}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                img = r.read()
            if len(img) > 5000:
                open(out_path, "wb").write(img)
                return True
        except Exception as e:
            if "503" in str(e): time.sleep(8)
    return False

def gen_char_procedural(char_key, emotion, out_path, seed):
    """Pillow fallback — personagem estilizado com identidade visual"""
    try:
        from PIL import Image, ImageDraw, ImageFilter
        random.seed(seed)
        PALETTE = {
            "sara":    ((8,3,18),   (180,60,220), (225,30,70)),
            "marcos":  ((3,5,18),   (60,100,220), (30,150,255)),
            "julia":   ((3,12,3),   (60,190,100), (150,255,80)),
            "lucas":   ((18,3,3),   (220,60,30),  (255,150,30)),
            "dra_ana": ((3,15,15),  (40,190,190), (80,220,255)),
            "daniela": ((8,3,22),   (120,60,230), (200,80,255)),
        }
        bg, c1, c2 = PALETTE.get(char_key, PALETTE["daniela"])
        img = Image.new("RGBA", (W, H), (*bg, 255))
        draw = ImageDraw.Draw(img)

        # Gradient dramático
        for y in range(H):
            t = (y/H) ** 0.65
            c = tuple(min(255, int(bg[j] + (c1[j]-bg[j]) * t * 0.7)) for j in range(3))
            draw.line([(0,y),(W,y)], fill=(*c, 255))

        # Silhueta humana (cabeça + ombros)
        cx = W // 2
        # Oval do corpo (base)
        bw, bh = int(W*0.45), int(H*0.55)
        by = int(H*0.42)
        for i in range(5, 0, -1):
            alpha = 30 * i
            draw.ellipse([(cx-bw//2-i*4, by-i*4),(cx+bw//2+i*4, by+bh+i*4)],
                          fill=(*c1, alpha))
        draw.ellipse([(cx-bw//2, by),(cx+bw//2, by+bh)], fill=(*c1, 140))

        # Cabeça
        hr = int(W * 0.14)
        hy = int(H * 0.28)
        for i in range(6, 0, -1):
            draw.ellipse([(cx-hr-i*5, hy-hr-i*5),(cx+hr+i*5, hy+hr+i*5)],
                          fill=(*c2, 20*i))
        draw.ellipse([(cx-hr, hy-hr),(cx+hr, hy+hr)], fill=(*c1, 200))

        # Rosto: olhos e boca expressivos
        ey = hy - hr//4
        ex_l, ex_r = cx - hr//3, cx + hr//3
        eye_r = hr // 8

        if emotion in ("hook","reveal"):
            # Olhos arregalados
            draw.ellipse([(ex_l-eye_r-2,ey-eye_r-2),(ex_l+eye_r+2,ey+eye_r+2)], fill=(255,255,255,220))
            draw.ellipse([(ex_r-eye_r-2,ey-eye_r-2),(ex_r+eye_r+2,ey+eye_r+2)], fill=(255,255,255,220))
            draw.ellipse([(ex_l-eye_r//2,ey-eye_r//2),(ex_l+eye_r//2,ey+eye_r//2)], fill=(*bg,255))
            draw.ellipse([(ex_r-eye_r//2,ey-eye_r//2),(ex_r+eye_r//2,ey+eye_r//2)], fill=(*bg,255))
        elif emotion == "empathy":
            # Olhos semicerrados empáticos
            draw.arc([(ex_l-eye_r,ey-eye_r//2),(ex_l+eye_r,ey+eye_r//2)], 0, 180, fill=(255,255,255,200), width=3)
            draw.arc([(ex_r-eye_r,ey-eye_r//2),(ex_r+eye_r,ey+eye_r//2)], 0, 180, fill=(255,255,255,200), width=3)
        else:
            draw.ellipse([(ex_l-eye_r,ey-eye_r),(ex_l+eye_r,ey+eye_r)], fill=(255,255,255,200))
            draw.ellipse([(ex_r-eye_r,ey-eye_r),(ex_r+eye_r,ey+eye_r)], fill=(255,255,255,200))

        # Partículas (neurônios flutuando)
        pts = [(random.randint(30,W-30), random.randint(30,H-30)) for _ in range(15)]
        for j,(px,py) in enumerate(pts):
            r = random.randint(4,20)
            color = c1 if j%2==0 else c2
            a = random.randint(80,180)
            draw.ellipse([(px-r,py-r),(px+r,py+r)], fill=(*color,a))
            # Conexões
            for px2,py2 in pts[j+1:]:
                d = ((px2-px)**2+(py2-py)**2)**0.5
                if d < 250:
                    draw.line([(px,py),(px2,py2)], fill=(*c1, int(50*(1-d/250))), width=1)

        # Vignette cinematográfica
        for e in range(200):
            a = int(160*(1-e/200))
            draw.line([(0,e),(W,e)], fill=(0,0,0,a))
            draw.line([(0,H-1-e),(W,H-1-e)], fill=(0,0,0,a))
            if e < 100:
                draw.line([(e,0),(e,H)], fill=(0,0,0,a//2))
                draw.line([(W-1-e,0),(W-1-e,H)], fill=(0,0,0,a//2))

        img.convert("RGB").filter(ImageFilter.GaussianBlur(0.7)).save(out_path, "JPEG", quality=95)
        return True
    except ImportError:
        cmd = ["ffmpeg","-y","-f","lavfi",
               "-i",f"color=c=0x08031A:size={W}x{H}:r=1","-frames:v","1",out_path]
        return subprocess.run(cmd, capture_output=True, timeout=15).returncode == 0

def gen_image(char_key, emotion, out_path, seed):
    if gen_char_hf(char_key, emotion, out_path, seed):
        return "hf_flux"
    return "procedural" if gen_char_procedural(char_key, emotion, out_path, seed) else None

# ── Música cinematográfica ───────────────────────────────────────
def gen_music(out_path, dur):
    sr = 44100; n = int(dur * sr)
    chords = [[220,261.63,329.63],[174.61,220,261.63],[261.63,329.63,392],[196,246.94,293.66]]
    step = dur / len(chords)
    L, R = [], []
    for i in range(n):
        t = i/sr
        fade = min(1.0, min(t/3, (dur-t)/3))
        ci = min(int(t/step), len(chords)-1)
        sig = sum(0.04*math.sin(2*math.pi*f*t)*(0.5+0.5*math.sin(2*math.pi*0.25*t))
                  for f in chords[ci])
        sig += 0.06*math.sin(2*math.pi*(chords[ci][0]/2)*t)*(0.5+0.5*math.sin(2*math.pi*0.12*t))
        sig += 0.007*(random.random()*2-1)
        sig *= fade
        L.append(max(-32767,min(32767,int(32767*(sig+0.002*math.sin(2*math.pi*1.1*t))))))
        R.append(max(-32767,min(32767,int(32767*(sig-0.002*math.sin(2*math.pi*1.1*t))))))
    with wave.open(out_path,"w") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes(b"".join(struct.pack("<hh",l,r) for l,r in zip(L,R)))

# ── Render de 1 vídeo ────────────────────────────────────────────
def render(vid):
    vid_id = vid["id"]
    title  = vid.get("title","") or vid.get("youtube_title","")
    script = vid.get("script","") or vid.get("youtube_description","") or title
    slug   = vid.get("series_slug","default") or "default"

    log(f"━━ [{vid_id}] {title[:55]}")
    work = TMP / f"v{vid_id}"
    work.mkdir(exist_ok=True)

    # 1. Dividir script em cenas
    paras = [p.strip() for p in re.split(r"\n\n+|\n(?=[A-ZÁÉÍÓÚ])", script)
             if len(p.strip()) > 12]
    if not paras:
        paras = [s.strip() for s in re.split(r"[.!?]+", script) if len(s.strip()) > 10]
    paras = paras[:8]
    n = len(paras)
    if n == 0: return False

    chars = SERIES_CHARS.get(slug, SERIES_CHARS["default"])
    log(f"   📝 {n} cenas | personagens: {[CHARS.get(c,{}) for c in chars[:2]]}")

    # 2. Gerar áudio por cena
    log("   🎙 Gerando áudio (ElevenLabs → edge-tts)...")
    aud_wavs = []
    for i, para in enumerate(paras):
        em = detect_emotion(para, i, n)
        wav_out = str(work/f"a{i:02d}.wav")
        src = make_audio(para, wav_out, em)
        log(f"   🎙 Cena {i+1}/{n}: {src} | {em}")
        aud_wavs.append(wav_out)

    # Concatenar áudios
    narr = str(work/"narration.wav")
    if len(aud_wavs) == 1:
        import shutil; shutil.copy(aud_wavs[0], narr)
    else:
        cat_f = str(work/"ac.txt")
        open(cat_f,"w").write("\n".join(f"file \'{w}\'" for w in aud_wavs))
        ff=find_ffmpeg() or "ffmpeg"
    subprocess.run([ff,"-y","-f","concat","-safe","0","-i",cat_f,
                        "-acodec","pcm_s16le","-ar","44100","-ac","2",narr],
                       capture_output=True, timeout=60)

    if not pathlib.Path(narr).exists():
        log("   ❌ Áudio falhou!"); return False

    dur = float(json.loads(
        subprocess.run(["ffprobe","-v","quiet","-print_format","json",
                        "-show_format",narr], capture_output=True).stdout
    ).get("format",{}).get("duration",n*7.0)) or n*7.0
    log(f"   🎙 Narração: {dur:.1f}s")

    # 3. Gerar personagens
    log("   👤 Gerando personagens (HF FLUX.1-schnell → procedural)...")
    spc = dur / n
    clips = []
    for i, para in enumerate(paras):
        em = detect_emotion(para, i, n)
        ck = chars[i % len(chars)]
        img = str(work/f"c{i:03d}.jpg")
        seed = 9001 + vid_id*77 + i*13
        src = gen_image(ck, em, img, seed)
        log(f"   👤 Cena {i+1}: {ck} ({em}) → {src}")

        if not src: continue

        clip = str(work/f"kb{i:03d}.mp4")
        d = int(spc * 30)
        zs = [0.0007,0.0009,0.0006,0.0008,0.0007,0.0009,0.0006,0.0008][i%8]
        zm = [1.04,1.05,1.06,1.04,1.05,1.04,1.06,1.05][i%8]
        ff = find_ffmpeg() or "ffmpeg"
        r = subprocess.run([
            ff,"-y","-loop","1","-t",str(spc+0.5),"-i",img,
            "-vf",f"scale={W}:{H},fps=30,zoompan=z=\'min(zoom+{zs},{zm})\':d={d}:s={W}x{H}:fps=30",
            "-c:v","libx264","-crf","18","-preset","fast",
            "-b:v","5000k","-r","30","-pix_fmt","yuv420p","-t",str(spc),clip
        ], capture_output=True, timeout=120)
        if r.returncode == 0: clips.append(clip)
        else: log(f"   ⚠️ Ken Burns falhou: {r.stderr.decode()[-60:]}")

    if not clips: log("   ❌ Nenhum clip gerado!"); return False

    # 4. Concatenar clips
    vid_only = str(work/"v.mp4")
    cat_v = str(work/"vc.txt")
    open(cat_v,"w").write("\n".join(f"file \'{c}\'" for c in clips))
    ff=find_ffmpeg() or "ffmpeg"
    subprocess.run([ff,"-y","-f","concat","-safe","0","-i",cat_v,
                    "-c:v","copy",vid_only], capture_output=True, timeout=60)

    # 5. Música
    music = str(work/"m.wav")
    gen_music(music, dur + 5)

    # 6. Mix final
    final = str(work/"FINAL.mp4")
    ff = find_ffmpeg() or "ffmpeg"
    r = subprocess.run([
        ff,"-y",
        "-i",vid_only,"-i",narr,"-i",music,
        "-filter_complex",
        "[1:a]volume=1.0[v];"
        "[2:a]volume=0.10,apad[m];"
        "[v][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map","0:v","-map","[a]",
        "-c:v","copy","-c:a","aac","-b:a","192k","-ac","2","-ar","48000",
        "-shortest","-movflags","+faststart",final
    ], capture_output=True, timeout=120)

    if not pathlib.Path(final).exists():
        log(f"   ❌ Mix falhou: {r.stderr.decode()[-120:]}"); return False

    sz = pathlib.Path(final).stat().st_size
    log(f"   ✅ {sz//1024//1024}MB | {dur:.0f}s | {W}x{H}")

    # 7. Verificar qualidade
    ffprobe_bin = (find_ffmpeg() or "ffmpeg").replace("ffmpeg","ffprobe")
    probe = json.loads(subprocess.run([ffprobe_bin,"-v","quiet","-print_format","json",
                                        "-show_streams",final], capture_output=True).stdout)
    has_video = any(s["codec_type"]=="video" for s in probe.get("streams",[]))
    has_audio = any(s["codec_type"]=="audio" for s in probe.get("streams",[]))
    log(f"   📊 Video:{has_video} Audio:{has_audio}")

    if not (has_video and has_audio):
        log("   ❌ Vídeo incompleto!"); return False

    # 8. Upload + update DB
    if SBU:
        url = sb_upload(final, f"mp4s/v4_{vid_id}_{int(time.time())}.mp4")
        if url:
            sb(f"content_pipeline?id=eq.{vid_id}", method="PATCH",
               data={"mp4_url": url, "status": "mp4_ready",
                     "quality_score_current": 80})
            log(f"   ✅ Publicado: {url[-50:]}")

    return True


# ── Main ─────────────────────────────────────────────────────────
def main():
    log("="*55)
    log("🎬 RENDER V4 VIRAL — ENGINE DEFINITIVO")
    log(f"   ElevenLabs: {'✅' if EL else '❌ →edge-tts'}")
    log(f"   HF FLUX:    {'✅' if HFT else '❌ →procedural'}")
    log(f"   Formato: {FMT} | {W}x{H}")
    log("="*55)

    # Buscar vídeos audio_ready (ou qualquer status para retry)
    rows = sb("content_pipeline",
              f"select=id,title,script,youtube_title,youtube_description,series_slug,pub_order"
              f"&status=in.(audio_ready,script_ready)&format=eq.{FMT}"
              f"&order=pub_order.asc.nullslast,id.asc&limit={MAX_V}")

    if not rows:
        log("Nenhum vídeo disponível — usando vídeo de teste")
        rows = [{
            "id": 683, "series_slug": "narcisismo", "pub_order": 1,
            "title": "Narcisismo encoberto: 3 sinais que você ignora",
            "script": (
                "Você convive com alguém que sempre parece ter razão, "
                "nunca pede desculpas, mas nunca grita?\n\n"
                "Isso é o narcisismo encoberto. E a neurociência de Harvard "
                "prova que é mais perigoso que o clássico.\n\n"
                "Na verdade, a pesquisa de Russ Malkin revelou: o cérebro "
                "narcísico tem hiperatividade na amígdala ao receber crítica.\n\n"
                "Por isso ele nunca muda — mudar é existencialmente ameaçador.\n\n"
                "Você já viveu isso? Me conta nos comentários — isso salva pessoas."
            )
        }]

    ok = 0
    for row in rows[:MAX_V]:
        if render(row): ok += 1

    log(f"\n✅ {ok}/{len(rows[:MAX_V])} vídeos renderizados")

if __name__ == "__main__":
    main()
