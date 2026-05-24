#!/usr/bin/env python3
"""
production_pipeline.py — Com 6 estilos visuais dos canais virais

Usa gen_viral_images.selecionar_estilo() para cada vídeo:
  sleep/528hz    → Meditative Mind (bioluminescent forest)
  focus/adhd/40hz → Greenred Productions (sacred geometry neon)
  narcissism/dark → Psychology Dark (cinematic dramatic)
  anxiety/attach  → Psych2Go (chibi anime)
  nature/default  → Jason Stephenson (mountain lake mirror)
"""
import os, subprocess, requests, pathlib, time, re, sys

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
GROQ   = os.getenv("GROQ_API_KEY","")
SBH    = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
          "Content-Type":"application/json","Prefer":"return=minimal"}
TMP    = pathlib.Path("/tmp/prod"); TMP.mkdir(exist_ok=True)
W, H   = 1920, 1080

CANAIS = {
    "EN":{"voz":"en-US-AriaNeural",     "cor":"#818CF8","cpm":25.0,"marca":"Psychology Frequencies · Science"},
    "PT":{"voz":"pt-BR-FranciscaNeural","cor":"#7C3AED","cpm":7.0, "marca":"Daniela Coelho · Pesquisa em Psicologia"},
    "ES":{"voz":"es-MX-DaliaNeural",    "cor":"#A78BFA","cpm":9.0, "marca":"Psicología Frecuencias · Ciencia"},
    "DE":{"voz":"de-DE-KatjaNeural",    "cor":"#60A5FA","cpm":18.0,"marca":"Psychologie Frequenzen · Wissenschaft"},
    "FR":{"voz":"fr-FR-DeniseNeural",   "cor":"#F472B6","cpm":14.0,"marca":"Psychologie Fréquences · Science"},
    "JA":{"voz":"ja-JP-NanamiNeural",   "cor":"#FB7185","cpm":15.0,"marca":"サイコロジー周波数 · 科学"},
    "KO":{"voz":"ko-KR-SunHiNeural",    "cor":"#FBBF24","cpm":12.0,"marca":"심리학 주파수 · 과학"},
    "IT":{"voz":"it-IT-ElsaNeural",     "cor":"#34D399","cpm":12.0,"marca":"Psicologia Frequenze · Scienza"},
}

# Mapa de palavras-chave → estilo visual do canal viral
ESTILO_MAP = {
    "sleep":"sleep","sono":"sleep","528hz":"sleep","432hz":"sleep","396hz":"sleep","174hz":"sleep",
    "focus":"focus","foco":"focus","adhd":"focus","tdah":"focus","40hz":"focus","gamma":"focus",
    "narcissism":"dark","narcisismo":"dark","gaslighting":"dark","abuse":"dark","trauma":"dark",
    "manipulat":"dark","toxic":"dark","abuse":"dark","narcis":"dark",
    "anxious":"psych","ansioso":"psych","apego":"psych","attachment":"psych","perfecti":"psych",
    "burnout":"psych","loneliness":"psych","solidão":"psych","depression":"psych","depressão":"psych",
}

ESTILOS_IMG = {
    "sleep":  "masterpiece 8K ultra HD photo dark bioluminescent forest night glowing blue purple mushrooms fireflies misty atmosphere mirror lake no text no people ### text watermark nsfw",
    "focus":  "sacred geometry mandala glowing neon green electric blue pure black background flower of life metatron cube fractal no text no people ### text watermark nsfw",
    "dark":   "dramatic dark cinematic background purple red tones silhouette psychology mask concept shadow light contrast moody ultra HD no text no real faces ### text watermark nsfw",
    "psych":  "kawaii chibi anime psychology student thoughtful expression soft purple blue gradient background floating icons clean digital art no text ### text watermark nsfw",
    "nature": "ultra HD dark blue serene mountain lake midnight perfect mirror reflection full moon aurora borealis mist absolute stillness no text no people ### text watermark nsfw",
    "lofi":   "anime cozy night bedroom girl studying desk rainy window city lights warm lamp books coffee Studio Ghibli no text ### text watermark nsfw",
}

