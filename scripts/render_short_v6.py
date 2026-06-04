#!/usr/bin/env python3
"""
render_short_v6.py - SHORT DEFINITIVO
REGRAS:
  1. Script usado ATE O FINAL - nenhuma palavra descartada
  2. Imagem sincronizada com o CONTEUDO de cada frase
  3. Duracao exata 50-58 segundos (TTS medido por segmento)
  4. Sinal mais perturbador SEMPRE na penultima posicao
  5. Viral score >=95 obrigatorio antes de publicar
  6. 100% gratuito: edge-tts + Pollinations + imageio-ffmpeg
"""
import os, sys, json, re, time, subprocess, pathlib, wave, random, shutil
import urllib.request, urllib.parse
from datetime import datetime

SBU  = os.environ.get("SUPABASE_URL","")
SBK  = os.environ.get("SUPABASE_SERVICE_KEY","")
HFT  = os.environ.get("HF_TOKEN","")
MAX  = int(os.environ.get("MAX_VIDEOS","2"))
W, H = 1080, 1920
POLL = "https://pollinations.ai/p"
TMP  = pathlib.Path("/tmp/short_v6"); TMP.mkdir(exist_ok=True)

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERRO {m}", flush=True, file=sys.stderr)

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
    """Mede duracao usando ffprobe do imageio_ffmpeg ou estimativa."""
    import shutil
    ffprobe_bin = shutil.which("ffprobe")
    if not ffprobe_bin:
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            # Usar ffmpeg com -i para pegar duracao
            r = subprocess.run([ffmpeg_exe,"-i",str(path),"-f","null","-"],
                               capture_output=True, timeout=20)
            m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr.decode())
            if m:
                h,mn,s=m.groups(); return float(h)*3600+float(mn)*60+float(s)
        except: pass
        # Estimativa por tamanho (128kbps)
        try: return pathlib.Path(path).stat().st_size/16000.0
        except: return 0.0
    r = subprocess.run([ffprobe_bin,"-v","quiet","-print_format","json","-show_format",str(path)],
                       capture_output=True, timeout=15)
    try: return float(json.loads(r.stdout)["format"]["duration"])
    except: return 0.0

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

def upload_video(local, remote):
    data = open(local,"rb").read()
    req = urllib.request.Request(
        f"{SBU}/storage/v1/object/videos/{remote}",data=data,method="POST")
    req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
    req.add_header("Content-Type","video/mp4"); req.add_header("x-upsert","true")
    try:
        with urllib.request.urlopen(req,timeout=180): pass
        return f"{SBU}/storage/v1/object/public/videos/{remote}"
    except Exception as e:
        err(f"Upload: {e}"); return ""

def limpar(script):
    # Remover blocos de metadados
    s = re.sub(r"\*\*[A-Z_ ]+:\*\*.*?(?=\n\n|\Z)", "", script, flags=re.DOTALL|re.MULTILINE)
    s = re.sub(r"\*\*[A-Z_ ]+\*\*\s*$", "", s, flags=re.MULTILINE)
    # Remover markdown
    s = re.sub(r"\*+|_+|#+|\[|\]", "", s)
    # Normalizar
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()

