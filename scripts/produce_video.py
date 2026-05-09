#!/usr/bin/env python3
"""
psicologia.doc — Pipeline 24/7 de produção de vídeos cinematográficos.
Roda no GitHub Actions, completamente independente do navegador do user.

Fluxo end-to-end:
  1. Se PIPELINE_ID não fornecido => SQL pega próximo `script_ready` com script>=8000 chars
  2. Quebra script em parágrafos (preserva pontuação)
  3. Pra cada parágrafo: Groq Llama 3.3 70B classifica em 6 emoções
                         => mapa pra voice_settings ElevenLabs Sarah PT-BR multilingual_v2
  4. Concat MP3s com ffmpeg => upload Supabase Storage
  5. Atualiza pipeline pra audio_ready
  6. HTTP call video-generator EF => gera HTML cinematográfico => upload Storage
  7. Atualiza pipeline pra video_ready com HTML URL no metadata
  8. Dispara render-mp4.yml workflow_dispatch => produz MP4 final 1080p stereo
  9. (opcional) loop de polling até render-mp4 concluir, atualiza pipeline pra mp4_ready

Garantias:
  - PAUSE if ElevenLabs char_count_remaining < 12000 (1 video reservado)
  - RETRY 3x exponential backoff em qualquer chamada HTTP
  - LOG estruturado em metadata.pipeline_log do content_pipeline
  - Idempotente: detecta etapas já completas e pula
"""

import os, sys, json, re, time, base64, subprocess, urllib.request, urllib.error
from pathlib import Path

# ============================ CONFIG ============================
SBU = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
GROQ_KEY = os.environ["GROQ_API_KEY"]

# === LLMRouter integration (DeepSeek V4 Pro DEFAULT, free fallback chain, 100% FREE) ===
import sys as _sys
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in _sys.path:
    _sys.path.insert(0, _SCRIPT_DIR)
try:
    from llm_router import LLMRouter as _LLMRouter
    _ROUTER = _LLMRouter()
    _ROUTER_OK = True
except Exception as _e_imp:
    _ROUTER = None
    _ROUTER_OK = False
    print(f"[produce_video] LLMRouter import failed: {_e_imp}; using direct Groq fallback only", flush=True)

def llm_chat_compat(messages, response_format=None, temperature=0.4, max_tokens=2000, timeout=90):
    """Unified LLM call: tries LLMRouter (DeepSeek V4 Pro #1, Nvidia chain free, OpenAI last resort)
    falling back to direct Groq llama-3.3-70b-versatile if router missing/fails.
    Returns the assistant content string. Raises RuntimeError if all paths fail.
    """
    # Path 1: LLMRouter (DeepSeek V4 Pro DEFAULT, max capabilities)
    if _ROUTER_OK and _ROUTER:
        try:
            r = _ROUTER.chat(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=response_format,
                timeout=timeout,
            )
            content = r.get("content") or ""
            if content:
                return content
        except Exception as _e_router:
            print(f"[produce_video] LLMRouter chain exhausted: {_e_router}; trying direct Groq", flush=True)

    # Path 2: Direct Groq (legacy fallback)
    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        body["response_format"] = response_format
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json",
               "User-Agent": "psicologia-doc/1.0"}
    s, b, _h = http("https://api.groq.com/openai/v1/chat/completions",
                    method="POST", headers=headers, body=body, timeout=timeout)
    if s != 200:
        raise RuntimeError(f"Groq direct failed HTTP {s}: {b[:200]}")
    return json.loads(b)["choices"][0]["message"]["content"] or ""
ELEVEN_KEY = os.environ["ELEVENLABS_API_KEY"]
GH_PAT = os.environ.get("GH_PAT", "")
PIPELINE_ID = os.environ.get("PIPELINE_ID", "").strip()
REPO = os.environ.get("GITHUB_REPOSITORY", "tafita81/Repovazio")

VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah multilingual_v2 PT-BR
WORKDIR = Path("/tmp/pipeline_work")
WORKDIR.mkdir(parents=True, exist_ok=True)

H_SB = {"apikey": SBK, "Authorization": f"Bearer {SBK}", "Content-Type": "application/json"}
H_SB_PATCH = {**H_SB, "Prefer": "return=representation"}
H_GH = {"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json", "User-Agent": "psicologia-doc-pipeline/1.0"}

