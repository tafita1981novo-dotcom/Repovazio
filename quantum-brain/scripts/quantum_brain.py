"""
QUANTUM BRAIN — Cérebro Quântico Principal
Orquestra todo o pipeline: conteúdo → distribuição → monetização
100% gratuito: NVIDIA API + Groq + Pollinations + MoviePy + YouTube API
"""

import os
import json
import requests
import datetime
import subprocess
from pathlib import Path

# ── Configuração (lidas de variáveis de ambiente / GitHub Secrets) ──────────
NVIDIA_API_KEY   = os.environ.get("NVIDIA_API_KEY2", "")
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY2", "")
ELEVENLABS_KEY   = os.environ.get("ELEVENLABS_API_KEY2", "")
SUPABASE_URL     = os.environ.get("SUPABASE_URL2", "")
SUPABASE_KEY     = os.environ.get("SUPABASE_KEY2", "")
YOUTUBE_TOKEN    = os.environ.get("YOUTUBE_REFRESH_TOKEN2", "")
YT_CLIENT_ID     = os.environ.get("YOUTUBE_CLIENT_ID2", "")
YT_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET2", "")

# ── LLM Router gratuito (NVIDIA → Groq → fallback) ──────────────────────────
def call_llm(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    """Tenta NVIDIA primeiro, Groq como fallback — ambos gratuitos."""

    # 1. NVIDIA DeepSeek (gratuito)
    if NVIDIA_API_KEY:
        try:
            r = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
                json={
                    "model": "deepseek-ai/deepseek-r1",
                    "messages": [
                        {"role": "system", "content": system or "Você é um assistente especialista em criação de conteúdo viral em português brasileiro."},
                        {"role": "user",   "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                },
                timeout=60
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"NVIDIA falhou: {e} — tentando Groq")

    # 2. Groq llama (gratuito)
    if GROQ_API_KEY:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system or "Você é um assistente especialista em criação de conteúdo viral em português brasileiro."},
                        {"role": "user",   "content": prompt}
                    ],
                    "max_tokens": max_tokens
                },
                timeout=60
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Groq falhou: {e}")

    return "Erro: nenhuma API disponível"


# ── Pesquisa de trending topics ──────────────────────────────────────────────
def pesquisar_trending(nicho: str = "psicologia comportamental") -> list[str]:
    """Usa LLM para gerar tópicos trending com alto potencial viral."""
    prompt = f"""
Você é um especialista em crescimento de canais YouTube em português brasileiro.
Nicho: {nicho}

Liste 10 ideias de vídeo com ALTO potencial viral agora em junho de 2026.
Cada ideia deve usar uma das fórmulas validadas:
- "N sinais de [condição invisível]"
- "Por que [paradoxo emocional]"
- "A verdade desconfortável sobre [tema]"
- "Não é X, é Y — a redefinição"

Responda APENAS com JSON no formato:
{{"topics": ["titulo1", "titulo2", ...]}}
"""
    resposta = call_llm(prompt)
    try:
        # limpar markdown fence se houver
        clean = resposta.strip().replace("```json","").replace("```","").strip()
        data = json.loads(clean)
        return data.get("topics", [])
    except:
        # fallback: tópicos padrão testados
        return [
            "7 sinais de que você tem ansiedade silenciosa e não sabe",
            "Por que pessoas inteligentes se sabotam sem perceber",
            "A verdade desconfortável sobre relacionamentos tóxicos",
            "Não é preguiça, é esgotamento emocional — entenda a diferença",
            "5 comportamentos que parecem normais mas são trauma"
        ]


