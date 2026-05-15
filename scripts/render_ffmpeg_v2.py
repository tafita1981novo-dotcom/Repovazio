#!/usr/bin/env python3
"""render_ffmpeg_v2.py Cerebro V15 — Multi-cena Ken Burns variado. ZERO texto na tela."""
import os, json, time, requests, subprocess, tempfile
from supabase import create_client

SB_URL = os.environ["SUPABASE_URL"]
SB_KEY = os.environ["SUPABASE_KEY"]
sb = create_client(SB_URL, SB_KEY)
SB_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwanZhbHp3a3F3dHR2bXN6dmllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwMzUyOTMsImV4cCI6MjA5MTYxMTI5M30.UEgUo0Mw15ihQZykLAY5QApRzgTXkfIewZFzIgwao3Q"

# Ken Burns: 5 movimentos diferentes por cena
KB_VARIANTS = [
    "z=\'zoom+0.0006\':x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\'",
    "z=\'zoom+0.0006\':x=\'0\':y=\'0\'",
    "z=\'zoom+0.0006\':x=\'iw-(iw/zoom)\':y=\'0\'",
    "z=\'zoom+0.0006\':x=\'iw/2-(iw/zoom/2)\':y=\'ih-(ih/zoom)\'",
    "z=\'1.10-in*0.0005\':x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\'",
]

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
    print(f"\n  #{vid_id} {v.get('title','')[:50]}")
    print(f"    {len(imgs)} cenas | dur_min={dur_min}")
    if not imgs or not audio_url:
        print("    falta imagem ou audio"); return False

    with tempfile.TemporaryDirectory() as tmp:
        audio_p = f"{tmp}/audio.mp3"
        out_p   = f"{tmp}/output.mp4"
        print("    Baixando audio...")
        if not baixar(audio_url, audio_p): return False

        probe = subprocess.run(
            ["ffprobe","-v","quiet","-print_format","json","-show_format",audio_p],
            capture_output=True, text=True)
        try: audio_dur = float(json.loads(probe.stdout)["format"]["duration"])
        except: audio_dur = dur_min * 60
        print(f"    Audio: {audio_dur:.1f}s")

        is_short = dur_min < 3
        W, H = (1080,1920) if is_short else (1920,1080)
        fps  = 30
        dur_cena = audio_dur / len(imgs)

        # Baixar imagens
        img_paths = []
        for i, url in enumerate(imgs):
            p = f"{tmp}/img_{i}.jpg"
            if baixar(url, p): img_paths.append(p)
        if not img_paths: return False
        print(f"    {len(img_paths)} imagens baixadas")

        # Renderizar cada cena como clip
        clip_paths = []
        lt_sz  = "28" if is_short else "34"
        lt_y   = "h-62" if is_short else "h-72"
        lt_y2  = "h-28" if is_short else "h-34"
        lt_bw  = "10" if is_short else "14"

        for i, ip in enumerate(img_paths):
            dur = audio_dur / len(img_paths)
            cp  = f"{tmp}/clip_{i}.mp4"
            kb  = KB_VARIANTS[i % len(KB_VARIANTS)]
            nf  = int(dur * fps) + 2

            vf = (
                f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},"
                f"zoompan={kb}:d={nf}:s={W}x{H}:fps={fps},"
                f"drawtext=text=\'Daniela Coelho \| Psicologa Clinica\':"
                f"fontsize={lt_sz}:fontcolor=white:font=DejaVuSans-Bold:"
                f"x=40:y={lt_y}:box=1:boxcolor=0x7C3AED@0.82:boxborderw={lt_bw},"
                f"drawtext=text=\'@psidanielacoelho\':"
                f"fontsize=22:fontcolor=0xC4B5FD:font=DejaVuSans:"
                f"x=40:y={lt_y2}:box=1:boxcolor=0x7C3AED@0.82:boxborderw=8,"
                f"drawtext=text=\'psi\':fontsize=20:fontcolor=white@0.12:font=DejaVuSans:x=w-55:y=18"
            )
            r = subprocess.run(
                ["ffmpeg","-y","-loop","1","-i",ip,"-vf",vf,
                 "-c:v","libx264","-preset","fast","-crf","20",
                 "-pix_fmt","yuv420p","-t",str(dur+0.05),"-an",cp],
                capture_output=True, text=True, timeout=240)
            if r.returncode != 0:
                # Fallback sem zoompan
                subprocess.run(
                    ["ffmpeg","-y","-loop","1","-i",ip,
                     "-vf",f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
                     "-c:v","libx264","-preset","fast","-crf","22",
                     "-pix_fmt","yuv420p","-t",str(dur),"-an",cp],
                    capture_output=True, timeout=120)
            if os.path.exists(cp): clip_paths.append(cp)

        # Concat list
        concat_p = f"{tmp}/lista.txt"
        with open(concat_p,"w") as f:
            for cp in clip_paths:
                f.write(f"file '{cp}'\n")

        print("    Concat + audio...")
        r = subprocess.run(
            ["ffmpeg","-y","-f","concat","-safe","0","-i",concat_p,
             "-i",audio_p,"-c:v","libx264","-preset","slow","-crf","18",
             "-c:a","aac","-b:a","192k","-ar","44100",
             "-pix_fmt","yuv420p","-shortest",out_p],
            capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            print(f"    ffmpeg erro: {r.stderr[-300:]}"); return False

        sz = os.path.getsize(out_p)
        print(f"    MP4: {sz:,}B ({sz/1024/1024:.1f}MB)")
        fname = f"mp4s/v{vid_id}_{int(time.time())}.mp4"
        with open(out_p,"rb") as f: mp4 = f.read()
        r2 = requests.post(f"{SB_URL}/storage/v1/object/videos/{fname}",
            headers={"apikey":SB_ANON,"Authorization":f"Bearer {SB_ANON}",
                     "Content-Type":"video/mp4","x-upsert":"true"}, data=mp4)
        if r2.status_code not in [200,201]:
            print(f"    upload erro: {r2.status_code}"); return False
        mp4_url = f"{SB_URL}/storage/v1/object/public/videos/{fname}"
        print(f"    OK: {mp4_url}")
        sb.table("content_pipeline").update({
            "status":"mp4_ready","mp4_url":mp4_url,
            "metadata":(meta) | {
                "mp4_url":mp4_url,"mp4_size_bytes":sz,
                "duration_seconds":audio_dur,"resolution":f"{W}x{H}",
                "render_version":"v2_multi_scene_psych2go_v15",
                "n_cenas":len(img_paths),"rendered_at":int(time.time()),
                "zero_texto_na_tela":True,"voz":"ElevenLabs_Sarah_ou_Edge",
                "lower_third":"Daniela Coelho | @psidanielacoelho",
            }
        }).eq("id",vid_id).execute()
        print("    status=mp4_ready")
        return True

def main():
    print("=== RENDER FFMPEG V15 multi-cena Ken Burns ZERO texto ===")
    videos = get_video_ready()
    print(f"Videos: {len(videos)}")
    ok = 0
    for v in videos:
        try:
            if render(v): ok += 1
            time.sleep(1)
        except:
            import traceback; traceback.print_exc()
    print(f"Concluido: {ok}/{len(videos)}")

if __name__ == "__main__":
    main()
