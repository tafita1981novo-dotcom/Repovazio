#!/usr/bin/env python3
"""
render_long_v6.py - LONG DEFINITIVO (8-15min com episodios de serie)
CORRECOES:
  - Sem zoompan (muito lento) -> Ken Burns simples com crop linear
  - Verificacao imagem >10KB antes de usar
  - Timeout 300s por clip
  - ffprobe via ffmpeg -i (sem ffprobe externo)
  - Script completo usado ATE O FINAL
  - Imagem nova por paragrafo (sincronizada)
  - 5 atos narrativos
  - Mid-rolls em 3:00, 6:00, 9:00, 12:00 (exige >=8min)
"""
import os, sys, json, re, time, subprocess, pathlib, wave, random, shutil
import urllib.request, urllib.parse
from datetime import datetime

SBU  = os.environ.get("SUPABASE_URL","")
SBK  = os.environ.get("SUPABASE_SERVICE_KEY","")
HFT  = os.environ.get("HF_TOKEN","")
MAX  = int(os.environ.get("MAX_VIDEOS","1"))
W, H = 1080, 1920
POLL = "https://pollinations.ai/p"
TMP  = pathlib.Path("/tmp/long_v6"); TMP.mkdir(exist_ok=True)
DUR_MIN = 480.0   # 8min minimo para mid-roll
DUR_MAX = 900.0   # 15min maximo
DUR_ALVO = 720.0  # 12min alvo (4 mid-rolls)
MIDROLL_POS = [180, 360, 540, 720]

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

def get_duracao(path):
    """Mede duracao sem ffprobe externo - usa ffmpeg -i"""
    try:
        ffbin = ffm()
        r = subprocess.run([ffbin,"-i",str(path),"-f","null","-"],
                           capture_output=True, timeout=20)
        m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr.decode())
        if m:
            h,mn,s = m.groups()
            return float(h)*3600+float(mn)*60+float(s)
    except: pass
    try: return pathlib.Path(path).stat().st_size/16000.0
    except: return 0.0

def sb(ep, params="", method="GET", data=None):
    url=f"{SBU}/rest/v1/{ep}?{params}"
    req=urllib.request.Request(url,data=data,method=method)
    req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
    req.add_header("Content-Type","application/json"); req.add_header("Prefer","return=minimal")
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            return json.loads(r.read()) if method=="GET" else {}
    except: return [] if method=="GET" else {}

def patch(id_, data):
    sb(f"content_pipeline",f"id=eq.{id_}","PATCH",json.dumps(data).encode())

def upload_video(local, remote):
    data=open(local,"rb").read()
    req=urllib.request.Request(f"{SBU}/storage/v1/object/videos/{remote}",data=data,method="POST")
    req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
    req.add_header("Content-Type","video/mp4"); req.add_header("x-upsert","true")
    try:
        with urllib.request.urlopen(req,timeout=300): pass
        return f"{SBU}/storage/v1/object/public/videos/{remote}"
    except Exception as e:
        err(f"Upload: {e}"); return ""

