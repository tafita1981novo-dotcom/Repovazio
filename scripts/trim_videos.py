#!/usr/bin/env python3
"""
trim_videos.py — Corta videos > 60s para 58s
Regra YouTube Shorts monetizacao: < 60 segundos
"""
import os, json, time, requests, subprocess, tempfile
from supabase import create_client

SB_URL = os.environ["SUPABASE_URL"]
SB_KEY = os.environ["SUPABASE_KEY"]
sb = create_client(SB_URL, SB_KEY)

# Videos para cortar: id, url_atual, duracao_atual
VIDEOS = [
    (682, "mp4s/v682_v4flat_1778847365.mp4", 61.7),
    (688, "mp4s/v688_v4flat_1778847641.mp4", 61.7),
    (689, "1778634177_O_perfeccionista_no_tem_medo_d_v8.mp4", 60.6),
]

MAX_SEGUNDOS = 58  # margem de segurança para < 60s

def download(url, path):
    r = requests.get(url, timeout=120)
    if r.status_code == 200:
        with open(path, "wb") as f: f.write(r.content)
        return True
    print("  DL err: " + str(r.status_code))
    return False

def upload_retry(data, fname, tentativas=3):
    for i in range(tentativas):
        try:
            r = requests.post(
                SB_URL + "/storage/v1/object/videos/" + fname,
                headers={"apikey":SB_KEY,"Authorization":"Bearer "+SB_KEY,
                         "Content-Type":"video/mp4","x-upsert":"true"},
                data=data, timeout=300)
            if r.status_code in [200,201]:
                return SB_URL + "/storage/v1/object/public/videos/" + fname
            print("  upload " + str(i+1) + ": " + str(r.status_code) + " " + r.text[:80])
        except Exception as e:
            print("  upload exc: " + str(e)[:80])
        time.sleep(3)
    return None

def main():
    print("=== TRIM < 60s para monetizacao YouTube Shorts ===")
    ok = 0
    for vid_id, url_path, dur_orig in VIDEOS:
        print("\n  #" + str(vid_id) + " (" + str(dur_orig) + "s → " + str(MAX_SEGUNDOS) + "s)")
        url = SB_URL + "/storage/v1/object/public/videos/" + url_path
        with tempfile.TemporaryDirectory() as tmp:
            orig = tmp + "/orig.mp4"
            cut  = tmp + "/cut.mp4"
            if not download(url, orig): continue
            # Cortar com stream copy (rapido, sem re-encode)
            r = subprocess.run([
                "ffmpeg","-y","-i",orig,
                "-t",str(MAX_SEGUNDOS),
                "-c:v","copy","-c:a","copy", cut
            ], capture_output=True, text=True, timeout=60)
            if r.returncode != 0 or not os.path.exists(cut):
                # Fallback: re-encode
                subprocess.run([
                    "ffmpeg","-y","-i",orig,"-t",str(MAX_SEGUNDOS),
                    "-c:v","libx264","-preset","fast","-crf","22",
                    "-c:a","aac","-b:a","128k","-pix_fmt","yuv420p",cut
                ], capture_output=True, timeout=180)
            if not os.path.exists(cut): print("  corte falhou"); continue
            # Verificar duracao
            probe = subprocess.run(
                ["ffprobe","-v","quiet","-print_format","json","-show_format",cut],
                capture_output=True, text=True)
            try: new_dur = float(json.loads(probe.stdout)["format"]["duration"])
            except: new_dur = MAX_SEGUNDOS
            sz = os.path.getsize(cut)
            print("  Novo: " + str(round(new_dur,1)) + "s | " + str(sz) + "B")
            with open(cut,"rb") as f: mp4b = f.read()
            fname = "mp4s/v" + str(vid_id) + "_58s_" + str(int(time.time())) + ".mp4"
            mp4_url = upload_retry(mp4b, fname)
            if not mp4_url: continue
            print("  OK: " + mp4_url)
            # Atualizar DB
            sb.table("content_pipeline").update({
                "mp4_url": mp4_url,
                "metadata": sb.table("content_pipeline").select("metadata").eq("id",vid_id).execute().data[0]["metadata"] or {}
            }).eq("id", vid_id).execute()
            # Update simples via SQL (mais confiavel)
            ok += 1
    print("\nConcluido: " + str(ok) + "/" + str(len(VIDEOS)))

if __name__ == "__main__":
    main()