# ── Geração de roteiro ────────────────────────────────────────────────────────
def gerar_roteiro(titulo: str, duracao_min: int = 10) -> dict:
    """Gera roteiro completo otimizado para retenção."""
    prompt = f"""
Crie um roteiro COMPLETO para YouTube de {duracao_min} minutos sobre:
"{titulo}"

Canal: psicologia e comportamento humano em português brasileiro
Tom: próximo, empático, revelador — como uma pesquisadora de comportamento humano
IMPORTANTE: nunca usar a palavra "psicóloga" ou "psicólogo"

Estrutura obrigatória:
1. HOOK (primeiros 15 segundos) — estatística chocante ou pergunta perturbadora
2. PROMESSA (15-30s) — o que o espectador vai descobrir
3. DESENVOLVIMENTO (blocos de 2 min com pattern interrupt a cada 60s)
4. REVELAÇÃO CENTRAL (momento mais poderoso)
5. CHAMADA PARA AÇÃO (inscrição + comentário + produto)

Responda em JSON:
{{
  "titulo_otimizado": "...",
  "descricao_youtube": "...",
  "tags": ["tag1","tag2",...],
  "roteiro_completo": "texto completo do roteiro",
  "prompt_thumbnail": "descrição visual para gerar thumbnail",
  "duracao_estimada_segundos": 600
}}
"""
    resposta = call_llm(prompt, max_tokens=4000)
    try:
        clean = resposta.strip().replace("```json","").replace("```","").strip()
        return json.loads(clean)
    except:
        return {
            "titulo_otimizado": titulo,
            "descricao_youtube": f"Neste vídeo exploramos: {titulo}",
            "tags": ["psicologia","comportamento","autoconhecimento","desenvolvimento pessoal"],
            "roteiro_completo": resposta,
            "prompt_thumbnail": f"Thumbnail impactante sobre: {titulo}",
            "duracao_estimada_segundos": duracao_min * 60
        }


# ── Geração de voz (ElevenLabs free ou gTTS fallback) ────────────────────────
def gerar_voz(texto: str, output_path: str) -> bool:
    """ElevenLabs free tier (10K chars/mês). Fallback: gTTS (100% grátis)."""

    # Limitar texto para não ultrapassar quota
    texto_cortado = texto[:9000]

    # 1. ElevenLabs free
    if ELEVENLABS_KEY:
        try:
            r = requests.post(
                "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
                headers={
                    "xi-api-key": ELEVENLABS_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "text": texto_cortado,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
                },
                timeout=120
            )
            if r.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(r.content)
                print(f"✅ Voz ElevenLabs gerada: {output_path}")
                return True
        except Exception as e:
            print(f"ElevenLabs falhou: {e} — usando gTTS")

    # 2. gTTS (100% gratuito, sem limite)
    try:
        from gtts import gTTS
        tts = gTTS(text=texto_cortado, lang='pt', slow=False)
        tts.save(output_path)
        print(f"✅ Voz gTTS gerada: {output_path}")
        return True
    except Exception as e:
        print(f"gTTS falhou: {e}")
        return False


