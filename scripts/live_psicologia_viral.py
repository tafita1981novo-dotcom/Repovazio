#!/usr/bin/env python3
"""
🔴 LIVE STREAM VIRAL 24/7 — psicologia.doc
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Estratégia baseada nos maiores canais virais de psicologia:
- Conteúdo rotativo de temas virais (narcisismo, ansiedade, trauma)
- Frases de impacto em tela + narração Edge TTS de alta qualidade
- Auto-renovação via Groq: sempre conteúdo novo, nunca repete
- Qualidade broadcast: 1080p H.264, 4500kbps, AAC stereo 48kHz
- Overlay dinâmico: CTAs, emojis, contador de seguidores

CONFIGURAÇÃO DE QUALIDADE PARA LIVE:
- Vídeo: 1080x1920 (Shorts/Vertical), 4500kbps, 30fps
- Áudio: AAC, 192kbps, Stereo, 48000Hz
- RTMP: Protocolo YouTube

TEMAS VIRAIS (psicologia comportamento humano):
1. Narcisismo & Relacionamentos Tóxicos
2. Ansiedade & Saúde Mental
3. Trauma de Infância
4. Manipulação & Gaslighting
5. Apego Emocional
6. Autossabotagem
7. Burnout & Esgotamento
"""
import os, sys, subprocess, time, json, threading, pathlib, random
import urllib.request, urllib.parse, hashlib, re
from datetime import datetime, timezone, timedelta

# ── Config ─────────────────────────────────────
STREAM_KEY  = os.getenv("YOUTUBE_STREAM_KEY", "")
GROQ_KEY    = os.getenv("GROQ_API_KEY", "")
CHANNEL     = "@psidanicoelho"
W, H        = 1080, 1920
FPS         = 30
V_BITRATE   = "4500k"
A_BITRATE   = "192k"
RTMP_URL    = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
TMP         = pathlib.Path("/tmp/live_psi"); TMP.mkdir(exist_ok=True)

# Duração de cada "bloco" de conteúdo (45 segundos = ideal para retenção)
BLOCK_DURATION = 45

# ── Temas virais rotativa ────────────────────────
VIRAL_TOPICS = [
    {
        "theme": "narcisismo",
        "emoji": "🧠",
        "color": "#8B0000",  # Vermelho escuro
        "hook": "Por que o narcisista NUNCA muda?",
        "cta": "👇 Segue para mais psicologia"
    },
    {
        "theme": "ansiedade",
        "emoji": "💭",
        "color": "#1a1a2e",  # Azul escuro
        "hook": "Seu cérebro está mentindo para você",
        "cta": "🔔 Ativa o sininho"
    },
    {
        "theme": "trauma infância",
        "emoji": "❤️",
        "color": "#4a0080",  # Roxo
        "hook": "5 sinais que você cresceu com trauma",
        "cta": "💬 Comenta se identificou"
    },
    {
        "theme": "manipulação",
        "emoji": "⚠️",
        "color": "#2d0a0a",  # Quase preto vermelho
        "hook": "Você está sendo manipulado?",
        "cta": "🔴 Assiste ao vídeo completo"
    },
    {
        "theme": "autossabotagem",
        "emoji": "🔮",
        "color": "#0a1628",  # Azul navy
        "hook": "Por que você se autossabota",
        "cta": "✨ Compartilha com quem precisa"
    },
]

def log(*a): print(f"[{datetime.now().strftime('%H:%M:%S')}]", *a, flush=True)

def groq_chat(prompt, max_tokens=300):
    if not GROQ_KEY: return ""
    try:
        body = json.dumps({
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": 0.9
        }).encode()
        req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",
            data=body, method="POST",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log(f"Groq: {e}")
        return ""

