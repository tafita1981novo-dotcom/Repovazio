#!/usr/bin/env python3
"""
gen_sleep_live.py — Live 24/7 TELA PRETA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
100% GRATUITO:
- Audio binaural delta/theta/alpha gerado por Python puro
- Tela preta absoluta (cor solida 0x06060F)
- Nome do canal sobreposto (texto minimo)
- Stream RTMP para YouTube 24/7
- Tipos: sleep | study | meditation | anxiety
"""
import os, sys, math, struct, wave, subprocess, pathlib, random, time
from datetime import datetime

STREAM_KEY   = os.getenv("YOUTUBE_STREAM_KEY","uaqu-vx24-86d8-r0wy-0jwc")
DURATION_H   = int(os.getenv("DURATION_HOURS","6"))
LIVE_TYPE    = os.getenv("LIVE_TYPE","sleep")
LANG         = os.getenv("LIVE_LANG","pt-BR")

TMP = pathlib.Path("/tmp/sleep_live"); TMP.mkdir(exist_ok=True)

def log(msg): print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)

def ffm():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError: pass
    import shutil
    b=shutil.which("ffmpeg")
    if b: return b
    for p in ["/snap/bin/ffmpeg","/usr/bin/ffmpeg","/usr/local/bin/ffmpeg"]:
        if pathlib.Path(p).exists(): return p
    return "ffmpeg"

# Configurações por tipo
CONFIGS = {
    "sleep": {
        "freq": 2.0,          # Delta: 0.5-4 Hz — sono profundo
        "base": 200,          # Hz base
        "color": "0x06060F",  # Preto quase absoluto
        "accent": "3B82F6",   # Azul suave
        "moon": "0x1e3a5f",   # Azul noturno para gradiente
        "titles": {
            "pt": "Musica para Dormir 8h - Sons Binaurais Delta - Sono Profundo",
            "en": "Sleep Music 8h - Delta Binaural Beats - Deep Sleep",
            "es": "Musica para Dormir 8h - Ondas Binaurales Delta",
        }
    },
    "study": {
        "freq": 5.5,          # Theta: 4-8 Hz — foco e memoria
        "base": 220,
        "color": "0x0F172A",  # Azul escuro
        "accent": "8B5CF6",   # Roxo foco
        "moon": "0x1e1b4b",
        "titles": {
            "pt": "Musica para Estudar 24/7 - Ondas Theta - Foco e Concentracao",
            "en": "Study Music 24/7 - Theta Waves - Deep Focus",
            "es": "Musica para Estudiar 24/7 - Ondas Theta - Foco Total",
        }
    },
    "meditation": {
        "freq": 10.0,         # Alpha: 8-14 Hz — relaxamento
        "base": 180,
        "color": "0x0A0A1A",
        "accent": "06B6D4",   # Ciano meditacao
        "moon": "0x0c4a6e",
        "titles": {
            "pt": "Meditacao 24/7 - Binaural Alpha - Alivio de Ansiedade",
            "en": "Meditation 24/7 - Alpha Waves - Anxiety Relief",
            "es": "Meditacion 24/7 - Ondas Alpha - Reducir Ansiedad",
        }
    },
    "anxiety": {
        "freq": 8.0,          # Low Alpha — ansiedade
        "base": 174,
        "color": "0x052e16",  # Verde escuro natureza
        "accent": "10B981",
        "moon": "0x064e3b",
        "titles": {
            "pt": "Alivio de Ansiedade 24/7 - Sons da Natureza - Relaxamento",
            "en": "Anxiety Relief 24/7 - Nature Sounds - Deep Relaxation",
            "es": "Alivio de Ansiedad 24/7 - Sonidos Naturaleza - Relajacion",
        }
    },
}

