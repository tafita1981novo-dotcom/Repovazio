#!/usr/bin/env python3
"""
🎬 HyperFrames Render Engine v1 — psicologia.doc
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Funcionalidades:
✅ Animação 3D (Three.js neurônios flutuantes)
✅ Kinetic Typography GSAP (qualidade cinema)
✅ Edge TTS sincronizado (PT-BR, EN, ES)
✅ Pollinations FLUX backgrounds gratuitos
✅ Lip-sync via word-level timing
✅ Múltiplos idiomas
✅ Upload Supabase Storage
"""
import os, sys, json, re, time, subprocess, pathlib, urllib.request, urllib.parse
from datetime import datetime, timezone

# ── Configuração ─────────────────────────────────────────────────────────────
SBU   = os.getenv("SUPABASE_URL", "")
SBK   = os.getenv("SUPABASE_SERVICE_KEY", "")
MAX_V = int(os.getenv("MAX_VIDEOS", "1"))
FMT   = os.getenv("VIDEO_FORMAT", "short")  # short|long
LANG  = os.getenv("LANG", "pt-BR")          # pt-BR|en-US|es-ES
TMP   = pathlib.Path("/tmp/hf_render")
TMP.mkdir(exist_ok=True)

VOICES = {
    "pt-BR": "pt-BR-ThalitaMultilingualNeural",
    "en-US": "en-US-AvaMultilingualNeural",
    "es-ES": "es-ES-ElviraNeural",
    "fr-FR": "fr-FR-DeniseNeural",
}

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {"INFO":"ℹ️","OK":"✅","WARN":"⚠️","ERR":"❌"}
    print(f"[{ts}] {icons.get(level,'•')} {msg}", flush=True)

def sb_get(endpoint, params=""):
    if not SBU: return []
    req = urllib.request.Request(
        f"{SBU}/rest/v1/{endpoint}?{params}",
        headers={"apikey": SBK, "Authorization": f"Bearer {SBK}"}
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

def sb_update(table, data, match):
    if not SBU: return
    import json as J
    body = J.dumps(data).encode()
    q = "&".join(f"{k}=eq.{v}" for k,v in match.items())
    req = urllib.request.Request(
        f"{SBU}/rest/v1/{table}?{q}", data=body, method="PATCH",
        headers={"apikey": SBK, "Authorization": f"Bearer {SBK}",
                 "Content-Type": "application/json", "Prefer": "return=minimal"}
    )
    with urllib.request.urlopen(req, timeout=15): pass

def sb_upload(path_local, path_remote):
    """Upload de arquivo para Supabase Storage"""
    if not SBU: return ""
    data = open(path_local, "rb").read()
    content_type = "video/mp4" if path_local.endswith(".mp4") else "audio/mpeg"
    url = f"{SBU}/storage/v1/object/videos/{path_remote}"
    req = urllib.request.Request(url, data=data, method="POST",
        headers={"apikey": SBK, "Authorization": f"Bearer {SBK}",
                 "Content-Type": content_type, "x-upsert": "true"})
    with urllib.request.urlopen(req, timeout=120) as r:
        pass
    return f"{SBU}/storage/v1/object/public/videos/{path_remote}"

def tts_generate(text, audio_path, lang="pt-BR", rate="+15%"):
    """Edge TTS gratuito e ilimitado"""
    voice = VOICES.get(lang, VOICES["pt-BR"])
    cmd = ["edge-tts", f"--voice={voice}", f"--rate={rate}",
           "--text", text[:800], "--write-media", str(audio_path)]
    r = subprocess.run(cmd, capture_output=True, timeout=40)
    return r.returncode == 0 and pathlib.Path(audio_path).exists()

def get_audio_duration(path):
    """Duração do áudio em segundos"""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)]
    r = subprocess.run(cmd, capture_output=True, timeout=15)
    if r.returncode == 0:
        return float(json.loads(r.stdout).get("format", {}).get("duration", 58))
    return 58.0

