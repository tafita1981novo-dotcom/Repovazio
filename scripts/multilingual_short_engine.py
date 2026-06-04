#!/usr/bin/env python3
"""
multilingual_short_engine.py - Shorts virais em 8 idiomas
IDIOMAS: PT, EN, ES, DE, FR, IT, JA, KO
ESTRATEGIA:
  - Script original em PT-BR
  - Traducao via LLM (Groq Llama 3.3) 
  - TTS com voz nativa de cada idioma
  - Upload para canal PT (com legendas) + canais locais
CPM por idioma: DE=$12 > EN=$10 > FR=$7 > IT=$6 > ES=$5 > KO=$4 > JA=$4 > PT=$2
"""
import os, sys, json, re, time, subprocess, pathlib, shutil, random, wave, struct
import urllib.request, urllib.parse
from datetime import datetime

SBU = os.environ.get("SUPABASE_URL","")
SBK = os.environ.get("SUPABASE_SERVICE_KEY","")
GROQ_KEY = os.environ.get("GROQ_API_KEY","")
YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
MAX = int(os.environ.get("MAX_PER_LANG","1"))

W, H = 1080, 1920
TMP = pathlib.Path("/tmp/multilang"); TMP.mkdir(exist_ok=True)

# Configuracao de idiomas: (codigo_edge_tts, nome_voz, codigo_lang)
IDIOMAS = {
    "en": ("en-US-AriaNeural",     "+12%", "English",   "en"),
    "es": ("es-ES-ElviraNeural",   "+10%", "Espanol",   "es"),
    "de": ("de-DE-KatjaNeural",    "+8%",  "Deutsch",   "de"),
    "fr": ("fr-FR-DeniseNeural",   "+10%", "Francais",  "fr"),
    "it": ("it-IT-ElsaNeural",     "+10%", "Italiano",  "it"),
    "ja": ("ja-JP-NanamiNeural",   "+5%",  "Japanese",  "ja"),
    "ko": ("ko-KR-SunHiNeural",    "+8%",  "Korean",    "ko"),
}

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERRO {m}", flush=True, file=sys.stderr)

def ffm():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    for p in [shutil.which("ffmpeg"),"/usr/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists(): return p
    return "ffmpeg"

def ff(*args, t=120):
    return subprocess.run([ffm(), *args], capture_output=True, timeout=t)

def get_yt_token():
    data = urllib.parse.urlencode({
        "client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read()).get("access_token","")

def sb(ep, params="", method="GET", data=None):
    url = f"{SBU}/rest/v1/{ep}?{params}"
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
    req.add_header("Content-Type","application/json"); req.add_header("Prefer","return=minimal")
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            return json.loads(r.read()) if method=="GET" else {}
    except: return [] if method=="GET" else {}

def patch(id_, data):
    sb(f"content_pipeline",f"id=eq.{id_}","PATCH",json.dumps(data).encode())

def traduzir_groq(texto_pt, idioma_alvo, nome_idioma):
    """Traduz script para o idioma alvo mantendo estrutura viral"""
    if not GROQ_KEY: return None
    
    system_prompt = f"""You are a professional psychology content translator.
Translate the Brazilian Portuguese psychology script to {nome_idioma}.
Rules:
- Keep the exact 5-paragraph structure (hook, signal, science, shocking reveal, CTA)
- Adapt idioms naturally to {nome_idioma} culture
- Keep emotional intensity and scientific references
- CTA should fit {nome_idioma} YouTube conventions
- Return ONLY the translated text, no explanations"""

    body = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Translate to {nome_idioma}:\n\n{texto_pt}"}
        ],
        "max_tokens": 600,
        "temperature": 0.3
    }).encode()

    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body)
    req.add_header("Authorization", f"Bearer {GROQ_KEY}")
    req.add_header("Content-Type","application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
        return d["choices"][0]["message"]["content"].strip()
    except Exception as e:
        err(f"Groq traducao {idioma_alvo}: {e}")
        return None

def gerar_tts(texto, out, voice, rate="+10%"):
    texto_clean = re.sub(r"[*_#\[\]]","",texto)[:600]
    r = subprocess.run(
        ["edge-tts", f"--voice={voice}", f"--rate={rate}",
         "--volume=+15%", "--text", texto_clean, "--write-media", str(out)],
        capture_output=True, timeout=60)
    if r.returncode==0 and pathlib.Path(out).exists():
        sz=pathlib.Path(out).stat().st_size
        if sz>500: return sz
    return 0

def get_duracao(path):
    try:
        ffbin=ffm()
        r=subprocess.run([ffbin,"-i",str(path),"-f","null","-"],capture_output=True,timeout=20)
        m=re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)",r.stderr.decode())
        if m:
            h,mn,s=m.groups(); return float(h)*3600+float(mn)*60+float(s)
    except: pass
    try: return pathlib.Path(path).stat().st_size/16000.0
    except: return 0.0

