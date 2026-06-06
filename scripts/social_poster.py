#!/usr/bin/env python3
"""
social_poster.py — Sistema automático de postagem Instagram + TikTok
Posta 3x/dia vídeos de white/brown noise black screen
Gerado por: psicologia.doc pipeline
"""
import os, json, pathlib, subprocess, struct, wave, random, shutil
import urllib.request, urllib.parse, requests
from datetime import datetime, timezone

# ─── CREDENCIAIS (GitHub Secrets) ──────────────────────────────────
IG_ACCESS_TOKEN    = os.environ.get("IG_ACCESS_TOKEN", "")
IG_BUSINESS_ID     = os.environ.get("IG_BUSINESS_ID", "")
TIKTOK_CLIENT_KEY  = os.environ.get("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SEC  = os.environ.get("TIKTOK_CLIENT_SECRET", "")
TIKTOK_ACCESS_TOK  = os.environ.get("TIKTOK_ACCESS_TOKEN", "")

TMP = pathlib.Path("/tmp")

# ─── CONTEÚDO ROTATIVO — 18 IDIOMAS ────────────────────────────────
# Formato: (caption, hashtags, language)
POSTS = [
    ("🖤 Black Screen + White Noise for sleep, study & focus. Runs 24/7 live on YouTube → link in bio",
     "#whitenoise #blackscreen #sleepsounds #study #focus #sleep #brownnoise #whitenoisesleep",
     "en"),
    ("🖤 Tela Preta + Ruído Branco para dormir, estudar e focar. Live 24/7 no YouTube → link na bio",
     "#telapreta #ruidobranco #dormir #estudar #focar #ruidomarrom #somparadormir #sonosbinaurais",
     "pt"),
    ("🖤 Pantalla Negra + Ruido Blanco para dormir, estudiar y concentrarse. Live 24/7 en YouTube → enlace en bio",
     "#pantallanegra #ruidoblanco #dormir #estudiar #concentrarse #ruidomarron #musicaparadormir",
     "es"),
    ("🖤 Schwarzer Bildschirm + Weißes Rauschen für Schlaf, Lernen & Fokus. 24/7 Live auf YouTube → Link in Bio",
     "#weißesrauschen #schwarzerbildschirm #schlafen #lernen #fokus #brauesrauschen #schlafmusik",
     "de"),
    ("🖤 Écran Noir + Bruit Blanc pour dormir, étudier et se concentrer. Live 24/7 sur YouTube → lien en bio",
     "#bruitblanc #ecrannoir #dormir #etudier #concentrer #bruitbrun #musiquepourseconcentrer",
     "fr"),
    ("🖤 Black Screen White Noise for babies & deep sleep 👶 24/7 Live on YouTube → link in bio",
     "#whitenoiseforbaby #babysleep #blackscreen #whitenoise #deepsleeP #brownnoise #lullaby",
     "en"),
    ("🖤 Brown Noise Black Screen for ADHD Focus 🧠 24/7 Live on YouTube → link in bio",
     "#brownnoise #adhd #focus #blackscreen #whitenoise #studywithme #deepfocus #adhdtiktok",
     "en"),
    ("🖤 Ruído Marrom Tela Preta para TDAH e Foco 🧠 Live 24/7 no YouTube → link na bio",
     "#ruidomarrom #tdah #foco #telapreta #ruidobranco #estudar #concentracao #tdahtiktok",
     "pt"),
    ("🖤 白噪音黑屏 — 助眠、学习、专注。YouTube 24/7 直播 → 点击简介链接",
     "#白噪音 #黑屏 #助眠 #学习 #专注 #棕噪音 #睡眠音乐 #冥想音乐",
     "zh"),
    ("🖤 백색소음 검은 화면 — 수면, 공부, 집중을 위해. YouTube 24/7 라이브 → 바이오 링크",
     "#백색소음 #검은화면 #수면 #공부 #집중 #갈색소음 #수면음악 #명상",
     "ko"),
]

# ─── GERAR VÍDEO 9:16 (Reels / TikTok) ────────────────────────────
def ffm():
    sf = shutil.which("ffmpeg")
    if sf: return sf
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except: return "ffmpeg"

def gerar_noise_wav(duracao=30):
    """White+Brown noise mix — 30s para Reels/TikTok"""
    SR = 44100
    s = SR * duracao
    out = bytearray()
    bL = bR = 0.0
    for i in range(s):
        wL = random.random() * 2 - 1
        wR = random.random() * 2 - 1
        bL = max(-1.0, min(1.0, bL * 0.999 + wL * 0.02))
        bR = max(-1.0, min(1.0, bR * 0.999 + wR * 0.02))
        mL = bL * 0.65 + wL * 0.35
        mR = bR * 0.65 + wR * 0.35
        out += struct.pack("<hh", int(mL * 18000), int(mR * 18000))
    p = TMP / "social_noise.wav"
    with wave.open(str(p), "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2)
        wf.setframerate(SR); wf.writeframes(bytes(out))
    return str(p)

def gerar_video_vertical(duracao=30):
    """Cria vídeo 1080x1920 (9:16) — formato Reels/TikTok"""
    ff = ffm()
    wav = gerar_noise_wav(duracao)
    out = str(TMP / "social_video.mp4")
    
    # ψ piscando + texto "White Noise" discreto no centro
    vf = (
        "drawtext=text=ψ:x=w-30:y=h-30:fontsize=12:"
        "fontcolor=0x222222@0.08:enable='gt(mod(t\\,2)\\,1)',"
        "drawtext=text='White Noise':x=(w-text_w)/2:y=(h-text_h)/2:"
        "fontsize=20:fontcolor=0x333333@0.05"
    )
    
    cmd = [ff, "-y",
           "-i", wav,
           "-f", "lavfi", "-i", "color=black:size=1080x1920:rate=30",
           "-map", "1:v", "-map", "0:a",
           "-c:v", "libx264", "-preset", "fast", "-crf", "26",
           "-b:v", "2M", "-pix_fmt", "yuv420p",
           "-vf", vf,
           "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "44100",
           "-t", str(duracao), out]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"ffmpeg erro: {result.stderr[-300:]}")
        return None
    
    size = pathlib.Path(out).stat().st_size // 1024
    print(f"✅ Vídeo 9:16 criado: {size}KB / {duracao}s")
    return out

# ─── INSTAGRAM — CONTENT PUBLISHING API ────────────────────────────
def postar_instagram(video_path, caption):
    """
    Posta Reel no Instagram via Graph API
    Requer: IG_ACCESS_TOKEN + IG_BUSINESS_ID
    """
    if not IG_ACCESS_TOKEN or not IG_BUSINESS_ID:
        print("⚠ IG_ACCESS_TOKEN ou IG_BUSINESS_ID não configurados")
        return False
    
    # STEP 1: Upload do container do vídeo
    # O Instagram requer URL pública do vídeo — precisa hospedar primeiro
    # Usaremos o GitHub Releases como CDN temporário
    print("📤 Instagram: iniciando upload...")
    
    # Para vídeo, Instagram Graph API requer URL pública
    # Opção: subir para Supabase Storage e usar URL pública
    SUPABASE_URL = "https://tpjvalzwkqwttvmszvie.supabase.co"
    SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
    
    if SUPABASE_KEY:
        # Upload para Supabase Storage
        with open(video_path, "rb") as f:
            video_data = f.read()
        
        filename = f"social_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.mp4"
        resp = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/social-videos/{filename}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "video/mp4",
                "x-upsert": "true"
            },
            data=video_data,
            timeout=120
        )
        
        if not resp.ok:
            print(f"❌ Upload Supabase falhou: {resp.status_code}")
            return False
        
        video_url = f"{SUPABASE_URL}/storage/v1/object/public/social-videos/{filename}"
        print(f"✅ Vídeo hospedado: {video_url[:60]}...")
        
        # STEP 2: Criar container no Instagram
        container_resp = requests.post(
            f"https://graph.facebook.com/v19.0/{IG_BUSINESS_ID}/media",
            params={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": IG_ACCESS_TOKEN
            },
            timeout=30
        )
        
        if not container_resp.ok:
            print(f"❌ Criar container: {container_resp.status_code} {container_resp.text[:200]}")
            return False
        
        container_id = container_resp.json().get("id")
        print(f"✅ Container criado: {container_id}")
        
        # STEP 3: Aguardar processamento (até 3 min)
        import time
        for attempt in range(18):
            time.sleep(10)
            status_resp = requests.get(
                f"https://graph.facebook.com/v19.0/{container_id}",
                params={"fields": "status_code", "access_token": IG_ACCESS_TOKEN},
                timeout=15
            )
            status = status_resp.json().get("status_code", "")
            print(f"  Container status ({attempt+1}/18): {status}")
            if status == "FINISHED": break
            if status == "ERROR":
                print(f"❌ Erro no processamento: {status_resp.json()}")
                return False
        
        # STEP 4: Publicar
        publish_resp = requests.post(
            f"https://graph.facebook.com/v19.0/{IG_BUSINESS_ID}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": IG_ACCESS_TOKEN
            },
            timeout=30
        )
        
        if publish_resp.ok:
            post_id = publish_resp.json().get("id")
            print(f"🎉 Instagram Reel publicado! ID: {post_id}")
            return True
        else:
            print(f"❌ Publicar: {publish_resp.status_code} {publish_resp.text[:200]}")
            return False
    
    return False

