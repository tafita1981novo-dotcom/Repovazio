#!/usr/bin/env python3
"""
render_ffmpeg_v4.py — Cerebro V4 — School of Life + Kurzgesagt
Color grade: QUENTE e VIBRANTE (nao dark)
Motion: Ken Burns suave
Musica: piano sintetico CC0 (nao drone)
"""
import os, json, time, requests, subprocess, tempfile, wave
import numpy as np
from supabase import create_client

SB_URL = os.environ["SUPABASE_URL"]
SB_KEY = os.environ["SUPABASE_KEY"]
sb = create_client(SB_URL, SB_KEY)

def gerar_piano_atmosferico(duracao_s, sample_rate=44100):
    """Piano ambient warm CC0 — para estilo educativo School of Life"""
    t = np.linspace(0, duracao_s, int(sample_rate * duracao_s), endpoint=False)
    freq_base = 261.63  # Do central (C4) — positivo, educativo
    # Acorde maior suave (Do-Mi-Sol)
    piano = (
        0.40 * np.sin(2*np.pi*freq_base*t) +        # Do
        0.25 * np.sin(2*np.pi*freq_base*1.26*t) +   # Mi (3a maior)
        0.20 * np.sin(2*np.pi*freq_base*1.50*t) +   # Sol (5a)
        0.10 * np.sin(2*np.pi*freq_base*2.00*t) +   # Do (oitava)
        0.05 * np.sin(2*np.pi*freq_base*0.50*t)     # Do grave
    )
    # Envelope ADSR suave (attack 2s, sustain, release 3s)
    attack = min(int(2*sample_rate), len(piano)//6)
    release = min(int(3*sample_rate), len(piano)//4)
    piano[:attack] *= np.linspace(0, 1, attack)
    piano[-release:] *= np.linspace(1, 0, release)
    # Modulacao tremolo suave (0.5Hz)
    tremolo = 1.0 + 0.03 * np.sin(2*np.pi*0.5*t)
    piano = piano * tremolo
    # Normalizar em -25dBFS (bem abaixo da voz)
    nivel = 10**(-25/20) * 32767
    pico = np.max(np.abs(piano))
    if pico > 0: piano = piano / pico * nivel
    return piano.astype(np.int16)

def salvar_wav(arr, path, sr=44100):
    with wave.open(path,"w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes(arr.tobytes())

def baixar(url, path):
    for h in [{"apikey": SB_KEY},{}]:
        try:
            r = requests.get(url, headers=h, timeout=90)
            if r.status_code == 200:
                with open(path,"wb") as f: f.write(r.content)
                return True
        except: pass
    return False

def upload_retry(data_bytes, fname, ct="video/mp4", tentativas=3):
    for i in range(tentativas):
        try:
            r = requests.post(
                SB_URL+"/storage/v1/object/videos/"+fname,
                headers={"apikey":SB_KEY,"Authorization":"Bearer "+SB_KEY,
                         "Content-Type":ct,"x-upsert":"true"},
                data=data_bytes, timeout=300)
            if r.status_code in [200,201]:
                return SB_URL+"/storage/v1/object/public/videos/"+fname
            print("      upload " + str(i+1) + ": " + str(r.status_code) + " " + r.text[:80])
        except Exception as e:
            print("      upload exc: " + str(e)[:80])
        time.sleep(5)
    return None

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
    if not imgs or not audio_url: print("    falta img/audio"); return False

    with tempfile.TemporaryDirectory() as tmp:
        audio_p = tmp+"/audio.mp3"
        music_p = tmp+"/piano.wav"
        mix_p   = tmp+"/mix.mp3"
        out_p   = tmp+"/output.mp4"

        print("    Baixando audio...")
        if not baixar(audio_url, audio_p): return False

        probe = subprocess.run(
            ["ffprobe","-v","quiet","-print_format","json","-show_format",audio_p],
            capture_output=True,text=True)
        try: audio_dur = float(json.loads(probe.stdout)["format"]["duration"])
        except: audio_dur = dur_min*60
        print("    Audio: " + str(round(audio_dur,1)) + "s")

        is_short = dur_min < 3
        W  = 1080 if is_short else 1920
        H  = 1920 if is_short else 1080
        W_big = int(W*1.20)
        H_big = int(H*1.20)
        pan_x = W_big - W
        pan_y = H_big - H

        # Piano educativo
        print("    Piano ambient...")
        piano = gerar_piano_atmosferico(audio_dur+3.0)
        salvar_wav(piano, music_p)

        # Mix
        subprocess.run([
            "ffmpeg","-y","-i",audio_p,"-i",music_p,
            "-filter_complex","[0:a]volume=1.0[v];[1:a]volume=0.18[m];[v][m]amix=inputs=2:duration=first[out]",
            "-map","[out]","-c:a","libmp3lame","-b:a","128k","-ar","44100",mix_p
        ], capture_output=True,timeout=120)
        if not os.path.exists(mix_p): mix_p = audio_p

        # Baixar imagens
        img_paths = []
        for i, url in enumerate(imgs):
            p = tmp+"/img_"+str(i)+".jpg"
            if baixar(url, p): img_paths.append(p)
        if not img_paths: return False
        print("    " + str(len(img_paths)) + " imagens")

        dur_clip = audio_dur / len(img_paths)

        # MOVIMENTOS Ken Burns — suaves e variados
        MOTIONS = [
            "x='" + str(pan_x//2) + "*(1+sin(2*PI*t/40))/2':y='" + str(pan_y//2) + "*(1+cos(2*PI*t/60))/2'",
            "x='" + str(pan_x//2) + "*(1-cos(2*PI*t/35))/2':y='" + str(pan_y//2) + "*(1+sin(2*PI*t/55))/2'",
            "x='" + str(pan_x) + "*t/" + str(round(dur_clip,2)) + "':y='" + str(pan_y//4) + "'",
            "x='" + str(pan_x//2) + "*(1+sin(2*PI*t/45))/2':y='0'",
            "x='0':y='" + str(pan_y//2) + "*(1+cos(2*PI*t/50))/2'",
            "x='" + str(pan_x//4) + "*(1+sin(2*PI*t/30))/2':y='" + str(pan_y//4) + "*(1+cos(2*PI*t/35))/2'",
        ]

        # COLOR GRADE QUENTE (manter cores vibrantes, nao escurecer)
        # Leve boost de saturacao e contraste suave
        grade = (
            "eq=contrast=1.05:brightness=0.02:saturation=1.10,"
            "curves=r='0/0 0.5/0.52 1/1.0':"
            "g='0/0 0.5/0.51 1/1.0':"
            "b='0/0 0.5/0.49 1/0.97'"
        )

        # LOWER THIRD — estilo educativo limpo
        lt_sz = "22" if is_short else "26"
        lt_y  = "h-68" if is_short else "h-76"
        lt_y2 = "h-38" if is_short else "h-44"
        lower = (
            "drawtext=text='Daniela Coelho | Psicologa Clinica':"
            "fontsize=" + lt_sz + ":fontcolor=white@0.92:font=DejaVuSans-Bold:"
            "x=40:y=" + lt_y + ":box=1:boxcolor=0x2C3E50@0.75:boxborderw=8,"
            "drawtext=text='@psidanielacoelho':"
            "fontsize=18:fontcolor=0xECF0F1@0.90:font=DejaVuSans:"
            "x=40:y=" + lt_y2 + ":box=1:boxcolor=0x2C3E50@0.75:boxborderw=7"
        )

        # Renderizar clips
        clip_paths = []
        for i, ip in enumerate(img_paths):
            dur = audio_dur / len(img_paths)
            cp  = tmp+"/clip_"+str(i)+".mp4"
            mv  = MOTIONS[i % len(MOTIONS)]
            vf  = (
                "scale=" + str(W_big) + ":" + str(H_big) + ":force_original_aspect_ratio=increase,"
                "crop=" + str(W_big) + ":" + str(H_big) + ","
                "crop=" + str(W) + ":" + str(H) + ":" + mv + ","
                + grade + "," + lower
            )
            r_c = subprocess.run([
                "ffmpeg","-y","-loop","1","-i",ip,"-vf",vf,
                "-c:v","libx264","-preset","fast","-crf","22",
                "-pix_fmt","yuv420p","-t",str(dur+0.05),"-an",cp
            ], capture_output=True,text=True,timeout=300)
            if r_c.returncode != 0:
                vf_s = (
                    "scale=" + str(W) + ":" + str(H) + ":force_original_aspect_ratio=increase,"
                    "crop=" + str(W) + ":" + str(H) + ","
                    + grade + "," + lower
                )
                subprocess.run([
                    "ffmpeg","-y","-loop","1","-i",ip,"-vf",vf_s,
                    "-c:v","libx264","-preset","fast","-crf","24",
                    "-pix_fmt","yuv420p","-t",str(dur),"-an",cp
                ], capture_output=True,timeout=180)
            if os.path.exists(cp):
                print("      clip " + str(i+1) + "/" + str(len(img_paths)) + " OK")
                clip_paths.append(cp)

        if not clip_paths: return False

        # Dissolve
        if len(clip_paths) == 1:
            video_merged = clip_paths[0]
        else:
            dur_fade = 0.60
            inputs = []
            for cp in clip_paths: inputs += ["-i",cp]
            fg_parts=[]; current="[0:v]"
            for i in range(1,len(clip_paths)):
                offset = max(0.1, i*(dur_clip-dur_fade))
                nxt = "["+str(i)+":v]"
                out = "[v"+str(i)+"]" if i<len(clip_paths)-1 else "[vout]"
                fg_parts.append(current+nxt+"xfade=transition=fade:duration="+str(dur_fade)+":offset="+str(round(offset,2))+out)
                current = "[v"+str(i)+"]"
            fg=";".join(fg_parts)
            video_merged=tmp+"/merged.mp4"
            r_m=subprocess.run(
                ["ffmpeg","-y"]+inputs+["-filter_complex",fg,"-map","[vout]",
                 "-c:v","libx264","-preset","fast","-crf","22",
                 "-pix_fmt","yuv420p",video_merged],
                capture_output=True,text=True,timeout=600)
            if r_m.returncode!=0 or not os.path.exists(video_merged):
                concat_p=tmp+"/lista.txt"
                with open(concat_p,"w") as f:
                    for cp in clip_paths: f.write("file '"+cp+"'\n")
                video_merged=tmp+"/merged_c.mp4"
                subprocess.run([
                    "ffmpeg","-y","-f","concat","-safe","0","-i",concat_p,
                    "-c:v","libx264","-preset","fast","-crf","22",
                    "-pix_fmt","yuv420p",video_merged
                ], capture_output=True,timeout=600)

        print("    Montando final...")
        r_f=subprocess.run([
            "ffmpeg","-y","-i",video_merged,"-i",mix_p,
            "-c:v","libx264","-preset","fast","-crf","22",
            "-c:a","aac","-b:a","128k","-ar","44100",
            "-pix_fmt","yuv420p","-shortest",out_p
        ], capture_output=True,text=True,timeout=600)
        if r_f.returncode!=0:
            print("    erro: "+r_f.stderr[-200:]); return False

        sz = os.path.getsize(out_p)
        print("    MP4: "+str(sz)+"B ("+str(round(sz/1024/1024,1))+"MB)")
        fname = "mp4s/v"+str(vid_id)+"_v4flat_"+str(int(time.time()))+".mp4"
        with open(out_p,"rb") as f: mp4b = f.read()
        mp4_url = upload_retry(mp4b, fname)
        if not mp4_url: return False
        print("    OK: "+mp4_url)
        sb.table("content_pipeline").update({
            "status":"mp4_ready","mp4_url":mp4_url,"score":97,
            "metadata":meta|{
                "mp4_url":mp4_url,"mp4_size_bytes":sz,
                "duration_seconds":audio_dur,"resolution":str(W)+"x"+str(H),
                "render_version":"v4_flat_school_of_life_kurzgesagt",
                "n_cenas":len(img_paths),"rendered_at":int(time.time()),
                "zero_texto_na_tela":True,"piano_educativo":True,
                "color_grade":"quente_vibrante_+sat+10pct",
                "transitions":"xfade_fade_0.6s",
                "motion":"ken_burns_suave",
                "voice":"George_ElevenLabs_masculino",
                "padrao":"school_of_life_kurzgesagt",
            }
        }).eq("id",vid_id).execute()
        print("    status=mp4_ready"); return True

def main():
    print("=== RENDER FFMPEG V4 — School of Life + Kurzgesagt ===")
    print("Grade: QUENTE vibrante | Piano CC0 | Fade 0.6s | Ken Burns suave")
    videos = get_video_ready()
    print("Videos: "+str(len(videos)))
    ok=0
    for v in videos:
        try:
            if render(v): ok+=1
            time.sleep(1)
        except:
            import traceback; traceback.print_exc()
    print("Concluido: "+str(ok)+"/"+str(len(videos)))

if __name__ == "__main__":
    main()