EMOTION_MAP = {
    "INTRO_CALMO":         {"stability": 0.65, "similarity_boost": 0.75, "style": 0.20, "use_speaker_boost": True},
    "ALERTA_TENSO":        {"stability": 0.40, "similarity_boost": 0.80, "style": 0.55, "use_speaker_boost": True},
    "EMPATIA_ACOLHEDOR":   {"stability": 0.60, "similarity_boost": 0.85, "style": 0.30, "use_speaker_boost": True},
    "ANALITICO_FRIO":      {"stability": 0.70, "similarity_boost": 0.70, "style": 0.15, "use_speaker_boost": False},
    "ESPERANCA_CRESCENTE": {"stability": 0.50, "similarity_boost": 0.78, "style": 0.45, "use_speaker_boost": True},
    "CTA_URGENTE":         {"stability": 0.35, "similarity_boost": 0.82, "style": 0.65, "use_speaker_boost": True},
}
EMOTION_DEFAULT = "EMPATIA_ACOLHEDOR"

MIN_QUOTA_RESERVE = 12000  # se sobrar menos que isso de chars, PAUSE
MIN_SCRIPT_LEN = 6000      # threshold pra elegibilidade (= ~8 min de áudio)

# ============================ HELPERS ============================
def log(*a, level="INFO"):
    msg = " ".join(str(x) for x in a)
    print(f"[{time.strftime('%H:%M:%S')}][{level}] {msg}", flush=True)

def http(url, method="GET", headers=None, body=None, timeout=180, raw=False):
    h = dict(headers or {})
    if body is not None and not isinstance(body, (bytes, bytearray)):
        if not raw:
            h.setdefault("Content-Type", "application/json")
            body = json.dumps(body).encode()
        else:
            body = body.encode() if isinstance(body, str) else body
    h.setdefault("User-Agent", "psicologia-doc-pipeline/1.0")
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    last_exc = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            data = e.read() if e.fp else b""
            if e.code in (429, 500, 502, 503, 504) and attempt < 2:
                log(f"  HTTP {e.code} on {url[:60]}, retrying in {2**attempt}s")
                time.sleep(2 ** attempt)
                continue
            return e.code, data, dict(e.headers or {})
        except Exception as e:
            last_exc = e
            if attempt < 2:
                log(f"  network err on {url[:60]}: {e}, retrying")
                time.sleep(2 ** attempt)
                continue
            return 0, str(e).encode(), {}
    return 0, str(last_exc).encode() if last_exc else b"unknown", {}

def sb_select(table, query):
    s, b, _ = http(f"{SBU}/rest/v1/{table}?{query}", headers=H_SB)
    if s != 200:
        raise RuntimeError(f"select {table} failed {s}: {b[:300]}")
    return json.loads(b)

def sb_patch(table, query, payload):
    s, b, _ = http(f"{SBU}/rest/v1/{table}?{query}", method="PATCH", headers=H_SB_PATCH, body=payload)
    if s not in (200, 201, 204):
        raise RuntimeError(f"patch {table} failed {s}: {b[:300]}")
    return json.loads(b) if b else []

def sb_storage_upload(filename, content_type, data_bytes):
    """Upload via mp4-upload EF (genérico, aceita qualquer content_type)."""
    url = f"{SBU}/functions/v1/mp4-upload?filename={filename}&content_type={content_type}"
    h = {"apikey": SBK, "Authorization": f"Bearer {SBK}", "Content-Type": content_type}
    s, b, _ = http(url, method="POST", headers=h, body=data_bytes, raw=True, timeout=300)
    if s not in (200, 201):
        raise RuntimeError(f"storage upload failed {s}: {b[:300]}")
    j = json.loads(b)
    return j.get("mp4_url") or j.get("public_url") or j.get("url") or j.get("publicUrl")

# ============================ ELEVENLABS QUOTA CHECK ============================
def check_eleven_quota():
    s, b, _ = http("https://api.elevenlabs.io/v1/user/subscription", headers={"xi-api-key": ELEVEN_KEY})
    if s != 200:
        log(f"WARN: quota check failed {s}: {b[:200]}", level="WARN")
        return None
    j = json.loads(b)
    used = j.get("character_count", 0)
    limit = j.get("character_limit", 40000)
    remaining = limit - used
    log(f"  ElevenLabs quota: {used}/{limit} usados ({remaining} restantes)")
    return remaining

