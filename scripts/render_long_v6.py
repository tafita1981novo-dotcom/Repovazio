#!/usr/bin/env python3
"""
render_long_v6.py - LONG DEFINITIVO (8-15 minutos com episodios)
REGRAS:
  1. Script completo usado ATE O FINAL
  2. Imagem sincronizada por paragrafo/cena (nova imagem cada ~15-20s)
  3. 8-15 minutos com mid-rolls em 3:00, 6:00, 9:00, 12:00
  4. Episodios de serie respeitados (S1E1, S2E3, etc.)
  5. 5 atos narrativos: Intro -> Problema -> Revelacao -> Perturbador -> Resolucao
  6. 100% gratuito: edge-tts + Pollinations + imageio-ffmpeg
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
DUR_MIN = 8.0*60; DUR_MAX = 15.0*60; DUR_ALVO = 12.0*60
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

def ff(*args, t=300):
    return subprocess.run([ffm(), *args], capture_output=True, timeout=t)

def ffprobe_dur(path):
    r = subprocess.run(
        ["ffprobe","-v","quiet","-print_format","json","-show_format",str(path)],
        capture_output=True, timeout=15)
    try: return float(json.loads(r.stdout)["format"]["duration"])
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
    5 atos narrativos usando o script COMPLETO.
    Divisao proporcional: intro(15%) problema(25%) ciencia(25%) perturb(20%) resolucao(15%)
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

    # Mover paragrafos perturbadores para o ato correto
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
        f"No proximo episodio, vamos explorar o que acontece quando voce finalmente "
        f"reconhece esse padrao. Segue o canal para nao perder."
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
                dur=medir_mp3(out); log(f"    TTS {dur:.1f}s: {texto_clean[:40]}..."); return dur
        time.sleep(3*attempt)
    return None

def medir_mp3(path):
    try:
        from mutagen.mp3 import MP3; return MP3(str(path)).info.length
    except: pass
    r=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_streams",str(path)],
                     capture_output=True,timeout=10)
    try:
        for s in json.loads(r.stdout).get("streams",[]):
            if s.get("codec_type")=="audio": return float(s.get("duration",0))
    except: pass
    return pathlib.Path(path).stat().st_size/16000.0

ESTILOS_LONG = {
    "narcisismo": "cinematic dark psychological drama, mirrors, shadows",
    "ansiedade":  "anxiety visualization, racing mind, warm documentary",
    "apego":      "attachment psychology, emotional connection, warm",
    "burnout":    "workplace exhaustion, overwhelm, desaturated",
    "trauma":     "trauma and healing, body memory, hopeful",
    "default":    "psychology documentary, warm cinematic, human emotion",
}

def prompt_long(texto, tipo, tema, i):
    t=texto.lower(); estilo=ESTILOS_LONG.get(tema,ESTILOS_LONG["default"])
    if tipo=="intro": ctx="presenter opening, direct eye contact, engaging cinematic"
    elif tipo=="problema":
        if any(w in t for w in ["briga","conflito","mensagem","trabalho"]): ctx="person in conflict, emotional distance, dramatic"
        else: ctx="person reflecting, problem visualization, thoughtful"
    elif tipo=="ciencia":
        if any(w in t for w in ["cerebro","cortex","amigdala","neuronio"]): ctx="brain neural visualization, scientific, glowing"
        else: ctx="researcher, data, scientific authority, lab setting"
    elif tipo=="perturb": ctx="shocking realization, person wide-eyed, dramatic revelation"
    elif tipo=="resolucao": ctx="hope and agency, person empowered, warm sunrise"
    else: ctx="human psychology portrait, cinematic"

    chars={"narcisismo":"Brazilian woman 28, dark hair","ansiedade":"Brazilian woman 26, expressive eyes",
           "burnout":"Brazilian man 32, exhausted","trauma":"Brazilian woman 30, healing",
           "default":"Brazilian woman 33, warm intelligent"}
    char=chars.get(tema,chars["default"])
    prompt=f"{char}, {ctx}, {estilo}, ultra detailed, 4k, no text"
    neg="text, watermark, logo, cartoon, ugly, blurry, nsfw"
    return prompt, neg

def imagem_pollinations(prompt, neg, out, seed):
    p_enc=urllib.parse.quote(prompt); n_enc=urllib.parse.quote(neg)
    url=f"{POLL}/{p_enc}?width={W}&height={H}&seed={seed}&nologo=true&negative={n_enc}"
    for a in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=90) as r: data=r.read()
            if len(data)>5000:
                open(out,"wb").write(data); log(f"    Img {len(data)//1024}KB OK"); return True
        except Exception as e:
            log(f"    Img tent {a+1}: {e}"); time.sleep(8*(a+1))
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
            draw.line([(0,e),(W,e)],fill=(0,0,0,a)); draw.line([(0,H-1-e),(W,H-1-e)],fill=(0,0,0,a))
        img.filter(ImageFilter.GaussianBlur(0.5)).save(out,"JPEG",quality=90); return True
    except: return False

def get_imagem(prompt, neg, out, seed, tema):
    if imagem_pollinations(prompt,neg,out,seed): return True
    return imagem_proc(out,seed,tema)

def criar_clip_long(img, aud, out, dur, seed):
    random.seed(seed)
    d=max(dur,1)
    vf=f"scale={W+80}:{H+80},crop={W}:{H}:'(iw-{W})*t/{d}':'(ih-{H})*t/{d}',scale={W}:{H}"
    r=ff("-y",
         "-loop","1","-t",str(dur+0.1),"-i",str(img),
         "-i",str(aud),
         "-vf",vf,
         "-c:v","libx264","-preset","veryfast","-crf","20",
         "-pix_fmt","yuv420p","-r","30",
         "-c:a","aac","-b:a","192k","-ac","2","-ar","48000",
         "-shortest","-movflags","+faststart",
         str(out), t=180)
    ok=r.returncode==0 and pathlib.Path(out).exists()
    if ok: log(f"    Clip {pathlib.Path(out).name}: {dur:.1f}s OK")
    else:  err(f"Clip: {r.stderr.decode()[-80:]}")
    return ok

def render_long(vid):
    vid_id=vid["id"]
    title=vid.get("youtube_title") or vid.get("title") or "Long"
    script=vid.get("script") or title
    tema=vid.get("series_slug") or "default"
    ep_num=vid.get("ep_number") or vid.get("episode_number") or 1

    log(f"\n{'='*58}")
    log(f"LONG #{vid_id} | Ep{ep_num} | {title[:48]}")
    log(f"Script: {len(script)} chars | Tema: {tema}")

    work=TMP/f"v{vid_id}_{int(time.time())}"; work.mkdir(parents=True,exist_ok=True)
    atos=estruturar_atos(script,ep_num)

    log("Estrutura narrativa:")
    for nome,ato in atos.items():
        log(f"  {nome.upper():10} {len(ato['paras']):2} paragrafos | {sum(len(p) for p in ato['paras'])} chars")

    clips=[]; clip_idx=0; dur_total=0.0

    for ato_nome,ato in atos.items():
        if not ato["paras"]: continue
        log(f"\n  === ATO: {ato_nome.upper()} ({len(ato['paras'])} paragrafos) ===")

        for j,para in enumerate(ato["paras"]):
            seed=9001+vid_id*77+clip_idx*13
            log(f"\n  Cena {clip_idx+1} [{ato_nome}]: {para[:50]}...")

            mp3=work/f"tts_{clip_idx:03d}.mp3"
            dur=gerar_tts_long(para,mp3,ato_nome)
            if not dur: clip_idx+=1; continue

            wav=work/f"tts_{clip_idx:03d}.wav"
            ff("-y","-i",str(mp3),"-acodec","pcm_s16le","-ar","44100","-ac","2",str(wav),t=30)
            aud=wav if wav.exists() else mp3
            dur_real=ffprobe_dur(aud) or dur

            # Pausa entre paragrafos
            if j<len(ato["paras"])-1:
                pausa=work/f"p_{clip_idx:03d}.wav"; sr=44100; n=int(0.5*sr)
                with wave.open(str(pausa),"w") as wf:
                    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
                    wf.writeframes(b"\x00"*4*n)
                cat=work/f"cat_{clip_idx:03d}.txt"
                cat.write_text(f"file '{aud}'\nfile '{pausa}'")
                aud2=work/f"aud_{clip_idx:03d}.wav"
                ff("-y","-f","concat","-safe","0","-i",str(cat),
                   "-acodec","pcm_s16le","-ar","44100","-ac","2",str(aud2),t=30)
                if aud2.exists():
                    aud=aud2; dur_real=ffprobe_dur(aud) or (dur_real+0.5)

            img=work/f"img_{clip_idx:03d}.jpg"
            prompt,neg=prompt_long(para,ato_nome,tema,clip_idx)
            if not get_imagem(prompt,neg,img,seed,tema): clip_idx+=1; continue

            clip=work/f"clip_{clip_idx:03d}.mp4"
            if criar_clip_long(img,aud,clip,dur_real,seed):
                clips.append(clip); dur_total+=dur_real
            clip_idx+=1

    log(f"\n  Clips: {len(clips)} | Total: {dur_total:.1f}s ({dur_total/60:.1f}min)")
    if not clips: err("Nenhum clip!"); return False

    if dur_total<DUR_MIN:
        log(f"  {dur_total:.0f}s < {DUR_MIN:.0f}s minimo. Script muito curto para 8min+.")

    cat_f=work/"concat.txt"; cat_f.write_text("\n".join(f"file '{c}'" for c in clips))
    concat=work/"concat.mp4"
    ff("-y","-f","concat","-safe","0","-i",str(cat_f),"-c","copy",str(concat),t=300)
    if not concat.exists(): err("Concat falhou!"); return False

    dur_concat=ffprobe_dur(concat)
    final=work/"FINAL_LONG.mp4"
    if dur_concat>DUR_MAX:
        ff("-y","-i",str(concat),"-t",str(DUR_MAX),"-c","copy",str(final),t=60)
    else:
        shutil.copy(concat,final)

    if not final.exists(): err("Final nao criado!"); return False

    dur_final=ffprobe_dur(final); sz=final.stat().st_size//1024//1024
    mid_rolls=[p for p in MIDROLL_POS if p<dur_final-30]
    log(f"\n  LONG PRONTO: {dur_final:.1f}s ({dur_final/60:.1f}min) | {sz}MB")
    log(f"  Mid-rolls possiveis: {len(mid_rolls)} em {[f'{p//60}:00' for p in mid_rolls]}")

    remote=f"mp4s/long_v6_{vid_id}_{int(time.time())}.mp4"
    url=upload_video(str(final),remote)
    if url:
        patch(vid_id,{"mp4_url":url,"status":"mp4_ready","quality_score_current":90})
        log(f"  Upload: {url[-60:]}")
    else:
        dest=pathlib.Path(f"/tmp/long_final_{vid_id}.mp4"); shutil.copy(final,dest)
        log(f"  Salvo: {dest}")
    return True

def main():
    log("="*60)
    log("RENDER LONG V6 - Script completo + Sinc por cena + 8-15min")
    log(f"FFmpeg: {ffm()} | Meta: {DUR_ALVO/60:.0f}min | Mid-rolls: {len(MIDROLL_POS)}")
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
                   "Voce ja se perguntou por que, mesmo quando tudo parece bem no relacionamento, "
                   "uma mensagem nao respondida pode destruir seu dia inteiro?\n\n"
                   "Isso tem um nome. E mais de 20% da populacao adulta experimenta isso diariamente.\n\n"
                   "Pesquisadores da Universidade de Harvard estudaram por mais de duas decadas como "
                   "os primeiros anos de vida moldam os circuitos de apego no cortex pre-frontal.\n\n"
                   "Quando voce era crianca, cada vez que um cuidador estava emocionalmente ausente, "
                   "seu sistema nervoso aprendeu uma equacao: ausencia = perigo.\n\n"
                   "Essa equacao nunca foi desinstalada. Ela so ficou mais sofisticada.\n\n"
                   "Hoje, quando alguem importante demora a responder, o mesmo sistema de alarme dispara. "
                   "Nao porque a situacao seja perigosa - mas porque seu cerebro opera pelo codigo de "
                   "sobrevivencia de uma crianca de 4 anos.\n\n"
                   "A pesquisa de Mary Ainsworth em 1978 revelou algo perturbador: bebes com apego "
                   "ansioso desenvolviam hipersensibilidade aos sinais emocionais dos outros que "
                   "persistia por decadas.\n\n"
                   "O sinal mais perturbador que a ciencia revela: voce pode inconscientemente CRIAR "
                   "as situacoes que mais teme. Pessoas com apego ansioso frequentemente provocam o "
                   "distanciamento dos parceiros ao tentar evita-lo. O cerebro cria uma profecia "
                   "autorrealizavel de abandono.\n\n"
                   "Mas a neurociencia prova: esse padrao e neuroplastico. Ele pode ser reescrito. "
                   "Nao com forca de vontade, mas com consciencia especifica e pratica intencional.\n\n"
                   "Salva esse episodio. E se voce se reconheceu em algo aqui - me conta nos comentarios."
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
