"""
TikTok LIVE 24/7 — White/Brown/Pink Noise + Tela Preta
Sistema de crescimento acelerado @newlife_2day
"""
import os, subprocess, requests, datetime

TIKTOK_STREAM_KEY = os.environ.get("TIKTOK_STREAM_KEY2", "")
TIKTOK_RTMP_URL   = "rtmp://push.tiktok.com/live/"
SUPABASE_URL      = os.environ.get("SUPABASE_URL2", "")
SUPABASE_KEY      = os.environ.get("SUPABASE_KEY2", "")

STREAM_TYPES = [
    {"tipo": "brown", "bg": "0x1a0a00", "cor": "0xD4A57A", "titulo": "BROWN NOISE Deep Sleep 24/7"},
    {"tipo": "white", "bg": "0xf0f0f0", "cor": "0x333333", "titulo": "WHITE NOISE Sleep Better 24/7"},
    {"tipo": "black", "bg": "0x000000", "cor": "0x111111", "titulo": "BLACK SCREEN Sleep Sound 24/7"},
    {"tipo": "pink",  "bg": "0x1a0010", "cor": "0xFFB3D9", "titulo": "PINK NOISE Relaxation 24/7"},
    {"tipo": "rain",  "bg": "0x001a2a", "cor": "0x87CEEB", "titulo": "RAIN SOUNDS Deep Sleep 24/7"},
]

def gerar_stream(tipo: str, bg: str) -> subprocess.Popen:
    filtros = {
        "brown": "anoisesrc=color=brown:amplitude=0.3",
        "white": "anoisesrc=color=white:amplitude=0.15",
        "pink":  "anoisesrc=color=pink:amplitude=0.25",
        "black": "anoisesrc=color=brown:amplitude=0.08",
        "rain":  "anoisesrc=color=pink:amplitude=0.2,aecho=0.8:0.7:60:0.3",
    }
    rtmp = f"{TIKTOK_RTMP_URL}{TIKTOK_STREAM_KEY}"
    noise = filtros.get(tipo, filtros["brown"])
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={bg}:size=720x1280:rate=1",
        "-f", "lavfi", "-i", f"{noise}",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
        "-b:v", "1000k", "-g", "60",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-f", "flv", rtmp
    ]
    print(f"🎬 Iniciando LIVE: {tipo.upper()} NOISE → {rtmp[:40]}...")
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def executar():
    if not TIKTOK_STREAM_KEY:
        print("❌ TIKTOK_STREAM_KEY2 não configurado nos secrets")
        return
    hora = datetime.datetime.utcnow().hour
    stream = STREAM_TYPES[hora % len(STREAM_TYPES)]
    print(f"🎵 Stream da hora {hora}h UTC: {stream['titulo']}")
    proc = gerar_stream(stream["tipo"], stream["bg"])
    if SUPABASE_URL:
        requests.post(f"{SUPABASE_URL}/rest/v1/tiktok_live_log",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                     "Content-Type": "application/json", "Prefer": "return=minimal"},
            json={"date": datetime.date.today().isoformat(), "hora": hora,
                  "tipo": stream["tipo"], "titulo": stream["titulo"], "status": "live"},
            timeout=10)
    print(f"✅ LIVE ativa: {stream['titulo']}")
    try:
        proc.wait(timeout=3540)
    except subprocess.TimeoutExpired:
        proc.terminate()
    print("🔄 Ciclo encerrado")

if __name__ == "__main__":
    executar()
