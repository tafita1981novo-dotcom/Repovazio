#!/usr/bin/env python3
"""
live_24h_manager.py — CORRIGIDO v2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VISUAL CORRETO POR BLOCO:

  22h-06h SONO 528Hz:
    → Natureza noturna (lua, estrelas, floresta escura, mar)
    → SEM personagem anime — NUNCA à noite
    → Texto minimalista: "528Hz ✦ Sono Profundo"
    → Onda binaural animada sutil
    → Silêncio + 528Hz puro (como Meditative Mind, Jason Stephenson)

  06h-09h FOCO 40Hz:
    → Natureza diurna (amanhecer, sol, floresta verde)
    → SEM personagem à noite
    → Texto: "40Hz ✦ Foco Total"

  09h-12h PSICOLOGIA (prime tarde):
    → Daniela Coelho aparece aqui — fundo dark roxo/preto
    → Tema: narcisismo, apego, gaslighting

  12h-15h FOCO 40Hz:
    → Workspace moderno, luz suave, verde
    → Texto: "40Hz ✦ Produtividade"

  15h-18h ANSIEDADE 432Hz:
    → Lavanda, natureza calma, azul suave
    → Texto: "432Hz ✦ Ansiedade Zero"

  18h-21h PRIME TIME PSICOLOGIA:
    → Daniela Coelho com gradiente roxo-vermelho
    → CTA máximo: "Comenta SONO"

  21h-22h CURA 174Hz:
    → Floresta, luz dourada, paz
    → Texto: "174Hz ✦ Cura Emocional"

REFERÊNCIAS DE VISUAL (canais que deram certo):
  - Meditative Mind 3.2M: fundo preto + lua + texto branco simples
  - Jason Stephenson 3M: floresta noturna + ondas suaves
  - Greenred 2M: background gradiente + onda animada + número Hz grande
"""
import os, time, subprocess, pathlib, requests
from datetime import datetime, timezone, timedelta
import urllib3; urllib3.disable_warnings()

STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY","")
GROQ_KEY   = os.getenv("GROQ_API_KEY","")
RTMP_PRI   = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
RTMP_BCK   = f"rtmp://b.rtmp.youtube.com/live2/{STREAM_KEY}?backup=1"
TMP        = pathlib.Path("/tmp/live_fix"); TMP.mkdir(exist_ok=True)