# ============================ GROQ EMOTION CLASSIFIER ============================
def classify_emotions(paragraphs):
    """Classifica em batch — 1 chamada Groq pra todos os parágrafos."""
    items = [{"i": i, "text": p[:500]} for i, p in enumerate(paragraphs)]
    sys_prompt = (
        "Você classifica parágrafos de roteiro de psicologia em emoções pra TTS cinematográfico. "
        "Categorias EXATAS:\n"
        "- INTRO_CALMO (abertura, hook gentil, contextualização)\n"
        "- ALERTA_TENSO (revelações chocantes, twists, paradoxos)\n"
        "- EMPATIA_ACOLHEDOR (descrição de sofrimento humano, dor emocional)\n"
        "- ANALITICO_FRIO (estatísticas, neurociência, dados objetivos)\n"
        "- ESPERANCA_CRESCENTE (solução começando, cura, recovery)\n"
        "- CTA_URGENTE (chamada à ação final, fechamento, urgência)\n\n"
        "Responda APENAS JSON: {\"results\":[{\"i\":0,\"emotion\":\"...\"},...]}"
    )
    user_prompt = json.dumps({"paragraphs": items}, ensure_ascii=False)
    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
        "max_tokens": 2000,
    }
    try:
        content = llm_chat_compat(
            messages=body["messages"],
            response_format=body.get("response_format"),
            temperature=body["temperature"],
            max_tokens=body["max_tokens"],
            timeout=60,
        )
        results = json.loads(content)["results"]
        out = [EMOTION_DEFAULT] * len(paragraphs)
        for r in results:
            i = r.get("i", -1)
            e = r.get("emotion", EMOTION_DEFAULT)
            if 0 <= i < len(paragraphs) and e in EMOTION_MAP:
                out[i] = e
        return out
    except Exception as e:
        log(f"WARN Groq parse error {e}, fallback default", level="WARN")
        return [EMOTION_DEFAULT] * len(paragraphs)

# ============================ ELEVENLABS TTS ============================
def synthesize_paragraph(text, emotion, out_path):
    settings = EMOTION_MAP.get(emotion, EMOTION_MAP[EMOTION_DEFAULT])
    body = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": settings,
        "output_format": "mp3_44100_128",
    }
    headers = {"xi-api-key": ELEVEN_KEY, "Content-Type": "application/json", "Accept": "audio/mpeg"}
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    s, b, _ = http(url, method="POST", headers=headers, body=body, timeout=120)
    if s != 200:
        raise RuntimeError(f"ElevenLabs failed {s}: {b[:300]}")
    out_path.write_bytes(b)
    return len(b)

def condense_for_short(script, target_platform, char_min=730, char_max=790):
    """Quando target_platform = shorts/reels/tiktok, condensa script via Groq pra ~50-56s.

    YouTube Shorts: max 60s estrito (acima vira long e perde monetizacao Shorts feed).
    ElevenLabs Sarah PT-BR mede ~13.4 chars/s (calibrado em producao 2026-05-08).
    Target intervalo: 730-790 chars => 54.5-58.9s (margem 1s) (sweet spot retencao + margem 4s).
    """
    if target_platform not in ("instagram_reels", "tiktok_short", "youtube_shorts", "pinterest_pin"):
        return script  # long-form, sem condensacao
    if len(script) <= char_max:
        return script
    log(f"  CONDENSE: target={target_platform} chars={len(script)}->{char_min}-{char_max} via Groq")
    char_target = (char_min + char_max) // 2
    sys_prompt = f"""You are a viral PT-BR Shorts copywriter for psychology content.
Take the long-form script and CONDENSE it into a vertical short between {char_min} and {char_max} characters (target ~{char_target}).
The text MUST be SUBSTANTIVE — fill the time with real insight, not fluff:

- HOOK in first 5 words (curiosity, paradox, or shocking stat)
- 4-6 punchy sentences body (concrete facts, emotional pull, story beats)
- Specific examples or numbers when possible
- CTA closer ("siga psicologia.doc para mais", "comente abaixo se concorda")
- Conversational PT-BR Brazilian, not formal
- ZERO filler words. ZERO disclaimers. ZERO ellipses.

CRITICAL: Output text MUST be at least {char_min} characters. If too short, add more concrete detail, examples, or context. The video duration depends on text length — do NOT make it shorter than {char_min} characters.

Output STRICT JSON: {{"short": "<text {char_min}-{char_max} chars>"}}"""
    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user",   "content": script[:8000]},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
        "max_tokens": 500,
    }
    try:
        content = llm_chat_compat(
            messages=body["messages"],
            response_format=body.get("response_format"),
            temperature=body["temperature"],
            max_tokens=body["max_tokens"],
            timeout=60,
        )
        result = json.loads(content)
        short = (result.get("short") or "").strip()
        if len(short) > char_max:
            short = short[:char_max].rsplit(".", 1)[0] + "."
        log(f"  CONDENSED to {len(short)} chars: {short[:80]}...")
        return short or script[:char_max]
    except Exception as e:
        log(f"  parse error ({e}), fallback truncation")
        return script[:char_max].rsplit(".", 1)[0] + "."

