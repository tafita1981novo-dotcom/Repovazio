"""
LIVE 24/7 — New Life 2Day | Sleep Sounds & Brain Science
Rotação automática por hora UTC: Brown / White / Black / Pink / Rain
YouTube RTMP contínuo — público inglês — monetização global
Custo: $0 (ffmpeg nativo + GitHub Actions)
"""
import os, subprocess, datetime
from pathlib import Path

YT_STREAM_KEY = os.environ.get("YOUTUBE_STREAM_KEY", "")
YT_RTMP       = f"rtmp://a.rtmp.youtube.com/live2/{YT_STREAM_KEY}"
TT_STREAM_KEY = os.environ.get("TIKTOK_STREAM_KEY", "")
TT_RTMP       = f"rtmp://live.tiktok.com/app/{TT_STREAM_KEY}"

SCHEDULE = {
    0:  {"type":"brown", "color":"3d1f0d", "title":"Brown Noise Deep Sleep 24/7 | Study Focus Sleep"},
    1:  {"type":"white", "color":"e8e8e8", "title":"White Noise Sleep 24/7 | Baby Sleep & Relaxation"},
    2:  {"type":"black", "color":"000000", "title":"Black Screen Sleep Sound 24/7 | Save Battery"},
    3:  {"type":"pink",  "color":"ffb6c1", "title":"Pink Noise Deep Sleep 24/7 | Memory & REM Boost"},
    4:  {"type":"rain",  "color":"1a3a5c", "title":"Rain Sounds Sleep 24/7 | Thunderstorm Relaxation"},
    5:  {"type":"brown", "color":"3d1f0d", "title":"Brown Noise Focus 24/7 | ADD DeeVWork Study"},
    6:  {"type":"white", "color":"e8e8e8", "title":"White Noise Morning Focus 24/7 | Productivity"},
    7:  {"type":"rain",  "color":"1a3a5c", "title":"Gentle Rain 24/7 | Relaxing ASMR Rain Sleep"},
    8:  {"type":"black", "color":"000000", "title":"Black Screen Study Sound 24/7 | No Distractions"},
    9:  {"type":"pink",  "color":"ffb6c1", "title":"Pink Noise Brain Boost 24/7 | Memory Learning"},
    10: {"type":"brown", "color":"3d1f0d", "title":"Brown Noise Tinnitus Relief 24/7 | Ear Masking"},
    11: {"type":"rain",  "color":"1a3a5c", "title":"Heavy Rain 24/7 | Thunderstorm Deep Sleep Sound"},
    12: {"type":"white", "color":"e8e8e8", "title":"White Noise Nap 24/7 | Power Nap Recharge"},
    13: {"type":"pink",  "color":"ffb6c1", "title":"Pink Noise Anxiety Relief 24/7 | Calm Mind"},
    14: {"type":"black", "color":"000000", "title":"Black Screen Meditation 24/7 | Mindfulness"},
    15: {"type":"brown", "color":"3d1f0d", "title":"Brown Noise Reading 24/7 | Library Ambience"},
    16: {"type":"rain",  "color":"1a3a5c", "title":"Rain Cafe Ambience 24/7 | Work Focus Sound"},
    17: {"type":"white", "color":"e8e8e8", "title":"White Noise Evening Unwind 24/7 | Decompress"},
    18: {"type":"pink",  "color":"ffb6c1", "title":"Pink Noise Bedtime 24/7 | Fall Asleep Fast"},
    19: {"type":"brown", "color":"3d1f0d", "title":"Brown Noise Night 24/7 | Block Noise Deep Sleep"},
    20: {"type":"black", "color":"000000", "title":"Black Screen Night 24/7 | Sleep No Light"},
    21: {"type":"rain",  "color":"1a3a5c", "title":"Midnight Rain 24/7 | Deep Sleep Rainfall"},
    22: {"type":"white", "color":"e8e8e8", "title":"White Noise All Night 24/7 | Sleep Aid Adults"},
    23: {"type":"pink",  "color":"ffb6c1", "title":"Pink Noise REM Sleep 24/7 | Wake Up Refreshed"},
}

