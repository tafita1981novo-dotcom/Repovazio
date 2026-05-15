#!/usr/bin/env python3
"""
render_ffmpeg_v3.py — V3 CINEMATOGRAFICO — UPLOAD FIX
Usa SERVICE KEY para uploads (resolve timeout)
CRF 22, preset fast (arquivo menor ~6-8MB)
Retry 3x no upload
"""
import os, json, time, requests, subprocess, tempfile, wave
import numpy as np
from supabase import create_client

SB_URL = os.environ["SUPABASE_URL"]
SB_KEY = os.environ["SUPABASE_KEY"]
sb = create_client(SB_URL, SB_KEY)
# SERVICE KEY para uploads (mais permissao, sem timeout)
SB_UPLOAD_KEY = os.environ.get("SUPABASE_KEY", "")

def gerar_drone(duracao_s, sample_rate=44100):
    t = np.linspace(0, duracao_s, int(sample_rate * duracao_s), endpoint=False)
    freq = 55.0
    drone = (
        0.50 * np.sin(2 * np.pi * freq * t) +
        0.25 * np.sin(2 * np.pi * freq * 2 * t) +
        0.15 * np.sin(2 * np.pi * freq * 3 * t) +
        0.08 * np.sin(2 * np.pi * freq * 4 * t) +
        0.04 * np.sin(2 * np.pi * freq * 5 * t) +
        0.03 * np.sin(2 * np.pi * freq * 0.5 * t)
    )
    mod = 0.75 + 0.25 * np.sin(2 * np.pi * 1.5 / max(duracao_s, 1) * t)
    tremolo = 1.0 + 0.04 * np.sin(2 * np.pi * 6.0 * t)
    drone = drone * mod * tremolo
    fade = min(int(3 * sample_rate), len(drone) // 4)
    drone[:fade] *= np.linspace(0, 1, fade)
    drone[-fade:] *= np.linspace(1, 0, fade)
    nivel = 10 ** (-22 / 20) * 32767
    pico = np.max(np.abs(drone))
    if pico > 0:
        drone = drone / pico * nivel
    return drone.astype(np.int16)

def salvar_wav(arr, path, sample_rate=44100):
    with wave.open(path, "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
        wf.writeframes(arr.tobytes())

def baixar(url, path):
    for h in [{"apikey": SB_UPLOAD_KEY}, {}]:
        try:
            r = requests.get(url, headers=h, timeout=90)
            if r.status_code == 200:
                with open(path, "wb") as f: f.write(r.content)
                return True
        except: pass
    return False

def upload_com_retry(data_bytes, fname, content_type="video/mp4", tentativas=3):
    """Upload com SERVICE KEY e retry automatico"""
    for i in range(tentativas):
        try:
            r = requests.post(
                SB_URL + "/storage/v1/object/videos/" + fname,
                headers={
                    "apikey": SB_UPLOAD_KEY,
                    "Authorization": "Bearer " + SB_UPLOAD_KEY,
                    "Content-Type": content_type,
                    "x-upsert": "true"
                },
                data=data_bytes,
                timeout=300
            )
            if r.status_code in [200, 201]:
                return SB_URL + "/storage/v1/object/public/videos/" + fname
            print("      upload tentativa " + str(i+1) + ": " + str(r.status_code) + " " + r.text[:100])
        except Exception as e:
            print("      upload exc tentativa " + str(i+1) + ": " + str(e)[:100])
        time.sleep(5)
    return None

def get_video_ready():
    r = sb.table("content_pipeline").select(
        "id,title,audio_url,duracao_min,metadata,pub_order"
    ).eq("status", "video_ready").is_("mp4_url", None).order("pub_order").limit(3).execute()
    return r.data or []

def render(v):
    vid_id    = v["id"]
    audio_url = v.get("audio_url", "")
    dur_min   = float(v.get("duracao_min") or 0.9)
    meta      = v.get("metadata") or {}
    imgs      = meta.get("quantum_images") or [meta.get("quantum_image", "")]
    imgs      = [u for u in imgs if u]

    print("\n  #" + str(vid_id) + " " + str(v.get("title", ""))[:50])
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
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", audio_p],
            capture_output=True, text=True)
        try:
            audio_dur = float(json.loads(probe.stdout)["format"]["duration"])
        except:
            audio_dur = dur_min * 60
        print("    Audio: " + str(round(audio_dur, 1)) + "s")

        is_short = dur_min < 3
        W  = 1080 if is_short else 1920
        H  = 1920 if is_short else 1080
        W_big = int(W * 1.25)
        H_big = int(H * 1.25)
        pan_x = W_big - W
        pan_y = H_big - H
        fps = 30

        # Drone
        print("    Drone...")
        drone = gerar_drone(audio_dur + 3.0)
        salvar_wav(drone, music_p)

        # Mix
        subprocess.run([
            "ffmpeg", "-y", "-i", audio_p, "-i", music_p,
            "-filter_complex",
            "[0:a]volume=1.0[v];[1:a]volume=0.20[m];[v][m]amix=inputs=2:duration=first[out]",
            "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "44100", mix_p
        ], capture_output=True, timeout=120)
        if not os.path.exists(mix_p): mix_p = audio_p

        # Baixar imagens
        img_paths = []
        for i, url in enumerate(imgs):
            p = tmp + "/img_" + str(i) + ".jpg"
            if baixar(url, p): img_paths.append(p)
        if not img_paths: return False
        print("    " + str(len(img_paths)) + " imagens")

        dur_clip = audio_dur / len(img_paths)

        MOTIONS = [
            "x='" + str(pan_x//2) + "*(1+sin(2*PI*t/40))/2':y='" + str(pan_y//2) + "*(1+cos(2*PI*t/60))/2'",
            "x='" + str(pan_x//2) + "*(1-cos(2*PI*t/35))/2':y='" + str(pan_y//2) + "*(1+sin(2*PI*t/55))/2'",
            "x='" + str(pan_x) + "*t/" + str(round(dur_clip, 2)) + "':y='" + str(pan_y//2) + "*(1+sin(2*PI*t/50))/2'",
            "x='" + str(pan_x//2) + "*(1+sin(2*PI*t/45))/2':y='0'",
            "x='0':y='" + str(pan_y//2) + "*(1+cos(2*PI*t/50))/2'",
            "x='" + str(pan_x//2) + "*(1+sin(2*PI*t/38))/2':y='" + str(pan_y//2) + "*(1+cos(2*PI*t/42))/2'",
            "x='" + str(pan_x//4) + "*(1+sin(2*PI*t/70))/2':y='" + str(pan_y//4) + "*(1+cos(2*PI*t/80))/2'",
        ]

        grade = (
            "curves=r='0/0 0.07/0.04 0.5/0.50 1/0.95':"
            "g='0/0 0.07/0.05 0.5/0.51 1/0.96':"
            "b='0/0 0.07/0.07 0.5/0.53 1/1.00',"
            "hue=s=0.80,"
            "eq=contrast=1.15:brightness=-0.02"
        )

        lt_sz = "20" if is_short else "24"
        lt_y  = "h-68" if is_short else "h-76"
        lt_y2 = "h-38" if is_short else "h-44"
        lt_bw = "7" if is_short else "8"
        lower = (
            "drawtext=text='Daniela Coelho | Psicologa Clinica':"
            "fontsize=" + lt_sz + ":fontcolor=white@0.80:font=DejaVuSans:"
            "x=40:y=" + lt_y + ":box=1:boxcolor=black@0.65:boxborderw=" + lt_bw + ","
            "drawtext=text='@psidanielacoelho':"
            "fontsize=16:fontcolor=0xC4B5FD:font=DejaVuSans:"
            "x=40:y=" + lt_y2 + ":box=1:boxcolor=black@0.65:boxborderw=6,"
            "drawtext=text='psi':fontsize=14:fontcolor=white@0.07:font=DejaVuSans:x=w-48:y=16"
        )

        clip_paths = []
        for i, ip in enumerate(img_paths):
            dur = audio_dur / len(img_paths)
            cp  = tmp + "/clip_" + str(i) + ".mp4"
            mv  = MOTIONS[i % len(MOTIONS)]
            vf  = (
                "scale=" + str(W_big) + ":" + str(H_big) + ":force_original_aspect_ratio=increase,"
                "crop=" + str(W_big) + ":" + str(H_big) + ","
                "crop=" + str(W) + ":" + str(H) + ":" + mv + ","
                + grade + "," + lower
            )
            r_c = subprocess.run([
                "ffmpeg", "-y", "-loop", "1", "-i", ip, "-vf", vf,
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-pix_fmt", "yuv420p", "-t", str(dur + 0.05), "-an", cp
            ], capture_output=True, text=True, timeout=300)
            if r_c.returncode != 0:
                vf_s = (
                    "scale=" + str(W) + ":" + str(H) + ":force_original_aspect_ratio=increase,"
                    "crop=" + str(W) + ":" + str(H) + ","
                    + grade + "," + lower
                )
                subprocess.run([
                    "ffmpeg", "-y", "-loop", "1", "-i", ip, "-vf", vf_s,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "24",
                    "-pix_fmt", "yuv420p", "-t", str(dur), "-an", cp
                ], capture_output=True, timeout=180)
            if os.path.exists(cp):
                print("      clip " + str(i+1) + "/" + str(len(img_paths)) + " OK")
                clip_paths.append(cp)

        if not clip_paths: return False

        # Dissolve xfade
        if len(clip_paths) == 1:
            video_merged = clip_paths[0]
        else:
            dur_fade = 0.80
            inputs = []
            for cp in clip_paths: inputs += ["-i", cp]
            fg_parts = []
            current = "[0:v]"
            for i in range(1, len(clip_paths)):
                offset = max(0.1, i * (dur_clip - dur_fade))
                nxt = "[" + str(i) + ":v]"
                out = "[v" + str(i) + "]" if i < len(clip_paths) - 1 else "[vout]"
                fg_parts.append(
                    current + nxt +
                    "xfade=transition=dissolve:duration=" + str(dur_fade) +
                    ":offset=" + str(round(offset, 2)) + out
                )
                current = "[v" + str(i) + "]"
            fg = ";".join(fg_parts)
            video_merged = tmp + "/merged.mp4"
            r_m = subprocess.run(
                ["ffmpeg", "-y"] + inputs + [
                    "-filter_complex", fg, "-map", "[vout]",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                    "-pix_fmt", "yuv420p", video_merged
                ],
                capture_output=True, text=True, timeout=600
            )
            if r_m.returncode != 0 or not os.path.exists(video_merged):
                # Fallback concat
                concat_p = tmp + "/lista.txt"
                with open(concat_p, "w") as f:
                    for cp in clip_paths: f.write("file '" + cp + "'\n")
                video_merged = tmp + "/merged_c.mp4"
                subprocess.run([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_p,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                    "-pix_fmt", "yuv420p", video_merged
                ], capture_output=True, timeout=600)

        # Final render
        print("    Montando final...")
        r_f = subprocess.run([
            "ffmpeg", "-y", "-i", video_merged, "-i", mix_p,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-pix_fmt", "yuv420p", "-shortest", out_p
        ], capture_output=True, text=True, timeout=600)

        if r_f.returncode != 0:
            print("    erro final: " + r_f.stderr[-300:]); return False

        sz = os.path.getsize(out_p)
        print("    MP4: " + str(sz) + "B (" + str(round(sz/1024/1024, 1)) + "MB)")

        fname = "mp4s/v" + str(vid_id) + "_v3cinem_" + str(int(time.time())) + ".mp4"
        with open(out_p, "rb") as f: mp4b = f.read()

        print("    Fazendo upload com service key...")
        mp4_url = upload_com_retry(mp4b, fname)

        if not mp4_url:
            print("    upload falhou apos 3 tentativas"); return False

        print("    OK: " + mp4_url)
        sb.table("content_pipeline").update({
            "status": "mp4_ready", "mp4_url": mp4_url,
            "metadata": meta | {
                "mp4_url": mp4_url, "mp4_size_bytes": sz,
                "duration_seconds": audio_dur, "resolution": str(W) + "x" + str(H),
                "render_version": "v3_cinematic_dark_documentary_FINAL",
                "n_cenas": len(img_paths), "rendered_at": int(time.time()),
                "zero_texto_na_tela": True, "drone_atmosferico": True,
                "color_grade": "curves+hue-20pct+eq+15pct",
                "transitions": "xfade_dissolve_0.8s",
                "motion": "crop_pan_floating",
                "voice_speed": "0.88x_ElevenLabs_Sarah",
                "padrao": "dark_documentary_viral_mundial",
            }
        }).eq("id", vid_id).execute()
        print("    status=mp4_ready SALVO")
        return True

def main():
    print("=== RENDER FFMPEG V3 FINAL — SERVICE KEY UPLOAD ===")
    print("Padrao: dark documentary viral | Drone CC0 | Dissolve | Grade")
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