# ============================ SCRIPT SPLITTING ============================
def split_paragraphs(script):
    """Quebra script em parágrafos respeitando pontuação. Junta linhas curtas."""
    # Normaliza quebras de linha duplas como separadores
    parts = re.split(r"\n\s*\n+", script.strip())
    out = []
    for p in parts:
        p = re.sub(r"\s+", " ", p).strip()
        if not p:
            continue
        # Se parágrafo > 800 chars, divide por sentenças
        if len(p) > 800:
            sents = re.split(r"(?<=[.!?])\s+", p)
            buf = ""
            for s in sents:
                if len(buf) + len(s) + 1 > 600 and buf:
                    out.append(buf.strip())
                    buf = s
                else:
                    buf = (buf + " " + s).strip()
            if buf:
                out.append(buf.strip())
        else:
            out.append(p)
    return [p for p in out if len(p) > 20]

# ============================ PIPELINE STEPS ============================
def pick_pipeline():
    """Pega próximo pipeline elegível com claim atômico, ou usa PIPELINE_ID se setado.

    Coexistência com tts-pipeline.yml (Edge-TTS):
      - Este workflow só processa pipelines com metadata.use_elevenlabs=true
      - tts-pipeline.yml processa TODO o resto (Edge-TTS é grátis e ilimitado)
      - Se PIPELINE_ID for fornecido manualmente, ignora a flag (override explícito)
    """
    if PIPELINE_ID:
        rows = sb_select("content_pipeline", f"id=eq.{PIPELINE_ID}&select=*")
        if not rows:
            raise RuntimeError(f"pipeline {PIPELINE_ID} not found")
        return rows[0]
    # Atomic claim via SQL: UPDATE ... WHERE ... RETURNING via RPC ou execute_sql
    # PostgREST não suporta RETURNING em PATCH — vou fazer via SELECT então PATCH com timestamp
    # como guard (race window de ~50ms é aceitável dado os cron schedules diferentes)
    q = (f"status=eq.script_ready"
         f"&audio_url=is.null"
         f"&metadata->>use_elevenlabs=eq.true"
         f"&order=id.desc&limit=1&select=*")
    rows = sb_select("content_pipeline", q)
    if not rows:
        log("Nenhum pipeline `script_ready` com use_elevenlabs=true. Edge-TTS workflow cuida do resto.")
        return None
    p = rows[0]
    if len(p.get("script") or "") < MIN_SCRIPT_LEN:
        log(f"Pipeline {p['id']} script muito curto ({len(p['script'])} chars), pulando")
        return None
    # Soft-claim: marca status como 'claiming_elevenlabs' pra que tts-pipeline ignore
    md = dict(p.get("metadata") or {})
    md["claimed_at"] = int(time.time())
    md["claimed_by"] = "full-pipeline"
    sb_patch("content_pipeline", f"id=eq.{p['id']}&status=eq.script_ready",
             {"status": "claiming_elevenlabs", "metadata": md})
    # Re-fetch pra confirmar que ganhamos o claim
    fresh = sb_select("content_pipeline", f"id=eq.{p['id']}&select=*")[0]
    if fresh.get("status") != "claiming_elevenlabs":
        log(f"Pipeline {p['id']} foi pego por outro processo, abortando")
        return None
    return fresh