def get_viral_insight(theme):
    """Gera insight viral via Groq — nunca repete"""
    seed = int(time.time()) % 1000
    prompt = f"""Você é Daniela Coelho, pesquisadora de comportamento humano.
    
Gere 1 insight IMPACTANTE e VIRAL sobre {theme} para live stream YouTube.
Formato: 1 frase de impacto (máx 12 palavras) + 2-3 linhas de revelação psicológica.
Tom: científico mas acessível, empático, revelador.
Seed de variação: {seed}
NÃO use: psicóloga, terapeuta, consulte um profissional.
Use: pesquisa mostra, estudos revelam, seu cérebro, mecanismo neural.
RESPONDA APENAS COM O TEXTO, sem títulos ou marcadores."""
    
    result = groq_chat(prompt, 150)
    if not result:
        # Fallback hardcoded
        fallbacks = {
            "narcisismo": "O narcisista não muda porque o cérebro narcísico\ndesenvolveu um mecanismo de defesa impenetrável.\nEstudos mostram: empatia é processada diferente neles.",
            "ansiedade": "Seu cérebro ansioso não consegue distinguir\nentre ameaça real e imaginária.\nIsso era útil para sobrevivência. Hoje, é uma prisão.",
            "trauma infância": "O trauma não fica no passado.\nEle reescreve como seu sistema nervoso\nresponde ao presente.",
            "manipulação": "O manipulador expert usa sua empatia\ncomo arma contra você.\nQuanto mais você sente, mais vulnerável fica.",
            "autossabotagem": "Você não se autossabota por fraqueza.\nÉ porque uma parte sua aprendeu que o fracasso\né mais seguro que o sucesso.",
        }
        return fallbacks.get(theme, f"Estudos revelam: {theme} afeta 1 em cada 3 pessoas.")
    return result

def get_pollinations_image(theme, seed=None):
    """Gera imagem via Pollinations FLUX (gratuito, ilimitado)"""
    if seed is None: seed = int(time.time()) % 9999
    prompt = urllib.parse.quote(
        f"masterpiece, best quality, kawaii chibi anime illustration, {theme}, "
        f"psychology concept, dark atmospheric, purple neon glow, emotional depth, "
        f"cinematic lighting, vertical portrait 9:16 ### text, watermark, nsfw, bad anatomy"
    )
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=1080&height=1920&seed={seed}&nologo=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "psidoc/1.0"})
        with urllib.request.urlopen(req, timeout=45) as r:
            data = r.read()
        if len(data) > 10000:
            p = TMP / f"bg_{seed}.jpg"
            p.write_bytes(data)
            return str(p)
    except Exception as e:
        log(f"  Pollinations: {e}")
    return None

def tts_edge(text, voice="pt-BR-ThalitaMultilingualNeural", speed="+15%"):
    """Edge TTS gratuito ilimitado"""
    try:
        out = TMP / f"tts_{hashlib.md5(text.encode()).hexdigest()[:8]}.mp3"
        if out.exists(): return str(out)
        cmd = ["edge-tts", f"--voice={voice}", f"--rate={speed}", "--text", text[:500], "--write-media", str(out)]
        r = subprocess.run(cmd, capture_output=True, timeout=30)
        if r.returncode == 0 and out.exists():
            return str(out)
    except Exception as e:
        log(f"  TTS: {e}")
    return None

