#!/usr/bin/env python3
"""Deletar todos os Shorts do canal + atualizar descrição da live"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error

CI=os.environ["YT_CLIENT_ID"]; CS=os.environ["YT_CLIENT_SECRET"]
RT=os.environ["YT_REFRESH_TOKEN"]

def get_token():
    r=urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=urllib.parse.urlencode({"client_id":CI,"client_secret":CS,
            "refresh_token":RT,"grant_type":"refresh_token"}).encode(),
        headers={"Content-Type":"application/x-www-form-urlencoded"}),timeout=15)
    return json.loads(r.read())["access_token"]

def yt(method,ep,data=None,params=None,token=None):
    url="https://www.googleapis.com/youtube/v3/"+ep
    if params: url+="?"+urllib.parse.urlencode(params)
    headers={"Authorization":f"Bearer {token}"}
    body=None
    if data is not None:
        body=json.dumps(data).encode(); headers["Content-Type"]="application/json"
    req=urllib.request.Request(url,data=body,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read(); return (json.loads(raw) if raw else {}),r.status
    except urllib.error.HTTPError as e:
        raw=e.read(); return (json.loads(raw) if raw else {}),e.code

TOKEN=get_token()
print(f"Token OK")

# ── 1. Listar todos os vídeos do canal ────────────────────────
print("\n1. Listando vídeos...")
# Buscar uploads playlist
res,_=yt("GET","channels",params={"part":"contentDetails","mine":"true"},token=TOKEN)
uploads_id=res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
print(f"   Playlist uploads: {uploads_id}")

videos=[]
page=None
while True:
    params={"part":"snippet,contentDetails","playlistId":uploads_id,"maxResults":"50"}
    if page: params["pageToken"]=page
    res,_=yt("GET","playlistItems",params=params,token=TOKEN)
    for item in res.get("items",[]):
        vid=item["snippet"]["resourceId"]["videoId"]
        title=item["snippet"]["title"][:50]
        videos.append({"id":vid,"title":title})
    page=res.get("nextPageToken")
    if not page: break

print(f"   Total: {len(videos)} vídeos")

# ── 2. Identificar Shorts (duração <= 60s) ────────────────────
print("\n2. Identificando Shorts...")
shorts=[]
for i in range(0,len(videos),50):
    batch=videos[i:i+50]
    ids=",".join(v["id"] for v in batch)
    res,_=yt("GET","videos",params={"part":"contentDetails,snippet","id":ids},token=TOKEN)
    for item in res.get("items",[]):
        dur=item["contentDetails"]["duration"]  # ISO 8601 PT#M#S
        title=item["snippet"]["title"][:50]
        vid=item["id"]
        # Parse duration
        import re
        m=re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',dur)
        if m:
            h,mn,s=int(m.group(1) or 0),int(m.group(2) or 0),int(m.group(3) or 0)
            total_s=h*3600+mn*60+s
            if total_s<=60:
                shorts.append({"id":vid,"title":title,"duration":total_s})
                print(f"   SHORT {vid} ({total_s}s): {title}")
    time.sleep(0.2)

print(f"\n   Total Shorts: {len(shorts)}")

# ── 3. Deletar todos os Shorts ────────────────────────────────
if shorts:
    print("\n3. Deletando Shorts...")
    deleted=0
    for video in shorts:
        res,code=yt("DELETE","videos",params={"id":video["id"]},token=TOKEN)
        print(f"   {'OK' if code in (200,204) else 'ERR '+str(code)} {video['id']}: {video['title']}")
        deleted+=1
        time.sleep(0.4)
    print(f"\n   Deletados: {deleted}/{len(shorts)}")
else:
    print("\n3. Nenhum Short encontrado!")

# ── 4. Atualizar descrição do broadcast eterno ───────────────
print("\n4. Atualizando descrição da live...")
BROADCAST_ID="5HqPWz058Qw"
DESC="""🔴 WHITE NOISE & BROWN NOISE 24/7 | Black Screen | Ruido Blanco | Ruído Branco | 白噪音

✅ Subscribe FREE   🔔 Notify ALL   📱 Best with headphones / Melhor com fones / Mejor con auriculares

🇺🇸 SLEEP  •  🇪🇸 SUEÑO  •  🇧🇷 DORMIR  •  🇩🇪 SCHLAFEN  •  🇫🇷 SOMMEIL  •  🇮🇹 DORMIRE
🇯🇵 眠る (NEMURU)  •  🇰🇷 수면 (SUMYEON)  •  🇨🇳 睡觉 (SHUÌ JIÀO)  •  🇸🇦 نوم (NAWM)  •  🇷🇺 СОН (SON)
🇮🇳 नींद (NĪND)  •  🇮🇩 TIDUR  •  🇳🇱 SLAPEN  •  🇹🇷 UYKU  •  🇵🇱 SEN  •  🇻🇳 NGỦ

────────────────────────────────────────
🧠 ADHD FOCUS  •  📚 STUDY WITH ME  •  👶 BABY SLEEP  •  🔇 TINNITUS ASMR RELIEF
────────────────────────────────────────

🎧 WHAT YOU HEAR / O QUE VOCÊ OUVE / LO QUE ESCUCHAS:
✅ White Noise — masks tinnitus, blocks distractions, soothes babies / mascara o zumbido
✅ Brown Noise — deep bass frequency for ADHD focus, deep sleep & anxiety relief
✅ Mix 40% White + 60% Brown — optimal for 8h+ sessions

🚀 WHY IT WORKS / POR QUE FUNCIONA / POR QUÉ FUNCIONA:
• Tinnitus relief — constant sound masks ear ringing (medically recommended)
• ADHD & study focus — brown noise reduces internal mind-wandering
• Baby sleep — white noise mimics womb sounds, calms newborns
• Deep sleep — masks snoring, traffic, sudden noises
• Lofi & study sessions — background noise without lyrics or distraction

📱 BEST EXPERIENCE / MELHOR EXPERIÊNCIA / MEJOR EXPERIENCIA:
• Use headphones at ~40% volume
• Set timer: 30min focus, 8h sleep, all night baby
• Compatible with: AirPods, earbuds, speakers, smart home

🔔 SUBSCRIBE / INSCREVA-SE / SUSCRRÍBETE — FREE, always:
» https://www.youtube.com/@psidanicoelho
» Ative o 🔔 sininho para ser notificado / Click the 🔔 bell / Activa la 🔔 campanita

────────────────────────────────────────
🏷️ TAGS / KEYWORDS:
sleep, white noise, brown noise, black screen, ruido blanco, tinnitus relief, ADHD focus,
baby sleep, study with me, lofi, deep sleep, anxiety relief, focus music, meditation,
relaxation, background noise, tinnitus masking, noise for sleep, ADHD music, baby calming,
睡眠 BGM, 白噪音, 수면 백색소음, nuit calme, dormir facile, ruído branco sono, gerusch schlafen

© psicologia.doc | @psidanicoelho | Always live 24/7 | Never recorded"""

res,code=yt("PUT","liveBroadcasts",params={"part":"snippet"},token=TOKEN,data={
    "id":BROADCAST_ID,
    "snippet":{
        "title":"\U0001f534 WHITE NOISE & BROWN NOISE 24/7 | Black Screen | sleep | tinnitus relief | ADHD focus | baby sleep",
        "scheduledStartTime":"2026-01-01T00:00:00.000Z",
        "description":DESC
    }
})
if code==200:
    print(f"   OK descrição atualizada!")
else:
    print(f"   WARN {code}: {str(res)[:200]}")

print("\n===== DONE =====")
