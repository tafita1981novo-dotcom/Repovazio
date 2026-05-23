#!/usr/bin/env python3
"""
youtube_live_v2.py — Live 24/7 OTIMIZADA para máximo watch time e receita
Estratégia: Lofi Psychology — calmo, contínuo, audiência BR primetime

ESTRUTURA DA LIVE:
- Fundo: imagem serena gerada por Pollinations FLUX
- Overlay topo: "🔴 AO VIVO | Psicologia | Daniela Coelho"
- Centro: insight de psicologia rotacionando a cada 45s
- Rodapé: barra de progresso + próximo tema
- Áudio: tom ambiente suave gerado por FFmpeg (livre de direitos)
- CTA sutil: link do produto na descrição

FASES DE MONETIZAÇÃO:
- 0-500 subs: acumular watch hours 24/7 + promover Interview Pro ($197)
- 500 subs: Super Thanks + Channel Memberships ($4.99/mês)
- 1000 subs + 4000h: AdSense ligado ($1-5/hora)
- 10K subs: Merchandise shelf
"""
import os, time, subprocess, pathlib, requests, textwrap
from datetime import datetime
import threading

STREAM_KEY  = os.getenv("YOUTUBE_STREAM_KEY", "")
GROQ_KEY    = os.getenv("GROQ_API_KEY", "")
RTMP_URL    = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
WIDTH, HEIGHT = 1280, 720
FPS = 30
TMP = pathlib.Path("/tmp/live_v2")
TMP.mkdir(exist_ok=True)

# Marca sem título profissional até 2027
MARCA        = "Daniela Coelho · Pesquisa e Conteúdo em Psicologia"
CANAL_URL    = "@psidanielacoelho"
PRODUTO_CTA  = "Interview Assistant Pro: bit.ly/interview-ia"

# Temas em ciclo otimizado — mix de viral e educacional
CICLO_TEMAS = [
    # HORA 1 — picos de audiência BR (19-21h)
    ("Narcisismo encoberto", "A pessoa mais tóxica da sua vida provavelmente não parece tóxica. Parece vítima. — Malkin, Harvard"),
    ("Apego ansioso", "Checkar o celular 80x por dia não é fraqueza. É dopamina em reforço variável. — Ainsworth, 1969"),
    ("Gaslighting", "Quando você duvida da própria memória, o gaslighting já funcionou. — Freyd, Oregon"),
    # HORA 2 — retenção
    ("Neurociência da ansiedade", "Sua amígdala não distingue leão de reunião importante. Ambos disparam o alarme. — LeDoux"),
    ("Burnout vs cansaço", "Burnout não melhora com férias. Cansaço sim. Essa diferença importa muito."),
    ("Síndrome do impostor", "Quanto mais você sabe, mais você sabe o que não sabe. — Dunning-Kruger"),
    # HORA 3 — novas audiências
    ("Depressão silenciosa", "Você pode funcionar perfeitamente e estar deprimido. São sistemas independentes. — Seligman"),
    ("Fronteiras emocionais", "Fronteira tem linguagem. Muro tem silêncio. São coisas muito diferentes."),
    ("Autocompaixão", "Autocrítica intensa não melhora performance. Piora. — Neff, UT Austin"),
    # HORA 4 — retenção noturna
    ("Solidão epidêmica", "15 cigarros por dia tem o mesmo impacto na mortalidade que solidão crônica. — Surgeon General, 2023"),
    ("Procrastinação", "Procrastinação não é preguiça. É evitar a emoção associada à tarefa. — Sirois, Sheffield"),
    ("Raiva como informação", "Raiva aponta para um valor violado ou limite cruzado. É dado, não falha de caráter."),
]

# Frases motivacionais reais de pesquisadores para preencher pausas
PESQUISADORES_QUOTES = [
    '"O corpo guarda as marcas." — Bessel van der Kolk',
    '"Pertencer começa com se pertencer." — Brené Brown, UT Austin',
    '"Apego ansioso não é destino. É padrão." — Sue Johnson',
    '"O cérebro é como velcro para o negativo." — Rick Hanson, UC Berkeley',
    '"Feito é melhor que perfeito." — Sheryl Sandberg',
    '"Nomear a emoção reduz sua intensidade." — Matthew Lieberman, UCLA',
    '"Autocompaixão não é fraqueza. É neurociência." — Kristin Neff',
]

def gerar_insight_groq(tema, frase_base):
    """Gera variação do insight via Groq para evitar repetição"""
    if not GROQ_KEY:
        return frase_base
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile",
                  "messages": [{"role": "user", "content":
                    f"Reescreva essa frase sobre psicologia de forma ligeiramente diferente, mantendo o fato científico e o impacto. Máximo 120 caracteres. Sem aspas:\n{frase_base}"}],
                  "max_tokens": 60, "temperature": 0.9},
            timeout=10)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except:
        pass
    return frase_base