def imagem_hf(prompt, out, seed):
    HFT = os.environ.get("HF_TOKEN","")
    if not HFT: return False
    body = json.dumps({
        "inputs": prompt[:150],
        "parameters": {"width":576,"height":1024,"num_inference_steps":4,"seed":seed,"guidance_scale":0.0}
    }).encode()
    req = urllib.request.Request(
        "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",data=body)
    req.add_header("Authorization", f"Bearer {HFT}")
    req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
        if len(data)>10000 and data[:4] in (b"\xff\xd8\xff",b"\x89PNG"):
            try:
                from PIL import Image; import io
                img = Image.open(io.BytesIO(data)).resize((W,H))
                img.save(out,"JPEG",quality=92)
            except: open(out,"wb").write(data)
            return True
    except: pass
    return False

def imagem_proc(out, seed, tema="default"):
    try:
        from PIL import Image, ImageDraw, ImageFilter
        random.seed(seed)
        P={"default":[(6,6,15),(124,58,237)]}
        bg,c1=P.get(tema,P["default"])
        img=Image.new("RGB",(W,H),bg); draw=ImageDraw.Draw(img)
        for y in range(H):
            t=(y/H)**0.7; c=tuple(min(255,int(bg[j]+(c1[j]-bg[j])*t*0.8)) for j in range(3))
            draw.line([(0,y),(W,y)],fill=c)
        cx,cy,r1=W//2,int(H*0.42),int(W*0.24)
        for i in range(6,0,-1):
            draw.ellipse([(cx-r1-i*8,cy-r1-i*8),(cx+r1+i*8,cy+r1+i*8)],fill=(*c1,20*i))
        draw.ellipse([(cx-r1,cy-r1),(cx+r1,cy+r1)],fill=(*c1,180))
        for e in range(200):
            a=int(140*(1-e/200))
            draw.line([(0,e),(W,e)],fill=(0,0,0,a)); draw.line([(0,H-1-e),(W,H-1-e)],fill=(0,0,0,a))
        img.filter(ImageFilter.GaussianBlur(0.5)).save(out,"JPEG",quality=92)
        return True
    except: return False

