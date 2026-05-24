#!/usr/bin/env python3
"""
robonil_free.py — Alternativa 100% gratuita ao Robonil

MODELO: Lightricks LTX-Video (2.1M downloads HuggingFace)
        Anima imagem estática com movimentos naturais
        Equivalente EXATO ao que o Robonil faz

ESTRATÉGIA DO VÍDEO ($5.600 em 7 dias):
  1. Gerar personagem Daniela (chibi anime) via Pollinations
  2. Animar via LTX-Video HuggingFace (gratuito)
  3. Montar vídeo com hook + overlay texto via FFmpeg
  4. Postar no TikTok Shop como UGC de psicologia
  5. Produto: livros, diários, merch psychology (afiliado)

IMPORTANTE: ZERO texto no prompt de imagem — só via FFmpeg overlay
"""
import os, requests, pathlib, subprocess, base64, time, json

TMP = pathlib.Path("/tmp/tiktok"); TMP.mkdir(exist_ok=True)
HF_TOKEN = os.getenv("HF_TOKEN", "")  # Opcional — aumenta rate limit
GH_RAW = "https://raw.githubusercontent.com/tafita81/Repovazio/main"
SB_URL = os.getenv("SUPABASE_URL", "")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
SBH = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
       "Content-Type": "application/json", "Prefer": "return=minimal"}

# Modelos LTX-Video gratuitos (fallback em sequência)
LTX_MODELS = [
    "https://api-inference.huggingface.co/models/Lightricks/LTX-2.3",
    "https://api-inference.huggingface.co/models/Lightricks/LTX-2",
    "https://api-inference.huggingface.co/models/Lightricks/LTX-Video",
]

# Imagens aprovadas do banco GitHub (analisadas visualmente)
IMAGENS_APROVADAS = {
    "psych":  f"{GH_RAW}/public/estilos_virais/psych2go.jpg",    # 8.5/10 ✅ chibi anime
    "sleep":  f"{GH_RAW}/public/estilos_virais/meditative.jpg",  # 9.5/10 ✅ bioluminescente
    "focus":  f"{GH_RAW}/public/thumbnails/thumbnail_adhd_focus.jpg",  # 8/10 ✅ neon
    "dark":   f"{GH_RAW}/public/thumbnails/thumbnail_narcissism_en.jpg",
}

# TikTok Shop produtos afiliados (psicologia)
PRODUTOS_TIKTOK = [
    {
        "nome": "Diário de Autoconhecimento",
        "categoria": "papelaria",
        "preco_sugerido": "R$39-79",
        "hooks": [
            "Esse diário me fez perceber padrões que destruíam meus relacionamentos",
            "3 perguntas por dia que mudaram minha saúde mental",
            "Psicólogos recomendam escrever. Eu testei por 30 dias.",
        ],
        "hashtags": "#autoconhecimento #saúdemental #terapia #psicologia #fyp",
        "estilo_imagem": "psych",
    },
    {
        "nome": "Livro Apego Ansioso",
        "categoria": "livros",
        "preco_sugerido": "R$35-55",
        "hooks": [
            "Se você se apega demais, esse livro vai mudar sua vida",
            "Entendi meu padrão de apego ansioso nesse livro",
            "Por que eu sempre escolhia as pessoas erradas? A resposta estava aqui",
        ],
        "hashtags": "#apegoan sioso #relacionamentos #psicologia #livros #fyp",
        "estilo_imagem": "psych",
    },
    {
        "nome": "Difusor Aromaterapia + Frequências",
        "categoria": "bem-estar",
        "preco_sugerido": "R$89-149",
        "hooks": [
            "Durmo 2h mais profundo com isso no quarto",
            "528Hz + lavanda = ansiedade zerada em 10 minutos",
            "Testei por 21 dias. Resultado no final do vídeo.",
        ],
        "hashtags": "#sono #ansiedade #aromaterapia #528hz #fyp",
        "estilo_imagem": "sleep",
    },
    {
        "nome": "Caderno Terapêutico Mindfulness",
        "categoria": "papelaria",
        "preco_sugerido": "R$45-85",
        "hooks": [
            "Esse exercício me fez parar de remoer pensamentos à noite",
            "5 minutos antes de dormir que mudaram minha ansiedade",
            "Por que minha terapeuta mandou eu comprar esse caderno",
        ],
        "hashtags": "#mindfulness #ansiedade #saúdemental #fyp",
        "estilo_imagem": "psych",
    },
]