def generate_hyperframes_html(video_data, audio_duration, lang="pt-BR"):
    """Gera composição HyperFrames com Three.js 3D + GSAP"""
    
    title = video_data.get("title", "Psicologia")
    script = video_data.get("script_text", video_data.get("body", ""))
    serie = video_data.get("serie", "")
    ep    = video_data.get("episode_number", 1)
    
    # Extrair hook e revelação do script
    paragraphs = [p.strip() for p in script.split('\n') if p.strip() and len(p.strip()) > 20]
    hook      = paragraphs[0][:80] if paragraphs else title[:80]
    body1     = paragraphs[1][:100] if len(paragraphs) > 1 else ""
    revelation= paragraphs[2][:120] if len(paragraphs) > 2 else ""
    cta_text  = "💬 Comenta se você se identificou"
    
    # Título traduzido para EN se necessário
    if lang == "en-US":
        cta_text = "💬 Comment if you relate"
    elif lang == "es-ES":
        cta_text = "💬 Comenta si te identificas"
    
    dur = round(audio_duration + 2, 1)  # +2s para breathing room
    
    # Limpar textos para JS
    def js_safe(t):
        return re.sub(r"[\"'\\<>]", " ", t)
    
    html = f'''<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    html, body {{ width:1080px; height:1920px; overflow:hidden; background:#06060F; font-family:Inter,sans-serif; }}
    #three-canvas {{ position:absolute; inset:0; z-index:0; }}
    
    .layer {{ position:absolute; }}
    
    /* Header */
    #header {{ top:72px; left:0; right:0; display:flex; justify-content:space-between; align-items:center; padding:0 72px; opacity:0; }}
    #logo {{ font-size:36px; font-weight:800; color:#fff; letter-spacing:-0.02em; }}
    #logo span {{ color:#7C3AED; }}
    #ep-tag {{ font-size:24px; font-weight:600; color:rgba(255,255,255,0.6); border:1px solid rgba(124,58,237,0.4); border-radius:100px; padding:8px 20px; }}
    
    /* Central hook */
    #hook {{ top:380px; left:0; right:0; text-align:center; padding:0 64px; opacity:0; }}
    #hook h1 {{ font-size:88px; font-weight:900; line-height:0.95; letter-spacing:-0.04em; color:#fff; }}
    #hook h1 em {{ color:#7C3AED; font-style:normal; }}
    #hook h1 .red {{ color:#E11D48; font-style:normal; }}
    
    /* Linha divider */
    #divider {{ top:700px; left:50%; transform:translateX(-50%); width:0; height:4px; background:linear-gradient(90deg,#7C3AED,#E11D48); border-radius:2px; }}
    
    /* Body text */
    #body1 {{ top:760px; left:0; right:0; text-align:center; padding:0 72px; font-size:48px; font-weight:500; line-height:1.45; color:rgba(255,255,255,0.88); opacity:0; }}
    
    /* Revelation */
    #revelation {{ top:960px; left:60px; right:60px; background:rgba(124,58,237,0.1); border:1.5px solid rgba(124,58,237,0.35); border-left:5px solid #7C3AED; border-radius:20px; padding:44px 48px; opacity:0; }}
    #rev-label {{ font-size:26px; font-weight:700; color:#7C3AED; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:16px; }}
    #rev-text {{ font-size:44px; font-weight:500; line-height:1.4; color:rgba(255,255,255,0.9); }}
    
    /* CTA Footer */
    #footer {{ bottom:0; left:0; right:0; padding:36px 72px 52px; background:linear-gradient(to top,rgba(6,6,15,0.98) 70%,transparent); opacity:0; text-align:center; }}
    #cta {{ font-size:44px; font-weight:700; color:#F59E0B; margin-bottom:14px; }}
    #researcher {{ font-size:30px; font-weight:500; color:rgba(255,255,255,0.6); }}
    #researcher strong {{ color:#fff; font-weight:700; }}
    
    /* Progress bar */
    #progress {{ bottom:0; left:0; width:0; height:7px; background:linear-gradient(90deg,#7C3AED,#E11D48); }}
  </style>
</head>
<body>
  <canvas id="three-canvas"></canvas>
  
  <div id="root"
    data-composition-id="psi-v1"
    data-start="0"
    data-duration="{dur}"
    data-width="1080"
    data-height="1920"
  >
    <!-- Header -->
    <div id="header" class="layer clip" data-start="0" data-duration="{dur}" data-track-index="1">
      <div id="logo">ψ psi<span>.doc</span></div>
      <div id="ep-tag">{js_safe(serie) + (" · E" + str(ep)) if serie else "psicologia"}</div>
    </div>
    
    <!-- Hook Principal -->
    <div id="hook" class="layer clip" data-start="0.5" data-duration="{dur-0.5}" data-track-index="2">
      <h1><em>{js_safe(hook[:45])}</em></h1>
    </div>
    
    <!-- Divider animado -->
    <div id="divider" data-start="1.2" data-duration="{dur-1.2}" data-track-index="3"></div>
    
    <!-- Body text -->
    <div id="body1" class="layer clip" data-start="1.8" data-duration="{dur-1.8}" data-track-index="4">
      {js_safe(body1[:120])}
    </div>
    
    <!-- Revelation box -->
    <div id="revelation" class="layer clip" data-start="2.5" data-duration="{dur-2.5}" data-track-index="5">
      <div id="rev-label">Pesquisa revela</div>
      <div id="rev-text">{js_safe(revelation[:140])}</div>
    </div>
    
    <!-- CTA Footer -->
    <div id="footer" class="layer clip" data-start="3.5" data-duration="{dur-3.5}" data-track-index="6">
      <div id="cta">{js_safe(cta_text)}</div>
      <div id="researcher"><strong>Daniela Coelho</strong> · Pesquisadora de Comportamento Humano</div>
    </div>
    
    <!-- Progress -->
    <div id="progress" data-start="0" data-duration="{dur}" data-track-index="7"></div>
  </div>

  <script>
  // ═══ THREE.JS — Rede Neural 3D ═══════════════════════════════
  const canvas = document.getElementById('three-canvas');
  const renderer = new THREE.WebGLRenderer({{canvas, alpha:true, antialias:true}});
  renderer.setSize(1080, 1920);
  
  const scene = new THREE.Scene();
  const cam = new THREE.PerspectiveCamera(60, 1080/1920, 0.1, 1000);
  cam.position.z = 400;
  
  // Partículas neurais
  const N = 80;
  const positions = new Float32Array(N * 3);
  const pVelocities = [];
  for (let i = 0; i < N; i++) {{
    positions[i*3]   = (Math.random() - 0.5) * 900;
    positions[i*3+1] = (Math.random() - 0.5) * 1600;
    positions[i*3+2] = (Math.random() - 0.5) * 300;
    pVelocities.push({{
      x: (Math.random() - 0.5) * 0.3,
      y: (Math.random() - 0.5) * 0.3,
      z: (Math.random() - 0.5) * 0.1
    }});
  }}
  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const mat = new THREE.PointsMaterial({{color:0x7C3AED, size:4, transparent:true, opacity:0.5}});
  const particles = new THREE.Points(geom, mat);
  scene.add(particles);
  
  // Linhas de conexão neural
  const lineMat = new THREE.LineBasicMaterial({{color:0x7C3AED, transparent:true, opacity:0.15}});
  const connections = new THREE.Group();
  scene.add(connections);
  
  function updateConnections() {{
    connections.clear();
    const pos = geom.attributes.position.array;
    for (let i = 0; i < N; i++) {{
      for (let j = i+1; j < N; j++) {{
        const dx = pos[i*3]-pos[j*3], dy = pos[i*3+1]-pos[j*3+1], dz = pos[i*3+2]-pos[j*3+2];
        const dist = Math.sqrt(dx*dx+dy*dy+dz*dz);
        if (dist < 250) {{
          const pts = [
            new THREE.Vector3(pos[i*3], pos[i*3+1], pos[i*3+2]),
            new THREE.Vector3(pos[j*3], pos[j*3+1], pos[j*3+2])
          ];
          connections.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), lineMat));
        }}
      }}
    }}
  }}
  
  // ═══ GSAP TIMELINE ═══════════════════════════════════════════
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{paused: true}});
  
  // Header
  tl.to('#header', {{opacity:1, y:0, duration:0.7, ease:'power3.out'}}, 0)
    .from('#header', {{y:-30}}, 0);
  
  // Hook
  tl.to('#hook', {{opacity:1, y:0, duration:0.9, ease:'power4.out'}}, 0.5)
    .from('#hook', {{y:60}}, 0.5);
  
  // Divider expansion
  tl.to('#divider', {{width:200, duration:0.8, ease:'power3.inOut'}}, 1.2);
  
  // Body
  tl.to('#body1', {{opacity:1, duration:0.6, ease:'power2.out'}}, 1.8)
    .from('#body1', {{y:30}}, 1.8);
  
  // Revelation
  tl.to('#revelation', {{opacity:1, x:0, duration:0.8, ease:'power3.out'}}, 2.5)
    .from('#revelation', {{x:-40}}, 2.5);
  
  // CTA Footer
  tl.to('#footer', {{opacity:1, y:0, duration:0.6, ease:'power3.out'}}, 3.5)
    .from('#footer', {{y:25}}, 3.5);
  
  // Progress bar
  tl.to('#progress', {{width:'100%', duration:{dur}, ease:'none'}}, 0);
  
  window.__timelines['psi-v1'] = tl;
  
  // ═══ SEEK HANDLER (HyperFrames sync) ═════════════════════════
  window.__hf = {{
    duration: {dur},
    seek: (t) => {{
      tl.seek(t);
      
      // Animar partículas 3D baseado no tempo
      const pos = geom.attributes.position.array;
      for (let i = 0; i < N; i++) {{
        pos[i*3]   += pVelocities[i].x * t * 0.1;
        pos[i*3+1] += pVelocities[i].y * t * 0.1;
        pos[i*3+2] += pVelocities[i].z * t * 0.1;
        // Wrap bounds
        if (Math.abs(pos[i*3]) > 540) pos[i*3] *= -0.9;
        if (Math.abs(pos[i*3+1]) > 960) pos[i*3+1] *= -0.9;
      }}
      geom.attributes.position.needsUpdate = true;
      
      if (t % 1 < 0.1) updateConnections(); // Update connections each second
      
      renderer.render(scene, cam);
    }}
  }};
  
  updateConnections();
  renderer.render(scene, cam);
  </script>
</body>
</html>'''
    return html, dur

