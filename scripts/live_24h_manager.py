#!/usr/bin/env python3
"""
live_24h_manager.py — Agenda de live 24h baseada em cases reais de crescimento
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CASES REAIS DE CRESCIMENTO RÁPIDO (referência):

  Meditative Mind (3.2M subs):
    → Fórmula: lives 24/7 frequências + título com keyword alta busca
    → Crescimento: 0→500K em 18 meses apenas com sleep music
    → RPM: $8-20 (wellness keyword = CPM alto)

  Jason Stephenson Sleep Meditation (3M subs):
    → Fórmula: vídeos 8h sono + live contínua noturna
    → Crescimento: 1M em 8 meses com sleep anxiety keyword
    → Estratégia: título começa com "528hz" para aparecer nas buscas

  Greenred Productions (2M subs):
    → Fórmula: binaural beats animados + Focus/Study = retenção alta
    → Estudantes deixam ligado por horas → AdSense por visualização longa
    → Lives 24/7 aparecem como "AO VIVO" no YouTube Search = prioridade

  Solfeggio Frequencies (1M em 6 meses):
    → Frequências 396Hz, 417Hz, 528Hz, 639Hz, 741Hz, 852Hz, 963Hz
    → Live não precisa de conteúdo novo — algoritmo prioriza lives longas
    → Watch time acumulado = boost orgânico de canal

ESTRATÉGIA @psidanielacoelho:
  DIFERENCIAL: combinar frequências + psicologia dark = RPM R$7-14 (2x normal)
  Keyword: "528hz sono" (74K buscas) + "psicologia do sono" (60K buscas)
  Lives aparecem em TEMPO REAL no Google quando alguém busca

AGENDA 24H — HORÁRIOS BRT:

  22h-06h  SONO E FREQUÊNCIAS (8h)   → 528Hz + narração ASMR Daniela
  06h-09h  DESPERTAR E FOCO (3h)     → 40Hz + motivação matinal
  09h-12h  PSICOLOGIA DARK (3h)      → narcisismo, apego, gaslighting
  12h-15h  FOCO E PRODUTIVIDADE (3h) → 40Hz binaural + burnout
  15h-18h  ANSIEDADE E CURA (3h)     → 432Hz + ansiedade, trauma
  18h-21h  PRIME TIME DARK (3h)      → CTA SONO + narcisismo + venda
  21h-22h  RELAXAMENTO (1h)          → 174Hz + emoções + cura

RTMP: rtmp://a.rtmp.youtube.com/live2/{KEY}
BACKUP: rtmp://b.rtmp.youtube.com/live2/{KEY}?backup=1
"""
import os, time, subprocess, pathlib, requests, threading
from datetime import datetime, timezone, timedelta
import urllib3; urllib3.disable_warnings()

STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY","")
GROQ_KEY   = os.getenv("GROQ_API_KEY","")
RTMP_PRI   = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
RTMP_BCK   = f"rtmp://b.rtmp.youtube.com/live2/{STREAM_KEY}?backup=1"
TMP        = pathlib.Path("/tmp/live24h"); TMP.mkdir(exist_ok=True)

# ── AGENDA COMPLETA 24H ──────────────────────────────────────────────────
AGENDA_24H = [
    # (hora_inicio_brt, hora_fim_brt, tipo, tema, hz, titulo_live)
    (22, 6,  "frequencia", "sono_profundo",    528,
     "🌙 Sono Profundo 528Hz — Regeneração Celular | AO VIVO @psidanielacoelho"),
    (6,  9,  "frequencia", "foco_matinal",     40,
     "☀️ Despertar Ativo 40Hz — Ondas Gamma para Foco Total | AO VIVO"),
    (9,  12, "psicologia", "narcisismo",        0,
     "😶 Narcisismo Encoberto — Os 8 Sinais | LIVE Daniela Coelho"),
    (12, 15, "frequencia", "foco_trabalho",    40,
     "🧠 Foco Total 40Hz — Produtividade Científica | AO VIVO"),
    (15, 18, "frequencia", "ansiedade_cura",   432,
     "💜 Ansiedade Zero 432Hz — Regulação do Sistema Nervoso | AO VIVO"),
    (18, 21, "psicologia", "prime_time",        0,
     "🔥 Psicologia Dark — Narcisismo, Apego, Trauma | AGORA @psidanielacoelho"),
    (21, 22, "frequencia", "cura_emocional",   174,
     "🌿 Cura Emocional 174Hz — Alívio do Trauma | AO VIVO"),
]