# ── PROMPTS VISUAIS CORRETOS ──────────────────────────────────────────────
VISUAIS = {
    "sono_528": {
        # NUNCA anime à noite — natureza escura + lua
        "prompt": (
            "serene moonlit forest at night, dark blue sky, stars reflection on calm lake, "
            "mist over water, sleeping nature, deep peace, cinematic photography, "
            "8k ultra detailed ### text, watermark, people, anime, cartoon, bright"
        ),
        "cor_fundo": "000814",
        "cor_texto": "88CCFF",
        "hz_label": "528 Hz",
        "sublabel": "Sono Profundo ✦ Regeneração Celular",
        "usa_daniela": False,
    },
    "foco_40": {
        # Amanhecer, natureza vibrante
        "prompt": (
            "golden sunrise over mountain valley, morning light rays through forest, "
            "fresh green nature, crisp morning air, energizing atmosphere, "
            "cinematic landscape photography, 8k ### text, watermark, anime, night"
        ),
        "cor_fundo": "0A1A0A",
        "cor_texto": "88FF88",
        "hz_label": "40 Hz",
        "sublabel": "Foco Total ✦ Ondas Gamma",
        "usa_daniela": False,
    },
    "psicologia": {
        # Daniela aparece SÓ aqui — fundo dark psicologia
        "prompt": (
            "masterpiece, kawaii chibi anime researcher woman, dark psychology, "
            "dramatic purple red gradient background, spotlight, dramatic shadows, "
            "no text ### text, watermark, nsfw, bright background"
        ),
        "cor_fundo": "0D000D",
        "cor_texto": "C084FC",
        "hz_label": "",
        "sublabel": "Psicologia Dark ✦ Daniela Coelho",
        "usa_daniela": True,
    },
    "foco_trabalho": {
        # Workspace moderno, produtividade
        "prompt": (
            "minimal modern workspace, soft morning light, clean desk, plant, "
            "productivity atmosphere, calm focus, warm lighting, "
            "cinematic interior photography ### text, watermark, anime, people"
        ),
        "cor_fundo": "0A0A1A",
        "cor_texto": "88AAFF",
        "hz_label": "40 Hz",
        "sublabel": "Produtividade ✦ Deep Work",
        "usa_daniela": False,
    },
    "ansiedade_432": {
        # Lavanda, natureza calma
        "prompt": (
            "peaceful lavender field at golden hour, soft purple tones, "
            "calm healing atmosphere, gentle breeze, serenity, "
            "cinematic nature photography ### text, watermark, anime, night, dark"
        ),
        "cor_fundo": "0D0D1F",
        "cor_texto": "A78BFA",
        "hz_label": "432 Hz",
        "sublabel": "Ansiedade Zero ✦ Sistema Nervoso",
        "usa_daniela": False,
    },
    "prime_time": {
        # Daniela no prime time
        "prompt": (
            "masterpiece, kawaii chibi anime researcher woman, dark dramatic psychology, "
            "deep purple crimson gradient, cinematic shadows, intense atmosphere, "
            "no text ### text, watermark, nsfw"
        ),
        "cor_fundo": "0F0005",
        "cor_texto": "F87171",
        "hz_label": "",
        "sublabel": "Psicologia Dark ✦ Prime Time",
        "usa_daniela": True,
    },
    "cura_174": {
        # Floresta cura, luz dourada
        "prompt": (
            "magical healing forest, golden sunlight rays through ancient trees, "
            "green moss, peace and restoration, ethereal atmosphere, "
            "cinematic nature photography ### text, watermark, anime, night"
        ),
        "cor_fundo": "050F05",
        "cor_texto": "86EFAC",
        "hz_label": "174 Hz",
        "sublabel": "Cura Emocional ✦ Alívio do Trauma",
        "usa_daniela": False,
    },
}

AGENDA_24H = [
    # (hora_inicio_brt, hora_fim_brt, bloco)
    (22, 6,  "sono_528"),
    (6,  9,  "foco_40"),
    (9,  12, "psicologia"),
    (12, 15, "foco_trabalho"),
    (15, 18, "ansiedade_432"),
    (18, 21, "prime_time"),
    (21, 22, "cura_174"),
]

def hora_brt():
    return (datetime.now(timezone.utc) - timedelta(hours=3)).hour

def bloco_atual():
    h = hora_brt()
    for ini, fim, bloco in AGENDA_24H:
        if ini > fim:
            if h >= ini or h < fim: return bloco
        else:
            if ini <= h < fim: return bloco
    return "prime_time"

def pollinations_frame(bloco, idx):
    v = VISUAIS[bloco]
    seed = 7001 + idx * 53
    url = (f"https://image.pollinations.ai/prompt/{requests.utils.quote(v['prompt'])}"
           f"?seed={seed}&width=1280&height=720&nologo=true")
    try:
        r = requests.get(url, timeout=35, verify=False)
        if r.status_code == 200 and len(r.content) > 8000:
            p = TMP / f"frame_{bloco}_{idx}.jpg"
            p.write_bytes(r.content)
            return str(p)
    except: pass
    return None

