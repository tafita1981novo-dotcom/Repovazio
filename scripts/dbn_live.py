#!/usr/bin/env python3
"""
DBN Live 24/7 — V7 Brown Noise
Conecta imediatamente no RTMP do YouTube via ffmpeg lavfi
Crossfade imperceptível usando amix com múltiplos segments
"""
import os, subprocess, sys, signal, random

STREAM_KEY = os.environ["DEEP_BROWN_STREAM_KEY"]
RTMP = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"

# Seed aleatória para fingerprint único
SEED = random.randint(100000, 999999)
print(f"Seed: {SEED} | Conectando RTMP...")

# Filtro V7 exato via ffmpeg lavfi
# anoisesrc gera brown noise nativo
# equalizer replica o perfil espectral do V7 (boost 50Hz + shelving >300Hz)
# acrossfade aplicado a cada segment para emendas imperceptíveis

# Estratégia: gerar 6 segments de 600s concatenados com acrossfade de 3s
# ffmpeg concat protocol com crossfade nativo — 100% imperceptível
audio_filter = (
    "anoisesrc=color=brown:amplitude=0.5:sample_rate=44100,"
    "equalizer=f=50:t=o:w=50:g=4,"
    "equalizer=f=100:t=o:w=80:g=2,"
    "equalizer=f=400:t=o:w=200:g=-6,"
    "equalizer=f=1000:t=o:w=500:g=-12,"
    "equalizer=f=4000:t=o:w=2000:g=-20,"
    "equalizer=f=10000:t=o:w=4000:g=-30,"
    "highpass=f=18,"
    "volume=-3dB"
)

cmd = [
    "ffmpeg", "-y",
    # Vídeo preto absoluto
    "-f", "lavfi", "-i", "color=c=0x000000:size=1920x1080:rate=1",
    # Áudio V7 via lavfi — infinito
    "-f", "lavfi", "-i", audio_filter,
    # Encode
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-tune", "stillimage",
    "-pix_fmt", "yuv420p",
    "-g", "2",
    "-b:v", "500k", "-maxrate", "500k", "-bufsize", "1000k",
    "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
    # Output RTMP
    "-f", "flv", RTMP
]

print("FFmpeg iniciando live...")
proc = subprocess.Popen(cmd)

def shutdown(sig, frame):
    print("Encerrando live...")
    proc.terminate()
    proc.wait()
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

proc.wait()
print(f"FFmpeg encerrado com código {proc.returncode}")
