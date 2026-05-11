#!/usr/bin/env python3
"""
thumbnail_gen.py — Gerador automático de thumbnails via Flux.1 Schnell (NVIDIA)
Gera imagens cinematográficas SEM TEXTO para cada vídeo publicado
"""
import os, json, requests, base64, time
from datetime import datetime, timezone

SBU = os.getenv("SBU","https://tpjvalzwkqwttvmszvie.supabase.co")
SBK = os.getenv("SBK","")
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY","")
H_SB = {"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def sb(method, path, data=None):
    r = requests.request(method, SBU+"/rest/v1/"+path, headers=H_SB, json=data, timeout=15)
    try: return r.json()
    except: return {}

def gerar_thumbnail_prompt(titulo, topico, serie=None):
    """Gera prompt cinematográfico para thumbnail sem texto"""
    paleta = {
        "narcisismo": "dark moody purple and red, dramatic shadows, intense expression",
        "apego": "warm blue and violet, soft emotional lighting, vulnerability",
        "ansiedade": "cool teal and blue, restless energy, dynamic movement",
        "trauma": "deep purple and dark blue, healing light breaking through darkness",
        "burnout": "exhausted orange and gray, dim light, quiet despair transitioning to hope",
        "autossabotagem": "introspective cool blue, mirror reflection concept, duality",
        "gaslighting": "distorted perception, green and purple light, confusion",
        "depressao": "muted blues and grays, heavy atmosphere, single warm light",
        "default": "cinematic neutral with warm Brazilian skin tone, professional psychological setting"
    }
    
    tema = topico or "default"
    cores = paleta.get(tema, paleta["default"])
    serie_ctx = f", part of {serie} series" if serie else ""
    
    return (
        f"Cinematic portrait of a thoughtful Brazilian woman in her 30s, "
        f"psychologist aesthetic, {cores}, "
        f"ultra-realistic, film-quality lighting, "
        f"emotional depth, no text, no words, no subtitles, "
        f"psychology theme{serie_ctx}, "
        f"shot on RED camera, 16:9 aspect ratio, "
        f"high contrast, professional color grade"
    )

def gerar_flux_image(prompt):
    """Gera imagem via Flux.1 Schnell NVIDIA API"""
    if not NVIDIA_KEY:
        log("❌ Sem NVIDIA_API_KEY"); return None
    
    log(f"Gerando imagem: {prompt[:60]}...")
    
    headers = {
        "Authorization": f"Bearer {NVIDIA_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "prompt": prompt,
        "negative_prompt": "text, words, letters, numbers, subtitles, watermark, blurry, low quality, cartoon, anime",
        "cfg_scale": 3.5,
        "num_inference_steps": 4,
        "width": 1280,
        "height": 720,
        "seed": -1
    }
    
    r = requests.post(
        "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell",
        headers=headers, json=payload, timeout=60
    )
    
    if r.ok:
        data = r.json()
        artifacts = data.get("artifacts",[])
        if artifacts:
            img_b64 = artifacts[0].get("base64","")
            if img_b64:
                return base64.b64decode(img_b64)
    
    log(f"❌ Erro Flux: {r.status_code} {r.text[:100]}")
    return None

def upload_thumbnail(pipeline_id, image_bytes):
    """Upload thumbnail para Supabase Storage"""
    filename = f"thumbs/{pipeline_id}/thumbnail.jpg"
    
    r = requests.post(
        f"{SBU}/storage/v1/object/videos/{filename}",
        headers={
            "apikey": SBK,
            "Authorization": f"Bearer {SBK}",
            "Content-Type": "image/jpeg",
            "x-upsert": "true"
        },
        data=image_bytes,
        timeout=30
    )
    
    if r.ok or r.status_code == 200:
        url = f"{SBU}/storage/v1/object/public/videos/{filename}"
        log(f"✅ Thumbnail: {url}")
        return url
    
    log(f"❌ Upload erro: {r.status_code}")
    return None

def main():
    log("=== Thumbnail Generator V1 ===")
    
    # Buscar vídeos sem thumbnail
    videos = sb("GET", "content_pipeline?status=eq.mp4_ready&thumbnail_url=is.null&limit=3")
    if not isinstance(videos, list) or not videos:
        # Tentar published sem thumbnail
        videos = sb("GET", "content_pipeline?status=eq.published&thumbnail_url=is.null&limit=3")
    
    if not isinstance(videos, list) or not videos:
        log("Nenhum vídeo sem thumbnail encontrado")
        return
    
    log(f"Gerando thumbnails para {len(videos)} vídeos")
    
    for v in videos:
        vid_id = v["id"]
        titulo = v.get("title","")
        meta   = v.get("metadata") or {}
        topico = meta.get("topico","")
        serie  = meta.get("serie","")
        
        log(f"\nProcessando: {titulo[:50]}")
        
        # Gerar prompt
        prompt = gerar_thumbnail_prompt(titulo, topico, serie)
        
        # Gerar imagem
        img_bytes = gerar_flux_image(prompt)
        if not img_bytes:
            log(f"⚠️ Pulando: {titulo[:30]}")
            continue
        
        # Upload
        thumb_url = upload_thumbnail(vid_id, img_bytes)
        if thumb_url:
            # Atualizar pipeline
            sb("PATCH", f"content_pipeline?id=eq.{vid_id}", {
                "thumbnail_url": thumb_url,
                "metadata": {**meta, "thumbnail_generated": True, "thumbnail_at": datetime.now(timezone.utc).isoformat()}
            })
            log(f"✅ Thumbnail salvo para pipeline {vid_id}")
        
        time.sleep(2)  # Rate limiting

if __name__ == "__main__":
    main()
