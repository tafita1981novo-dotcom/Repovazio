#!/usr/bin/env python3
"""
noise_live_24x7.py  —  Gerencia lives 24/7 dos 4 canais Noise com stream key ativa
VM GCP: 34.148.152.96
Uso: python3 noise_live_24x7.py [DBN|ADHD|WNV|TINNITUS|ALL]
"""
import subprocess, sys, os, time, signal, json
from pathlib import Path

CANAIS = {
    "DBN": {
        "mp4": "DBN.mp4",
        "key": "1740-u687-ptt1-9q0a-ar9z",
        "rtmp": "rtmp://a.rtmp.youtube.com/live2/1740-u687-ptt1-9q0a-ar9z",
        "title": "Brown Noise LIVE 24/7 | ADHD Focus & Deep Sleep | No Ads",
        "bitrate_v": "2000k",
        "bitrate_a": "128k",
    },
    "ADHD": {
        "mp4": "ADHD.mp4",
        "key": "gcbd-yey8-yc9e-13gx-5zfx",
        "rtmp": "rtmp://a.rtmp.youtube.com/live2/gcbd-yey8-yc9e-13gx-5zfx",
        "title": "ADHD Focus Noise LIVE 24/7 | Brown Noise Concentration | No Ads",
        "bitrate_v": "2000k",
        "bitrate_a": "128k",
    },
    "WNV": {
        "mp4": "WNV.mp4",
        "key": "39yz-ufuh-79pj-8mze-d9z1",
        "rtmp": "rtmp://a.rtmp.youtube.com/live2/39yz-ufuh-79pj-8mze-d9z1",
        "title": "White Noise LIVE 24/7 | Sleep, Baby & Tinnitus Relief | No Ads",
        "bitrate_v": "2000k",
        "bitrate_a": "128k",
    },
    "TINNITUS": {
        "mp4": "TINNITUS.mp4",
        "key": "5jgp-majw-c2ww-0m3g-a7zx",
        "rtmp": "rtmp://a.rtmp.youtube.com/live2/5jgp-majw-c2ww-0m3g-a7zx",
        "title": "Tinnitus Relief LIVE 24/7 | Pink & White Noise Masking | No Ads",
        "bitrate_v": "1500k",
        "bitrate_a": "128k",
    },
}

BASE_DIR = Path(os.environ.get("NOISE_DIR", "/opt/noise"))

def cmd_live(canal: str) -> list:
    c   = CANAIS[canal]
    mp4 = BASE_DIR / c["mp4"]
    return [
        "ffmpeg",
        "-re", "-stream_loop", "-1",
        "-i", str(mp4),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "stillimage",         # otimizado para tela preta estática
        "-b:v", c["bitrate_v"],
        "-maxrate", c["bitrate_v"],
        "-bufsize", "4000k",
        "-g", "60",                    # keyframe a cada 2s @ 30fps
        "-c:a", "aac",
        "-b:a", c["bitrate_a"],
        "-ar", "44100",
        "-ac", "2",
        "-f", "flv",
        c["rtmp"],
    ]

def iniciar_live(canal: str):
    if canal not in CANAIS:
        print(f"Canal desconhecido: {canal}"); return

    c   = CANAIS[canal]
    mp4 = BASE_DIR / c["mp4"]
    if not mp4.exists():
        print(f"[{canal}] Arquivo não encontrado: {mp4}")
        print(f"  → Baixar de: https://github.com/tafita1981novo-dotcom/Repovazio/releases")
        return

    print(f"[{canal}] Iniciando live 24/7...")
    print(f"  MP4:  {mp4} ({mp4.stat().st_size/1e9:.2f} GB)")
    print(f"  RTMP: {c['rtmp'][:50]}...")
    print(f"  Ctrl+C para parar | use screen/tmux para persistir")

    tentativa = 0
    while True:
        tentativa += 1
        print(f"\n[{canal}] Stream #{tentativa} iniciando...")
        try:
            proc = subprocess.run(cmd_live(canal), check=False)
            if proc.returncode == 0:
                print(f"[{canal}] Stream encerrado normalmente. Reiniciando em 5s...")
            else:
                print(f"[{canal}] ffmpeg saiu com código {proc.returncode}. Reiniciando em 10s...")
                time.sleep(10)
        except KeyboardInterrupt:
            print(f"\n[{canal}] Live encerrada pelo usuário.")
            break
        except Exception as e:
            print(f"[{canal}] Erro: {e}. Reiniciando em 30s...")
            time.sleep(30)
        time.sleep(5)

def iniciar_todos():
    """Inicia todos os 4 canais em paralelo (use apenas em VM com 4+ CPUs)"""
    import threading
    threads = []
    for canal in CANAIS:
        t = threading.Thread(target=iniciar_live, args=(canal,), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(2)  # stagger para não sobrecarregar I/O

    print("\nTodos os 4 streams iniciados. Ctrl+C para parar tudo.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nEncerrando todos os streams...")

if __name__ == "__main__":
    target = sys.argv[1].upper() if len(sys.argv) > 1 else "ALL"
    if target == "ALL":
        iniciar_todos()
    elif target in CANAIS:
        iniciar_live(target)
    else:
        print(f"Uso: python3 noise_live_24x7.py [DBN|ADHD|WNV|TINNITUS|ALL]")
        print(f"Canais disponíveis: {', '.join(CANAIS.keys())}")