# ── Geração de imagens (Pollinations FLUX — 100% gratuito) ───────────────────
def gerar_imagens(prompts: list[str], output_dir: str) -> list[str]:
    """Pollinations.ai FLUX — gratuito e ilimitado."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    imagens = []

    for i, prompt in enumerate(prompts):
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=1280&height=720&nologo=true&seed={i}"
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                path = f"{output_dir}/img_{i:03d}.jpg"
                with open(path, "wb") as f:
                    f.write(r.content)
                imagens.append(path)
                print(f"✅ Imagem {i+1}/{len(prompts)} gerada")
        except Exception as e:
            print(f"Imagem {i} falhou: {e}")

    return imagens


# ── Montagem do vídeo (MoviePy — gratuito) ────────────────────────────────────
def montar_video(imagens: list[str], audio_path: str, output_path: str) -> bool:
    """Monta vídeo com Ken Burns effect usando MoviePy."""
    try:
        from moviepy.editor import (
            ImageClip, AudioFileClip, concatenate_videoclips
        )
        import numpy as np

        audio = AudioFileClip(audio_path)
        duracao_total = audio.duration
        duracao_por_img = duracao_total / max(len(imagens), 1)

        clips = []
        for img_path in imagens:
            clip = ImageClip(img_path, duration=duracao_por_img)
            # Ken Burns: zoom leve
            def make_frame(t, clip=clip, dur=duracao_por_img):
                zoom = 1 + 0.05 * (t / dur)
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                new_h = int(h / zoom)
                new_w = int(w / zoom)
                y1 = (h - new_h) // 2
                x1 = (w - new_w) // 2
                cropped = frame[y1:y1+new_h, x1:x1+new_w]
                import cv2
                return cv2.resize(cropped, (w, h))
            clip = clip.fl(lambda gf, t: make_frame(t))
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")
        video = video.set_audio(audio)
        video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None
        )
        print(f"✅ Vídeo montado: {output_path}")
        return True
    except Exception as e:
        print(f"MoviePy falhou: {e}")
        return False


# ── Thumbnail (Pollinations — gratuito) ──────────────────────────────────────
def gerar_thumbnail(prompt: str, titulo: str, output_path: str) -> bool:
    """Gera thumbnail 1280×720 via Pollinations FLUX."""
    prompt_completo = f"{prompt}, thumbnail YouTube profissional, texto grande '{titulo[:30]}', cores vibrantes, rosto expressivo, alta qualidade"
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt_completo)}?width=1280&height=720&nologo=true"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
            print(f"✅ Thumbnail gerada: {output_path}")
            return True
    except Exception as e:
        print(f"Thumbnail falhou: {e}")
    return False


# ── Upload YouTube (API v3 — gratuito) ───────────────────────────────────────
def obter_youtube_token() -> str:
    """Obtém access token via refresh token."""
    r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id":     YT_CLIENT_ID,
            "client_secret": YT_CLIENT_SECRET,
            "refresh_token": YOUTUBE_TOKEN,
            "grant_type":    "refresh_token"
        }
    )
    if r.status_code == 200:
        return r.json().get("access_token", "")
    return ""


def upload_youtube(video_path: str, thumbnail_path: str, roteiro: dict) -> str:
    """Faz upload do vídeo para o YouTube."""
    access_token = obter_youtube_token()
    if not access_token:
        print("❌ YouTube token inválido")
        return ""

    # Metadata do vídeo
    metadata = {
        "snippet": {
            "title":       roteiro.get("titulo_otimizado", ""),
            "description": roteiro.get("descricao_youtube", "") + "\n\n#psicologia #autoconhecimento #comportamento",
            "tags":        roteiro.get("tags", []),
            "categoryId":  "22"  # People & Blogs
        },
        "status": {
            "privacyStatus":           "public",
            "selfDeclaredMadeForKids": False
        }
    }

    # Upload multipart
    import io
    headers = {"Authorization": f"Bearer {access_token}"}

    # 1. Iniciar upload resumável
    r = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={**headers, "Content-Type": "application/json", "X-Upload-Content-Type": "video/mp4"},
        json=metadata
    )
    if r.status_code != 200:
        print(f"❌ YouTube upload init falhou: {r.status_code} {r.text}")
        return ""

    upload_url = r.headers.get("Location", "")

    # 2. Enviar arquivo
    with open(video_path, "rb") as f:
        video_data = f.read()

    r2 = requests.put(
        upload_url,
        headers={**headers, "Content-Type": "video/mp4"},
        data=video_data,
        timeout=300
    )

    if r2.status_code in (200, 201):
        video_id = r2.json().get("id", "")
        print(f"✅ YouTube upload OK: https://youtube.com/watch?v={video_id}")

        # 3. Thumbnail
        if thumbnail_path and video_id:
            with open(thumbnail_path, "rb") as f:
                thumb_data = f.read()
            requests.post(
                f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}&uploadType=media",
                headers={**headers, "Content-Type": "image/jpeg"},
                data=thumb_data
            )

        return video_id

    print(f"❌ Upload falhou: {r2.status_code}")
    return ""


# ── Salvar no Supabase ────────────────────────────────────────────────────────
def salvar_supabase(tabela: str, dados: dict) -> bool:
    """Salva dados no Supabase free tier."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/{tabela}",
            headers={
                "apikey":        SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type":  "application/json",
                "Prefer":        "return=minimal"
            },
            json=dados,
            timeout=10
        )
        return r.status_code in (200, 201)
    except:
        return False