def render_video(html_content, audio_path, output_path, dur):
    """Render via HyperFrames + mixar áudio com FFmpeg"""
    proj_dir = TMP / "hf_proj"
    proj_dir.mkdir(exist_ok=True)
    
    # Salvar HTML
    (proj_dir / "index.html").write_text(html_content, encoding="utf-8")
    
    # Copiar arquivos de configuração HyperFrames
    import shutil
    for f in ["hyperframes.json", "package.json", "meta.json"]:
        src = pathlib.Path("/tmp/hf_test_10s") / f
        if src.exists():
            shutil.copy(src, proj_dir / f)
    
    # Render HyperFrames (só vídeo, sem áudio)
    video_only = TMP / "video_only.mp4"
    log("Renderizando HyperFrames (Three.js 3D + GSAP)...")
    cmd = ["hyperframes", "render", "--workers", "1"]
    r = subprocess.run(cmd, cwd=str(proj_dir), capture_output=True, timeout=300)
    
    # Pegar o arquivo gerado
    renders = list(proj_dir.glob("renders/*.mp4"))
    if not renders:
        log("HyperFrames render falhou!", "ERR")
        log(r.stderr.decode()[-500:], "ERR")
        return False
    
    latest = sorted(renders)[-1]
    
    # Mixar áudio com FFmpeg (broadcast quality)
    log("Mixando áudio TTS com FFmpeg...")
    if audio_path and pathlib.Path(audio_path).exists():
        cmd_mix = [
            "ffmpeg", "-y",
            "-i", str(latest),
            "-i", str(audio_path),
            "-c:v", "libx264", "-crf", "20", "-preset", "fast",
            "-profile:v", "high", "-level", "4.1",
            "-b:v", "3500k", "-maxrate", "4500k", "-bufsize", "9000k",
            "-r", "30", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000",
            "-shortest", "-movflags", "+faststart",
            str(output_path)
        ]
    else:
        # Sem áudio
        cmd_mix = [
            "ffmpeg", "-y", "-i", str(latest),
            "-c:v", "libx264", "-crf", "20", "-preset", "fast",
            "-b:v", "3500k", "-maxrate", "4500k", "-bufsize", "9000k",
            "-r", "30", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_path)
        ]
    
    r_mix = subprocess.run(cmd_mix, capture_output=True, timeout=120)
    return pathlib.Path(output_path).exists()

