#!/usr/bin/env python3
"""
multi_platform_distributor.py
Distribui o mesmo vídeo em TikTok, Instagram Reels, YouTube Shorts, Pinterest.
Corta o vídeo para os formatos certos automaticamente via FFmpeg.
"""
import os, subprocess, pathlib, requests, time

SB_URL = os.getenv("SUPABASE_URL","")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
SBH = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json"}

def cortar_para_short(mp4_entrada, out_dir, duracao=58):
    """Converte vídeo para formato Short/Reel/TikTok: 9:16, 1080x1920"""
    out_dir = pathlib.Path(out_dir); out_dir.mkdir(exist_ok=True)
    basename = pathlib.Path(mp4_entrada).stem
    
    # Formato vertical 9:16 (TikTok / Reels / Shorts)
    vertical = out_dir / f"{basename}_vertical.mp4"
    subprocess.run([
        "ffmpeg","-y","-i",mp4_entrada,
        "-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-t",str(duracao),
        "-c:v","libx264","-preset","fast","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k","-ar","44100",
        str(vertical)
    ], capture_output=True, timeout=120)
    
    # Formato quadrado 1:1 (Instagram feed)
    quadrado = out_dir / f"{basename}_square.mp4"
    subprocess.run([
        "ffmpeg","-y","-i",mp4_entrada,
        "-vf","scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080",
        "-t",str(duracao),
        "-c:v","libx264","-preset","fast","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k",
        str(quadrado)
    ], capture_output=True, timeout=120)
    
    # Thumbnail extraída (frame 5s)
    thumb = out_dir / f"{basename}_thumb.jpg"
    subprocess.run([
        "ffmpeg","-y","-i",mp4_entrada,
        "-ss","5","-frames:v","1",
        "-vf","scale=1280:720",
        str(thumb)
    ], capture_output=True, timeout=30)
    
    resultados = {}
    if vertical.exists(): resultados["vertical"] = str(vertical)
    if quadrado.exists(): resultados["square"] = str(quadrado)
    if thumb.exists(): resultados["thumbnail"] = str(thumb)
    return resultados

def gerar_caption_viral(titulo, idioma="EN"):
    """Gera caption otimizada para cada plataforma"""
    captions = {
        "tiktok": f"{titulo}\n\n#psychology #mentalhealth #healing #narcissism #anxiousattachment",
        "instagram": f"{titulo}\n\n📚 Psychology based on peer-reviewed research\n🧠 Save for later\n👇 Share with someone who needs this\n\n#psychology #mentalhealth #narcissism #healing #528hz",
        "youtube_short": titulo,
    }
    return captions

PLATAFORMAS_HASHTAGS = {
    "EN": "#psychology #mentalhealth #narcissism #anxiousattachment #528hz #healing #trauma #gaslighting",
    "PT": "#psicologia #saudemental #narcisismo #apegoansioso #528hz #cura #trauma #gaslighting",
    "ES": "#psicología #saludmental #narcisismo #apegoansioso #528hz #sanacion #trauma #gaslighting",
    "DE": "#psychologie #mentalhealth #narzissmus #angst #528hz #heilung #trauma #gaslighting",
    "FR": "#psychologie #santemental #narcissisme #anxiete #528hz #guerison #trauma #gaslighting",
    "JA": "#心理学 #メンタルヘルス #ナルシシズム #不安 #528hz #癒し #トラウマ",
    "KO": "#심리학 #멘탈헬스 #나르시시즘 #불안 #528hz #치유 #트라우마",
}

def run():
    print("=== MULTI-PLATFORM DISTRIBUTOR ===")
    # Buscar vídeos prontos
    r = requests.get(f"{SB_URL}/rest/v1/en_channel_queue?status=eq.mp4_ready&limit=3",
        headers=SBH, timeout=10)
    videos = r.json() if r.status_code == 200 else []
    print(f"Vídeos para distribuir: {len(videos)}")
    for v in videos:
        mp4 = v.get("script_en","")
        if not pathlib.Path(mp4).exists(): continue
        print(f"  Cortando: {v['titulo_en'][:45]}...")
        formatos = cortar_para_short(mp4, f"/tmp/dist_{v['id']}")
        captions = gerar_caption_viral(v["titulo_en"])
        print(f"  Formatos: {list(formatos.keys())}")
        print(f"  Caption TikTok: {captions['tiktok'][:80]}")

if __name__ == "__main__":
    run()
