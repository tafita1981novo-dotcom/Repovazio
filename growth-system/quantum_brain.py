"""
QUANTUM BRAIN v2.0 — Pipeline Completo de Monetização
Canal: @newlife_2day | Nicho: Psicologia / Sleep / Brain Science
100% gratuito: NVIDIA + Groq + Pollinations + gTTS + MoviePy + YouTube API
Afiliados ClickBank de maior APV/EPC selecionados (junho 2026)
"""

import os, json, requests, datetime, subprocess, textwrap
from pathlib import Path

# ── Credenciais (GitHub Secrets) ────────────────────────────────────────────
NVIDIA_API_KEY    = os.environ.get("NVIDIA_API_KEY2", "")
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY2", "")
ELEVENLABS_KEY    = os.environ.get("ELEVENLABS_API_KEY2", "")
YOUTUBE_TOKEN     = os.environ.get("YOUTUBE_REFRESH_TOKEN2", "")
YT_CLIENT_ID      = os.environ.get("YOUTUBE_CLIENT_ID2", "")
YT_CLIENT_SECRET  = os.environ.get("YOUTUBE_CLIENT_SECRET2", "")

# ── Top afiliados ClickBank (nicho: psicologia/cérebro/self-help) ────────────
# Ordenados por EPC × conversão (maior receita real por clique)
AFFILIATE_LINKS = {
    "Billionaire Brain Wave": {
        "url":  "https://tafita1981.attractbr.hop.clickbank.net",
        "apv":  63.73, "epc": 1.68, "conv": 3.04,
        "desc": "Ative ondas cerebrais Theta e atraia prosperidade"
    },
    "The Brain Song": {
        "url":  "https://tafita1981.brainsong.hop.clickbank.net",
        "apv":  55.00, "epc": 1.50, "conv": 2.80,
        "desc": "Programa neurocientífico para otimização cerebral"
    },
    "Individualist — Psicologia Junguiana": {
        "url":  "https://tafita1981.individua1.hop.clickbank.net",
        "apv":  48.00, "epc": 0.95, "conv": 1.20,
        "desc": "Descubra seu arquétipo e transforme sua vida"
    },
    "Wealth DNA Code": {
        "url":  "https://tafita1981.wealthdna.hop.clickbank.net",
        "apv":  48.30, "epc": 0.39, "conv": 0.82,
        "desc": "Ative o código de riqueza no seu DNA"
    }
}

def gerar_footer_afiliados() -> str:
    footer  = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    footer += "🔗 RECURSOS RECOMENDADOS:\n\n"
    for nome, d in AFFILIATE_LINKS.items():
        footer += f"✅ {d['desc']}:\n{d['url']}\n\n"
    footer += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    footer += "👍 Gostou? Deixe seu like e se inscreva!\n"
    footer += "🔔 Ative o sininho para não perder nenhum vídeo\n"
    footer += "💬 Comente sua experiência!\n"
    return footer

# ── LLM Router gratuito ──────────────────────────────────────────────────────
def call_llm(prompt: str, system: str = "", max_tokens: int = 3000) -> str:
    sys = system or "Você é especialista em criação de conteúdo viral em português brasileiro sobre psicologia e comportamento humano."

    # 1. NVIDIA DeepSeek (grátis)
    if NVIDIA_API_KEY:
        try:
            r = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
                json={"model": "deepseek-ai/deepseek-r1",
                      "messages": [{"role":"system","content":sys},{"role":"user","content":prompt}],
                      "max_tokens": max_tokens, "temperature": 0.7},
                timeout=60
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except: pass

    # 2. Groq (grátis, fallback)
    if GROQ_API_KEY:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={"model": "llama-3.3-70b-versatile",
                      "messages": [{"role":"system","content":sys},{"role":"user","content":prompt}],
                      "max_tokens": max_tokens},
                timeout=60
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except: pass

    return ""

# ── Trending topics ──────────────────────────────────────────────────────────
def pesquisar_trending() -> list:
    prompt = """Liste 10 títulos de vídeo YouTube com ALTO potencial viral agora em junho 2026.
Nicho: psicologia comportamental, autoconhecimento, mente e comportamento humano.
Canal: @newlife_2day — audience: Brasil.

Formato EXATO (JSON array):
[
  {"titulo": "...", "descricao": "...", "tags": ["...", "..."]},
  ...
]

Só o JSON, sem explicação."""
    resp = call_llm(prompt)
    try:
        start = resp.find("[")
        end   = resp.rfind("]") + 1
        return json.loads(resp[start:end]) if start >= 0 else []
    except:
        return [{"titulo": "O poder oculto da sua mente subconsciente",
                 "descricao": "Descubra como seu cérebro toma decisões sem você saber",
                 "tags": ["psicologia","mente","comportamento"]}]