def baixar_imagem(estilo):
    """Baixa imagem aprovada do GitHub (sem texto)"""
    cached = TMP / f"base_{estilo}.jpg"
    if cached.exists() and cached.stat().st_size > 20000:
        return cached
    url = IMAGENS_APROVADAS.get(estilo, IMAGENS_APROVADAS["psych"])
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and len(r.content) > 10000:
            cached.write_bytes(r.content)
            return cached
    except: pass
    return None

def animar_ltx(img_path, prompt_movimento):
    """
    Anima imagem via LTX-Video HuggingFace (GRATUITO)
    
    Equivalente ao Robonil:
    - Input: imagem estática
    - Output: vídeo 5-10 segundos com movimento natural
    - Prompt: "natural gentle movement toward camera"
    """
    if not HF_TOKEN:
        return None  # Sem token → usa Ken Burns

    img_bytes = img_path.read_bytes()
    img_b64 = base64.b64encode(img_bytes).decode()

    payload = {
        "inputs": {
            "image": img_b64,
            "prompt": prompt_movimento,
            "num_frames": 25,
            "num_inference_steps": 25,
            "guidance_scale": 3.0,
            "height": 480,
            "width": 848,
        }
    }
    headers = {"Content-Type": "application/json"}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"

    for model_url in LTX_MODELS:
        try:
            r = requests.post(model_url, headers=headers, json=payload, timeout=120)
            if r.status_code == 200 and len(r.content) > 10000:
                out = TMP / f"animated_{hash(str(img_path))}.mp4"
                out.write_bytes(r.content)
                return out
            elif r.status_code == 503:
                time.sleep(20)  # Modelo carregando
        except: pass
    return None

def ken_burns_free(img_path, duracao=7, zoom_type="in"):
    """
    Alternativa gratuita ILIMITADA ao LTX-Video.
    Ken Burns effect = zoom + pan = mesmo resultado visual do Robonil.
    FFmpeg nativo, zero custo, zero limite.
    """
    out = TMP / f"kb_{img_path.stem}_{zoom_type}.mp4"
    if zoom_type == "in":
        vf = (f"scale=8000:-1,zoompan=z='min(zoom+0.0015,1.5)':d={duracao*25}:"
              f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps=25:s=1280x720")
    elif zoom_type == "out":
        vf = (f"scale=8000:-1,zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))':"
              f"d={duracao*25}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps=25:s=1280x720")
    else:  # pan lateral
        vf = (f"scale=8000:-1,zoompan=z='1.3':d={duracao*25}:"
              f"x='(iw-iw/zoom)*on/{duracao*25}':y='ih/2-(ih/zoom/2)':fps=25:s=1280x720")
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(img_path),
        "-vf", vf, "-t", str(duracao), "-c:v", "libx264", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-r", "25", "-an", str(out)],
        capture_output=True, timeout=120)
    return out if out.exists() and out.stat().st_size > 10000 else None