# ── Pipeline principal ────────────────────────────────────────────────────────
def executar_pipeline():
    """Executa o pipeline completo de conteúdo."""
    hoje = datetime.date.today().isoformat()
    base = Path(f"/tmp/quantum_brain/{hoje}")
    base.mkdir(parents=True, exist_ok=True)

    print("🧠 QUANTUM BRAIN iniciando pipeline...")

    # 1. Pesquisar trending
    print("\n📊 Pesquisando trending topics...")
    topics = pesquisar_trending("psicologia comportamental e autoconhecimento")
    titulo = topics[0] if topics else "7 sinais de que você tem ansiedade silenciosa"
    print(f"📌 Tópico escolhido: {titulo}")

    # 2. Gerar roteiro
    print("\n✍️ Gerando roteiro...")
    roteiro = gerar_roteiro(titulo, duracao_min=10)
    with open(base / "roteiro.json", "w") as f:
        json.dump(roteiro, f, ensure_ascii=False, indent=2)

    # 3. Gerar voz
    print("\n🎙️ Gerando narração...")
    audio_path = str(base / "audio.mp3")
    texto_roteiro = roteiro.get("roteiro_completo", titulo)[:9000]
    gerar_voz(texto_roteiro, audio_path)

    # 4. Gerar imagens
    print("\n🖼️ Gerando imagens...")
    prompts_img = [
        f"{titulo}, emocional, fotorrealista, pessoa pensativa, luz dramática",
        f"cérebro humano, neurônios, azul e roxo, futurista, conceitual",
        f"pessoa olhando para o horizonte, pôr do sol, esperança, emocional",
        f"relação humana, conexão emocional, quente, íntimo",
        f"livros e conhecimento, biblioteca, sabedoria, profundidade",
        f"espelho refletindo, autoconhecimento, introspectivo, artístico",
        f"mãos estendidas, ajuda, suporte emocional, caloroso",
        f"{titulo}, representação visual abstrata, impactante"
    ]
    imagens = gerar_imagens(prompts_img, str(base / "images"))

    # 5. Montar vídeo
    print("\n🎬 Montando vídeo...")
    video_path = str(base / "video.mp4")
    if imagens and Path(audio_path).exists():
        montar_video(imagens, audio_path, video_path)

    # 6. Gerar thumbnail
    print("\n🖼️ Gerando thumbnail...")
    thumb_path = str(base / "thumbnail.jpg")
    gerar_thumbnail(
        roteiro.get("prompt_thumbnail", titulo),
        titulo,
        thumb_path
    )

    # 7. Upload YouTube
    video_id = ""
    if Path(video_path).exists() and YT_CLIENT_ID:
        print("\n📤 Fazendo upload para o YouTube...")
        video_id = upload_youtube(video_path, thumb_path, roteiro)

    # 8. Salvar no Supabase
    salvar_supabase("content_log", {
        "date":      hoje,
        "titulo":    titulo,
        "video_id":  video_id,
        "platform":  "youtube",
        "status":    "published" if video_id else "generated"
    })

    print(f"\n✅ Pipeline concluído!")
    print(f"   Vídeo: {titulo}")
    print(f"   YouTube ID: {video_id or 'não publicado (sem credenciais YT)'}")
    return {"titulo": titulo, "video_id": video_id, "roteiro": roteiro}


if __name__ == "__main__":
    executar_pipeline()
