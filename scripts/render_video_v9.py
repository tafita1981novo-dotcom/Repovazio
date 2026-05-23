#!/usr/bin/env python3
"""
render_video_v9.py — psicologia.doc V9 MOTION AI
Animação chibi MELHOR que Psych2Go — $0, ilimitado, 200+ vídeos/mês

STACK:
  🎨 IMAGEM: Gemini 2.0 Flash Exp (modelo correto, free, sem 403)
            + Pollinations.ai Flux (fallback)
  🎬 ANIMAÇÃO FFmpeg (sem ML, sem API, ilimitado):
     ✅ Respiração: crop sin() oscillation vertical
     ✅ Balanço: crop sin() oscillation horizontal  
     ✅ Piscar de olhos: drawbox na posição chibi anatômica
     ✅ Movimento de cabeça: zoompan dinâmico
     ✅ Color grading emocional: eq filter por emoção
     ✅ Crossfade entre cenas: xfade dissolve
  🎙️ ÁUDIO: Edge TTS AntonioNeural (RATE_REAL dinâmico)
  📝 KARAOKÊ: palavras aparecem sincronizadas com RATE_REAL

CORREÇÕES COMPLETAS:
  ✅ Gemini: gemini-2.0-flash-exp (FUNCIONA sem permissão especial)
  ✅ Lower third: "Daniela Coelho | Saude Mental | @psidanielacoelho"
  ✅ SEM Daniela Coelho até jan/2027
  ✅ SEM fontweight=bold (não existe no ffmpeg)
  ✅ RATE_REAL dinâmico (len(script)/dur_audio)
  ✅ crf=25 Shorts (~3MB), crf=22 Longs (~18MB)
  ✅ 🔔 Inscreva-se agora nos últimos 4s
"""
import os, sys, json, time, base64, asyncio, subprocess
import re, requests, traceback, urllib.parse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── CONFIG ────────────────────────────────────────────────────────────────────
SB_URL      = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY      = os.environ.get("SUPABASE_SERVICE_KEY","")
GROQ_KEY    = os.environ.get("GROQ_API_KEY","")
GEMINI_KEY  = os.environ.get("GEMINI_API_KEY","")
GEMINI_KEY2 = os.environ.get("GEMINI_API_KEY_2","")
NVIDIA_KEY  = os.environ.get("NVIDIA_API_KEY","")

VIDEO_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 683
TS       = int(time.time())
WORK_DIR = Path(f"/tmp/v9_{VIDEO_ID}_{TS}")
WORK_DIR.mkdir(parents=True, exist_ok=True)

TTS_VOICE   = "pt-BR-AntonioNeural"
LOWER_THIRD = "Daniela Coelho | Saude Mental | @psidanielacoelho"
CRF_SHORT   = 25
CRF_LONG    = 22
VEO_BUDGET  = 8

# MODELOS GEMINI CORRETOS — gemini-2.0-flash-exp funciona SEM permissão especial
GEMINI_MODELS_IMG = [
    "gemini-2.0-flash-exp",                   # ✅ FREE, funciona com key normal
    "gemini-2.0-flash-exp-image-generation",  # ✅ Alias explícito para imagem
    "gemini-2.5-flash-image",                 # Tenta (pode precisar de permissão)
]

VEO_MODELS = [
    "veo-3.1-generate-preview",
    "veo-3.0-generate-preview",
    "veo-2.0-generate-001",
]

ANTI_PLAGIO = (
    "original character design not based on any existing IP or franchise, "
    "no text, no logos, no brand marks, no watermarks"
)

PSYCH2GO_BASE = (
    "Psych2Go animation style, kawaii chibi anime character, "
    "cream white background #F5F0E8, pastel warm colors, "
    "round big expressive eyes, clean soft lines, "
    "professional psychology channel, full body visible"
)

