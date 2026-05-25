#!/usr/bin/env python3
"""
multi_stream_global.py — Múltiplas streams simultâneas 24h globais
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RTMP PRIMARY: rtmp://a.rtmp.youtube.com/live2/{KEY}
RTMP BACKUP:  rtmp://b.rtmp.youtube.com/live2/{KEY}?backup=1

HORÁRIOS GLOBAIS — PRIME TIME POR FUSO:
  USA East   (UTC-5)  → stream 20h ET = 01h UTC next day
  USA West   (UTC-8)  → stream 20h PT = 04h UTC next day
  Brasil     (UTC-3)  → stream 20h BRT = 23h UTC
  UK         (UTC+1)  → stream 20h GMT = 19h UTC
  Alemanha   (UTC+2)  → stream 20h CET = 18h UTC
  Japão      (UTC+9)  → stream 20h JST = 11h UTC
  Austrália  (UTC+10) → stream 20h AEDT = 10h UTC

CANAIS POR IDIOMA (via live_universal.py):
  PT-BR → YOUTUBE_STREAM_KEY      (canal principal)
  EN    → YOUTUBE_STREAM_KEY_EN   (Psychology Frequencies)
  ES    → YOUTUBE_STREAM_KEY_ES   (Psicología Frecuencias)
  DE    → YOUTUBE_STREAM_KEY_DE   (Psychologie Frequenzen)
  JP    → YOUTUBE_STREAM_KEY_JP
  FR    → YOUTUBE_STREAM_KEY_FR

COMO APARECER NO GOOGLE/YAHOO:
  1. Live streams aparecem em resultados de busca em tempo real
  2. Título: keyword principal + número + urgência (ex: "Narcisismo AGORA")
  3. Thumbnail CTR: rosto + expressão + número + cor contrastante
  4. Descrição: primeiras 2 linhas = keyword + CTA antes do fold
  5. Tags: 15 tags, mix amplo + específico + trending
  6. Capítulos: timestamps aumentam tempo de permanência (fator ranking)
  7. Pinned comment: link produto + CTA dentro de 5 minutos do início
"""
import os, time, subprocess, pathlib, threading, requests, textwrap
from datetime import datetime, timezone, timedelta

TMP = pathlib.Path("/tmp/multistream"); TMP.mkdir(exist_ok=True)

# Horários de stream por idioma (hora LOCAL do prime time = 20h)
# Convertidos para UTC
SCHEDULE_UTC = {
    "PT": 23,   # 20h BRT = 23h UTC
    "EN": 1,    # 20h ET = 01h UTC
    "ES": 23,   # 20h BRT/MX (mesma janela)
    "DE": 18,   # 20h CET = 18h UTC
    "JP": 11,   # 20h JST = 11h UTC
    "FR": 19,   # 20h GMT+1 = 19h UTC
}

TEMAS_PT = [
    "Narcisismo Encoberto — Os 8 Sinais Que Você Ignora",
    "Por Que Você Escolhe Quem Te Machuca — Teoria do Apego",
    "Por Que Você Acorda Às 3h — A Ciência do Cortisol",
    "Burnout Invisível — 3 Fases Antes do Colapso",
    "Gaslighting — Quando Fazem Você Duvidar da Sua Realidade",
]

TEMAS_EN = [
    "Covert Narcissist Signs — What Harvard Research Shows",
    "Why You Wake at 3AM — The Cortisol Science",
    "Anxious Attachment — Why You Choose Who Hurts You",
    "Silent Burnout — 3 Stages Before The Crash",
    "Gaslighting — When They Make You Doubt Reality",
]

GROQ_KEY   = os.getenv("GROQ_API_KEY","")
RTMP_BASE  = "rtmp://a.rtmp.youtube.com/live2"
RTMP_BCK   = "rtmp://b.rtmp.youtube.com/live2"

