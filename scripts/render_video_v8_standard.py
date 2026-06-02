#!/usr/bin/env python3
"""
render_video_v8_standard.py — Render V3 ATIVO
Pipeline: Supabase audio_ready → Pollinations FLUX imagens → Ken Burns → FFmpeg MP4

Bio: Daniela Coelho · Pesquisa e Conteúdo em Psicologia
SEM título profissional até jan/2027
"""
import os, json, time, subprocess, pathlib, hashlib, re
import requests
from PIL import Image

# Config
SB_URL  = os.getenv("SUPABASE_URL",         "https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY  = os.getenv("SUPABASE_SERVICE_KEY", "")
GROQ_K  = os.getenv("GROQ_API_KEY",         "")
VIDEO_ID   = os.getenv("VIDEO_ID", "")
MAX_VIDEOS = int(os.getenv("MAX_VIDEOS", "3"))

SB_H = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}", "Content-Type": "application/json"}

OUT = pathlib.Path("output/renders")
TMP = pathlib.Path("tmp_render")
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)

BRAND_SUB = "Daniela Coelho · Pesquisa e Conteúdo em Psicologia"

def sb_get(table, query="", limit=5):
    url = f"{SB_URL}/rest/v1/{table}?{query}&limit={limit}"
    r = requests.get(url, headers=SB_H, timeout=15)
    return r.json() if r.status_code == 200 else []

def sb_update(table, id_, data):
    url = f"{SB_URL}/rest/v1/{table}?id=eq.{id_}"
    r = requests.patch(url, headers={**SB_H, "Prefer": "return=minimal"},
        json=data, timeout=15)
    if r.status_code >= 400:
        print(f"  ⚠️ sb_update falhou {r.status_code}: {r.text[:120]}")

def upload_to_storage(file_path, vid_id):
    """Upload mp4 ao Supabase Storage, retorna URL pública"""
    storage_path = f"renders/v{vid_id}.mp4"
    url = f"{SB_URL}/storage/v1/object/videos/{storage_path}"
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        r = requests.post(url,
            headers={**SB_H, "Content-Type": "video/mp4", "x-upsert": "true"},
            data=data, timeout=180)
        if r.status_code in (200, 201):
            return f"{SB_URL}/storage/v1/object/public/videos/{storage_path}"
        r2 = requests.put(url,
            headers={**SB_H, "Content-Type": "video/mp4"},
            data=data, timeout=180)
        if r2.status_code in (200, 201, 204):
            return f"{SB_URL}/storage/v1/object/public/videos/{storage_path}"
        print(f"  ⚠️ Storage falhou POST={r.status_code} PUT={r2.status_code}")
    except Exception as e:
        print(f"  Storage erro: {e}")
    return None

def get_image_pollinations(prompt, seed, w=576, h=1024):
    """Busca imagem via Pollinations FLUX — grátis, ilimitado"""
    prompt_enc = requests.utils.quote(prompt[:500])
    url = f"https://image.pollinations.ai/prompt/{prompt_enc}?model=flux&width={w}&height={h}&seed={seed}&nologo=true"
    try:
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and len(r.content) > 10000:
            return r.content
    except Exception as e:
        print(f"  Pollinations erro: {e}")
    return None

def ken_burns(img_path, out_path, duration=4, zoom=4):
    """Ken Burns zoom 0/4/8% via FFmpeg"""
    zooms = [1.0, 1.04, 1.08]
    z = zooms[zoom // 4] if zoom in (0, 4, 8) else 1.04
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(img_path),
        "-vf", f"scale=1080:1920,zoompan=z='{z}+0*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={duration*25}:s=1080x1920",
        "-t", str(duration), "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-r", "25", str(out_path)
    ]
    subprocess.run(cmd, capture_output=True, timeout=60)

