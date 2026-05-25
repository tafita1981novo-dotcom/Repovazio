#!/usr/bin/env python3
"""
live_24h_manager.py v3 — Visual limpo + Som binaural CORRIGIDO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROBLEMAS CORRIGIDOS:
  ✅ Sem menina/anime — visual minimalista profissional como Meditative Mind
  ✅ Som binaural gerado inline no FFmpeg (sem arquivo externo)
  ✅ Thumbnails coloridos e vibrantes por bloco
"""
import os, time, subprocess, pathlib, sys, requests
from datetime import datetime, timezone, timedelta
import urllib3; urllib3.disable_warnings()

STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY","")
GROQ_KEY   = os.getenv("GROQ_API_KEY","")
RTMP_PRI   = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
RTMP_BCK   = f"rtmp://b.rtmp.youtube.com/live2/{STREAM_KEY}?backup=1"
TMP        = pathlib.Path("/tmp/lv3"); TMP.mkdir(exist_ok=True)
FONT       = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_L     = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Blocos — visual, cores, frequência
BLOCOS = {
    "sono_528": {
        "hz":528, "hz2":538,
        "bg":"0x030818",       # azul noite profundo
        "cor1":"0x4488FF",     # azul vivo
        "cor2":"0x0066CC",     # azul médio
        "cor3":"0xAADDFF",     # azul claro
        "label":"528 Hz",
        "linha1":"SONO PROFUNDO",
        "linha2":"Regeneração Celular • Walker/Berkeley",
        "tag":"🌙 AO VIVO 8H • @psidanielacoelho",
    },
    "foco_40": {
        "hz":40, "hz2":50,
        "bg":"0x010F01",
        "cor1":"0x00FF88",
        "cor2":"0x00AA55",
        "cor3":"0x88FFCC",
        "label":"40 Hz",
        "linha1":"FOCO TOTAL",
        "linha2":"Ondas Gamma • Deep Work • MIT Research",
        "tag":"⚡ AO VIVO • @psidanielacoelho",
    },
    "psicologia": {
        "hz":0, "hz2":0,
        "bg":"0x0D000D",
        "cor1":"0xCC00FF",
        "cor2":"0x880099",
        "cor3":"0xFF88FF",
        "label":"PSICOLOGIA",
        "linha1":"DARK PSYCHOLOGY",
        "linha2":"Narcisismo • Apego • Harvard Research",
        "tag":"😶 Daniela Coelho • AO VIVO",
    },
    "foco_trabalho": {
        "hz":40, "hz2":50,
        "bg":"0x010818",
        "cor1":"0x0099FF",
        "cor2":"0x0055BB",
        "cor3":"0x88CCFF",
        "label":"40 Hz",
        "linha1":"PRODUTIVIDADE",
        "linha2":"Deep Work • Gamma • Burnout Science",
        "tag":"🧠 AO VIVO • @psidanielacoelho",
    },
    "ansiedade_432": {
        "hz":432, "hz2":442,
        "bg":"0x080014",
        "cor1":"0x9900FF",
        "cor2":"0x6600AA",
        "cor3":"0xCC88FF",
        "label":"432 Hz",
        "linha1":"ANSIEDADE ZERO",
        "linha2":"Sistema Nervoso • Dr. Porges Research",
        "tag":"💜 AO VIVO • @psidanielacoelho",
    },
    "prime_time": {
        "hz":0, "hz2":0,
        "bg":"0x0F0000",
        "cor1":"0xFF2200",
        "cor2":"0xAA1100",
        "cor3":"0xFF8866",
        "label":"PRIME TIME",
        "linha1":"PSICOLOGIA DARK",
        "linha2":"Trauma • Apego • Burnout • AO VIVO",
        "tag":"🔥 18h BRT • @psidanielacoelho",
    },
    "cura_174": {
        "hz":174, "hz2":184,
        "bg":"0x010F03",
        "cor1":"0x00FF66",
        "cor2":"0x00AA44",
        "cor3":"0x88FFAA",
        "label":"174 Hz",
        "linha1":"CURA EMOCIONAL",
        "linha2":"Alívio do Trauma • van der Kolk",
        "tag":"🌿 AO VIVO • @psidanielacoelho",
    },
}