def groq_insight(tema, lang="PT"):
    if not GROQ_KEY: return tema
    lang_prompt = "PT-BR" if lang == "PT" else "English"
    prompt = (
        f"Você é uma pesquisadora de comportamento humano.\n"
        f"Idioma: {lang_prompt} | Tema: {tema}\n"
        f"Gere 3 frases impactantes para live 24h de psicologia dark.\n"
        f"Baseado em pesquisas reais (Harvard, Berkeley, PubMed).\n"
        f"PROIBIDO: psicóloga/psicólogo. Max 60 palavras total."
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
    return tema

def pollinations_frame(tema, idx, lang="PT"):
    seed = 9001 + idx * 77
    prompt = (
        "masterpiece, kawaii chibi anime researcher woman, "
        "dark psychology background, purple glow, dramatic lighting, "
        "no text, minimal clean ### text, watermark, nsfw, blurry"
    )
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    url += f"?seed={seed}&width=1280&height=720&nologo=true"
    try:
        r = requests.get(url, timeout=30, verify=False)
        if r.status_code == 200 and len(r.content) > 5000:
            p = TMP / f"frame_{lang}_{idx}.jpg"
            p.write_bytes(r.content)
            return str(p)
    except: pass
    return None

def criar_frame_texto(texto, idx, lang):
    output = str(TMP / f"frame_txt_{lang}_{idx}.jpg")
    lines = textwrap.wrap(texto[:120], 35)[:3]
    y = 300
    vf_parts = []
    for line in lines:
        vf_parts.append(
            f"drawtext=text='{line}':fontsize=30:fontcolor=white:x=(w-text_w)/2:y={y}"
        )
        y += 50
    vf = ",".join(vf_parts) if vf_parts else "null"
    cmd = ["ffmpeg","-y","-f","lavfi","-i","color=c=06060F:size=1280x720:rate=1",
           "-vf",vf,"-frames:v","1","-q:v","2",output]
    r = subprocess.run(cmd, capture_output=True, timeout=15)
    return output if r.returncode == 0 else None

def stream_frame(frame_path, stream_key, duracao_seg=45, use_backup=False):
    if use_backup:
        rtmp = f"{RTMP_BCK}/{stream_key}?backup=1"
    else:
        rtmp = f"{RTMP_BASE}/{stream_key}"
    cmd = [
        "ffmpeg","-y","-re",
        "-loop","1","-i",frame_path,
        "-f","lavfi","-i","anullsrc=r=44100:cl=stereo",
        "-c:v","libx264","-preset","ultrafast","-tune","zerolatency",
        "-b:v","2500k","-maxrate","2500k","-bufsize","5000k",
        "-pix_fmt","yuv420p","-r","30",
        "-c:a","aac","-b:a","128k","-ar","44100",
        "-t",str(duracao_seg),"-f","flv",rtmp
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=duracao_seg+30)
        return result.returncode == 0
    except: return False

def stream_loop(lang, stream_key, temas, duracao_total_seg=18000):
    """Loop de stream para um idioma — roda em thread separada"""
    import urllib3; urllib3.disable_warnings()
    print(f"  [STREAM {lang}] Iniciando — {duracao_total_seg//3600}h")
    idx = 0
    tempo_inicio = time.time()
    while time.time() - tempo_inicio < duracao_total_seg:
        tema = temas[idx % len(temas)]
        print(f"  [{lang}] Tema: {tema[:40]} ({idx+1})")
        insight = groq_insight(tema, lang)
        frame = pollinations_frame(tema, idx, lang)
        if not frame:
            frame = criar_frame_texto(insight, idx, lang)
        if frame:
            # Tenta primary, cai para backup se falhar
            ok = stream_frame(frame, stream_key, 45, use_backup=False)
            if not ok:
                print(f"  [{lang}] Primary falhou, tentando backup...")
                ok = stream_frame(frame, stream_key, 45, use_backup=True)
        idx += 1
        time.sleep(2)
    print(f"  [STREAM {lang}] Encerrado após {(time.time()-tempo_inicio)//3600:.0f}h")

def run():
    import urllib3; urllib3.disable_warnings()
    print("=== MULTI-STREAM GLOBAL 24h ===")
    print("  Primary:  rtmp://a.rtmp.youtube.com/live2/{KEY}")
    print("  Backup:   rtmp://b.rtmp.youtube.com/live2/{KEY}?backup=1")
    print()

    # Pegar keys dos env vars
    canais = []
    for lang in ["PT","EN","ES","DE","JP","FR"]:
        key_name = f"YOUTUBE_STREAM_KEY_{lang}" if lang != "PT" else "YOUTUBE_STREAM_KEY"
        key = os.getenv(key_name,"")
        if key:
            temas = TEMAS_EN if lang in ["EN","DE","JP","FR"] else TEMAS_PT
            canais.append((lang, key, temas))
            print(f"  Canal {lang}: KEY configurada ✅")
        else:
            print(f"  Canal {lang}: {key_name} ausente — pulando")

    if not canais:
        print("\n  ERRO: Nenhuma YOUTUBE_STREAM_KEY configurada")
        print("  Adicionar em: github.com/tafita81/Repovazio/settings/secrets/actions")
        return

    print(f"\n  Iniciando {len(canais)} stream(s) simultânea(s)...")
    threads = []
    for lang, key, temas in canais:
        t = threading.Thread(target=stream_loop, args=(lang, key, temas, 18000), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(3)  # stagger para não saturar Pollinations

    for t in threads:
        t.join()

if __name__=="__main__": run()
