#!/usr/bin/env python3
"""
kwai_short_video_renderer.py — Render Short 60-90s para Kwai/TikTok/YouTube
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMATO VALIDADO (transcript Kwai Shop):
  ├── Review honesto: produto + ciência + resultado pessoal
  ├── 60-90 segundos (ideal para Kwai Shop)
  ├── CTA: "Link com desconto no Kwai Shop na bio 👆"
  └── Mesmo vídeo → YouTube + Kwai + TikTok = 3× alcance

LAYOUT (Canal Dark adaptado para produto):
  ┌─────────────────────────────────────────┐
  │ 🔴  psicologia.doc · Daniela Coelho    │ ← barra topo
  ├──────────────┬──────────────────────────│
  │   DANIELA    │  "Tomei magnésio por    │
  │   CHIBI      │   30 dias com ansiedade │
  │   lateral    │   alta. O resultado..." │ ← texto reflexivo
  ├──────────────┴──────────────────────────│
  │ LINK NA BIO 👆  Kwai Shop  YouTube     │ ← CTA barra
  └─────────────────────────────────────────┘
"""
import os, subprocess, requests, pathlib, time, json
import urllib3; urllib3.disable_warnings()

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
GROQ   = os.getenv("GROQ_API_KEY","")
SBH    = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
          "Content-Type":"application/json","Prefer":"return=minimal"}
TMP    = pathlib.Path("/tmp/kwai_vid"); TMP.mkdir(exist_ok=True)
W, H   = 1920, 1080

GH_RAW = "https://raw.githubusercontent.com/tafita81/Repovazio/main"
DANIELA_POSE = (
    "kawaii chibi anime girl, short dark bob hair, mint-green blouse, gold psi pin, "
    "holding supplement bottle, warm smile, big eyes, flat anime illustration, "
    "soft cream background, no text, no watermarks"
)

PRODUTOS = [
    {
        "id":"magnesio","nome":"Magnésio Glicinato","cat":"sono e ansiedade",
        "pubmed":"Boyle NB (2017) — magnesium supplementation reduces anxiety",
        "hook":"Tomei magnésio por 30 dias com ansiedade alta. O que aconteceu me surpreendeu.",
        "cor_cta":"#22C55E","icone":"💊",
        "tags":["magnésio ansiedade","cortisol sono","suplemento natural psicologia"],
    },
    {
        "id":"omega3","nome":"Ômega-3 DHA+EPA","cat":"cognição e humor",
        "pubmed":"Mocking RJ (2016) — omega-3 meta-analysis depression",
        "hook":"Minha névoa mental durou 2 anos. A pesquisa mostrou o motivo.",
        "cor_cta":"#3B82F6","icone":"🐟",
        "tags":["ômega-3 depressão","DHA cognição","suplemento humor"],
    },
    {
        "id":"ashwagandha","nome":"Ashwagandha KSM-66","cat":"burnout e cortisol",
        "pubmed":"Chandrasekhar K (2012) — ashwagandha cortisol stress",
        "hook":"Meu cortisol estava 28% acima do normal. Isso é o que mudei.",
        "cor_cta":"#F59E0B","icone":"🌿",
        "tags":["ashwagandha burnout","adaptógeno estresse","cortisol alto"],
    },
    {
        "id":"lteanina","nome":"L-Teanina + Cafeína","cat":"foco e TDAH",
        "pubmed":"Nathan PJ (2006) — L-theanine attention performance",
        "hook":"TDAH sem remédio. A combinação que o MIT pesquisou funciona assim.",
        "cor_cta":"#8B5CF6","icone":"🧠",
        "tags":["l-teanina foco","TDAH natural","teanina cafeína estudo"],
    },
]

