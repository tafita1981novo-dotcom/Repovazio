#!/usr/bin/env python3
"""
render_video_v9.py — psicologia.doc V9 MOTION AI
Image generation: Pollinations.ai/Flux (primary, free, sem API key)
                  + NVIDIA (fallback) + Gemini (fallback) + creme (último recurso)

TODAS CORREÇÕES APLICADAS:
  ✅ Pollinations.ai Flux como gerador principal (gratuito, sem API key)
  ✅ Gemini Image como fallback (se NVIDIA falhar)
  ✅ Veo 3.x para cenas-chave com real motion
  ✅ reference_image: personagem consistente (NVIDIA gera referência)
  ✅ RATE_REAL dinâmico (len(script)/dur_audio — NUNCA hardcoded)
  ✅ Lower third: "Daniela Coelho | Saude Mental | @psidanielacoelho"
  ✅ SEM Psicóloga até jan/2027
  ✅ 🔔 Inscreva-se agora nos últimos 4s (sem fontweight=bold)
  ✅ Anti-plágio: "original character design not based on any existing IP"
  ✅ Fundo creme #F5F0E8 Psych2Go (NUNCA escuro)
  ✅ crf=25 Shorts (~3MB), crf=22 Longs (~18MB)
  ✅ Ken Burns suave para imagens estáticas
"""
import os, sys, json, time, base64, asyncio, subprocess
import re, requests, traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── CONFIG ────────────────────────────────────────────────────────────────────
SB_URL       = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY       = os.environ.get("SUPABASE_SERVICE_KEY", "")
GROQ_KEY     = os.environ.get("GROQ_API_KEY", "")
GEMINI_KEY   = os.environ.get("GEMINI_API_KEY", "")
GEMINI_KEY2  = os.environ.get("GEMINI_API_KEY_2", "")
NVIDIA_KEY   = os.environ.get("NVIDIA_API_KEY", "")

VIDEO_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 683
TS       = int(time.time())
WORK_DIR = Path(f"/tmp/v9_{VIDEO_ID}_{TS}")
WORK_DIR.mkdir(parents=True, exist_ok=True)

TTS_VOICE   = "pt-BR-AntonioNeural"
LOWER_THIRD = "Daniela Coelho | Saude Mental | @psidanielacoelho"
CRF_SHORT   = 25
CRF_LONG    = 22
VEO_BUDGET  = 8

# Gemini fallback (raramente usado — Pollinations é primary)
GEMINI_MODELS_IMG = [
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image-preview",
]

VEO_MODELS = [
    "veo-3.1-generate-preview",
    "veo-3.0-generate-preview",
    "veo-2.0-generate-001",
]

ANTI_PLAGIO = (
    "original character design not based on any existing IP, "
    "no text, no logos, no brand marks"
)
PSYCH2GO_BASE = (
    "Psych2Go animation style, kawaii chibi anime character, "
    "cream white background #F5F0E8, pastel warm colors, "
    "round big expressive eyes, clean soft lines, "
    "professional psychology channel"
)

# ── SUPABASE ──────────────────────────────────────────────────────────────────
def sb_get(table, qs=""):
    r = requests.get(f"{SB_URL}/rest/v1/{table}?{qs}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=30)
    r.raise_for_status(); return r.json()

def sb_patch(table, id_, data):
    r = requests.patch(f"{SB_URL}/rest/v1/{table}?id=eq.{id_}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"},
        json=data, timeout=30)
    r.raise_for_status(); return r.json()

def sb_upload(storage_path, file_path, ctype="video/mp4"):
    with open(file_path,"rb") as f: data = f.read()
    r = requests.post(f"{SB_URL}/storage/v1/object/{storage_path}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":ctype,"x-upsert":"true"},
        data=data, timeout=300)
    r.raise_for_status()
    return f"{SB_URL}/storage/v1/object/public/{storage_path}"

# ── TTS ───────────────────────────────────────────────────────────────────────
async def _tts_async(text, path):
    import edge_tts
    await edge_tts.Communicate(text, TTS_VOICE).save(path)

def generate_tts(script, out_path):
    asyncio.run(_tts_async(script, str(out_path)))

def get_audio_duration(path):
    r = subprocess.run(
        ["ffprobe","-v","quiet","-print_format","json","-show_streams",str(path)],
        capture_output=True, text=True)
    for s in json.loads(r.stdout).get("streams",[]):
        if s.get("codec_type") == "audio":
            return float(s.get("duration",60))
    return 60.0

