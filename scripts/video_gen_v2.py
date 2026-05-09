#!/usr/bin/env python3
"""Video Gen V2 - Psych2Go style: scene segmentation + Flux Schnell + Edge TTS + ffmpeg.
ZERO text on screen. Synced illustrations matching narration."""
import os, sys, json, base64, requests, subprocess, asyncio, time, tempfile, shutil, random, traceback
from pathlib import Path

NV = os.environ['NVIDIA_API_KEY']
SU = os.environ['SUPABASE_URL']
SK = os.environ['SUPABASE_SERVICE_KEY']
PID = int(os.environ.get('PIPELINE_ID') or sys.argv[1])
W = Path(tempfile.mkdtemp(prefix='vg2_'))
print(f"[init] pid={PID} work={W}")
T0 = time.time()

def sb(method, path, body=None, ct='application/json'):
    h = {'apikey': SK, 'Authorization': f'Bearer {SK}', 'Content-Type': ct}
    if method == 'GET': return requests.get(f"{SU}/rest/v1/{path}", headers=h, timeout=30).json()
    if method == 'PATCH':
        h['Prefer'] = 'return=representation'
        return requests.patch(f"{SU}/rest/v1/{path}", headers=h, json=body, timeout=30)

def upload_storage(bucket, path, fp, ct):
    with open(fp, 'rb') as f: d = f.read()
    h = {'apikey': SK, 'Authorization': f'Bearer {SK}', 'Content-Type': ct, 'x-upsert': 'true'}
    r = requests.post(f"{SU}/storage/v1/object/{bucket}/{path}", headers=h, data=d, timeout=180)
    if r.status_code >= 400: print(f"[upload ERR {r.status_code}] {r.text[:200]}"); return None
    return f"{SU}/storage/v1/object/public/{bucket}/{path}"

def deepseek(prompt, system, max_tok=8000, temp=0.5):
    r = requests.post('https://integrate.api.nvidia.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {NV}', 'Content-Type': 'application/json'},
        json={'model': 'deepseek-ai/deepseek-v4-pro',
              'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': prompt}],
              'max_tokens': max_tok, 'temperature': temp,
              'response_format': {'type': 'json_object'}}, timeout=180)
    r.raise_for_status()
    return json.loads(r.json()['choices'][0]['message']['content'])

def segment_scenes(script, plat, dur):
    short = any(s in plat.lower() for s in ['short','reel','tiktok','pin'])
    aspect = '9:16' if short else '16:9'
    n_target = max(6, int(dur / 4))
    sys_p = "Voce e diretor visual do canal Psych2Go (9M subs). Estilo: personagens humanoides ilustrados, cores pastel, ZERO TEXTO. Retorne SOMENTE JSON valido."
    usr_p = f"""Segmente este roteiro em cenas visuais {aspect}.

ROTEIRO: {script}
DURACAO: {dur}s
CENAS ALVO: {n_target}
PLATAFORMA: {plat}

REGRAS PSYCH2GO:
1. NUNCA gere prompt pedindo texto/palavras/letras na imagem
2. 1 personagem humanoide brasileiro como FOCO (mulher/homem alternando, 20-45a, peles variadas)
3. Fundos minimalistas, cores pastel suaves
4. Expressao casa com emocao da narracao
5. Variar enquadramento: close_face, medium, wide, silhouette, hands_close, profile
6. Cada cena 3-6s

Para cada cena retorne:
- narration: fragmento literal do roteiro
- duration_s: 3-6
- image_prompt: descricao visual EM INGLES, comece com "minimalist illustration in Psych2Go style, soft pastel colors, clean background, no text, no words,"
- emotion: [calmo, tenso, empatia, esperanca, urgente, contemplativo, melancolico, alivio]
- ken_burns: [zoom_in, zoom_out, pan_left, pan_right, static]
- shot_type: [close_face, medium, wide, silhouette, hands_close, profile]

Retorne: {{"scenes": [...], "music_mood": "calmo_reflexivo|melancolico_esperancoso|tenso_curioso|empatico_morno"}}"""
    d = deepseek(usr_p, sys_p)
    return d['scenes'], d.get('music_mood', 'calmo_reflexivo')