TEMAS = [
    {"en":"covert narcissism victimhood","hz":"528Hz","seed":9001,
     "titulos":{"EN":"The Narcissist Who Looks Like a Victim","PT":"O Narcisista Que Parece Vítima",
                "ES":"El Narcisista Que Parece Víctima","DE":"Der Narzisst Wie Ein Opfer",
                "FR":"Le Narcissiste Ressemble À Une Victime","JA":"被害者に見える自己愛者",
                "KO":"피해자처럼 보이는 나르시시스트","IT":"Il Narcisista Sembra Una Vittima"}},
    {"en":"528hz cortisol stress reduction","hz":"528Hz","seed":9334,
     "titulos":{"EN":"528Hz Reduces Cortisol — The Science","PT":"528Hz Reduz Cortisol — Ciência",
                "ES":"528Hz Reduce Cortisol — La Ciencia","DE":"528Hz Reduziert Cortisol",
                "FR":"528Hz Réduit le Cortisol — Science","JA":"528Hzコルチゾール減少科学",
                "KO":"528Hz 코르티솔 감소 과학","IT":"528Hz Riduce il Cortisolo"}},
    {"en":"anxious attachment sleep","hz":"432Hz","seed":9667,
     "titulos":{"EN":"Anxious Attachment Hijacks Your Sleep","PT":"Apego Ansioso Sequestra o Sono",
                "ES":"El Apego Ansioso Roba tu Sueño","DE":"Ängstliche Bindung Raubt Schlaf",
                "FR":"L'Attachement Anxieux Vole le Sommeil","JA":"不安型愛着が睡眠を奪う",
                "KO":"불안 애착이 수면을 방해한다","IT":"L'Attaccamento Ansioso Ruba Il Sonno"}},
    {"en":"ADHD 40hz gamma waves","hz":"40Hz","seed":4001,
     "titulos":{"EN":"40Hz Gamma Improves ADHD Focus 23%","PT":"40Hz Gamma Melhora TDAH 23%",
                "ES":"40Hz Gamma Mejora TDAH 23%","DE":"40Hz Gamma ADHS 23% Besser",
                "FR":"40Hz Gamma Améliore TDAH 23%","JA":"40Hz ADHD改善23%",
                "KO":"40Hz 감마 ADHD 23% 향상","IT":"40Hz Gamma ADHD 23% Meglio"}},
    {"en":"burnout exhaustion nervous system","hz":None,"seed":8001,
     "titulos":{"EN":"Burnout Doesn't Recover With Rest","PT":"Burnout Não Melhora Com Descanso",
                "ES":"El Burnout No Cura Con Descanso","DE":"Burnout Erholt Nicht Mit Ruhe",
                "FR":"Le Burnout Ne Guérit Pas Au Repos","JA":"バーンアウトは休養で回復しない",
                "KO":"번아웃은 휴식으로 회복 안 된다","IT":"Il Burnout Non Guarisce Col Riposo"}},
]

def selecionar_estilo(titulo):
    t = titulo.lower()
    for kw, estilo in ESTILO_MAP.items():
        if kw in t: return estilo
    return "nature"

def pubmed(q):
    try:
        r = requests.get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={requests.utils.quote(q)}&retmax=1&retmode=json",timeout=7)
        pmids = r.json().get("esearchresult",{}).get("idlist",[])
        if pmids:
            r2 = requests.get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmids[0]}&retmode=json",timeout=7)
            doc = r2.json().get("result",{}).get(pmids[0],{})
            a=(doc.get("authors",[{}]) or [{}])[0].get("name","")
            return f"{a} ({doc.get('pubdate','')[:4]}), PubMed"
    except: pass
    return "Research (NCBI)"

def img(estilo, seed):
    prompt = ESTILOS_IMG.get(estilo, ESTILOS_IMG["nature"])
    url = (f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt[:400])}"
           f"?model=flux&width={W}&height={H}&seed={seed}&nologo=true&enhance=true")
    try:
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and len(r.content) > 20000: return r.content
    except: pass
    return None

def freq(hz_str):
    hz = int(hz_str.replace("Hz","")) if hz_str else 528
    ao = TMP/f"f{hz}.aac"
    if ao.exists() and ao.stat().st_size > 30000: return ao
    hz_r = hz + (4 if hz < 200 else 8)
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i",f"sine=frequency={hz}:duration=600",
        "-f","lavfi","-i",f"sine=frequency={hz_r}:duration=600",
        "-filter_complex","[0:a]volume=0.04[l];[1:a]volume=0.04[r];[l][r]amerge=inputs=2[out]",
        "-map","[out]","-c:a","aac","-b:a","128k",str(ao)], capture_output=True, timeout=90)
    return ao if ao.exists() else None