def create_frame_ffmpeg(bg_img, text_lines, emoji, color, duration, out_path, audio_path=None):
    """Cria frame de live stream via FFmpeg com qualidade broadcast"""
    
    # Texto principal formatado com filtros FFmpeg
    lines = text_lines.split('\n')
    
    # Construir filtro de vídeo complexo
    filters = []
    
    # 1. Background: usar imagem ou cor sólida
    if bg_img and pathlib.Path(bg_img).exists():
        video_input = f"-loop 1 -i {bg_img}"
        # Overlay escuro para legibilidade
        filters.append("scale=1080:1920")
        filters.append("colorize=hue=0:saturation=0.3")
        filters.append(f"curves=all='0/0 0.5/0.3 1/0.7'")  # Escurecer
    else:
        video_input = f"-f lavfi -i color={color}:size=1080x1920"
        filters.append("null")
    
    # 2. Ken Burns suave (mais profissional para live)
    filters.append(f"zoompan=z='1.02+0.005*sin(2*PI*t/10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={duration*FPS}:s=1080x1920:fps={FPS}")
    
    # 3. Gradient overlay escuro nas bordas
    filters.append("vignette=PI/4")
    
    vf = ",".join(filters)
    
    # Textos via drawtext
    y_pos = 400
    drawtext_filters = []
    
    # Emoji grande
    drawtext_filters.append(
        f"drawtext=text='{emoji}':fontsize=120:x=(w-text_w)/2:y=280:alpha=1"
    )
    
    # Linha divisória
    drawtext_filters.append(
        "drawbox=x=80:y=440:w=920:h=6:color=white@0.8:t=fill"
    )
    
    # Texto principal
    for i, line in enumerate(lines[:4]):
        line_clean = re.sub(r"[\"'\\]", "", line[:45])
        if not line_clean.strip(): continue
        font_size = 58 if i == 0 else 44
        y = 480 + i * 70
        drawtext_filters.append(
            f"drawtext=text='{line_clean}':fontsize={font_size}:"
            f"fontcolor=white:shadowcolor=black@0.9:shadowx=3:shadowy=3:"
            f"x=(w-text_w)/2:y={y}:line_spacing=8"
        )
    
    # CTA (call to action) fixo no fundo
    drawtext_filters.append(
        "drawbox=x=0:y=1750:w=1080:h=170:color=black@0.7:t=fill"
    )
    drawtext_filters.append(
        f"drawtext=text='🧠 psicologia.doc  |  Daniela Coelho':"
        f"fontsize=38:fontcolor=white@0.9:x=(w-text_w)/2:y=1770"
    )
    drawtext_filters.append(
        f"drawtext=text='🔴 AO VIVO • Ciência do Comportamento':"
        f"fontsize=34:fontcolor=yellow@0.95:x=(w-text_w)/2:y=1815"
    )
    
    # Indicador de live (pulsante via sin)
    drawtext_filters.append(
        f"drawtext=text='● AO VIVO':"
        f"fontsize=42:fontcolor='red@1':x=80:y=100:"
        f"shadowcolor=black:shadowx=2:shadowy=2"
    )
    
    # Timestamp
    drawtext_filters.append(
        f"drawtext=text='%{{localtime\\:%H\\:%M\\:%S}}':"
        f"fontsize=30:fontcolor=white@0.6:x=w-200:y=110"
    )
    
    full_vf = vf + "," + ",".join(drawtext_filters)
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color={color.replace('#','')}:size=1080x1920",
        "-t", str(duration),
        "-vf", full_vf,
        "-c:v", "libx264", "-preset", "fast",
        "-profile:v", "high", "-level", "4.1",
        "-b:v", V_BITRATE, "-maxrate", "5500k", "-bufsize", "11000k",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p"
    ]
    
    if audio_path and pathlib.Path(audio_path).exists():
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color={color.replace('#','')}:size=1080x1920",
            "-i", audio_path,
            "-t", str(duration),
            "-vf", full_vf,
            "-c:v", "libx264", "-preset", "fast",
            "-profile:v", "high", "-level", "4.1",
            "-b:v", V_BITRATE, "-maxrate", "5500k", "-bufsize", "11000k",
            "-r", str(FPS), "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", A_BITRATE, "-ac", "2", "-ar", "48000",
            "-shortest",
            str(out_path)
        ]
    else:
        cmd.extend([
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-c:a", "aac", "-b:a", A_BITRATE,
            "-shortest", str(out_path)
        ])
    
    subprocess.run(cmd, capture_output=True, timeout=90)
    return pathlib.Path(out_path).exists()

def generate_live_segment(topic, segment_idx):
    """Gera um segmento de live com conteúdo viral fresco"""
    log(f"  Gerando segmento {segment_idx}: {topic['theme']}")
    
    # 1. Conteúdo gerado por IA
    insight = get_viral_insight(topic['theme'])
    
    # 2. TTS do insight
    audio = tts_edge(insight)
    
    # 3. Imagem de fundo (async, pode falhar e usar cor sólida)
    seed = segment_idx * 777 + hash(topic['theme']) % 9999
    bg_img = get_pollinations_image(topic['theme'], seed)
    
    # 4. Criar frame
    out = TMP / f"segment_{segment_idx:04d}.mp4"
    ok = create_frame_ffmpeg(
        bg_img=bg_img,
        text_lines=insight,
        emoji=topic['emoji'],
        color=topic['color'],
        duration=BLOCK_DURATION,
        out_path=out,
        audio_path=audio
    )
    
    if ok:
        log(f"  ✅ Segmento {segment_idx} criado ({out.stat().st_size//1024}KB)")
        return str(out)
    else:
        log(f"  ❌ Segmento {segment_idx} falhou")
        return None