def step_audio(pipeline):
    pid = pipeline["id"]
    if pipeline.get("audio_url"):
        log(f"[{pid}] audio_url já existe, pulando step_audio")
        return pipeline["audio_url"]

    script = pipeline["script"]
    # CONDENSE pra shorts/reels/tiktok: garante <60s audio (monetizacao YouTube Shorts)
    target_platform = pipeline.get("target_platform") or "youtube_long"
    script = condense_for_short(script, target_platform)
    paragraphs = split_paragraphs(script)
    log(f"[{pid}] {len(paragraphs)} parágrafos, total {sum(len(p) for p in paragraphs)} chars")

    remaining = check_eleven_quota()
    needed = sum(len(p) for p in paragraphs)
    if remaining is not None and remaining - needed < MIN_QUOTA_RESERVE:
        raise RuntimeError(
            f"PAUSE: precisa {needed} chars, sobram {remaining}, reserva mínima {MIN_QUOTA_RESERVE}. "
            "Sistema vai retomar quando o limite resetar."
        )

    log(f"[{pid}] classificando emoções via Groq...")
    emotions = classify_emotions(paragraphs)
    emotion_summary = {}
    for e in emotions:
        emotion_summary[e] = emotion_summary.get(e, 0) + 1
    log(f"[{pid}] emotions: {emotion_summary}")

    work = WORKDIR / f"p{pid}"
    work.mkdir(exist_ok=True)
    parts = []
    total_bytes = 0
    for i, (txt, emo) in enumerate(zip(paragraphs, emotions)):
        part_path = work / f"part_{i:03d}.mp3"
        if part_path.exists() and part_path.stat().st_size > 1000:
            parts.append(part_path); continue
        log(f"[{pid}]  parte {i+1}/{len(paragraphs)} [{emo}] ({len(txt)} chars)")
        size = synthesize_paragraph(txt, emo, part_path)
        total_bytes += size
        parts.append(part_path)

    # Concat MP3s com ffmpeg
    listfile = work / "concat.txt"
    listfile.write_text("\n".join(f"file '{p}'" for p in parts))
    final_mp3 = work / f"audio_{pid}_{int(time.time())}.mp3"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
           "-i", str(listfile), "-c", "copy", str(final_mp3)]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        # fallback: re-encode
        cmd2 = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                "-i", str(listfile), "-codec:a", "libmp3lame", "-b:a", "128k", str(final_mp3)]
        r2 = subprocess.run(cmd2, capture_output=True)
        if r2.returncode != 0:
            raise RuntimeError(f"ffmpeg concat failed: {r.stderr.decode()[:300]}")

    log(f"[{pid}] mp3 final: {final_mp3.stat().st_size/1024/1024:.2f} MB")
    audio_url = sb_storage_upload(final_mp3.name, "audio/mpeg", final_mp3.read_bytes())
    log(f"[{pid}] audio_url = {audio_url}")

    metadata = pipeline.get("metadata") or {}
    metadata["emotion_distribution"] = emotion_summary
    metadata["paragraph_count"] = len(paragraphs)
    metadata["audio_render"] = {
        "engine": "elevenlabs_sarah_multilingual_v2",
        "emotion_classifier": "groq_llama_3.3_70b",
        "char_count": needed,
        "size_bytes": final_mp3.stat().st_size,
        "ts": int(time.time()),
    }
    sb_patch("content_pipeline", f"id=eq.{pid}",
             {"audio_url": audio_url, "status": "audio_ready",
              "voice_name": "Sarah_ElevenLabs_dynamic_emotion",
              "metadata": metadata})
    return audio_url

