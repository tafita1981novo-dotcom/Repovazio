#!/usr/bin/env python3
"""
DBN Live 24/7 para VM GCP
Brown noise V7 via ffmpeg lavfi — tela preta absoluta
Reinicia automaticamente se cair
"""
import os, subprocess, sys, signal, time, random

STREAM_KEY = os.environ.get("DEEP_BROWN_STREAM_KEY","")
if not STREAM_KEY:
    print("ERRO: DEEP_BROWN_STREAM_KEY não definida")
    sys.exit(1)

RTMP = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"

# Filtro V7 corrigido — sem NaN/Inf
# lowpass duplo 300Hz replica perfil V7 + bass boost sub-grave
AUDIO = (
    "anoisesrc=color=brown:amplitude=0.35:sample_rate=44100,"
    "lowpass=f=300,"
    "lowpass=f=300,"
    "bass=g=4:f=60:w=80,"
    "aresample=44100,"
    "asetnsamples=n=1024,"
    "aformat=sample_rates=44100:channel_layouts=stereo:sample_fmts=fltp,"
    "volume=0.7"
)

CMD = [
    "ffmpeg", "-y", "-re",
    "-f", "lavfi", "-i", f"color=c=0x000000:size=1920x1080:rate=1",
    "-f", "lavfi", "-i", AUDIO,
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-tune",   "stillimage",
    "-pix_fmt","yuv420p",
    "-g",      "2",
    "-b:v",    "500k",
    "-maxrate","500k",
    "-bufsize","1000k",
    "-c:a",    "aac",
    "-b:a",    "192k",
    "-ar",     "44100",
    "-f",      "flv", RTMP
]

print(f"DBN Live 24/7 iniciando...")
print(f"RTMP: rtmp://a.rtmp.youtube.com/live2/****")

tentativa = 0
while True:
    tentativa += 1
    print(f"[tentativa {tentativa}] Conectando...")
    proc = subprocess.run(CMD)
    if proc.returncode == 0:
        print("Stream encerrado normalmente")
        break
    print(f"Stream caiu (código {proc.returncode}) — reiniciando em 10s...")
    time.sleep(10)