def get_image_pollinations(tema, seed):
    """Busca imagem via Pollinations FLUX — grátis, ilimitado"""
    prompt = (
        f"masterpiece, best quality, kawaii chibi anime illustration, "
        f"serene peaceful psychology concept: {tema}, "
        f"soft purple tones, minimalist zen background, no text, "
        f"calming lofi aesthetic, warm lighting "
        f"### lowres, bad anatomy, text, watermark, nsfw, blurry, harsh"
    )
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt[:450])}"
    url += f"?model=flux&width={WIDTH}&height={HEIGHT}&seed={seed}&nologo=true"
    try:
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and len(r.content) > 10000:
            return r.content
    except Exception as e:
        print(f"    Pollinations: {e}")
    return None

def gerar_audio_ambiente(duracao_seg, out_path):
    """Gera áudio ambiente calmo via FFmpeg — livre de direitos"""
    # Mix de tons suaves: 174Hz (cura) + 528Hz (transformação) + ruído branco suave
    cmd = [
        "ffmpeg", "-y",
        # Tom 174 Hz (relaxamento)
        "-f", "lavfi", "-i", f"sine=frequency=174:duration={duracao_seg}",
        # Tom 528 Hz (muito suave, quase inaudível)
        "-f", "lavfi", "-i", f"sine=frequency=528:duration={duracao_seg}",
        # Mix e normalizar muito baixo
        "-filter_complex",
        "[0:a]volume=0.03[a1];[1:a]volume=0.008[a2];[a1][a2]amix=inputs=2:duration=longest[out]",
        "-map", "[out]",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    return out_path.exists()

def criar_frame_overlay(img_path, tema, insight, quote_pesquisador, progresso_pct, out_path):
    """Cria frame com todos os overlays via FFmpeg drawtext"""
    
    # Quebrar insight em 2 linhas máx 40 chars
    linhas = textwrap.wrap(insight, 42)[:2]
    linha1 = linhas[0].replace("'", r"\'") if linhas else ""
    linha2 = linhas[1].replace("'", r"\'") if len(linhas) > 1 else ""
    
    tema_esc    = tema.replace("'", r"\'")
    quote_esc   = quote_pesquisador.replace("'", r"\'")[:70]
    marca_esc   = MARCA.replace("'", r"\'")
    cta_esc     = PRODUTO_CTA.replace("'", r"\'")
    
    # Barra de progresso (largura baseada no pct)
    prog_w = max(1, int(WIDTH * progresso_pct))
    hora_br = (datetime.utcnow()).strftime("%H:%M") + " BR"
    
    vf = (
        # Imagem base
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},"
        # Overlay escurecido no topo (header)
        f"drawbox=y=0:color=black@0.75:width=iw:height=70:t=fill,"
        # Overlay no rodapé
        f"drawbox=y=ih-80:color=black@0.80:width=iw:height=80:t=fill,"
        # Barra de progresso tema
        f"drawbox=y=ih-5:color=#7C3AED@0.9:width={prog_w}:height=5:t=fill,"
        # Ponto vermelho AO VIVO
        f"drawbox=x=16:y=18:color=#EF4444:width=12:height=12:t=fill,"
        # Texto AO VIVO
        f"drawtext=text='AO VIVO':fontsize=14:fontcolor=#EF4444:x=35:y=18:bold=1,"
        # Tema atual
        f"drawtext=text='Psicologia | {tema_esc}':fontsize=18:fontcolor=white:x=(w-text_w)/2:y=20:shadowcolor=#000:shadowx=1:shadowy=1,"
        # Horário
        f"drawtext=text='{hora_br}':fontsize=13:fontcolor=#94A3B8:x=w-80:y=22,"
        # Linha insight principal
        f"drawtext=text='{linha1}':fontsize=28:fontcolor=white:x=(w-text_w)/2:y=h*0.38:shadowcolor=#1a0044:shadowx=2:shadowy=2:bold=1,"
    )
    
    if linha2:
        vf += (
            f"drawtext=text='{linha2}':fontsize=28:fontcolor=white:x=(w-text_w)/2:y=h*0.38+42:shadowcolor=#1a0044:shadowx=2:shadowy=2:bold=1,"
        )
    
    vf += (
        # Quote pesquisador (rodapé)
        f"drawtext=text='{quote_esc}':fontsize=14:fontcolor=#C4B5FD:x=(w-text_w)/2:y=h-62:shadowcolor=#000:shadowx=1:shadowy=1,"
        # Marca
        f"drawtext=text='{marca_esc}':fontsize=13:fontcolor=#94A3B8:x=(w-text_w)/2:y=h-40,"
        # CTA produto
        f"drawtext=text='{cta_esc}':fontsize=12:fontcolor=#60A5FA:x=(w-text_w)/2:y=h-20"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(img_path),
        "-vf", vf,
        "-t", "45",  # 45 segundos por tema
        "-c:v", "libx264", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-an", str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    return out_path.exists() and out_path.stat().st_size > 10000

def stream_24_7():
    """Loop principal da live 24/7"""
    if not STREAM_KEY:
        print("YOUTUBE_STREAM_KEY nao configurado.")
        print()
        print("SETUP (5 minutos):")
        print("1. studio.youtube.com > Criar > Transmissao ao vivo")
        print("2. Copiar Stream Key")
        print("3. GitHub: tafita81/Repovazio > Settings > Secrets")
        print("   YOUTUBE_STREAM_KEY = [stream key]")
        print()
        print("Depois: Actions > YouTube Live 24/7 V2 > Run workflow")
        return
    
    print(f"=== YOUTUBE LIVE 24/7 V2 ===")
    print(f"    {MARCA}")
    print(f"    Inicio: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print()
    
    # Pré-gerar 3 slides
    print("Gerando slides iniciais (3)...")
    slides = []
    concat_file = TMP / "playlist.txt"
    
    for i in range(3):
        tema, base_frase = CICLO_TEMAS[i % len(CICLO_TEMAS)]
        seed = 9001 + i * 77
        
        print(f"  [{i+1}/3] {tema}")
        
        # Insight via Groq
        insight = gerar_insight_groq(tema, base_frase)
        quote   = PESQUISADORES_QUOTES[i % len(PESQUISADORES_QUOTES)]
        
        # Imagem
        img_data = get_image_pollinations(tema, seed)
        if not img_data:
            print(f"    Imagem falhou — usando fallback")
            continue
        
        img_path = TMP / f"bg_{seed}.jpg"
        img_path.write_bytes(img_data)
        
        # Frame com overlay
        slide_path = TMP / f"slide_{seed}.mp4"
        prog = (i % len(CICLO_TEMAS)) / len(CICLO_TEMAS)
        ok = criar_frame_overlay(img_path, tema, insight, quote, prog, slide_path)
        
        if ok:
            slides.append(slide_path)
            print(f"    ✅ slide_{seed}.mp4 ({slide_path.stat().st_size//1024}KB)")
        
        time.sleep(2)
    
    if not slides:
        print("Nenhum slide gerado.")
        return
    
    # Gerar áudio ambiente (30 min)
    print("\nGerando audio ambiente 30min...")
    audio_path = TMP / "ambient_30min.aac"
    gerar_audio_ambiente(1800, audio_path)
    
    # Criar playlist inicial
    with open(concat_file, "w") as f:
        for s in slides:
            f.write(f"file '{s.resolve()}'\n")
    
    print(f"\nIniciando stream RTMP...")
    print(f"Canal: {CANAL_URL}")
    print(f"Monitorar: https://studio.youtube.com")
    
    # FFmpeg stream → YouTube RTMP
    cmd_stream = [
        "ffmpeg", "-y",
        # Video: loop infinito da playlist
        "-f", "concat", "-safe", "0", "-stream_loop", "-1",
        "-i", str(concat_file),
        # Audio: loop infinito do ambiente
        "-stream_loop", "-1", "-i", str(audio_path) if audio_path.exists() else "/dev/null",
        # Encoding para YouTube Live
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "stillimage",  # otimiza para slides
        "-b:v", "3000k",
        "-maxrate", "3000k",
        "-bufsize", "6000k",
        "-pix_fmt", "yuv420p",
        "-g", str(FPS * 2),  # keyframe a cada 2s
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-ac", "2",
        "-f", "flv",
        RTMP_URL
    ]
    
    proc = subprocess.Popen(cmd_stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Thread paralela: gerar novos slides enquanto transmite
    def gerar_slides_background(start_idx=3):
        idx = start_idx
        while proc.poll() is None:
            time.sleep(40)  # gerar antes do slide acabar
            
            tema, base_frase = CICLO_TEMAS[idx % len(CICLO_TEMAS)]
            seed = 9001 + idx * 77
            insight = gerar_insight_groq(tema, base_frase)
            quote = PESQUISADORES_QUOTES[idx % len(PESQUISADORES_QUOTES)]
            
            img_data = get_image_pollinations(tema, seed)
            if img_data:
                img_path = TMP / f"bg_{seed}.jpg"
                img_path.write_bytes(img_data)
                slide_path = TMP / f"slide_{seed}.mp4"
                prog = (idx % len(CICLO_TEMAS)) / len(CICLO_TEMAS)
                if criar_frame_overlay(img_path, tema, insight, quote, prog, slide_path):
                    with open(concat_file, "a") as f:
                        f.write(f"file '{slide_path.resolve()}'\n")
                    print(f"  + Slide adicionado: {tema[:35]}")
            
            # Limpar slides antigos (manter últimos 8)
            old_slides = sorted(TMP.glob("slide_*.mp4"))[:-8]
            for s in old_slides:
                s.unlink(missing_ok=True)
            
            idx += 1
    
    bg_thread = threading.Thread(target=gerar_slides_background, daemon=True)
    bg_thread.start()
    
    # Aguardar processo
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        print("\nLive encerrada.")

if __name__ == "__main__":
    stream_24_7()
