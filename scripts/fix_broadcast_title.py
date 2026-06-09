#!/usr/bin/env python3
"""Corrigir broadcast eterno: título EN, descrição sem Daniela Coelho"""
import json, os, urllib.request, urllib.parse, urllib.error

def token():
    r=urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token",
        data=urllib.parse.urlencode({"client_id":os.environ["YT_CLIENT_ID"],
        "client_secret":os.environ["YT_CLIENT_SECRET"],
        "refresh_token":os.environ["YT_REFRESH_TOKEN"],"grant_type":"refresh_token"}).encode(),
        headers={"Content-Type":"application/x-www-form-urlencoded"}),timeout=15)
    return json.loads(r.read())["access_token"]

def yt(method,ep,data=None,params=None,T=None):
    url="https://www.googleapis.com/youtube/v3/"+ep
    if params: url+="?"+urllib.parse.urlencode(params)
    h={"Authorization":f"Bearer {T}"}; b=None
    if data: b=json.dumps(data).encode(); h["Content-Type"]="application/json"
    req=urllib.request.Request(url,data=b,headers=h,method=method)
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read(); return (json.loads(raw) if raw else {}),r.status
    except urllib.error.HTTPError as e:
        raw=e.read(); return (json.loads(raw) if raw else {}),e.code

T=token(); BID="5HqPWz058Qw"
TITLE='🔴 WHITE NOISE & BROWN NOISE 24/7 | Black Screen | sleep | tinnitus relief | ADHD focus | baby sleep'
DESC='🌙 WHITE NOISE & BROWN NOISE 24/7 — Always LIVE, Never Recorded\n\n✅ Subscribe FREE  🔔 Notify ALL  📱 Best with headphones / Melhor com fones / Mejor con auriculares\n\n🇺🇸 SLEEP  •  🇪🇸 SUEÑO  •  🇧🇷 DORMIR  •  🇩🇪 SCHLAFEN  •  🇫🇷 SOMMEIL  •  🇮🇹 DORMIRE\n🇯🇵 眠る  •  🇰🇷 수면  •  🇨🇳 睡觉  •  🇸🇦 نوم  •  🇷🇺 Сон  •  🇮🇳 नींद\n🇮🇩 TIDUR  •  🇳🇱 SLAPEN  •  🇹🇷 UYKU  •  🇵🇱 SEN  •  🇻🇳 NGỦ\n\n────────────────────────────────────────\n🧠 ADHD FOCUS  •  📚 STUDY WITH ME  •  👶 BABY SLEEP  •  🔇 TINNITUS ASMR RELIEF\n────────────────────────────────────────\n\n🎧 WHAT YOU HEAR:\n✅ White Noise — masks tinnitus, blocks distractions, soothes babies\n✅ Brown Noise — deep bass frequency for ADHD focus, deep sleep & anxiety relief\n✅ Mix 40% White + 60% Brown — optimal for 8h+ sessions\n\n🔔 SUBSCRIBE / INSCREVA-SE / SUSCRRÍBETE:\n» https://www.youtube.com/@psidanicoelho\n\n#whitenoise #brownnoise #sleep #ASMR #blackscreen #lofi #tinnitus #babysleep #ADHDfocus #studywithme\n#백색소음 #白噪音 #ホワイトノイズ #ruidoblanco #ruidobranco'

print("Atualizando broadcast eterno...")
res,code=yt("PUT","liveBroadcasts",T=T,params={"part":"snippet"},data={
    "id":BID,
    "snippet":{"title":TITLE,"scheduledStartTime":"2026-01-01T00:00:00.000Z","description":DESC}
})
if code==200:
    print(f"OK titulo: {res.get('snippet',{}).get('title','?')[:60]}")
else:
    print(f"ERRO {code}: {str(res)[:200]}")
