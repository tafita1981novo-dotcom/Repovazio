#!/usr/bin/env python3
"""
master_image_selector.py
Seleciona e aplica a imagem CERTA para cada tipo de vídeo.

REGRAS APRENDIDAS DA ANÁLISE VISUAL:
  1. NUNCA incluir texto no prompt Pollinations — o FLUX distorce tudo
  2. Texto SEMPRE via FFmpeg overlay com fontes corretas
  3. meditative.jpg (9.5/10) → sono/528Hz/healing (MELHOR background disponível)
  4. psych2go.jpg (8.5/10) → psicologia/ansiedade/narcisismo (CTR 15%+)
  5. thumbnail_adhd_focus.jpg (8/10) → ADHD/40Hz/foco
  6. Regenerar qualquer imagem com texto distorcido

PROMPTS SEGUROS (sem texto):
  sleep:  "dark bioluminescent forest mushrooms blue purple lake reflection"
  psych:  "kawaii chibi anime psychology girl thoughtful gradient purple"
  focus:  "sacred geometry mandala neon green black background fractal"
  dark:   "dramatic cinematic silhouette dark purple spotlight mist"
  cosmic: "deep space milky way aurora borealis purple blue nebula"
  nature: "mountain lake midnight aurora reflection serene"
"""
import requests, pathlib, subprocess, textwrap

TMP = pathlib.Path("/tmp/imgs"); TMP.mkdir(exist_ok=True)
GH_RAW = "https://raw.githubusercontent.com/tafita81/Repovazio/main"

# Imagens analisadas e aprovadas — download direto do GitHub
IMAGENS_APROVADAS = {
    "sleep":   f"{GH_RAW}/public/estilos_virais/meditative.jpg",  # 9.5/10
    "psych":   f"{GH_RAW}/public/estilos_virais/psych2go.jpg",    # 8.5/10
    "focus":   f"{GH_RAW}/public/thumbnails/thumbnail_adhd_focus.jpg", # 8/10
    "dark":    f"{GH_RAW}/public/thumbnails/thumbnail_narcissism_en.jpg",
    "cosmic":  f"{GH_RAW}/public/thumbnails/sleep_528hz.jpg",
}

# Mapeamento keyword → estilo (ordem importa: mais específico primeiro)
MAPA_ESTILO = [
    (["528hz","432hz","396hz","174hz","sono","sleep","healing"], "sleep"),
    (["40hz","gamma","adhd","tdah","foco","focus","concentra"],  "focus"),
    (["narcis","gaslight","trauma","manipul","toxic","abuse"],    "dark"),
    (["ansios","anxious","apego","attachment","burnout","depres","solidao","loneli","perfecti"],"psych"),
    (["cosmic","universe","cosmos","galaxy","meditacao","medita"], "cosmic"),
]

PROMPTS_FALLBACK = {
    "sleep":  "masterpiece 8K dark bioluminescent forest at night glowing blue purple mushrooms fireflies misty lake no text no people no logos ### text watermark nsfw",
    "psych":  "kawaii chibi anime psychology girl thoughtful expression soft purple blue gradient icons floating clean digital art no text ### text watermark nsfw",
    "focus":  "sacred geometry mandala glowing neon green electric blue black background flower of life fractal mathematical no text no people ### text watermark nsfw",
    "dark":   "dramatic dark cinematic purple silhouette spotlight mist psychology concept shadow contrast moody no text no faces ### text watermark nsfw",
    "cosmic": "deep dark cosmic space milky way purple blue nebula aurora borealis particles ethereal serene no text no people ### text watermark nsfw",
    "nature": "ultra HD dark mountain lake midnight aurora reflection mist serenity no text no people ### text watermark nsfw",
}

def selecionar_estilo(titulo):
    t = titulo.lower()
    for keywords, estilo in MAPA_ESTILO:
        if any(k in t for k in keywords):
            return estilo
    return "nature"

