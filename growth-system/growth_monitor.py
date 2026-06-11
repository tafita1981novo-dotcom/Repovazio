"""
GROWTH MONITOR — New Life 2Day
Monitora seguidores YouTube toda hora
Alerta em milestones: 100, 500, 1K (TikTok LIVE), 4K horas (AdSense), 10K, 100K
Otimiza canal às 6h UTC: título, descrição multilíngue, keywords
"""
import os, requests, json, datetime
from pathlib import Path

YT_REFRESH      = os.environ.get("YOUTUBE_REFRESH_TOKEN2","")
YT_CLIENT_ID    = os.environ.get("YOUTUBE_CLIENT_ID2","")
YT_CLIENT_SECRET= os.environ.get("YOUTUBE_CLIENT_SECRET2","")
MILESTONES      = [100,500,1000,5000,10000,50000,100000]

def yt_token():
    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH]): return ""
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
        "refresh_token":YT_REFRESH,"grant_type":"refresh_token"})
    return r.json().get("access_token","") if r.status_code==200 else ""

def get_stats():
    token = yt_token()
    if not token: return {}
    r = requests.get("https://www.googleapis.com/youtube/v3/channels?part=statistics&mine=true",
                     headers={"Authorization":f"Bearer {token}"})
    if r.status_code != 200: return {}
    items = r.json().get("items",[])
    if not items: return {}
    s = items[0]["statistics"]
    return {"subs":int(s.get("subscriberCount",0)),
            "views":int(s.get("viewCount",0)),
            "videos":int(s.get("videoCount",0))}

def checar_milestones(subs):
    f = "/tmp/milestones.json"
    hit = json.loads(Path(f).read_text()) if Path(f).exists() else []
    for m in MILESTONES:
        if subs >= m and m not in hit:
            print(f"🎉 MILESTONE {m:,} subs!")
            if m == 1000:  print("  🔴 → Configurar TIKTOK_STREAM_KEY p/ LIVE TikTok")
            if m == 4000:  print("  💰 → Verificar 4.000h assistidas → Ativar AdSense!")
            hit.append(m)
    Path(f).write_text(json.dumps(hit))

def otimizar_canal():
    token = yt_token()
    if not token: return
    desc = """🧠 Sleep Sounds & Brain Science — 24/7 LIVE

🌙 Brown Noise | White Noise | Pink Noise | Rain Sounds | Black Screen
Perfect for: Deep Sleep • Study Focus • Baby Sleep • Tinnitus • ADHD • Meditation • Relaxation

✅ No Ads during sleep hours | ✅ Battery saver mode | ✅ Science-backed sounds

🔔 Subscribe for daily sleep science content
Available 24/7 · All devices · All time zones

🇺🇸 EN | 🇪🇸 ES | 🇧🇷 PT | 🇫🇷 FR | 🇩🇪 DE | 🇮🇹 IT | 🇯🇵 JA

#SleepSounds #WhiteNoise #BrownNoise #PinkNoise #RainSounds #DeepSleep
#StudyMusic #FocusMusic #Meditation #ASMR #TinnitusRelief #BabySleep #ADHD"""

    kw = ("sleep sounds white noise brown noise pink noise rain sounds deep sleep "
          "focus study meditation ADHD tinnitus baby sleep relaxation binaural "
          "ruido blanco dormir lluvia bruit blanc sommeil weißes Rauschen Schlaf")

    r = requests.put(
        "https://www.googleapis.com/youtube/v3/channels?part=brandingSettings",
        headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
        json={"id":"mine","brandingSettings":{"channel":{
            "title":"New Life 2Day | Sleep Sounds & Brain Science",
            "description":desc, "keywords":kw, "defaultLanguage":"en"}}})
    print("✅ Canal otimizado" if r.status_code==200 else f"⚠️ {r.status_code}")

def main():
    print(f"📈 Monitor {datetime.datetime.utcnow():%Y-%m-%d %H:%M UTC}")
    stats = get_stats()
    if stats:
        ts = datetime.datetime.utcnow().isoformat()
        with open("/tmp/growth.jsonl","a") as f: f.write(json.dumps({"ts":ts,**stats})+"\n")
        print(f"   Subs:{stats['subs']:,} | Views:{stats['views']:,} | Vídeos:{stats['videos']}")
        checar_milestones(stats["subs"])
    else: print("⚠️ Sem dados — verificar tokens YouTube")
    if datetime.datetime.utcnow().hour == 6: otimizar_canal()

if __name__ == "__main__":
    main()
