#!/usr/bin/env python3
"""Diagnóstico RTMP — roda em 30s, imprime resultado no log"""
import subprocess, socket, sys, os, shutil

def ffm():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    return shutil.which("ffmpeg") or "/usr/bin/ffmpeg"

print("=== DIAGNÓSTICO RTMP ===", flush=True)

ST_KEY = "ewme-91sq-yae7-yj1q-5skw"
ff = ffm()
print(f"FFmpeg: {ff}", flush=True)

# Teste de porta
for host,port in [("a.rtmp.youtube.com",1935),("a.rtmps.youtube.com",443),("youtube.com",80)]:
    try:
        s=socket.create_connection((host,port),timeout=8); s.close()
        print(f"  ✅ {host}:{port} — ACESSÍVEL", flush=True)
    except Exception as e:
        print(f"  ❌ {host}:{port} — BLOQUEADA ({e})", flush=True)

# Teste ffmpeg 15s com rtmp://
for proto in ["rtmp","rtmps"]:
    url = f"{proto}://a.{proto}.youtube.com/live2/{ST_KEY}"
    print(f"\nTestando {url[:50]}...", flush=True)
    cmd=[ff,"-y","-re",
         "-f","lavfi","-i","color=black:size=640x360:rate=10",
         "-f","lavfi","-i","sine=frequency=440:sample_rate=44100",
         "-f","lavfi","-i","sine=frequency=442:sample_rate=44100",
         "-filter_complex","[1:a][2:a]amerge=inputs=2,volume=0.3[a]",
         "-map","0:v","-map","[a]",
         "-c:v","libx264","-preset","ultrafast","-crf","40","-b:v","50k","-r","10","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","64k","-ac","2","-ar","44100",
         "-f","flv","-t","10", url]
    result=subprocess.run(cmd,capture_output=True,timeout=30)
    print(f"  rc={result.returncode}", flush=True)
    if result.returncode==0:
        print(f"  ✅ RTMP {proto.upper()} FUNCIONA!", flush=True)
        break
    else:
        err=result.stderr.decode()[-500:] if result.stderr else ""
        print(f"  Erro: {err[-200:]}", flush=True)

print("\n=== FIM DIAGNÓSTICO ===", flush=True)
