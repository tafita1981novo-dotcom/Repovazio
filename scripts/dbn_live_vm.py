#!/usr/bin/env python3
import os, sys, signal, time, random
import numpy as np
import subprocess

SR      = 44100
CHUNK_N = SR * 30    # 30s por bloco — usa ~6MB RAM
FADE_N  = SR * 2     # 2s crossfade imperceptivel

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
    t = np.linspace(0.0, 1.0, fade_n)
    r = np.copy(a)
    r[-fade_n:] = a[-fade_n:] * (1-t)**2 + b[:fade_n] * t**2
    return np.concatenate([r, b[fade_n:]])

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
print(f"DBN Live 24/7 | seed={BASE} | blocos 30s | ~6MB RAM")

# Pre-gerar primeiro bloco (rapido — 30s leva <1s)
atual = gerar_v7(BASE, CHUNK_N)
print(f"Conectando RTMP...")

proc  = None
bloco = 1

def shutdown(sig, frame):
    print("Encerrando...")
    try: proc.stdin.close(); proc.terminate(); proc.wait()
    except: pass
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT,  shutdown)

tentativa = 0
while True:
    tentativa += 1
    print(f"[tentativa {tentativa}] Conectando...")
    proc = subprocess.Popen(CMD, stdin=subprocess.PIPE)
    try:
        pcm = to_pcm(atual)
        for i in range(0, len(pcm), 32768):
            proc.stdin.write(pcm[i:i+32768])

        while True:
            bloco += 1
            prox  = gerar_v7(BASE + bloco, CHUNK_N)
            audio = crossfade(atual, prox, FADE_N)
            pcm   = to_pcm(audio)
            for i in range(0, len(pcm), 32768):
                proc.stdin.write(pcm[i:i+32768])
            atual = prox
            if bloco % 20 == 0:
                print(f"{bloco*30//60}min no ar")

    except (BrokenPipeError, OSError):
        try: proc.wait(timeout=5)
        except: proc.kill()
        print("Caiu — reiniciando em 15s...")
        time.sleep(15)
    except Exception as e:
        print(f"Erro: {e}")
        try: proc.wait(timeout=5)
        except: proc.kill()
        time.sleep(15)