NOISE_FILTER = {
    "brown": "anoisesrc=color=brown:amplitude=0.5",
    "white": "anoisesrc=color=white:amplitude=0.3",
    "black": "anoisesrc=color=brown:amplitude=0.12",
    "pink":  "anoisesrc=color=pink:amplitude=0.4",
    "rain":  "anoisesrc=color=brown:amplitude=0.7,highpass=f=150,lowpass=f=9000",
}

def gerar_frame(tipo, cor_hex):
    out = f"/tmp/frame_{tipo}.png"
    if Path(out).exists(): return out
    labels = {"brown":"BROWN NOISE","white":"WHITE NOISE","black":"BLACK SCREEN","pink":"PINK NOISE","rain":"RAIN SOUNDS"}
    txt = labels.get(tipo,"SLEEP SOUND")
    fg  = "ffffff" if cor_hex in ["3d1f0d","000000","1a3a5c"] else "222222"
    cmd = ["ffmpeg","-y","-f","lavfi","-i",
           f"color=#{cor_hex}:size=1920x1080:rate=1",
           "-vf",
           f"drawtext=text='{txt}':fontcolor=#{fg}:fontsize=90:x=(w-text_w)/2:y=(h-text_h)/2-60:font=monospace:style=bold,"
           f"drawtext=text='New Life 2Day':fontcolor=#{fg}@0.9:fontsize=36:x=(w-text_w)/2:y=(h-text_h)/2+60:font=monospace,"
           f"drawtext=text='24/7 LIVE — Sleep Sounds & Brain Science':fontcolor=#{fg}@0.6:fontsize=22:x=(w-text_w)/2:y=60:font=monospace",
           "-frames:v","1", out]
    try: subprocess.run(cmd, check=True, capture_output=True, timeout=30); return out
    except: return ""

def gerar_audio(tipo, dur=3620):
    out = f"/tmp/audio_{tipo}.aac"
    if Path(out).exists(): return out
    filt = NOISE_FILTER.get(tipo, NOISE_FILTER["brown"])
    cmd = ["ffmpeg","-y","-f","lavfi","-i",f"{dfilt}:duration={dur}","-c:a","aac","-b:a","128k","-ar","44100",out]
    try: subprocess.run(cmd, check=True, capture_output=True, timeout=120); return out
    except: return ""

def stream_rtmp(rtmp_url, frame, audio, dur=3600):
    if not rtmp_url or "None" in rtmp_url: return False
    cmd = ["ffmpeg","-y","-loop","1","-i",frame,"-i",audio,
           "-c:v","libx264","-preset","ultrafast","-tune","stillimage",
           "-c:a","aac","-b:a","128k","-pix_fmt","yuv420p",
           "-g","50","-b:v","2500k","-maxrate","3000k","-bufsize","6000k",
           "-f","flv","-t",str(dur), rtmp_url]
    try:
        subprocess.run(cmd, timeout=dur+120, capture_output=True)
        return True
    except: return False

def main():
    hora = datetime.datetime.utcnow().hour
    slot = SCHEDULE.get(hora, SCHEDULE[0])
    tipo, cor, titulo = slot["type"], slot["color"], slot["title"]
    print(f"😙️ LIVE 24/7 | {datetime.datetime.utcnow():%Y-%m-%d %H:%M UTC} | {hora}h → {tipo.upper()}")
    print(f"   📺 {titulo}")
    frame = gerar_frame(tipo, cor)
    audio = gerar_audio(tipo)
    if not frame or not audio:
        print("❌ Assets não gerados"); return
    if YT_STREAM_KEY:
        print("📡 Streaming → YouTube...")
        stream_rtmp(YT_RTMP, frame, audio)
        print("✅ YouTube stream concluído")
    else:
        print("⚠️ YOUTUBE_STREAM_KEY ausente → studio.youtube.com → Ir ao vivo → copiar key")
        print("   github.com/tafita81/Repovazio/settings/secrets/actions → YOUTUBE_STREAM_KEY")
    if TT_STREAM_KEY:
        print("📡 Streaming → TikTok...")
        stream_rtmp(TT_RTMP, frame, audio)
        print("✅ TikTok stream concluído")

if __name__ == "__main__":
    main()