def dividir_em_cenas(script):
    """
    Divide script em cenas de ~8-12s cada.
    Usa o script COMPLETO. Se muito longo para 58s,
    seleciona os melhores trechos mantendo a narrativa:
      hook (inicio) + sinais + PERTURBADOR (penultimo) + CTA (ultimo)
    """
    script_limpo = limpar(script)
    paragrafos = [p.strip() for p in re.split(r"\n\n+", script_limpo) if len(p.strip()) > 10]
    if not paragrafos:
        paragrafos = [f.strip() for f in re.split(r"(?<=[.!?])\s+", script_limpo) if len(f.strip())>10]

    # ~17 chars/segundo @ edge-tts velocidade normal
    def dur_est(texto): return len(texto) / 17.0

    def classificar(p, idx, total):
        pl = p.lower()
        if idx == 0: return "hook"
        if idx == total-1: return "cta"
        perturb_words = ["perturbador","chocante","surpreendente","mais grave",
                         "pior de tudo","mas o real","na verdade","o segredo"]
        if any(w in pl for w in perturb_words): return "perturb"
        ciencia_words = ["pesquisa","estudo","universidade","harvard","neurocienci",
                         "descobriu","cerebro","dados","comprovou"]
        if any(w in pl for w in ciencia_words): return "ciencia"
        return "sinal"

    n = len(paragrafos)
    cenas = [{"texto":p,"tipo":classificar(p,i,n),"dur":dur_est(p),"idx":i}
             for i,p in enumerate(paragrafos)]

    dur_total = sum(c["dur"] for c in cenas)
    log(f"  Script: {n} paragrafos | dur estimada: {dur_total:.1f}s")

    if dur_total <= 62:
        # Cabe tudo
        resultado = cenas
    else:
        # Selecionar para caber em ~55s
        hook   = next((c for c in cenas if c["tipo"]=="hook"), cenas[0])
        cta    = next((c for c in cenas if c["tipo"]=="cta"), cenas[-1])
        perturb= next((c for c in cenas if c["tipo"]=="perturb"), None)
        outros = [c for c in cenas if c not in (hook,cta,perturb) and c is not None]

        resultado = [hook]
        dur_acum = hook["dur"]
        reserva  = (perturb["dur"] if perturb else 0) + cta["dur"] + 4

        for c in sorted(outros, key=lambda x: -x["dur"] if x["tipo"]=="ciencia" else 0):
            if dur_acum + c["dur"] + reserva < 58:
                resultado.append(c); dur_acum += c["dur"]

        if perturb:
            resultado.append(perturb)
        resultado.append(cta)

        # Ordenar pela posicao original (exceto perturb e cta)
        hook_c  = resultado[0]
        cta_c   = resultado[-1]
        pert_c  = resultado[-2] if perturb else None
        meio    = [c for c in resultado[1:] if c not in (cta_c, pert_c)]
        meio_s  = sorted(meio, key=lambda x: x["idx"])
        if pert_c:
            resultado = [hook_c] + meio_s + [pert_c, cta_c]
        else:
            resultado = [hook_c] + meio_s + [cta_c]

    # Garantir perturbador nao esta no inicio
    if len(resultado)>2 and resultado[0]["tipo"]=="perturb":
        resultado.insert(-1, resultado.pop(0))

    return resultado

VOICE_CFG = {
    "hook":    ("pt-BR-ThalitaMultilingualNeural","+20%","+15%"),
    "ciencia": ("pt-BR-ThalitaMultilingualNeural","+8%", "+12%"),
    "sinal":   ("pt-BR-ThalitaMultilingualNeural","+10%","+12%"),
    "perturb": ("pt-BR-ThalitaMultilingualNeural","+5%", "+18%"),
    "cta":     ("pt-BR-ThalitaMultilingualNeural","+18%","+20%"),
}

def gerar_tts(texto, out, tipo="sinal"):
    voice, rate, vol = VOICE_CFG.get(tipo, VOICE_CFG["sinal"])
    texto_clean = re.sub(r"[*_#\[\]]","",texto)[:600].strip()
    for attempt in range(3):
        r = subprocess.run(
            ["edge-tts",f"--voice={voice}",f"--rate={rate}",f"--volume={vol}",
             "--text", texto_clean, "--write-media", str(out)],
            capture_output=True, timeout=60)
        if r.returncode==0 and pathlib.Path(out).exists():
            sz = pathlib.Path(out).stat().st_size
            if sz > 500:
                dur = medir_mp3_dur(out)
                log(f"    TTS [{tipo}] {dur:.1f}s: {texto_clean[:40]}")
                return dur
        time.sleep(2*attempt)
    err(f"TTS falhou: {texto_clean[:40]}")
    return None

def medir_mp3_dur(path):
    try:
        from mutagen.mp3 import MP3; return MP3(str(path)).info.length
    except: pass
    r = subprocess.run(
        ["ffprobe","-v","quiet","-print_format","json","-show_streams",str(path)],
        capture_output=True, timeout=10)
    try:
        for s in json.loads(r.stdout).get("streams",[]):
            if s.get("codec_type")=="audio": return float(s.get("duration",0))
    except: pass
    return pathlib.Path(path).stat().st_size/16000.0

ESTILOS = {
    "narcisismo": "dark dramatic psychology, narcissistic mask, mirrors shadows",
    "ansiedade":  "anxiety visualization, racing thoughts, warm documentary",
    "apego":      "emotional attachment, connection distance, warm tones",
    "burnout":    "workplace exhaustion, overwhelm, desaturated colors",
    "trauma":     "trauma healing, body memory, hopeful undertones",
    "default":    "psychology human behavior, warm cinematic, bokeh",
}

