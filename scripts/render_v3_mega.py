#!/usr/bin/env python3
"""
render_v3_mega.py — Pipeline Definitivo com Gemini
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HIERARQUIA DE QUALIDADE:
  1. Veo 3 clip disponível → usa como fundo (melhor)
  2. Imagen 3 disponível   → usa como fundo estático (ótimo)
  3. Estilos virais analisados → fallback (bom)

FLUXO:
  gemini_mega_pipeline.py → gera imagens/vídeos
  render_v3_mega.py       → monta vídeo final com overlays
  canal_dark_pipeline.py  → publica com Daniela lateral

RESULTADO: vídeos de qualidade cinematográfica grátis
"""
import os, subprocess, requests, pathlib, time, json
import urllib3; urllib3.disable_warnings()

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
GROQ   = os.getenv("GROQ_API_KEY","")
GEMINI = os.getenv("GEMINI_API_KEY","AIzaSyDzCea_65Al-vy342xslBSVmKPv0qzTuXY")
SBH    = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
          "Content-Type":"application/json","Prefer":"return=minimal"}
TMP    = pathlib.Path("/tmp/render_v3"); TMP.mkdir(exist_ok=True)
MEGA   = pathlib.Path("/tmp/gemini_mega")
GH_RAW = "https://raw.githubusercontent.com/tafita81/Repovazio/main"
W, H   = 1920, 1080

TEMAS_DARK = [
    {"id":"narcis","titulo":"O Narcisista Que Você Não Vê Vir","style":"narcisismo","hz":None},
    {"id":"burnout","titulo":"Burnout Não Começa Com Cansaço","style":"burnout","hz":None},
    {"id":"apego","titulo":"Por Que Você Escolhe Quem Te Faz Sofrer","style":"apego","hz":None},
    {"id":"528hz","titulo":"528Hz Enquanto Você Dorme","style":"sleep","hz":"528Hz"},
    {"id":"trauma","titulo":"Seu Corpo Guardou o Trauma Por Você","style":"trauma","hz":None},
]

VOZES = {
    "PT": {"voz":"pt-BR-FranciscaNeural","rate":"-13%"},
    "EN": {"voz":"en-US-AriaNeural","rate":"-10%"},
    "ES": {"voz":"es-MX-DaliaNeural","rate":"-10%"},
    "DE": {"voz":"de-DE-KatjaNeural","rate":"-8%"},
    "FR": {"voz":"fr-FR-DeniseNeural","rate":"-10%"},
}

def get_best_bg(tema_id):
    """Hierarquia: Veo3 > Imagen3 > Viral Style"""
    # 1. Veo3
    veo = MEGA/f"veo_veo_{tema_id}.mp4"
    if veo.exists() and veo.stat().st_size > 100000:
        return veo, "video"
    # 2. Imagen3
    for sufixo in [f"imagen_{tema_id}_lab", f"imagen_{tema_id}_spotlight",
                   f"imagen_{tema_id}", f"imagen_narcis_lab"]:
        img = MEGA/f"{sufixo}.jpg"
        if img.exists() and img.stat().st_size > 50000:
            return img, "image"
    # 3. Fallback estilos virais
    slug = {"narcis":"cinematic_dark","sleep":"meditative",
            "apego":"psych2go","burnout":"cinematic_dark","trauma":"cinematic_dark"}.get(tema_id,"cinematic_dark")
    viral = pathlib.Path(f"/tmp/dark/bg_{slug}.jpg")
    if viral.exists(): return viral, "image"
    return None, None

def groq_script_v3(titulo, tema_id, idioma="PT"):
    if not GROQ: return None
    lang = {"PT":"Brazilian Portuguese","EN":"English","ES":"Spanish",
            "DE":"German","FR":"French"}.get(idioma,"English")
    prompt = (
        f"Write a dark psychology YouTube short script in {lang}.\n"
        f"Title: {titulo}\n"
        f"Tone: reflective, cinematic, 1st person (researcher voice)\n"
        f"Research: PubMed + Harvard psychology literature\n\n"
        f"FORMAT (canal dark viral):\n"
        f"- Line 1: HOOK (counter-intuitive danger that looks safe)\n"
        f"- Line 2-3: Revelation with real researcher name\n"
        f"- Line 4: Neural mechanism (simple, surprising)\n"
        f"- Line 5: Counter-intuitive signal\n"
        f"- Line 6: Agency return to viewer\n"
        f"70 words total. Pure reflection. No hashtags."
    )
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":220,"temperature":0.85},
            timeout=15, verify=False)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return None

def tts(texto, voz, rate, out):
    s = ". ".join(x.strip() for x in texto.replace("\n"," ").split(".") if x.strip())
    subprocess.run(["edge-tts",f"--voice={voz}",f"--rate={rate}",
                    f"--text={s}",f"--write-media={out}"],
                   capture_output=True, timeout=60)
    return pathlib.Path(out).exists()

def dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","default=noprint_wrappers=1:nokey=1",str(p)],
                       capture_output=True, timeout=8)
    try: return float(r.stdout.strip())
    except: return 3.0

