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
import os, sys, json, base64, requests, subprocess, asyncio, hashlib, time, tempfile, shutil, random
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

# -------------- DeepSeek V4 Pro: scene segmentation --------------
def segment_scenes(script, target_platform, total_duration_s):
    is_short = any(s in target_platform.lower() for s in ['short', 'reel', 'tiktok', 'pin'])
    aspect = '9:16' if is_short else '16:9'
    avg_scene_dur = 4 if is_short else 5
    n_scenes_target = max(6, int(total_duration_s / avg_scene_dur))
    
    prompt = f"""Voce eh diretor visual do canal Psych2Go (9 milhoes de inscritos). Vai segmentar este roteiro de psicologia em cenas visuais para um video {aspect}.

ROTEIRO COMPLETO:
{script}

DURACAO TOTAL: {total_duration_s} segundos
NUMERO DE CENAS ALVO: {n_scenes_target}
PLATAFORMA: {target_platform}

REGRAS CRITICAS PARA O ESTILO PSYCH2GO:
1. NUNCA gere prompt que peca texto, palavras, letras ou subtitulos na imagem
2. Sempre tenha 1 personagem humanoide ilustrado como FOCO da imagem (mulher ou homem brasileiro de pele clara/morena/negra alternando, idade 20-45)
3. Fundos: minimalistas, cores pastel suaves (rosa pessego, azul ceu, verde menta, lavanda)
4. Expressoes faciais devem CASAR com a emocao da narracao naquele trecho
5. Variar enquadramento entre: close de rosto, plano medio, silhueta, mao em close-up, perfil
6. Cada cena dura entre 3 e 6 segundos

Para CADA cena retorne:
- "narration": fragmento curto do roteiro (literal, sem mudar palavras) que vai ser narrado naquela cena
- "duration_s": 3-6 segundos (decida baseado no comprimento da narracao)
- "image_prompt": descricao visual em INGLES (Flux entende ingles melhor) descrevendo SOMENTE a cena visual sem mencionar texto. Comece sempre com "minimalist illustration in Psych2Go style, soft pastel colors, clean background, no text, no words,"
- "emotion": uma das emocoes [calmo, tenso, empatia, esperanca, urgente, contemplativo, melancolico, alivio]
- "ken_burns": uma de [zoom_in, zoom_out, pan_left, pan_right, static]
- "shot_type": uma de [close_face, medium, wide, silhouette, hands_close, profile]

Retorne APENAS JSON valido: {{"scenes": [...], "background_music_mood": "calmo_reflexivo|melancolico_esperancoso|tenso_curioso|empatico_morno"}}

NAO USE TEXTO NA IMAGEM. NAO MENCIONE PALAVRAS NO PROMPT. So personagens, expressoes, ambientes."""

    r = requests.post('https://integrate.api.nvidia.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {NVIDIA_KEY}', 'Content-Type': 'application/json'},
        json={
            'model': 'deepseek-ai/deepseek-v4-pro',
            'messages': [
                {'role': 'system', 'content': 'Voce eh diretor visual do canal Psych2Go (9M subs). Estilo: personagens humanoides ilustrados, cores pastel, ZERO TEXTO na tela. Retorne SOMENTE JSON valido.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 8000, 'temperature': 0.5,
            'response_format': {'type': 'json_object'}
        }, timeout=180)
    r.raise_for_status()
    data = json.loads(r.json()['choices'][0]['message']['content'])
    return data['scenes'], data.get('background_music_mood', 'calmo_reflexivo')

# -------------- Flux Schnell Nvidia: image generation --------------
def gen_image_flux(prompt, output_path, width=768, height=1344, retries=3):
    """9:16 portrait = 768x1344. 16:9 landscape = 1344x768."""
    # Reforço anti-texto
    safe_prompt = (prompt + ", clean illustration, no text, no words, no letters, no signs, no captions, no typography, no writing")[:1000]
    payload = {
        'prompt': safe_prompt,
        'cfg_scale': 0,
        'width': width, 'height': height,
        'seed': random.randint(0, 1000000),
        'steps': 4, 'mode': 'base'
    }
    for attempt in range(retries):
        try:
            r = requests.post('https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell',
                headers={'Authorization': f'Bearer {NVIDIA_KEY}', 'Accept': 'application/json'},
                json=payload, timeout=120)
            if r.status_code == 200:
                d = r.json()
                if 'artifacts' in d and d['artifacts']:
                    img_b64 = d['artifacts'][0]['base64']
                    Path(output_path).write_bytes(base64.b64decode(img_b64))
                    return True
            print(f"[flux retry {attempt+1}] {r.status_code}: {r.text[:200]}")
            time.sleep(2)
        except Exception as e:
            print(f"[flux err] {e}")
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
    import edge_tts
    voice, rate, pitch = EMOTION_VOICE.get(emotion, EMOTION_VOICE['calmo'])
    async def _gen():
        comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await comm.save(output_path)
    asyncio.run(_gen())
    # Get actual duration
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=noprint_wrappers=1:nokey=1', output_path],
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
    is_short = any(s in target_platform.lower() for s in ['short', 'reel', 'tiktok', 'pin'])
    target_duration = 60 if is_short else 480
    
    print(f"  Title: {title}")
    print(f"  Platform: {target_platform} ({'SHORT 9:16' if is_short else 'LONG 16:9'})")
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