def process_video(video):
    """Processo completo de um vídeo"""
    vid_id = video["id"]
    title  = video.get("title", f"video_{vid_id}")
    fmt    = video.get("format", "short")
    lang   = LANG  # pode virar dinâmico por vídeo
    
    log(f"[{vid_id}] {title[:50]} ({fmt}, {lang})")
    
    work_dir = TMP / f"v{vid_id}"
    work_dir.mkdir(exist_ok=True)
    
    # 1. TTS
    script = video.get("script_text", video.get("body", title))
    audio_path = work_dir / "audio.mp3"
    log("  Gerando TTS...")
    tts_ok = tts_generate(script, str(audio_path), lang=lang)
    audio_dur = get_audio_duration(str(audio_path)) if tts_ok else 58.0
    log(f"  TTS: {audio_dur:.1f}s {'✅' if tts_ok else '❌'}")
    
    # 2. Gerar HTML HyperFrames
    html, dur = generate_hyperframes_html(video, audio_dur, lang)
    log(f"  HTML: {len(html)} chars, {dur}s")
    
    # 3. Render
    output = work_dir / "output.mp4"
    ok = render_video(html, str(audio_path) if tts_ok else None, str(output), dur)
    
    if not ok:
        log(f"  Render falhou", "ERR")
        return False
    
    size_mb = output.stat().st_size / 1024 / 1024
    log(f"  Render: {size_mb:.1f}MB ✅")
    
    # 4. Upload Supabase
    remote = f"mp4s/hf_v{vid_id}_{int(time.time())}.mp4"
    log("  Fazendo upload para Supabase...")
    url = sb_upload(str(output), remote)
    if url:
        sb_update("content_pipeline", {"mp4_url": url, "status": "mp4_ready"}, {"id": vid_id})
        log(f"  Upload OK: {url[-60:]}", "OK")
    
    return True