def criar_frame_ffmpeg(bloco, idx):
    """Frame via FFmpeg com texto Hz — fallback sempre limpo"""
    v = VISUAIS[bloco]
    out = str(TMP / f"ff_{bloco}_{idx}.jpg")
    bg  = v["cor_fundo"]
    tc  = v["cor_texto"]
    hz  = v.get("hz_label","")
    sub = v.get("sublabel","")

    vf_parts = [f"drawbox=w=iw:h=ih:color=0x{bg}:t=fill"]

    if hz:
        vf_parts.append(
            f"drawtext=text='{hz}':fontsize=96:fontcolor=0x{tc}:x=(w-text_w)/2:y=240"
            f":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        )
    if sub:
        vf_parts.append(
            f"drawtext=text='{sub}':fontsize=32:fontcolor=0x{tc}AA:x=(w-text_w)/2:y=370"
            f":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        )

    vf = ",".join(vf_parts)
    cmd = ["ffmpeg","-y","-f","lavfi","-i","color=size=1280x720:rate=1",
           "-vf",vf,"-frames:v","1","-q:v","2",out]
    r = subprocess.run(cmd, capture_output=True, timeout=15)
    return out if r.returncode == 0 else None

def gerar_binaural(hz, out):
    if hz <= 0 or pathlib.Path(out).exists(): return True
    freq2 = hz + 10
    cmd = ["ffmpeg","-y","-f","lavfi",
           "-i",f"sine=frequency={hz}:duration=600",
           "-f","lavfi","-i",f"sine=frequency={freq2}:duration=600",
           "-filter_complex","[0:a][1:a]amerge,volume=0.25[out]",
           "-map","[out]","-ar","44100","-b:a","128k",out]
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    return r.returncode == 0

HZ_MAP = {
    "sono_528": 528, "foco_40": 40, "foco_trabalho": 40,
    "ansiedade_432": 432, "cura_174": 174,
    "psicologia": 0, "prime_time": 0,
}

def stream_frame(frame, hz, duracao=60):
    audio_args = []
    if hz > 0:
        tone = str(TMP / f"tone_{hz}.mp3")
        gerar_binaural(hz, tone)
        if pathlib.Path(tone).exists():
            audio_args = ["-stream_loop","-1","-i",tone,
                          "-c:a","aac","-b:a","128k","-ar","44100"]
    if not audio_args:
        audio_args = ["-f","lavfi","-i","anullsrc=r=44100:cl=stereo",
                      "-c:a","aac","-b:a","128k","-ar","44100"]
    for rtmp in [RTMP_PRI, RTMP_BCK]:
        cmd = (["ffmpeg","-y","-re","-loop","1","-i",frame]
               + audio_args
               + ["-c:v","libx264","-preset","ultrafast","-tune","zerolatency",
                  "-b:v","3000k","-maxrate","3000k","-bufsize","6000k",
                  "-pix_fmt","yuv420p","-r","30",
                  "-t",str(duracao),"-f","flv",rtmp])
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=duracao+30)
            if result.returncode == 0: return True
        except: pass
    return False

def run():
    import sys
    if not STREAM_KEY:
        print("ERRO: YOUTUBE_STREAM_KEY não configurado")
        sys.exit(1)
    print("=== LIVE 24H v2 — Visual Correto por Bloco ===")
    print("  22-06h: NATUREZA NOTURNA (sem anime) + 528Hz sono")
    print("  06-09h: AMANHECER + 40Hz foco")
    print("  09-12h: DANIELA dark + psicologia")
    print("  12-15h: WORKSPACE + 40Hz produtividade")
    print("  15-18h: LAVANDA + 432Hz ansiedade")
    print("  18-21h: DANIELA prime time + CTA SONO")
    print("  21-22h: FLORESTA + 174Hz cura")
    print()
    idx = 0
    while True:
        bloco = bloco_atual()
        hz    = HZ_MAP.get(bloco, 0)
        v     = VISUAIS[bloco]
        h_brt = hora_brt()
        print(f"  {h_brt:02d}h BRT [{bloco}] {'Daniela' if v['usa_daniela'] else 'Natureza'} {f'{hz}Hz' if hz else ''}")
        # Gerar frame via Pollinations primeiro, fallback FFmpeg
        frame = pollinations_frame(bloco, idx)
        if not frame:
            frame = criar_frame_ffmpeg(bloco, idx)
        if frame:
            stream_frame(frame, hz, 60)
        idx += 1
        time.sleep(2)

if __name__=="__main__": run()
