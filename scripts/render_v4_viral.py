#!/usr/bin/env python3
"""
render_v4_viral.py — 100% GRATUITO
edge-tts (Microsoft gratis) + HF FLUX.1-schnell (gratis) + FFmpeg snap
"""
import os, json, re, time, subprocess, pathlib, math, struct, wave, random
import urllib.request
from datetime import datetime

SBU  = os.getenv("SUPABASE_URL","")
SBK  = os.getenv("SUPABASE_SERVICE_KEY","")
HFT  = os.getenv("HF_TOKEN","")
MAX_V= int(os.getenv("MAX_VIDEOS","2"))
FMT  = os.getenv("VIDEO_FORMAT","short")
TMP  = pathlib.Path("/tmp/v4"); TMP.mkdir(exist_ok=True)
W, H = (1080, 1920) if FMT=="short" else (1920, 1080)

def log(msg): print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)

def ffm():
    """`imageio-ffmpeg` portátil — nunca falha"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError: pass
    import shutil
    b=shutil.which("ffmpeg")
    if b: return b
    for p in ["/snap/bin/ffmpeg","/usr/bin/ffmpeg","/usr/local/bin/ffmpeg"]:
        if pathlib.Path(p).exists(): return p
    return "ffmpeg"

def ffrun(args, timeout=120):
    return subprocess.run([ffm()]+args, capture_output=True, timeout=timeout)

def mp3_dur(path):
    size=pathlib.Path(path).stat().st_size
    try:
        from mutagen.mp3 import MP3
        return MP3(path).info.length
    except ImportError: pass
    return size/16000

# Supabase
def sb(ep, params="", method="GET", data=None):
    if not SBU: return [] if method=="GET" else None
    url=f"{SBU}/rest/v1/{ep}?{params}" if params else f"{SBU}/rest/v1/{ep}"
    req=urllib.request.Request(url,data=json.dumps(data).encode() if data else None,method=method)
    req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
    if data: req.add_header("Content-Type","application/json")
    if method in ("PATCH","POST"): req.add_header("Prefer","return=minimal")
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            return json.loads(r.read()) if method=="GET" else True
    except: return [] if method=="GET" else False

def sb_upload(local, remote):
    if not SBU: return ""
    data=open(local,"rb").read()
    req=urllib.request.Request(f"{SBU}/storage/v1/object/videos/{remote}",data=data,method="POST")
    req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
    req.add_header("Content-Type","video/mp4"); req.add_header("x-upsert","true")
    try:
        with urllib.request.urlopen(req,timeout=120): pass
        return f"{SBU}/storage/v1/object/public/videos/{remote}"
    except: return ""

# TTS edge-tts GRATIS (Microsoft Azure, sem chave)
RATES = {"hook":"+20%","reveal":"+12%","science":"+6%","empathy":"+8%","cta":"+16%","default":"+10%"}

def detect_emotion(text, idx, total):
    t=text.lower()
    if idx==0: return "hook"
    if idx>=total-1: return "cta"
    if any(w in t for w in ["harvard","pesquisa","estudo","neurociência","cérebro"]): return "science"
    if any(w in t for w in ["na verdade","mas ","porém","diferente","surpreendente"]): return "reveal"
    return "empathy"

def tts_edge(text, out_mp3, emotion="default"):
    rate=RATES.get(emotion,"+10%")
    cmd=["edge-tts","--voice=pt-BR-ThalitaMultilingualNeural",
         f"--rate={rate}","--volume=+15%",
         "--text",text[:600],"--write-media",out_mp3]
    try:
        r=subprocess.run(cmd,capture_output=True,timeout=90)
        p=pathlib.Path(out_mp3)
        size=p.stat().st_size if p.exists() else 0
        log(f"   edge-tts: rc={r.returncode} {size//1024}KB")
        return r.returncode==0 and size>200
    except Exception as e:
        log(f"   edge-tts err: {e}"); return False

def tts_async(text, out_mp3, emotion="default"):
    try:
        import asyncio, edge_tts
        rate=RATES.get(emotion,"+10%")
        async def _g():
            c=edge_tts.Communicate(text[:600],voice="pt-BR-ThalitaMultilingualNeural",
                                    rate=rate,volume="+15%")
            await c.save(out_mp3)
        asyncio.run(_g())
        size=pathlib.Path(out_mp3).stat().st_size if pathlib.Path(out_mp3).exists() else 0
        log(f"   edge-tts async: {size//1024}KB")
        return size>200
    except Exception as e:
        log(f"   async err: {e}"); return False

def gen_audio(full_text, work):
    mp3=str(work/"narration.mp3")
    if tts_edge(full_text, mp3): return mp3, "edge-tts"
    if tts_async(full_text, mp3): return mp3, "edge-tts-async"
    return None, None

# Personagens HF FLUX (gratis)
CHARS={
    "sara":    "photorealistic brazilian woman 28yo, dark wavy hair, sad worried, window, coffee, morning light, cinematic, no text",
    "marcos":  "photorealistic brazilian man 35yo, sharp jaw, cold smile, suit, office, dramatic light, cinematic, no text",
    "julia":   "photorealistic brazilian woman 26yo, curly hair, tired eyes, desk, papers, overwhelmed, warm lamp, no text",
    "lucas":   "photorealistic brazilian man 31yo, casual shirt, lying bed, cannot get up, morning light, exhausted, no text",
    "dra_ana": "photorealistic brazilian woman 42yo, white coat, glasses, warm, laboratory, explaining, professional, no text",
    "daniela": "photorealistic brazilian woman 33yo, intelligent eyes, bookshelf background, speaking camera, empathetic, no text",
}
SERIES_CHARS={
    "narcisismo":["sara","marcos","dra_ana"],
    "ansiedade": ["julia","dra_ana","daniela"],
    "apego":     ["sara","marcos","daniela"],
    "burnout":   ["lucas","dra_ana","daniela"],
    "depressao": ["sara","lucas","dra_ana"],
    "default":   ["daniela","dra_ana","sara"],
}
EM_VIS={
    "hook":"anxious troubled expression, worried",
    "reveal":"surprised realization, raised eyebrows",
    "science":"thoughtful analytical, nodding",
    "empathy":"compassionate warm smile",
    "cta":"encouraging hopeful, direct eye contact",
}

def gen_hf(char_key, em, out, seed):
    if not HFT: return False
    prompt=(f"masterpiece, best quality, photorealistic, {CHARS.get(char_key,CHARS['daniela'])}, "
            f"{EM_VIS.get(em,'natural expression')}, "
            f"no text, no words, no watermark, cinematic, 4k, film grain")
    body=json.dumps({"inputs":prompt,"parameters":{"width":W,"height":H,"num_inference_steps":4,"seed":seed}}).encode()
    for model in ["black-forest-labs/FLUX.1-schnell","stabilityai/stable-diffusion-xl-base-1.0"]:
        req=urllib.request.Request(f"https://api-inference.huggingface.co/models/{model}",data=body)
        req.add_header("Authorization",f"Bearer {HFT}")
        req.add_header("Content-Type","application/json")
        try:
            with urllib.request.urlopen(req,timeout=90) as r:
                img=r.read()
            if len(img)>5000:
                open(out,"wb").write(img); log(f"   HF {model.split('/')[-1][:14]}: {len(img)//1024}KB")
                return True
        except Exception as e:
            if "503" in str(e): time.sleep(8)
    return False

def gen_proc(char_key, em, out, seed):
    try:
        from PIL import Image, ImageDraw, ImageFilter
        random.seed(seed)
        PAL={"sara":((8,3,18),(180,60,220),(225,30,70)),"marcos":((3,5,18),(60,100,220),(30,150,255)),
             "julia":((3,12,3),(60,190,100),(150,255,80)),"lucas":((18,3,3),(220,60,30),(255,150,30)),
             "dra_ana":((3,15,15),(40,190,190),(80,220,255)),"daniela":((8,3,22),(120,60,230),(200,80,255))}
        bg,c1,c2=PAL.get(char_key,PAL["daniela"])
        img=Image.new("RGBA",(W,H),(*bg,255)); draw=ImageDraw.Draw(img)
        for y in range(H):
            t=(y/H)**0.65; c=tuple(min(255,int(bg[j]+(c1[j]-bg[j])*t*0.7)) for j in range(3))
            draw.line([(0,y),(W,y)],fill=(*c,255))
        cx=W//2; cy=int(H*0.55); bw,bh=int(W*0.44),int(H*0.54)
        for i in range(4,0,-1): draw.ellipse([(cx-bw//2-i*6,cy-i*6),(cx+bw//2+i*6,cy+bh+i*6)],fill=(*c1,25*i))
        draw.ellipse([(cx-bw//2,cy),(cx+bw//2,cy+bh)],fill=(*c1,145))
        hr=int(W*0.13); hy=int(H*0.285)
        for i in range(5,0,-1): draw.ellipse([(cx-hr-i*5,hy-hr-i*5),(cx+hr+i*5,hy+hr+i*5)],fill=(*c2,18*i))
        draw.ellipse([(cx-hr,hy-hr),(cx+hr,hy+hr)],fill=(*c1,210))
        ey=hy-hr//5; ex_l=cx-hr//3; ex_r=cx+hr//3; er=hr//9
        for ex in (ex_l,ex_r): draw.ellipse([(ex-er,ey-er),(ex+er,ey+er)],fill=(255,255,255,200))
        pts=[(random.randint(30,W-30),random.randint(30,H-30)) for _ in range(15)]
        for j,(px,py) in enumerate(pts):
            r=random.randint(4,22); col=c1 if j%2==0 else c2
            draw.ellipse([(px-r,py-r),(px+r,py+r)],fill=(*col,random.randint(80,180)))
            for px2,py2 in pts[j+1:]:
                d=((px2-px)**2+(py2-py)**2)**0.5
                if d<260: draw.line([(px,py),(px2,py2)],fill=(*c1,int(50*(1-d/260))),width=1)
        for e in range(200):
            a=int(160*(1-e/200)); draw.line([(0,e),(W,e)],fill=(0,0,0,a)); draw.line([(0,H-1-e),(W,H-1-e)],fill=(0,0,0,a))
            if e<100: draw.line([(e,0),(e,H)],fill=(0,0,0,a//2)); draw.line([(W-1-e,0),(W-1-e,H)],fill=(0,0,0,a//2))
        img.convert("RGB").filter(ImageFilter.GaussianBlur(0.7)).save(out,"JPEG",quality=95)
        return True
    except: return False

def gen_img(ck,em,out,seed):
    if gen_hf(ck,em,out,seed): return "hf"
    return "proc" if gen_proc(ck,em,out,seed) else None

def gen_music(out, dur):
    sr=44100; n=int(dur*sr)
    chords=[[220,261.63,329.63],[174.61,220,261.63],[261.63,329.63,392],[196,246.94,293.66]]
    step=dur/len(chords); L,R=[],[]
    for i in range(n):
        t=i/sr; fade=min(1.0,min(t/3,(dur-t)/3))
        ci=min(int(t/step),len(chords)-1)
        sig=sum(0.04*math.sin(2*math.pi*f*t)*(0.5+0.5*math.sin(2*math.pi*0.25*t)) for f in chords[ci])
        sig+=0.06*math.sin(2*math.pi*(chords[ci][0]/2)*t)*(0.5+0.5*math.sin(2*math.pi*0.12*t))
        sig+=0.007*(random.random()*2-1); sig*=fade
        L.append(max(-32767,min(32767,int(32767*(sig+0.002*math.sin(2*math.pi*1.1*t))))))
        R.append(max(-32767,min(32767,int(32767*(sig-0.002*math.sin(2*math.pi*1.1*t))))))
    with wave.open(out,"w") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes(b"".join(struct.pack("<hh",l,r) for l,r in zip(L,R)))

def render(vid):
    vid_id=vid["id"]; title=vid.get("title","") or vid.get("youtube_title","")
    script=vid.get("script","") or vid.get("youtube_description","") or title
    slug=vid.get("series_slug","default") or "default"
    log(f"--- [{vid_id}] {title[:55]}")
    work=TMP/f"v{vid_id}"; work.mkdir(exist_ok=True)
    paras=[p.strip() for p in re.split(r'\n\n+',script) if len(p.strip())>12]
    if not paras: paras=[s.strip() for s in re.split(r'[.!?]+',script) if len(s.strip())>10]
    paras=paras[:8]; n=len(paras)
    if n==0: return False
    chars=SERIES_CHARS.get(slug,SERIES_CHARS["default"])
    # Áudio
    log("   Gerando narração edge-tts (gratis)...")
    full_text=" ... ".join(paras)
    aud_mp3,aud_src=gen_audio(full_text,work)
    if not aud_mp3: log("   ERRO: TTS falhou!"); return False
    dur=mp3_dur(aud_mp3)
    if dur<=0: dur=n*7.0
    log(f"   {aud_src} | {dur:.1f}s")
    # Personagens
    log("   Gerando personagens (HF FLUX gratis)...")
    spc=dur/n; clips=[]
    for i,para in enumerate(paras):
        em=detect_emotion(para,i,n); ck=chars[i%len(chars)]
        img=str(work/f"c{i:03d}.jpg"); seed=9001+vid_id*77+i*13
        src=gen_img(ck,em,img,seed)
        log(f"   Cena {i+1}/{n}: {ck} ({em}) -> {src or 'FALHOU'}")
        if not src: continue
        clip=str(work/f"c{i:03d}.mp4")
        r=ffrun(["-y","-loop","1","-t",str(spc),"-i",img,
                  "-vf",f"scale={W}:{H}",
                  "-c:v","libx264","-crf","20","-preset","ultrafast",
                  "-pix_fmt","yuv420p","-r","25",clip],60)
        if r.returncode==0 and pathlib.Path(clip).exists() and pathlib.Path(clip).stat().st_size>500:
            clips.append(clip)
        else:
            log(f"   clip err rc={r.returncode}: {r.stderr.decode()[-100:]}")
    if not clips: log("   ERRO: Nenhum clip!"); return False
    vid_only=str(work/"v.mp4"); cat=str(work/"c.txt")
    open(cat,"w").write("\n".join(f"file '{c}'" for c in clips))
    ffrun(["-y","-f","concat","-safe","0","-i",cat,"-c:v","copy",vid_only],60)
    music=str(work/"m.wav"); gen_music(music,dur+5)
    log("   Mix final...")
    final=str(work/"FINAL.mp4")
    r=ffrun(["-y","-i",vid_only,"-i",aud_mp3,"-i",music,
              "-filter_complex",
              "[1:a]volume=1.0,apad[narr];"
              "[2:a]volume=0.10,apad[music];"
              "[narr][music]amix=inputs=2:duration=first:dropout_transition=2[a]",
              "-map","0:v","-map","[a]",
              "-c:v","copy","-c:a","aac","-b:a","192k","-ac","2","-ar","48000",
              "-shortest","-movflags","+faststart",final],120)
    if not pathlib.Path(final).exists():
        log(f"   ERRO mix: {r.stderr.decode()[-100:]}"); return False
    sz=pathlib.Path(final).stat().st_size
    log(f"   OK {sz//1024//1024:.1f}MB | {dur:.0f}s | {W}x{H}")
    if SBU:
        url=sb_upload(final,f"mp4s/v4_{vid_id}_{int(time.time())}.mp4")
        if url:
            sb(f"content_pipeline?id=eq.{vid_id}","","PATCH",
               {"mp4_url":url,"status":"mp4_ready","quality_score_current":80})
            log(f"   Upload: {url[-50:]}")
    return True

def main():
    log("="*55)
    log("RENDER V4 - 100% GRATUITO")
    log(f"  TTS: edge-tts Microsoft (gratis)")
    log(f"  Imagens: HF FLUX.1-schnell (gratis)")
    log(f"  FFmpeg: {ffm()}")
    log("="*55)
    rows=sb("content_pipeline",
            f"select=id,title,script,youtube_title,youtube_description,series_slug,pub_order"
            f"&status=in.(audio_ready,script_ready)&format=eq.{FMT}"
            f"&order=pub_order.asc.nullslast,id.asc&limit={MAX_V}")
    if not rows:
        rows=[{"id":683,"series_slug":"narcisismo","pub_order":1,
               "title":"Narcisismo encoberto: 3 sinais que voce ignora",
               "script":"Voce convive com alguem que sempre parece ter razao, nunca pede desculpas, mas nunca grita?\n\nIsso e o narcisismo encoberto. E a neurociencia de Harvard prova que e mais perigoso que o classico.\n\nNa verdade, o cerebro narcisico tem hiperatividade na amigdala ao receber qualquer critica.\n\nPor isso ele nunca muda. Mudar e existencialmente ameacador para ele.\n\nVoce ja viveu isso? Me conta nos comentarios."}]
        log("Modo teste #683")
    ok=0
    for row in rows[:MAX_V]:
        if render(row): ok+=1
    log(f"\n{ok}/{len(rows[:MAX_V])} renderizados - 100% GRATUITO")

if __name__=="__main__": main()