def start_rtmp_stream(segment_files, loop=True):
    """Inicia stream RTMP para YouTube com qualidade broadcast"""
    if not STREAM_KEY:
        log("❌ YOUTUBE_STREAM_KEY não configurado!")
        return None
    
    # Criar concat file para loop
    concat = TMP / "stream_list.txt"
    with open(concat, "w") as f:
        for seg in segment_files:
            if pathlib.Path(seg).exists():
                f.write(f"file '{pathlib.Path(seg).resolve()}'\n")
    
    cmd = [
        "ffmpeg", "-y",
        "-re",  # Real-time
        "-stream_loop", "-1" if loop else "0",  # Loop infinito
        "-f", "concat", "-safe", "0", "-i", str(concat),
        # Vídeo broadcast quality para RTMP
        "-c:v", "libx264", "-preset", "veryfast",  # veryfast para stream
        "-profile:v", "high", "-level", "4.1",
        "-b:v", "4500k", "-maxrate", "5500k", "-bufsize", "11000k",
        "-r", "30", "-g", "60",  # GOP = 2s para live
        "-keyint_min", "60",
        "-pix_fmt", "yuv420p",
        # Áudio broadcast
        "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000",
        # RTMP output
        "-f", "flv", RTMP_URL
    ]
    
    log(f"🔴 Iniciando stream → {RTMP_URL[:50]}...")
    return subprocess.Popen(cmd, stderr=subprocess.PIPE)

def main():
    log("=" * 60)
    log("🧠 LIVE STREAM VIRAL 24/7 — psicologia.doc")
    log("=" * 60)
    log(f"Qualidade: {W}x{H} @ {FPS}fps | {V_BITRATE} vídeo | {A_BITRATE} áudio stereo")
    
    if not STREAM_KEY:
        log("❌ Configure YOUTUBE_STREAM_KEY no GitHub Secrets")
        log("   YouTube Studio → Ao vivo → Transmissão ao vivo → Chave de stream")
        sys.exit(1)
    
    DURATION_H = float(os.getenv("HOURS", "6"))
    total_segments = int(DURATION_H * 3600 / BLOCK_DURATION)
    log(f"Duração: {DURATION_H}h | {total_segments} segmentos | {BLOCK_DURATION}s cada")
    
    # Pré-gerar batch inicial de segmentos
    log("\n[PRÉ-GERAÇÃO] Criando banco de segmentos virais...")
    segments = []
    PRE_GENERATE = min(12, total_segments)
    
    for i in range(PRE_GENERATE):
        topic = VIRAL_TOPICS[i % len(VIRAL_TOPICS)]
        seg = generate_live_segment(topic, i)
        if seg:
            segments.append(seg)
        time.sleep(1)
    
    if not segments:
        log("❌ Nenhum segmento gerado — abortando")
        sys.exit(1)
    
    log(f"\n✅ {len(segments)} segmentos prontos. Iniciando stream...")
    
    # Iniciar stream RTMP
    proc = start_rtmp_stream(segments)
    if not proc:
        sys.exit(1)
    
    # Gerar mais segmentos em background enquanto stream roda
    def background_generator():
        for i in range(PRE_GENERATE, total_segments):
            topic = VIRAL_TOPICS[i % len(VIRAL_TOPICS)]
            seg = generate_live_segment(topic, i)
            if seg:
                segments.append(seg)
                # Atualizar concat file com novos segmentos
                concat = TMP / "stream_list.txt"
                with open(concat, "a") as f:
                    f.write(f"file '{pathlib.Path(seg).resolve()}'\n")
            time.sleep(30)  # Gerar 1 novo segmento a cada 30s
    
    gen_thread = threading.Thread(target=background_generator, daemon=True)
    gen_thread.start()
    
    # Aguardar stream terminar
    timeout = int(DURATION_H * 3600) + 300
    start = time.time()
    while proc.poll() is None and (time.time() - start) < timeout:
        time.sleep(10)
        elapsed = time.time() - start
        log(f"⏱  {elapsed/3600:.1f}h de {DURATION_H}h | {len(segments)} segmentos gerados")
    
    if proc.returncode and proc.returncode != 0:
        log(f"❌ Stream terminou com erro: {proc.returncode}")
    else:
        log("✅ Stream finalizado")

if __name__ == "__main__":
    main()