def gerar_daniela(prod_id, seed):
    p = TMP/f"daniela_{prod_id}.jpg"
    if p.exists() and p.stat().st_size > 8000: return p
    prompt = f"{DANIELA_POSE} ### text watermark nsfw blurry"
    url = (f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt[:400])}"
           f"?model=flux&width=576&height=1024&seed={seed}&nologo=true")
    try:
        r = requests.get(url, timeout=50, verify=False)
        if r.status_code == 200 and len(r.content) > 8000:
            p.write_bytes(r.content); return p
    except: pass
    return None

def gerar_bg(estilo="dark"):
    p = TMP/f"bg_{estilo}.jpg"
    if p.exists() and p.stat().st_size > 10000: return p
    url = f"{GH_RAW}/public/estilos_virais/cinematic_dark.jpg"
    try:
        r = requests.get(url, timeout=20, verify=False)
        if r.status_code == 200:
            p.write_bytes(r.content); return p
    except: pass
    return None

def groq_script(produto, idioma="PT"):
    if not GROQ: return None
    lang = "Portuguese Brazilian" if idioma=="PT" else "English"
    hook_en = produto["hook"].replace("Tomei","I took").replace("Minha","My").replace("Meu","My").replace("O que aconteceu me surpreendeu","What happened surprised me")
    hook = produto["hook"] if idioma=="PT" else hook_en
    prompt = (
        f"Write a 75-second Kwai Shop / TikTok / YouTube Short script in {lang}.\n"
        f"Product: {produto['nome']} (for {produto['cat']})\n"
        f"Hook: \"{hook}\"\n"
        f"Research: {produto['pubmed']}\n\n"
        f"FORMAT (validado para Kwai Shop — converte muito):\n"
        f"1. HOOK (linha acima, chocante e pessoal)\n"
        f"2. O QUÊ a pesquisa confirma (citar autor e ano)\n"
        f"3. COMO eu usei e o que senti (honesto, específico)\n"
        f"4. QUANTO: dosagem segura sugerida + sempre consultar médico\n"
        f"5. CTA: 'Link na bio 👆 com desconto no Kwai Shop'\n"
        f"REGRAS: NUNCA 'cura/trata'. SEMPRE 'estudos mostram/pode ajudar'.\n"
        f"Total: 80-90 palavras. Tom: pessoal, honesto, baseado em ciência."
    )
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":250,"temperature":0.82},
            timeout=15, verify=False)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return None

def tts(texto, voz, out, rate="-10%"):
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