AGENDA = [
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
    for ini, fim, b in AGENDA:
        if ini > fim:
            if h >= ini or h < fim: return b
        else:
            if ini <= h < fim: return b
    return "prime_time"

def gerar_frame(bloco, idx):
    """Gera frame colorido profissional via FFmpeg — SEM FIGURAS HUMANAS"""
    b = BLOCOS[bloco]
    out = str(TMP / f"f_{bloco}_{idx%4}.jpg")
    hora_str = datetime.now().strftime("%H:%M")

    # Cores sem prefixo 0x para drawtext
    c1 = b["cor1"].replace("0x","")
    c2 = b["cor2"].replace("0x","")
    c3 = b["cor3"].replace("0x","")

    vf_parts = [
        # Fundo
        f"drawbox=w=iw:h=ih:color={b['bg']}:t=fill",
        # Barra top colorida
        f"drawbox=x=0:y=0:w=iw:h=8:color=0x{c1}:t=fill",
        # Barra bottom colorida
        f"drawbox=x=0:y=712:w=iw:h=8:color=0x{c1}:t=fill",
        # Retângulo central sutil
        f"drawbox=x=100:y=180:w=1080:h=360:color=0x{c2}22:t=fill",
    ]

    # Hz grande (ou LABEL para psicologia)
    vf_parts.append(
        f"drawtext=text='{b['label']}':fontsize=140:fontcolor=0x{c1}:"
        f"x=(w-text_w)/2:y=200:fontfile={FONT}"
    )
    # Linha 1
    vf_parts.append(
        f"drawtext=text='{b['linha1']}':fontsize=42:fontcolor=0x{c3}:"
        f"x=(w-text_w)/2:y=375:fontfile={FONT}:fontcolor_expr=0x{c3}"
    )
    # Linha 2
    vf_parts.append(
        f"drawtext=text='{b['linha2']}':fontsize=26:fontcolor=0x{c1}AA:"
        f"x=(w-text_w)/2:y=430:fontfile={FONT_L}"
    )
    # Separador
    vf_parts.append(
        f"drawbox=x=200:y=475:w=880:h=2:color=0x{c1}66:t=fill"
    )
    # Tag bottom + hora
    tag_esc = b['tag'].replace("'","\'").replace(":",r"\:")
    vf_parts.append(
        f"drawtext=text='{tag_esc}   {hora_str} BRT':fontsize=22:fontcolor=0x{c3}:"
        f"x=(w-text_w)/2:y=495:fontfile={FONT_L}"
    )
    # Dot AO VIVO (canto superior esquerdo)
    vf_parts.append(
        "drawbox=x=30:y=25:w=12:h=12:color=0xFF3333:t=fill"
    )
    vf_parts.append(
        "drawtext=text='AO VIVO':fontsize=18:fontcolor=0xFF3333:x=52:y=24:fontfile=" + FONT
    )

    vf = ",".join(vf_parts)
    cmd = ["ffmpeg","-y","-f","lavfi","-i","color=size=1280x720:rate=1",
           "-vf",vf,"-frames:v","1","-q:v","2",out]
    r = subprocess.run(cmd, capture_output=True, timeout=20)
    if r.returncode == 0: return out
    # Fallback mínimo
    cmd2 = ["ffmpeg","-y","-f","lavfi","-i",f"color=c={b['bg']}:size=1280x720:rate=1",
            "-frames:v","1",out]
    subprocess.run(cmd2, capture_output=True, timeout=10)
    return out

def stream_com_binaural(frame, hz, hz2, duracao=60):
    """
    Stream com som binaural gerado INLINE pelo FFmpeg.
    Hz esquerdo ≠ Hz direito → efeito binaural no ouvinte.
    Sem arquivo externo de áudio — 100% confiável.
    """
    for rtmp in [RTMP_PRI, RTMP_BCK]:
        if hz > 0:
            # Binaural real: canal esq = hz, canal dir = hz2
            audio_filter = (
                f"[0:a]pan=stereo|c0=c0|c1=c1[binaural]"
            )
            cmd = [
                "ffmpeg","-y","-re",
                "-loop","1","-i",frame,
                # Gera dois tons diferentes em mono
                "-f","lavfi","-i",f"sine=frequency={hz}:sample_rate=44100",
                "-f","lavfi","-i",f"sine=frequency={hz2}:sample_rate=44100",
                # Merge os dois canais em stereo (esquerdo=hz, direito=hz2)
                "-filter_complex",
                f"[1:a][2:a]join=inputs=2:channel_layout=stereo,volume=0.3[a]",
                "-map","0:v","-map","[a]",
                "-c:v","libx264","-preset","ultrafast","-tune","zerolatency",
                "-b:v","3000k","-maxrate","3000k","-bufsize","6000k",
                "-pix_fmt","yuv420p","-r","30",
                "-c:a","aac","-b:a","192k","-ar","44100",
                "-t",str(duracao),"-f","flv",rtmp
            ]
        else:
            # Psicologia: fundo musical suave (sine grave)
            cmd = [
                "ffmpeg","-y","-re",
                "-loop","1","-i",frame,
                "-f","lavfi","-i","sine=frequency=180:sample_rate=44100",
                "-filter_complex","[1:a]volume=0.08[a]",
                "-map","0:v","-map","[a]",
                "-c:v","libx264","-preset","ultrafast","-tune","zerolatency",
                "-b:v","3000k","-pix_fmt","yuv420p","-r","30",
                "-c:a","aac","-b:a","128k","-ar","44100",
                "-t",str(duracao),"-f","flv",rtmp
            ]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=duracao+30)
            if result.returncode == 0: return True
        except Exception as e:
            print(f"  Erro RTMP: {e}")
    return False

def run():
    if not STREAM_KEY:
        print("ERRO: YOUTUBE_STREAM_KEY não configurado"); sys.exit(1)

    print("=== LIVE 24H v3 — Visual Profissional + Som Binaural Corrigido ===")
    print("  Visual: texto Hz grande, cores vibrantes, SEM figuras")
    print("  Som: binaural inline FFmpeg (esq/dir diferente = efeito real)")
    print()

    idx = 0
    while True:
        bloco = bloco_atual()
        b     = BLOCOS[bloco]
        hz    = b["hz"]
        hz2   = b["hz2"]
        h_brt = hora_brt()

        print(f"  {h_brt:02d}h [{bloco}] {b['label']} | "
              f"{'binaural '+str(hz)+'Hz/'+str(hz2)+'Hz' if hz else 'tom ambiente'}")

        frame = gerar_frame(bloco, idx)
        ok    = stream_com_binaural(frame, hz, hz2, 60)
        if not ok:
            print("  Stream falhou — tentando próximo frame")

        idx += 1
        time.sleep(2)

if __name__=="__main__": run()
