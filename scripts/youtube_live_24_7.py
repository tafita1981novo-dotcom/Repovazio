#!/usr/bin/env python3
"""
youtube_live_24_7.py
Stream 24/7 no YouTube com áudio de psicologia + overlay visual.
Usa FFmpeg (grátis) + YouTube Live RTMP.
Custo: ZERO. Renda: AdSense enquanto roda.

SETUP:
  1. YouTube Studio → Create → Go Live → Stream Key
  2. Adicionar YOUTUBE_STREAM_KEY como GitHub Secret
  3. Executar via GitHub Actions (ubuntu tem FFmpeg)
"""
import os, subprocess, sys, time, random, requests

STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY", "")
GROQ_KEY   = os.getenv("GROQ_API_KEY", "")

# Frases de psicologia para overlay (rolam na tela)
FRASES_PSI = [
    "A autocompaixão é o início de qualquer mudança real — Kristin Neff",
    "Nosso cérebro cria histórias para dar sentido às emoções que sente",
    "Fronteiras saudáveis não afastam pessoas — atraem as certas",
    "O trauma não é o que aconteceu com você — é o que aconteceu dentro de você",
    "Regulação emocional começa com reconhecer, não suprimir",
    "Apego ansioso aprende. Não é destino, é padrão — e padrões mudam",
    "A solidão mais dolorosa é estar rodeado de pessoas e não ser visto",
    "Perfeccionismo é medo de inadequação disfarçado de ambição",
    "Você pode sentir duas coisas contraditórias ao mesmo tempo — isso é humano",
    "Cura não é linear. Dias ruins não apagam o progresso",
]

def gerar_frase_groq():
    if not GROQ_KEY:
        return random.choice(FRASES_PSI)
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile",
                  "messages": [{"role": "user", "content": 
                    "Crie 1 frase profunda sobre psicologia emocional em PT-BR. "
                    "Máximo 90 caracteres. Sem aspas. Inspiracional mas baseada em ciência."}],
                  "max_tokens": 60}, timeout=10)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()[:90]
    except: pass
    return random.choice(FRASES_PSI)

def criar_overlay_frame(frase, output="frame.png"):
    """Cria frame PNG com texto usando FFmpeg"""
    frase_safe = frase.replace("'", "\'").replace('"', '\"').replace(":", "\:")
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "color=c=0x06060F:size=1280x720:rate=1",
        "-vf", (
            f"drawtext=fontcolor=white:fontsize=28:x=(w-tw)/2:y=h-100:"
            f"text='{frase_safe[:80]}',"
            "drawtext=fontcolor=0x7C3AED:fontsize=18:x=50:y=30:"
            "text='ψ Daniela Coelho | Psicologia'"
        ),
        "-frames:v", "1", output
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=30)
    return result.returncode == 0

def stream_loop():
    if not STREAM_KEY:
        print("YOUTUBE_STREAM_KEY não configurado.")
        print("1. YouTube Studio → Go Live → Stream Key")
        print("2. Adicionar como GitHub Secret: YOUTUBE_STREAM_KEY")
        return False
    
    print(f"Iniciando stream 24/7 para YouTube...")
    
    # Stream: áudio silencioso (pode trocar por música) + overlay
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
    
    # Gerar frase atual
    frase = gerar_frase_groq()
    print(f"Overlay: {frase}")
    criar_overlay_frame(frase)
    
    cmd = [
        "ffmpeg", "-y",
        # Input: imagem estática em loop
        "-loop", "1", "-i", "frame.png",
        # Input: áudio silencioso (pode trocar por música real)
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        # Video encode
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
        "-b:v", "800k", "-maxrate", "800k", "-bufsize", "1600k",
        "-g", "50", "-keyint_min", "50",
        "-vf", "scale=1280:720,format=yuv420p",
        # Audio encode
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        # Output RTMP
        "-f", "flv", rtmp_url
    ]
    
    print("Stream iniciado. Ctrl+C para parar.")
    proc = subprocess.Popen(cmd)
    
    # Atualizar overlay a cada 10 minutos
    try:
        while True:
            time.sleep(600)
            nova_frase = gerar_frase_groq()
            print(f"Atualizando overlay: {nova_frase}")
            criar_overlay_frame(nova_frase)
    except KeyboardInterrupt:
        proc.terminate()
        print("Stream encerrado.")
    
    return True

if __name__ == "__main__":
    stream_loop()
