#!/usr/bin/env python3
"""
live_24h_manager.py — PRETO MATEMÁTICO ABSOLUTO (Y=0, U=128, V=128)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TÉCNICA DEFINITIVA para zero brilho:
  geq=0:128:128 → gera Y=0 U=128 V=128 em cada pixel
  Isso é preto MATEMÁTICO em espaço de cor YUV.
  NENHUM codec consegue adicionar brilho nisso.
  NENHUM pixel diferente de zero luminância.
  
  No AMOLED: pixel Y=0 = pixel DESLIGADO = consumo zero = brilho zero.
  No LCD:    pixel Y=0 = backlight mínimo possível do display.

  DURANTE SONO (22h-06h BRT):
  → ZERO texto na tela
  → ZERO elementos visuais
  → ZERO brilho
  → APENAS áudio binaural 528Hz/538Hz nos fones
"""
import os, time, subprocess, pathlib, sys
from datetime import datetime, timezone, timedelta

STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY","")
GROQ_KEY   = os.getenv("GROQ_API_KEY","")
RTMP_PRI   = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
RTMP_BCK   = f"rtmp://b.rtmp.youtube.com/live2/{STREAM_KEY}?backup=1"
TMP        = pathlib.Path("/tmp/lv"); TMP.mkdir(exist_ok=True)
FONT_B     = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_L     = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BLOCOS = {
    "sono_528":     {"hz":528,"hz2":538,"preta":True},
    "foco_40":      {"hz":40,"hz2":50,"preta":False,"bg":"010C01","c1":"00FF66","c2":"00AA44","label":"40 Hz","sub":"Foco Total Ondas Gamma"},
    "psicologia":   {"hz":0,"hz2":0,"preta":False,"bg":"08000F","c1":"CC00FF","c2":"880099","label":"PSICOLOGIA","sub":"Dark Psychology Daniela Coelho"},
    "foco_trabalho":{"hz":40,"hz2":50,"preta":False,"bg":"010814","c1":"0088FF","c2":"0055AA","label":"40 Hz","sub":"Produtividade Deep Work"},
    "ansiedade_432":{"hz":432,"hz2":442,"preta":False,"bg":"060010","c1":"9955FF","c2":"6633CC","label":"432 Hz","sub":"Ansiedade Zero"},
    "prime_time":   {"hz":0,"hz2":0,"preta":False,"bg":"0F0000","c1":"FF2200","c2":"AA1100","label":"PRIME TIME","sub":"Psicologia Dark Ao Vivo"},
    "cura_174":     {"hz":174,"hz2":184,"preta":False,"bg":"010C02","c1":"00DD55","c2":"009933","label":"174 Hz","sub":"Cura Emocional"},
}
AGENDA = [(22,6,"sono_528"),(6,9,"foco_40"),(9,12,"psicologia"),
          (12,15,"foco_trabalho"),(15,18,"ansiedade_432"),(18,21,"prime_time"),(21,22,"cura_174")]

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

def stream_preto_zero(hz, hz2, duracao=60):
    """
    PRETO MATEMÁTICO ABSOLUTO:
    - nullsrc gera frames sem conteúdo
    - geq=0:128:128 força Y=0 U=128 V=128 em cada pixel
    - Y=0 = luminância ZERO = pixel completamente apagado no AMOLED
    - Sem texto, sem elemento, sem nada na tela
    """
    for rtmp in [RTMP_PRI, RTMP_BCK]:
        cmd = [
            "ffmpeg","-y",
            # Fonte de vídeo: pixels gerados matematicamente com Y=0
            "-f","lavfi",
            "-i","nullsrc=size=1280x720:rate=30",
            # Áudio: binaural real (hz=esq, hz2=dir)
            "-f","lavfi","-i",f"sine=frequency={hz}:sample_rate=44100",
            "-f","lavfi","-i",f"sine=frequency={hz2}:sample_rate=44100",
            # Filtro de vídeo: força preto matemático Y=0 U=128 V=128
            "-filter_complex",
            "geq=0:128:128[v];[1:a][2:a]join=inputs=2:channel_layout=stereo,volume=0.22[a]",
            "-map","[v]","-map","[a]",
            # Codec: qualidade mínima, bitrate mínimo, ainda image
            "-c:v","libx264",
            "-preset","ultrafast",
            "-tune","stillimage",
            "-crf","51",
            "-b:v","50k","-maxrate","50k","-bufsize","100k",
            "-pix_fmt","yuv420p",
            "-color_range","tv",      # limited range: preto = nível 16
            "-r","30","-g","60",
            "-c:a","aac","-b:a","192k","-ar","44100",
            "-t",str(duracao),"-f","flv",rtmp
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=duracao+30)
            if r.returncode == 0: return True
        except Exception as e:
            print(f"  erro: {e}")
    return False

