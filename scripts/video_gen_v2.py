#!/usr/bin/env python3
"""
Video Generator V2 - Psych2Go style
- DeepSeek V4 Pro: scene segmentation
- Flux Schnell (Nvidia free): illustration generation per scene
- Edge TTS: voice with emotional mapping
- ffmpeg: Ken Burns + crossfade + audio mix
- ZERO TEXT on screen
- Output: MP4 1080p 30fps
"""
import os, sys, re, json, base64, requests, subprocess, asyncio, hashlib, time, tempfile, shutil, random
from pathlib import Path

NVIDIA_KEY = os.environ['NVIDIA_API_KEY']
SB_URL = os.environ['SUPABASE_URL']
SB_KEY = os.environ['SUPABASE_SERVICE_KEY']
PIPELINE_ID = int(os.environ.get('PIPELINE_ID', sys.argv[1] if len(sys.argv) > 1 else '0'))

WORK = Path(tempfile.mkdtemp(prefix='vidgen_'))
print(f"[init] work dir: {WORK} | pipeline #{PIPELINE_ID}")

# -------------- Supabase helpers --------------
def sb_get(path):
    r = requests.get(f"{SB_URL}/rest/v1/{path}",
        headers={'apikey': SB_KEY, 'Authorization': f'Bearer {SB_KEY}'}, timeout=30)
    r.raise_for_status()
    return r.json()

def sb_patch(path, body):
    r = requests.patch(f"{SB_URL}/rest/v1/{path}",
        headers={'apikey': SB_KEY, 'Authorization': f'Bearer {SB_KEY}',
                 'Content-Type': 'application/json', 'Prefer': 'return=representation'},
        json=body, timeout=30)
    if r.status_code >= 400:
        print(f"[sb_patch ERR] {r.status_code}: {r.text[:300]}")
    return r.json() if r.status_code < 400 else None

def sb_upload_storage(bucket, path, file_path, content_type):
    with open(file_path, 'rb') as f:
        data = f.read()
    r = requests.post(f"{SB_URL}/storage/v1/object/{bucket}/{path}",
        headers={'apikey': SB_KEY, 'Authorization': f'Bearer {SB_KEY}',
                 'Content-Type': content_type, 'x-upsert': 'true'},
        data=data, timeout=120)
    if r.status_code >= 400:
        print(f"[upload ERR] {r.status_code}: {r.text[:300]}")
        return None
    return f"{SB_URL}/storage/v1/object/public/{bucket}/{path}"

# -------------- LLM scene segmentation (multi-provider chain) --------------
# Groq primary (sub-second), Nvidia fallback, OpenAI ultimate fallback
GROQ_KEY = os.environ.get('GROQ_API_KEY', '')
OPENAI_KEY = os.environ.get('OPENAI_API_KEY', '')

LLM_CHAIN = [
    # (provider, model, endpoint, key, timeout_s, max_tokens)
    ('groq',   'llama-3.3-70b-versatile',     'https://api.groq.com/openai/v1/chat/completions',     GROQ_KEY,   90,  12000),
    ('openai', 'gpt-4o-mini',                  'https://api.openai.com/v1/chat/completions',          OPENAI_KEY, 120, 12000),
    ('nvidia', 'meta/llama-3.3-70b-instruct', 'https://integrate.api.nvidia.com/v1/chat/completions', NVIDIA_KEY, 120, 8000),
]

