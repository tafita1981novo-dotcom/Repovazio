#!/usr/bin/env python3
"""
thumbnail_dark_gen.py — Gera thumbnails dark para YouTube
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Estética: fundo escuro #06060F, Daniela chibi kawaii,
texto impactante, gradiente roxo-vermelho
Usa Pollinations FLUX (grátis, ilimitado)
Formato: 1280x720 YouTube thumbnail
"""
import os, requests, pathlib, subprocess, time
import urllib3; urllib3.disable_warnings()

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
SBH    = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
          "Content-Type":"application/json","Prefer":"return=minimal"}
TMP    = pathlib.Path("/tmp/thumbs"); TMP.mkdir(exist_ok=True)

THUMBNAILS = [
    {
        "video_id":"narcis1",
        "titulo":"O Narcisista Que Você Não Vê Vir",
        "prompt":"masterpiece, best quality, kawaii chibi anime girl with serious expression, dark background #06060F, purple and red gradient glow, dramatic lighting, ψ symbol golden pin, minimalist art, no text ### watermark, text, nsfw, blurry, lowres",
        "seed":9001,
    },
    {
        "video_id":"burnout1",
        "titulo":"Burnout Não Começa Com Cansaço",
        "prompt":"masterpiece, kawaii chibi anime character exhausted, dark dramatic background, corporate setting shadows, purple neon glow, cinematic, minimalist ### text, watermark, nsfw, blurry",
        "seed":9078,
    },
    {
        "video_id":"sono1",
        "titulo":"Por Que Você Acorda Às 3h da Manhã",
        "prompt":"masterpiece, kawaii chibi anime character awake at night, moonlight through window, dark bedroom, blue-purple atmosphere, alarm clock 3:00, minimal ### text, watermark, nsfw, blurry",
        "seed":9155,
    },
    {
        "video_id":"apego1",
        "titulo":"Por Que Você Escolhe Quem Te Machuca",
        "prompt":"masterpiece, kawaii chibi anime character sad expression, dark background, two silhouettes, purple red gradient, emotional, cinematic ### text, watermark, nsfw, blurry",
        "seed":9232,
    },
    {
        "video_id":"528hz",
        "titulo":"528Hz Enquanto Você Dorme",
        "prompt":"masterpiece, kawaii chibi anime character peaceful sleeping, sound waves visualization, binaural frequencies, dark teal background, golden glow, ethereal ### text, watermark, nsfw, blurry",
        "seed":9309,
    },
]

def pollinations_url(prompt, seed, w=1280, h=720):
    p = requests.utils.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{p}?seed={seed}&width={w}&height={h}&nologo=true"

def baixar_thumb(url, path):
    try:
        r = requests.get(url, timeout=30, verify=False)
        if r.status_code == 200 and len(r.content) > 10000:
            path.write_bytes(r.content)
            return True
    except: pass
    return False

def salvar_supabase(thumb, url):
    if not SB_KEY: return
    requests.post(f"{SB_URL}/rest/v1/video_seo",
        headers={**SBH,"Prefer":"return=minimal"},
        json={"video_id":thumb["video_id"],"titulo_principal":thumb["titulo"],
              "status":"ready"},
        timeout=8, verify=False)

def run():
    print("=== THUMBNAIL DARK GENERATOR ===\n")
    print("  Estética: dark #06060F + Daniela chibi + gradiente ψ\n")
    total = 0
    for thumb in THUMBNAILS:
        url = pollinations_url(thumb["prompt"], thumb["seed"])
        path = TMP / f"thumb_{thumb['video_id']}.jpg"
        print(f"  🖼️  {thumb['titulo'][:40]}")
        print(f"     URL: {url[:70]}...")
        ok = baixar_thumb(url, path)
        if ok:
            size = path.stat().st_size // 1024
            print(f"     ✅ {path.name} ({size}KB)")
            total += 1
        else:
            print(f"     ⚠️  URL gerada (sem download neste run)")
        salvar_supabase(thumb, url)
        time.sleep(2)
    print(f"\n  ✅ {total} thumbnails processadas")
    print(f"  📁 Salvas em: {TMP}")

if __name__=="__main__": run()
