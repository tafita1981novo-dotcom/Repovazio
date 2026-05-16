#!/usr/bin/env python3
"""
render_video_v9.py — psicologia.doc V9 MOTION AI
CORREÇÕES APLICADAS:
  ✅ FFmpeg drawtext: removido fontweight (não existe), fixed "Saude Mental"
  ✅ Gemini: log de erros detalhado, retry com backoff, modelos corretos
  ✅ Groq: response_format removido, parsing robusto
  ✅ Veo 3.x para cenas-chave (real motion)
  ✅ RATE_REAL dinâmico (len(script)/dur_audio, NUNCA hardcoded)
  ✅ Lower third SEM Psicóloga até jan/2027
  ✅ 🔔 Inscreva-se agora nos últimos 4s
  ✅ Anti-plágio em TODOS os prompts
  ✅ Fundo creme #F5F0E8 Psych2Go (NUNCA escuro)
  ✅ crf=25 Shorts, crf=22 Longs
  ✅ Ken Burns suave para cenas estáticas
"""
import os, sys, json, time, base64, asyncio, subprocess
import re, requests, traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── CONFIG ────────────────────────────────────────────────────────────────────
SB_URL      = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY      = os.environ.get("SUPABASE_SERVICE_KEY", "")
GROQ_KEY    = os.environ.get("GROQ_API_KEY", "")
GEMINI_KEY  = os.environ.get("GEMINI_API_KEY", "")
GEMINI_KEY2 = os.environ.get("GEMINI_API_KEY_2", "")

VIDEO_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 683
TS       = int(time.time())
WORK_DIR = Path(f"/tmp/v9_{VIDEO_ID}_{TS}")
WORK_DIR.mkdir(parents=True, exist_ok=True)

TTS_VOICE   = "pt-BR-AntonioNeural"
# CORRETO: "Saude Mental" (não "Metal")
LOWER_THIRD = "Daniela Coelho | Saude Mental | @psidanielacoelho"
CRF_SHORT   = 25
CRF_LONG    = 22
VEO_BUDGET  = 8