def call_llm_with_fallback(messages, response_format=None):
    last_err = None
    for provider, model, endpoint, key, timeout, max_tok in LLM_CHAIN:
        if not key:
            print(f"  [llm] skip {provider}/{model} (no key)")
            continue
        for attempt in range(3):
            try:
                payload = {
                    'model': model,
                    'messages': messages,
                    'max_tokens': max_tok,
                    'temperature': 0.5,
                }
                if response_format:
                    payload['response_format'] = response_format
                print(f"  [llm] try {provider}/{model} (timeout={timeout}s, attempt {attempt+1}, max_tok={max_tok})")
                t0 = time.time()
                r = requests.post(endpoint,
                    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
                    json=payload, timeout=timeout)
                # Handle rate limit with exponential backoff
                if r.status_code == 429:
                    backoff = 5 * (2 ** attempt)  # 5, 10, 20s
                    print(f"  [llm] 429 rate limit on {provider}, sleeping {backoff}s")
                    time.sleep(backoff)
                    last_err = RuntimeError(f"429 rate limit on {provider}")
                    continue
                # Handle payload too large by skipping this model
                if r.status_code == 413:
                    print(f"  [llm] 413 payload too large for {provider}/{model}, skipping to next provider")
                    last_err = RuntimeError(f"413 payload too large for {model}")
                    break  # next provider
                r.raise_for_status()
                content = r.json()['choices'][0]['message']['content']
                print(f"  [llm] ✓ {provider}/{model} returned {len(content)} chars in {time.time()-t0:.1f}s")
                # Validate JSON parses if response_format requested
                if response_format and response_format.get('type') == 'json_object':
                    try:
                        json.loads(content)
                    except json.JSONDecodeError as je:
                        print(f"  [llm] ⚠ {provider}/{model} returned malformed JSON ({len(content)} chars, error at char {je.pos}), retrying")
                        last_err = je
                        continue
                return content
            except requests.exceptions.HTTPError as e:
                last_err = e
                print(f"  [llm] ✗ {provider}/{model} attempt {attempt+1}: HTTP {e.response.status_code}: {e.response.text[:120]}")
                time.sleep(3)
            except Exception as e:
                last_err = e
                print(f"  [llm] ✗ {provider}/{model} attempt {attempt+1}: {type(e).__name__}: {str(e)[:120]}")
                time.sleep(3)
    raise RuntimeError(f"All LLM attempts failed. Last: {last_err}")

# ===== VIRAL MODE CONSTANTS =====
# 50-58s = sweet spot algoritmo TikTok/Reels/Shorts em 2026
VIRAL_TARGET_DUR = 55          # alvo central
VIRAL_MIN_DUR = 50
VIRAL_MAX_DUR = 58
VIRAL_TARGET_CHARS = 800       # ~55s a 14.5 chars/s PT-BR
VIRAL_N_SCENES = 8             # ~7s por cena (Psych2Go ritmo)

def expand_short_to_viral(script_short, hook_hint=None, cliff_hint=None):
    """Expande script curto para ~800 chars formato viral 55s.
    Usa hooks/cliffhangers do split_long se disponiveis."""
    extras = ""
    if hook_hint: extras += f"\n\nHOOK SUGERIDO (use no inicio): {hook_hint}"
    if cliff_hint: extras += f"\n\nCLIFFHANGER SUGERIDO (use no fim): {cliff_hint}"
    
    prompt = f"""Voce eh roteirista de canal viral PT-BR de psicologia (estilo Psych2Go, 9M subs).
TAREFA: EXPANDIR este roteiro curto para um video VIRAL de 55 segundos exatos (~800 caracteres).

ROTEIRO ATUAL (curto demais, {len(script_short)} chars):
{script_short}{extras}

REGRAS RIGIDAS:
1. SCRIPT FINAL DEVE TER ENTRE 750 E 850 CARACTERES (nao mais, nao menos)
2. PRESERVE 100% do conteudo original. Adicione exemplos concretos, detalhes psicologicos, situacoes reais.
3. ESTRUTURA OBRIGATORIA: HOOK (45c, 3s) + CONTEUDO (650c, 45s) + CLIFFHANGER (100c, 7s)
4. Linguagem direta TikTok: "voce", frases curtas (max 12 palavras), sem cumprimentos, sem despedidas
5. HOOK chocante ou pergunta provocativa ja na primeira linha
6. CLIFFHANGER instigante: pergunta + CTA ("Comenta aqui", "Salva pra ver depois")

Retorne APENAS JSON: {{"viral_script": "texto narrado completo 750-850 chars"}}"""
    content = call_llm_with_fallback(
        messages=[
            {'role':'system','content':'Voce eh roteirista viral PT-BR. EXPANDA scripts curtos para 750-850 chars. Retorne APENAS JSON valido.'},
            {'role':'user','content':prompt}
        ],
        response_format={'type':'json_object'}
    )
    content = content.strip()
    if content.startswith('```'):
        content = re.sub(r'^```(?:json)?\n', '', content)
        content = re.sub(r'\n```$', '', content)
    data = json.loads(content)
    return data['viral_script']

