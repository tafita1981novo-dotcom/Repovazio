#!/usr/bin/env python3
"""
gen_viral_images.py
Gera imagens baseadas nos 6 estilos visuais dos canais virais de milhões:

1. MEDITATIVE MIND (3.2M): Natureza bioluminescente escura + Hz dourado
2. PSYCH2GO (10.5M): Chibi anime + gradiente colorido  
3. LOFI GIRL (14M): Anime cozy bedroom + janela chuva
4. GREENRED (2M): Geometria sagrada neon + preto
5. JASON STEPHENSON (2.5M): Lago espelhado noturno sereno
6. CINEMATIC DARK (Psychology): Silhueta + contraste dramático

Para cada vídeo, seleciona o estilo certo baseado no tipo de conteúdo.
"""
import os, subprocess, requests, pathlib, time

TMP = pathlib.Path("/tmp/viral"); TMP.mkdir(exist_ok=True)
W, H = 1920, 1080

ESTILOS = {
    "sleep":   {
        "prompt": "masterpiece 8K ultra HD photo, dark bioluminescent forest at night, glowing blue purple mushrooms, fireflies, misty atmosphere, mirror lake, no text no people",
        "cor": "#FFD700", "label": "Meditative Mind",
    },
    "psych":   {
        "prompt": "kawaii chibi anime psychology student thoughtful expression, soft purple blue gradient background, floating icons, clean digital art, no text",
        "cor": "#FF6B6B", "label": "Psych2Go",
    },
    "lofi":    {
        "prompt": "anime cozy night bedroom girl studying at desk rainy window city lights warm lamp books coffee Studio Ghibli no text",
        "cor": "#E8C49A", "label": "Lofi Girl",
    },
    "focus":   {
        "prompt": "sacred geometry mandala glowing neon green electric blue pure black background flower of life metatron cube fractal no text no people",
        "cor": "#00FF88", "label": "Greenred",
    },
    "nature":  {
        "prompt": "ultra HD dark blue serene mountain lake midnight perfect mirror reflection full moon aurora borealis mist absolute stillness no text no people",
        "cor": "#818CF8", "label": "Jason Stephenson",
    },
    "dark":    {
        "prompt": "dramatic dark cinematic purple red tones silhouette psychology concept shadow light contrast moody ultra HD no text no real faces",
        "cor": "#EF4444", "label": "Psychology Dark",
    },
}

TIPO_PARA_ESTILO = {
    "narcissism": "dark", "narcisismo": "dark", "gaslighting": "dark", "trauma": "dark",
    "sleep": "sleep", "sono": "sleep", "528hz": "sleep", "432hz": "sleep",
    "focus": "focus", "foco": "focus", "adhd": "focus", "tdah": "focus", "40hz": "focus",
    "anxious": "psych", "ansioso": "psych", "apego": "psych", "perfectionism": "psych",
    "perfecti": "psych", "burnout": "psych", "loneliness": "psych", "solidão": "psych",
    "lofi": "lofi", "study": "lofi", "estudo": "lofi", "music": "lofi",
}

def selecionar_estilo(titulo):
    t = titulo.lower()
    for kw, estilo in TIPO_PARA_ESTILO.items():
        if kw in t: return estilo
    return "nature"  # default: Jason Stephenson style

def gerar_imagem(titulo, seed, estilo_override=None):
    estilo_key = estilo_override or selecionar_estilo(titulo)
    cfg = ESTILOS[estilo_key]
    
    prompt = f"{cfg['prompt']} ### text watermark nsfw blurry logos"
    url = (f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt[:400])}"
           f"?model=flux&width={W}&height={H}&seed={seed}&nologo=true&enhance=true")
    try:
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and len(r.content) > 20000:
            return r.content, cfg["cor"], cfg["label"], estilo_key
    except: pass
    return None, cfg["cor"], cfg["label"], estilo_key