def tts(texto, voz, out):
    s=". ".join(x.strip() for x in texto.replace('\n',' ').split('.') if x.strip())
    subprocess.run(["edge-tts",f"--voice={voz}","--rate=+32%",f"--text={s}",f"--write-media={out}"],
                   capture_output=True, timeout=60)
    return pathlib.Path(out).exists()

def render(img_p, voz_p, freq_p, titulo, marca, cor, estilo, hz_label, idioma, idx):
    mix=TMP/f"mix_{idioma}_{idx}.aac"
    if freq_p and freq_p.exists():
        subprocess.run(["ffmpeg","-y","-i",str(voz_p),"-i",str(freq_p),
            "-filter_complex","[0:a]volume=1[v];[1:a]volume=0.12[f];[v][f]amix=inputs=2:duration=first[out]",
            "-map","[out]","-c:a","aac","-b:a","128k",str(mix)],capture_output=True,timeout=60)
    else: mix=voz_p
    
    dur_r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(mix)],capture_output=True,timeout=8)
    try: dur=min(float(dur_r.stdout.strip())+0.5,59.0)
    except: dur=55.0
    
    t_e=titulo[:52].replace("'",r"\'")
    m_e=marca.replace("'",r"\'")
    hz=hz_label or "528Hz"
    
    bright={"sleep":"0.55","focus":"0.50","dark":"0.52","psych":"0.60","nature":"0.55","lofi":"0.62"}.get(estilo,"0.60")
    
    if estilo=="sleep":
        vf=(f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"colorchannelmixer=rr={bright}:gg={bright}:bb={bright},"
            f"drawbox=y=0:color=black@0.70:width=iw:height=120:t=fill,"
            f"drawbox=y=ih-78:color=black@0.70:width=iw:height=78:t=fill,"
            f"drawtext=text='{hz}':fontsize=66:fontcolor=#FFD700:x=(w-text_w)/2:y=14:bold=1:shadowcolor=#000:shadowx=3:shadowy=3,"
            f"drawtext=text='BINAURAL DELTA 4Hz':fontsize=22:fontcolor=#FCD34D@0.85:x=(w-text_w)/2:y=90,"
            f"drawtext=text='{t_e}':fontsize=30:fontcolor=white@0.9:x=(w-text_w)/2:y=h*0.78:shadowcolor=#000:shadowx=2:shadowy=2,"
            f"drawtext=text='{m_e}':fontsize=14:fontcolor=#94A3B8:x=(w-text_w)/2:y=h-50")
    elif estilo=="focus":
        vf=(f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"colorchannelmixer=rr={bright}:gg={bright}:bb={bright},"
            f"drawbox=y=0:color=black@0.75:width=iw:height=110:t=fill,"
            f"drawbox=y=ih-78:color=black@0.75:width=iw:height=78:t=fill,"
            f"drawtext=text='{hz}':fontsize=80:fontcolor=#00FF88:x=(w-text_w)/2:y=8:bold=1:shadowcolor=#003:shadowx=4:shadowy=4,"
            f"drawtext=text='GAMMA WAVES · FOCUS':fontsize=20:fontcolor=#00CC66:x=(w-text_w)/2:y=96,"
            f"drawtext=text='{t_e}':fontsize=28:fontcolor=white:x=(w-text_w)/2:y=h*0.80:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
            f"drawtext=text='{m_e}':fontsize=14:fontcolor=#86EFAC:x=(w-text_w)/2:y=h-50")
    elif estilo=="dark":
        vf=(f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"colorchannelmixer=rr={bright}:gg={bright}:bb={bright},"
            f"drawbox=y=0:color=black@0.82:width=iw:height=100:t=fill,"
            f"drawbox=y=ih-78:color=black@0.82:width=iw:height=78:t=fill,"
            f"drawbox=x=14:y=18:color=#EF4444:width=12:height=12:t=fill,"
            f"drawtext=text='LIVE · Psychology':fontsize=18:fontcolor=#EF4444:x=36:y=15:bold=1,"
            f"drawtext=text='{t_e}':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=h*0.40:bold=1:shadowcolor=#000:shadowx=3:shadowy=3,"
            f"drawtext=text='{m_e}':fontsize=14:fontcolor=#CBD5E1:x=(w-text_w)/2:y=h-50")
    else:  # nature/psych/lofi
        vf=(f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"colorchannelmixer=rr={bright}:gg={bright}:bb={bright},"
            f"drawbox=y=0:color=black@0.70:width=iw:height=88:t=fill,"
            f"drawbox=y=ih-78:color=black@0.70:width=iw:height=78:t=fill,"
            f"drawbox=x=14:y=18:color=#EF4444:width=10:height=10:t=fill,"
            f"drawtext=text='LIVE · {hz}':fontsize=18:fontcolor={cor}:x=32:y=15:bold=1,"
            f"drawtext=text='{t_e}':fontsize=30:fontcolor=white:x=(w-text_w)/2:y=h*0.42:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
            f"drawtext=text='{m_e}':fontsize=14:fontcolor=#94A3B8:x=(w-text_w)/2:y=h-50")
    
    out=TMP/f"vid_{idioma}_{idx:03d}.mp4"
    subprocess.run(["ffmpeg","-y","-loop","1","-i",str(img_p),"-i",str(mix),
        "-vf",vf,"-t",str(dur),"-c:v","libx264","-preset","fast",
        "-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","128k","-shortest",str(out)],
        capture_output=True,timeout=300)
    return out if out.exists() and out.stat().st_size>50000 else None

