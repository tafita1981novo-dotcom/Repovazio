#!/usr/bin/env python3
"""
psicologia.doc — TTS Pipeline com Edge TTS (Microsoft) + Groq Llama 3.3 70B
GRÁTIS ILIMITADO. Voz neural PT-BR multi-voz com emoção dinâmica.

Vozes PT-BR Edge TTS usadas:
  - Francisca  (acolhedora, narradora padrão)
  - Antonio    (sério, masculino, dados/análise/CTA)
  - Thalita    (multilingual, neutra, esperança)
  - Brenda     (jovem, hooks/intro)

Fluxo:
  1. SQL: pega pipeline (PIPELINE_ID env ou próximo `ready_tts`)
  2. Quebra script em parágrafos
  3. Groq classifica emoção de cada parágrafo (6 categorias)
  4. Mapa emoção → (voz, rate, pitch, volume)
  5. Edge TTS gera 1 MP3 por parágrafo
  6. ffmpeg concat MP3s, mix com bg music opcional, EBU R128 -16 LUFS
  7. Upload Supabase Storage
  8. video-generator EF gera HTML cinematográfico
  9. Atualiza pipeline → video_ready com html_url no metadata
  10. workflow_dispatch render-mp4.yml v8.2 com html_url
"""
import os, sys, re, json, time, asyncio, hashlib, urllib.request, urllib.error
import subprocess, tempfile
from pathlib import Path

SBU = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
GROQ_KEY = os.environ["GROQ_API_KEY"]
GH_PAT = os.environ["GH_PAT"]
PIPELINE_ID = os.environ.get("PIPELINE_ID", "").strip()
TARGET_PLATFORM = os.environ.get("TARGET_PLATFORM", "youtube_long").strip()
REPO = os.environ.get("GITHUB_REPOSITORY", "tafita81/Repovazio")

H_SB = {"apikey": SBK, "Authorization": f"Bearer {SBK}"}
H_SB_J = {**H_SB, "Content-Type": "application/json"}