# ── YouTube token ────────────────────────────────────────────────────────────
def yt_token() -> str:
    if not (YT_CLIENT_ID and YT_CLIENT_SECRET and YOUTUBE_TOKEN):
        return ""
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YOUTUBE_TOKEN, "grant_type": "refresh_token"
    })
    return r.json().get("access_token", "") if r.status_code == 200 else ""

# ── Gerar narração ───────────────────────────────────────────────────────────
def gerar_narracao(texto: str, output_path: str) -> bool:
    # 1. ElevenLabs (qualidade premium)
    if ELEVENLABS_KEY:
        try:
            r = requests.post(
                "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB",
                headers={"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"},
                json={"text": texto[:500], "model_id": "eleven_multilingual_v2",
                      "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
                timeout=30
            )
            if r.status_code == 200:
                with open(output_path, "wb") as f: f.write(r.content)
                return True
        except: pass

    # 2. gTTS (fallback grátis)
    try:
        from gtts import gTTS
        gTTS(text=texto[:500], lang="pt", slow=False).save(output_path)
        return True
    except: pass

    return False

# ── Gerar imagem ─────────────────────────────────────────────────────────────
def gerar_imagem(prompt_img: str, output_path: str) -> bool:
    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt_img)}?width=1280&height=720&nologo=true"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            with open(output_path, "wb") as f: f.write(r.content)
            return True
    except: pass
    return False

# ── Montar vídeo ─────────────────────────────────────────────────────────────
def montar_video(img_path: str, audio_path: str, output_path: str) -> bool:
    if not (Path(img_path).exists() and Path(audio_path).exists()):
        return False
    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-loop", "1", "-i", img_path,
            "-i", audio_path,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest", output_path
        ], check=True, capture_output=True, timeout=120)
        return True
    except: return False

# ── Upload YouTube ───────────────────────────────────────────────────────────
def upload_youtube(video_path: str, titulo: str, descricao: str, tags: list) -> str:
    token = yt_token()
    if not token or not Path(video_path).exists():
        return ""

    desc_completa = descricao + gerar_footer_afiliados()

    metadata = {"snippet": {"title": titulo[:100],
                             "description": desc_completa[:5000],
                             "tags": tags[:15],
                             "categoryId": "27"},
                "status": {"privacyStatus": "public"}}

    r = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json",
                 "X-Upload-Content-Type": "video/mp4"},
        json=metadata, timeout=30
    )
    if r.status_code != 200:
        return ""

    upload_url = r.headers.get("Location", "")
    if not upload_url:
        return ""

    with open(video_path, "rb") as f:
        r2 = requests.put(upload_url,
                          headers={"Authorization": f"Bearer {token}",
                                   "Content-Type": "video/mp4"},
                          data=f, timeout=300)
    return r2.json().get("id", "") if r2.status_code in (200, 201) else ""

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print(f"🧠 Quantum Brain v2.0 — {datetime.date.today()}")

    topicos = pesquisar_trending()
    if not topicos:
        print("❌ Sem tópicos"); return

    topico = topicos[0]
    titulo = topico["titulo"]
    print(f"📝 Tópico: {titulo}")

    # Gerar roteiro completo
    roteiro_prompt = f"""Escreva um script de vídeo YouTube de 90 segundos sobre: {titulo}

Formato:
- Hook nos primeiros 5 segundos (pergunta ou afirmação chocante)
- 3 pontos principais explicados com exemplos
- CTA final pedindo like e inscrição
- Tom: íntimo, científico mas acessível, em português brasileiro

Só o texto do script, sem marcações."""

    script = call_llm(roteiro_prompt)
    if not script:
        print("❌ Script vazio"); return

    # Gerar assets
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    img  = f"/tmp/thumb_{ts}.jpg"
    aud  = f"/tmp/audio_{ts}.mp3"
    vid  = f"/tmp/video_{ts}.mp4"

    print("🎨 Gerando imagem...")
    gerar_imagem(f"Cinematic psychology concept: {titulo}, dark blue background, brain visualization, high quality", img)

    print("🎤 Gerando narração...")
    gerar_narracao(script, aud)

    print("🎬 Montando vídeo...")
    ok = montar_video(img, aud, vid)
    if not ok:
        print("⚠️ Vídeo não montado — assets faltando")
        return

    print("📤 Enviando para YouTube...")
    tags = topico.get("tags", []) + ["psicologia", "mente", "comportamento", "newlife2day"]
    vid_id = upload_youtube(vid, titulo, topico.get("descricao", titulo), tags)

    if vid_id:
        print(f"✅ Publicado: https://youtube.com/watch?v={vid_id}")
    else:
        print("⚠️ Upload falhou — verifique tokens YouTube")

    print(f"\n💰 Footer de afiliados incluído com {len(AFFILIATE_LINKS)} links ClickBank")

if __name__ == "__main__":
    main()
