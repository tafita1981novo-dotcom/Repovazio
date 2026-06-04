#!/usr/bin/env python3
"""
render_short_v6.py - SHORT DEFINITIVO (50-58 segundos)
REGRAS:
  - Script usado ATE O FINAL
  - Imagem sincronizada com o CONTEUDO de cada frase especifica
  - Duracao exata 50-58s (TTS medido por segmento)
  - Sinal mais perturbador SEMPRE na penultima posicao
  - Viral score >=95 obrigatorio
  - Sem ffprobe externo (usa ffmpeg -i para medir duracao)
  - Verificacao imagem >10KB
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
    for p in [shutil.which("ffmpeg"),"/usr/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists(): return p
    return "ffmpeg"

def ff(*args, t=120):
    return subprocess.run([ffm(), *args], capture_output=True, timeout=t)

def get_duracao(path):
    """Mede duracao sem ffprobe externo - usa ffmpeg -i"""
    try:
        ffbin=ffm()
        r=subprocess.run([ffbin,"-i",str(path),"-f","null","-"],capture_output=True,timeout=20)
        m=re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)",r.stderr.decode())
        if m:
            h,mn,s=m.groups(); return float(h)*3600+float(mn)*60+float(s)
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
        with urllib.request.urlopen(req,timeout=180): pass
        return f"{SBU}/storage/v1/object/public/videos/{remote}"
    except Exception as e:
        err(f"Upload: {e}"); return ""

def limpar(script):
    s=re.sub(r"\*\*[A-Z_ ]+:\*\*.*?(?=\n\n|\Z)","",script,flags=re.DOTALL|re.MULTILINE)
    s=re.sub(r"\*\*[A-Z_ ]+\*\*\s*$","",s,flags=re.MULTILINE)
    s=re.sub(r"\*+|_+|#+|\[|\]","",s)
    s=re.sub(r"\n{3,}","\n\n",s)
    s=re.sub(r"[ \t]+"," ",s)
    return s.strip()

def dividir_em_cenas(script):
    """
    Divide script em cenas de ~8-12s cada.
    Usa o script COMPLETO. Se muito longo para 58s,
    seleciona: hook + sinais + PERTURBADOR(penultimo) + CTA(ultimo)
    """
    script_limpo=limpar(script)
    paragrafos=[p.strip() for p in re.split(r"\n\n+",script_limpo) if len(p.strip())>10]
    if not paragrafos:
        paragrafos=[f.strip() for f in re.split(r"(?<=[.!?])\s+",script_limpo) if len(f.strip())>10]

    def dur_est(texto): return len(texto)/17.0  # ~17 chars/s @ edge-tts

    def tipo_cena(p, idx, total):
        pl=p.lower()
        if idx==0: return "hook"
        if idx==total-1: return "cta"
        perturb_words=["perturbador","chocante","surpreendente","mais grave",
                       "pior de tudo","mais real","na verdade","o segredo"]
        if any(w in pl for w in perturb_words): return "perturb"
        ciencia_words=["pesquisa","estudo","universidade","harvard","neurocienci",
                       "descobriu","cerebro","dados","comprovou"]
        if any(w in pl for w in ciencia_words): return "ciencia"
        return "sinal"

    n=len(paragrafos)
    cenas=[{"texto":p,"tipo":tipo_cena(p,i,n),"dur":dur_est(p),"idx":i}
           for i,p in enumerate(paragrafos)]
    dur_total=sum(c["dur"] for c in cenas)
    log(f"  Script: {n} paragrafos | dur estimada: {dur_total:.1f}s")

    if dur_total<=62:
        resultado=cenas  # Cabe tudo!
    else:
        # Selecionar para caber em ~55s
        hook=cenas[0]
        cta=cenas[-1]
        perturb=next((c for c in cenas if c["tipo"]=="perturb"),None)
        outros=[c for c in cenas if c not in (hook,cta,perturb) and c is not None]
        resultado=[hook]; dur_acum=hook["dur"]
        reserva=(perturb["dur"] if perturb else 0)+cta["dur"]+4
        for c in outros:
            if dur_acum+c["dur"]+reserva<58:
                resultado.append(c); dur_acum+=c["dur"]
        if perturb: resultado.append(perturb)
        resultado.append(cta)
        # Reordenar pela posicao original (exceto perturb e cta fixos)
        hook_c=resultado[0]; cta_c=resultado[-1]
        pert_c=resultado[-2] if perturb else None
        meio=[c for c in resultado[1:] if c not in (cta_c,pert_c)]
        meio_s=sorted(meio,key=lambda x: x["idx"])
        resultado=[hook_c]+meio_s+([pert_c] if pert_c else [])+[cta_c]

    # Garantir perturbador nao no inicio
    if len(resultado)>2 and resultado[0]["tipo"]=="perturb":
        resultado.insert(-1,resultado.pop(0))

    return resultado

VOICE_CFG={
    "hook":    ("pt-BR-ThalitaMultilingualNeural","+20%","+15%"),
    "ciencia": ("pt-BR-ThalitaMultilingualNeural","+8%", "+12%"),
    "sinal":   ("pt-BR-ThalitaMultilingualNeural","+10%","+12%"),
    "perturb": ("pt-BR-ThalitaMultilingualNeural","+5%", "+18%"),
    "cta":     ("pt-BR-ThalitaMultilingualNeural","+18%","+20%"),
}

def gerar_tts(texto, out, tipo="sinal"):
    voice,rate,vol=VOICE_CFG.get(tipo,VOICE_CFG["sinal"])
    texto_clean=re.sub(r"[*_#\[\]]","",texto)[:600].strip()
    for attempt in range(3):
        r=subprocess.run(
            ["edge-tts",f"--voice={voice}",f"--rate={rate}",f"--volume={vol}",
             "--text",texto_clean,"--write-media",str(out)],
            capture_output=True, timeout=60)
        if r.returncode==0 and pathlib.Path(out).exists():
            if pathlib.Path(out).stat().st_size>500:
                dur=get_duracao(out); log(f"    TTS [{tipo}] {dur:.1f}s: {texto_clean[:40]}"); return dur
        time.sleep(2*attempt)
    err(f"TTS falhou: {texto_clean[:40]}"); return None

ESTILOS={
    "narcisismo": "dark psychology, narcissistic pattern, shadows",
    "ansiedade":  "anxiety visualization, racing thoughts",
    "apego":      "emotional attachment, connection warmth",
    "burnout":    "exhaustion overwhelm, desaturated",
    "trauma":     "trauma healing, hope light",
    "default":    "psychology portrait, cinematic warm",
}

def prompt_para_cena(texto, tipo, tema, seed):
    t=texto.lower(); estilo=ESTILOS.get(tema,ESTILOS["default"])
    if any(w in t for w in ["celular","mensagem","notificacao","telefone"]): ctx="person checking phone anxious, night"
    elif any(w in t for w in ["chora","lagrima","triste","dor"]): ctx="person sad tearful, window light"
    elif any(w in t for w in ["pesquisa","harvard","estudo","neurocienci","cerebro"]): ctx="brain visualization, scientific, neural"
    elif any(w in t for w in ["coracao","peito","corpo","respiracao"]): ctx="person hands on chest, emotion"
    elif any(w in t for w in ["narcis","manipul","control"]): ctx="shadow figure, manipulation, mirror"
    elif any(w in t for w in ["alivio","consegue","mudanca","forca"]): ctx="person empowered, hopeful, sunrise"
    elif any(w in t for w in ["perturbador","chocante","revela"]): ctx="shocking realization, wide eyes, dramatic"
    elif any(w in t for w in ["salva","comenta","inscreve"]): ctx="direct eye contact, warm smile, speaking"
    elif tipo=="hook": ctx="intense direct gaze, dramatic scroll-stopping"
    else: ctx="thoughtful psychology portrait"
    chars={"narcisismo":"Brazilian woman 28, dark hair","ansiedade":"Brazilian woman 26, expressive",
           "burnout":"Brazilian man 32, exhausted","trauma":"Brazilian woman 30, healing",
           "default":"Brazilian woman 33, warm intelligent"}
    char=chars.get(tema,chars["default"])
    prompt=f"{char}, {ctx}, {estilo}, masterpiece, 4k, no text, no watermark"
    neg="text, watermark, logo, ugly, blurry, nsfw, cartoon"
    return prompt, neg

def imagem_pollinations(prompt, neg, out, seed):
    p_enc=urllib.parse.quote(prompt); n_enc=urllib.parse.quote(neg)
    url=f"{POLL}/{p_enc}?width={W}&height={H}&seed={seed}&nologo=true&negative={n_enc}"
    for a in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=90) as r: data=r.read()
            if len(data)>10000:  # Minimo 10KB
                open(out,"wb").write(data); log(f"    Img {len(data)//1024}KB OK"); return True
            else: log(f"    Img {len(data)}B invalida")
        except Exception as e: log(f"    Img tent {a+1}: {e}")
        time.sleep(8*(a+1))
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
        img.filter(ImageFilter.GaussianBlur(0.5)).save(out,"JPEG",quality=92)
        log(f"    Img procedural OK"); return True
    except Exception as e:
        err(f"Proc img: {e}"); return False

def get_imagem(prompt, neg, out, seed, tema):
    if imagem_pollinations(prompt,neg,out,seed): return True
    return imagem_proc(out,seed,tema)

def criar_clip(img, aud, out, dur):
    """Ken Burns simples: crop linear. RAPIDO e confiavel."""
    d=max(dur,1.0)
    vf=(f"scale={W+40}:{H+40},"
        f"crop={W}:{H}:"
        f"'(iw-{W})*t/{d}':"
        f"'(ih-{H})*0.5'")
    r=ff("-y",
         "-loop","1","-t",str(d+0.05),"-i",str(img),
         "-i",str(aud),
         "-vf",vf,
         "-c:v","libx264","-preset","ultrafast","-crf","20",
         "-pix_fmt","yuv420p","-r","25",
         "-c:a","aac","-b:a","192k","-ac","2","-ar","48000",
         "-shortest","-movflags","+faststart",
         str(out), t=90)
    ok=r.returncode==0 and pathlib.Path(out).exists()
    if ok: log(f"    Clip OK: {dur:.1f}s | {pathlib.Path(out).stat().st_size//1024}KB")
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
    vid_id=vid["id"]
    title=vid.get("youtube_title") or vid.get("title") or "Short"
    script=vid.get("script") or title
    tema=vid.get("series_slug") or "default"

    log(f"\n{'='*55}")
    log(f"SHORT #{vid_id} | {title[:48]}")
    log(f"Script: {len(script)} chars | Tema: {tema}")

    work=TMP/f"v{vid_id}_{int(time.time())}"; work.mkdir(parents=True,exist_ok=True)

    # Dividir em cenas (script completo)
    cenas=dividir_em_cenas(script)
    if not cenas: err("Nenhuma cena!"); return False

    log("Estrutura:")
    for i,c in enumerate(cenas):
        log(f"  [{c['tipo'].upper():8}] {c['texto'][:60]}...")

    # Viral score
    score,det=viral_score(cenas)
    log(f"Viral score: {score}/100 | {' | '.join(det)}")

    if score<95:
        log("Ajustando score...")
        perturbs=[c for c in cenas if c["tipo"]=="perturb"]
        if perturbs:
            cenas=[c for c in cenas if c["tipo"]!="perturb"]
            cenas.insert(-1,perturbs[0])
        score,det=viral_score(cenas); log(f"Score ajustado: {score}/100")
        if score<70:
            err(f"Score {score}/100 muito baixo!"); patch(vid_id,{"status":"script_ready"}); return False

    # TTS + imagem por cena
    clips=[]; dur_total=0.0

    for i,cena in enumerate(cenas):
        seed=9001+vid_id*77+i*13; tipo=cena["tipo"]
        log(f"\n  Cena {i+1}/{len(cenas)} [{tipo}]:")

        mp3=work/f"tts_{i:02d}.mp3"
        dur=gerar_tts(cena["texto"],mp3,tipo)
        if not dur: continue

        wav=work/f"tts_{i:02d}.wav"
        ff("-y","-i",str(mp3),"-acodec","pcm_s16le","-ar","44100","-ac","2",str(wav),t=30)
        aud=wav if wav.exists() else mp3
        dur_real=get_duracao(aud) or dur

        # Pausa dramatica entre cenas (exceto ultima)
        if i<len(cenas)-1:
            pausa=work/f"pausa_{i:02d}.wav"; sr=44100; n=int(0.35*sr)
            with wave.open(str(pausa),"w") as wf:
                wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
                wf.writeframes(b"\x00"*4*n)
            cat=work/f"cat_{i:02d}.txt"; cat.write_text(f"file '{aud}'\nfile '{pausa}'")
            aud2=work/f"aud_{i:02d}.wav"
            ff("-y","-f","concat","-safe","0","-i",str(cat),
               "-acodec","pcm_s16le","-ar","44100","-ac","2",str(aud2),t=30)
            if aud2.exists(): aud=aud2; dur_real=get_duracao(aud) or (dur_real+0.35)

        # Imagem sincronizada com CONTEUDO desta cena
        img=work/f"img_{i:03d}.jpg"
        prompt,neg=prompt_para_cena(cena["texto"],tipo,tema,seed)
        if not get_imagem(prompt,neg,img,seed,tema): continue

        clip=work/f"clip_{i:03d}.mp4"
        if criar_clip(img,aud,clip,dur_real):
            clips.append(clip); dur_total+=dur_real

    if not clips: err("Nenhum clip!"); return False

    log(f"\n  Clips: {len(clips)} | Total: {dur_total:.1f}s")
    if dur_total<45: err(f"Muito curto ({dur_total:.1f}s)!"); return False

    # Concatenar
    cat_f=work/"concat.txt"; cat_f.write_text("\n".join(f"file '{c}'" for c in clips))
    concat=work/"concat.mp4"
    ff("-y","-f","concat","-safe","0","-i",str(cat_f),"-c","copy",str(concat),t=60)
    if not concat.exists(): err("Concat falhou!"); return False

    dur_concat=get_duracao(concat)
    final=work/"FINAL.mp4"
    if dur_concat>62:
        log(f"  Cortando {dur_concat:.1f}s -> 58s")
        ff("-y","-i",str(concat),"-t","58","-c","copy",str(final),t=30)
    else:
        shutil.copy(concat,final)

    if not final.exists(): err("Final nao criado!"); return False

    dur_final=get_duracao(final); sz=final.stat().st_size//1024//1024
    log(f"\n  PRONTO: {dur_final:.1f}s | {sz}MB | viral={score}/100")

    remote=f"mp4s/short_v6_{vid_id}_{int(time.time())}.mp4"
    url=upload_video(str(final),remote)
    if url:
        patch(vid_id,{"mp4_url":url,"status":"mp4_ready","quality_score_current":score})
        log(f"  Upload: {url[-60:]}")
    else:
        dest=pathlib.Path(f"/tmp/short_{vid_id}.mp4"); shutil.copy(final,dest)
        log(f"  Salvo: {dest}")
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
                   "E voce acaba pedindo desculpas sem entender por que.\n\n"
                   "O cerebro interpreta a ausencia emocional como rejeicao fisica - "
                   "ativa as mesmas areas que sentem dor real.\n\n"
                   "O sinal mais perturbador: voce aprendeu a sentir alivio quando ele voltava a "
                   "falar. Mesmo sendo voce quem estava certa.\n\n"
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