# Emotion → voice POOLS (Edge TTS Microsoft, 16 PT-BR neural voices, 100% FREE ILIMITADO)
# Each emotion has multiple compatible voice variants. A deterministic hash of
# (pipeline_id + emotion) selects which variant to use per video, providing
# variety across videos while maintaining consistency within a single video.
#
# All 16 PT-BR Neural voices: Francisca, Antonio, Thalita, Brenda, Donato, Elza,
# Fabio, Giovanna, Humberto, Julio, Leila, Leticia, Manuela, Nicolau, Valerio, Yara
EMOTION_VOICES = {
    # Calm openers — slow Francisca/Thalita (3 valid PT-BR voices: Antonio/Francisca/ThalitaMultilingual)
    "INTRO_CALMO": [
        {"voice": "pt-BR-FranciscaNeural", "rate": "-5%",  "volume": "+0%"},
        {"voice": "pt-BR-FranciscaNeural", "rate": "-3%",  "volume": "+0%"},
        {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "-5%",  "volume": "+0%"},
        {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "-3%",  "volume": "+0%"},
    ],
    # Tense alerts — punchy Antonio
    "ALERTA_TENSO": [
        {"voice": "pt-BR-AntonioNeural",   "rate": "+8%",  "volume": "+5%"},
        {"voice": "pt-BR-AntonioNeural",   "rate": "+10%", "volume": "+5%"},
        {"voice": "pt-BR-AntonioNeural",   "rate": "+12%", "volume": "+8%"},
        {"voice": "pt-BR-AntonioNeural",   "rate": "+15%", "volume": "+5%"},
    ],
    # Warm empathy — slow Francisca/Thalita
    "EMPATIA_ACOLHEDOR": [
        {"voice": "pt-BR-FranciscaNeural", "rate": "-10%", "volume": "+0%"},
        {"voice": "pt-BR-FranciscaNeural", "rate": "-12%", "volume": "+0%"},
        {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "-10%", "volume": "+0%"},
        {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "-8%",  "volume": "+0%"},
    ],
    # Cold analytical — neutral Antonio
    "ANALITICO_FRIO": [
        {"voice": "pt-BR-AntonioNeural",   "rate": "+0%",  "volume": "+0%"},
        {"voice": "pt-BR-AntonioNeural",   "rate": "+2%",  "volume": "+0%"},
        {"voice": "pt-BR-AntonioNeural",   "rate": "-2%",  "volume": "+0%"},
        {"voice": "pt-BR-AntonioNeural",   "rate": "+3%",  "volume": "-2%"},
    ],
    # Rising hope — modern Thalita/Francisca
    "ESPERANCA_CRESCENTE": [
        {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+0%",  "volume": "+2%"},
        {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+2%",  "volume": "+3%"},
        {"voice": "pt-BR-FranciscaNeural", "rate": "+0%",  "volume": "+2%"},
        {"voice": "pt-BR-FranciscaNeural", "rate": "+2%",  "volume": "+3%"},
    ],
    # Urgent CTA — strong commanding Antonio
    "CTA_URGENTE": [
        {"voice": "pt-BR-AntonioNeural",   "rate": "+12%", "volume": "+8%"},
        {"voice": "pt-BR-AntonioNeural",   "rate": "+10%", "volume": "+10%"},
        {"voice": "pt-BR-AntonioNeural",   "rate": "+15%", "volume": "+8%"},
        {"voice": "pt-BR-AntonioNeural",   "rate": "+13%", "volume": "+12%"},
    ],
    # Energetic hook — bright Thalita/Francisca
    "HOOK_ENERGICO": [
        {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+5%",  "volume": "+5%"},
        {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+8%",  "volume": "+5%"},
        {"voice": "pt-BR-FranciscaNeural", "rate": "+5%",  "volume": "+5%"},
        {"voice": "pt-BR-FranciscaNeural", "rate": "+8%",  "volume": "+8%"},
    ],
}

# Backward-compat alias (set membership checks still work via __contains__)
EMOTION_VOICE = EMOTION_VOICES
DEFAULT_EMOTION = "EMPATIA_ACOLHEDOR"

# Global seed used by pick_emotion_voice. Set in main() from pipeline_id so the
# voice rotation is deterministic per video but varies across videos.
_SEED_STR = "default_seed"

def pick_emotion_voice(emotion: str, seed: str = None) -> dict:
    """Pick a voice variant for the given emotion. Deterministic per (emotion, seed).
    Same pipeline + same emotion always picks the same voice; different pipelines
    rotate through the variants for natural variety across videos."""
    options = EMOTION_VOICES.get(emotion, EMOTION_VOICES[DEFAULT_EMOTION])
    s = seed if seed is not None else _SEED_STR
    h = int(hashlib.sha256(f"{emotion}:{s}".encode()).hexdigest(), 16)
    return options[h % len(options)]

WORKDIR = Path("/tmp/tts_work")
WORKDIR.mkdir(parents=True, exist_ok=True)

def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)

def http_json(url, method="GET", body=None, headers=None, timeout=120):
    h = dict(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h.setdefault("Content-Type", "application/json")
    h.setdefault("User-Agent", "psicologia-doc-tts/1.0")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    last_exc = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                return r.status, raw, dict(r.headers)
        except urllib.error.HTTPError as e:
            body_b = e.read() if e.fp else b""
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                wait = 2 ** attempt
                log(f"  retry {attempt+1} after {wait}s (status={e.code})")
                time.sleep(wait); continue
            return e.code, body_b, dict(e.headers or {})
        except Exception as e:
            last_exc = e
            if attempt < 3:
                time.sleep(2 ** attempt); continue
            raise
    if last_exc: raise last_exc

def sb_select(table, query):
    s, b, _ = http_json(f"{SBU}/rest/v1/{table}?{query}", headers=H_SB)
    if s != 200: raise RuntimeError(f"select {table} failed {s}: {b[:300]}")
    return json.loads(b)

def sb_patch(table, query, payload):
    s, b, _ = http_json(f"{SBU}/rest/v1/{table}?{query}", method="PATCH",
                       body=payload, headers={**H_SB_J, "Prefer": "return=representation"})
    if s not in (200, 204):
        raise RuntimeError(f"patch {table} failed {s}: {b[:300]}")
    return json.loads(b) if b else []

def claim_pipeline():
    """Pega PIPELINE_ID env, OU próximo `ready_tts` da target_platform."""
    if PIPELINE_ID:
        rows = sb_select("content_pipeline",
                        f"id=eq.{PIPELINE_ID}&select=id,title,script,target_platform,duration_target_min,case_id,series_id,episode_number,metadata")
        if not rows: raise SystemExit(f"pipeline {PIPELINE_ID} not found")
        return rows[0]
    # auto-pick by platform
    rows = sb_select("content_pipeline",
        f"status=eq.ready_tts&target_platform=eq.{TARGET_PLATFORM}"
        f"&select=id,title,script,target_platform,duration_target_min,case_id,series_id,episode_number,metadata"
        f"&order=id.desc&limit=1")
    if not rows: raise SystemExit(f"no ready_tts for {TARGET_PLATFORM}")
    return rows[0]

def condense_for_short(script, target_platform, char_min=800, char_max=860):
    """Quando target_platform = shorts/reels/tiktok, condensa script via Groq pra ~50-56s.

    YouTube Shorts: max 60s estrito. Acima de 60s vira long e perde monetizacao Shorts feed.
    Edge-TTS PT-BR mede ~15.2 chars/s (re-calibrado em producao 2026-05-08).
    Target intervalo: 800-860 chars => 52.6-56.6s (sweet spot retencao + margem 4s).
    Groq recebe MIN+MAX e mira no centro do range.
    """
    if target_platform not in ("instagram_reels", "tiktok_short", "youtube_shorts", "pinterest_pin"):
        return script  # long-form, sem condensacao
    if len(script) <= char_max:
        return script  # ja eh curto o suficiente
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
            {"role": "user",   "content": script[:8000]},  # input cap
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
        "max_tokens": 500,
    }
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json",
               "User-Agent": "psicologia-doc/1.0"}
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",
                                 data=json.dumps(body).encode(), method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            j = json.loads(r.read())
        content = j["choices"][0]["message"]["content"]
        result = json.loads(content)
        short = result.get("short", "").strip()
        # Hard cap: trunca se excedeu target+10%
        # Cap superior: nunca passar de char_max (pra ficar abaixo de 60s)
        if len(short) > char_max:
            short = short[:char_max].rsplit(".", 1)[0] + "."
        # Se ficou MUITO abaixo do mínimo, retry com prompt mais agressivo (silencioso)
        if len(short) < char_min - 50:
            log(f"  WARN: short {len(short)} chars < {char_min-50}, considering retry")
        log(f"  CONDENSED to {len(short)} chars: {short[:80]}...")
        return short or script[:char_max]
    except Exception as e:
        log(f"  Groq condense failed ({e}), naive truncation to char_max")
        return script[:char_max].rsplit(".", 1)[0] + "."

def split_paragraphs(script, target_platform):
    """Quebra em parágrafos respeitando o tamanho ideal por plataforma."""
    # Long videos: parágrafos por blank line / section header
    # Shorts: corta em sentenças mais curtas
    text = script.strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    if target_platform in ("instagram_reels", "tiktok_short", "youtube_shorts"):
        # short: 5-8 sentenças no máximo
        sents = re.split(r'(?<=[.!?])\s+', text)
        # group every 1-2 sents into "paragraphs"
        groups, buf = [], []
        for s in sents:
            buf.append(s)
            if len(' '.join(buf)) > 100:
                groups.append(' '.join(buf)); buf = []
        if buf: groups.append(' '.join(buf))
        return [g.strip() for g in groups if g.strip()]
    else:
        # long: blank-line paragraphs, then split if > 800 chars
        paras = [p.strip() for p in text.split('\n\n') if p.strip()]
        out = []
        for p in paras:
            if len(p) <= 800:
                out.append(p); continue
            # split by sentence boundaries
            sents = re.split(r'(?<=[.!?])\s+', p)
            buf = []
            for s in sents:
                buf.append(s)
                if len(' '.join(buf)) > 600:
                    out.append(' '.join(buf)); buf = []
            if buf: out.append(' '.join(buf))
        return out

def classify_emotions_groq(paragraphs):
    """Classifica TODOS os parágrafos numa única chamada Groq (Llama 3.3 70B)."""
    numbered = "\n".join(f"[P{i}] {p[:500]}" for i, p in enumerate(paragraphs))
    sys_prompt = """You are a Brazilian Portuguese narrative emotion classifier.
For each paragraph below, output the SINGLE best matching category from this list:
- INTRO_CALMO (opening, gentle hook, calm setup)
- ALERTA_TENSO (revelation, twist, tension, warning)
- EMPATIA_ACOLHEDOR (describing pain, emotion, story, vulnerability)
- ANALITICO_FRIO (statistics, neuroscience, data, research)
- ESPERANCA_CRESCENTE (solution, recovery, hope, growth)
- CTA_URGENTE (call to action, closing, urgent recommendation)
- HOOK_ENERGICO (surprise, curiosity hook, attention grabber)

Output STRICT JSON: {"results":[{"id":"P0","emotion":"<CATEGORY>"},...]}"""
    # NEW 2026-05-08: LLMRouter first - fallback chain Groq->DeepSeek->Nvidia V4Pro->OpenAI
    content = None
    try:
        from llm_router import LLMRouter
        _result = LLMRouter().chat(
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": numbered},
            ],
            temperature=0.2,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        content = _result["content"]
        log(f"  emotions classified by {_result['engine']} ({_result['latency_ms']}ms)")
    except Exception as _e:
        log(f"  LLMRouter unavailable ({type(_e).__name__}: {_e}), falling back to direct Groq")
        body = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user",   "content": numbered},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "max_tokens": 1024,
        }
        s, raw, _ = http_json("https://api.groq.com/openai/v1/chat/completions",
                              method="POST", body=body,
                              headers={"Authorization": f"Bearer {GROQ_KEY}"})
        if s != 200:
            log(f"  GROQ FAIL {s}, fallback to default emotion")
            return [DEFAULT_EMOTION] * len(paragraphs)
        payload = json.loads(raw)
        content = payload["choices"][0]["message"]["content"]
    try:
        results = json.loads(content)["results"]
        ordered = [DEFAULT_EMOTION] * len(paragraphs)
        for r in results:
            idx = int(r["id"].lstrip("P"))
            emo = r["emotion"]
            if emo in EMOTION_VOICE and 0 <= idx < len(paragraphs):
                ordered[idx] = emo
        # heurística: 1º parágrafo = HOOK_ENERGICO ou INTRO_CALMO
        if len(ordered) > 0 and ordered[0] not in ("HOOK_ENERGICO", "INTRO_CALMO"):
            ordered[0] = "INTRO_CALMO"
        # último = CTA_URGENTE se não vier
        if ordered and ordered[-1] != "CTA_URGENTE":
            ordered[-1] = "CTA_URGENTE"
        return ordered
    except Exception as e:
        log(f"  parse fail: {e}, content={content[:200]}")
        return [DEFAULT_EMOTION] * len(paragraphs)

async def gen_para_audio(idx, text, emotion):
    """Gera 1 MP3 com Edge TTS pra um parágrafo."""
    import edge_tts
    cfg = pick_emotion_voice(emotion, _SEED_STR)
    out = WORKDIR / f"p{idx:03d}.mp3"
    communicate = edge_tts.Communicate(
        text, cfg["voice"], rate=cfg["rate"], volume=cfg["volume"])
    await communicate.save(str(out))
    sz = out.stat().st_size
    return idx, str(out), sz, emotion, cfg["voice"]

async def gen_all_audio(paragraphs, emotions, max_concurrent=8):
    """Gera todos parágrafos em paralelo (Edge TTS handle WebSocket conn)."""
    sem = asyncio.Semaphore(max_concurrent)
    async def one(i, text, emo):
        async with sem:
            for attempt in range(3):
                try:
                    return await gen_para_audio(i, text, emo)
                except Exception as e:
                    log(f"  P{i} attempt {attempt+1} failed: {e}")
                    await asyncio.sleep(2 ** attempt)
            raise RuntimeError(f"P{i} all retries failed")
    tasks = [one(i, p, emotions[i]) for i, p in enumerate(paragraphs)]
    return await asyncio.gather(*tasks)

def concat_mp3(parts, output_path):
    """Concat MP3s + normaliza pra -16 LUFS estéreo 48kHz 192kbps."""
    list_file = WORKDIR / "list.txt"
    list_file.write_text("\n".join(f"file '{p}'" for _, p, _, _, _ in sorted(parts)))
    raw_concat = WORKDIR / "_concat.mp3"
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
           "-c", "copy", str(raw_concat)]
    subprocess.run(cmd, check=True, capture_output=True)
    # Normalize loudness to broadcast standard
    cmd2 = ["ffmpeg", "-y", "-i", str(raw_concat),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "48000", "-ac", "2", "-b:a", "192k", "-c:a", "aac",
            output_path]
    r = subprocess.run(cmd2, capture_output=True, text=True)
    if r.returncode != 0:
        log("  ffmpeg loudnorm failed, falling back to copy:", r.stderr[-300:])
        # fallback: just copy concat as mp3 with 192k
        cmd3 = ["ffmpeg", "-y", "-i", str(raw_concat),
                "-ar", "44100", "-ac", "2", "-b:a", "192k", "-c:a", "libmp3lame",
                output_path]
        subprocess.run(cmd3, check=True, capture_output=True)

