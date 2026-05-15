#!/usr/bin/env python3
"""
trim_videos.py V2 — Dinâmico: lê do DB todos os vídeos com audio > 60s e trim para 58s
Regra YouTube Shorts monetizacao: OBRIGATORIO < 60 segundos
"""
import os, json, time, requests, subprocess, tempfile
from supabase import create_client

SB_URL = os.environ["SUPABASE_URL"]
SB_KEY = os.environ["SUPABASE_KEY"]
sb = create_client(SB_URL, SB_KEY)
MAX_S = 58

def probe_duration(path):
    r = subprocess.run(["ffprobe","-v","quiet","-print_format","json",
        "-show_format", path], capture_output=True, text=True)
    try: return float(json.loads(r.stdout)["format"]["duration"])
    except: return 0.0

def upload_retry(data, fname, tentativas=3):
    for i in range(tentativas):
        try:
            r = requests.post(SB_URL+"/storage/v1/object/videos/"+fname,
                headers={"apikey":SB_KEY,"Authorization":"Bearer "+SB_KEY,
                         "Content-Type":"video/mp4","x-upsert":"true"},
                data=data, timeout=300)
            if r.status_code in [200,201]:
                return SB_URL+"/storage/v1/object/public/videos/"+fname
        except: pass
        time.sleep(3)
    return None

def main():
    print("=== TRIM V2 — Todos os videos > 60s ===")
    
    # Buscar todos os mp4_ready com mp4_url
    rows = sb.table("content_pipeline").select(
        "id,mp4_url,metadata"
    ).eq("status","mp4_ready").not_.is_("mp4_url","null").execute().data or []
    
    print(f"Videos mp4_ready com mp4_url: {len(rows)}")
    ok = 0
    for v in rows:
        vid_id = v["id"]
        url = v.get("mp4_url","")
        if not url: continue
        
        with tempfile.TemporaryDirectory() as tmp:
            orig = tmp+"/orig.mp4"
            cut  = tmp+"/cut.mp4"
            
            # Download
            r = requests.get(url, timeout=120)
            if r.status_code != 200: continue
            with open(orig,"wb") as f: f.write(r.content)
            
            dur = probe_duration(orig)
            print(f"  #{vid_id}: {dur:.1f}s")
            if dur <= 60.0:
                print(f"    OK — sem trim")
                continue
            
            print(f"    TRIMMING {dur:.1f}s → {MAX_S}s")
            res = subprocess.run(["ffmpeg","-y","-i",orig,"-t",str(MAX_S),
                "-c:v","copy","-c:a","copy",cut],capture_output=True,timeout=60)
            if res.returncode != 0 or not os.path.exists(cut):
                subprocess.run(["ffmpeg","-y","-i",orig,"-t",str(MAX_S),
                    "-c:v","libx264","-preset","fast","-crf","22",
                    "-c:a","aac","-b:a","128k","-pix_fmt","yuv420p",cut],
                    capture_output=True,timeout=120)
            if not os.path.exists(cut): continue
            
            new_dur = probe_duration(cut)
            sz = os.path.getsize(cut)
            print(f"    Novo: {new_dur:.1f}s {sz//1024}KB")
            
            with open(cut,"rb") as f: mp4b = f.read()
            fname = f"mp4s/v{vid_id}_58s_{int(time.time())}.mp4"
            mp4_url = upload_retry(mp4b, fname)
            if not mp4_url: continue
            
            print(f"    OK: {mp4_url[-50:]}")
            sb.table("content_pipeline").update({
                "mp4_url": mp4_url,
                "metadata": (v.get("metadata") or {}) | {"duration_seconds": new_dur, "trimmed_58s": True}
            }).eq("id", vid_id).execute()
            ok += 1
    
    print(f"Concluido: {ok} vídeos trimados")

if __name__ == "__main__":
    main()