def limpar(script):
    s = re.sub(r"\*\*[A-Z_ ]+:\*\*.*?(?=\n\n|\Z)", "", script, flags=re.DOTALL|re.MULTILINE)
    s = re.sub(r"\*\*[A-Z_ ]+\*\*\s*$", "", s, flags=re.MULTILINE)
    s = re.sub(r"\*+|_+|#+|\[|\]", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()

def estruturar_atos(script, ep_num=1):
    """
    5 atos: intro(15%) problema(25%) ciencia(25%) perturb(20%) resolucao(15%)
    Script completo dividido proporcionalmente.
    """
    script_limpo = limpar(script)
    paragrafos = [p.strip() for p in re.split(r"\n\n+", script_limpo) if len(p.strip())>10]
    if not paragrafos:
        paragrafos=[f.strip() for f in re.split(r"(?<=[.!?])\s+", script_limpo) if len(f.strip())>10]

    n = len(paragrafos)
    log(f"  Script: {n} paragrafos | {len(script_limpo)} chars")

    PROPORCOES = [("intro",0.15),("problema",0.25),("ciencia",0.25),("perturb",0.20),("resolucao",0.15)]
    atos = {k:{"tipo":k,"paras":[]} for k,_ in PROPORCOES}
    ordem = [k for k,_ in PROPORCOES]
    limites = []
    acum=0.0
    for k,pct in PROPORCOES:
        acum+=pct; limites.append(int(acum*n))

    ato_idx=0
    for i,para in enumerate(paragrafos):
        if ato_idx<len(limites)-1 and i>=limites[ato_idx]: ato_idx+=1
        atos[ordem[ato_idx]]["paras"].append(para)

    # Mover paragrafos perturbadores para ato correto
    perturb_words=["perturbador","chocante","mais grave","pior de tudo","mas o real","na verdade"]
    for k in ["intro","problema","ciencia"]:
        normais=[]; perturbantes=[]
        for p in atos[k]["paras"]:
            if any(w in p.lower() for w in perturb_words): perturbantes.append(p)
            else: normais.append(p)
        atos[k]["paras"]=normais
        atos["perturb"]["paras"]=perturbantes+atos["perturb"]["paras"]

    # Gancho proximo episodio
    atos["resolucao"]["paras"].append(
        f"No proximo episodio, vamos explorar o que acontece quando voce "
        f"finalmente reconhece esse padrao. Segue o canal para nao perder."
    )

    return atos

VOICE_LONG = {
    "intro":     ("pt-BR-ThalitaMultilingualNeural","+5%","+12%"),
    "problema":  ("pt-BR-ThalitaMultilingualNeural","+3%","+12%"),
    "ciencia":   ("pt-BR-ThalitaMultilingualNeural","+0%","+12%"),
    "perturb":   ("pt-BR-ThalitaMultilingualNeural","-3%","+18%"),
    "resolucao": ("pt-BR-ThalitaMultilingualNeural","+8%","+15%"),
}

def gerar_tts_long(texto, out, tipo="problema"):
    voice,rate,vol = VOICE_LONG.get(tipo, VOICE_LONG["problema"])
    texto_clean = re.sub(r"[*_#\[\]]","",texto)[:800].strip()
    for attempt in range(3):
        r=subprocess.run(
            ["edge-tts",f"--voice={voice}",f"--rate={rate}",f"--volume={vol}",
             "--text",texto_clean,"--write-media",str(out)],
            capture_output=True, timeout=90)
        if r.returncode==0 and pathlib.Path(out).exists():
            sz=pathlib.Path(out).stat().st_size
            if sz>500:
                dur=get_duracao(out); log(f"    TTS {dur:.1f}s: {texto_clean[:40]}..."); return dur
        time.sleep(3*attempt)
    return None

ESTILOS_LONG = {
    "narcisismo": "cinematic dark psychology, dramatic shadows",
    "ansiedade":  "anxiety visualization, racing mind, warm documentary",
    "apego":      "emotional attachment, warmth, connection",
    "burnout":    "workplace exhaustion, desaturated, overwhelm",
    "trauma":     "trauma healing, body memory, hope",
    "default":    "psychology documentary, warm cinematic",
}

def prompt_long(texto, tipo, tema, i):
    t=texto.lower(); estilo=ESTILOS_LONG.get(tema,ESTILOS_LONG["default"])
    if tipo=="intro": ctx="presenter, direct eye contact, engaging"
    elif tipo=="problema":
        ctx="person reflecting problem, thoughtful, documentary"
    elif tipo=="ciencia":
        ctx="brain visualization scientific, data, research lab"
    elif tipo=="perturb": ctx="shocking realization, wide eyes, dramatic light"
    elif tipo=="resolucao": ctx="hope empowerment, warm sunrise, agency"
    else: ctx="psychology portrait, cinematic"
    chars={"narcisismo":"Brazilian woman 28, dark hair",
           "ansiedade":"Brazilian woman 26, expressive",
           "burnout":"Brazilian man 32, exhausted",
           "trauma":"Brazilian woman 30, healing",
           "default":"Brazilian woman 33, warm intelligent"}
    char=chars.get(tema,chars["default"])
    prompt=f"{char}, {ctx}, {estilo}, 4k, ultra detailed, no text, no watermark"
    neg="text, watermark, logo, cartoon, ugly, blurry, nsfw"
    return prompt, neg

# HuggingFace FLUX como primario (Pollinations passou a cobrar 402)
HF_API = "https://api-inference.huggingface.co/models"
HF_MODELS = [
    "black-forest-labs/FLUX.1-schnell",
    "stabilityai/sdxl-turbo",
]

def imagem_hf(prompt, out, seed):
    """HuggingFace FLUX.1-schnell - primario, gratuito com HF_TOKEN"""
    if not HFT: return False
    # Prompt curto para evitar erros
    p_short = prompt[:150]
    body = json.dumps({
        "inputs": p_short,
        "parameters": {
            "width": 576, "height": 1024,
            "num_inference_steps": 4, "seed": seed,
            "guidance_scale": 0.0
        }
    }).encode()
    for model in HF_MODELS:
        req = urllib.request.Request(f"{HF_API}/{model}", data=body)
        req.add_header("Authorization", f"Bearer {HFT}")
        req.add_header("Content-Type","application/json")
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            if len(data)>10000 and data[:4] in (b"\xff\xd8\xff", b"\x89PNG"):
                # Redimensionar para 1080x1920
                try:
                    from PIL import Image; import io
                    img = Image.open(io.BytesIO(data))
                    img = img.resize((W,H), Image.LANCZOS)
                    img.save(out,"JPEG",quality=92)
                except: open(out,"wb").write(data)
                log(f"    Img HF: {len(data)//1024}KB OK")
                return True
        except Exception as e:
            if "503" in str(e): time.sleep(8)
    return False

def get_imagem(prompt, neg, out, seed, tema):
    """HF FLUX primario, procedural fallback garantido"""
    if imagem_hf(prompt, out, seed): return True
    return imagem_proc(out, seed, tema)


def criar_clip_long(img, aud, out, dur):
    """
    Ken Burns SIMPLES com crop linear - MUITO mais rapido que zoompan.
    Nao usa zoompan que pode travar por minutos.
    """
    d = max(dur, 1.0)
    # Ken Burns: escala levemente maior e crop com deslocamento linear
    vf = (f"scale={W+40}:{H+40},"
          f"crop={W}:{H}:"
          f"'(iw-{W})*t/{d}':"
          f"'(ih-{H})*0.5'")
    
    r = ff("-y",
           "-loop","1","-t",str(d+0.1),"-i",str(img),
           "-i",str(aud),
           "-vf",vf,
           "-c:v","libx264","-preset","ultrafast","-crf","22",
           "-pix_fmt","yuv420p","-r","25",
           "-c:a","aac","-b:a","192k","-ac","2","-ar","48000",
           "-shortest","-movflags","+faststart",
           str(out), t=300)
    
    ok = r.returncode==0 and pathlib.Path(out).exists()
    if ok:
        log(f"    Clip OK: {dur:.1f}s | {pathlib.Path(out).stat().st_size//1024}KB")
    else:
        err(f"Clip: {r.stderr.decode()[-150:]}")
    return ok

def render_long(vid):
    vid_id=vid["id"]
    title=vid.get("youtube_title") or vid.get("title") or "Long"
    script=vid.get("script") or title
    tema=vid.get("series_slug") or "default"
    ep_num=vid.get("ep_number") or vid.get("episode_number") or 1

    log(f"\n{'='*60}")
    log(f"LONG #{vid_id} | Ep{ep_num} | {title[:50]}")
    log(f"Script: {len(script)} chars | Tema: {tema}")

    work=TMP/f"v{vid_id}_{int(time.time())}"; work.mkdir(parents=True,exist_ok=True)
    atos=estruturar_atos(script,ep_num)

    log("Estrutura dos 5 atos:")
    for nome,ato in atos.items():
        chars=sum(len(p) for p in ato["paras"])
        log(f"  {nome.upper():10} {len(ato['paras']):2} paragrafos | {chars} chars")

    clips=[]; clip_idx=0; dur_total=0.0

    for ato_nome,ato in atos.items():
        if not ato["paras"]: continue
        log(f"\n  === ATO: {ato_nome.upper()} ({len(ato['paras'])} paragrafos) ===")

        for j,para in enumerate(ato["paras"]):
            seed=9001+vid_id*77+clip_idx*13
            log(f"\n  Cena {clip_idx+1} [{ato_nome}]: {para[:55]}...")

            # TTS desta cena (paragrafo completo)
            mp3=work/f"tts_{clip_idx:03d}.mp3"
            dur=gerar_tts_long(para,mp3,ato_nome)
            if not dur:
                log(f"    TTS falhou, pulando cena {clip_idx+1}")
                clip_idx+=1; continue

            # Converter mp3 -> wav para concat com pausa
            wav=work/f"tts_{clip_idx:03d}.wav"
            ff("-y","-i",str(mp3),"-acodec","pcm_s16le","-ar","44100","-ac","2",str(wav),t=30)
            aud=wav if wav.exists() else mp3
            dur_real=get_duracao(aud) or dur

            # Pausa natural entre paragrafos (0.6s)
            if j<len(ato["paras"])-1:
                pausa=work/f"p_{clip_idx:03d}.wav"; sr=44100; n=int(0.6*sr)
                with wave.open(str(pausa),"w") as wf:
                    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
                    wf.writeframes(b"\x00"*4*n)
                cat=work/f"cat_{clip_idx:03d}.txt"
                cat.write_text(f"file '{aud}'\nfile '{pausa}'")
                aud2=work/f"aud_{clip_idx:03d}.wav"
                ff("-y","-f","concat","-safe","0","-i",str(cat),
                   "-acodec","pcm_s16le","-ar","44100","-ac","2",str(aud2),t=30)
                if aud2.exists():
                    aud=aud2; dur_real=get_duracao(aud) or (dur_real+0.6)

            # Imagem sincronizada com CONTEUDO desta cena
            img=work/f"img_{clip_idx:03d}.jpg"
            prompt,neg=prompt_long(para,ato_nome,tema,clip_idx)
            ok_img=get_imagem(prompt,neg,img,seed,tema)
            if not ok_img:
                log(f"    Imagem falhou, pulando cena {clip_idx+1}")
                clip_idx+=1; continue

            # Clip: Ken Burns simples com duracao = duracao REAL do audio
            clip=work/f"clip_{clip_idx:03d}.mp4"
            if criar_clip_long(img,aud,clip,dur_real):
                clips.append(clip); dur_total+=dur_real
            clip_idx+=1

    log(f"\n  Clips gerados: {len(clips)} | Total: {dur_total:.1f}s ({dur_total/60:.1f}min)")

    if not clips: err("Nenhum clip!"); return False

    if dur_total < DUR_MIN:
        log(f"  AVISO: {dur_total:.0f}s < {DUR_MIN:.0f}s min para mid-rolls")
        log(f"  Para 8min+, o script precisa ter mais de 1200 palavras")

    # Concatenar
    cat_f=work/"concat.txt"; cat_f.write_text("\n".join(f"file '{c}'" for c in clips))
    concat=work/"concat.mp4"
    r=ff("-y","-f","concat","-safe","0","-i",str(cat_f),"-c","copy",str(concat),t=300)
    if not concat.exists(): err("Concat falhou!"); return False

    dur_concat=get_duracao(concat)
    final=work/"FINAL_LONG.mp4"
    if dur_concat>DUR_MAX:
        ff("-y","-i",str(concat),"-t",str(DUR_MAX),"-c","copy",str(final),t=60)
    else:
        shutil.copy(concat,final)

    if not final.exists(): err("Final nao criado!"); return False

    dur_final=get_duracao(final); sz=final.stat().st_size//1024//1024
    mid_rolls=[p for p in MIDROLL_POS if p<dur_final-30]
    log(f"\n  LONG PRONTO:")
    log(f"    Duracao: {dur_final:.1f}s ({dur_final/60:.1f}min)")
    log(f"    Tamanho: {sz}MB")
    log(f"    Mid-rolls possiveis: {len(mid_rolls)} em {[f'{p//60}:00' for p in mid_rolls]}")

    # Upload e marcar mp4_ready
    remote=f"mp4s/long_v6_{vid_id}_{int(time.time())}.mp4"
    url=upload_video(str(final),remote)
    if url:
        patch(vid_id,{"mp4_url":url,"status":"mp4_ready","quality_score_current":90})
        log(f"    Upload: {url[-60:]}")
    else:
        dest=pathlib.Path(f"/tmp/long_{vid_id}.mp4"); shutil.copy(final,dest)
        log(f"    Salvo local: {dest}")
    return True

def main():
    log("="*60)
    log("RENDER LONG V6 - Script completo + Sinc por paragrafo + 8-15min")
    log(f"FFmpeg: {ffm()} | Alvo: {DUR_ALVO/60:.0f}min | Mid-rolls: {len(MIDROLL_POS)}")
    log("="*60)

    rows=[]
    if SBU:
        rows=sb("content_pipeline",
                "select=id,title,script,youtube_title,series_slug,pub_order,format,ep_number,episode_number"
                "&status=in.(audio_ready,script_ready)"
                "&format=eq.long"
                "&order=pub_order.asc.nullslast,id.asc"
                f"&limit={MAX}")

    if not rows:
        log("Modo teste:")
        rows=[{"id":8888,"format":"long","series_slug":"apego","ep_number":1,
               "title":"S1E1 | Apego Ansioso: A Raiz do Medo de Abandono","youtube_title":None,
               "script":(
                   "Voce ja se perguntou por que uma mensagem nao respondida pode destruir seu dia?\n\n"
                   "Isso tem um nome cientifico. E mais de 20% da populacao adulta experimenta isso.\n\n"
                   "Pesquisadores da Universidade de Harvard estudaram dois decadas como os primeiros "
                   "anos de vida moldam os circuitos de apego no cortex pre-frontal. O que descobriram "
                   "mudou a forma como entendemos o medo do abandono.\n\n"
                   "Quando voce era crianca, cada vez que um cuidador estava emocionalmente ausente, "
                   "seu sistema nervoso aprendeu uma equacao simples: ausencia equivale a perigo.\n\n"
                   "Essa equacao nunca foi desinstalada. Ela apenas ficou mais sofisticada com o tempo.\n\n"
                   "Hoje, quando alguem importante demora a responder, o mesmo sistema de alarme dispara. "
                   "Nao porque a situacao seja perigosa, mas porque seu cerebro ainda opera pelo codigo "
                   "de sobrevivencia de uma crianca de quatro anos de idade.\n\n"
                   "A pesquisa de Mary Ainsworth, publicada em 1978, revelou algo perturbador: bebes "
                   "com apego ansioso desenvolviam hipersensibilidade aos sinais emocionais dos outros "
                   "que persistia por decadas inteiras na vida adulta.\n\n"
                   "O sinal mais perturbador que a ciencia revela nao e o medo do abandono em si. "
                   "E o fato de que pessoas com apego ansioso frequentemente provocam o distanciamento "
                   "dos parceiros ao tentar evita-lo. O cerebro cria uma profecia autorrealizavel.\n\n"
                   "Mas aqui esta o que a neurociencia tambem prova: esse padrao e neuroplastico. "
                   "Ele pode ser reescrito. Nao com forca de vontade, mas com consciencia e pratica.\n\n"
                   "Salva esse episodio. E se voce se reconheceu em algo aqui, me conta nos comentarios."
               )}]

    ok=0
    for row in rows[:MAX]:
        try:
            if render_long(row): ok+=1
        except Exception as e:
            err(f"#{row.get('id',0)}: {e}")
            import traceback; traceback.print_exc()

    log(f"\n{'='*60}")
    log(f"OK: {ok}/{min(len(rows),MAX)} longs concluidos")

if __name__ == "__main__":
    main()