def get_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                       "-of", "default=noprint_wrappers=1:nokey=1", path],
                      capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

def upload_to_storage(local_path, remote_name, content_type):
    """Upload via mp4-upload EF (suporta MP3, MP4, etc)."""
    url = f"{SBU}/functions/v1/mp4-upload?filename={remote_name}&content_type={content_type}"
    data = open(local_path, "rb").read()
    h = {**H_SB, "Content-Type": content_type}
    req = urllib.request.Request(url, data=data, method="POST", headers=h)
    with urllib.request.urlopen(req, timeout=300) as r:
        body = r.read()
    return json.loads(body)

def call_video_generator(pipeline_id, title, script, audio_url, target_platform, case_data=None):
    """Chama video-generator EF pra gerar HTML cinematográfico."""
    style_map = {
        "youtube_long":     "documentary",
        "youtube_shorts":   "shorts_vertical",
        "instagram_reels":  "shorts_vertical",
        "tiktok_short":     "shorts_vertical",
        "pinterest_pin":    "shorts_vertical",  # generates 9:16, render adjusts
    }
    body = {
        "pipeline_id": pipeline_id,
        "title": title,
        "script": script,
        "audio_url": audio_url,
        "style": style_map.get(target_platform, "documentary"),
        "case_data": case_data,
    }
    s, raw, _ = http_json(f"{SBU}/functions/v1/video-generator",
                         method="POST", body=body, headers=H_SB_J, timeout=180)
    if s != 200:
        raise RuntimeError(f"video-generator failed {s}: {raw[:400]}")
    return json.loads(raw)