def flux(prompt, out, w=768, h=1344, retries=3):
    sp = (prompt + ", clean illustration, no text, no words, no letters, no signs, no captions, no typography, no writing")[:1000]
    for i in range(retries):
        try:
            r = requests.post('https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell',
                headers={'Authorization': f'Bearer {NV}', 'Accept': 'application/json'},
                json={'prompt': sp, 'cfg_scale': 0, 'width': w, 'height': h,
                      'seed': random.randint(0,1000000), 'steps': 4, 'mode': 'base'}, timeout=120)
            if r.status_code == 200:
                d = r.json()
                if d.get('artifacts'):
                    Path(out).write_bytes(base64.b64decode(d['artifacts'][0]['base64']))
                    return True
            print(f"[flux retry {i+1}] {r.status_code}: {r.text[:150]}")
            time.sleep(2)
        except Exception as e:
            print(f"[flux err] {e}"); time.sleep(2)
    return False

EMO = {
    'calmo': ('pt-BR-AntonioNeural','+0%','+0Hz'),
    'tenso': ('pt-BR-FranciscaNeural','+8%','+30Hz'),
    'empatia': ('pt-BR-FranciscaNeural','-3%','+0Hz'),
    'esperanca': ('pt-BR-FranciscaNeural','+5%','+15Hz'),
    'urgente': ('pt-BR-FranciscaNeural','+12%','+25Hz'),
    'contemplativo': ('pt-BR-AntonioNeural','-5%','-5Hz'),
    'melancolico': ('pt-BR-AntonioNeural','-8%','-10Hz'),
    'alivio': ('pt-BR-FranciscaNeural','-3%','+5Hz'),
}

def tts(text, emo, out):
    import edge_tts
    v, r, p = EMO.get(emo, EMO['calmo'])
    async def g():
        c = edge_tts.Communicate(text, v, rate=r, pitch=p)
        await c.save(out)
    asyncio.run(g())
    rs = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                         '-of','default=noprint_wrappers=1:nokey=1', out], capture_output=True, text=True)
    return float(rs.stdout.strip()) if rs.stdout.strip() else 0.0

def kb_clip(img, dur, out, motion='static', tw=1080, th=1920):
    fps = 30
    nf = int(dur * fps)
    if motion == 'zoom_in':
        z, x, y = "min(zoom+0.0015,1.3)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == 'zoom_out':
        z, x, y = "if(eq(on,0),1.3,max(zoom-0.0015,1.0))", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == 'pan_left':
        z, x, y = "1.15", "if(eq(on,0),iw-(iw/1.15),x-(iw*0.0008))", "ih/2-(ih/zoom/2)"
    elif motion == 'pan_right':
        z, x, y = "1.15", "if(eq(on,0),0,x+(iw*0.0008))", "ih/2-(ih/zoom/2)"
    else:
        z, x, y = "min(zoom+0.0008,1.1)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    vf = f"scale={tw*2}:{th*2}:flags=lanczos,zoompan=z='{z}':x='{x}':y='{y}':d={nf}:s={tw}x{th}:fps={fps}"
    subprocess.run(['ffmpeg','-y','-loglevel','error','-loop','1','-i', str(img),
                    '-vf', vf, '-t', str(dur), '-r', str(fps),
                    '-c:v','libx264','-preset','fast','-crf','20',
                    '-pix_fmt','yuv420p', str(out)], check=True, capture_output=True)

def merge_audio(paths, out):
    lf = W / 'a_concat.txt'
    lf.write_text('\n'.join(f"file '{p}'" for p in paths))
    subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0',
                    '-i', str(lf), '-c:a','libmp3lame','-b:a','192k', str(out)], check=True)

