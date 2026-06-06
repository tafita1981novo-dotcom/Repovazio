#!/usr/bin/env python3
"""
create_short.py — Cria um Short de 60s para impulsionar o canal
Estratégia: Shorts com white/brown noise black screen = alimenta o algoritmo
Título rotativo a cada run: keywords de alta busca em EN/ES/PT
"""
import os, json, urllib.request, urllib.parse, subprocess, math, struct, wave, shutil, pathlib, random, time
from datetime import datetime, timezone, timedelta

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
TMP = pathlib.Path("/tmp")

TITULOS_SHORTS = [
    "Black Screen White Noise for Sleep 😴 #shorts #whitenoise #blackscreen #sleep",
    "Tela Preta Ruído Branco para Dormir 😴 #shorts #telapreta #dormir #ruidobranco",
    "Pantalla Negra Ruido Blanco para Dormir 😴 #shorts #pantallanegra #ruido #dormir",
    "Brown Noise Black Screen for ADHD Focus 🧠 #shorts #brownnoise #adhd #focus",
    "White Noise for Baby Sleep 👶 #shorts #whitenoise #babysleep #blackscreen",
    "Ruído Marrom Tela Preta para Foco TDAH 🧠 #shorts #ruidomarrom #tdah #telapreta",
    "Schwarzer Bildschirm Weißes Rauschen Schlafen 😴 #shorts #schlaf #weißesrauschen",
    "Black Screen Brown Noise 10 Hours 😴 #shorts #brownnoise #blackscreen #sleep",
    "White Noise Black Screen No Ads Study 📚 #shorts #whitenoise #study #blackscreen",
    "Tela Preta Ruído Marrom TDAH Foco 🧠 #shorts #ruidomarrom #tdah #foco",
]

DESC_SHORT = """🖤 BLACK SCREEN | White Noise & Brown Noise for Sleep, Study & Focus
Runs 24/7 LIVE: https://youtube.com/channel/UCSH63tBfY6wEIdkC4u4zKdg/live

#whitenoise #brownnoise #blackscreen #sleep #study #focus
#telapreta #ruidobranco #ruidomarrom #dormir #pantallanegra #ruido"""

def get_token():
    data=urllib.parse.urlencode({"client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
        "refresh_token":YT_REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    req=urllib.request.Request("https://oauth2.googleapis.com/token",data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read())["access_token"]

def ffm():
    sf=shutil.which("ffmpeg")
    if sf: return sf
    try: import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except: return "ffmpeg"

def gerar_noise_wav():
    """White+Brown noise mix para o Short"""
    import random
    SR,DUR=44100,62; s=SR*DUR; out=bytearray()
    bL=bR=0.0
    for i in range(s):
        wL=(random.random()*2-1); wR=(random.random()*2-1)
        bL=max(-1.0,min(1.0,bL*0.999+wL*0.02)); bR=max(-1.0,min(1.0,bR*0.999+wR*0.02))
        mL=bL*0.65+wL*0.35; mR=bR*0.65+wR*0.35
        out+=struct.pack("<hh",int(mL*18000),int(mR*18000))
    p=TMP/"short_noise.wav"
    with wave.open(str(p),"wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(bytes(out))
    return str(p)

def criar_short_video(ff, wav, titulo):
    """Cria vídeo vertical 1080x1920 (formato Short) com ψ piscando"""
    out_path = str(TMP/"short.mp4")
    # ψ bem visível no Short (12px, para passar na revisão de conteúdo original)
    psi = "drawtext=text=ψ:x=50:y=h-60:fontsize=12:fontcolor=0x222222@0.08:enable=gt(mod(t\,2)\,1)"
    cmd=[ff,"-y","-re",
         "-i",wav,
         "-f","lavfi","-i","color=black:size=1080x1920:rate=30",
         "-map","1:v","-map","0:a",
         "-c:v","libx264","-preset","fast","-crf","28",
         "-b:v","1M","-pix_fmt","yuv420p",
         "-vf",psi,
         "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
         "-t","60",
         out_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        print(f"ffmpeg erro: {result.stderr[-500:]}")
        return None
    print(f"Short criado: {pathlib.Path(out_path).stat().st_size//1024}KB")
    return out_path

def upload_short(token, video_path, titulo):
    """Upload via YouTube Data API v3 resumable upload (requests lib)"""
    import requests as req_lib
    
    # Título limpo sem emoji (YouTube API pode rejeitar)
    titulo_clean = titulo.split(" #")[0].strip()
    
    meta = {
        "snippet": {
            "title": titulo_clean[:100],
            "description": DESC_SHORT,
            "categoryId": "10",
            "tags": ["white noise","brown noise","black screen","sleep","study",
                     "tela preta","ruido blanco","pantalla negra","whitenoise","brownnoise",
                     "blackscreen","sleepsounds","whitenoiseforbabies","brownnoise10hours"]
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    video_size = pathlib.Path(video_path).stat().st_size
    
    # Iniciar upload resumable
    init_resp = req_lib.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(video_size)
        },
        json=meta,
        timeout=30
    )
    
    if init_resp.status_code not in (200, 201):
        print(f"Erro iniciar upload: {init_resp.status_code} {init_resp.text[:500]}")
        return None
    
    upload_url = init_resp.headers.get("Location","")
    if not upload_url:
        print("Sem upload URL"); return None
    
    print(f"Upload URL obtida: {upload_url[:60]}...")
    
    # Enviar vídeo
    with open(video_path,"rb") as f: video_data=f.read()
    
    upload_resp = req_lib.put(
        upload_url,
        headers={"Content-Type": "video/mp4", "Content-Length": str(video_size)},
        data=video_data,
        timeout=300
    )
    
    if upload_resp.status_code not in (200, 201):
        print(f"Erro enviar vídeo: {upload_resp.status_code} {upload_resp.text[:300]}")
        return None
    
    res = upload_resp.json()
    vid_id = res.get("id","")
    print(f"✅ Short publicado: https://www.youtube.com/shorts/{vid_id}")
    return vid_id

def main():
    print(f"[{datetime.now(timezone.utc):%H:%M}] Criando Short para impulsionar canal...")
    ff=ffm(); print(f"FFmpeg: {ff}")
    
    # Selecionar título pelo dia da semana (rotação)
    day_of_week = datetime.now(timezone.utc).weekday()
    hour = datetime.now(timezone.utc).hour
    idx = (day_of_week * 24 + hour) % len(TITULOS_SHORTS)
    titulo = TITULOS_SHORTS[idx]
    print(f"Título: {titulo}")
    
    wav = gerar_noise_wav()
    video_path = criar_short_video(ff, wav, titulo)
    if not video_path:
        print("Falha ao criar vídeo"); return
    
    token = get_token()
    vid_id = upload_short(token, video_path, titulo)
    print(f"Short {idx+1}/{len(TITULOS_SHORTS)} publicado ✅")

if __name__=="__main__": main()