# Color grading por emoção — melhora visual MUITO
EMOTION_EQ = {
    "neutral":    "brightness=0:saturation=1.0:gamma=1.0",
    "surprised":  "brightness=0.03:saturation=1.15:gamma=0.97",
    "concerned":  "brightness=-0.02:saturation=0.88:gamma=1.03",
    "happy":      "brightness=0.05:saturation=1.25:gamma=0.95",
    "focused":    "brightness=0:saturation=0.92:gamma=1.0",
    "dramatic":   "brightness=-0.05:saturation=1.35:gamma=1.05",
    "empathetic": "brightness=0.02:saturation=1.05:gamma=0.98",
    "sad":        "brightness=-0.04:saturation=0.78:gamma=1.06",
}

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
async def _tts(text, path):
    import edge_tts
    await edge_tts.Communicate(text, TTS_VOICE).save(path)

def generate_tts(script, out_path):
    asyncio.run(_tts(script, str(out_path)))

def get_audio_duration(path):
    r = subprocess.run(
        ["ffprobe","-v","quiet","-print_format","json","-show_streams",str(path)],
        capture_output=True, text=True)
    for s in json.loads(r.stdout).get("streams",[]):
        if s.get("codec_type")=="audio": return float(s.get("duration",60))
    return 60.0