# ── GROQ: prompts de cena ─────────────────────────────────────────────────────
def generate_scene_prompts(script, paragraphs):
    n = len(paragraphs)
    user = f"""Script PT-BR (canal psicologia @psidanielacoelho):
{script}

Para cada um dos {n} parágrafos, gere JSON array com {n} objetos:
[{{"img":"english chibi prompt for stable diffusion","veo":"english 8s motion clip prompt","key":true/false,"emotion":"neutral"}}]

- img: prompt inglês para FLUX imagem chibi estática (kawaii, psych2go style, creme background)
- veo: prompt clip animado 8s (max {VEO_BUDGET} com key=true)
- key: true apenas para hook/clímax/revelação emocional (máx {VEO_BUDGET})
- emotion: neutral|surprised|concerned|happy|focused|dramatic

RETORNE APENAS O JSON ARRAY."""

    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":user}],
                  "temperature":0.5,"max_tokens":4096},
            timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
        m = re.search(r'\[[\s\S]*\]', content)
        if m: return json.loads(m.group())
    except Exception as e:
        print(f"   ⚠️ Groq: {e}")
    
    emotions = ["neutral","concerned","dramatic","surprised","empathetic","focused","happy","sad"]
    return [{"img":f"kawaii chibi anime girl psychology channel, {emotions[i%8]} expression, "
                   f"psych2go style, cream white background, expressive eyes",
             "veo":f"chibi character explains psychology, {emotions[i%8]} gesture, natural movement",
             "key": i < min(VEO_BUDGET, max(1, n//4)), "emotion": emotions[i%8]}
            for i in range(n)]

# ── POLLINATIONS.AI (principal, grátis, sem API key) ──────────────────────────
def pollinations_generate_image(prompt, seed=42):
    """
    Pollinations.ai — 100% gratuito, sem API key, modelo Flux.
    Requisições SEQUENCIAIS com backoff agressivo em 402.
    """
    import urllib.parse
    full = f"{PSYCH2GO_BASE}, {prompt}. {ANTI_PLAGIO}"
    encoded = urllib.parse.quote(full)
    
    # Tentar diferentes modelos se flux falhar
    models = ["flux", "flux-realism", "turbo"]
    
    for model in models:
        url = (f"https://image.pollinations.ai/prompt/{encoded}"
               f"?width=576&height=1024&seed={seed}&nologo=true&model={model}"
               f"&enhance=true")
        
        for attempt in range(5):
            try:
                r = requests.get(url, timeout=120)
                
                if r.status_code == 402:
                    wait = 15 * (2 ** attempt)  # 15s, 30s, 60s, 120s, 240s
                    wait = min(wait, 90)  # max 90s
                    print(f"      Pollinations 402 (fila cheia, {model}) — aguardando {wait}s [{attempt+1}/5]")
                    time.sleep(wait)
                    continue
                
                if r.status_code == 200:
                    ct = r.headers.get('content-type','')
                    if ct.startswith('image'):
                        print(f"      ✅ Pollinations OK ({model}, {len(r.content)//1024}KB)")
                        return r.content
                    raise ValueError(f"Non-image content-type: {ct}")
                
                raise ValueError(f"HTTP {r.status_code}: {r.text[:60]}")
            
            except ValueError: raise
            except Exception as e:
                if attempt < 4:
                    print(f"      Pollinations exc [{attempt+1}]: {str(e)[:50]}")
                    time.sleep(20)
                else:
                    raise ValueError(f"Pollinations {model}: {e}")
        
        # Esse modelo falhou — tentar próximo
    
    raise ValueError("Pollinations: todos os modelos falharam")

def nvidia_generate_image_fallback(prompt):
    """NVIDIA FLUX fallback"""
    import random as _random
    full = f"{PSYCH2GO_BASE}, {prompt}. {ANTI_PLAGIO}"
    endpoints = [
        ("https://integrate.api.nvidia.com/v1/images/generations",
         {"model":"black-forest-labs/flux-schnell","prompt":full,"n":1,
          "size":"1024x1792","response_format":"b64_json"}),
        ("https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux-schnell",
         {"prompt":full,"width":576,"height":1024,
          "num_inference_steps":4,"guidance_scale":3.5,
          "num_images":1,"seed":_random.randint(1,999999)}),
    ]
    for ep, payload in endpoints:
        try:
            r = requests.post(ep,
                headers={"Authorization":f"Bearer {NVIDIA_KEY}","Content-Type":"application/json"},
                json=payload, timeout=90)
            if r.status_code != 200: continue
            data = r.json()
            b64 = (data.get("artifacts",[{}])[0].get("base64","") or
                   data.get("data",[{}])[0].get("b64_json",""))
            if b64: return base64.b64decode(b64)
        except: continue
    raise ValueError("NVIDIA fallback: todos os endpoints falharam")

# ── GEMINI IMAGE (fallback) ───────────────────────────────────────────────────
def gemini_generate_image(prompt, key):
    """Fallback: Gemini Image se NVIDIA falhar"""
    full = f"{PSYCH2GO_BASE}, {prompt}. {ANTI_PLAGIO}"
    for model in GEMINI_MODELS_IMG:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            r = requests.post(url,
                headers={"Content-Type":"application/json"},
                json={"contents":[{"parts":[{"text":full}]}],
                      "generationConfig":{"responseModalities":["IMAGE","TEXT"]}},
                timeout=60)
            if r.status_code != 200: continue
            for part in r.json().get("candidates",[{}])[0].get("content",{}).get("parts",[]):
                if "inlineData" in part:
                    return base64.b64decode(part["inlineData"]["data"])
        except: continue
    raise ValueError("Gemini Image: todos os modelos falharam")

def generate_image(prompt, idx=0):
    """
    Tenta em ordem: Pollinations.ai (primary, sem key) → NVIDIA → Gemini → ValueError
    """
    # 1. Pollinations.ai — gratuito, sem API key, funciona sempre
    try:
        return pollinations_generate_image(prompt, seed=42 + idx)
    except Exception as e:
        print(f"      Pollinations: {str(e)[:60]} → NVIDIA fallback")
    
    # 2. NVIDIA (se disponível)
    if NVIDIA_KEY:
        try:
            return nvidia_generate_image_fallback(prompt)
        except Exception as e:
            print(f"      NVIDIA: {str(e)[:60]} → Gemini fallback")
    
    # 3. Gemini (raramente funciona, mas tenta)
    gemini_keys = [k for k in [GEMINI_KEY, GEMINI_KEY2] if k]
    k = gemini_keys[idx % len(gemini_keys)] if gemini_keys else ""
    if k:
        try:
            return gemini_generate_image(prompt, k)
        except Exception as e:
            print(f"      Gemini: {str(e)[:40]}")
    
    raise ValueError("Todos os backends de imagem falharam")

# ── VEO 3.x ───────────────────────────────────────────────────────────────────
def veo_generate_clip(veo_prompt, ref_b64, key, duration_s=8):
    full_prompt = f"{PSYCH2GO_BASE}, {veo_prompt}. {ANTI_PLAGIO}"
    for model in VEO_MODELS:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateVideo?key={key}"
            body = {
                "prompt": {"text": full_prompt},
                "image": {"imageBytes": ref_b64, "mimeType": "image/png"},
                "generationConfig": {
                    "durationSeconds": duration_s, "aspectRatio": "9:16",
                    "numberOfVideos": 1, "personGeneration": "ALLOW_ADULT"
                }
            }
            r = requests.post(url, json=body, timeout=60)
            if r.status_code in (400,403,404): continue
            if r.status_code not in (200,202): continue
            
            op = r.json()
            op_name = op.get("name","")
            if not op_name:
                result = _extract_video(op)
                if result: return result
                continue
            
            poll_url = f"https://generativelanguage.googleapis.com/v1beta/{op_name}?key={key}"
            for i in range(48):
                time.sleep(5)
                pd = requests.get(poll_url, timeout=30).json()
                if pd.get("done"):
                    result = _extract_video(pd.get("response",pd))
                    if result:
                        print(f"      ✅ Veo: {model}")
                        return result
                    break
                if i%6==0: print(f"      ⏳ Veo... {(i+1)*5}s")
        except Exception as e:
            print(f"      {model}: {str(e)[:50]}")
    raise ValueError("Veo: indisponível (paid preview)")

def _extract_video(resp):
    samples = resp.get("generatedSamples") or resp.get("videos") or []
    if not samples: return None
    v = samples[0]
    uri = v.get("video",{}).get("uri") or v.get("uri","")
    if uri:
        vr = requests.get(uri, timeout=120)
        if vr.ok: return vr.content
    b64 = v.get("video",{}).get("videoBytes") or v.get("videoBytes","")
    if b64: return base64.b64decode(b64)
    return None

# ── CLIPS ─────────────────────────────────────────────────────────────────────
def build_static_clip(img_bytes, duration, idx):
    img_p  = WORK_DIR / f"img_{idx:03d}.png"
    clip_p = WORK_DIR / f"clip_{idx:03d}.mp4"
    img_p.write_bytes(img_bytes)
    df = max(1, int(duration*30))
    # FLUX gera 576x1024 — escalar para 1080x1920
    z = "min(zoom+0.0012,1.25)" if idx%2==0 else "if(lte(zoom,1.0),1.25,max(1.0,zoom-0.0012))"
    vf = (f"scale=1080:1920:force_original_aspect_ratio=decrease,"
          f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=#F5F0E8,"
          f"zoompan=z='{z}':d={df}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30")
    subprocess.run([
        "ffmpeg","-y","-loop","1","-i",str(img_p),
        "-vf",vf,"-t",str(duration),
        "-c:v","libx264","-pix_fmt","yuv420p","-r","30",str(clip_p)
    ], check=True, capture_output=True, timeout=120)
    return clip_p

def build_motion_clip(video_bytes, target_dur, idx):
    raw_p  = WORK_DIR / f"veo_{idx:03d}.mp4"
    clip_p = WORK_DIR / f"clip_{idx:03d}.mp4"
    raw_p.write_bytes(video_bytes)
    vf = ("scale=1080:1920:force_original_aspect_ratio=decrease,"
          "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=#F5F0E8")
    subprocess.run([
        "ffmpeg","-y","-stream_loop","-1","-i",str(raw_p),
        "-vf",vf,"-t",str(target_dur),
        "-c:v","libx264","-pix_fmt","yuv420p","-r","30",str(clip_p)
    ], check=True, capture_output=True, timeout=120)
    return clip_p

def build_fallback_clip(duration, idx):
    clip_p = WORK_DIR / f"clip_{idx:03d}.mp4"
    subprocess.run([
        "ffmpeg","-y","-f","lavfi",
        "-i",f"color=c=0xF5F0E8:s=1080x1920:d={duration}:r=30",
        "-c:v","libx264","-pix_fmt","yuv420p",str(clip_p)
    ], check=True, capture_output=True)
    return clip_p

# ── OVERLAYS FINAIS ───────────────────────────────────────────────────────────
def finalize_video(concat_path, audio_path, out_path, total_dur, is_long):
    """
    Lower third SEM Psicóloga + progress bar + 🔔 Inscreva-se agora.
    CORRIGIDO: sem fontweight=bold (não existe no ffmpeg drawtext)
    """
    crf = CRF_LONG if is_long else CRF_SHORT
    end_start = max(0.0, total_dur - 4.0)
    lt = LOWER_THIRD.replace("'", "\\'").replace(":", "\\:")
    
    vf = (
        # Lower third
        f"drawtext=text='{lt}'"
        f":fontsize=26:fontcolor=white"
        f":x=(w-text_w)/2:y=h-75"
        f":box=1:boxcolor=black@0.65:boxborderw=8,"
        # Progress bar violeta
        f"drawbox=x=0:y=h-10"
        f":w='min(iw\\,iw*t/{total_dur:.3f})':h=10"
        f":color=0x7C3AED:t=fill,"
        # Inscreva-se nos últimos 4s
        f"drawtext=text='Inscreva-se agora'"
        f":fontsize=40:fontcolor=0x7C3AED"
        f":x=(w-text_w)/2:y=h/2+200"
        f":box=1:boxcolor=white@0.88:boxborderw=16"
        f":enable='gte(t\\,{end_start:.3f})'"
    )
    
    result = subprocess.run([
        "ffmpeg","-y",
        "-i",str(concat_path),"-i",str(audio_path),
        "-vf",vf,
        "-c:v","libx264","-crf",str(crf),"-preset","fast",
        "-c:a","aac","-b:a","128k",
        "-pix_fmt","yuv420p","-shortest",
        str(out_path)
    ], capture_output=True, timeout=600)
    
    if result.returncode != 0:
        err = result.stderr.decode(errors='replace')[-400:]
        print(f"FFmpeg stderr: {err}")
        raise subprocess.CalledProcessError(result.returncode, "ffmpeg")

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"  ψ V9 MOTION AI — Video #{VIDEO_ID}")
    print(f"  Image backend: {'NVIDIA FLUX.1 Schnell' if NVIDIA_KEY else 'Gemini fallback'}")
    print(f"{'='*60}")
    
    # 1. Dados do Supabase
    rows = sb_get("content_pipeline", f"id=eq.{VIDEO_ID}&select=id,title,script,audio_url,status")
    if not rows: sys.exit(f"❌ Vídeo {VIDEO_ID} não encontrado")
    row = rows[0]
    title, script = row["title"], row["script"]
    print(f"\n📄 {title}")
    print(f"   {len(script)} chars | {row['status']}")
    
    is_long  = len(script) > 4000
    n_scenes = 50 if is_long else 20
    
    # 2. Áudio
    audio_path = WORK_DIR / "audio.mp3"
    if row.get("audio_url"):
        print(f"\n🎙️  Usando áudio existente (AntonioNeural)...")
        ar = requests.get(row["audio_url"], timeout=60)
        ar.raise_for_status(); audio_path.write_bytes(ar.content)
    else:
        print(f"\n🎙️  Gerando TTS AntonioNeural...")
        generate_tts(script, audio_path)
        ap = sb_upload(f"videos/audios/v{VIDEO_ID}_v9_{TS}.mp3", audio_path, "audio/mpeg")
        sb_patch("content_pipeline", VIDEO_ID, {"audio_url": ap})
    
    # 3. Timing DINÂMICO (NUNCA hardcoded)
    dur_audio = get_audio_duration(audio_path)
    rate_real = len(script) / dur_audio
    print(f"\n⏱️  {dur_audio:.1f}s | RATE_REAL={rate_real:.2f} chars/s (dinâmico)")
    
    # 4. Parágrafos
    paragraphs = [p.strip() for p in script.split("\n") if p.strip()]
    actual_n   = min(len(paragraphs), n_scenes)
    scene_durs = [max(1.5, min(len(p)/rate_real, 15.0)) for p in paragraphs[:actual_n]]
    print(f"   {actual_n} cenas | ~{sum(scene_durs):.0f}s")
    
    # 5. Prompts Groq
    print(f"\n🧠 Groq: {actual_n} prompts de cena...")
    scenes = generate_scene_prompts(script, paragraphs[:actual_n])
    key_n  = sum(1 for s in scenes if s.get("key"))
    print(f"   {key_n} key (Veo) | {actual_n-key_n} normal (NVIDIA/Gemini)")
    
    # 6. Referência de personagem (NVIDIA FLUX)
    print(f"\n🎨 Referência NVIDIA FLUX.1 Schnell...")
    ref_b64 = None
    master_prompt = (
        "psychology channel host chibi character, kawaii anime girl, dark hair, "
        "warm friendly smile, professional casual outfit, front facing, full body, "
        "cream white background, studio lighting, high quality"
    )
    try:
        ref_bytes = generate_image(master_prompt, idx=0)
        ref_path  = WORK_DIR / "reference.png"
        ref_path.write_bytes(ref_bytes)
        ref_b64   = base64.b64encode(ref_bytes).decode()
        print(f"   ✅ Referência: {len(ref_bytes)//1024}KB")
    except Exception as e:
        print(f"   ⚠️  Referência falhou: {e}")
    
    # 7. Identificar cenas
    veo_indices = []
    vrem = VEO_BUDGET
    for i, s in enumerate(scenes[:actual_n]):
        if s.get("key") and vrem > 0 and ref_b64:
            veo_indices.append(i); vrem -= 1
    img_indices = [i for i in range(actual_n) if i not in veo_indices]
    
    clips     = [None] * actual_n
    veo_count = 0
    img_count = 0
    
    # 8a. Imagens em paralelo (NVIDIA FLUX / Gemini)
    print(f"\n🖼️  {len(img_indices)} imagens NVIDIA FLUX (4 workers)...")
    
    def render_img(idx):
        s = scenes[idx] if idx < len(scenes) else {}
        p = s.get("img","kawaii chibi anime psychology channel character, cream white background")
        try:
            b = generate_image(p, idx)
            # Delay entre imagens para respeitar rate limit do Pollinations
            time.sleep(3)
            return idx, build_static_clip(b, scene_durs[idx], idx), True
        except Exception as e:
            print(f"   [{idx+1:02d}] imagem falhou: {str(e)[:50]}")
            time.sleep(2)  # Delay mesmo no fallback
            return idx, build_fallback_clip(scene_durs[idx], idx), False
    
    with ThreadPoolExecutor(max_workers=1) as ex:  # 1 worker SEQUENCIAL — respeitar rate limit Pollinations
        futs = {ex.submit(render_img,i):i for i in img_indices}
        done = 0
        for fut in as_completed(futs):
            idx, clip_p, ok = fut.result()
            clips[idx] = clip_p
            if ok: img_count += 1
            done += 1
            sys.stdout.write(f"\r   ✅ {done}/{len(img_indices)} imagens")
            sys.stdout.flush()
    print()
    
    # 8b. Veo motion (sequencial)
    if veo_indices:
        print(f"\n🎬 {len(veo_indices)} cenas Veo motion...")
        for idx in veo_indices:
            s  = scenes[idx] if idx < len(scenes) else {}
            vp = s.get("veo","chibi character explains psychology enthusiastically")
            print(f"   [{idx+1:02d}] {vp[:50]}...")
            try:
                gk = GEMINI_KEY or GEMINI_KEY2
                v  = veo_generate_clip(vp, ref_b64, gk, duration_s=8)
                clips[idx] = build_motion_clip(v, scene_durs[idx], idx)
                veo_count += 1
            except Exception as e:
                print(f"   ⚠️  {str(e)[:50]} → FLUX fallback")
                try:
                    b = generate_image(s.get("img","kawaii chibi"), idx)
                    clips[idx] = build_static_clip(b, scene_durs[idx], idx)
                    img_count += 1
                except:
                    clips[idx] = build_fallback_clip(scene_durs[idx], idx)
    
    print(f"\n   ✅ Veo: {veo_count} | FLUX/Gemini: {img_count} | "
          f"Fallback: {actual_n-veo_count-img_count}")
    
    # 9. Concatenar
    print(f"\n🔗 Concatenando {actual_n} clips...")
    ctxt = WORK_DIR / "input.txt"
    with open(ctxt,"w") as f:
        for c in clips:
            if c: f.write(f"file '{c}'\n")
    
    concat_mp4 = WORK_DIR / "concat.mp4"
    subprocess.run([
        "ffmpeg","-y","-f","concat","-safe","0",
        "-i",str(ctxt),
        "-c:v","libx264","-pix_fmt","yuv420p","-r","30",str(concat_mp4)
    ], check=True, capture_output=True, timeout=300)
    
    # 10. Overlays + áudio
    print(f"🎨 Overlays (lower third, progress, 🔔, áudio)...")
    out_name = f"v{VIDEO_ID}_v9_{TS}.mp4"
    out_path = WORK_DIR / out_name
    finalize_video(concat_mp4, audio_path, out_path, dur_audio, is_long)
    
    mb = out_path.stat().st_size / 1024 / 1024
    print(f"   ✅ {mb:.1f}MB | {dur_audio:.1f}s | crf={CRF_LONG if is_long else CRF_SHORT}")
    
    # 11. Upload + DB
    print(f"\n☁️  Upload Supabase...")
    pub_url = sb_upload(f"videos/mp4s/{out_name}", out_path)
    sb_patch("content_pipeline", VIDEO_ID, {
        "video_url": pub_url,
        "status": "pending_credentials",
        "metadata": json.dumps({
            "render_version": "v9",
            "image_backend": "nvidia_flux" if NVIDIA_KEY else "gemini",
            "veo_clips": veo_count,
            "image_clips": img_count,
            "total_clips": actual_n,
            "duration_s": round(dur_audio,2),
            "rate_real": round(rate_real,3),
            "file_mb": round(mb,2),
            "rendered_at": datetime.utcnow().isoformat(),
            "lower_third": LOWER_THIRD,
            "has_reference_image": ref_b64 is not None,
        })
    })
    
    print(f"\n{'='*60}")
    print(f"  ✅ V9 COMPLETO — #{VIDEO_ID}")
    print(f"  🎬 {pub_url}")
    print(f"  FLUX/Gemini: {img_count} | Veo: {veo_count} | {dur_audio:.1f}s | {mb:.1f}MB")
    print(f"{'='*60}")

if __name__ == "__main__":
    try: main()
    except Exception as e:
        print(f"\n❌ ERRO: {e}"); traceback.print_exc(); sys.exit(1)
