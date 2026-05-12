#!/usr/bin/env python3
"""
render_quantum_v2.py — Cerebro V14
Renderiza EXCLUSIVAMENTE com padrao quantico Flux.1 Schnell + Ken Burns
REGRAS IMUTAVEIS: Long=15min | Short=50-58s | ZERO texto nas imagens
"""
import os, sys, json, time, requests, base64, random, textwrap
from supabase import create_client

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SB_URL = os.environ["SUPABASE_URL"]
SB_KEY = os.environ["SUPABASE_KEY"]
sb = create_client(SB_URL, SB_KEY)

NVIDIA_KEY  = os.environ.get("NVIDIA_API_KEY","")
GROQ_KEY    = os.environ.get("GROQ_API_KEY","")
OPENAI_KEY  = os.environ.get("OPENAI_API_KEY","")

# REGRAS IMUTAVEIS DO CEREBRO V14
REGRAS = {
    "long_target":   900,   # 15 min
    "long_min":      840,   # 14 min
    "long_max":      960,   # 16 min
    "short_target":   54,   # 54s
    "short_min":      50,   # 50s minimo
    "short_max":      58,   # 58s maximo
    "gate_render":    90,
    "gate_publish":   92,
    "batch_size":      5,
}

# ─── PALETA QUANTICA (Psych2Go BR) ───────────────────────────────────────────
PALETTES = {
    "calmo":         "sky blue #A8D8EA pastel",
    "tenso":         "warm coral red #FF8C6B pastel",
    "empatia":       "warm peach #FFD1BD pastel",
    "esperanca":     "soft mint green #B2D8B2 pastel",
    "urgente":       "amber #FFB347 pastel",
    "contemplativo": "soft lavender #E8C1E8 pastel",
    "melancolico":   "dusty blue #B0C4DE pastel",
    "alivio":        "light mint #C8F0C8 pastel",
    "ansioso":       "pale yellow #FFF3A3 pastel",
    "raiva":         "soft salmon #FFB3B3 pastel",
}

PERSONAGENS = [
    "Brazilian woman 25-30 years old, medium brown skin, dark wavy hair",
    "Brazilian man 28-35 years old, light olive skin, short dark hair",
    "Brazilian woman 35-45 years old, Black skin, natural afro hair",
    "Brazilian man 22-28 years old, light skin, casual clothes",
    "Brazilian woman 40-50 years old, mixed race, shoulder length hair",
    "Brazilian man 30-40 years old, dark skin, friendly face",
    "Brazilian young woman 20-25 years old, tan skin, long straight hair",
    "Brazilian middle-aged man 45-55 years old, salt-pepper hair",
]

SHOT_TYPES = [
    "extreme close-up face, filling entire frame, massive expressive eyes",
    "medium shot from waist up, centered, neutral background",
    "wide shot full body, centered, simple background",
    "close-up chest and head, 3/4 angle, expressive",
    "portrait shot head and shoulders, direct gaze at viewer",
]

def detectar_emocao(titulo: str, script: str) -> str:
    t = (titulo + " " + script[:300]).lower()
    if any(x in t for x in ["ansio","panico","medo","abandono","apego"]): return "ansioso"
    if any(x in t for x in ["trauma","dor","ferida","abuso"]): return "melancolico"
    if any(x in t for x in ["narcis","manipu","toxico","abusivo"]): return "tenso"
    if any(x in t for x in ["burnout","esgota","cansa"]): return "urgente"
    if any(x in t for x in ["cura","supera","evolui","cresci"]): return "esperanca"
    if any(x in t for x in ["limites","autoestima","valoriza"]): return "empatia"
    return "contemplativo"

def gerar_prompt_quantico(titulo: str, script: str, emocao: str) -> str:
    personagem = random.choice(PERSONAGENS)
    shot = random.choice(SHOT_TYPES)
    paleta = PALETTES.get(emocao, PALETTES["contemplativo"])
    
    # Expressao por emocao
    expressoes = {
        "ansioso": "wide anxious eyes, worried expression, slightly trembling",
        "melancolico": "sad thoughtful expression, downcast eyes, contemplative",
        "tenso": "alert suspicious expression, narrowed eyes, tense jaw",
        "urgente": "urgent concerned expression, raised eyebrows, intense",
        "esperanca": "warm hopeful smile, soft gentle eyes, optimistic",
        "empatia": "compassionate warm smile, kind eyes, understanding",
        "contemplativo": "thoughtful pensive expression, slightly tilted head",
        "calmo": "peaceful serene expression, soft eyes, slight smile",
        "alivio": "relieved gentle smile, relaxed posture, open expression",
    }
    expr = expressoes.get(emocao, "thoughtful expressive face")
    
    return (
        f"flat 2D vector art illustration, educational animation style, "
        f"{shot}, {personagem}, {expr}, "
        f"solid {paleta} background, bold clean outlines, "
        f"Psych2Go style, single character centered, emotional educational, "
        f"NO text NO words NO letters NO numbers NO logos NO watermarks "
        f"NO brand marks ZERO text in image ZERO writing"
    )

