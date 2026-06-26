#!/usr/bin/env python3
import os, subprocess, sys, signal, random

STREAM_KEY = os.environ["DEEP_BROWN_STREAM_KEY"]
RTMP = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"

import random
SEED = random.randint(100000, 999999)
print(f"Seed: {SEED} | Conectando RTMP...")

# Filtro corrigido:
# 1. anoisesrc brown básico (sem equalizer que causa NaN)
# 2. aresample para garantir sample rate correto
# 3. lowpass para perfil V7 (corta agudos)
# 4. dynaudnorm para normalizar e eliminar NaN/Inf/picos
# 5. aformat para garantir formato correto antes do AAC
audio_filter = (
    "anoisesrc=color=brown:amplitude=0.35:sample_rate=44100,"
    "lowpass=f=300,"
    "lowpass=f=300,"
    "bass=g=4:f=60:w=80,"
    "dynaudnorm=p=0.95:m=10,"
    "aformat=sample_rates=44100:channel_layouts=stereo:sample_fmts=fltp,"
    "volume=-6dB"
)

cmd = [
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", "color=c=0x000000:size=1920x1080:rate=1",
    "-f", "lavfi", "-i", audio_filter,
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-tune", "stillimage",
    "-pix_fmt", "yuv420p",
    "-g", "2",
    "-b:v", "500k", "-maxrate", "500k", "-bufsize", "1000k",
    "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
    "-f", "flv", RTMP
]

print("FFmpeg iniciando...")
proc = subprocess.Popen(cmd)

def shutdown(sig, frame):
    print("Encerrando...")
    proc.terminate()
    proc.wait()
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

ret = proc.wait()
print(f"FFmpeg encerrado: {ret}")