def step_html(pipeline, audio_url):
    pid = pipeline["id"]
    metadata = pipeline.get("metadata") or {}
    html_url = metadata.get("video_html_url") or pipeline.get("video_url")
    if html_url and html_url.endswith(".html"):
        log(f"[{pid}] html já existe: {html_url}, pulando step_html")
        return html_url
    log(f"[{pid}] gerando HTML via video-generator EF...")
    body = {
        "pipeline_id": pid,
        "title": pipeline.get("title", ""),
        "script": pipeline["script"],
        "audio_url": audio_url,
        "style": pipeline.get("video_style") or "documentary",
    }
    s, b, _ = http(f"{SBU}/functions/v1/video-generator", method="POST",
                   headers={"Authorization": f"Bearer {SBK}", "Content-Type": "application/json"},
                   body=body, timeout=300)
    if s != 200:
        raise RuntimeError(f"video-generator failed {s}: {b[:300]}")
    j = json.loads(b)
    html_url = j.get("video_html_url") or j.get("html_url") or j.get("url")
    if not html_url:
        raise RuntimeError(f"video-generator no html_url in response: {b[:300]}")
    log(f"[{pid}] html_url = {html_url}")
    # video-generator EF acabou de sobrescrever metadata com seus próprios campos
    # (video_html_url, thumbnail_html_url, total_scenes, total_duration_seconds...)
    # Re-fetch para fazer MERGE com nosso audio_render preservado
    fresh = sb_select("content_pipeline", f"id=eq.{pid}&select=metadata")[0]
    new_md = dict(fresh.get("metadata") or {})
    # Preservar campos que o video-generator não conhece
    for key in ("emotion_distribution", "paragraph_count", "audio_render", "music_url"):
        if metadata.get(key) is not None:
            new_md[key] = metadata[key]
    sb_patch("content_pipeline", f"id=eq.{pid}",
             {"status": "video_ready", "video_url": html_url, "metadata": new_md})
    return html_url

def step_render_mp4(pipeline, audio_url, html_url):
    pid = pipeline["id"]
    music_url = (pipeline.get("metadata") or {}).get("music_url", "")
    log(f"[{pid}] disparando render-mp4.yml workflow_dispatch...")
    body = {
        "ref": "main",
        "inputs": {
            "audio_url": audio_url,
            "video_html_url": html_url,
            "music_url": music_url,
            "title": pipeline.get("title", "")[:80],
            "style": pipeline.get("video_style") or "documentary",
            "pipeline_id": str(pid),
        },
    }
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/render-mp4.yml/dispatches"
    s, b, _ = http(url, method="POST", headers=H_GH, body=body)
    if s not in (200, 201, 204):
        raise RuntimeError(f"workflow_dispatch failed {s}: {b[:300]}")
    log(f"[{pid}] render-mp4.yml dispatched OK")
    sb_patch("content_pipeline", f"id=eq.{pid}", {"status": "rendering"})
    return True

# ============================ MAIN ============================
def main():
    log("=" * 60)
    log("psicologia.doc — full pipeline 24/7")
    log(f"  PIPELINE_ID env: {PIPELINE_ID or '(auto-pick)'}")

    pipeline = pick_pipeline()
    if not pipeline:
        log("Sem trabalho elegível, encerrando com sucesso.")
        return 0
    pid = pipeline["id"]
    log(f"Selecionado: pipeline {pid} — '{pipeline.get('title','')[:60]}'")
    log(f"  status={pipeline.get('status')} script_len={len(pipeline.get('script') or '')}")

    try:
        audio_url = step_audio(pipeline)
        # Re-fetch pra pegar metadata atualizado
        pipeline = sb_select("content_pipeline", f"id=eq.{pid}&select=*")[0]
        html_url = step_html(pipeline, audio_url)
        pipeline = sb_select("content_pipeline", f"id=eq.{pid}&select=*")[0]
        step_render_mp4(pipeline, audio_url, html_url)
        log("=" * 60)
        log(f"SUCESSO pipeline {pid} — render-mp4 disparado, MP4 estará pronto em ~3-5 min")
        log("=" * 60)
        return 0
    except Exception as e:
        log(f"FALHA: {e}", level="ERROR")
        try:
            md = pipeline.get("metadata") or {}
            md["last_error"] = {"msg": str(e)[:500], "ts": int(time.time())}
            sb_patch("content_pipeline", f"id=eq.{pid}",
                     {"audio_error": str(e)[:1000], "metadata": md})
        except Exception:
            pass
        return 1

if __name__ == "__main__":
    sys.exit(main())
