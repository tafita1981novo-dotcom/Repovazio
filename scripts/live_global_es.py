#!/usr/bin/env python3
"""
live_global_es.py — 24/7 Spanish Stream targeting MX/ES/CO/AR
CPM: $5-15 | 500M+ hablantes | keywords: 528hz dormir, frecuencia curación
"""
import os, time, subprocess, pathlib, requests, textwrap, hashlib, threading
from datetime import datetime, timezone, timedelta

STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY_ES", os.getenv("YOUTUBE_STREAM_KEY", ""))
GROQ_KEY   = os.getenv("GROQ_API_KEY", "")
RTMP_URL   = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
W, H = 1280, 720
TMP = pathlib.Path("/tmp/live_es")
TMP.mkdir(exist_ok=True)

STREAMS_ES = {
    "dormir": {
        "hz": 528, "hz_right": 532, "hz_base": 174,
        "title": "🔴 528Hz DORMIR PROFUNDO | Ansiedad y Apego | Psicología EN VIVO",
        "color": "#050520", "text_color": "#818CF8",
        "brand": "Daniela Coelho · Investigación y Contenido en Psicología",
        "content": [
            ("Apego ansioso y sueño", "El apego ansioso hiperactivia la amígdala durante el sueño. Por eso te despiertas a las 3am pensando en alguien. — Ainsworth"),
            ("Cortisol e insomnio", "La ansiedad crónica eleva el cortisol y suprime la melatonina. El 40% de los ansiosos tienen disrupciones del sueño. — Sapolsky"),
            ("Narcisismo encubierto", "El narcisista más peligroso no parece arrogante. Parece víctima. — Malkin/Harvard"),
            ("Trauma y sueño REM", "El trauma no procesado interrumpe los ciclos REM. El cuerpo ensaya las amenazas pasadas por la noche. — van der Kolk"),
            ("528Hz y bienestar", "La frecuencia 528Hz se ha asociado con reducción de hormonas de estrés en investigación revisada. — NCBI"),
            ("Apego seguro y descanso", "Las personas con apego seguro duermen 1.2 horas más en promedio. — Johnson/EFT"),
            ("Gaslighting y recuperación", "Después del gaslighting, confiar en tu propia percepción lleva tiempo. El sistema nervioso necesita experiencias correctivas."),
            ("Síndrome del impostor", "Cuanto más competente eres, más sabes lo que no sabes. La duda no es señal — es metacognición. — Dunning/Kruger"),
        ]
    },
    "foco": {
        "hz": 40, "hz_right": 40, "hz_base": 10,
        "title": "🔴 40Hz CONCENTRACIÓN | TDAH y Procrastinación | Neurociencia LIVE",
        "color": "#020F04", "text_color": "#34D399",
        "brand": "Daniela Coelho · Investigación y Contenido en Psicología",
        "content": [
            ("40Hz y TDAH", "La estimulación gamma de 40Hz mejora la memoria de trabajo un 23% en adultos con TDAH. — MIT 2024"),
            ("Procrastinación es dolor", "Procrastinar activa el córtex cingulado anterior — la misma región del dolor físico. — Sirois/Sheffield"),
            ("Dopamina y TDAH", "El TDAH es desregulación de dopamina, no fallo de atención. La tarea debe activar el circuito de recompensa. — Barkley"),
            ("Estado de flujo", "En el estado de flujo, el córtex prefrontal se desactiva parcialmente. Piensas menos y haces más. — Csikszentmihalyi"),
            ("Ritmo ultradiano", "25 minutos de foco + 5 de descanso corresponde al ciclo ultradiano natural del cerebro. No es técnica — es biología."),
            ("Autocompasión y TDAH", "La autocrítica intensa empeora los síntomas del TDAH. La autocompasión mejora la función ejecutiva. — Neff"),
            ("Ondas gamma y memoria", "Las oscilaciones gamma están asociadas al procesamiento de información de alta velocidad y la potenciación a largo plazo."),
            ("TDAH y rechazo", "La disforia sensible al rechazo en el TDAH es intensa pero subdiagnosticada. No es debilidad — es neurobiología. — Dodson"),
        ]
    },
    "prime": {
        "hz": 963, "hz_right": 971, "hz_base": 396,
        "title": "🔴 963Hz LIBERACIÓN | Ansiedad, Narcisismo y Apego | Psicología EN VIVO",
        "color": "#120005", "text_color": "#FB7185",
        "brand": "Daniela Coelho · Investigación y Contenido en Psicología",
        "content": [
            ("Ansiedad y amígdala", "Tu amígdala detecta amenazas 33ms antes de que seas consciente de ellas. No es exageración — es evolución. — LeDoux"),
            ("Gaslighting identificación", "Cuando confías más en su versión de la realidad que en la tuya, el gaslighting ya funcionó. — Freyd"),
            ("Apego ansioso estadísticas", "El 62% de los adultos tienen apego inseguro. La mayoría nunca lo supo. Es la norma, no la excepción."),
            ("963Hz activación", "963Hz se asocia con activación, claridad y reconexión con el procesamiento intuitivo. — Tradición Solfeggio"),
            ("Adicción a validación", "Los likes activan el mismo circuito de recompensa que la cocaína. Refuerzo variable — el más adictivo. — Skinner"),
            ("Narcisismo encubierto", "La persona más tóxica de tu vida probablemente no parece tóxica. Parece víctima. — Malkin/Harvard"),
            ("Impostor peak", "El síndrome del impostor es más común en los más competentes. Es el precio de la metacognición."),
            ("Liberación emocional", "Sanar el trauma no es olvidar. Es que el sistema nervioso aprenda que la amenaza ya pasó. — van der Kolk"),
        ]
    },
}