# Temas de psicologia dark por horário (prime time = mais vendas)
TEMAS_PSICO = {
    "narcisismo": [
        "Você Está Num Relacionamento com um Narcisista Encoberto?",
        "Os 8 Sinais de Narcisismo Encoberto Que Harvard Confirmou",
        "Por Que Você Não Vê o Narcisista — A Ciência Explica",
        "Gaslighting: Como Eles Fazem Você Duvidar de Tudo",
    ],
    "prime_time": [
        "Narcisismo, Apego e Trauma — Tudo Que Ninguém Te Conta | AO VIVO",
        "A Psicologia do Porque Você Fica Em Relacionamentos Ruins | LIVE",
        "Burnout, Ansiedade, Trauma de Apego — Daniela Responde | AO VIVO",
    ],
    "sono_profundo": [
        "Sono Profundo 528Hz + Psicologia — Regeneração Celular | 8H AO VIVO",
        "528Hz Sono Reparador — Cortisol e Sono Explicados | LIVE NOTURNA",
        "Dormir Bem Com Psicologia e 528Hz — Matthew Walker Research | AO VIVO",
    ],
    "ansiedade_cura": [
        "432Hz Ansiedade Zero — Sistema Nervoso em Paz | AO VIVO",
        "Cura da Ansiedade com Frequência e Psicologia | LIVE",
        "432Hz + Teoria Polivagal — Dr. Porges Explica | AO VIVO",
    ],
    "foco_matinal": [
        "40Hz Foco Matinal — Ondas Gamma para Começar o Dia | AO VIVO",
        "Despertar Ativo com Neurociência 40Hz | LIVE MATINAL",
    ],
    "foco_trabalho": [
        "40Hz Foco Total — Estudo e Produtividade | 3H AO VIVO",
        "Gamma 40Hz para Trabalho Profundo | LIVE AFTERNOON",
    ],
    "cura_emocional": [
        "174Hz Cura Emocional — Alívio de Trauma e Estresse | AO VIVO",
        "Frequência 174Hz + Psicologia do Trauma | LIVE NOTURNA",
    ],
}

def hora_brt():
    return (datetime.now(timezone.utc) - timedelta(hours=3)).hour

def bloco_atual():
    h = hora_brt()
    for inicio, fim, tipo, tema, hz, titulo in AGENDA_24H:
        if inicio > fim:  # atravessa meia-noite
            if h >= inicio or h < fim:
                return tipo, tema, hz, titulo
        else:
            if inicio <= h < fim:
                return tipo, tema, hz, titulo
    return "psicologia", "prime_time", 0, "🔥 Psicologia Dark | AO VIVO @psidanielacoelho"

def groq_narrar(tema, hz):
    if not GROQ_KEY: return f"Frequência {hz}Hz. Relaxe. Respire."
    if hz > 0:
        prompt = (
            f"Você é Daniela Coelho, pesquisadora de comportamento humano.\n"
            f"Gere 3 frases ASMR para live 24/7 de frequência {hz}Hz sobre: {tema}\n"
            f"Tom: muito suave, hipnótico, como uma voz guiada de meditação.\n"
            f"Base científica: citar 1 pesquisador real (Walker, Porges, van der Kolk).\n"
            f"PROIBIDO: psicóloga/psicólogo. Max 50 palavras."
        )
    else:
        import random
        titulo_tema = random.choice(TEMAS_PSICO.get(tema, TEMAS_PSICO["prime_time"]))
        prompt = (
            f"Você é Daniela Coelho, pesquisadora de comportamento humano.\n"
            f"Gere 3 frases impactantes para live de psicologia dark sobre: {titulo_tema}\n"
            f"Citar pesquisador Harvard/Berkeley/UCLA. Tom: revelador, dark, empático.\n"
            f"PROIBIDO: psicóloga/psicólogo. Max 50 palavras."
        )
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":80,"temperature":0.85},
            timeout=12, verify=False)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return f"{tema} — baseado em pesquisa científica."

def gerar_binaural_tone(hz, duracao_seg, output):
    """Gera tom binaural puro via FFmpeg"""
    freq_dir = hz + 10  # diferença de 10Hz = efeito binaural
    cmd = [
        "ffmpeg","-y","-f","lavfi",
        "-i",f"sine=frequency={hz}:duration={duracao_seg}",
        "-f","lavfi",
        "-i",f"sine=frequency={freq_dir}:duration={duracao_seg}",
        "-filter_complex","[0:a][1:a]amerge=inputs=2,volume=0.35[out]",
        "-map","[out]","-ar","44100","-b:a","128k",output
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=120)
    return r.returncode == 0