def viralize_script(script_long):
    """Resume script longo pra ~800 chars otimizado pra viralizar em 55s.
    Estrutura: HOOK (3s) -> CONTEUDO (45s) -> CLIFFHANGER (7s)."""
    prompt = f"""Voce eh roteirista de canal viral PT-BR de psicologia (estilo Psych2Go, 9M subs).
Tarefa: condensar este roteiro num video VIRAL de 55 segundos exatos (~800 caracteres de narracao).

ROTEIRO ORIGINAL:
{script_long}

ESTRUTURA OBRIGATORIA (replica formato dos virais 2026):
1. HOOK (primeiros 3 segundos / ~45 chars): pergunta provocativa OU afirmacao chocante que prende ("Voce sabia que...", "99% das pessoas nao percebe...", "Se voce faz X, isso revela Y")
2. CONTEUDO PRINCIPAL (45 segundos / ~650 chars): 3-4 pontos rapidos do roteiro original, na linguagem direta de TikTok
3. CLIFFHANGER (7 segundos / ~100 chars): pergunta ou call-to-action que instiga ("Comenta aqui se voce ja passou", "Salva pra rever", "Voce se identifica com qual?")

REGRAS:
- LINGUAGEM DIRETA, FRASES CURTAS (max 12 palavras)
- NADA de "neste video", "vamos falar", "como voces sabem"
- USAR "voce" sempre, NUNCA "voces"
- SEM cumprimentos. Comeca DIRETO no hook.
- SEM despedidas. Termina no cliffhanger.

Retorne APENAS JSON: {{"viral_script": "texto narrado completo em portugues"}}"""
    content = call_llm_with_fallback(
        messages=[
            {'role':'system','content':'Voce eh roteirista de viral psicologia PT-BR. Retorne APENAS JSON valido.'},
            {'role':'user','content':prompt}
        ],
        response_format={'type':'json_object'}
    )
    content = content.strip()
    if content.startswith('```'):
        content = re.sub(r'^```(?:json)?\n', '', content)
        content = re.sub(r'\n```$', '', content)
    data = json.loads(content)
    return data['viral_script']

