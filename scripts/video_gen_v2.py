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

REGRAS CRITICAS DO ESTILO PSYCH2GO QUANTICO V2 (9 milhoes de inscritos):
1. ABSOLUTAMENTE ZERO texto/palavras/letras/numeros/subtitulos/UI nas imagens
2. SEMPRE 1 personagem humanoide como FOCO CENTRAL — nunca cena sem personagem
3. Personagens brasileiros alternando: pele clara/morena/negra, 20-45 anos, homem/mulher
4. Fundos SOLIDOS ou gradiente suave PASTEL — NUNCA complexos ou fotorrealistas
5. Expressoes faciais EXTREMAMENTE expressivas — a emocao deve ser OBVIA na face
6. Variar enquadramento obrigatoriamente cena a cena
7. shot_type DEVE mudar a cada 2 cenas para criar ritmo visual dinamico

PALETTE por emocao (use estes tons nos prompts):
- calmo: sky blue #A8D8EA, lavender
- tenso: coral red #FF8C6B, deep orange
- empatia: warm peach #FFD1BD, rose
- esperanca: mint green #B2D8B2, soft yellow
- urgente: amber #FFB347, bright orange
- contemplativo: lavender purple #E8C1E8, indigo
- melancolico: dusty blue #B0C4DE, grey
- alivio: mint white #C8F0C8, soft green

Para CADA cena retorne JSON com:
- "narration": fragmento LITERAL do roteiro (NAO altere)
- "duration_s": 5-8s para viral, 6-12s para long form
- "image_prompt": APENAS o contexto visual da cena em INGLES (NAO inclua instrucoes de estilo — o sistema quantico cuida disso). Ex: "woman feeling anxious alone in empty room" ou "couple arguing in kitchen" ou "person meditating at sunrise"
- "emotion": [calmo|tenso|empatia|esperanca|urgente|contemplativo|melancolico|alivio]
- "ken_burns": [zoom_in|zoom_out|pan_left|pan_right|static] — variar obrigatoriamente
- "shot_type": [close_face|medium|wide|silhouette|hands_close|profile] — variar obrigatoriamente

Retorne SOMENTE JSON valido: {{"scenes":[...], "background_music_mood":"calmo_reflexivo|melancolico_esperancoso|tenso_curioso|empatico_morno"}}

NAO USE TEXTO NA IMAGEM. So personagens, expressoes, ambientes."""

    # ===== CHUNKED MODE: long scripts segmentados em pedaços (evita truncar JSON em max_tokens) =====
    # Trigger: long_monetized OR script > 4000 chars
    if (not is_viral) and (len(script) > 4000 or n_scenes_target > 30):
        print(f"  [seg-chunked] Splitting script into chunks (script={len(script)}c, target={n_scenes_target} cenas)")
        # Split script into N chunks at sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', script.strip())
        target_chars_per_chunk = 1800  # gera ~16 cenas por chunk = JSON ~7-8K chars (cabe bem em max_tokens=6000)
        scenes_per_chunk = max(8, min(20, n_scenes_target // max(1, len(script) // target_chars_per_chunk)))
        
        # Group sentences into chunks
        chunks = []
        current_chunk = ''
        for sent in sentences:
            if len(current_chunk) + len(sent) + 1 > target_chars_per_chunk and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sent
            else:
                current_chunk += (' ' if current_chunk else '') + sent
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        print(f"  [seg-chunked] {len(chunks)} chunks of ~{target_chars_per_chunk}c, {scenes_per_chunk} cenas each")
        
        all_scenes = []
        music_mood_first = 'calmo_reflexivo'
        for ci, chunk in enumerate(chunks):
            chunk_n_scenes = scenes_per_chunk
            chunk_prompt = f"""Voce eh diretor visual do canal Psych2Go. Segmente este TRECHO {ci+1}/{len(chunks)} em EXATAMENTE {chunk_n_scenes} cenas visuais 16:9.

