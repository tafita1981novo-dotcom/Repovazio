#!/usr/bin/env python3
import os, sys, signal, time, random
import numpy as np
import subprocess

SR      = 44100
CHUNK_N = SR * 600   # 10 min por bloco
FADE_N  = SR * 5     # 5s crossfade

KEY = os.environ.get("DEEP_BROWN_STREAM_KEY","")
if not KEY:
    print("ERRO: DEEP_BROWN_STREAM_KEY nao definida"); sys.exit(1)

RTMP = f"rtmp://a.rtmp.youtube.com/live2/{KEY}"

def gerar_v7(seed, n):
    np.random.seed(seed)
    white   = np.random.randn(n)
    f_white = np.fft.rfft(white)
    freqs   = np.fft.rfftfreq(n, d=1.0/SR); freqs[0] = 1
    f_brown  = f_white / freqs
    boost    = np.ones_like(freqs)
    boost   += 1.8 * np.exp(-((freqs - 50)**2) / (2 * 25**2))
    shelf    = np.ones_like(freqs)
    shelf[freqs > 300] = (300.0 / freqs[freqs > 300]) ** 2.2
    f_final  = f_brown * boost * shelf
    f_final[freqs < 18] = 0
    brown = np.fft.irfft(f_final, n=n)
    brown = brown / np.max(np.abs(brown)) * 0.707
    return brown.astype(np.float32)

def crossfade(a, b, fade_n):
    t      = np.linspace(0.0, 1.0, fade_n)
    fade_o = (1.0 - t) ** 2
    fade_i = t ** 2
    result = np.copy(a)
    result[-fade_n:] = a[-fade_n:] * fade_o + b[:fade_n] * fade_i
    return np.concatenate([result, b[fade_n:]])

def to_pcm(audio):
    return (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16).tobytes()

CMD = [
    "ffmpeg", "-y",
    "-f","s16le", "-ar",str(SR), "-ac","1", "-i","pipe:0",
    "-f","lavfi", "-i","color=c=0x000000:size=1920x1080:rate=1",
    "-c:v","libx264", "-preset","ultrafast", "-tune","stillimage",
    "-pix_fmt","yuv420p", "-g","2",
    "-b:v","500k", "-maxrate","500k", "-bufsize","1000k",
    "-c:a","aac", "-b:a","192k", "-ar",str(SR),
    "-f","flv", RTMP
]

BASE = random.randint(100000, 999999)
print(f"DBN Live 24/7 | seed={BASE}")
print(f"Gerando primeiro bloco antes de conectar...")

# Pre-gerar primeiro bloco ANTES de abrir ffmpeg
# Evita timeout do systemd durante geração
atual = gerar_v7(BASE, CHUNK_N)
print(f"Bloco 1 gerado. Conectando RTMP...")

proc = None

def shutdown(sig, frame):
    print("Encerrando..."); 
    try: proc.stdin.close(); proc.terminate(); proc.wait()
    except: pass
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT,  shutdown)

tentativa = 0
bloco     = 1

while True:
    tentativa += 1
    print(f"[tentativa {tentativa}] Conectando RTMP...")
    proc = subprocess.Popen(CMD, stdin=subprocess.PIPE)

    try:
        # Enviar bloco atual
        pcm = to_pcm(atual)
        for i in range(0, len(pcm), 32768):
            proc.stdin.write(pcm[i:i+32768])

        while True:
            bloco += 1
            print(f"Gerando bloco {bloco}...")
            prox  = gerar_v7(BASE + bloco, CHUNK_N)
            audio = crossfade(atual, prox, FADE_N)
            pcm   = to_pcm(audio)
            for i in range(0, len(pcm), 32768):
                proc.stdin.write(pcm[i:i+32768])
            atual = prox
            print(f"Bloco {bloco} enviado — {bloco*10}min no ar")

    except (BrokenPipeError, OSError):
        try: proc.wait(timeout=5)
        except: proc.kill()
        print("Stream caiu — reiniciando em 15s...")
        time.sleep(15)
