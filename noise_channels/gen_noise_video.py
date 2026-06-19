#!/usr/bin/env python3
"""
Gerador de vídeo 10h ruído + tela preta
Uso: python3 gen_noise_video.py --canal dbn --duracao 36000
"""
import subprocess, argparse, os

CANAIS = {
    "dbn":      {"color": "brownian", "cor_hex": "0x1A0800", "titulo": "Deep Brown Noise | ADHD Focus Sleep"},
    "wnv":      {"color": "white",    "cor_hex": "0x000000", "titulo": "White Noise | Sleep Fast Study"},
    "adhd":     {"color": "brownian", "cor_hex": "0x001A1F", "titulo": "ADHD Focus Brown Noise | Hyperfocus"},
    "tinnitus": {"color": "pink",     "cor_hex": "0x000A1A", "titulo": "Tinnitus Relief | Pink White Noise"},
    "bsn":      {"color": "white",    "cor_hex": "0x00001A", "titulo": "Baby Sleep | White Noise Newborn"},
    "pink":     {"color": "pink",     "cor_hex": "0x1A0015", "titulo": "Pure Pink Noise | Deep Sleep Science"},
}

def gerar_video(canal, duracao=36000, output=None):
    info = CANAIS[canal]
    if not output:
        output = f"{canal}_{duracao//3600}h_noise.mp4"
    
    cor = info["cor_hex"]
    color_noise = info["color"]
    
    # ffmpeg command
    # -t duracao = duração em segundos (36000 = 10h)
    # anoisesrc = gerar ruído
    # color + size = tela preta/colorida 1920x1080
    # -crf 28 = qualidade ok para upload (menor arquivo)
    # -preset veryfast = encoding rápido
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=color={cor}:size=1920x1080:rate=30:duration={duracao}",
        "-f", "lavfi", 
        "-i", f"anoisesrc=color={color_noise}:amplitude=0.15:duration={duracao}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-t", str(duracao),
        "-movflags", "+faststart",
        output
    ]
    
    print(f"Gerando: {output}")
    print(f"Canal: {info['titulo']}")
    print(f"Duração: {duracao//3600}h ({duracao}s)")
    print(f"Ruído: {color_noise}")
    print(f"Cor de fundo: {cor}")
    print(f"Tamanho estimado: {duracao//3600 * 250}MB")
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        size = os.path.getsize(output) / (1024*1024*1024)
        print(f"✅ Gerado: {output} ({size:.1f}GB)")
    else:
        print(f"❌ Erro: {result.stderr[-500:]}")
    return result.returncode

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--canal", choices=list(CANAIS.keys()), required=True)
    parser.add_argument("--duracao", type=int, default=36000)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    gerar_video(args.canal, args.duracao, args.output)