def montar_slide_viral(img_data, titulo, marca, cor, hz_label, idioma, idx, estilo):
    """Monta slide com overlay baseado no estilo do canal viral"""
    img_p = TMP/f"bg_{estilo}_{idx}.jpg"
    img_p.write_bytes(img_data)
    
    t_e = titulo[:52].replace("'",r"\'")
    m_e = marca.replace("'",r"\'")
    
    # Escurecer imagem conforme estilo
    bright = "0.55" if estilo in ("dark","sleep","nature") else "0.65"
    
    # Overlay específico por estilo
    if estilo == "sleep":
        # Meditative Mind: Hz grande dourado no topo, texto minimal
        hz = hz_label or "528Hz"
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"colorchannelmixer=rr={bright}:gg={bright}:bb={bright},"
            f"drawbox=y=0:color=black@0.70:width=iw:height=120:t=fill,"
            f"drawbox=y=ih-80:color=black@0.70:width=iw:height=80:t=fill,"
            f"drawtext=text='{hz}':fontsize=64:fontcolor=#FFD700:x=(w-text_w)/2:y=14:bold=1:shadowcolor=#000:shadowx=3:shadowy=3,"
            f"drawtext=text='BINAURAL DELTA 4Hz':fontsize=22:fontcolor=#FCD34D@0.85:x=(w-text_w)/2:y=88,"
            f"drawtext=text='{t_e}':fontsize=30:fontcolor=white@0.9:x=(w-text_w)/2:y=h*0.78:shadowcolor=#000:shadowx=2:shadowy=2,"
            f"drawtext=text='{m_e}':fontsize=14:fontcolor=#94A3B8:x=(w-text_w)/2:y=h-50"
        )
    elif estilo == "focus":
        # Greenred: Hz ENORME neon no centro
        hz = hz_label or "40Hz"
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"colorchannelmixer=rr={bright}:gg={bright}:bb={bright},"
            f"drawbox=y=0:color=black@0.75:width=iw:height=110:t=fill,"
            f"drawbox=y=ih-80:color=black@0.75:width=iw:height=80:t=fill,"
            f"drawtext=text='{hz}':fontsize=80:fontcolor=#00FF88:x=(w-text_w)/2:y=8:bold=1:shadowcolor=#003300:shadowx=4:shadowy=4,"
            f"drawtext=text='GAMMA WAVES · FOCUS MODE':fontsize=20:fontcolor=#00CC66:x=(w-text_w)/2:y=96,"
            f"drawtext=text='{t_e}':fontsize=28:fontcolor=white:x=(w-text_w)/2:y=h*0.80:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
            f"drawtext=text='{m_e}':fontsize=14:fontcolor=#86EFAC:x=(w-text_w)/2:y=h-50"
        )
    elif estilo == "dark":
        # Psych/Narcissism: texto impactante grande
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"colorchannelmixer=rr={bright}:gg={bright}:bb={bright},"
            f"drawbox=y=0:color=black@0.80:width=iw:height=100:t=fill,"
            f"drawbox=y=ih-80:color=black@0.80:width=iw:height=80:t=fill,"
            f"drawbox=x=14:y=18:color=#EF4444:width=12:height=12:t=fill,"
            f"drawtext=text='LIVE · Psychology':fontsize=18:fontcolor=#EF4444:x=36:y=15:bold=1,"
            f"drawtext=text='{t_e}':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=h*0.40:bold=1:shadowcolor=#000:shadowx=3:shadowy=3,"
            f"drawtext=text='{m_e}':fontsize=14:fontcolor=#CBD5E1:x=(w-text_w)/2:y=h-50"
        )
    elif estilo == "psych":
        # Psych2Go: número grande em destaque
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"colorchannelmixer=rr={bright}:gg={bright}:bb={bright},"
            f"drawbox=y=0:color=black@0.75:width=iw:height=100:t=fill,"
            f"drawbox=y=ih-80:color=black@0.75:width=iw:height=80:t=fill,"
            f"drawtext=text='{t_e}':fontsize=34:fontcolor=white:x=(w-text_w)/2:y=h*0.42:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
            f"drawtext=text='{m_e}':fontsize=14:fontcolor=#A5B4FC:x=(w-text_w)/2:y=h-50"
        )
    else:  # nature/lofi/default — Jason Stephenson minimal
        hz = hz_label or "528Hz"
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"colorchannelmixer=rr={bright}:gg={bright}:bb={bright},"
            f"drawbox=y=0:color=black@0.65:width=iw:height=100:t=fill,"
            f"drawbox=y=ih-80:color=black@0.65:width=iw:height=80:t=fill,"
            f"drawtext=text='{hz}':fontsize=44:fontcolor=#818CF8:x=(w-text_w)/2:y=14:bold=1,"
            f"drawtext=text='{t_e}':fontsize=30:fontcolor=white@0.9:x=(w-text_w)/2:y=h*0.79:shadowcolor=#000:shadowx=2:shadowy=2,"
            f"drawtext=text='{m_e}':fontsize=14:fontcolor=#94A3B8:x=(w-text_w)/2:y=h-50"
        )
    
    out = TMP/f"slide_{estilo}_{idx:03d}.mp4"
    subprocess.run([
        "ffmpeg","-y","-loop","1","-i",str(img_p),"-vf",vf,
        "-t","60","-c:v","libx264","-preset","fast","-tune","stillimage",
        "-pix_fmt","yuv420p","-r","30","-an",str(out)
    ], capture_output=True, timeout=180)
    return out if out.exists() and out.stat().st_size > 10000 else None

if __name__ == "__main__":
    print("=== TESTE DOS 6 ESTILOS VIRAIS ===")
    testes = [
        ("The Narcissist Who Looks Like a Victim", None, "Psychology Frequencies"),
        ("528Hz Deep Sleep — Anxiety Healing", "528Hz", "Psychology Frequencies"),
        ("40Hz Gamma ADHD Focus Protocol", "40Hz", "Psychology Frequencies"),
        ("10 Signs of Anxious Attachment", None, "Daniela Coelho"),
    ]
    for titulo, hz, marca in testes:
        estilo = selecionar_estilo(titulo)
        print(f"  '{titulo[:40]}' → estilo: {estilo}")
    print("\n✅ Motor de estilos virais pronto!")
