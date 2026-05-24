#!/usr/bin/env python3
"""
render_en_channel.py
Processa en_channel_queue: gera audio (Edge TTS) + imagens (Pollinations) + mp4 (FFmpeg)
Produz Shorts EN de 58s para @psidanielacoelho com alta monetização USA/UK/AU
"""
import os, subprocess, requests, pathlib, textwrap, time, json
from datetime import datetime

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
GROQ   = os.getenv("GROQ_API_KEY","")
TMP    = pathlib.Path("/tmp/en_render"); TMP.mkdir(exist_ok=True)
SBH    = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json"}

# Rate para voz EN — AriaNeural EN-US
RATE_EN = "+37%"
VOICE_EN = "en-US-AriaNeural"

def get_pending():
    r = requests.get(f"{SB_URL}/rest/v1/en_channel_queue?status=eq.pending&limit=3",
        headers=SBH, timeout=10)
    return r.json() if r.status_code == 200 else []

def mark_done(vid_id, mp4_path=""):
    requests.patch(f"{SB_URL}/rest/v1/en_channel_queue?id=eq.{vid_id}",
        headers=SBH, json={"status":"mp4_ready","script_en":mp4_path}, timeout=10)

def generate_audio_edge(text, out_path, voice=VOICE_EN, rate=RATE_EN):
    """Edge TTS — gratuito, ilimitado"""
    sentences = ". ".join([s.strip() for s in text.replace('\n',' ').split('.') if s.strip()])
    cmd = ["edge-tts", f"--voice={voice}", f"--rate={rate}",
           f"--text={sentences}", f"--write-media={out_path}"]
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    return pathlib.Path(out_path).exists()

def generate_image(tema, seed):
    """Pollinations FLUX"""
    prompt = (f"masterpiece, best quality, kawaii chibi anime, "
              f"{tema} psychology concept, soft purple tones, clean background "
              f"### lowres, bad anatomy, text, watermark, nsfw, blurry")
    url = (f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt[:380])}"
           f"?model=flux&width=576&height=1024&seed={seed}&nologo=true")
    try:
        ri = requests.get(url, timeout=60)
        if ri.status_code == 200 and len(ri.content) > 10000:
            return ri.content
    except: pass
    return None

def render_short(titulo, script, idx):
    """Renderiza Short de 58s em inglês"""
    print(f"  Rendering: {titulo[:45]}...")
    seed = 9001 + idx * 77

    # Audio
    audio_p = TMP / f"audio_en_{idx}.mp3"
    if not generate_audio_edge(script, str(audio_p)):
        print("    Audio fallback: ffmpeg sine")
        subprocess.run(["ffmpeg","-y","-f","lavfi","-i","sine=frequency=440:duration=58",
            "-c:a","libmp3lame",str(audio_p)], capture_output=True, timeout=30)

    # Duração do áudio
    r_dur = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(audio_p)],
        capture_output=True, timeout=10)
    try:
        dur = float(r_dur.stdout.strip())
    except:
        dur = 58.0

    # Imagem
    img_data = generate_image(titulo.split(":")[0], seed)
    if img_data:
        img_p = TMP / f"img_en_{seed}.jpg"
        img_p.write_bytes(img_data)
    else:
        img_p = None

    # Upscale imagem 576→1080
    if img_p:
        img_hd = TMP / f"img_en_{seed}_hd.jpg"
        subprocess.run(["ffmpeg","-y","-i",str(img_p),"-vf","scale=1080:1920:flags=lanczos",
            str(img_hd)], capture_output=True, timeout=30)
        img_p = img_hd if img_hd.exists() else img_p

    if not img_p:
        img_p = TMP / f"bg_en_{seed}.jpg"
        subprocess.run(["ffmpeg","-y","-f","lavfi",
            "-i","color=c=0x06060F:s=1080x1920","-frames:v","1",str(img_p)],
            capture_output=True, timeout=10)

    # Overlay com texto
    titulo_esc = titulo.replace("'",r"\'")[:45]
    linhas = textwrap.wrap(script, 35)[:3]
    l1 = (linhas[0] if linhas else "").replace("'",r"\'")
    l2 = (linhas[1] if len(linhas)>1 else "").replace("'",r"\'")
    marca = "Daniela Coelho . Psychology Research"

    vf = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"drawbox=y=0:color=black@0.75:width=iw:height=100:t=fill,"
        f"drawbox=y=ih-90:color=black@0.85:width=iw:height=90:t=fill,"
        f"drawtext=text='{titulo_esc}':fontsize=32:fontcolor=white:x=(w-text_w)/2:y=25:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
        f"drawtext=text='{l1}':fontsize=28:fontcolor=white:x=(w-text_w)/2:y=h*0.42:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
    )
    if l2:
        vf += f"drawtext=text='{l2}':fontsize=28:fontcolor=white:x=(w-text_w)/2:y=h*0.42+42:shadowcolor=#000:shadowx=2:shadowy=2,"
    vf += f"drawtext=text='{marca}':fontsize=20:fontcolor=#C4B5FD:x=(w-text_w)/2:y=h-60"

    out_p = TMP / f"short_en_{idx:03d}.mp4"
    subprocess.run([
        "ffmpeg","-y","-loop","1","-i",str(img_p),
        "-i",str(audio_p),
        "-vf",vf,
        "-t",str(min(dur+0.5, 59)),
        "-c:v","libx264","-preset","fast","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k","-ar","44100","-shortest",
        str(out_p)
    ], capture_output=True, timeout=300)

    if out_p.exists() and out_p.stat().st_size > 100000:
        print(f"    ✅ {out_p.name} ({out_p.stat().st_size//1024}KB)")
        return str(out_p)
    return None

def run():
    print(f"=== RENDER EN CHANNEL ===")
    print(f"Buscando vídeos pendentes na fila EN...")
    videos = get_pending()
    print(f"Encontrados: {len(videos)}")
    for i, v in enumerate(videos):
        mp4 = render_short(v["titulo_en"], v["script_en"], i)
        if mp4:
            mark_done(v["id"], mp4)
            print(f"  ✅ Done: {v['titulo_en'][:40]}")
        time.sleep(3)
    print(f"\nRender EN concluído: {len(videos)} vídeos processados")

if __name__ == "__main__":
    run()