# ─── TIKTOK — CONTENT POSTING API ──────────────────────────────────
def postar_tiktok(video_path, caption):
    """
    Posta vídeo no TikTok via Content Posting API
    Requer: TIKTOK_ACCESS_TOKEN
    """
    if not TIKTOK_ACCESS_TOK:
        print("⚠ TIKTOK_ACCESS_TOKEN não configurado")
        return False
    
    print("📤 TikTok: iniciando upload...")
    
    video_size = pathlib.Path(video_path).stat().st_size
    
    # STEP 1: Iniciar upload
    init_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        headers={
            "Authorization": f"Bearer {TIKTOK_ACCESS_TOK}",
            "Content-Type": "application/json; charset=UTF-8"
        },
        json={
            "post_info": {
                "title": caption[:150],
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1
            }
        },
        timeout=30
    )
    
    if not init_resp.ok:
        print(f"❌ TikTok init: {init_resp.status_code} {init_resp.text[:200]}")
        return False
    
    data = init_resp.json().get("data", {})
    publish_id = data.get("publish_id")
    upload_url = data.get("upload_url")
    
    if not upload_url:
        print(f"❌ Sem upload_url: {init_resp.json()}")
        return False
    
    print(f"✅ TikTok publish_id: {publish_id}")
    
    # STEP 2: Upload do vídeo
    with open(video_path, "rb") as f:
        video_data = f.read()
    
    upload_resp = requests.put(
        upload_url,
        headers={
            "Content-Type": "video/mp4",
            "Content-Length": str(video_size),
            "Content-Range": f"bytes 0-{video_size-1}/{video_size}"
        },
        data=video_data,
        timeout=300
    )
    
    if upload_resp.status_code in (200, 201, 204):
        print(f"🎉 TikTok vídeo publicado! publish_id: {publish_id}")
        return True
    else:
        print(f"❌ Upload TikTok: {upload_resp.status_code} {upload_resp.text[:200]}")
        return False

