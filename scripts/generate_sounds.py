#!/usr/bin/env python3
"""Gerar áudio para live: APENAS White Noise + Brown Noise (mix 40/60)"""
import numpy as np, struct, os, wave

SR=48000; DUR=10; SAMPLES=SR*DUR

def write_wav(path, data, sr=SR):
    data=np.clip(data,-1,1); pcm=(data*(32767)).astype(np.int16)
    with wave.open(path,'w') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())

# White noise
white = np.random.normal(0,0.3,SAMPLES)
write_wav('/tmp/sound_white_noise.wav', white)
print("✅ white noise")

# Brown noise (integração de white)
brown_raw = np.cumsum(np.random.normal(0,1,SAMPLES))
brown_raw -= brown_raw.mean()
brown = brown_raw / (np.abs(brown_raw).max()+1e-9) * 0.5
write_wav('/tmp/sound_brown_noise.wav', brown)
print("✅ brown noise")

# Mix 40% white + 60% brown
mix = white*0.4 + brown*0.6
mix /= (np.abs(mix).max()+1e-9); mix *= 0.85
write_wav('/tmp/sound_live_mix.wav', mix)
print("✅ live mix (40w+60b)")
print("Sons prontos: white_noise.wav + brown_noise.wav + live_mix.wav")