def render_kwai_short(bg_p, daniela_p, audio_p, produto, out_p):
    """Render 16:9 estilo canal dark adaptado para review de produto"""
    d = min(dur(audio_p)+0.5, 90.0)
    nm = produto["nome"][:30].replace("'",r"\'")
    ct = produto["cat"][:25].replace("'",r"\'")
    cor = produto["cor_cta"]
    ico = produto["icone"]

    if daniela_p and daniela_p.exists():
        vf = (
            f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"colorchannelmixer=rr=0.45:gg=0.45:bb=0.45[bg];"
            f"[1:v]scale=480:960:force_original_aspect_ratio=decrease[char];"
            f"[bg][char]overlay=15:h/2-480[comp];"
            f"[comp]"
            f"drawbox=y=0:color=black@0.90:width=iw:height=90:t=fill,"
            f"drawbox=y=ih-80:color=black@0.90:width=iw:height=80:t=fill,"
            f"drawbox=x=15:y=18:color=#EF4444:width=12:height=12:t=fill,"
            f"drawtext=text='AO VIVO · psicologia.doc':fontsize=17:fontcolor=#EF4444:x=35:y=15:bold=1,"
            f"drawtext=text='Daniela Coelho · Pesquisa em Psicologia':fontsize=14:fontcolor=#94A3B8:x=35:y=40,"
            f"drawtext=text='{ico} {nm}':fontsize=30:fontcolor=white:x=510:y=110:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
            f"drawtext=text='{ct}':fontsize=18:fontcolor=#CBD5E1:x=510:y=150,"
            f"drawtext=text='LINK NA BIO 👆 · Kwai Shop · YouTube':fontsize=16:fontcolor={cor}:x=(w-text_w)/2:y=h-52:bold=1"
        )
        cmd = ["ffmpeg","-y","-loop","1","-i",str(bg_p),"-loop","1","-i",str(daniela_p),
               "-i",str(audio_p),"-filter_complex",vf,
               "-map","[comp]","-map","2:a",
               "-t",str(d),"-c:v","libx264","-preset","fast","-pix_fmt","yuv420p",
               "-r","30","-c:a","aac","-b:a","128k","-shortest",str(out_p)]
    else:
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"colorchannelmixer=rr=0.45:gg=0.45:bb=0.45,"
            f"drawbox=y=0:color=black@0.90:width=iw:height=90:t=fill,"
            f"drawbox=y=ih-80:color=black@0.90:width=iw:height=80:t=fill,"
            f"drawbox=x=15:y=18:color=#EF4444:width=12:height=12:t=fill,"
            f"drawtext=text='AO VIVO · psicologia.doc':fontsize=17:fontcolor=#EF4444:x=35:y=15:bold=1,"
            f"drawtext=text='{ico} {nm}':fontsize=34:fontcolor=white:x=(w-text_w)/2:y=h/2-60:bold=1,"
            f"drawtext=text='{ct}':fontsize=20:fontcolor=#CBD5E1:x=(w-text_w)/2:y=h/2-10,"
            f"drawtext=text='LINK NA BIO 👆 · Kwai Shop':fontsize=18:fontcolor={cor}:x=(w-text_w)/2:y=h-50:bold=1"
        )
        cmd = ["ffmpeg","-y","-loop","1","-i",str(bg_p),"-i",str(audio_p),
               "-vf",vf,"-t",str(d),"-c:v","libx264","-preset","fast",
               "-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","128k","-shortest",str(out_p)]
    subprocess.run(cmd, capture_output=True, timeout=300)
    return out_p.exists() and out_p.stat().st_size > 100000

def salvar(prod, script, mp4=""):
    if not SB_KEY: return
    requests.post(f"{SB_URL}/rest/v1/kwai_products", headers=SBH,
        json={"produto": prod["nome"], "beneficio": prod["cat"],
              "pubmed_cit": prod["pubmed"],
              "titulo_pt": f"{prod['icone']} {prod['nome']}: {prod['cat'].title()} — Pesquisa Confirma",
              "script_pt": script,
              "cta_kwai": "Link na bio 👆 com desconto no Kwai Shop",
              "status": "mp4_ready" if mp4 else "pending"},
        timeout=8, verify=False)

def run():
    print("=== KWAI SHORT VIDEO RENDERER ===\n")
    bg_p = gerar_bg()
    total = 0

    for i, prod in enumerate(PRODUTOS):
        print(f"\n  {prod['icone']} {prod['nome']}")
        script = groq_script(prod,"PT")
        if not script:
            script = f"{prod['hook']}\n\n{prod['pubmed']}.\n\nLink na bio 👆"
        print(f"     📝 Script: {script[:60]}...")

        daniela_p = gerar_daniela(prod["id"], 8001+i*77)
        if daniela_p: print(f"     🎨 Daniela: {daniela_p.stat().st_size//1024}KB")

        voz_p = TMP/f"voz_{prod['id']}.mp3"
        ok_tts = bg_p and tts(script, "pt-BR-FranciscaNeural", str(voz_p), rate="-10%")

        if ok_tts and bg_p:
            out_p = TMP/f"kwai_{prod['id']}.mp4"
            ok_v = render_kwai_short(bg_p, daniela_p, voz_p, prod, out_p)
            if ok_v:
                print(f"     🎬 MP4: {out_p.stat().st_size//1024}KB ✅")
                salvar(prod, script, str(out_p)); total+=1
                continue
        salvar(prod, script)
        total+=1
        time.sleep(3)

    print(f"\n  ✅ {total} produtos Kwai prontos")
    print(f"  📱 Mesmo vídeo → YouTube + Kwai + TikTok = 3× alcance")

if __name__=="__main__": run()