def pollinations_frame(tema, hz, idx):
    """Gera frame visual para a live"""
    estilos = {
        "sono_profundo":  "dark bedroom, moonlight, peaceful blue atmosphere, stars",
        "foco_matinal":   "bright morning light, coffee desk, energetic atmosphere",
        "foco_trabalho":  "modern workspace, purple glow, focus atmosphere",
        "ansiedade_cura": "lavender fields, calm water, healing teal atmosphere",
        "narcisismo":     "dark psychology, dramatic shadows, mirror reflection",
        "prime_time":     "dark psychology, purple red gradient, dramatic lighting",
        "cura_emocional": "forest healing, golden light, peace and calm",
    }
    estilo = estilos.get(tema, "dark psychology peaceful atmosphere")
    hz_txt = f"{hz}hz frequency visualization" if hz > 0 else ""
    prompt = (
        f"masterpiece, kawaii chibi anime researcher woman, {estilo}, "
        f"{hz_txt}, no text, minimal clean ### text, watermark, nsfw"
    )
    seed = 9001 + idx * 77
    url  = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    url += f"?seed={seed}&width=1280&height=720&nologo=true"
    try:
        r = requests.get(url, timeout=30, verify=False)
        if r.status_code == 200 and len(r.content) > 5000:
            p = TMP / f"frame_{tema}_{idx}.jpg"
            p.write_bytes(r.content)
            return str(p)
    except: pass
    return None

def stream_frame_com_audio(frame, rtmp, duracao=60, hz=0):
    """Stream frame com áudio binaural ou silencioso"""
    audio_src = "anullsrc=r=44100:cl=stereo"
    if hz > 0:
        tone_file = str(TMP / f"tone_{hz}.mp3")
        if not pathlib.Path(tone_file).exists():
            gerar_binaural_tone(hz, 300, tone_file)
        if pathlib.Path(tone_file).exists():
            cmd = [
                "ffmpeg","-y","-re",
                "-loop","1","-i",frame,
                "-stream_loop","-1","-i",tone_file,
                "-c:v","libx264","-preset","ultrafast","-tune","zerolatency",
                "-b:v","2500k","-maxrate","2500k","-bufsize","5000k",
                "-pix_fmt","yuv420p","-r","30",
                "-c:a","aac","-b:a","128k","-ar","44100",
                "-t",str(duracao),"-f","flv",rtmp
            ]
            try:
                subprocess.run(cmd, capture_output=True, timeout=duracao+30)
                return True
            except: pass
    # Fallback silencioso
    cmd = [
        "ffmpeg","-y","-re","-loop","1","-i",frame,
        "-f","lavfi","-i",f"{audio_src}",
        "-c:v","libx264","-preset","ultrafast","-tune","zerolatency",
        "-b:v","2500k","-pix_fmt","yuv420p","-r","30",
        "-c:a","aac","-b:a","128k","-ar","44100",
        "-t",str(duracao),"-f","flv",rtmp
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=duracao+30)
        return True
    except: return False

def titulo_atual(titulo_base, tema, hz):
    """Título com keyword de alta busca por horário"""
    h = hora_brt()
    if hz > 0:
        return f"{titulo_base} | 🔴 {datetime.now().strftime('%H:%M')} BRT"
    return titulo_base

def run():
    import sys
    if not STREAM_KEY:
        print("ERRO: YOUTUBE_STREAM_KEY nao configurado")
        sys.exit(1)

    print("=== LIVE 24H MANAGER — @psidanielacoelho ===")
    print("  RTMP Primary: rtmp://a.rtmp.youtube.com/live2/[KEY]")
    print("  RTMP Backup:  rtmp://b.rtmp.youtube.com/live2/[KEY]?backup=1")
    print("  Agenda: Sono 528Hz(22-6) | Foco 40Hz(6-9,12-15) | Psico(9-12,18-21)")
    print()

    idx = 0
    while True:
        tipo, tema, hz, titulo = bloco_atual()
        h_brt = hora_brt()
        titulo_live = titulo_atual(titulo, tema, hz)

        print(f"  {h_brt:02d}h BRT [{tipo.upper()}] {tema} {f'{hz}Hz' if hz else ''}")
        print(f"  Título: {titulo_live[:60]}")

        narr = groq_narrar(tema, hz)
        frame = pollinations_frame(tema, hz, idx)

        if frame:
            # Tenta primary, fallback para backup
            ok = stream_frame_com_audio(frame, RTMP_PRI, 60, hz)
            if not ok:
                print(f"  Primary falhou → backup RTMP")
                stream_frame_com_audio(frame, RTMP_BCK, 60, hz)
        else:
            print(f"  Frame falhou — gerando próximo")

        idx += 1
        time.sleep(2)

if __name__=="__main__": run()
