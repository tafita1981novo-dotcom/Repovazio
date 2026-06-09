#!/usr/bin/env python3
"""
long_video_hq.py — Gera vídeos LONGOS de qualidade extrema (15min+)
Pipeline: Script (Groq) → TTS (Edge TTS ThalitaMultilingualNeural)
        → Imagens (Pollinations FLUX) → Ken Burns 1080p → YouTube
"""
import os, sys, json, subprocess, pathlib, time, urllib.request
import urllib.parse, asyncio, random, struct, wave, array, tempfile

SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_SERVICE_KEY"]
GROQ_KEY      = os.environ.get("GROQ_API_KEY","")
CLIENT_ID     = os.environ["YT_CLIENT_ID"]
CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
TMP = pathlib.Path("/tmp/hq")
TMP.mkdir(exist_ok=True)

SB_H = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"}
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def sb_get(table, qs=""):
    r = urllib.request.urlopen(
        urllib.request.Request(f"{SUPABASE_URL}/rest/v1/{table}?{qs}", headers=SB_H), timeout=25)
    return json.loads(r.read())

def sb_patch(table, rid, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{rid}",
                                  data=body, method="PATCH",
                                  headers={**SB_H,"Prefer":"return=minimal"})
    urllib.request.urlopen(req, timeout=15)