def render_short_lang(script_pt, lang_code, vid_id, work):
    """Renderiza um short em um idioma especifico"""
    if lang_code not in IDIOMAS:
        err(f"Idioma nao suportado: {lang_code}"); return None

    voice, rate, nome, _ = IDIOMAS[lang_code]
    log(f"  Traduzindo para {nome}...")

    # Traduzir
    script_lang = traduzir_groq(script_pt, lang_code, nome)
    if not script_lang:
        err(f"Traducao falhou para {lang_code}"); return None

    # Dividir em 5 cenas
    paragrafos = [p.strip() for p in re.split(r"\n\n+", script_lang) if len(p.strip())>10]
    if len(paragrafos) < 3:
        paragrafos = re.split(r"(?<=[.!?])\s+", script_lang)
        paragrafos = [p.strip() for p in paragrafos if len(p.strip())>10]

    # Limitar a 5 cenas
    cenas = paragrafos[:5]
    if len(cenas) < 3: err(f"Script {lang_code} muito curto"); return None

    clips = []
    dur_total = 0.0

    for i, cena in enumerate(cenas):
        seed = 9001 + vid_id*77 + i*13 + ord(lang_code[0])*1000

        # TTS
        mp3 = work/f"tts_{lang_code}_{i:02d}.mp3"
        sz = gerar_tts(cena, mp3, voice, rate)
        if not sz: continue

        # Converter mp3 -> wav
        wav = work/f"tts_{lang_code}_{i:02d}.wav"
        ff("-y","-i",str(mp3),"-acodec","pcm_s16le","-ar","44100","-ac","2",str(wav),t=30)
        aud = wav if wav.exists() else mp3
        dur = get_duracao(aud) or sz/16000.0

        # Pausa
        if i < len(cenas)-1:
            pausa=work/f"p_{lang_code}_{i:02d}.wav"; sr=44100; n=int(0.35*sr)
            with wave.open(str(pausa),"w") as wf:
                wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
                wf.writeframes(b"\x00"*4*n)
            cat=work/f"cat_{lang_code}_{i:02d}.txt"
            cat.write_text(f"file '{aud}'\nfile '{pausa}'")
            aud2=work/f"aud_{lang_code}_{i:02d}.wav"
            ff("-y","-f","concat","-safe","0","-i",str(cat),"-acodec","pcm_s16le","-ar","44100","-ac","2",str(aud2),t=30)
            if aud2.exists(): aud=aud2; dur=get_duracao(aud) or (dur+0.35)

        # Imagem
        img = work/f"img_{lang_code}_{i:03d}.jpg"
        prompt = f"psychology human emotion {nome} style cinematic 4k portrait, {cena[:60]}"
        if not imagem_hf(prompt, img, seed):
            imagem_proc(img, seed)

        # Clip
        d = max(dur, 1.0)
        vf = f"scale={W+40}:{H+40},crop={W}:{H}:'(iw-{W})*t/{d}':'(ih-{H})*0.5'"
        clip = work/f"clip_{lang_code}_{i:03d}.mp4"
        r = ff("-y",
               "-loop","1","-t",str(d+0.05),"-i",str(img),
               "-i",str(aud),"-vf",vf,
               "-c:v","libx264","-preset","ultrafast","-crf","20",
               "-pix_fmt","yuv420p","-r","25",
               "-c:a","aac","-b:a","192k","-ac","2","-ar","48000",
               "-shortest","-movflags","+faststart",str(clip),t=90)
        if r.returncode==0 and clip.exists():
            clips.append(clip); dur_total+=dur

    if not clips: return None

    # Concatenar
    cat_f = work/f"concat_{lang_code}.txt"
    cat_f.write_text("\n".join(f"file '{c}'" for c in clips))
    out_mp4 = work/f"final_{lang_code}.mp4"
    ff("-y","-f","concat","-safe","0","-i",str(cat_f),"-c","copy",str(out_mp4),t=60)

    if out_mp4.exists() and get_duracao(out_mp4) > 30:
        log(f"  {nome}: {get_duracao(out_mp4):.1f}s OK")
        return str(out_mp4)
    return None

