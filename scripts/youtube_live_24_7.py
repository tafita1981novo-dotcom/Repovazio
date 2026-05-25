#!/usr/bin/env python3
"""
youtube_live_24_7.py — Stream 24/7 Psicologia Dark
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pipeline: Groq gera insight → Pollinations gera frame → FFmpeg → RTMP YouTube
Identidade: Daniela Coelho · pesquisadora de comportamento humano
PROIBIDO: psicóloga/psicólogo até jan/2027
"""
import os, time, subprocess, pathlib, requests, textwrap, sys
from datetime import datetime

STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY","")
GROQ_KEY   = os.getenv("GROQ_API_KEY","")
RTMP_URL   = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
TMP        = pathlib.Path("/tmp/live"); TMP.mkdir(exist_ok=True)

# Validações
if not STREAM_KEY:
    print("ERRO: YOUTUBE_STREAM_KEY nao configurado")
    print("Obter em: studio.youtube.com -> Criar -> Live -> Chave de stream")
    print("Adicionar em: github.com/tafita81/Repovazio/settings/secrets/actions")
    sys.exit(1)

TEMAS = [
    ("Narcisismo Encoberto",   "sinais que voce ignora em relacionamentos toxicos"),
    ("Apego Ansioso",          "por que voce escolhe quem te machuca"),
    ("Sono e Cortisol",        "por que voce acorda as 3h da manha"),
    ("Burnout Invisivel",      "esgotamento antes do colapso que ninguem viu chegar"),
    ("Gaslighting",            "quando fazem voce duvidar da sua propria realidade"),
    ("Fronteiras Saudaveis",   "como dizer nao sem se sentir culpada"),
    ("Trauma de Apego",        "como a infancia ainda controla seus relacionamentos"),
    ("Autocompaixao",          "o que Harvard descobriu sobre se perdoar"),
    ("Dopamina e Redes Sociais","por que voce nao consegue parar de verificar o celular"),
    ("Solidao Moderna",        "por que nos sentimos sozinhos mesmo conectados"),
]

CORES = {"bg":"#06060F","texto":"#F1F5F9","roxo":"#7C3AED","vermelho":"#E11D48"}

def groq_insight(tema, subtema):
    if not GROQ_KEY: return f"{tema}: {subtema}. Pesquisa: van der Kolk, 2014."
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":
                    f"Voce e Daniela Coelho, pesquisadora de comportamento humano.\n"
                    f"Tema: {tema} — {subtema}\n"
                    f"Gere 3 frases impactantes para live de psicologia dark.\n"
                    f"Cite 1 pesquisador real (Harvard/PubMed/Berkeley).\n"
                    f"PROIBIDO: psicologa/psicologo. Max 60 palavras total."}],
                  "max_tokens":80,"temperature":0.85},
            timeout=12, verify=False)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return f"{tema}: {subtema}"

def pollinations_frame(tema, idx):
    seed = 9001 + idx * 77
    prompt = (
        f"masterpiece, kawaii chibi anime researcher woman, dark background #{CORES['bg'][1:]}, "
        f"purple glow, dramatic lighting, psychology theme, minimal, no text "
        f"### watermark, text, nsfw, blurry"
    )
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    url += f"?seed={seed}&width=1280&height=720&nologo=true"
    try:
        r = requests.get(url, timeout=30, verify=False)
        if r.status_code == 200 and len(r.content) > 5000:
            p = TMP / f"frame_{idx}.jpg"
            p.write_bytes(r.content)
            return str(p)
    except: pass
    return None

def criar_frame_texto(texto, idx):
    """Cria frame via FFmpeg com texto sobreposto (fallback)"""
    output = str(TMP / f"frame_txt_{idx}.jpg")
    lines  = textwrap.wrap(texto, 40)[:4]
    y      = 280
    overlay_parts = []
    for line in lines:
        overlay_parts.append(
            f"drawtext=text='{line}':fontsize=28:fontcolor=white:x=(w-text_w)/2:y={y}"
        )
        y += 45
    vf = ",".join(overlay_parts) if overlay_parts else "null"
    cmd = [
        "ffmpeg","-y",
        "-f","lavfi","-i",f"color=c={CORES['bg'][1:]}:size=1280x720:rate=1",
        "-vf", vf,
        "-frames:v","1","-q:v","2",output
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=15)
    return output if r.returncode == 0 else None

def stream_frame(frame_path, duracao_seg=45):
    """Transmite um frame via RTMP por N segundos"""
    cmd = [
        "ffmpeg","-y","-re",
        "-loop","1","-i", frame_path,          # frame imagem
        "-f","lavfi","-i","anullsrc=r=44100:cl=stereo",  # áudio silencioso
        "-c:v","libx264","-preset","ultrafast","-tune","zerolatency",
        "-b:v","2500k","-maxrate","2500k","-bufsize","5000k",
        "-pix_fmt","yuv420p","-r","30",
        "-c:a","aac","-b:a","128k","-ar","44100",
        "-t", str(duracao_seg),
        "-f","flv", RTMP_URL
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=duracao_seg+30)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return True  # normal

def run():
    print(f"=== YOUTUBE LIVE 24/7 — psicologia.doc ===")
    print(f"Canal: UCyCkIpsVgME9yCj_oXJFheA (@psidanielacoelho)")
    print(f"RTMP: {RTMP_URL[:50]}...")
    print(f"Inicio: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")

    import urllib3; urllib3.disable_warnings()
    idx = 0
    while True:
        tema, subtema = TEMAS[idx % len(TEMAS)]
        print(f"  [{idx+1}] {tema} ({datetime.now().strftime('%H:%M')})")

        insight = groq_insight(tema, subtema)
        print(f"     Insight: {insight[:60]}...")

        frame = pollinations_frame(tema, idx)
        if not frame:
            print(f"     Pollinations falhou, usando frame texto")
            frame = criar_frame_texto(insight, idx)
        if not frame:
            print(f"     Frame falhou, pulando")
            idx += 1; time.sleep(5); continue

        print(f"     Transmitindo 45s via RTMP...")
        ok = stream_frame(frame, 45)
        print(f"     {'OK' if ok else 'Erro RTMP'}")
        idx += 1
        time.sleep(2)

if __name__=="__main__": run()