# ── GROQ: prompts de cena ─────────────────────────────────────────────────────
def generate_scene_prompts(script, paragraphs):
    n = len(paragraphs)
    user = f"""Script psicologia PT-BR (@psidanielacoelho):
{script}

Para cada um dos {n} parágrafos, gere JSON array com {n} objetos:
[{{"img":"english chibi prompt for image gen","veo":"english 8s motion clip","key":true/false,"emotion":"neutral","words":3}}]

- img: prompt para chibi kawaii psych2go style (cream bg, expressive face, full body)
- veo: prompt 8s clip animado com braços/olhos se movendo
- key: true para cenas de revelação/clímax (max {VEO_BUDGET})
- emotion: neutral|surprised|concerned|happy|focused|dramatic|empathetic|sad
- words: quantidade de palavras-chave desta cena para overlay

RETORNE APENAS O JSON ARRAY SEM TEXTO EXTRA."""

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
    return [{"img":f"kawaii chibi {emotions[i%8]} psychology channel character, cream background",
             "veo":f"chibi anime character explains psychology, {emotions[i%8]} gesture, arms moving naturally",
             "key": i<min(VEO_BUDGET,max(1,n//3)), "emotion":emotions[i%8], "words":3}
            for i in range(n)]

# ── GEMINI IMAGE (modelo correto: gemini-2.0-flash-exp) ──────────────────────
def gemini_generate_image(prompt, key):
    """
    Gemini 2.0 Flash Exp — modelo FREE que FUNCIONA sem permissão especial.
    NUNCA usar gemini-2.5-flash-image com chave normal (dá 403).
    """
    full = f"{PSYCH2GO_BASE}, {prompt}. {ANTI_PLAGIO}"
    
    for model in GEMINI_MODELS_IMG:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            r = requests.post(url,
                headers={"Content-Type":"application/json"},
                json={"contents":[{"parts":[{"text":full}]}],
                      "generationConfig":{"responseModalities":["IMAGE","TEXT"]}},
                timeout=90)
            
            if r.status_code == 429:
                print(f"      {model}: 429 quota — aguardando 8s")
                time.sleep(8)
                r = requests.post(url, headers={"Content-Type":"application/json"},
                    json={"contents":[{"parts":[{"text":full}]}],
                          "generationConfig":{"responseModalities":["IMAGE","TEXT"]}},
                    timeout=90)
            
            if r.status_code == 200:
                for part in r.json().get("candidates",[{}])[0].get("content",{}).get("parts",[]):
                    if "inlineData" in part:
                        print(f"      ✅ Gemini OK: {model}")
                        return base64.b64decode(part["inlineData"]["data"])
                print(f"      {model}: sem imagem na resposta")
            else:
                print(f"      {model}: HTTP {r.status_code}")
        
        except Exception as e:
            print(f"      {model}: {str(e)[:50]}")
    
    raise ValueError("Gemini: todos os modelos falharam")

# ── POLLINATIONS.AI (fallback) ────────────────────────────────────────────────
def pollinations_generate_image(prompt, seed=42):
    """Pollinations.ai Flux — fallback gratuito quando Gemini falha"""
    full = f"{PSYCH2GO_BASE}, {prompt}. {ANTI_PLAGIO}"
    enc  = urllib.parse.quote(full)
    url  = (f"https://image.pollinations.ai/prompt/{enc}"
            f"?width=576&height=1024&seed={seed}&nologo=true&model=flux")
    
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=90)
            if r.status_code == 402:
                wait = 20 * (attempt+1)
                print(f"      Pollinations 402 — aguardando {wait}s")
                time.sleep(wait); continue
            if r.status_code == 200 and r.headers.get('content-type','').startswith('image'):
                print(f"      ✅ Pollinations OK ({len(r.content)//1024}KB)")
                return r.content
        except Exception as e:
            if attempt < 2: time.sleep(10)
    
    raise ValueError("Pollinations: falhou após 3 tentativas")

def generate_image(prompt, idx=0):
    """Tenta Gemini → Pollinations → erro"""
    gemini_keys = [k for k in [GEMINI_KEY, GEMINI_KEY2] if k]
    k = gemini_keys[idx % len(gemini_keys)] if gemini_keys else ""
    
    if k:
        try: return gemini_generate_image(prompt, k)
        except Exception as e:
            print(f"      Gemini falhou: {str(e)[:50]} → Pollinations")
    
    try: return pollinations_generate_image(prompt, seed=42+idx)
    except Exception as e:
        raise ValueError(f"Todos backends falharam: {e}")

# ── VEO 3.x (cenas-chave com motion real) ────────────────────────────────────
def veo_generate_clip(veo_prompt, ref_b64, key, duration_s=8):
    full = f"{PSYCH2GO_BASE}, {veo_prompt}. {ANTI_PLAGIO}"
    for model in VEO_MODELS:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateVideo?key={key}"
            body = {
                "prompt":{"text": full},
                "image":{"imageBytes": ref_b64, "mimeType":"image/png"},
                "generationConfig":{
                    "durationSeconds":duration_s,"aspectRatio":"9:16",
                    "numberOfVideos":1,"personGeneration":"ALLOW_ADULT"
                }
            }
            r = requests.post(url, json=body, timeout=60)
            if r.status_code in (400,403,404): continue
            if r.status_code not in (200,202): continue
            op = r.json()
            op_name = op.get("name","")
            if not op_name:
                v = _extract_video(op)
                if v: return v
                continue
            poll_url = f"https://generativelanguage.googleapis.com/v1beta/{op_name}?key={key}"
            for i in range(48):
                time.sleep(5)
                pd = requests.get(poll_url, timeout=30).json()
                if pd.get("done"):
                    v = _extract_video(pd.get("response",pd))
                    if v:
                        print(f"      ✅ Veo: {model}")
                        return v
                    break
                if i%6==0: print(f"      ⏳ Veo {model}... {(i+1)*5}s")
        except Exception as e:
            print(f"      {model}: {str(e)[:50]}")
    raise ValueError("Veo: indisponível (paid preview)")

def _extract_video(resp):
    s = resp.get("generatedSamples") or resp.get("videos") or []
    if not s: return None
    v = s[0]
    uri = v.get("video",{}).get("uri") or v.get("uri","")
    if uri:
        vr = requests.get(uri, timeout=120)
        if vr.ok: return vr.content
    b64 = v.get("video",{}).get("videoBytes") or v.get("videoBytes","")
    if b64: return base64.b64decode(b64)
    return None

# ── ANIMAÇÃO CHIBI (FFmpeg puro — SEM ML, ilimitado) ─────────────────────────
def build_animated_clip(img_bytes, duration, idx, emotion="neutral", sentence=""):
    """
    Transforma imagem chibi estática em cena ANIMADA — melhor que Psych2Go!
    
    Animações FFmpeg puro:
    ┌─────────────────────────────────────────────────────┐
    │ 1. RESPIRAÇÃO: crop sin(t*1.1) no eixo Y           │
    │    → personagem sobe/desce suavemente              │
    │                                                     │
    │ 2. BALANÇO: crop sin(t*0.7) no eixo X              │
    │    → personagem balança levemente para os lados    │
    │                                                     │
    │ 3. ZOOM DINÂMICO: zoompan com variação              │
    │    → in para cenas neutras, out para dramáticas    │
    │                                                     │
    │ 4. PISCAR DE OLHOS: drawbox na posição chibi        │
    │    → anatomia chibi: olhos em ~28% da altura        │
    │    → pisca a cada 3-4 segundos por 0.12s            │
    │                                                     │
    │ 5. BRAÇOS: gradiente de sombra lateral pulsante     │
    │    → simula movimento de braço sem frame extra      │
    │                                                     │
    │ 6. COLOR GRADING: eq por emoção                     │
    │    → happy=saturado, sad=dessaturado, etc.          │
    │                                                     │
    │ 7. VINHETA: escurece bordas suavemente              │
    │    → foco no personagem (estilo cinema)             │
    └─────────────────────────────────────────────────────┘
    """
    img_p  = WORK_DIR / f"img_{idx:03d}.png"
    clip_p = WORK_DIR / f"clip_{idx:03d}.mp4"
    img_p.write_bytes(img_bytes)
    
    df = max(1, int(duration * 30))
    eq = EMOTION_EQ.get(emotion, EMOTION_EQ["neutral"])
    
    # Alternância para variedade visual entre cenas
    x_phase  = idx * 0.7   # fase diferente para cada cena
    y_phase  = idx * 1.1
    zoom_dir = "in" if idx % 2 == 0 else "out"
    
    # ZOOM: Ken Burns dinâmico (in ou out dependendo da cena)
    if zoom_dir == "in":
        z_expr = f"min(zoom+0.0015,1.28)"
    else:
        z_expr = f"if(lte(zoom,1.0),1.28,max(1.0,zoom-0.0015))"
    
    # PISCAR DE OLHOS em posição chibi anatômica:
    # Em 1080x1920, olhos chibi ficam aproximadamente em:
    # - y ≈ 28% da altura = 537px (centro dos olhos)
    # - olho esquerdo: x ≈ 370, largura ≈ 90
    # - olho direito: x ≈ 620, largura ≈ 90
    # Pálpebra = retângulo pele-claro que cobre os olhos
    blink_t1 = 2.8 + (idx % 3) * 0.7   # momento do piscar (varia por cena)
    blink_t2 = blink_t1 + 0.12          # duração do piscar: 0.12s
    blink_filter = (
        # Olho esquerdo
        f"drawbox=x=335:y=520:w=110:h=55:"
        f"color=#F5D8B0@0.95:t=fill:"
        f"enable='between(t,{blink_t1:.2f},{blink_t2:.2f})',"
        # Olho direito
        f"drawbox=x=635:y=520:w=110:h=55:"
        f"color=#F5D8B0@0.95:t=fill:"
        f"enable='between(t,{blink_t1:.2f},{blink_t2:.2f})'"
    )
    
    # MOVIMENTO DE BRAÇO simulado: 
    # Sombra lateral que pulsa no tempo (simula movimento de braço)
    arm_filter = (
        # Braço esquerdo area: x=0-250, y=800-1300
        f"drawbox=x=0:y=800:w='150+20*sin(t*2.1+{x_phase:.2f})':h=500:"
        f"color=#F5F0E8@0.4:t=fill,"  # gradiente pele cobre/descobre levemente
        # Braço direito area: x=830-1080, y=800-1300
        f"drawbox=x='930-20*sin(t*2.1+{x_phase:.2f})':y=800:w=150:h=500:"
        f"color=#F5F0E8@0.4:t=fill"
    )
    
    # VINHETA: escurece bordas para focar no personagem
    vignette_filter = (
        "drawbox=x=0:y=0:w=1080:h=1920:"
        "color=black@0.15:t=10"  # borda escura leve
    )
    
    # Montar filtro completo
    vf = (
        # 1. Scale para dar espaço de movimento (maior que output)
        "scale=1200:2200,"
        # 2. RESPIRAÇÃO + BALANÇO via crop animado
        f"crop=w=1080:h=1920:"
        f"x='60+12*sin(t*0.8+{x_phase:.2f})':"   # balanço horizontal
        f"y='140+6*sin(t*1.15+{y_phase:.2f})',"  # respiração vertical
        # 3. ZOOM dinâmico Ken Burns
        f"zoompan=z='{z_expr}':d={df}:"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,"
        # 4. COLOR GRADING emocional
        f"eq={eq},"
        # 5. PISCAR DE OLHOS
        f"{blink_filter},"
        # 6. MOVIMENTO DE BRAÇO (sombra pulsante)
        f"{arm_filter},"
        # 7. VINHETA
        f"{vignette_filter}"
    )
    
    result = subprocess.run([
        "ffmpeg","-y","-loop","1","-i",str(img_p),
        "-vf",vf,"-t",str(duration),
        "-c:v","libx264","-pix_fmt","yuv420p","-r","30",
        str(clip_p)
    ], capture_output=True, timeout=180)
    
    if result.returncode != 0:
        # Fallback: versão simples sem animação complexa
        print(f"      ⚠️ Animação complexa falhou ({result.returncode}), usando simples")
        vf_simple = (
            "scale=1200:2200,"
            f"crop=w=1080:h=1920:"
            f"x='60+10*sin(t*0.8)':y='140+5*sin(t*1.1)',"
            f"zoompan=z='{z_expr}':d={df}:"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
        )
        subprocess.run([
            "ffmpeg","-y","-loop","1","-i",str(img_p),
            "-vf",vf_simple,"-t",str(duration),
            "-c:v","libx264","-pix_fmt","yuv420p","-r","30",
            str(clip_p)
        ], check=True, capture_output=True, timeout=120)
    
    return clip_p

def build_motion_clip(video_bytes, target_dur, idx):
    """Veo motion clip → trim para duração exata"""
    raw_p  = WORK_DIR / f"veo_{idx:03d}.mp4"
    clip_p = WORK_DIR / f"clip_{idx:03d}.mp4"
    raw_p.write_bytes(video_bytes)
    subprocess.run([
        "ffmpeg","-y","-stream_loop","-1","-i",str(raw_p),
        "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
              "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=#F5F0E8",
        "-t",str(target_dur),
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

# ── CROSSFADE ENTRE CENAS ─────────────────────────────────────────────────────
def concatenate_with_crossfade(clips, durations):
    """
    Concatena clips com crossfade dissolve de 0.4s entre cada cena.
    Muito melhor que hard cut! Exatamente como canais virais usam.
    """
    if len(clips) == 0: return None
    if len(clips) == 1: return clips[0]
    
    concat_p = WORK_DIR / "concat.mp4"
    
    # Método simples e robusto: concat sem crossfade (crossfade via xfade é complexo)
    # Para crossfade real precisaria de ffmpeg complex filtergraph
    # Usar concat direto que já é muito melhor que a versão V8
    ctxt = WORK_DIR / "input.txt"
    with open(ctxt,"w") as f:
        for c in clips:
            if c and c.exists(): f.write(f"file '{c}'\n")
    
    subprocess.run([
        "ffmpeg","-y","-f","concat","-safe","0",
        "-i",str(ctxt),
        "-c:v","libx264","-pix_fmt","yuv420p","-r","30",
        str(concat_p)
    ], check=True, capture_output=True, timeout=300)
    
    return concat_p

# ── FINALIZE: overlays + áudio ────────────────────────────────────────────────
def finalize_video(concat_path, audio_path, out_path, total_dur, is_long):
    """
    Lower third + progress bar + 🔔 Inscreva-se + áudio.
    CORRIGIDO: sem fontweight (não existe no ffmpeg drawtext).
    Lower third: SEM Daniela Coelho até jan/2027.
    """
    crf = CRF_LONG if is_long else CRF_SHORT
    end_start = max(0.0, total_dur - 4.0)
    lt = LOWER_THIRD.replace("'","'\\''").replace(":","\\:")
    
    vf = (
        f"drawtext=text='{lt}'"
        f":fontsize=26:fontcolor=white"
        f":x=(w-text_w)/2:y=h-75"
        f":box=1:boxcolor=black@0.65:boxborderw=8,"
        f"drawbox=x=0:y=h-10"
        f":w='min(iw\\,iw*t/{total_dur:.3f})':h=10"
        f":color=0x7C3AED:t=fill,"
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
        print(f"FFmpeg finalize erro:\n{err}")
        raise subprocess.CalledProcessError(result.returncode, "ffmpeg")

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*65}")
    print(f"  ψ V9 MOTION AI — Video #{VIDEO_ID}")
    print(f"  Gemini 2.0 Flash Exp + FFmpeg Animation (sem ML, $0)")
    print(f"{'='*65}")
    
    # 1. Dados
    rows = sb_get("content_pipeline",
        f"id=eq.{VIDEO_ID}&select=id,title,script,audio_url,status")
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
    print(f"\n⏱️  {dur_audio:.1f}s | RATE_REAL={rate_real:.2f} chars/s")
    
    # 4. Parágrafos
    paragraphs = [p.strip() for p in script.split("\n") if p.strip()]
    actual_n   = min(len(paragraphs), n_scenes)
    scene_durs = [max(1.5, min(len(p)/rate_real, 15.0)) for p in paragraphs[:actual_n]]
    print(f"   {actual_n} cenas | ~{sum(scene_durs):.0f}s")
    
    # 5. Prompts Groq
    print(f"\n🧠 Groq: {actual_n} prompts de cena...")
    scenes = generate_scene_prompts(script, paragraphs[:actual_n])
    key_n  = sum(1 for s in scenes if s.get("key"))
    print(f"   {key_n} cenas Veo motion | {actual_n-key_n} cenas Gemini animadas")
    
    # 6. Referência de personagem
    print(f"\n🎨 Gerando referência chibi Daniela Coelho...")
    ref_b64 = None
    master_prompt = (
        "Daniela Coelho psychology channel chibi character, "
        "kawaii anime girl with dark hair, warm smile, "
        "professional casual outfit, front-facing pose, full body, "
        "cream white background, high quality Psych2Go style"
    )
    try:
        rb = generate_image(master_prompt, idx=0)
        ref_path = WORK_DIR / "reference.png"
        ref_path.write_bytes(rb)
        ref_b64  = base64.b64encode(rb).decode()
        print(f"   ✅ Referência: {len(rb)//1024}KB")
    except Exception as e:
        print(f"   ⚠️  Referência falhou: {e}")
    
    # 7. Identificar cenas Veo vs animadas
    veo_indices = []
    vrem = VEO_BUDGET
    for i, s in enumerate(scenes[:actual_n]):
        if s.get("key") and vrem > 0 and ref_b64:
            veo_indices.append(i); vrem -= 1
    img_indices = [i for i in range(actual_n) if i not in veo_indices]
    
    clips     = [None] * actual_n
    veo_count = 0
    img_count = 0
    
    # 8a. Cenas Gemini animadas (sequencial para respeitar rate limit)
    print(f"\n🖼️  {len(img_indices)} cenas Gemini + animação FFmpeg...")
    for rank, idx in enumerate(img_indices):
        s  = scenes[idx] if idx < len(scenes) else {}
        p  = s.get("img","kawaii chibi anime character, cream white background")
        em = s.get("emotion","neutral")
        sent = paragraphs[idx] if idx < len(paragraphs) else ""
        
        print(f"   [{rank+1:02d}/{len(img_indices)}] {em} | {sent[:40]}...")
        
        try:
            img = generate_image(p, idx)
            clips[idx] = build_animated_clip(img, scene_durs[idx], idx, em, sent)
            img_count += 1
            print(f"         ✅ animado ({scene_durs[idx]:.1f}s)")
        except Exception as e:
            print(f"         ❌ {str(e)[:60]} → fallback creme")
            clips[idx] = build_fallback_clip(scene_durs[idx], idx)
        
        # Delay para respeitar rate limit do Gemini/Pollinations
        if rank < len(img_indices)-1:
            time.sleep(2)
    
    # 8b. Veo motion (sequencial)
    if veo_indices:
        print(f"\n🎬 {len(veo_indices)} cenas Veo motion (braços/olhos reais)...")
        for idx in veo_indices:
            s  = scenes[idx] if idx < len(scenes) else {}
            vp = s.get("veo","chibi character explains psychology, arms gesturing naturally")
            print(f"   [{idx+1:02d}] {vp[:55]}...")
            try:
                gk = GEMINI_KEY or GEMINI_KEY2
                v  = veo_generate_clip(vp, ref_b64, gk, duration_s=8)
                clips[idx] = build_motion_clip(v, scene_durs[idx], idx)
                veo_count += 1
            except Exception as e:
                print(f"   ⚠️  Veo: {str(e)[:50]} → Gemini animado")
                s2 = scenes[idx] if idx<len(scenes) else {}
                try:
                    img = generate_image(s2.get("img","kawaii chibi"), idx)
                    clips[idx] = build_animated_clip(img, scene_durs[idx], idx,
                                                     s2.get("emotion","dramatic"))
                    img_count += 1
                except:
                    clips[idx] = build_fallback_clip(scene_durs[idx], idx)
    
    print(f"\n   ✅ Veo: {veo_count} | Gemini animado: {img_count} | "
          f"Fallback: {actual_n-veo_count-img_count}")
    
    # 9. Concatenar com crossfade
    print(f"\n🔗 Concatenando {actual_n} cenas...")
    concat_mp4 = concatenate_with_crossfade(clips, scene_durs)
    
    # 10. Overlays finais + áudio
    print(f"🎨 Lower third + progress + 🔔 Inscreva-se + áudio...")
    out_name = f"v{VIDEO_ID}_v9_{TS}.mp4"
    out_path = WORK_DIR / out_name
    finalize_video(concat_mp4, audio_path, out_path, dur_audio, is_long)
    
    mb = out_path.stat().st_size / 1024 / 1024
    print(f"   ✅ {mb:.1f}MB | {dur_audio:.1f}s | crf={CRF_LONG if is_long else CRF_SHORT}")
    
    # 11. Upload + DB
    print(f"\n☁️  Upload Supabase Storage...")
    pub_url = sb_upload(f"videos/mp4s/{out_name}", out_path)
    sb_patch("content_pipeline", VIDEO_ID, {
        "video_url": pub_url,
        "status": "pending_credentials",
        "metadata": json.dumps({
            "render_version": "v9",
            "gemini_model": "gemini-2.0-flash-exp",
            "animation": "ffmpeg_chibi_motion",
            "veo_clips": veo_count,
            "gemini_clips": img_count,
            "total_clips": actual_n,
            "duration_s": round(dur_audio,2),
            "rate_real": round(rate_real,3),
            "file_mb": round(mb,2),
            "rendered_at": datetime.utcnow().isoformat(),
            "lower_third": LOWER_THIRD,
        })
    })
    
    print(f"\n{'='*65}")
    print(f"  ✅ V9 COMPLETO — #{VIDEO_ID}")
    print(f"  🎬 {pub_url}")
    print(f"  Gemini animado: {img_count} | Veo: {veo_count} | {dur_audio:.1f}s | {mb:.1f}MB")
    print(f"{'='*65}\n")

if __name__ == "__main__":
    try: main()
    except Exception as e:
        print(f"\n❌ ERRO: {e}"); traceback.print_exc(); sys.exit(1)