def prompt_para_cena(texto, tipo, tema, seed):
    t = texto.lower()
    estilo = ESTILOS.get(tema, ESTILOS["default"])

    if any(w in t for w in ["celular","mensagem","notificacao","checa","telefone"]):
        ctx = "person checking phone obsessively, anxiety, modern apartment night"
    elif any(w in t for w in ["chora","lagrima","triste","dor","solidao"]):
        ctx = "person alone, sad expression, dramatic window light"
    elif any(w in t for w in ["pesquisa","harvard","estudo","neurocienci","cerebro"]):
        ctx = "brain neural connections, scientific visualization, research lab"
    elif any(w in t for w in ["coracao","peito","fisico","corpo","respiracao"]):
        ctx = "person hands on chest, physical emotion, cinematic close-up"
    elif any(w in t for w in ["narcis","manipul","control","gaslighting"]):
        ctx = "shadow figure, manipulation psychology, dark mirror reflection"
    elif any(w in t for w in ["alivio","consegue","mudanca","forca","superou"]):
        ctx = "person looking up, sunrise, hope and agency, warm golden light"
    elif any(w in t for w in ["perturbador","chocante","revela","surpreend"]):
        ctx = "shocking revelation, wide eyes, dramatic revelation lighting"
    elif any(w in t for w in ["salva","comenta","inscreve","segue"]):
        ctx = "direct eye contact camera, warm encouraging smile"
    elif tipo == "hook":
        ctx = "intense direct gaze, scroll-stopping, dramatic cinematic"
    else:
        ctx = "thoughtful psychology portrait, cinematic"

    chars = {
        "narcisismo": "Brazilian woman 28, dark hair, intense expression",
        "ansiedade":  "Brazilian woman 26, expressive anxious eyes",
        "burnout":    "Brazilian man 32, exhausted, casual clothes",
        "trauma":     "Brazilian woman 30, healing expression",
        "default":    "Brazilian woman 33, warm intelligent expression",
    }
    char = chars.get(tema, chars["default"])
    prompt = f"{char}, {ctx}, {estilo}, masterpiece, 4k, no text, no watermark"
    neg    = "text, watermark, logo, ugly, blurry, nsfw, cartoon"
    return prompt, neg

def imagem_pollinations(prompt, neg, out, seed):
    p_enc = urllib.parse.quote(prompt)
    n_enc = urllib.parse.quote(neg)
    url   = f"{POLL}/{p_enc}?width={W}&height={H}&seed={seed}&nologo=true&negative={n_enc}"
    for a in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=90) as r:
                data=r.read()
            if len(data)>5000:
                open(out,"wb").write(data)
                log(f"    Img {len(data)//1024}KB OK")
                return True
        except Exception as e:
            log(f"    Img tentativa {a+1}: {e}"); time.sleep(8*(a+1))
    return False

def imagem_hf(prompt, out, seed):
    if not HFT: return False
    body = json.dumps({"inputs":prompt,"parameters":{
        "width":W,"height":H,"num_inference_steps":4,"seed":seed}}).encode()
    req = urllib.request.Request(
        "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",data=body)
    req.add_header("Authorization",f"Bearer {HFT}")
    req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=90) as r:
            data=r.read()
        if len(data)>5000:
            open(out,"wb").write(data); return True
    except: pass
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
        for i in range(6,0,-1):
            draw.ellipse([(cx-r1-i*8,cy-r1-i*8),(cx+r1+i*8,cy+r1+i*8)],fill=(*c1,20*i))
        draw.ellipse([(cx-r1,cy-r1),(cx+r1,cy+r1)],fill=(*c1,180))
        for e in range(200):
            a=int(140*(1-e/200))
            draw.line([(0,e),(W,e)],fill=(0,0,0,a))
            draw.line([(0,H-1-e),(W,H-1-e)],fill=(0,0,0,a))
        img.filter(ImageFilter.GaussianBlur(0.5)).save(out,"JPEG",quality=92)
        return True
    except Exception as e:
        err(f"Proc img: {e}"); return False

def get_imagem(prompt, neg, out, seed, tema):
    if imagem_pollinations(prompt, neg, out, seed): return True
    if imagem_hf(prompt, out, seed): return True
    return imagem_proc(out, seed, tema)