def segment_scenes(script, target_platform, total_duration_s):
    is_viral = any(s in target_platform.lower() for s in ['short','reel','tiktok','pin','viral'])
    aspect = '9:16' if is_viral else '16:9'
    
    # ===== MODO VIRAL: target 55s, force 8 cenas, viralize script if needed =====
    if is_viral:
        # Se script muito longo, condensa pra formato viral primeiro
        if len(script) > 950:
            print(f"  [viral] script {len(script)}c -> condensando para ~{VIRAL_TARGET_CHARS}c")
            script = viralize_script(script)
            print(f"  [viral] viralized -> {len(script)}c")
        # Se script muito curto (de split_long ou similar), EXPANDE pra 800c
        elif len(script) < 700:
            print(f"  [viral] script {len(script)}c -> EXPANDING para ~{VIRAL_TARGET_CHARS}c")
            script = expand_short_to_viral(script)
            print(f"  [viral] expanded -> {len(script)}c")
        # Cap forte: 8 cenas exatas para hit 50-58s
        n_scenes_target = VIRAL_N_SCENES
        target_scene_dur = round(VIRAL_TARGET_DUR / n_scenes_target, 1)  # ~6.9s
        max_scenes = 9
        viral_rules = f"""
ESTRUTURA VIRAL OBRIGATORIA (50-58 SEGUNDOS TOTAIS):
- Cena 1: HOOK forte (3s) - pergunta ou afirmacao que prende
- Cenas 2-7: conteudo principal (~6-7s cada)  
- Cena 8: CLIFFHANGER/CTA (5-7s) - instiga interacao

DURACAO POR CENA: TODAS entre 5-8s. SOMA TOTAL deve ficar entre 50-58s."""
    else:
        # Long form (youtube/youtube_long/youtube_long_monetized)
        is_long_monetized = 'monetized' in target_platform.lower() or 'youtube_long' in target_platform.lower()
        if is_long_monetized:
            # 15-18min monetized: pattern interrupt every 6-8s = ~120-150 cenas pra 16min
            # Strip [MIDROLL_AD_SPOT] markers from script (those are for YouTube auto-ads, not voice)
            script = script.replace('[MIDROLL_AD_SPOT]', ' ')
            estimated_dur_s = len(script) / 14.5
            target_scene_dur = 7  # 7s media = bom equilibrio entre variacao visual e custo Flux
            n_scenes_ideal = max(80, int(estimated_dur_s / target_scene_dur))
            max_scenes = 160  # cap pra render rodar em <30min no GH Actions
            n_scenes_target = min(n_scenes_ideal, max_scenes)
            viral_rules = """
ESTRUTURA LONG-FORM MONETIZED YOUTUBE 15-18min (validada por dados de retencao 70%+ Psych2Go/Therapy in a Nutshell):
- ALTERNAR PROTAGONISTA: nunca repetir mesma pessoa em mais de 3 cenas seguidas (anti-monotonia)
- Pattern interrupt visual a cada 15-25s (mudanca brusca de angulo, cor de fundo, ou personagem)
- Variar generos: 50% mulheres / 50% homens / silhuetas neutras
- Variar etnias: clara/morena/negra alternando
- Variar idades: 20-25, 30-35, 40-50
- Variar cenarios: quarto, escritorio, parque, cafe, rua noite, casa minimalista
- Cenas com ALTA emocao em momentos chave (ponto principal de cada subtopico)
- DURACAO POR CENA: variar entre 5-12s (NAO uniformes - bom ritmo natural)"""
        else:
            # Legacy long form (sem monetizacao planejada)
            estimated_dur_s = len(script) / 14.5
            target_scene_dur = 6
            n_scenes_ideal = max(4, int(estimated_dur_s / target_scene_dur))
            max_scenes = 25
            n_scenes_target = min(n_scenes_ideal, max_scenes)
            viral_rules = ""
    
    print(f"  [seg] {target_platform} | {len(script)}c | {n_scenes_target} cenas alvo (cap {max_scenes}) | viral={is_viral}")
    
    prompt = f"""Voce eh diretor visual do canal Psych2Go (9 milhoes de inscritos). Vai segmentar este roteiro em cenas visuais para um video {aspect}.

ROTEIRO COMPLETO:
{script}

NUMERO DE CENAS: EXATAMENTE {n_scenes_target} CENAS. NEM MAIS, NEM MENOS.
PLATAFORMA: {target_platform}
{viral_rules}

REGRAS CRITICAS DO ESTILO PSYCH2GO (mesmo de canais virais mundiais):
1. NUNCA peca texto, palavras, letras ou subtitulos na imagem
2. Sempre 1 personagem humanoide ilustrado como FOCO (mulher ou homem brasileiro de pele clara/morena/negra alternando entre cenas, 20-40 anos)
3. Fundos minimalistas, cores pastel suaves (rosa pessego, azul ceu, verde menta, lavanda, bege creme)
4. Expressoes faciais MUITO expressivas casando com a emocao da narracao
5. Variar enquadramento: close_face / medium / wide / silhouette / hands_close / profile
6. Cada cena DEVE conter 2-4 frases inteiras. Distribua o roteiro INTEIRO entre as {n_scenes_target} cenas.

Para CADA cena retorne JSON com:
- "narration": fragmento literal do roteiro (NAO mude palavras)
- "duration_s": entre 5-8s
- "image_prompt": descricao visual em INGLES comecando "minimalist 2D illustration in Psych2Go style, flat vector art, soft pastel colors, clean white or pastel background, no text no words no letters,"
- "emotion": [calmo|tenso|empatia|esperanca|urgente|contemplativo|melancolico|alivio]
- "ken_burns": [zoom_in|zoom_out|pan_left|pan_right|static]
- "shot_type": [close_face|medium|wide|silhouette|hands_close|profile]

Retorne SOMENTE JSON valido: {{"scenes":[...], "background_music_mood":"calmo_reflexivo|melancolico_esperancoso|tenso_curioso|empatico_morno"}}

NAO USE TEXTO NA IMAGEM. So personagens, expressoes, ambientes."""

    content = call_llm_with_fallback(
        messages=[
            {'role':'system','content':'Voce eh diretor visual do canal Psych2Go. Personagens humanoides ilustrados, cores pastel, ZERO TEXTO. Retorne APENAS JSON valido.'},
            {'role':'user','content':prompt}
        ],
        response_format={'type':'json_object'}
    )
    content = content.strip()
    if content.startswith('```'):
        content = re.sub(r'^```(?:json)?\n', '', content)
        content = re.sub(r'\n```$', '', content)
    data = json.loads(content)
    scenes = data['scenes']
    
    # Hard cap pos-LLM (caso o modelo gerar mais cenas que o pedido)
    if len(scenes) > max_scenes:
        print(f"  [seg] truncating {len(scenes)} -> {max_scenes} (LLM ignored cap)")
        scenes = scenes[:max_scenes]
    
    # VIRAL MODE: validar total de narration chars >= 700c (~48s)
    # Se LLM cortou narração demais, redistribui o script ORIGINAL pelas cenas
    if is_viral:
        total_narration = sum(len(s.get('narration','')) for s in scenes)
        if total_narration < 700:
            print(f"  [seg] WARN: narration total {total_narration}c < 700c. Redistribuindo script original pelas cenas.")
            # Split script in N approximately equal chunks at sentence boundaries
            n = len(scenes)
            sentences = re.split(r'(?<=[.!?])\s+', script.strip())
            chunks_per_scene = max(1, len(sentences) // n)
            for i, s in enumerate(scenes):
                start = i * chunks_per_scene
                end = (i+1) * chunks_per_scene if i < n-1 else len(sentences)
                new_narr = ' '.join(sentences[start:end]).strip()
                if new_narr:
                    s['narration'] = new_narr
            new_total = sum(len(s.get('narration','')) for s in scenes)
            print(f"  [seg] redistributed -> total {new_total}c across {n} scenes")
    
    return scenes, data.get('background_music_mood', 'calmo_reflexivo')

# -------------- Flux Schnell Nvidia: image generation --------------
def _is_image_valid(path, min_brightness=15, max_brightness=245):
    """Reject black, white, or single-color images that Flux sometimes returns."""
    try:
        # Use ffprobe to get average frame brightness via signalstats
        r = subprocess.run([
            'ffmpeg', '-i', str(path), '-vf',
            'signalstats,metadata=print:key=lavfi.signalstats.YAVG',
            '-f', 'null', '-'
        ], capture_output=True, text=True, timeout=10)
        # Parse YAVG from stderr
        import re
        m = re.search(r'YAVG=([\d.]+)', r.stderr)
        if m:
            yavg = float(m.group(1))
            if yavg < min_brightness:
                print(f"  [flux validate] ✗ image too DARK (yavg={yavg:.0f} < {min_brightness}): {path}")
                return False
            if yavg > max_brightness:
                print(f"  [flux validate] ✗ image too BRIGHT (yavg={yavg:.0f} > {max_brightness}): {path}")
                return False
            return True
    except Exception as e:
        print(f"  [flux validate] could not analyze {path}: {e}")
    # If validation fails for any reason, accept the image (don't block render)
    return True

def gen_image_flux(prompt, output_path, width=768, height=1344, retries=4):
    """9:16 portrait = 768x1344. 16:9 landscape = 1344x768.
    Validates image isn't black/empty; retries with new seed if so."""
    safe_prompt = (prompt + ", clean illustration, no text, no words, no letters, no signs, no captions, no typography, no writing")[:1000]
    for attempt in range(retries):
        payload = {
            'prompt': safe_prompt,
            'cfg_scale': 0,
            'width': width, 'height': height,
            'seed': random.randint(1, 1000000),
            'steps': 4, 'mode': 'base'
        }
        try:
            r = requests.post('https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell',
                headers={'Authorization': f'Bearer {NVIDIA_KEY}', 'Accept': 'application/json'},
                json=payload, timeout=120)
            if r.status_code == 200:
                d = r.json()
                if 'artifacts' in d and d['artifacts']:
                    img_b64 = d['artifacts'][0]['base64']
                    Path(output_path).write_bytes(base64.b64decode(img_b64))
                    # Validate not black/empty
                    if _is_image_valid(output_path):
                        return True
                    print(f"  [flux retry {attempt+1}] image rejected by validator")
                    time.sleep(1)
                    continue
            print(f"  [flux retry {attempt+1}] HTTP {r.status_code}: {r.text[:200]}")
            time.sleep(2)
        except Exception as e:
            print(f"  [flux err {attempt+1}] {type(e).__name__}: {e}")
            time.sleep(2)
    return False

# -------------- Edge TTS audio --------------
EMOTION_VOICE = {
    'calmo':         ('pt-BR-AntonioNeural',   '+0%',   '+0Hz'),
    'tenso':         ('pt-BR-FranciscaNeural', '+8%',   '+30Hz'),
    'empatia':       ('pt-BR-FranciscaNeural', '-3%',   '+0Hz'),
    'esperanca':     ('pt-BR-FranciscaNeural', '+5%',   '+15Hz'),
    'urgente':       ('pt-BR-FranciscaNeural', '+12%',  '+25Hz'),
    'contemplativo': ('pt-BR-AntonioNeural',   '-5%',   '-5Hz'),
    'melancolico':   ('pt-BR-AntonioNeural',   '-8%',   '-10Hz'),
    'alivio':        ('pt-BR-FranciscaNeural', '-3%',   '+5Hz'),
}

def gen_audio_edge_tts(text, emotion, output_path):
    """Generate audio with TTS chain: Edge (1 try) -> gTTS -> OpenAI TTS."""
    voice, rate, pitch = EMOTION_VOICE.get(emotion, EMOTION_VOICE['calmo'])
    errors = []
    
    # 1. Try Edge TTS once (often fails in GH Actions due to MS auth changes)
    try:
        import edge_tts
        async def _gen():
            comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            await comm.save(output_path)
        asyncio.run(_gen())
        if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
            return _probe_duration(output_path)
        raise RuntimeError("edge_tts produced empty file")
    except Exception as e:
        errors.append(f"edge-tts: {type(e).__name__}: {str(e)[:80]}")
    
    # 2. Try gTTS (free, reliable, no emotion control but works in GH Actions)
    try:
        from gtts import gTTS
        # gTTS speed control via slow=True/False only; pick based on emotion
        slow = emotion in ('contemplativo', 'melancolico', 'calmo')
        tts = gTTS(text=text, lang='pt', tld='com.br', slow=slow)
        tts.save(output_path)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
            print(f"  [tts] gTTS used (emotion={emotion}, slow={slow})")
            return _probe_duration(output_path)
        raise RuntimeError("gTTS produced empty file")
    except Exception as e:
        errors.append(f"gTTS: {type(e).__name__}: {str(e)[:80]}")
    
    # 3. Final fallback: OpenAI TTS-1 (paid but very cheap ~$0.015/1k chars)
    if OPENAI_KEY:
        try:
            voice_map_oa = {
                'calmo': 'onyx', 'tenso': 'nova', 'empatia': 'nova',
                'esperanca': 'shimmer', 'urgente': 'nova',
                'contemplativo': 'onyx', 'melancolico': 'echo', 'alivio': 'shimmer'
            }
            r = requests.post('https://api.openai.com/v1/audio/speech',
                headers={'Authorization': f'Bearer {OPENAI_KEY}', 'Content-Type': 'application/json'},
                json={
                    'model': 'tts-1',
                    'input': text,
                    'voice': voice_map_oa.get(emotion, 'nova'),
                    'response_format': 'mp3',
                    'speed': 1.0
                }, timeout=60)
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                f.write(r.content)
            print(f"  [tts] OpenAI TTS used (voice={voice_map_oa.get(emotion, 'nova')})")
            return _probe_duration(output_path)
        except Exception as e:
            errors.append(f"openai-tts: {type(e).__name__}: {str(e)[:80]}")
    
    raise RuntimeError(f"ALL TTS engines failed: {' | '.join(errors)}")

def _probe_duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=noprint_wrappers=1:nokey=1', path],
                       capture_output=True, text=True)
    return float(r.stdout.strip()) if r.stdout.strip() else 0.0