def concat_clips(clips, audio, out):
    lf = W / 'v_concat.txt'
    lf.write_text('\n'.join(f"file '{p}'" for p in clips))
    inter = W / 'concat.mp4'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0',
                    '-i', str(lf),'-c:v','libx264','-preset','fast','-crf','20',
                    '-pix_fmt','yuv420p', str(inter)], check=True)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i', str(inter),'-i', audio,
                    '-c:v','copy','-c:a','aac','-b:a','192k','-shortest', str(out)], check=True)

def run():
    print(f"[1/7] Fetch pipeline #{PID}")
    ps = sb('GET', f"content_pipeline?id=eq.{PID}&select=*")
    if not ps: print(f"❌ #{PID} not found"); return 1
    p = ps[0]
    script = p['script']; title = p['title']; plat = p['target_platform']
    short = any(s in plat.lower() for s in ['short','reel','tiktok','pin'])
    dur = 60 if short else 480
    print(f"  '{title}' | {plat} | {len(script)} chars")

    print(f"[2/7] Segment script (DeepSeek V4 Pro)")
    scenes, mood = segment_scenes(script, plat, dur)
    print(f"  {len(scenes)} scenes | mood={mood}")

    print(f"[3/7] Generate audio (Edge TTS) per scene")
    auds = []; durs = []
    for i, s in enumerate(scenes):
        ap = W / f"a_{i:03d}.mp3"
        d = tts(s['narration'], s.get('emotion','calmo'), str(ap))
        auds.append(str(ap)); durs.append(d)
        s['duration_s'] = max(d + 0.3, 2.0)
        print(f"  [{i+1}/{len(scenes)}] {d:.1f}s {s.get('emotion')} - {s['narration'][:50]}")

    print(f"[4/7] Generate images (Flux Schnell Nvidia)")
    iw, ih = (768, 1344) if short else (1344, 768)
    ow, oh = (1080, 1920) if short else (1920, 1080)
    imgs = []
    for i, s in enumerate(scenes):
        ip = W / f"i_{i:03d}.jpg"
        ok = flux(s['image_prompt'], ip, w=iw, h=ih)
        if ok:
            imgs.append(str(ip)); print(f"  [{i+1}/{len(scenes)}] ok")
        elif imgs:
            shutil.copy(imgs[-1], ip); imgs.append(str(ip))
            print(f"  [{i+1}/{len(scenes)}] reused prev")
        else:
            print(f"  [{i+1}/{len(scenes)}] FAILED no fallback"); return 2

    print(f"[5/7] Compose Ken Burns clips")
    clips = []
    for i, s in enumerate(scenes):
        cp = W / f"c_{i:03d}.mp4"
        kb_clip(imgs[i], s['duration_s'], cp, motion=s.get('ken_burns','static'), tw=ow, th=oh)
        clips.append(str(cp))
    print(f"  {len(clips)} clips")

    print(f"[6/7] Merge + final encode")
    fa = W / 'narration.mp3'
    merge_audio(auds, str(fa))
    final = W / f"pipeline_{PID}_v2.mp4"
    concat_clips(clips, str(fa), str(final))
    sz = final.stat().st_size
    print(f"  MP4: {sz/1024/1024:.1f}MB")

    print(f"[7/7] Upload to Supabase Storage")
    sp = f"v2/pipeline_{PID}_{int(time.time())}.mp4"
    url = upload_storage('videos', sp, str(final), 'video/mp4')
    if not url: print("❌ upload failed"); return 3

    nm = (p.get('metadata') or {}) | {'video_gen_v2': {
        'engine': 'flux_schnell_nvidia + edge_tts + ffmpeg',
        'scenes': len(scenes), 'duration_s': sum(durs),
        'music_mood': mood, 'visual_style': 'psych2go_clone',
        'no_text_on_screen': True,
        'rendered_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}}
    sb('PATCH', f"content_pipeline?id=eq.{PID}", {'mp4_url': url, 'metadata': nm})
    print(f"\n✅ DONE in {time.time()-T0:.0f}s")
    print(f"📺 {url}")
    return 0

if __name__ == '__main__':
    try: sys.exit(run())
    except Exception as e:
        traceback.print_exc(); sys.exit(99)