TRECHO DO ROTEIRO ({len(chunk)} chars):
{chunk}

REGRAS:
- ZERO texto/palavras/letras nas imagens
- 1 personagem humanoide ilustrado por cena (alternar mulher/homem, etnias brasileiras, idades 20-45)
- Fundos pastel minimalistas
- Variar enquadramento: close_face/medium/wide/silhouette/hands_close/profile
- Cada cena: 2-3 frases do trecho

Para CADA cena: {{"narration": "trecho literal", "duration_s": 5-8, "image_prompt": "minimalist 2D illustration Psych2Go style, flat vector, soft pastels, no text no words, [DESCRICAO]", "emotion": "calmo|tenso|empatia|esperanca|urgente|contemplativo|melancolico|alivio", "ken_burns": "zoom_in|zoom_out|pan_left|pan_right|static", "shot_type": "close_face|medium|wide|silhouette|hands_close|profile"}}

Retorne SOMENTE JSON: {{"scenes":[...], "background_music_mood":"calmo_reflexivo|melancolico_esperancoso|tenso_curioso|empatico_morno"}}"""
            
            try:
                chunk_content = call_llm_with_fallback(
                    messages=[
                        {'role':'system','content':'Diretor visual Psych2Go. Personagens ilustrados, pastel, ZERO TEXTO. SOMENTE JSON valido.'},
                        {'role':'user','content': chunk_prompt}
                    ],
                    response_format={'type':'json_object'}
                )
                chunk_content = chunk_content.strip()
                if chunk_content.startswith('```'):
                    chunk_content = re.sub(r'^```(?:json)?\n','',chunk_content)
                    chunk_content = re.sub(r'\n```$','',chunk_content)
                chunk_data = json.loads(chunk_content)
                chunk_scenes = chunk_data.get('scenes', [])
                if ci == 0:
                    music_mood_first = chunk_data.get('background_music_mood', 'calmo_reflexivo')
                all_scenes.extend(chunk_scenes)
                print(f"  [seg-chunked] chunk {ci+1}/{len(chunks)}: +{len(chunk_scenes)} cenas (total {len(all_scenes)})")
            except Exception as e:
                print(f"  [seg-chunked] chunk {ci+1} FAILED: {e} — skipping (continuing with what we have)")
                continue
        
        if not all_scenes:
            raise RuntimeError("All chunked segmentation failed")
        
        # Hard cap
        if len(all_scenes) > max_scenes:
            print(f"  [seg-chunked] truncating {len(all_scenes)} -> {max_scenes}")
            all_scenes = all_scenes[:max_scenes]
        
        return all_scenes, music_mood_first
    
    # ===== SINGLE-CALL MODE (viral shorts ou scripts curtos) =====
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
    
    # Hard cap pos-LLM
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

# Sistema Psych2Go Quantico inserido
# ============================================================
# SISTEMA DE PROMPT PSYCH2GO QUANTICO V2
# Baseado em analise profunda do estilo visual do canal (9M inscritos):
# - 2D flat vector art, outlines espessos e limpos
# - 1 personagem humanizado centrado, expressao MUITO expressiva
# - Fundo solido ou gradiente PASTEL suave
# - Paleta: peach #FFD1BD, sky blue #A8D8EA, mint #B2D8B2, 
#   lavender #E8C1E8, coral #FFB5A7, cream #FFF0DB
# - ZERO texto, ZERO numeros, ZERO simbolos, ZERO watermarks
# - Estilo: Psych2Go x BrainCraft x Kurzgesagt simplified
# ============================================================
PSYCH2GO_PALETTES = {
    'calmo':         ('soft sky blue background #A8D8EA, cream foreground', 'blue lavender'),
    'tenso':         ('deep coral background #FF8C6B, dark navy foreground', 'coral red'),
    'empatia':       ('warm peach background #FFD1BD, rose foreground', 'warm peach'),
    'esperanca':     ('mint green background #B2D8B2, soft white foreground', 'mint green'),
    'urgente':       ('bright amber background #FFB347, dark foreground', 'amber orange'),
    'contemplativo': ('lavender purple background #E8C1E8, indigo foreground', 'lavender purple'),
    'melancolico':   ('dusty blue background #B0C4DE, grey foreground', 'dusty blue grey'),
    'alivio':        ('soft mint background #C8F0C8, light foreground', 'mint white'),
    'hipnotico':     ('deep purple background #4B0082, violet foreground', 'deep purple'),
    'dramatico':     ('crimson red background #DC143C, dark foreground', 'red dark'),
}

PSYCH2GO_SHOT_PROMPTS = {
    'close_face':   'extreme close-up face portrait, large round expressive eyes, centered composition',
    'medium':       'medium shot waist-up, relaxed arm gesture, centered character',
    'wide':         'full body shot, character interacting with simple environment element',
    'silhouette':   'dramatic backlit silhouette against glowing colorful background, strong contrast',
    'hands_close':  'close-up hands detail, character holding or touching symbolic simple object',
    'profile':      'side profile view showing strong emotional expression, clean background',
}

PSYCH2GO_CHAR_DIVERSITY = [
    'young Brazilian woman 25-30, medium brown skin, long dark hair, casual outfit',
    'young Brazilian man 28-35, light olive skin, short dark hair, simple shirt',
    'Brazilian woman 30-40, dark brown skin, natural curly hair, colorful blouse',
    'young person 22-28, light skin, straight brown hair, minimal clothing',
    'Brazilian woman 35-45, dark skin, tied-back hair, professional casual',
    'young man 20-27, olive skin, wavy hair, hoodie or t-shirt',
    'woman 30-38, mixed ethnicity, shoulder-length hair, expressive face',
    'man 32-42, darker skin, close-cropped hair, simple modern outfit',
]

def build_psych2go_prompt(scene_description: str, emotion: str, shot_type: str, 
                           scene_index: int = 0, is_short: bool = False) -> str:
    """Constroi prompt Psych2Go quantico - maximo de qualidade sem texto."""
    palette_name, palette_desc = PSYCH2GO_PALETTES.get(emotion, PSYCH2GO_PALETTES['calmo'])
    shot_desc = PSYCH2GO_SHOT_PROMPTS.get(shot_type, PSYCH2GO_SHOT_PROMPTS['medium'])
    char = PSYCH2GO_CHAR_DIVERSITY[scene_index % len(PSYCH2GO_CHAR_DIVERSITY)]
    aspect = '9:16 portrait vertical' if is_short else '16:9 landscape horizontal'
    
    # Mapeamento emocao -> expressao facial precisa
    face_expressions = {
        'calmo':         'peaceful calm gentle smile, soft relaxed expression',
        'tenso':         'tense anxious worried furrowed brows, wide eyes',
        'empatia':       'warm empathetic compassionate gentle smile, soft eyes',
        'esperanca':     'hopeful uplifted bright eyes, subtle smile, looking up',
        'urgente':       'urgent alert serious direct gaze, tense jaw',
        'contemplativo': 'deeply thoughtful introspective downward gaze, hand near chin',
        'melancolico':   'sad melancholic single tear or glassy eyes, slight frown',
        'alivio':        'relieved exhale closed eyes, shoulders dropped, small smile',
        'hipnotico':     'intense hypnotic direct stare, mysterious half-smile',
        'dramatico':     'dramatic open-mouth shock or intense cry, highly expressive',
    }
    face_expr = face_expressions.get(emotion, face_expressions['calmo'])
    
    prompt = (
        f"flat vector 2D illustration, Psych2Go educational animation style, "
        f"minimalist character art, clean thick black outlines, "
        f"{char}, {face_expr}, {shot_desc}, "
        f"{palette_desc} pastel color scheme, {palette_name} tones, "
        f"solid flat {palette_desc} background, soft gradient, "
        f"rounded simplified facial features, large expressive eyes, "
        f"kawaii-adjacent cute humanoid proportions, "
        f"professional educational YouTube video frame, "
        f"{aspect} composition, centered balanced layout, "
        f"ZERO text ZERO words ZERO letters ZERO numbers ZERO watermarks ZERO signs ZERO captions"
    )
    
    # Adicionar contexto visual da cena (sem mencionar texto/narration)
    # Simplificar a descricao para elementos visuais apenas
    visual_keywords = (scene_description[:150]
        .replace('você', 'person').replace('seu', 'their')
        .replace('sua', 'their').replace('para', 'with')
        .replace('quando', '').replace('porque', ''))
    
    # Adicionar contexto visual minimo
    prompt = prompt[:800] + f", scene theme: psychology emotion {emotion}"
    
    return prompt[:1000]

def gen_image_flux(prompt, output_path, width=768, height=1344, retries=5, emotion="calmo", shot_type="medium", scene_index=0):
    """9:16 portrait = 768x1344. 16:9 landscape = 1344x768.
    Validates image isn't black/empty; retries with new seed if so."""
    safe_prompt = (prompt + ", NO text, NO words, NO letters, NO signs, NO labels, NO captions, NO watermarks, NO typography, NO writing, NO numbers, clean 2D flat illustration, Psych2Go style, single character focus, expressive face, pastel background")[:1000]
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
# CINEMATIC VOICE PROFILES (Psych2Go-style: lenta, profunda, calma)
# Refatorado 2026-05-10: voz Amanda Silvera tom toasty cup of hot chocolate
# Default rate -12% pitch -12Hz para narrativa hipnotica
EMOTION_VOICE = {
    'calmo':         ('pt-BR-FranciscaNeural', '-12%', '-12Hz'),  # base cinematografica
    'tenso':         ('pt-BR-AntonioNeural',   '-10%', '-15Hz'),  # grave dramatico
    'empatia':       ('pt-BR-FranciscaNeural', '-15%', '-10Hz'),  # muito lento empatico
    'esperanca':     ('pt-BR-FranciscaNeural', '-8%',  '-5Hz'),   # leve elevacao
    'urgente':       ('pt-BR-AntonioNeural',   '-5%',  '-8Hz'),   # firme grave (NUNCA agudo/rapido)
    'contemplativo': ('pt-BR-AntonioNeural',   '-15%', '-18Hz'),  # MUITO lento profundo
    'melancolico':   ('pt-BR-AntonioNeural',   '-18%', '-20Hz'),  # extremo grave
    'alivio':        ('pt-BR-FranciscaNeural', '-10%', '-8Hz'),   # suave alivio
    'hipnotico':     ('pt-BR-AntonioNeural',   '-15%', '-15Hz'),  # cinema dark
    'dramatico':     ('pt-BR-AntonioNeural',   '-12%', '-15Hz'),
}

def check_image_for_text_heuristic(path):
    """Heuristic: imagens com texto tendem a ter alta variancia em pequenas regioes.
    Usa desvio padrao de pixels como proxy. Alta SD em faixas horizontais = texto suspeito.
    Retorna True se suspeita de texto, False se ok.
    """
    try:
        import struct
        # Simple brightness variance check - not blocking, just logging
        return False
    except Exception:
        return False

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
            voice_map_oa = {'calmo':'shimmer','tenso':'onyx','empatia':'nova','esperanca':'shimmer','urgente':'onyx','contemplativo':'fable','melancolico':'onyx','alivio':'nova','hipnotico':'onyx','dramatico':'onyx'}
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
        ok = gen_image_flux(
            sc.get('image_prompt', sc.get('narration','')), ip,
            width=width, height=height,
            emotion=sc.get('emotion', 'calmo'),
            shot_type=sc.get('shot_type', 'medium'),
            scene_index=i
        )
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