def gerar_imagem_flux(prompt: str, video_id: int) -> str | None:
    """Gera imagem com Flux.1 Schnell NVIDIA — ZERO texto garantido"""
    if not NVIDIA_KEY:
        return None
    try:
        resp = requests.post(
            "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux-schnell",
            headers={"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"},
            json={"prompt": prompt, "width": 1344, "height": 768,
                  "num_inference_steps": 4, "guidance_scale": 0.0,
                  "num_images": 1, "seed": random.randint(1, 999999)},
            timeout=60
        )
        if resp.status_code == 200:
            data = resp.json()
            b64 = data.get("artifacts",[{}])[0].get("base64","")
            if b64:
                # Upload para Supabase Storage
                img_bytes = base64.b64decode(b64)
                fname = f"v2/img_{video_id}_{int(time.time())}.jpg"
                sb.storage.from_("videos").upload(
                    fname, img_bytes,
                    file_options={"content-type":"image/jpeg","x-upsert":"true"}
                )
                return f"{SB_URL}/storage/v1/object/public/videos/{fname}"
    except Exception as e:
        print(f"  FLUX erro: {e}")
    return None

def get_videos_pendentes() -> list:
    """Busca vídeos mp4_ready sem mp4_url quântico"""
    r = sb.table("content_pipeline").select(
        "id,title,script,audio_url,metadata,score"
    ).eq("status","mp4_ready").is_("mp4_url",None).order("id").limit(REGRAS["batch_size"]).execute()
    return r.data or []

def processar_video(v: dict) -> bool:
    vid_id = v["id"]
    title  = v.get("title","")
    script = v.get("script","") or ""
    audio  = v.get("audio_url","")
    
    print(f"  #{vid_id} {title[:55]}")
    
    if not audio:
        print(f"    ⚠ sem audio — pulando")
        return False
    
    emocao = detectar_emocao(title, script)
    print(f"    emoção: {emocao}")
    
    # Gerar imagem quântica
    prompt = gerar_prompt_quantico(title, script, emocao)
    img_url = gerar_imagem_flux(prompt, vid_id)
    
    if not img_url:
        print(f"    ⚠ imagem falhou")
        # Marcar como erro temporário para retry
        sb.table("content_pipeline").update({
            "metadata": (v.get("metadata") or {}) | {"quantum_retry": True, "last_attempt": int(time.time())}
        }).eq("id", vid_id).execute()
        return False
    
    print(f"    ✓ imagem: {img_url}")
    
    # Construir mp4 via Ken Burns (script externo roda no mesmo runner)
    # Por agora: marcar como video_ready com a imagem para o runner de ffmpeg
    sb.table("content_pipeline").update({
        "status": "video_ready",
        "mp4_url": None,  # será preenchido pelo ffmpeg
        "metadata": (v.get("metadata") or {}) | {
            "quantum_image": img_url,
            "emocao": emocao,
            "render_method": "flux_kenburns_v2",
            "prompt_quantico": prompt[:200],
            "processado_em": int(time.time()),
            "cerebro_v14": True,
        }
    }).eq("id", vid_id).execute()
    print(f"    ✓ marcado video_ready")
    return True

def main():
    print(f"=== RENDER QUANTICO V2 — Cerebro V14 ===")
    print(f"Regras: long={REGRAS['long_target']}s | short={REGRAS['short_target']}s | gate={REGRAS['gate_render']}")
    
    videos = get_videos_pendentes()
    print(f"Encontrados {len(videos)} vídeos para render quantico")
    
    ok = 0
    for v in videos:
        try:
            if processar_video(v):
                ok += 1
            time.sleep(2)
        except Exception as e:
            print(f"  ERRO #{v.get('id')}: {e}")
    
    print(f"\nConcluido: {ok}/{len(videos)} vídeos processados")
    
    # Registrar evolucao
    try:
        sb.table("cerebro_evolucao").insert({
            "versao": "v14",
            "tipo": "render_quantico",
            "descricao": f"Batch render V2: {ok}/{len(videos)} ok",
            "mudancas": {"batch": ok, "total": len(videos), "metodo": "flux_kenburns_v2"}
        }).execute()
    except: pass

if __name__ == "__main__":
    main()