def montar_tiktok(video_base, audio_p, hook_texto, hashtags, produto_nome, out_path):
    """
    Monta vídeo final TikTok Shop com:
    - Vídeo animado (Ken Burns ou LTX)
    - Hook texto no topo (estilo Jéssica do vídeo)
    - Nome do produto no bottom
    - Hashtags
    - VERTICAL 9:16 (1080x1920)
    """
    hook = hook_texto[:55].replace("'", r"\'")
    prod = produto_nome[:35].replace("'", r"\'")
    tags = hashtags[:60].replace("'", r"\'")

    vf = (
        # Resize para 9:16 TikTok
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        "colorchannelmixer=rr=0.75:gg=0.75:bb=0.75,"
        # Faixa superior para hook
        "drawbox=y=0:color=black@0.80:width=iw:height=160:t=fill,"
        # Faixa inferior para produto + hashtags
        "drawbox=y=ih-180:color=black@0.85:width=iw:height=180:t=fill,"
        # Hook texto (para o scroll!)
        f"drawtext=text='{hook}':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=18:"
        "bold=1:shadowcolor=#000:shadowx=2:shadowy=2:line_spacing=4,"
        # Linha vermelha decorativa
        "drawbox=y=152:color=#EF4444:width=iw:height=3:t=fill,"
        # Nome do produto
        f"drawtext=text='{prod}':fontsize=28:fontcolor=#FCD34D:x=(w-text_w)/2:y=ih-155:bold=1,"
        # Hashtags
        f"drawtext=text='{tags}':fontsize=18:fontcolor=#94A3B8@0.9:x=(w-text_w)/2:y=ih-105,"
        # CTA "🛒 Link na bio"
        "drawtext=text='🛒 Link na bio':fontsize=26:fontcolor=white:x=(w-text_w)/2:y=ih-55:bold=1"
    )

    audio_arg = ["-i", str(audio_p), "-c:a", "aac", "-b:a", "128k"] if audio_p and audio_p.exists() else ["-an"]

    cmd = ["ffmpeg", "-y", "-i", str(video_base)] + audio_arg + ["-vf", vf]
    if audio_p and audio_p.exists():
        cmd += ["-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p", "-r", "25", "-t", "15", str(out_path)]

    subprocess.run(cmd, capture_output=True, timeout=180)
    return out_path.exists() and out_path.stat().st_size > 50000

def salvar_supabase(produto, hook, video_path=""):
    if not SB_KEY: return
    requests.post(f"{SB_URL}/rest/v1/tiktok_shop_queue", headers=SBH,
        json={"produto": produto["nome"], "hook": hook[:200],
              "hashtags": produto["hashtags"],
              "categoria": produto["categoria"],
              "preco_sugerido": produto["preco_sugerido"],
              "estilo_imagem": produto["estilo_imagem"],
              "status": "mp4_ready" if video_path else "pending",
              "video_path": video_path},
        timeout=8)

def run():
    print("=== ROBONIL FREE — TikTok Shop Psychology ===")
    print("Modelo: $5.600 em 7 dias — UGC anônimo sem rosto\n")
    total = 0
    for produto in PRODUTOS_TIKTOK:
        estilo = produto["estilo_imagem"]
        print(f"\n📦 {produto['nome']} ({produto['preco_sugerido']})")
        img = baixar_imagem(estilo)
        if not img:
            print(f"  ⚠️ Imagem {estilo} não disponível")
            continue
        for i, hook in enumerate(produto["hooks"][:2]):  # 2 versões por produto
            print(f"  Hook: {hook[:50]}...")
            # Tentativa 1: LTX-Video (se tiver HF_TOKEN)
            video_base = animar_ltx(img, "natural gentle movement character moves slightly toward camera, gentle breathing motion")
            # Fallback: Ken Burns (sempre gratuito)
            if not video_base:
                zoom = ["in","out","pan"][i % 3]
                video_base = ken_burns_free(img, 7, zoom)
            if video_base:
                out = TMP / f"tiktok_{produto['nome'][:10].replace(' ','_')}_{i}.mp4"
                ok = montar_tiktok(video_base, None, hook, produto["hashtags"], produto["nome"], out)
                if ok:
                    total += 1
                    print(f"  ✅ Vídeo TikTok: {out.name} ({out.stat().st_size//1024}KB)")
                    salvar_supabase(produto, hook, str(out))
                else:
                    salvar_supabase(produto, hook)
                    print(f"  📝 Script salvo no Supabase")
            else:
                salvar_supabase(produto, hook)
    print(f"\n{'='*48}")
    print(f"  ✅ {total} vídeos TikTok prontos")
    print(f"  🎯 Estratégia: UGC anônimo = zero rosto")
    print(f"  📱 Formato: 9:16 vertical, 7-15s, hook no topo")
    print(f"  🛒 TikTok Shop: link na bio = vendas afiliado")
    print(f"  💸 Modelo comprovado: R$5.600/semana")

if __name__ == "__main__":
    run()
