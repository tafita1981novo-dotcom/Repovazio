#!/usr/bin/env python3
"""🔴 Live Stream Viral v2 — 24/7 com conteúdo dinâmico e hooks virais"""
import os, json, subprocess, time, random, urllib.request
from datetime import datetime

SBU = os.getenv("SUPABASE_URL",""); SBK = os.getenv("SUPABASE_SERVICE_KEY","")
STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY","")
DURATION_H = int(os.getenv("DURATION_HOURS","5"))
GROQ = os.getenv("GROQ_API_KEY","")

RTMP_URL = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"

HOOKS_VIRAIS = [
    "Você sabia que o cérebro narcísico é neurologicamente diferente?",
    "Harvard descobriu por que você sempre volta para quem te machuca",
    "A ansiedade não é fraqueza — é o cérebro tentando te proteger",
    "O trauma fica armazenado no corpo. Van der Kolk explica como",
    "Você se sabota porque o sucesso ativa o medo de abandono",
    "O amor bomba é calculado. A neurociência prova",
    "Burnout não é cansaço — é colapso neurológico completo",
    "Por que você sempre cede no relacionamento? Apego ansioso",
]

def get_live_content():
    """Busca conteúdo do Supabase para a live"""
    try:
        req = urllib.request.Request(f"{SBU}/rest/v1/live_content_blocks?status=eq.ready&limit=20",
            headers={"apikey":SBK,"Authorization":f"Bearer {SBK}"})
        with urllib.request.urlopen(req,timeout=10) as r:
            return json.loads(r.read())
    except:
        return []

def generate_live_frame(hook, timestamp):
    """Gera frame da live com texto dinâmico usando FFmpeg"""
    text = hook.replace("'","\\'").replace(":","\\:")[:60]
    ts = datetime.now().strftime("%H:%M:%S")
    return [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x06060F:size=1920x1080:rate=30",
        "-f", "lavfi",
        "-i", "anullsrc=r=48000:cl=stereo",
        "-vf", f"drawtext=text='ψ psicologia.doc':fontcolor=0x7C3AED:fontsize=60:x=(w-text_w)/2:y=200,"
               f"drawtext=text='{text}':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=500:enable='between(t,0,5)',"
               f"drawtext=text='AO VIVO | {ts}':fontcolor=0xE11D48:fontsize=30:x=50:y=50",
        "-t", "30",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-b:v", "4500k", "-maxrate", "4500k", "-bufsize", "9000k",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "48000",
        "-f", "flv", RTMP_URL
    ]

def run_live():
    if not STREAM_KEY:
        print("❌ YOUTUBE_STREAM_KEY não configurada")
        print("   Instruções: YouTube Studio → Ir ao vivo → Chave de stream")
        return False
    
    print(f"🔴 Iniciando live stream — {DURATION_H}h — {datetime.now():%Y-%m-%d %H:%M}")
    
    end_time = time.time() + (DURATION_H * 3600)
    hook_idx = 0
    
    while time.time() < end_time:
        hook = HOOKS_VIRAIS[hook_idx % len(HOOKS_VIRAIS)]
        cmd = generate_live_frame(hook, time.time())
        
        print(f"  🎙 {hook[:50]}...")
        r = subprocess.run(cmd, capture_output=True, timeout=40)
        
        if r.returncode != 0:
            print(f"  ⚠️ Erro FFmpeg: {r.stderr.decode()[-200:]}")
            time.sleep(5)
        
        hook_idx += 1
        time.sleep(1)
    
    print("✅ Live encerrada")
    return True

def main():
    print("=" * 50)
    print("🔴 Live Broadcast v2 — psicologia.doc")
    print("=" * 50)
    run_live()

if __name__ == "__main__":
    main()