def publicar_youtube(token, path, title, desc, lang_code, tags):
    """Publica o video no YouTube"""
    file_size = pathlib.Path(path).stat().st_size
    snippet = {
        "title": title[:100], "description": desc[:4000],
        "tags": tags[:15], "categoryId": "22",
        "defaultLanguage": lang_code, "defaultAudioLanguage": lang_code
    }
    status = {"privacyStatus":"public","selfDeclaredMadeForKids":False,"madeForKids":False}
    body = json.dumps({"snippet":snippet,"status":status}).encode()

    init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
    req = urllib.request.Request(init_url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type","application/json")
    req.add_header("X-Upload-Content-Type","video/mp4")
    req.add_header("X-Upload-Content-Length", str(file_size))
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            upload_url = r.headers.get("Location","")
    except urllib.error.HTTPError as e:
        err_b = e.read().decode()[:200]
        err(f"Init upload {lang_code}: {e.code} | {err_b}")
        return None

    if not upload_url: return None

    with open(path,"rb") as f:
        video_data = f.read()
    req2 = urllib.request.Request(upload_url, data=video_data, method="PUT")
    req2.add_header("Content-Type","video/mp4")
    req2.add_header("Content-Length", str(file_size))
    try:
        with urllib.request.urlopen(req2, timeout=300) as r:
            result = json.loads(r.read())
        return result.get("id","")
    except urllib.error.HTTPError as e:
        err(f"Upload {lang_code}: {e.code}")
        return None

def main():
    log("="*65)
    log("MULTILINGUAL SHORT ENGINE — 8 idiomas, max CPM global")
    log(f"Idiomas: EN ES DE FR IT JA KO (CPM alto)")
    log("="*65)

    # Buscar videos prontos em PT para traduzir
    rows = sb("content_pipeline",
              "select=id,title,script,youtube_title,series_slug"
              "&status=eq.mp4_ready"
              "&quality_score_current=gte.95"
              "&mp4_url=not.is.null"
              f"&limit={MAX*4}")

    if not rows:
        err("Sem videos prontos para traducao!")
        return

    log(f"Videos disponiveis: {len(rows)}")

    # Obter token YT
    token = get_yt_token()
    if not token: err("Sem token YT!"); return

    ok_total = 0
    for row in rows[:MAX]:
        vid_id = row["id"]
        title_pt = row.get("youtube_title") or row.get("title") or ""
        script_pt = row.get("script","") or title_pt

        log(f"\n  Video #{vid_id}: {title_pt[:50]}")
        work = TMP/f"v{vid_id}_{int(time.time())}"; work.mkdir(parents=True,exist_ok=True)

        # Prioridade: DE > EN > ES > FR > IT > KO > JA (CPM order)
        langs_priority = ["de","en","es","fr","it","ko","ja"]

        for lang_code in langs_priority:
            voice, rate, nome, _ = IDIOMAS[lang_code]
            log(f"\n    [{nome.upper()}] Gerando short...")

            mp4_path = render_short_lang(script_pt, lang_code, vid_id, work)

            if mp4_path:
                # Traduzir titulo
                title_lang = traduzir_groq(title_pt[:80], lang_code, nome) or title_pt
                title_lang = title_lang[:100]

                # Tags por idioma
                tags_por_idioma = {
                    "en": ["psychology","behavior","narcissism","anxiety","mental health","daniela"],
                    "es": ["psicologia","comportamiento","narcisismo","ansiedad","salud mental"],
                    "de": ["psychologie","verhalten","narzissmus","angst","mentale gesundheit"],
                    "fr": ["psychologie","comportement","narcissisme","anxiete","sante mentale"],
                    "it": ["psicologia","comportamento","narcisismo","ansia","salute mentale"],
                    "ja": ["心理学","行動","ナルシシズム","不安","メンタルヘルス"],
                    "ko": ["심리학","행동","나르시시즘","불안","정신건강"],
                }
                tags = tags_por_idioma.get(lang_code, [])

                desc = f"Daniela Coelho — Psychology Researcher\n\n#{title_lang}\n\n@psidanicoelho"

                yt_id = publicar_youtube(token, mp4_path, title_lang, desc, lang_code, tags)
                if yt_id:
                    log(f"    PUBLICADO [{nome}]: youtube.com/watch?v={yt_id}")
                    ok_total += 1
                else:
                    log(f"    Publicacao [{nome}] falhou (quota?)")
                time.sleep(3)

    log(f"\n{'='*65}")
    log(f"RESULTADO: {ok_total} videos publicados em multiplos idiomas")

if __name__ == "__main__":
    main()