def render_video(row):
    vid_id = row["id"]
    titulo = row.get("title", f"video_{vid_id}")
    audio_url = row.get("audio_url") or row.get("audio_path", "") or (row.get("metadata") or {}).get("audio_url", "")
    script_txt = row.get("script", titulo)
    style = row.get("video_style", "animated_slides")
    
    print(f"\n  Renderizando: [{vid_id}] {titulo[:50]}")
    
    # Gerar prompts de imagem via Groq
    prompts = []
    if GROQ_K and script_txt:
        try:
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_K}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile",
                      "messages": [{"role": "user", "content":
                        f"Gere 5 prompts de imagem para Stable Diffusion sobre: {titulo}\n"
                        f"Contexto: {script_txt[:300]}\n"
                        f"Formato: um por linha, estilo kawaii chibi anime, psicologia.\n"
                        f"SEM texto nas imagens. SEM título de psicóloga."}],
                      "max_tokens": 500, "temperature": 0.8}, timeout=30)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                prompts = [l.strip() for l in content.split("\n") if len(l.strip()) > 20][:5]
        except Exception as e:
            print(f"  Groq: {e}")
    
    if not prompts:
        prompts = [f"kawaii chibi anime illustration of {titulo} psychology concept ### text, watermark, nsfw"]
    
    # Baixar imagens
    img_paths = []
    for i, prompt in enumerate(prompts[:5]):
        seed = 9001 + vid_id * 77 + i
        data = get_image_pollinations(prompt, seed)
        if data:
            p = TMP / f"{vid_id}_img_{i}.jpg"
            p.write_bytes(data)
            img = Image.open(p).convert("RGB").resize((1080, 1920), Image.LANCZOS)
            img.save(p)
            img_paths.append(p)
            print(f"    ✅ Imagem {i+1}/5 ({len(data)//1024}KB)")
            time.sleep(2)
    
    if not img_paths:
        print("  ❌ Sem imagens — pulando")
        return False
    
    # Ken Burns em cada imagem
    clip_paths = []
    for i, img_path in enumerate(img_paths):
        clip = TMP / f"{vid_id}_clip_{i}.mp4"
        zoom_val = [0, 4, 8, 4, 0][i % 5]
        ken_burns(img_path, clip, duration=4, zoom=zoom_val)
        if clip.exists() and clip.stat().st_size > 1000:
            clip_paths.append(clip)
    
    if not clip_paths:
        print("  ❌ Sem clips — pulando")
        return False
    
    # Concatenar clips
    concat_list = TMP / f"{vid_id}_concat.txt"
    with open(concat_list, "w") as f:
        for cp in clip_paths:
            f.write(f"file '{cp.resolve()}'\n")
    
    video_sem_audio = TMP / f"{vid_id}_video.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy", str(video_sem_audio)], capture_output=True, timeout=120)
    
    # Adicionar áudio se disponível
    final = OUT / f"{vid_id}_{re.sub(r'[^a-z0-9]', '_', titulo.lower()[:40])}.mp4"
    
    if audio_url and video_sem_audio.exists():
        try:
            audio_data = requests.get(audio_url, timeout=30).content
            audio_path = TMP / f"{vid_id}_audio.mp3"
            audio_path.write_bytes(audio_data)
            subprocess.run(["ffmpeg", "-y", "-i", str(video_sem_audio), "-i", str(audio_path),
                "-c:v", "copy", "-c:a", "aac", "-shortest", str(final)], capture_output=True, timeout=120)
        except Exception as e:
            print(f"  Audio erro: {e}")
            if video_sem_audio.exists():
                video_sem_audio.rename(final)
    else:
        if video_sem_audio.exists():
            video_sem_audio.rename(final)
    
    if final.exists() and final.stat().st_size > 10000:
        print(f"  ✅ {final.name} ({final.stat().st_size//1024}KB)")
        storage_url = upload_to_storage(final, vid_id)
        if storage_url:
            print(f"  ✅ Storage: {storage_url[-40:]}")
        sb_update("content_pipeline", vid_id, {
            "status": "mp4_ready",
            "video_url": storage_url or ""
        })
        return True
    return False

def run():
    print(f"=== RENDER V3 — Pollinations FLUX + Ken Burns ===")
    print(f"    {BRAND_SUB}")
    
    if VIDEO_ID:
        rows = sb_get("content_pipeline", f"id=eq.{VIDEO_ID}")
    else:
        rows = sb_get("content_pipeline", "status=eq.audio_ready&order=id.asc", MAX_VIDEOS)
    
    if not rows:
        print("Nenhum vídeo audio_ready encontrado.")
        return
    
    print(f"\nProcessando {len(rows)} vídeo(s)...")
    ok = 0
    for row in rows:
        if render_video(row):
            ok += 1
    print(f"\n✅ Renderizados: {ok}/{len(rows)}")

if __name__ == "__main__":
    run()