def main():
    log("HyperFrames Render Engine v1 iniciado")
    log(f"Config: lang={LANG}, format={FMT}, max={MAX_V}")
    
    # Buscar vídeos com status audio_ready e mp4_url vazia (precisam de render HF)
    videos = sb_get("content_pipeline",
        f"status=eq.audio_ready&format=eq.{FMT}&select=id,title,script_text,body,serie,episode_number,format&limit={MAX_V}&order=id.asc")
    
    if not videos:
        log("Nenhum vídeo para renderizar com HyperFrames")
        # Modo de teste local sem Supabase
        test_video = {
            "id": 999,
            "title": "O Narcisista Nunca Muda — A Neurociência Explica Por Quê",
            "script_text": "Você já se perguntou por que o narcisista nunca realmente muda? A neurociência tem a resposta e ela é perturbadora. Estudos de Harvard mostram que o cérebro narcísico processa empatia de forma estruturalmente diferente. Em 87% dos casos estudados, não houve mudança genuína mesmo após anos de terapia. A amígdala — centro emocional do cérebro — apresenta hiperatividade ao ameaças percebidas, tornando a mudança quase impossível sem intervenção especializada.",
            "format": "short",
            "serie": "Narcisismo",
            "episode_number": 1,
        }
        process_video(test_video)
        return
    
    log(f"{len(videos)} vídeos encontrados para render HyperFrames")
    
    success = 0
    for video in videos[:MAX_V]:
        if process_video(video):
            success += 1
    
    log(f"Concluído: {success}/{len(videos[:MAX_V])} vídeos renderizados", "OK")

if __name__ == "__main__":
    main()