GEMINI_MODELS_IMG = [
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image-preview",
    "gemini-2.0-flash-exp-image-generation",
    "imagen-3.0-generate-002",
]
VEO_MODELS = [
    "veo-3.1-generate-preview",
    "veo-3.0-generate-preview",
    "veo-2.0-generate-001",
]
ANTI_PLAGIO = (
    "original character design not based on any existing IP, "
    "no text, no logos, no brand marks, no watermarks"
)
PSYCH2GO_BASE = (
    "Psych2Go animation style, kawaii chibi anime character, "
    "cream white background #F5F0E8, pastel warm colors, "
    "round big expressive eyes, clean soft lines"
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
    user = f"""Script PT-BR (canal psicologia):
{script}

Para cada um dos {n} parágrafos, gere JSON. Retorne EXATAMENTE array JSON com {n} objetos:
[{{"img":"english chibi image prompt","veo":"english 8s motion clip prompt","key":true/false,"emotion":"neutral"}}]

- img: prompt imagem chibi estática (kawaii, psych2go style)
- veo: prompt clip animado 8s com movimento real (max {VEO_BUDGET} com key=true)
- key: true apenas para cenas de revelação/clímax emocional (max {VEO_BUDGET})
- emotion: neutral|surprised|concerned|happy|focused|dramatic

RETORNE APENAS O ARRAY JSON. Nenhum texto antes ou depois."""

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
    return [{"img":f"kawaii chibi {emotions[i%8]} psychology channel character",
             "veo":f"chibi character explains psychology, {emotions[i%8]} gesture, natural movement",
             "key": i < min(VEO_BUDGET, n//3), "emotion": emotions[i%8]}
            for i in range(n)]

# ── GEMINI IMAGE ──────────────────────────────────────────────────────────────
def gemini_generate_image(prompt, key):
    """
    Gera imagem chibi com Gemini Image.
    Tenta múltiplos modelos com log detalhado.
    """
    full_prompt = f"{PSYCH2GO_BASE}, {prompt}. {ANTI_PLAGIO}"
    
    for model in GEMINI_MODELS_IMG:
        try:
            if model == "imagen-3.0-generate-002":
                # Imagen tem endpoint diferente
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateImages?key={key}"
                payload = {
                    "prompt": {"text": full_prompt},
                    "numberOfImages": 1,
                    "aspectRatio": "9:16",
                    "safetySettings": {"category": "BLOCK_ONLY_HIGH"}
                }
                r = requests.post(url, json=payload, timeout=60)
                if r.status_code == 200:
                    imgs = r.json().get("generatedImages",[])
                    if imgs:
                        b64 = imgs[0].get("image",{}).get("imageBytes","")
                        if b64: return base64.b64decode(b64)
                print(f"      Imagen {r.status_code}: {r.text[:100]}")
                continue
            
            # generateContent para modelos gemini-*-image
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {"responseModalities": ["IMAGE","TEXT"]}
            }
            r = requests.post(url, json=payload, timeout=60)
            
            if r.status_code == 429:
                print(f"      {model}: quota limit, aguardando 5s...")
                time.sleep(5)
                # Retry uma vez
                r = requests.post(url, json=payload, timeout=60)
            
            if r.status_code != 200:
                print(f"      {model}: HTTP {r.status_code} — {r.text[:80]}")
                continue
            
            for part in r.json().get("candidates",[{}])[0].get("content",{}).get("parts",[]):
                if "inlineData" in part:
                    return base64.b64decode(part["inlineData"]["data"])
            
            print(f"      {model}: sem imagem na resposta")
        
        except Exception as e:
            print(f"      {model}: {str(e)[:60]}")
    
    raise ValueError("Todos os modelos Gemini Image falharam")

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
            if r.status_code in (400,403,404):
                print(f"      {model}: HTTP {r.status_code}")
                continue
            if r.status_code not in (200,202):
                print(f"      {model}: HTTP {r.status_code} {r.text[:60]}")
                continue
            
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
            print(f"      {model}: {str(e)[:60]}")
    raise ValueError("Veo indisponível (paid preview ou quota esgotada)")

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
    z = "min(zoom+0.0012,1.25)" if idx%2==0 else "if(lte(zoom,1.0),1.25,max(1.0,zoom-0.0012))"
    vf = (f"scale=1200:2133,zoompan=z='{z}':d={df}:"
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
    """Creme sólido — fallback quando Gemini falha"""
    clip_p = WORK_DIR / f"clip_{idx:03d}.mp4"
    subprocess.run([
        "ffmpeg","-y","-f","lavfi",
        "-i",f"color=c=0xF5F0E8:s=1080x1920:d={duration}:r=30",
        "-c:v","libx264","-pix_fmt","yuv420p",str(clip_p)
    ], check=True, capture_output=True)
    return clip_p

# ── FINALIZE ──────────────────────────────────────────────────────────────────
def finalize_video(concat_path, audio_path, out_path, total_dur, is_long):
    """
    Overlays + áudio final.
    CORRIGIDO: removido fontweight=bold (não existe no ffmpeg drawtext)
    Lower third: "Daniela Coelho | Saude Mental | @psidanielacoelho" (SEM Psicóloga)
    """
    crf = CRF_LONG if is_long else CRF_SHORT
    end_start = max(0.0, total_dur - 4.0)
    
    # Usar aspas simples escapadas para o texto
    lt = LOWER_THIRD.replace("'", "\\'")
    
    # CORRIGIDO: sem fontweight, sem font não disponível
    vf = (
        # Lower third (SEM Psicóloga até jan/2027)
        f"drawtext=text='{lt}'"
        f":fontsize=26:fontcolor=white"
        f":x=(w-text_w)/2:y=h-75"
        f":box=1:boxcolor=black@0.65:boxborderw=8,"
        # Progress bar violeta
        f"drawbox=x=0:y=h-10"
        f":w='min(iw\\,iw*t/{total_dur:.3f})':h=10"
        f":color=0x7C3AED:t=fill,"
        # 🔔 Inscreva-se nos últimos 4s
        f"drawtext=text='Inscreva-se agora'"
        f":fontsize=40:fontcolor=0x7C3AED"
        f":x=(w-text_w)/2:y=h/2+200"
        f":box=1:boxcolor=white@0.88:boxborderw=16"
        f":enable='gte(t\\,{end_start:.3f})'"
    )
    
    result = subprocess.run([
        "ffmpeg","-y",
        "-i",str(concat_path),
        "-i",str(audio_path),
        "-vf",vf,
        "-c:v","libx264","-crf",str(crf),"-preset","fast",
        "-c:a","aac","-b:a","128k",
        "-pix_fmt","yuv420p","-shortest",
        str(out_path)
    ], capture_output=True, timeout=600)
    
    if result.returncode != 0:
        print(f"FFmpeg stderr: {result.stderr.decode(errors='replace')[-500:]}")
        raise subprocess.CalledProcessError(result.returncode, "ffmpeg")

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"  ψ V9 MOTION AI — Video #{VIDEO_ID}")
    print(f"{'='*60}")
    
    rows = sb_get("content_pipeline", f"id=eq.{VIDEO_ID}&select=id,title,script,audio_url,status")
    if not rows: sys.exit(f"❌ Vídeo {VIDEO_ID} não encontrado")
    row = rows[0]
    title, script = row["title"], row["script"]
    print(f"\n📄 {title}")
    print(f"   {len(script)} chars | {row['status']}")
    
    is_long  = len(script) > 4000
    n_scenes = 50 if is_long else 20
    
    # Áudio
    audio_path = WORK_DIR / "audio.mp3"
    if row.get("audio_url"):
        print(f"\n🎙️  Usando áudio existente...")
        ar = requests.get(row["audio_url"], timeout=60)
        ar.raise_for_status(); audio_path.write_bytes(ar.content)
    else:
        print(f"\n🎙️  Gerando TTS AntonioNeural...")
        generate_tts(script, audio_path)
        ap = sb_upload(f"videos/audios/v{VIDEO_ID}_v9_{TS}.mp3", audio_path, "audio/mpeg")
        sb_patch("content_pipeline", VIDEO_ID, {"audio_url": ap})
    
    # Timing DINÂMICO (NUNCA hardcoded)
    dur_audio = get_audio_duration(audio_path)
    rate_real = len(script) / dur_audio
    print(f"\n⏱️  {dur_audio:.1f}s | RATE_REAL={rate_real:.2f} chars/s")
    
    # Parágrafos
    paragraphs = [p.strip() for p in script.split("\n") if p.strip()]
    actual_n   = min(len(paragraphs), n_scenes)
    scene_durs = [max(1.5, min(len(p)/rate_real, 15.0)) for p in paragraphs[:actual_n]]
    print(f"   {actual_n} cenas | ~{sum(scene_durs):.0f}s")
    
    # Prompts Groq
    print(f"\n🧠 Groq: {actual_n} prompts de cena...")
    scenes = generate_scene_prompts(script, paragraphs[:actual_n])
    key_n  = sum(1 for s in scenes if s.get("key"))
    print(f"   {key_n} key (Veo) | {actual_n-key_n} normal (Gemini)")
    
    # Referência de personagem
    print(f"\n🎨 Referência Gemini Image...")
    ref_b64 = None
    gemini_keys = [k for k in [GEMINI_KEY, GEMINI_KEY2] if k]
    for k in gemini_keys:
        try:
            rb = gemini_generate_image(
                "psychology channel host chibi, kawaii anime girl, dark hair, "
                "friendly warm smile, white cream background, full body, neutral pose", k)
            ref_b64 = base64.b64encode(rb).decode()
            print(f"   ✅ Referência: {len(rb)//1024}KB")
            break
        except Exception as e:
            print(f"   Key {k[:20]}: {e}")
    if not ref_b64: print("   ⚠️  Sem referência — Veo usará apenas texto")
    
    # Identificar índices
    veo_indices = []
    vrem = VEO_BUDGET
    for i, s in enumerate(scenes[:actual_n]):
        if s.get("key") and vrem > 0 and ref_b64:
            veo_indices.append(i); vrem -= 1
    gem_indices = [i for i in range(actual_n) if i not in veo_indices]
    
    clips     = [None] * actual_n
    veo_count = 0
    gem_count = 0
    
    # Gemini em paralelo
    print(f"\n🖼️  {len(gem_indices)} cenas Gemini (4 workers)...")
    def render_gem(idx):
        s = scenes[idx] if idx < len(scenes) else {}
        p = s.get("img","kawaii chibi neutral psychology")
        k = gemini_keys[idx % len(gemini_keys)] if gemini_keys else ""
        if not k: return idx, build_fallback_clip(scene_durs[idx], idx), "fallback"
        try:
            b = gemini_generate_image(p, k)
            return idx, build_static_clip(b, scene_durs[idx], idx), "gemini"
        except Exception as e:
            return idx, build_fallback_clip(scene_durs[idx], idx), "fallback"
    
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(render_gem,i):i for i in gem_indices}
        done = 0
        for fut in as_completed(futs):
            idx, clip_p, src = fut.result()
            clips[idx] = clip_p
            if src=="gemini": gem_count += 1
            done += 1
            sys.stdout.write(f"\r   ✅ {done}/{len(gem_indices)}")
            sys.stdout.flush()
    print()
    
    # Veo sequencial
    if veo_indices:
        print(f"\n🎬 {len(veo_indices)} cenas Veo (motion)...")
        for idx in veo_indices:
            s  = scenes[idx] if idx < len(scenes) else {}
            vp = s.get("veo","chibi explains psychology, natural gestures")
            print(f"   [{idx+1:02d}] {vp[:50]}...")
            try:
                gk  = GEMINI_KEY or GEMINI_KEY2
                vid = veo_generate_clip(vp, ref_b64, gk, duration_s=8)
                clips[idx] = build_motion_clip(vid, scene_durs[idx], idx)
                veo_count += 1
            except Exception as e:
                print(f"   ⚠️  {str(e)[:50]} → Gemini fallback")
                try:
                    k = GEMINI_KEY or GEMINI_KEY2
                    b = gemini_generate_image(s.get("img","kawaii chibi"), k)
                    clips[idx] = build_static_clip(b, scene_durs[idx], idx)
                    gem_count += 1
                except:
                    clips[idx] = build_fallback_clip(scene_durs[idx], idx)
    
    print(f"\n   ✅ Veo: {veo_count} | Gemini: {gem_count} | Fallback creme: {actual_n-veo_count-gem_count}")
    
    # Concatenar
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
    
    # Overlays + áudio
    print(f"🎨 Overlays + áudio...")
    out_name = f"v{VIDEO_ID}_v9_{TS}.mp4"
    out_path = WORK_DIR / out_name
    finalize_video(concat_mp4, audio_path, out_path, dur_audio, is_long)
    
    mb = out_path.stat().st_size / 1024 / 1024
    print(f"   ✅ {mb:.1f}MB | {dur_audio:.1f}s | crf={CRF_LONG if is_long else CRF_SHORT}")
    
    # Upload + DB
    print(f"\n☁️  Upload Supabase...")
    pub_url = sb_upload(f"videos/mp4s/{out_name}", out_path)
    sb_patch("content_pipeline", VIDEO_ID, {
        "video_url": pub_url, "status": "pending_credentials",
        "metadata": json.dumps({
            "render_version": "v9",
            "veo_clips": veo_count, "gemini_clips": gem_count,
            "total_clips": actual_n,
            "duration_s": round(dur_audio,2), "rate_real": round(rate_real,3),
            "file_mb": round(mb,2),
            "rendered_at": datetime.utcnow().isoformat(),
            "lower_third": LOWER_THIRD,
            "has_reference_image": ref_b64 is not None,
        })
    })
    
    print(f"\n{'='*60}")
    print(f"  ✅ V9 COMPLETO — #{VIDEO_ID}")
    print(f"  🎬 {pub_url}")
    print(f"  Veo: {veo_count} | Gemini: {gem_count} | {dur_audio:.1f}s | {mb:.1f}MB")
    print(f"{'='*60}")

if __name__ == "__main__":
    try: main()
    except Exception as e:
        print(f"\n❌ ERRO: {e}"); traceback.print_exc(); sys.exit(1)