def gen_binaural(out_path, dur_sec, freq_hz=2.0, base_hz=200):
    """
    Gera audio binaural em Python puro — 100% gratuito
    L = base_hz, R = base_hz + freq_hz (diferenca = beat binaural)
    + ondas de chuva/oceano simuladas
    """
    log(f"   Gerando {dur_sec//3600}h de audio binaural {freq_hz}Hz...")
    sr = 44100; total = int(dur_sec * sr)
    L_data, R_data = [], []

    for i in range(total):
        t = i / sr
        # Fade suave in/out (60 segundos)
        fade = 1.0
        if t < 60: fade = t / 60
        if t > dur_sec - 60: fade = (dur_sec - t) / 60
        fade = max(0.0, min(1.0, fade))

        # Tom binaural principal
        L = 0.30 * math.sin(2 * math.pi * base_hz * t)
        R = 0.30 * math.sin(2 * math.pi * (base_hz + freq_hz) * t)

        # Ruido branco suave (textura ar)
        noise = 0.06 * (random.random() * 2 - 1)

        # Ondas de oceano simuladas (respiracao ritmica)
        wave1 = 0.10 * math.sin(2 * math.pi * 0.08 * t)
        wave2 = 0.06 * math.sin(2 * math.pi * 0.05 * t + 1.2)
        ocean = (wave1 + wave2) * (random.random() * 2 - 1) * 0.5

        # Chuva leve
        rain = 0.04 * (random.random() * 2 - 1) * abs(math.sin(2*math.pi*0.2*t))

        # Composicao final
        L_full = (L + noise + ocean + rain) * fade
        R_full = (R + noise + ocean + rain) * fade

        L_data.append(max(-32767, min(32767, int(32767 * L_full))))
        R_data.append(max(-32767, min(32767, int(32767 * R_full))))

        # Progress a cada 30min
        if i > 0 and i % (sr * 1800) == 0:
            log(f"   Audio: {i//sr//60}min/{dur_sec//60}min")

    log(f"   Salvando WAV ({total*4/1024/1024:.1f}MB)...")
    with wave.open(str(out_path), 'w') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
        stereo = b"".join(struct.pack('<hh', l, r) for l, r in zip(L_data, R_data))
        wf.writeframes(stereo)
    log(f"   Audio OK: {out_path.stat().st_size//1024//1024}MB")
    return True

def start_live():
    cfg = CONFIGS.get(LIVE_TYPE, CONFIGS["sleep"])
    lang_short = LANG[:2].lower()
    title = cfg["titles"].get(lang_short, cfg["titles"]["pt"])
    freq  = cfg["freq"]
    base  = cfg["base"]
    color = cfg["color"]  # cor de fundo hex

    dur_sec = DURATION_H * 3600
    rtmp = f"rtmps://a.rtmps.youtube.com/live2/{STREAM_KEY}"

    log("="*55)
    log(f"LIVE 24/7 TELA PRETA — {LIVE_TYPE.upper()}")
    log(f"  Titulo: {title[:60]}")
    log(f"  Binaural: {freq}Hz delta | Base: {base}Hz")
    log(f"  Duracao: {DURATION_H}h | Cor: {color}")
    log(f"  RTMP: {rtmp[:50]}...")
    log("="*55)

    # 1. Gerar audio binaural (bloco de 1 hora para nao encher RAM)
    BLOCK_H = 1  # gerar 1h de cada vez e fazer loop
    block_sec = BLOCK_H * 3600
    audio_path = TMP / "binaural_1h.wav"

    log("1. Gerando audio binaural 1h (loop infinito no ffmpeg)...")
    gen_binaural(audio_path, block_sec, freq_hz=freq, base_hz=base)

    # 2. Stream FFmpeg — tela preta + audio binaural em loop
    log("2. Iniciando stream YouTube...")

    ff = ffm()

    # Tela preta absoluta com overlay de texto minimo (nome do canal)
    # Sem imagens, sem animacoes complexas — apenas cor solida
    stream_cmd = [
        ff, "-y",
        # Video: cor solida preta/escura em loop infinito
        "-f", "lavfi", "-i", f"color=c={color}:size=1920x1080:r=1",
        # Audio: WAV binaural em loop infinito
        "-stream_loop", "-1", "-i", str(audio_path),
        # Filtros de video: texto minimo
        "-vf", (
            "drawtext=text='@psidanicoelho':"
            "fontcolor=white:fontsize=24:x=20:y=20:alpha=0.5:"
            "font=DejaVuSans"
        ),
        # Codecs
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-b:v", "1500k", "-maxrate", "2000k", "-bufsize", "4000k",
        "-g", "60", "-keyint_min", "60",
        "-r", "1",  # 1fps para economizar CPU (tela parada)
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "44100",
        # RTMP YouTube
        "-f", "flv", "-t", str(dur_sec),
        rtmp
    ]

    log(f"3. Stream ativo por {DURATION_H}h! Canal @psidanicoelho")
    log(f"   cmd: {' '.join(stream_cmd[:5])}... [omitido para brevidade]")

    r = subprocess.run(stream_cmd, timeout=dur_sec + 120)

    if r.returncode == 0:
        log(f"Live finalizada apos {DURATION_H}h")
        return True
    else:
        log(f"Live encerrada (codigo {r.returncode})")
        return r.returncode in (0, 1)  # 1 = interrupcao normal

if __name__ == "__main__":
    start_live()