def llm_call(prompt, max_tokens=4000):
    """Chama Groq Llama 3.3 70B"""
    body = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "max_tokens": max_tokens,
        "messages": [{"role":"user","content":prompt}],
        "temperature": 0.7
    }).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body)
    req.add_header("Authorization", f"Bearer {GROQ_KEY}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

def gerar_script_longo(topico, titulo_seo):
    """Gera script de 15min baseado no QUALITY_STANDARD"""
    prompt = f"""Crie um script de vídeo de 15 minutos sobre: "{topico}"
Título SEO: {titulo_seo}

REGRAS OBRIGATÓRIAS (QUALITY_STANDARD):
1. Hook nos primeiros 30s: perigo que parece seguro (NÃO use pergunta genérica)
2. Revelação contra-intuitiva no minuto 1
3. Cite pesquisador real: Malkin/Harvard, van der Kolk, Ainsworth, Gottman, Siegel/UCLA, Brown/U.Texas ou Beck
4. Sinal contra-intuitivo + mecanismo neural explicado
5. Final que restaura agency (NÃO vitimização)

PROIBIDO: pesquisa vaga, sinais óbvios, vitimização, "psicóloga" ou "psicólogo"

FORMATO DO SCRIPT:
- Divida em CENAS numeradas [CENA 1], [CENA 2], etc.
- Cada cena tem ~60 segundos de narração
- Total: 15 cenas = ~15 minutos
- Para cada cena, inclua: NARRAÇÃO + [PROMPT DE IMAGEM para FLUX]

Escreva em Português do Brasil, tom científico mas acessível.
Persona: pesquisadora de comportamento humano.
"""
    return llm_call(prompt, max_tokens=6000)

def gerar_imagem_flux(prompt_en, idx):
    """Gera imagem via Pollinations FLUX"""
    prompt_encoded = urllib.parse.quote(f"cinematic dark psychology, {prompt_en}, ultra HD 1920x1080, moody lighting, professional")
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1920&height=1080&seed={idx}&nologo=true"
    dest = TMP / f"img_{idx:03d}.jpg"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r, open(dest,"wb") as f:
        f.write(r.read())
    return str(dest)

def tts_edge(texto, output_path):
    """TTS via edge-tts ThalitaMultilingualNeural"""
    subprocess.run([
        "edge-tts",
        "--voice", "pt-BR-ThalitaMultilingualNeural",
        "--rate", "+5%",
        "--text", texto[:4900],
        "--write-media", output_path
    ], check=True, timeout=120, capture_output=True)

def ken_burns_clip(img_path, audio_path, out_path, duration):
    """Ken Burns effect: zoom suave + pan aleatório"""
    # Zoom in de 1.0 para 1.1 com pan suave
    direction = random.choice(["tl","tr","bl","br","c"])
    zooms = {
        "tl": "x='iw/2*(1-1/zoom)':y='ih/2*(1-1/zoom)'",
        "tr": "x='iw-iw/zoom':y='0'",
        "bl": "x='0':y='ih-ih/zoom'",
        "br": "x='iw-iw/zoom':y='ih-ih/zoom'",
        "c":  "x='iw/2*(1-1/zoom)':y='ih/2*(1-1/zoom)'"
    }
    vf = (f"scale=8000:-1,zoompan=z='min(zoom+0.0015,1.1)':d={int(duration*25)}:"
          f"{zooms[direction]}:fps=25:s=1920x1080")
    cmd = ["ffmpeg","-y","-loop","1","-i",img_path,
           "-i",audio_path,
           "-vf",vf,
           "-c:v","libx264","-preset","fast","-crf","23",
           "-c:a","aac","-b:a","192k",
           "-t",str(duration),"-pix_fmt","yuv420p",
           "-shortest",out_path]
    subprocess.run(cmd, check=True, timeout=300, capture_output=True)
    return out_path

def concatenar_clips(clips, output):
    """Concatena todos os clips em um único vídeo"""
    list_file = TMP / "concat.txt"
    with open(list_file,"w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",str(list_file),
           "-c:v","libx264","-preset","fast","-crf","22",
           "-c:a","aac","-b:a","192k","-movflags","+faststart",output]
    subprocess.run(cmd, check=True, timeout=600, capture_output=True)

def get_yt_token():
    data = urllib.parse.urlencode({"client_id":CLIENT_ID,"client_secret":CLIENT_SECRET,
                                    "refresh_token":REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token",data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req,timeout=15) as r:
        return json.loads(r.read())["access_token"]

def upload_yt(token, mp4_path, title, desc, tags):
    size = pathlib.Path(mp4_path).stat().st_size
    metadata = json.dumps({
        "snippet":{"title":title[:100],"description":desc[:4900],
                   "tags":tags[:30],"categoryId":"27",
                   "defaultLanguage":"pt","defaultAudioLanguage":"pt"},
        "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False}
    }).encode()
    boundary = b"frontier"
    with open(mp4_path,"rb") as f: video_data = f.read()
    body = (b"--frontier\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
            + metadata + b"\r\n--frontier\r\nContent-Type: video/mp4\r\n\r\n"
            + video_data + b"\r\n--frontier--")
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=multipart&part=snippet,status",
        data=body)
    req.add_header("Authorization",f"Bearer {token}")
    req.add_header("Content-Type","multipart/related; boundary=frontier")
    req.add_header("Content-Length",str(len(body)))
    with urllib.request.urlopen(req,timeout=600) as r:
        return json.loads(r.read())

def main():
    log("=== LONG VIDEO HQ GENERATOR ===")

    # Buscar próximo long pending_generation com script pronto
    videos = sb_get("content_pipeline",
        "format=eq.long&status=in.(pending_generation,script_ready)&select=id,topic,youtube_title,youtube_description,youtube_tags,series_slug&order=id.asc&limit=1")
    
    if not videos:
        # Usar tópicos W24 da strategy
        topics_w24 = [
            ("O impacto da tecnologia na saúde mental dos jovens",
             "Por que usar o celular antes de dormir destrói sua saúde mental"),
            ("O papel da empatia na construção de relacionamentos saudáveis",
             "Por que pessoas sem empatia destroem relacionamentos sem perceber"),
            ("O impacto da mídia social na autoestima dos adolescentes",
             "Por que o Instagram está destruindo a autoestima de uma geração inteira"),
            ("O poder da gratidão no relacionamento",
             "Por que casais que praticam gratidão nunca se separam, segundo a ciência"),
            ("O papel da resiliência na superação de obstáculos",
             "Por que algumas pessoas superam qualquer adversidade enquanto outras quebram"),
        ]
        # Inserir o primeiro que ainda não existe
        for topico, titulo in topics_w24:
            existing = sb_get("content_pipeline", f"topic=eq.{urllib.parse.quote(topico)}&format=eq.long&limit=1")
            if not existing:
                body = json.dumps({
                    "topic": topico, "youtube_title": titulo,
                    "format": "long", "status": "pending_generation",
                    "quality_tier": "hq", "duration_target_min": 15
                }).encode()
                req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/content_pipeline",
                                              data=body, headers={**SB_H,"Prefer":"return=representation"})
                r = urllib.request.urlopen(req, timeout=15)
                vid = json.loads(r.read())[0]
                log(f"Inserido novo vídeo long: ID {vid['id']} — {topico[:50]}")
                videos = [vid]
                break

    if not videos:
        log("Nenhum vídeo long pendente"); return 0

    v = videos[0]
    vid_id = v["id"]
    topico = v.get("topic","Psicologia e Comportamento Humano")
    titulo = v.get("youtube_title") or topico
    log(f"Gerando vídeo long ID {vid_id}: {titulo[:60]}")

    sb_patch("content_pipeline", vid_id, {"status":"generating_script"})

    # Gerar script
    log("Gerando script 15min...")
    script = gerar_script_longo(topico, titulo)
    sb_patch("content_pipeline", vid_id, {"script": script, "status":"generating_media"})

    # Parsear cenas
    import re
    cenas = re.split(r"\[CENA \d+\]", script)
    cenas = [c.strip() for c in cenas if c.strip()][:15]
    log(f"Cenas identificadas: {len(cenas)}")

    # Gerar mídia por cena
    clips = []
    for i, cena in enumerate(cenas):
        log(f"Cena {i+1}/{len(cenas)}...")
        # Extrair prompt de imagem
        img_prompt_match = re.search(r"\[PROMPT DE IMAGEM[^\]]*\](.*?)(?=\[|$)", cena, re.DOTALL)
        img_prompt = img_prompt_match.group(1).strip() if img_prompt_match else f"psychology {topico} concept dark"
        narr = re.sub(r"\[PROMPT DE IMAGEM[^\]]*\].*", "", cena, flags=re.DOTALL).strip()
        narr = re.sub(r"\[.*?\]","",narr).strip()[:1000]
        if not narr: continue

        img_path = gerar_imagem_flux(img_prompt, i)
        audio_path = str(TMP / f"audio_{i:03d}.mp3")
        tts_edge(narr, audio_path)

        # Duração do áudio
        result = subprocess.run(["ffprobe","-v","quiet","-show_entries",
            "format=duration","-of","json",audio_path], capture_output=True, text=True)
        dur = float(json.loads(result.stdout)["format"]["duration"]) if result.returncode==0 else 60.0

        clip_path = str(TMP / f"clip_{i:03d}.mp4")
        ken_burns_clip(img_path, audio_path, clip_path, dur + 0.5)
        clips.append(clip_path)
        log(f"  ✅ Cena {i+1} ok ({dur:.0f}s)")

    # Concatenar
    output_path = str(TMP / f"long_{vid_id}_hq.mp4")
    log(f"Concatenando {len(clips)} clips...")
    concatenar_clips(clips, output_path)

    size_mb = pathlib.Path(output_path).stat().st_size / 1024 / 1024
    log(f"Vídeo pronto: {size_mb:.1f}MB")

    # Upload YouTube
    log("Enviando para YouTube...")
    token = get_yt_token()
    desc = (v.get("youtube_description") or "") + """

🔔 Inscreva-se e ative o sininho para não perder nenhum episódio!

Baseado em pesquisas de Harvard, van der Kolk, Ainsworth, Gottman, Siegel/UCLA.

⚠️ Conteúdo informativo e educacional. Para suporte, consulte um profissional.

#psicologia #saudemental #neurociencia #comportamento #psidanicoelho"""

    raw_tags = v.get("youtube_tags") or []
    if isinstance(raw_tags,str):
        try: raw_tags = json.loads(raw_tags)
        except: raw_tags = []
    tags = raw_tags + ["psicologia","saúde mental","neurociência","comportamento humano"]

    result = upload_yt(token, output_path, titulo, desc[:4900], tags[:30])
    yt_id = result.get("id")

    if yt_id:
        log(f"✅ Publicado: https://www.youtube.com/watch?v={yt_id}")
        sb_patch("content_pipeline", vid_id, {
            "status": "published", "youtube_id": yt_id,
            "youtube_url": f"https://www.youtube.com/watch?v={yt_id}",
            "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
        })
    else:
        log(f"❌ Upload falhou: {result}")
        sb_patch("content_pipeline", vid_id, {"status":"publish_error","error":str(result)[:200]})

    return 0

if __name__ == "__main__":
    sys.exit(main())