def render_v3(bg, bg_type, audio_p, titulo, out_p):
    d = min(dur(audio_p)+0.5, 59.0)
    t = titulo[:48].replace("'",r"\'")

    if bg_type == "video":
        # Usa Veo3 como fundo com loop
        vf = (
            f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"colorchannelmixer=rr=0.50:gg=0.50:bb=0.50[bg];"
            f"[bg]"
            f"drawbox=y=0:color=black@0.85:width=iw:height=88:t=fill,"
            f"drawbox=y=ih-72:color=black@0.85:width=iw:height=72:t=fill,"
            f"drawbox=x=15:y=18:color=#EF4444:width=12:height=12:t=fill,"
            f"drawtext=text='AO VIVO · psicologia.doc':fontsize=17:fontcolor=#EF4444:x=35:y=15:bold=1,"
            f"drawtext=text='Daniela Coelho · Pesquisa em Psicologia':fontsize=13:fontcolor=#94A3B8:x=35:y=40,"
            f"drawtext=text='{t}':fontsize=32:fontcolor=white:x=(w-text_w)/2:y=h*0.40:bold=1:shadowcolor=#000:shadowx=3:shadowy=3,"
            f"drawtext=text='Daniela Coelho · @psidanielacoelho':fontsize=14:fontcolor=#A78BFA:x=(w-text_w)/2:y=h-46"
        )
        cmd = ["ffmpeg","-y","-stream_loop","-1","-i",str(bg),"-i",str(audio_p),
               "-filter_complex",vf,"-map","[bg]","-map","1:a",
               "-t",str(d),"-c:v","libx264","-preset","fast","-pix_fmt","yuv420p",
               "-r","30","-c:a","aac","-b:a","128k","-shortest",str(out_p)]
    else:
        # Imagen3 como fundo estático
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"colorchannelmixer=rr=0.48:gg=0.48:bb=0.48,"
            f"drawbox=y=0:color=black@0.88:width=iw:height=88:t=fill,"
            f"drawbox=y=ih-72:color=black@0.88:width=iw:height=72:t=fill,"
            f"drawbox=x=15:y=18:color=#EF4444:width=12:height=12:t=fill,"
            f"drawtext=text='AO VIVO · psicologia.doc':fontsize=17:fontcolor=#EF4444:x=35:y=15:bold=1,"
            f"drawtext=text='Daniela Coelho · Pesquisa em Psicologia':fontsize=13:fontcolor=#94A3B8:x=35:y=40,"
            f"drawtext=text='{t}':fontsize=32:fontcolor=white:x=(w-text_w)/2:y=h*0.40:bold=1:shadowcolor=#000:shadowx=3:shadowy=3,"
            f"drawtext=text='Daniela Coelho · @psidanielacoelho':fontsize=14:fontcolor=#A78BFA:x=(w-text_w)/2:y=h-46"
        )
        cmd = ["ffmpeg","-y","-loop","1","-i",str(bg),"-i",str(audio_p),
               "-vf",vf,"-t",str(d),"-c:v","libx264","-preset","fast",
               "-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","128k","-shortest",str(out_p)]
    subprocess.run(cmd, capture_output=True, timeout=300)
    return out_p.exists() and out_p.stat().st_size > 100000

def salvar(titulo, script, mp4=""):
    if not SB_KEY: return
    requests.post(f"{SB_URL}/rest/v1/en_channel_queue", headers=SBH,
        json={"titulo_en":titulo[:100],"script_en":script,
              "voz_en":"pt-BR-FranciscaNeural",
              "canal_destino":"UCyCkIpsVgME9yCj_oXJFheA",
              "rpm_estimado":7.0,"status":"mp4_ready" if mp4 else "pending"},
        timeout=8, verify=False)

def run():
    print("=== RENDER V3 MEGA — Imagen3/Veo3 ===\n")
    total = 0

    for tema in TEMAS_DARK:
        bg, bg_type = get_best_bg(tema["id"])
        if not bg:
            # Download viral fallback
            url = f"{GH_RAW}/public/estilos_virais/cinematic_dark.jpg"
            bg = TMP/f"fallback_{tema['id']}.jpg"
            try:
                r = requests.get(url, timeout=20, verify=False)
                if r.status_code == 200: bg.write_bytes(r.content)
            except: pass
            bg_type = "image"

        if not bg or not bg.exists():
            print(f"  ⚠️  {tema['id']}: sem background"); continue

        print(f"\n  🎬 {tema['titulo'][:45]} [{bg_type}]")
        script = groq_script_v3(tema["titulo"], tema["id"], "PT")
        if not script: script = f"{tema['titulo']}.\n\nA pesquisa confirma isso.\n\nSalva este vídeo."

        voz_p = TMP/f"voz_{tema['id']}_PT.mp3"
        cfg = VOZES["PT"]
        ok_tts = tts(script, cfg["voz"], cfg["rate"], str(voz_p))
        if not ok_tts: salvar(tema["titulo"], script); continue

        out_p = TMP/f"v3_{tema['id']}.mp4"
        ok = render_v3(bg, bg_type, voz_p, tema["titulo"], out_p)
        if ok:
            print(f"     ✅ {out_p.stat().st_size//1024}KB [{bg_type}]")
            salvar(tema["titulo"], script, str(out_p)); total += 1
        else:
            salvar(tema["titulo"], script)
        time.sleep(3)

    print(f"\n  ✅ {total} vídeos V3 (Imagen3/Veo3)")

if __name__=="__main__": run()