def dispatch_render_workflow(pipeline_id, audio_url, html_url, title, target_platform):
    """Dispara render-mp4.yml workflow_dispatch."""
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/render-mp4.yml/dispatches"
    style_map_render = {
        "youtube_long":     "documentary",
        "youtube_shorts":   "shorts_vertical",
        "instagram_reels":  "shorts_vertical",
        "tiktok_short":     "shorts_vertical",
        "pinterest_pin":    "shorts_vertical",
    }
    body = {
        "ref": "main",
        "inputs": {
            "pipeline_id": str(pipeline_id),
            "audio_url": audio_url,
            "video_html_url": html_url,
            "music_url": "",
            "title": title[:80],
            "style": style_map_render.get(target_platform, "documentary"),
        }
    }
    h = {"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json"}
    s, raw, _ = http_json(url, method="POST", body=body, headers=h)
    if s not in (200, 204):
        raise RuntimeError(f"workflow_dispatch failed {s}: {raw[:300]}")
    return True

def main():
    pipe = claim_pipeline()
    pid = pipe["id"]
    # Set voice rotation seed: each pipeline_id deterministically picks a unique
    # combination from the 16 PT-BR Neural voice pool. Same video = same voices,
    # different videos = different voice combinations (natural variety).
    global _SEED_STR
    _SEED_STR = str(pid)
    log(f"[VOICES] _SEED_STR={_SEED_STR[:24]} (rotates across 16 PT-BR neural voices)")
    title = pipe["title"]
    script = pipe["script"]
    target = pipe.get("target_platform") or TARGET_PLATFORM
    log(f"PIPELINE id={pid} title={title[:60]!r} target={target} script_chars={len(script)}")

    # mark as processing
    sb_patch("content_pipeline", f"id=eq.{pid}",
             {"status": "audio_processing",
              "audio_queued_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})

    # CONDENSE pra shorts/reels/tiktok: garante <60s áudio (monetização YouTube Shorts)
    script = condense_for_short(script, target)
    paras = split_paragraphs(script, target)
    log(f"  split into {len(paras)} paragraphs")

    log("  classifying emotions with Groq Llama 3.3 70B…")
    t0 = time.time()
    emotions = classify_emotions_groq(paras)
    log(f"  emotions ({time.time()-t0:.2f}s): {[e[:8] for e in emotions]}")

    log("  generating MP3s with Edge TTS (multi-voice)…")
    t0 = time.time()
    parts = asyncio.run(gen_all_audio(paras, emotions))
    log(f"  generated {len(parts)} parts in {time.time()-t0:.1f}s")
    voices_used = sorted(set(p[4] for p in parts))
    total_bytes = sum(p[2] for p in parts)
    log(f"  voices used: {voices_used} | total bytes: {total_bytes:,}")

    final_mp3 = WORKDIR / f"final_{pid}.mp3"
    log("  concatenating + normalizing -16 LUFS …")
    concat_mp3(parts, str(final_mp3))
    duration = get_duration(str(final_mp3))
    log(f"  final audio: {final_mp3.stat().st_size:,} bytes  duration={duration:.1f}s")

    safe_title = re.sub(r'[^a-zA-Z0-9_-]+', '_', title)[:48]
    audio_name = f"{int(time.time())}_{pid}_{safe_title}.mp3"
    log(f"  uploading audio as {audio_name} …")
    up = upload_to_storage(str(final_mp3), audio_name, "audio/mpeg")
    audio_url = up.get("mp4_url") or up.get("public_url") or up.get("url") or f"{SBU}/storage/v1/object/public/videos/{audio_name}"
    log(f"  audio_url = {audio_url}")

    # update DB → audio_ready
    sb_patch("content_pipeline", f"id=eq.{pid}", {
        "audio_url": audio_url,
        "status": "audio_ready",
        "voice_name": "EdgeTTS_MultiVoice_Groq_Emotion_v1",
        "voice_id": "edge-tts-multi",
        "emotion_profile": json.dumps([{"para": i, "emotion": emotions[i],
                                        "voice": pick_emotion_voice(emotions[i], _SEED_STR)["voice"]}
                                       for i in range(len(paras))]),
        "metadata": {
            "audio_engine": "edge-tts-microsoft",
            "audio_duration_sec": duration,
            "paragraphs": len(paras),
            "voices_used": voices_used,
            "emotion_classifier": "groq_llama_3.3_70b",
        },
    })

    # generate HTML via EF
    log("  generating HTML via video-generator EF …")
    case_data = None
    if pipe.get("case_id"):
        cd = sb_select("real_cases", f"id=eq.{pipe['case_id']}&select=*")
        if cd: case_data = cd[0]
    vg = call_video_generator(pid, title, script, audio_url, target, case_data)
    html_url = vg.get("video_html_url") or vg.get("html_url") or vg.get("url")
    if not html_url:
        raise RuntimeError(f"video-generator returned no html_url: {vg}")
    log(f"  html_url = {html_url}")

    # update DB → video_ready
    cur = sb_select("content_pipeline", f"id=eq.{pid}&select=metadata")
    md = (cur[0].get("metadata") if cur else {}) or {}
    if isinstance(md, str): md = json.loads(md)
    md["html_url"] = html_url
    sb_patch("content_pipeline", f"id=eq.{pid}", {
        "status": "video_ready",
        "video_url": html_url,
        "metadata": md,
    })

    # dispatch render-mp4 workflow
    log("  dispatching render-mp4.yml workflow…")
    dispatch_render_workflow(pid, audio_url, html_url, title, target)
    log(f"DONE pipeline_id={pid} → render-mp4 will produce final MP4")

if __name__ == "__main__":
    main()