def groq_gen(titulo, cit, idioma):
    if not GROQ: return None, None
    lang={"EN":"English","PT":"Portuguese Brazilian","ES":"Spanish","DE":"German",
           "FR":"French","JA":"Japanese","KO":"Korean","IT":"Italian"}.get(idioma,"English")
    try:
        r=requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":
                    f"YouTube Short script in {lang}. Title: {titulo}\n"
                    f"Citation: {cit}\n"
                    f"Hook (cite author), fact, takeaway. 70 words. No hashtags.\n"
                    f"TAGS: 8 SEO keywords comma-separated"}],
                  "max_tokens":250,"temperature":0.72},timeout=20)
        if r.status_code==200:
            txt=r.json()["choices"][0]["message"]["content"]
            tm=re.search(r'TAGS[:\s]+(.*?)$',txt,re.IGNORECASE|re.MULTILINE)
            tags=tm.group(1).strip() if tm else "psychology,528hz"
            scr=re.sub(r'TAGS[:\s]+.*','',txt,flags=re.IGNORECASE|re.MULTILINE).strip()
            return scr, tags
    except: pass
    return None, None

def save(titulo, script, tags, idioma, mp4=""):
    if not SB_KEY: return
    requests.post(f"{SB_URL}/rest/v1/en_channel_queue",headers=SBH,
        json={"titulo_en":titulo[:100],"script_en":script,
              "voz_en":CANAIS.get(idioma,{}).get("voz","en-US-AriaNeural"),
              "canal_destino":"UCyCkIpsVgME9yCj_oXJFheA",
              "rpm_estimado":CANAIS.get(idioma,{}).get("cpm",10.0),
              "status":"mp4_ready" if mp4 else "pending"},timeout=8)

def run():
    print("=== PRODUCTION PIPELINE — Estilos Virais ===\n")
    total=0
    for t_idx, tema in enumerate(TEMAS):
        titulo_en=tema["titulos"]["EN"]
        estilo=selecionar_estilo(titulo_en)
        print(f"\n[{t_idx+1}] {titulo_en[:50]} → estilo: {estilo}")
        cit=pubmed(tema["en"])
        print(f"  PubMed: {cit[:55]}")
        img_d=img(estilo, tema["seed"])
        img_p=None
        if img_d: img_p=TMP/f"bg_{t_idx}.jpg"; img_p.write_bytes(img_d)
        fa=freq(tema.get("hz","528Hz"))
        for idioma, cfg in CANAIS.items():
            titulo=tema["titulos"].get(idioma, titulo_en)
            script, tags=groq_gen(titulo, cit, idioma)
            if not script: continue
            voz_p=TMP/f"voz_{idioma}_{t_idx}.mp3"
            ok=tts(script, cfg["voz"], str(voz_p))
            mp4=""
            if ok and img_p:
                v=render(img_p, voz_p, fa, titulo, cfg["marca"], cfg["cor"], estilo, tema.get("hz"), idioma, t_idx)
                if v: mp4=str(v); total+=1; print(f"  ✅ [{idioma}] {estilo} {v.stat().st_size//1024}KB")
                else: print(f"  📝 [{idioma}]")
            else: print(f"  📝 [{idioma}]")
            save(titulo, script, tags, idioma, mp4)
            time.sleep(1.2)
        time.sleep(4)
    print(f"\n✅ {total} vídeos com estilos dos canais virais")

if __name__=="__main__":
    run()