# -------------- ffmpeg compose --------------
def make_kenburns_clip(image_path, duration_s, output_path, motion='zoom_in', target_w=1080, target_h=1920):
    """Generate 30fps clip with Ken Burns motion from static image."""
    fps = 30
    n_frames = int(duration_s * fps)
    
    # Ken Burns parameters per motion type
    if motion == 'zoom_in':
        zoom_expr = f"min(zoom+0.0015,1.3)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif motion == 'zoom_out':
        zoom_expr = f"if(eq(on,0),1.3,max(zoom-0.0015,1.0))"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif motion == 'pan_left':
        zoom_expr = "1.15"
        x_expr = f"if(eq(on,0),iw-(iw/1.15),x-(iw*0.0008))"
        y_expr = "ih/2-(ih/zoom/2)"
    elif motion == 'pan_right':
        zoom_expr = "1.15"
        x_expr = f"if(eq(on,0),0,x+(iw*0.0008))"
        y_expr = "ih/2-(ih/zoom/2)"
    else:  # static with subtle zoom
        zoom_expr = f"min(zoom+0.0008,1.1)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    
    vf = (
        f"scale={target_w*2}:{target_h*2}:flags=lanczos,"
        f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':"
        f"d={n_frames}:s={target_w}x{target_h}:fps={fps}"
    )
    
    cmd = [
        'ffmpeg', '-y', '-loglevel', 'error',
        '-loop', '1', '-i', str(image_path),
        '-vf', vf, '-t', str(duration_s),
        '-r', str(fps),
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
        '-pix_fmt', 'yuv420p', str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def concat_clips_with_crossfade(clip_paths, audio_path, output_path, crossfade_s=0.4):
    """Concatenate Ken Burns clips and overlay narration audio."""
    # Build concat input list
    list_file = WORK / 'concat.txt'
    list_file.write_text('\n'.join(f"file '{p}'" for p in clip_paths))
    
    # Concat video
    intermediate = WORK / 'concat.mp4'
    subprocess.run([
        'ffmpeg', '-y', '-loglevel', 'error',
        '-f', 'concat', '-safe', '0', '-i', str(list_file),
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
        '-pix_fmt', 'yuv420p', str(intermediate)
    ], check=True)
    
    # Mix narration audio + soft background music if available
    bg_music = WORK / 'bg_music.mp3'
    if bg_music.exists():
        # narration full vol + bg music at 8%
        af = '[0:a]volume=1.0[a1];[1:a]volume=0.08,aloop=loop=-1:size=2e+09[a2];[a1][a2]amix=inputs=2:duration=first[aout]'
        cmd = [
            'ffmpeg', '-y', '-loglevel', 'error',
            '-i', str(intermediate),
            '-i', audio_path,
            '-i', str(bg_music),
            '-filter_complex', af,
            '-map', '0:v', '-map', '[aout]',
            '-c:v', 'copy',
            '-c:a', 'aac', '-b:a', '192k',
            '-shortest', str(output_path)
        ]
    else:
        cmd = [
            'ffmpeg', '-y', '-loglevel', 'error',
            '-i', str(intermediate),
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac', '-b:a', '192k',
            '-shortest', str(output_path)
        ]
    subprocess.run(cmd, check=True)

def merge_scene_audios(audio_paths, output_path):
    """Concatenate per-scene audio files into one."""
    list_file = WORK / 'audio_concat.txt'
    list_file.write_text('\n'.join(f"file '{p}'" for p in audio_paths))
    subprocess.run([
        'ffmpeg', '-y', '-loglevel', 'error',
        '-f', 'concat', '-safe', '0', '-i', str(list_file),
        '-c:a', 'libmp3lame', '-b:a', '192k', str(output_path)
    ], check=True)

# -------------- Main pipeline --------------
def run():
    print(f"[1/7] Fetch pipeline #{PIPELINE_ID}")
    pipelines = sb_get(f"content_pipeline?id=eq.{PIPELINE_ID}&select=*")
    if not pipelines:
        print(f"❌ Pipeline #{PIPELINE_ID} not found")
        return 1
    p = pipelines[0]
    script = p['script']
    title = p['title']
    target_platform = p['target_platform']
    # 9:16 ONLY for vertical platforms (shorts/reels/tiktok/pin); long_monetized = 16:9
    is_short = any(s in target_platform.lower() for s in ['short','reel','tiktok','pin'])
    is_long_monetized = 'monetized' in target_platform.lower() or 'youtube_long' in target_platform.lower()
    target_duration = 60 if is_short else (960 if is_long_monetized else 480)  # 16min long_monetized
    
    print(f"  Title: {title}")
    fmt = 'SHORT 9:16' if is_short else ('LONG_MONETIZED 16:9 16min' if is_long_monetized else 'LONG 16:9')
    print(f"  Platform: {target_platform} ({fmt})")
    print(f"  Script: {len(script)} chars")
    
    print(f"\n[2/7] Segment script into scenes (DeepSeek V4 Pro)")
    scenes, music_mood = segment_scenes(script, target_platform, target_duration)
    print(f"  Generated {len(scenes)} scenes · music_mood={music_mood}")
    for i, s in enumerate(scenes[:3]):
        print(f"  • Scene {i+1} ({s['duration_s']}s, {s['emotion']}, {s['shot_type']}): {s['narration'][:70]}...")
    
    print(f"\n[3/7] Generate audio per scene (Edge TTS)")
    audio_paths = []
    actual_durations = []
    for i, sc in enumerate(scenes):
        ap = WORK / f"audio_{i:03d}.mp3"
        actual_dur = gen_audio_edge_tts(sc['narration'], sc['emotion'], str(ap))
        audio_paths.append(str(ap))
        actual_durations.append(actual_dur)
        # Use ACTUAL audio duration (more accurate than DeepSeek estimate)
        sc['duration_s'] = max(actual_dur + 0.3, 2.0)  # +0.3s breathing room, min 2s
        print(f"  ✓ Scene {i+1}: {sc['duration_s']:.1f}s ({sc['emotion']})")
    
    print(f"\n[4/7] Generate images (Flux Schnell Nvidia)")
    width, height = (768, 1344) if is_short else (1344, 768)
    out_w, out_h = (1080, 1920) if is_short else (1920, 1080)
    image_paths = []
    for i, sc in enumerate(scenes):
        ip = WORK / f"image_{i:03d}.jpg"
        ok = gen_image_flux(sc['image_prompt'], ip, width=width, height=height)
        if ok:
            image_paths.append(str(ip))
            print(f"  ✓ Scene {i+1} image generated")
        else:
            # Fallback: copy previous image if exists
            if image_paths:
                shutil.copy(image_paths[-1], ip)
                image_paths.append(str(ip))
                print(f"  ⚠ Scene {i+1} flux failed, reused previous")
            else:
                print(f"  ❌ Scene {i+1} flux failed and no previous image")
                return 2
    
    print(f"\n[5/7] Compose Ken Burns clips per scene")
    clip_paths = []
    for i, sc in enumerate(scenes):
        cp = WORK / f"clip_{i:03d}.mp4"
        make_kenburns_clip(image_paths[i], sc['duration_s'], cp,
                          motion=sc.get('ken_burns', 'static'),
                          target_w=out_w, target_h=out_h)
        clip_paths.append(str(cp))
    print(f"  ✓ {len(clip_paths)} Ken Burns clips generated")
    
    print(f"\n[6/7] Merge audio + concat clips + final encode")
    full_audio = WORK / 'narration.mp3'
    merge_scene_audios(audio_paths, str(full_audio))
    
    final_mp4 = WORK / f"pipeline_{PIPELINE_ID}_v2.mp4"
    concat_clips_with_crossfade(clip_paths, str(full_audio), str(final_mp4))
    final_size = final_mp4.stat().st_size
    print(f"  ✓ Final MP4: {final_size/1024/1024:.1f}MB")
    
    print(f"\n[7/7] Upload to Supabase Storage")
    storage_path = f"v2/pipeline_{PIPELINE_ID}_{int(time.time())}.mp4"
    public_url = sb_upload_storage('videos', storage_path, str(final_mp4), 'video/mp4')
    if not public_url:
        print("❌ Upload failed")
        return 3
    print(f"  ✓ Public URL: {public_url}")
    
    # Update pipeline metadata
    new_meta = p.get('metadata', {}) or {}
    new_meta['video_gen_v2'] = {
        'engine': 'flux_schnell_nvidia + edge_tts + ffmpeg',
        'scenes': len(scenes),
        'duration_s': sum(actual_durations),
        'music_mood': music_mood,
        'rendered_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'visual_style': 'psych2go_clone',
        'no_text_on_screen': True
    }
    sb_patch(f"content_pipeline?id=eq.{PIPELINE_ID}",
             {'mp4_url': public_url, 'metadata': new_meta})
    print(f"  ✓ Pipeline #{PIPELINE_ID} updated")
    
    print(f"\n✅ DONE in {time.time() - START_TIME:.0f}s")
    print(f"📺 Watch: {public_url}")
    return 0

START_TIME = time.time()
if __name__ == '__main__':
    try:
        sys.exit(run())
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(99)
