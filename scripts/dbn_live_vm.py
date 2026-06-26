#!/usr/bin/env python3
"""
DBN Live 24/7 — Som idêntico ao V7 aprovado
Gera áudio via FFT Python (mesmo algoritmo do arquivo aprovado)
e faz pipe direto para ffmpeg → YouTube RTMP
"""
import os, sys, signal, time, random
import numpy as np
import subprocess

SR         = 44100
CHUNK_SECS = 600        # 10 min por chunk
CHUNK_N    = SR * CHUNK_SECS
CROSSFADE  = SR * 3     # 3s crossfade imperceptível

STREAM_KEY = os.environ.get("DEEP_BROWN_STREAM_KEY","")
if not STREAM_KEY:
    print("ERRO: DEEP_BROWN_STREAM_KEY nao definida"); sys.exit(1)

RTMP = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
print(f"DBN Live 24/7 — som V7 identico ao arquivo aprovado")
print(f"RTMP: rtmp://a.rtmp.youtube.com/live2/****")

def gerar_v7(seed, n):
    """Perfil V7 exato via FFT — identico ao arquivo aprovado"""
    np.random.seed(seed)
    white   = np.random.randn(n)
    f_white = np.fft.rfft(white)
    freqs   = np.fft.rfftfreq(n, d=1.0/SR)
    freqs[0]= 1
    f_brown  = f_white / freqs
    boost    = np.ones_like(freqs)
    boost   += 1.8 * np.exp(-((freqs - 50)**2) / (2 * 25**2))
    shelving = np.ones_like(freqs)
    shelving[freqs > 300] = (300.0 / freqs[freqs > 300]) ** 2.2
    f_final  = f_brown * boost * shelving
    f_final[freqs < 18] = 0
    brown = np.fft.irfft(f_final, n=n)
    return (brown / np.max(np.abs(brown)) * 0.707).astype(np.float32)

def crossfade(a, b, fade_n):
    """Emenda imperceptível entre blocos"""
    fade_out = np.linspace(1.0, 0.0, fade_n) ** 2
    fade_in  = np.linspace(0.0, 1.0, fade_n) ** 2
    joined = np.copy(a)
    joined[-fade_n:] = a[-fade_n:] * fade_out + b[:fade_n] * fade_in
    return np.concatenate([joined, b[fade_n:]])

def to_i16(samples_f32):
    return (np.clip(samples_f32, -1.0, 1.0) * 32767).astype(np.int16).tobytes()

# FFmpeg — recebe PCM s16le mono via stdin
ffmpeg_cmd = [
    "ffmpeg", "-y",
    # Audio pipe
    "-f","s16le", "-ar",str(SR), "-ac","1", "-i","pipe:0",
    # Video preto absoluto
    "-f","lavfi", "-i","color=c=0x000000:size=1920x1080:rate=1",
    # Encode video
    "-c:v","libx264", "-preset","ultrafast", "-tune","stillimage",
    "-pix_fmt","yuv420p", "-g","2",
    "-b:v","500k", "-maxrate","500k", "-bufsize","1000k",
    # Encode audio
    "-c:a","aac", "-b:a","192k", "-ar",str(SR),
    # Output
    "-f","flv", RTMP
]

BASE_SEED = random.randint(100000, 999999)
print(f"Seed base: {BASE_SEED}")

def shutdown(sig, frame):
    print("\nEncerrando live...")
    try: proc.stdin.close()
    except: pass
    try: proc.terminate(); proc.wait()
    except: pass
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT,  shutdown)

tentativa = 0
while True:
    tentativa += 1
    print(f"[tentativa {tentativa}] Iniciando ffmpeg...")

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    try:
        # Pré-gerar primeiro bloco
        bloco_atual = gerar_v7(BASE_SEED, CHUNK_N)
        bloco_num   = 0

        while True:
            bloco_num += 1

            # Gerar próximo bloco em paralelo
            proximo = gerar_v7(BASE_SEED + bloco_num, CHUNK_N)

            # Crossfade imperceptível
            audio = crossfade(bloco_atual, proximo, CROSSFADE)
            audio_i16 = to_i16(audio)

            # Enviar para ffmpeg em chunks de 8192 amostras
            CHUNK = 8192 * 2  # bytes
            for offset in range(0, len(audio_i16), CHUNK):
                proc.stdin.write(audio_i16[offset:offset+CHUNK])

            bloco_atual = proximo
            print(f"  Bloco {bloco_num} — {bloco_num * CHUNK_SECS // 60}min no ar")

    except (BrokenPipeError, OSError):
        print(f"Stream caiu — reiniciando em 10s...")
        try: proc.wait()
        except: pass
        time.sleep(10)