def utc_hour(): return datetime.now(timezone.utc).hour

def select_stream():
    h = utc_hour()
    if h in [0,1,2,3,4,5,6,7,8,9,10,11]: return "dormir", STREAMS_ES["dormir"]
    elif h in [12,13,14,15,16,17]: return "foco", STREAMS_ES["foco"]
    else: return "prime", STREAMS_ES["prime"]

def gen_audio(hz, hz_r, hz_b, mins=30):
    out = TMP / f"aud_{hz}_{mins}.aac"
    if out.exists() and out.stat().st_size > 50000: return out
    dur = mins * 60
    cmd = ["ffmpeg","-y",
        "-f","lavfi","-i",f"sine=frequency={hz}:duration={dur}",
        "-f","lavfi","-i",f"sine=frequency={hz_r}:duration={dur}",
        "-f","lavfi","-i",f"sine=frequency={hz_b}:duration={dur}",
        "-f","lavfi","-i",f"anoisesrc=color=pink:duration={dur}",
        "-filter_complex",
        "[0:a]volume=0.035[l];[1:a]volume=0.035[r];[2:a]volume=0.012[b];[3:a]volume=0.004[p];"
        "[l][r]amerge=inputs=2[bin];[bin][b][p]amix=inputs=3:duration=longest[out]",
        "-map","[out]","-c:a","aac","-b:a","192k","-ar","44100",str(out)]
    subprocess.run(cmd, capture_output=True, timeout=120)
    return out if out.exists() else None

def get_img(tema, color, seed):
    p = (f"masterpiece, ultra HD cinematic dark {color} background, {tema} psychology, "
         f"aurora borealis particles, extremely calming, no text no people ### text watermark nsfw blurry")
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(p[:380])}?model=flux&width={W}&height={H}&seed={seed}&nologo=true"
    try:
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and len(r.content) > 10000: return r.content
    except: pass
    return None

