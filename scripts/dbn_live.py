#!/usr/bin/env python3
import numpy as np, struct, os, subprocess, random, tempfile, signal, sys

SR    = 44100
BLOCO = SR * 600  # 10 min por bloco
FADE  = SR * 3    # 3 segundos de crossfade — imperceptível ao ouvido

def gerar_bloco(seed, n):
    np.random.seed(seed)
    white   = np.random.randn(n)
    f_white = np.fft.rfft(white)
    freqs   = np.fft.rfftfreq(n, d=1.0/SR); freqs[0]=1
    f_brown  = f_white / freqs
    boost    = np.ones_like(freqs)
    boost   += 1.8 * np.exp(-((freqs-50)**2)/(2*25**2))
    shelving = np.ones_like(freqs)
    shelving[freqs>300] = (300.0/freqs[freqs>300])**2.2
    f_final  = f_brown * boost * shelving
    f_final[freqs<18] = 0
    brown = np.fft.irfft(f_final, n=n)
    return (brown/np.max(np.abs(brown))*0.707).astype(np.float32)

def crossfade(a, b, fade_len):
    """Emenda imperceptível: fade out no fim de A + fade in no inicio de B"""
    result = np.copy(a)
    fade_out = np.linspace(1.0, 0.0, fade_len)**2  # curva quadrática mais suave
    fade_in  = np.linspace(0.0, 1.0, fade_len)**2
    result[-fade_len:] = a[-fade_len:] * fade_out + b[:fade_len] * fade_in
    return np.concatenate([result, b[fade_len:]])

def to_wav(samples_f32, path):
    samples_i16 = (np.clip(samples_f32, -1.0, 1.0) * 32767).astype(np.int16)
    data = samples_i16.tobytes()
    with open(path,'wb') as f:
        f.write(b'RIFF'); f.write(struct.pack('<I',36+len(data)))
        f.write(b'WAVE'); f.write(b'fmt '); f.write(struct.pack('<I',16))
        f.write(struct.pack('<HHIIHH',1,1,SR,SR*2,2,16))
        f.write(b'data'); f.write(struct.pack('<I',len(data))); f.write(data)

RTMP_URL = f"rtmp://a.rtmp.youtube.com/live2/{os.environ['DEEP_BROWN_STREAM_KEY']}"
print(f"RTMP: rtmp://a.rtmp.youtube.com/live2/****")

# Processo ffmpeg persistente — recebe áudio via pipe
ffmpeg_proc = subprocess.Popen([
    'ffmpeg',
    '-f','s16le','-ar',str(SR),'-ac','1','-i','pipe:0',
    '-f','lavfi','-i','color=c=0x000000:size=1920x1080:rate=1',
    '-c:v','libx264','-preset','ultrafast','-tune','stillimage',
    '-pix_fmt','yuv420p','-g','2','-keyint_min','2',
    '-b:v','500k','-maxrate','500k','-bufsize','1000k',
    '-c:a','aac','-b:a','192k','-ar',str(SR),
    '-f','flv', RTMP_URL
], stdin=subprocess.PIPE)

print("FFmpeg iniciado — live começando...")

seed_base = random.randint(100000, 999999)
bloco_atual = gerar_bloco(seed_base, BLOCO)
bloco_num   = 0

def shutdown(sig, frame):
    print("Encerrando...")
    ffmpeg_proc.stdin.close()
    ffmpeg_proc.wait()
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

while True:
    # Gerar próximo bloco com crossfade
    bloco_num += 1
    proximo = gerar_bloco(seed_base + bloco_num, BLOCO)
    
    # Emenda imperceptível — crossfade de 3s
    audio_com_fade = crossfade(bloco_atual, proximo, FADE)
    
    # Enviar para ffmpeg em chunks de 4096 amostras
    audio_i16 = (np.clip(audio_com_fade, -1.0, 1.0) * 32767).astype(np.int16)
    chunk_size = 4096
    for i in range(0, len(audio_i16), chunk_size):
        chunk = audio_i16[i:i+chunk_size].tobytes()
        try:
            ffmpeg_proc.stdin.write(chunk)
        except BrokenPipeError:
            print("FFmpeg encerrado")
            sys.exit(0)
    
    bloco_atual = proximo
    print(f"Bloco {bloco_num} enviado — live {bloco_num*10}min no ar")