# ─── MAIN ───────────────────────────────────────────────────────────
def main():
    now = datetime.now(timezone.utc)
    print(f"[{now:%Y-%m-%d %H:%M}] Social Poster iniciando...")
    
    # Selecionar caption do dia
    hour = now.hour
    day = now.weekday()
    idx = (day * 24 + hour) % len(POSTS)
    caption, hashtags, lang = POSTS[idx]
    full_caption = f"{caption}\n\n{hashtags}\n\n▶ YouTube 24/7: youtube.com/channel/UCSH63tBfY6wEIdkC4u4zKdg/live"
    
    print(f"Caption ({lang}): {caption[:60]}...")
    
    # Gerar vídeo
    video = gerar_video_vertical(30)
    if not video:
        print("❌ Falha ao gerar vídeo"); return
    
    # Postar
    ig_ok = postar_instagram(video, full_caption)
    tt_ok = postar_tiktok(video, caption)
    
    print(f"\nResultado: Instagram={'✅' if ig_ok else '⚠'} | TikTok={'✅' if tt_ok else '⚠'}")
    if not ig_ok and not tt_ok:
        print("⚠ Tokens não configurados — configure IG_ACCESS_TOKEN, IG_BUSINESS_ID, TIKTOK_ACCESS_TOKEN")

if __name__ == "__main__":
    main()