def make_slide(img_p, cfg, tema, insight, idx, total, out):
    hz = cfg["hz"]; tc = cfg["text_color"]
    brand = cfg["brand"].replace("'",r"\'"); tema_e = tema.replace("'",r"\'")
    lines = textwrap.wrap(insight, 42)[:2]
    l1 = (lines[0] if lines else "").replace("'",r"\'")
    l2 = (lines[1] if len(lines)>1 else "").replace("'",r"\'")
    pw = max(4, int(W * idx / max(total,1)))
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"colorchannelmixer=rr=0.65:gg=0.65:bb=0.65,"
        f"drawbox=y=0:color=black@0.88:width=iw:height=66:t=fill,"
        f"drawbox=y=ih-70:color=black@0.92:width=iw:height=70:t=fill,"
        f"drawbox=y=ih-4:color={tc}@0.85:width={pw}:height=4:t=fill,"
        f"drawbox=x=12:y=16:color=#EF4444:width=10:height=10:t=fill,"
        f"drawtext=text='{hz}Hz':fontsize=22:fontcolor={tc}:x=30:y=12:bold=1:shadowcolor=black:shadowx=1:shadowy=1,"
        f"drawtext=text='EN VIVO':fontsize=13:fontcolor=#EF4444:x=30:y=38:bold=1,"
        f"drawtext=text='{tema_e}':fontsize=16:fontcolor={tc}@0.9:x=(w-text_w)/2:y=h*0.34:shadowcolor=black:shadowx=1:shadowy=1,"
        f"drawtext=text='{l1}':fontsize=25:fontcolor=white:x=(w-text_w)/2:y=h*0.41:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
    )
    if l2: vf += f"drawtext=text='{l2}':fontsize=25:fontcolor=white:x=(w-text_w)/2:y=h*0.41+37:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
    vf += f"drawtext=text='{brand}':fontsize=12:fontcolor=#94A3B8:x=(w-text_w)/2:y=h-45"
    cmd = ["ffmpeg","-y","-loop","1","-i",str(img_p),"-vf",vf,
           "-t","60","-c:v","libx264","-preset","fast","-tune","stillimage",
           "-pix_fmt","yuv420p","-r","30","-an",str(out)]
    subprocess.run(cmd, capture_output=True, timeout=180)
    return out.exists() and out.stat().st_size > 10000

def run():
    if not STREAM_KEY:
        print("YOUTUBE_STREAM_KEY_ES not set. Add to GitHub Secrets.")
        return
    key, cfg = select_stream()
    content = cfg["content"]
    print(f"=== 🌍 GLOBAL ES LIVE | {cfg['hz']}Hz {key.upper()} ===")
    print(f"    MX/ES/CO/AR | CPM: $5-15")
    audio = gen_audio(cfg["hz"], cfg["hz_right"], cfg["hz_base"])
    slides, concat_f = [], TMP / "pl_es.txt"
    for i in range(4):
        tema, base = content[i % len(content)]
        seed = int(hashlib.md5(f"es_{key}_{i}".encode()).hexdigest()[:8], 16)
        img_data = get_img(tema, cfg["color"], seed)
        if not img_data: continue
        img_p = TMP / f"bg_{key}_{seed}.jpg"; img_p.write_bytes(img_data)
        sl = TMP / f"sl_es_{key}_{i}.mp4"
        if make_slide(img_p, cfg, tema, base, i, len(content), sl):
            slides.append(sl); print(f"  ✅ [{i+1}] {tema[:40]}")
        time.sleep(2)
    if not slides: return
    with open(concat_f,"w") as f: [f.write(f"file '{s.resolve()}'\n") for s in slides]
    audio_src = ["-stream_loop","-1","-i",str(audio)] if audio and audio.exists() \
                else ["-f","lavfi","-i",f"sine=frequency={cfg['hz']}:duration=999999"]
    proc = subprocess.Popen(["ffmpeg","-y",
        "-f","concat","-safe","0","-stream_loop","-1","-i",str(concat_f),
        *audio_src,"-c:v","libx264","-preset","veryfast","-tune","stillimage",
        "-b:v","3500k","-maxrate","3500k","-bufsize","7000k","-g","60","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","192k","-ar","44100","-ac","2","-f","flv",RTMP_URL])
    def bg(start=4):
        idx=start
        while proc.poll() is None:
            time.sleep(55)
            tema,base = content[idx%len(content)]
            seed = int(hashlib.md5(f"es_{key}_{idx}".encode()).hexdigest()[:8],16)
            img_data = get_img(tema, cfg["color"], seed)
            if img_data:
                img_p = TMP/f"bg_{key}_{seed}.jpg"; img_p.write_bytes(img_data)
                sl = TMP/f"sl_es_{key}_{idx}.mp4"
                if make_slide(img_p,cfg,tema,base,idx%len(content),len(content),sl):
                    with open(concat_f,"a") as f: f.write(f"file '{sl.resolve()}'\n")
                    print(f"  + {tema[:35]}")
            for old in sorted(TMP.glob(f"sl_es_{key}_*.mp4"))[:-6]: old.unlink(missing_ok=True)
            idx+=1
    threading.Thread(target=bg,daemon=True).start()
    try: proc.wait()
    except KeyboardInterrupt: proc.terminate()

if __name__ == "__main__":
    run()
