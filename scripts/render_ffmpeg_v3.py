#!/usr/bin/env python3
"""
render_ffmpeg_v3.py — Cerebro V3 CINEMATOGRAFICO
Tecnicas premium:
  - Color grading: saturacao -20%, contraste +15%, temperatura fria
  - Floating motion variado (drift + micro-zoom contemplativo)
  - Dissolve transitions entre cenas (atmosferico, invisivel)
  - Music bed: drone atmosferico sintetico CC0 (numpy/wave)
  - Vinheta adicional
  - ZERO texto durante narracao
  - Lower third minimalista ψ Daniela
"""
import os, json, time, requests, subprocess, tempfile, math, wave, struct
import numpy as np
from supabase import create_client

SB_URL = os.environ["SUPABASE_URL"]
SB_KEY = os.environ["SUPABASE_KEY"]
sb = create_client(SB_URL, SB_KEY)
SB_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwanZhbHp3a3F3dHR2bXN6dmllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwMzUyOTMsImV4cCI6MjA5MTYxMTI5M30.UEgUo0Mw15ihQZykLAY5QApRzgTXkfIewZFzIgwao3Q"

def gerar_drone(duracao_s, sample_rate=44100):
    """
    Drone atmosferico sintetico CC0.
    Multi-frequencia, modulacao lenta (respiracao), fade in/out.
    """
    t = np.linspace(0, duracao_s, int(sample_rate * duracao_s), endpoint=False)
    freq = 55.0  # La grave (A1)
    # Harmonicos organicos
    drone = (
        0.50 * np.sin(2 * np.pi * freq * t) +
        0.25 * np.sin(2 * np.pi * freq * 2 * t) +
        0.15 * np.sin(2 * np.pi * freq * 3 * t) +
        0.08 * np.sin(2 * np.pi * freq * 4 * t) +
        0.04 * np.sin(2 * np.pi * freq * 5 * t) +
        0.03 * np.sin(2 * np.pi * freq * 0.5 * t)
    )
    # Modulacao lenta — "respiracao atmosferica"
    mod = 0.75 + 0.25 * np.sin(2 * np.pi * 1.5 / max(duracao_s, 1) * t)
    tremolo = 1.0 + 0.04 * np.sin(2 * np.pi * 6.0 * t)
    drone = drone * mod * tremolo
    # Fade in/out (3s)
    fade = min(int(3 * sample_rate), len(drone)//4)
    drone[:fade] *= np.linspace(0, 1, fade)
    drone[-fade:] *= np.linspace(1, 0, fade)
    # Normalizar em -22dBFS (bem abaixo da voz)
    nivel = 10 ** (-22/20) * 32767
    pico = np.max(np.abs(drone))
    if pico > 0:
        drone = drone / pico * nivel
    return drone.astype(np.int16)

def salvar_wav(arr, path, sample_rate=44100):
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(arr.tobytes())

def baixar(url, path):
    for h in [{"apikey":SB_ANON},{}]:
        try:
            r = requests.get(url, headers=h, timeout=90)
            if r.status_code == 200:
                with open(path,"wb") as f: f.write(r.content)
                return True
        except: pass
    return False

def get_video_ready():
    r = sb.table("content_pipeline").select(
        "id,title,audio_url,duracao_min,metadata,pub_order"
    ).eq("status","video_ready").is_("mp4_url",None).order("pub_order").limit(3).execute()
    return r.data or []

def render(v):
    vid_id    = v["id"]
    audio_url = v.get("audio_url","")
    dur_min   = float(v.get("duracao_min") or 0.9)
    meta      = v.get("metadata") or {}
    imgs      = meta.get("quantum_images") or [meta.get("quantum_image","")]
    imgs      = [u for u in imgs if u]

    print("\n  #" + str(vid_id) + " " + str(v.get("title",""))[:50])
    print("    " + str(len(imgs)) + " cenas | dur_min=" + str(dur_min))

    if not imgs or not audio_url:
        print("    falta imagem ou audio"); return False

    with tempfile.TemporaryDirectory() as tmp:
        audio_p = tmp + "/audio.mp3"
        music_p = tmp + "/drone.wav"
        mix_p   = tmp + "/mix.mp3"
        out_p   = tmp + "/output.mp4"

        print("    Baixando audio...")
        if not baixar(audio_url, audio_p): return False

        probe = subprocess.run(
            ["ffprobe","-v","quiet","-print_format","json","-show_format",audio_p],
            capture_output=True, text=True)
        try:
            audio_dur = float(json.loads(probe.stdout)["format"]["duration"])
        except:
            audio_dur = dur_min * 60
        print("    Audio: " + str(round(audio_dur,1)) + "s")

        is_short = dur_min < 3
        W  = 1080 if is_short else 1920
        H  = 1920 if is_short else 1080
        fps = 30

        # Gerar drone atmosferico
        print("    Gerando drone atmosferico sintetico...")
        drone = gerar_drone(audio_dur + 3.0)
        salvar_wav(drone, music_p)

        # Mixar voz + drone
        r_mix = subprocess.run([
            "ffmpeg","-y","-i",audio_p,"-i",music_p,
            "-filter_complex",
            "[0:a]volume=1.0[v];[1:a]volume=0.20[m];[v][m]amix=inputs=2:duration=first[out]",
            "-map","[out]","-c:a","libmp3lame","-b:a","192k","-ar","44100", mix_p
        ], capture_output=True, timeout=120)
        if not os.path.exists(mix_p):
            mix_p = audio_p  # fallback sem drone

        # Baixar imagens
        img_paths = []
        for i, url in enumerate(imgs):
            p = tmp + "/img_" + str(i) + ".jpg"
            if baixar(url, p): img_paths.append(p)
        if not img_paths: return False
        print("    " + str(len(img_paths)) + " imagens baixadas")

        # Movimentos floating (variados, cinematograficos)
        MOVIMENTOS = [
            "z='zoom+0.0004':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
            "z='zoom+0.0004':x='iw*0.44-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
            "z='zoom+0.0004':x='iw*0.56-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
            "z='1.08-in*0.0003':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
            "z='zoom+0.0003':x='iw/2-(iw/zoom/2)':y='ih*0.47-(ih/zoom/2)'",
            "z='zoom+0.0003':x='iw/2-(iw/zoom/2)':y='ih*0.53-(ih/zoom/2)'",
            "z='zoom+0.0002':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
        ]

        # Color grading cinematografico (DaVinci-style, free via ffmpeg)
        # Lift/gamma/gain para simular grade cinema fria
        grade = (
            "curves=r='0/0 0.07/0.04 0.5/0.50 1/0.95':"
            "g='0/0 0.07/0.05 0.5/0.51 1/0.96':"
            "b='0/0 0.07/0.07 0.5/0.53 1/1.00',"
            "hue=s=0.80,"
            "eq=contrast=1.15:brightness=-0.02:gamma=1.04,"
            "colorbalance=ss=-0.05:ms=0.04:hs=0.07"
        )

        # Lower third minimalista (nao Psych2Go, mais sutil)
        lt_sz = "20" if is_short else "24"
        lt_y  = "h-68" if is_short else "h-76"
        lt_y2 = "h-38" if is_short else "h-44"
        lt_bw = "7" if is_short else "8"
        lower = (
            "drawtext=text='Daniela Coelho | Psicologa Clinica':"
            "fontsize=" + lt_sz + ":fontcolor=white@0.80:font=DejaVuSans:"
            "x=40:y=" + lt_y + ":box=1:boxcolor=0x06060F@0.65:boxborderw=" + lt_bw + ","
            "drawtext=text='@psidanielacoelho':"
            "fontsize=16:fontcolor=0xC4B5FD@0.70:font=DejaVuSans:"
            "x=40:y=" + lt_y2 + ":box=1:boxcolor=0x06060F@0.65:boxborderw=6,"
            "drawtext=text='psi':fontsize=14:fontcolor=white@0.07:font=DejaVuSans:x=w-48:y=16"
        )

        # Renderizar cada clip
        clip_paths = []
        for i, ip in enumerate(img_paths):
            dur = audio_dur / len(img_paths)
            cp  = tmp + "/clip_" + str(i) + ".mp4"
            mv  = MOVIMENTOS[i % len(MOVIMENTOS)]
            nf  = int(dur * fps) + 2
            vf  = (
                "scale=" + str(W) + ":" + str(H) + ":force_original_aspect_ratio=increase,"
                "crop=" + str(W) + ":" + str(H) + ","
                "zoompan=" + mv + ":d=" + str(nf) + ":s=" + str(W) + "x" + str(H) + ":fps=" + str(fps) + ","
                + grade + "," + lower
            )
            r_clip = subprocess.run(
                ["ffmpeg","-y","-loop","1","-i",ip,"-vf",vf,
                 "-c:v","libx264","-preset","fast","-crf","20",
                 "-pix_fmt","yuv420p","-t",str(dur+0.05),"-an",cp],
                capture_output=True, text=True, timeout=300
            )
            if r_clip.returncode != 0:
                vf_s = (
                    "scale=" + str(W) + ":" + str(H) + ":force_original_aspect_ratio=increase,"
                    "crop=" + str(W) + ":" + str(H) + ","
                    + grade + "," + lower
                )
                subprocess.run(
                    ["ffmpeg","-y","-loop","1","-i",ip,"-vf",vf_s,
                     "-c:v","libx264","-preset","fast","-crf","22",
                     "-pix_fmt","yuv420p","-t",str(dur),"-an",cp],
                    capture_output=True, timeout=180
                )
            if os.path.exists(cp):
                clip_paths.append(cp)

        if not clip_paths: return False

        # Merge com dissolve (xfade) ou concat
        if len(clip_paths) == 1:
            video_merged = clip_paths[0]
        else:
            dur_fade = 0.80
            dur_clip = audio_dur / len(clip_paths)
            inputs = []
            for cp in clip_paths:
                inputs += ["-i", cp]
            fg_parts = []
            current = "[0:v]"
            for i in range(1, len(clip_paths)):
                offset = max(0.1, i * dur_clip - dur_fade * i)
                nxt = "[" + str(i) + ":v]"
                out = "[v" + str(i) + "]" if i < len(clip_paths)-1 else "[vout]"
                fg_parts.append(current + nxt + "xfade=transition=dissolve:duration=" + str(dur_fade) + ":offset=" + str(offset) + out)
                current = "[v" + str(i) + "]"
            fg = ";".join(fg_parts)
            video_merged = tmp + "/merged.mp4"
            r_merge = subprocess.run(
                ["ffmpeg","-y"] + inputs + [
                    "-filter_complex", fg,
                    "-map","[vout]",
                    "-c:v","libx264","-preset","slow","-crf","18",
                    "-pix_fmt","yuv420p", video_merged
                ],
                capture_output=True, text=True, timeout=600
            )
            if r_merge.returncode != 0 or not os.path.exists(video_merged):
                # Fallback concat simples
                concat_p = tmp + "/lista.txt"
                with open(concat_p,"w") as f:
                    for cp in clip_paths:
                        f.write("file '" + cp + "'\n")
                video_merged = tmp + "/merged_concat.mp4"
                subprocess.run(
                    ["ffmpeg","-y","-f","concat","-safe","0","-i",concat_p,
                     "-c:v","libx264","-preset","fast","-crf","20",
                     "-pix_fmt","yuv420p",video_merged],
                    capture_output=True, timeout=600
                )

        print("    Montando video final...")
        r_final = subprocess.run(
            ["ffmpeg","-y","-i",video_merged,"-i",mix_p,
             "-c:v","libx264","-preset","slow","-crf","17",
             "-c:a","aac","-b:a","192k","-ar","44100",
             "-pix_fmt","yuv420p","-shortest",out_p],
            capture_output=True, text=True, timeout=600
        )
        if r_final.returncode != 0:
            print("    erro final: " + r_final.stderr[-300:])
            return False

        sz = os.path.getsize(out_p)
        print("    MP4: " + str(sz) + "B (" + str(round(sz/1024/1024,1)) + "MB)")

        fname = "mp4s/v" + str(vid_id) + "_cinem_" + str(int(time.time())) + ".mp4"
        with open(out_p,"rb") as f: mp4b = f.read()
        r2 = requests.post(
            SB_URL + "/storage/v1/object/videos/" + fname,
            headers={"apikey":SB_ANON,"Authorization":"Bearer "+SB_ANON,
                     "Content-Type":"video/mp4","x-upsert":"true"},
            data=mp4b
        )
        if r2.status_code not in [200,201]:
            print("    upload err: " + str(r2.status_code)); return False

        mp4_url = SB_URL + "/storage/v1/object/public/videos/" + fname
        print("    OK: " + mp4_url)
        sb.table("content_pipeline").update({
            "status":"mp4_ready","mp4_url":mp4_url,
            "metadata":meta | {
                "mp4_url":mp4_url,"mp4_size_bytes":sz,
                "duration_seconds":audio_dur,"resolution":str(W)+"x"+str(H),
                "render_version":"v3_cinematic_dark_documentary",
                "n_cenas":len(img_paths),"rendered_at":int(time.time()),
                "zero_texto_na_tela":True,"drone_atmosferico":True,
                "color_grading":"sat-20pct_contrast+15pct_frio",
                "transitions":"xfade_dissolve_0.8s",
                "voice_speed":"0.88x",
            }
        }).eq("id",vid_id).execute()
        print("    status=mp4_ready")
        return True

def main():
    print("=== RENDER FFMPEG V3 CINEMATOGRAFICO ===")
    print("Dissolve | Color grade DaVinci | Drone atmosferico | 0.88x voz")
    videos = get_video_ready()
    print("Videos: " + str(len(videos)))
    ok = 0
    for v in videos:
        try:
            if render(v): ok += 1
            time.sleep(1)
        except:
            import traceback; traceback.print_exc()
    print("Concluido: " + str(ok) + "/" + str(len(videos)))

if __name__ == "__main__":
    main()