def stream_visual(bloco_nome, duracao=60):
    b = BLOCOS[bloco_nome]
    hz = b["hz"]; hz2 = b["hz2"]
    out = str(TMP / f"f_{bloco_nome}.jpg")
    hora = datetime.now().strftime("%H:%M")
    vf = (
        f"drawbox=w=iw:h=ih:color=0x{b['bg']}:t=fill,"
        f"drawbox=x=0:y=0:w=iw:h=6:color=0x{b['c1']}:t=fill,"
        f"drawbox=x=0:y=714:w=iw:h=6:color=0x{b['c1']}:t=fill,"
        f"drawtext=text='{b['label']}':fontsize=120:fontcolor=0x{b['c1']}:"
        f"x=(w-text_w)/2:y=210:fontfile={FONT_B},"
        f"drawtext=text='{b['sub']}':fontsize=30:fontcolor=0x{b['c1']}CC:"
        f"x=(w-text_w)/2:y=358:fontfile={FONT_L},"
        f"drawbox=x=160:y=415:w=960:h=2:color=0x{b['c2']}:t=fill,"
        f"drawtext=text='AO VIVO {hora} BRT @psidanielacoelho':"
        f"fontsize=20:fontcolor=0x{b['c2']}:x=(w-text_w)/2:y=435:fontfile={FONT_L}"
    )
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","color=size=1280x720:rate=1",
                    "-vf",vf,"-frames:v","1","-q:v","2",out],
                   capture_output=True, timeout=20)
    if hz > 0:
        audio = ["-f","lavfi","-i",f"sine=frequency={hz}:sample_rate=44100",
                 "-f","lavfi","-i",f"sine=frequency={hz2}:sample_rate=44100",
                 "-filter_complex","[1:a][2:a]join=inputs=2:channel_layout=stereo,volume=0.22[a]",
                 "-map","0:v","-map","[a]","-c:a","aac","-b:a","192k","-ar","44100"]
    else:
        audio = ["-f","lavfi","-i","sine=frequency=60:sample_rate=44100",
                 "-filter_complex","[1:a]volume=0.04[a]",
                 "-map","0:v","-map","[a]","-c:a","aac","-b:a","128k","-ar","44100"]
    for rtmp in [RTMP_PRI, RTMP_BCK]:
        cmd = (["ffmpeg","-y","-re","-loop","1","-i",out]
               + audio
               + ["-c:v","libx264","-preset","ultrafast","-tune","zerolatency",
                  "-b:v","3000k","-maxrate","3000k","-bufsize","6000k",
                  "-pix_fmt","yuv420p","-r","30","-t",str(duracao),"-f","flv",rtmp])
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=duracao+30)
            if r.returncode == 0: return True
        except: pass
    return False

def run():
    if not STREAM_KEY:
        print("ERRO: YOUTUBE_STREAM_KEY nao configurado"); sys.exit(1)
    print("=== LIVE 24H — PRETO MATEMÁTICO ABSOLUTO ===")
    print("  SONO (22-06h): geq=0:128:128 → Y=0 em cada pixel → brilho ZERO")
    print("  ZERO texto na tela durante sono — apenas áudio binaural")
    print()
    while True:
        bloco = bloco_atual()
        b     = BLOCOS[bloco]
        h_brt = hora_brt()
        if b.get("preta"):
            hz = b["hz"]; hz2 = b["hz2"]
            print(f"  {h_brt:02d}h [PRETO ZERO] {hz}Hz/{hz2}Hz binaural — tela 100% apagada")
            stream_preto_zero(hz, hz2, 60)
        else:
            print(f"  {h_brt:02d}h [{bloco}] {b.get('label','')} — {b.get('sub','')[:25]}")
            stream_visual(bloco, 60)
        time.sleep(2)

if __name__=="__main__": run()
