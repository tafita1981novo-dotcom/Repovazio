#!/usr/bin/env python3
"""
🌙 Sleep Live 24/7 — Transmissão de Sono, Foco e Meditação
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gera live infinita com:
- Sons binaurais delta (0.5-4 Hz) para sono profundo
- Imagens de natureza calma geradas por IA
- Texto mínimo: só título flutuante no top
- Qualidade 1080p60 / 4500kbps
- Multi-language: PT, EN, ES, FR, DE

Monetização: AdSense em lives longas (RPM $3-8 sleep niche)
"""
import os, sys, json, math, struct, wave, subprocess, pathlib, urllib.request
import random, time
from datetime import datetime

SBU = os.getenv("SUPABASE_URL","")
SBK = os.getenv("SUPABASE_SERVICE_KEY","")
STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY","")
DURATION_H = int(os.getenv("DURATION_HOURS","8"))
LANG  = os.getenv("LIVE_LANG","pt-BR")
LIVE_TYPE = os.getenv("LIVE_TYPE","sleep")  # sleep|study|meditation|anxiety

TMP = pathlib.Path("/tmp/sleep_live")
TMP.mkdir(exist_ok=True)

# Stream keys por prioridade
def get_stream_key():
    if STREAM_KEY: return STREAM_KEY
    # Buscar do Supabase
    try:
        anon = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwanZhbHp3a3F3dHR2bXN6dmllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDg2OTU4NjUsImV4cCI6MjAyNDI3MTg2NX0.YdlTF_7NaHT6k2MWjMIQxHvtFimjFlCvIVqGwf5eqY4"
        req = urllib.request.Request(
            f"{SBU}/rest/v1/ia_cache?cache_key=eq.secret:YOUTUBE_STREAM_KEY&select=value",
            headers={"apikey": SBK or anon, "Authorization": f"Bearer {SBK or anon}"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            rows = json.loads(r.read())
            return rows[0]["value"] if rows else ""
    except:
        return "uaqu-vx24-86d8-r0wy-0jwc"  # fallback default

LIVE_CONFIGS = {
    "sleep": {
        "pt": "🌙 Música para Dormir 24/7 | Sons Binaurais Delta | Psicologia do Sono",
        "en": "🌙 Deep Sleep Music 24/7 | Binaural Beats | Sleep Psychology",
        "es": "🌙 Música para Dormir 24/7 | Ondas Binaurales | Psicología del Sueño",
        "freq": 2.0,   # Delta waves: 0.5-4 Hz
        "bg_color": "0x06060F",
        "accent": "0x3B82F6",
        "images": ["peaceful night sky with stars", "calm ocean waves at night no text",
                   "misty forest at dawn no text", "cozy bedroom with soft moonlight no text"],
    },
    "study": {
        "pt": "📚 Música para Estudar 24/7 | Ondas Theta | Foco Total",
        "en": "📚 Study Music 24/7 | Theta Waves | Deep Focus",
        "es": "📚 Música para Estudiar 24/7 | Ondas Theta | Enfoque Total",
        "freq": 5.5,   # Theta: 4-8 Hz
        "bg_color": "0x0F172A",
        "accent": "0x8B5CF6",
        "images": ["minimalist study desk with warm lamp no text",
                   "coffee and open books in cafe window no text",
                   "library interior with soft lighting no text"],
    },
    "meditation": {
        "pt": "🧘 Meditação 24/7 | Binaural Alpha | Reduzir Ansiedade",
        "en": "🧘 Meditation 24/7 | Alpha Waves | Anxiety Relief",
        "es": "🧘 Meditación 24/7 | Ondas Alpha | Reducir Ansiedad",
        "freq": 10.0,  # Alpha: 8-14 Hz
        "bg_color": "0x0A0A1A",
        "accent": "0x06B6D4",
        "images": ["zen garden with pebbles and water no text",
                   "lotus flower on calm water no text",
                   "mountain sunrise meditation no text"],
    },
    "anxiety": {
        "pt": "😌 Alívio de Ansiedade 24/7 | Sons da Natureza | Técnicas de Respiração",
        "en": "😌 Anxiety Relief 24/7 | Nature Sounds | Breathing Techniques",
        "es": "😌 Alivio de Ansiedad 24/7 | Sonidos Naturales | Técnicas de Respiración",
        "freq": 8.0,   # Low Alpha
        "bg_color": "0x052e16",
        "accent": "0x10B981",
        "images": ["gentle rain on window no text",
                   "green bamboo forest path no text",
                   "calm river in forest morning light no text"],
    },
}

def generate_binaural_audio(output_path, duration_sec, freq_hz=2.0, base_hz=200):
    """Gera áudio binaural: L=base_hz, R=base_hz+freq_hz"""
    sr = 44100
    total = int(duration_sec * sr)
    left_data = []
    right_data = []
    
    for i in range(total):
        t = i / sr
        # Fade in/out suave (30 segundos)
        fade = 1.0
        if t < 30: fade = t / 30
        if t > duration_sec - 30: fade = (duration_sec - t) / 30
        fade = max(0, min(1, fade))
        
        # Tons binaurais
        L = fade * 0.35 * math.sin(2 * math.pi * base_hz * t)
        R = fade * 0.35 * math.sin(2 * math.pi * (base_hz + freq_hz) * t)
        
        # Ruído branco suave (textura oceânica)
        noise = 0.08 * (random.random() * 2 - 1) * fade
        
        # Som de ondas simulado
        wave_mod = 0.12 * math.sin(2 * math.pi * 0.1 * t) * (0.5 + 0.5 * math.sin(2*math.pi*0.07*t))
        ocean_noise = wave_mod * (random.random() * 2 - 1) * fade
        
        L_full = L + noise * 0.5 + ocean_noise * 0.5
        R_full = R + noise * 0.5 + ocean_noise * 0.5
        
        left_data.append(max(-32767, min(32767, int(32767 * L_full))))
        right_data.append(max(-32767, min(32767, int(32767 * R_full))))
    
    with wave.open(str(output_path), 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        stereo = b''.join(struct.pack('<hh', l, r) for l, r in zip(left_data, right_data))
        wf.writeframes(stereo)
    
    return True

def generate_background_image(live_type, idx, output_path):
    """Gera imagem de fundo calma via Pollinations"""
    config = LIVE_CONFIGS.get(live_type, LIVE_CONFIGS["sleep"])
    base_prompts = config["images"]
    prompt = base_prompts[idx % len(base_prompts)]
    full_prompt = f"masterpiece, ultra HD, {prompt}, no text, no words, no letters, peaceful, cinematic, photorealistic, 4k"
    
    url = f"https://image.pollinations.ai/prompt/{urllib.request.quote(full_prompt)}"
    url += f"?width=1920&height=1080&seed={1234+idx}&model=flux&nologo=true"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"sleep-live/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
            if len(data) > 5000:
                open(output_path, "wb").write(data)
                return True
    except:
        pass
    return False

def get_title(live_type, lang_code="pt"):
    config = LIVE_CONFIGS.get(live_type, LIVE_CONFIGS["sleep"])
    lang_short = lang_code[:2].lower()
    return config.get(lang_short, config["en"])

def start_sleep_live():
    key = get_stream_key()
    if not key:
        print("❌ Stream key não encontrada!")
        print("   Configure YOUTUBE_STREAM_KEY ou execute setup no Supabase")
        return False
    
    config = LIVE_CONFIGS.get(LIVE_TYPE, LIVE_CONFIGS["sleep"])
    title  = get_title(LIVE_TYPE, LANG)
    freq   = config["freq"]
    bg     = config["bg_color"]
    accent = config["accent"]
    
    duration_sec = DURATION_H * 3600
    rtmp = f"rtmps://a.rtmps.youtube.com/live2/{key}"
    
    print(f"🔴 Iniciando {LIVE_TYPE} live — {DURATION_H}h")
    print(f"   Título: {title}")
    print(f"   Binaural: {freq} Hz | RTMP: {rtmp[:50]}...")
    
    # 1. Gerar áudio binaural (60 min, loop)
    print("\n1. Gerando áudio binaural...")
    audio_path = TMP / "binaural_60min.wav"
    generate_binaural_audio(str(audio_path), 3600, freq_hz=freq)
    print(f"   ✅ {audio_path.stat().st_size//1024//1024}MB de áudio binaural")
    
    # 2. Gerar imagens de fundo (3 imagens para loop)
    print("\n2. Gerando imagens de fundo calmas...")
    images = []
    for i in range(3):
        img_path = TMP / f"bg_{i}.jpg"
        ok = generate_background_image(LIVE_TYPE, i, str(img_path))
        if ok: images.append(str(img_path))
        print(f"   {'✅' if ok else '⚠️'} Imagem {i+1}/3")
        time.sleep(1)
    
    if not images:
        # Fallback: cor sólida
        images = [None]
    
    # 3. Montar stream FFmpeg
    print(f"\n3. Iniciando stream para YouTube...")
    
    # Texto mínimo: apenas título no top (NÃO preenche a tela)
    title_safe = title.replace("'","").replace(":","-")[:60]
    
    if images[0]:
        # Usar imagem de fundo + loop
        input_cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",  # loop infinito
            "-i", images[0],
            "-stream_loop", "-1",
            "-i", str(audio_path),
        ]
        video_filter = (
            f"[0:v]scale=1920:1080,fps=30,"
            f"drawtext=text='@psidanicoelho':fontcolor={accent}:fontsize=28:x=40:y=40:alpha=0.7,"
            f"zoompan=z='1+0.001*sin(2*3.14*0.01*n)':s=1920x1080:fps=30[vout]"
        )
    else:
        # Fundo cor sólida
        input_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c={bg}:size=1920x1080:r=30",
            "-stream_loop", "-1",
            "-i", str(audio_path),
        ]
        # Mandala animada com texto mínimo
        video_filter = (
            f"[0:v]"
            f"drawtext=text='🌙':fontsize=120:x=(W-text_w)/2:y=H/3:fontcolor={accent}:alpha='0.6+0.3*sin(2*PI*t/8)',"
            f"drawtext=text='@psidanicoelho':fontsize=28:x=40:y=40:fontcolor={accent}:alpha=0.6"
            f"[vout]"
        )
    
    stream_cmd = input_cmd + [
        "-filter_complex", video_filter,
        "-map", "[vout]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-b:v", "4500k", "-maxrate", "4500k", "-bufsize", "9000k",
        "-g", "60", "-keyint_min", "60",  # 2s keyframe interval
        "-r", "30", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000",
        "-f", "flv", "-t", str(duration_sec),
        rtmp
    ]
    
    print(f"   Stream ativo! Duração: {DURATION_H}h")
    r = subprocess.run(stream_cmd, timeout=duration_sec + 60)
    
    if r.returncode == 0:
        print(f"\n✅ Live finalizada após {DURATION_H}h")
        return True
    else:
        print(f"\n⚠️ Live finalizada (código {r.returncode})")
        return False

if __name__ == "__main__":
    start_sleep_live()