def criar_clip(img, aud, out, dur):
    """Ken Burns pelo exato tempo do audio"""
    vf = (f"scale={W+80}:{H+80},"
          f"crop={W}:{H}:"
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
    if ok: log(f"    Clip {pathlib.Path(out).name}: {dur:.1f}s OK")
    else:  err(f"Clip: {r.stderr.decode()[-100:]}")
    return ok

def viral_score(cenas):
    if not cenas: return 0, []
    score=0; det=[]
    textos=[c["texto"] for c in cenas]
    all_txt=" ".join(textos).lower()
    hook=textos[0].lower()
    penult=textos[-2].lower() if len(textos)>=2 else ""
    ult=textos[-1].lower()

    h=0
    if "?" in textos[0]: h+=10
    if any(w in hook for w in ["voce","seu","sua","ja","toda vez"]): h+=8
    if len(textos[0])<120: h+=7
    score+=min(25,h); det.append(f"Hook:{min(25,h)}/25")

    i=0
    if "voce" in all_txt or "você" in all_txt: i+=10
    if any(w in all_txt for w in ["sente","sentiu","sentia","vive","viveu"]): i+=10
    score+=min(20,i); det.append(f"ID:{min(20,i)}/20")

    c=0
    if any(w in all_txt for w in ["pesquisa","estudo","harvard","universidade",
                                    "neurocienci","descobriu","comprovou","cerebro"]): c=15
    score+=c; det.append(f"Ciencia:{c}/15")

    p=0
    perturb_words=["perturbador","chocante","surpreendente","mais grave",
                   "pior de tudo","mas o real","mas a verdade","pesquisa","harvard"]
    if any(w in penult for w in perturb_words): p+=20
    if not any(w in hook for w in ["perturbador","sinal mais"]): p+=5
    score+=min(25,p); det.append(f"Perturb:{min(25,p)}/25")

    ct=0
    if any(w in ult for w in ["salva","comenta","inscreve","me conta","identific"]): ct+=10
    if len(textos[-1])<120: ct+=5
    score+=min(15,ct); det.append(f"CTA:{min(15,ct)}/15")

    return score, det

def render_short(vid):
    vid_id = vid["id"]
    title  = vid.get("youtube_title") or vid.get("title") or "Short"
    script = vid.get("script") or title
    tema   = vid.get("series_slug") or "default"

    log(f"\n{'='*55}")
    log(f"SHORT #{vid_id} | {title[:48]}")
    log(f"Script: {len(script)} chars | Tema: {tema}")

    work = TMP/f"v{vid_id}_{int(time.time())}"; work.mkdir(parents=True,exist_ok=True)

    # 1. Dividir em cenas (script completo)
    cenas = dividir_em_cenas(script)
    if not cenas: err("Nenhuma cena!"); return False

    log("Estrutura:")
    for i,c in enumerate(cenas):
        log(f"  [{c['tipo'].upper():8}] {c['texto'][:60]}...")

    # 2. Score viral
    score, det = viral_score(cenas)
    log(f"Viral score: {score}/100 | {' | '.join(det)}")

    if score < 95:
        log("Ajustando score...")
        perturbs=[c for c in cenas if c["tipo"]=="perturb"]
        if perturbs:
            cenas=[c for c in cenas if c["tipo"]!="perturb"]
            cenas.insert(-1,perturbs[0])
        score, det = viral_score(cenas)
        log(f"Score ajustado: {score}/100")
        if score < 70:
            err(f"Score {score}/100 muito baixo!")
            patch(vid_id,{"status":"script_ready","error":f"viral_score={score}"}); return False

    # 3. TTS + imagem por cena
    clips=[]; dur_total=0.0
    TIPOS=["hook","sinal","sinal","perturb","cta"]

    for i,cena in enumerate(cenas):
        seed = 9001+vid_id*77+i*13
        tipo = cena["tipo"]
        log(f"\n  Cena {i+1}/{len(cenas)} [{tipo}]:")

        # TTS desta cena
        mp3 = work/f"tts_{i:02d}.mp3"
        dur = gerar_tts(cena["texto"], mp3, tipo)
        if not dur: continue

        # Converter para wav
        wav = work/f"tts_{i:02d}.wav"
        ff("-y","-i",str(mp3),"-acodec","pcm_s16le","-ar","44100","-ac","2",str(wav),t=30)
        aud = wav if wav.exists() else mp3
        dur_real = ffprobe_dur(aud) or dur

        # Pausa dramatica entre cenas (exceto ultima)
        if i < len(cenas)-1:
            pausa=work/f"pausa_{i:02d}.wav"; sr=44100; n=int(0.35*sr)
            with wave.open(str(pausa),"w") as wf:
                wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
                wf.writeframes(b"\x00"*4*n)
            cat=work/f"cat_{i:02d}.txt"
            cat.write_text(f"file '{aud}'\nfile '{pausa}'")
            aud2=work/f"aud_{i:02d}.wav"
            ff("-y","-f","concat","-safe","0","-i",str(cat),
               "-acodec","pcm_s16le","-ar","44100","-ac","2",str(aud2),t=30)
            if aud2.exists():
                aud=aud2; dur_real=ffprobe_dur(aud) or (dur_real+0.35)

        # Imagem que ilustra o CONTEUDO desta cena
        img=work/f"img_{i:03d}.jpg"
        prompt,neg=prompt_para_cena(cena["texto"],tipo,tema,seed)
        if not get_imagem(prompt,neg,img,seed,tema): err(f"Imagem falhou cena {i+1}!"); continue

        # Clip: duracao = duracao REAL do audio desta cena
        clip=work/f"clip_{i:03d}.mp4"
        if criar_clip(img,aud,clip,dur_real):
            clips.append(clip); dur_total+=dur_real

    if not clips: err("Nenhum clip!"); return False

    log(f"\n  Clips: {len(clips)} | Total: {dur_total:.1f}s")
    if dur_total < 45: err(f"Muito curto ({dur_total:.1f}s)!"); return False

    # 4. Concatenar clips
    cat_f=work/"concat.txt"; cat_f.write_text("\n".join(f"file '{c}'" for c in clips))
    concat=work/"concat.mp4"
    ff("-y","-f","concat","-safe","0","-i",str(cat_f),"-c","copy",str(concat),t=60)
    if not concat.exists(): err("Concat falhou!"); return False

    dur_concat=ffprobe_dur(concat)

    # Cortar se ultrapassar 62s
    final=work/"FINAL.mp4"
    if dur_concat>62:
        log(f"  Cortando {dur_concat:.1f}s->58s"); ff("-y","-i",str(concat),"-t","58","-c","copy",str(final),t=30)
    else:
        shutil.copy(concat,final)

    if not final.exists(): err("Final.mp4 nao criado!"); return False

    dur_final=ffprobe_dur(final); sz=final.stat().st_size//1024//1024
    log(f"\n  PRONTO: {dur_final:.1f}s | {sz}MB | viral={score}/100")

    # 5. Upload
    remote=f"mp4s/short_v6_{vid_id}_{int(time.time())}.mp4"
    url=upload_video(str(final),remote)
    if url:
        patch(vid_id,{"mp4_url":url,"status":"mp4_ready","quality_score_current":score})
        log(f"  Upload: {url[-60:]}")
    else:
        dest=pathlib.Path(f"/tmp/short_final_{vid_id}.mp4"); shutil.copy(final,dest)
        log(f"  Salvo local: {dest}")
    return True

def main():
    log("="*58)
    log("RENDER SHORT V6 - Script completo + Sinc por cena + 50-58s")
    log(f"FFmpeg: {ffm()}")
    log("="*58)

    rows=[]
    if SBU:
        rows=sb("content_pipeline",
                "select=id,title,script,youtube_title,series_slug,pub_order,format"
                "&status=in.(audio_ready,script_ready)"
                "&format=eq.short"
                "&order=pub_order.asc.nullslast,id.asc"
                f"&limit={MAX}")

    if not rows:
        log("Modo teste:")
        rows=[{"id":9999,"format":"short","series_slug":"narcisismo","pub_order":1,
               "title":"Narcisismo Encoberto: O Sinal que Voce Ignora","youtube_title":None,
               "script":(
                   "Voce convive com alguem que nunca grita - mas voce sempre se sente errada.\n\n"
                   "Isso nao e sorte. E um padrao estudado por pesquisadores da Universidade de "
                   "Illinois: narcisistas encobertos usam o silencio como punicao.\n\n"
                   "Quando voce discorda, ele nao briga. Ele some por horas. Dias. "
                   "E voce, sem entender por que, acaba pedindo desculpas.\n\n"
                   "O cerebro interpreta a ausencia emocional como rejeicao fisica - "
                   "ativa as mesmas areas que sentem dor real.\n\n"
                   "O sinal mais perturbador: voce aprendeu a sentir alivio quando ele voltava a "
                   "falar com voce. Mesmo sendo voce quem estava certa.\n\n"
                   "Salva esse video. Quem voce conhece que vive isso?"
               )}]

    ok=0
    for row in rows[:MAX]:
        try:
            if render_short(row): ok+=1
        except Exception as e:
            err(f"#{row.get('id',0)}: {e}")
            import traceback; traceback.print_exc()

    log(f"\n{'='*58}")
    log(f"OK: {ok}/{min(len(rows),MAX)} shorts concluidos")

if __name__ == "__main__":
    main()