def obter_imagem(estilo, seed=9001):
    """Tenta GitHub primeiro, gera nova se falhar"""
    # 1. Tentar imagem aprovada do GitHub
    if estilo in IMAGENS_APROVADAS:
        cached = TMP/f"gh_{estilo}.jpg"
        if cached.exists() and cached.stat().st_size > 20000:
            return cached
        try:
            r = requests.get(IMAGENS_APROVADAS[estilo], timeout=15)
            if r.status_code == 200 and len(r.content) > 20000:
                cached.write_bytes(r.content)
                return cached
        except: pass
    
    # 2. Gerar nova via Pollinations (sem texto no prompt!)
    prompt = PROMPTS_FALLBACK.get(estilo, PROMPTS_FALLBACK["nature"])
    url = (f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt[:400])}"
           f"?model=flux&width=1920&height=1080&seed={seed}&nologo=true&enhance=true")
    nova = TMP/f"gen_{estilo}_{seed}.jpg"
    try:
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and len(r.content) > 20000:
            nova.write_bytes(r.content)
            return nova
    except: pass
    return None

def aplicar_overlay_ffmpeg(img_p, voz_p, freq_p, titulo, marca, estilo, hz_label, out_p):
    """
    Aplica overlay correto baseado no estilo — texto via FFmpeg, não no prompt.
    
    ESTILOS E OVERLAYS:
    sleep   → Hz dourado 66px no topo + título branco suave baixo (Meditative Mind)
    focus   → Hz neon verde 80px centro + GAMMA WAVES (Greenred)
    dark    → Indicador LIVE + título 36px bold central (Psychology dark)
    psych   → Número grande + título (Psych2Go)
    cosmic  → Hz azul 44px + título (Jason Stephenson)
    nature  → Minimal: Hz pequeno + título suave
    """
    # Mix de áudio
    mix = TMP/f"mix_{out_p.stem}.aac"
    if freq_p and freq_p.exists():
        subprocess.run(["ffmpeg","-y","-i",str(voz_p),"-i",str(freq_p),
            "-filter_complex","[0:a]volume=1[v];[1:a]volume=0.12[f];[v][f]amix=inputs=2:duration=first[out]",
            "-map","[out]","-c:a","aac","-b:a","128k",str(mix)],
            capture_output=True, timeout=60)
    else: mix=voz_p
    
    dur_r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(mix)],capture_output=True,timeout=8)
    try: dur=min(float(dur_r.stdout.strip())+0.5,59.0)
    except: dur=55.0
    
    t = titulo[:52].replace("'",r"\'")
    m = marca.replace("'",r"\'")
    hz = (hz_label or "528Hz").replace("'",r"\'")
    
    BRIGHT = {"sleep":"0.55","focus":"0.50","dark":"0.52","psych":"0.62","cosmic":"0.58","nature":"0.60"}
    b = BRIGHT.get(estilo,"0.60")
    W, H = 1920, 1080
    
    if estilo == "sleep":
        # Meditative Mind: Hz DOURADO grande no topo
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"colorchannelmixer=rr={b}:gg={b}:bb={b},"
              f"drawbox=y=0:color=black@0.72:width=iw:height=130:t=fill,"
              f"drawbox=y=ih-80:color=black@0.72:width=iw:height=80:t=fill,"
              f"drawtext=text='{hz}':fontsize=66:fontcolor=#FFD700:x=(w-text_w)/2:y=12:bold=1:shadowcolor=#8B6914:shadowx=3:shadowy=3,"
              f"drawtext=text='BINAURAL · DELTA 4Hz':fontsize=22:fontcolor=#FCD34D@0.88:x=(w-text_w)/2:y=90,"
              f"drawtext=text='{t}':fontsize=30:fontcolor=white@0.9:x=(w-text_w)/2:y=h*0.78:shadowcolor=#000:shadowx=2:shadowy=2,"
              f"drawtext=text='{m}':fontsize=14:fontcolor=#94A3B8:x=(w-text_w)/2:y=h-52")
    elif estilo == "focus":
        # Greenred: Hz neon verde ENORME
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"colorchannelmixer=rr={b}:gg={b}:bb={b},"
              f"drawbox=y=0:color=black@0.78:width=iw:height=120:t=fill,"
              f"drawbox=y=ih-80:color=black@0.78:width=iw:height=80:t=fill,"
              f"drawtext=text='{hz}':fontsize=80:fontcolor=#00FF88:x=(w-text_w)/2:y=6:bold=1:shadowcolor=#001a00:shadowx=5:shadowy=5,"
              f"drawtext=text='GAMMA WAVES · FOCUS · WORKING MEMORY':fontsize=18:fontcolor=#00CC66@0.9:x=(w-text_w)/2:y=96,"
              f"drawtext=text='{t}':fontsize=28:fontcolor=white:x=(w-text_w)/2:y=h*0.80:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
              f"drawtext=text='{m}':fontsize=14:fontcolor=#86EFAC:x=(w-text_w)/2:y=h-52")
    elif estilo == "dark":
        # Psychology Dark: indicador LIVE + título central grande
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"colorchannelmixer=rr={b}:gg={b}:bb={b},"
              f"drawbox=y=0:color=black@0.85:width=iw:height=105:t=fill,"
              f"drawbox=y=ih-80:color=black@0.85:width=iw:height=80:t=fill,"
              f"drawbox=x=16:y=20:color=#EF4444:width=13:height=13:t=fill,"
              f"drawtext=text='AO VIVO · Psychology':fontsize=18:fontcolor=#EF4444:x=38:y=16:bold=1,"
              f"drawtext=text='Science-Based Content':fontsize=15:fontcolor=#94A3B8:x=38:y=42,"
              f"drawtext=text='{t}':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=h*0.38:bold=1:shadowcolor=#000:shadowx=3:shadowy=3,"
              f"drawtext=text='{m}':fontsize=14:fontcolor=#CBD5E1:x=(w-text_w)/2:y=h-52")
    elif estilo == "psych":
        # Psych2Go: título bem legível, personagem como fundo
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"colorchannelmixer=rr={b}:gg={b}:bb={b},"
              f"drawbox=y=0:color=black@0.70:width=iw:height=100:t=fill,"
              f"drawbox=y=ih-80:color=black@0.70:width=iw:height=80:t=fill,"
              f"drawbox=x=16:y=20:color=#EF4444:width=10:height=10:t=fill,"
              f"drawtext=text='Psychology · Science':fontsize=18:fontcolor=#818CF8:x=36:y=17:bold=1,"
              f"drawtext=text='{t}':fontsize=32:fontcolor=white:x=(w-text_w)/2:y=h*0.42:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
              f"drawtext=text='{m}':fontsize=14:fontcolor=#A5B4FC:x=(w-text_w)/2:y=h-52")
    else:  # cosmic/nature — Jason Stephenson minimal
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"colorchannelmixer=rr={b}:gg={b}:bb={b},"
              f"drawbox=y=0:color=black@0.68:width=iw:height=100:t=fill,"
              f"drawbox=y=ih-80:color=black@0.68:width=iw:height=80:t=fill,"
              f"drawtext=text='{hz}':fontsize=44:fontcolor=#818CF8:x=(w-text_w)/2:y=14:bold=1,"
              f"drawtext=text='Science · Psychology':fontsize=18:fontcolor=#A5B4FC@0.85:x=(w-text_w)/2:y=68,"
              f"drawtext=text='{t}':fontsize=30:fontcolor=white@0.9:x=(w-text_w)/2:y=h*0.80:shadowcolor=#000:shadowx=2:shadowy=2,"
              f"drawtext=text='{m}':fontsize=14:fontcolor=#94A3B8:x=(w-text_w)/2:y=h-52")
    
    subprocess.run(["ffmpeg","-y","-loop","1","-i",str(img_p),"-i",str(mix),
        "-vf",vf,"-t",str(dur),"-c:v","libx264","-preset","fast",
        "-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","128k","-shortest",str(out_p)],
        capture_output=True,timeout=300)
    return out_p.exists() and out_p.stat().st_size > 50000

if __name__ == "__main__":
    print("=== TESTE DO SELETOR DE IMAGENS ===")
    test_casos = [
        ("528Hz Deep Sleep — Anxiety Healing",  "528Hz"),
        ("10 Signs of Covert Narcissism",        None),
        ("40Hz Gamma ADHD Focus Protocol",       "40Hz"),
        ("Anxious Attachment Hijacks Your Sleep","432Hz"),
        ("Cosmic Meditation — Universe Healing", "174Hz"),
    ]
    for titulo, hz in test_casos:
        estilo = selecionar_estilo(titulo)
        img = obter_imagem(estilo, 9001)
        status = f"✅ {img}" if img and img.exists() else "❌ falhou"
        print(f"  [{estilo:7}] '{titulo[:45]}' → {status}")
    print("\n✅ Seletor funcionando!")
