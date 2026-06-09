#!/usr/bin/env python3
"""Corrigir broadcast: título EN + descrição 17 idiomas + keywords completas"""
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
DESC='🌙 WHITE NOISE & BROWN NOISE 24/7 — Always LIVE, Never Recorded | Black Screen\n🔔 Subscribe FREE → https://www.youtube.com/@psidanicoelho\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🧠 ADHD FOCUS  •  📚 STUDY WITH ME  •  👶 BABY SLEEP  •  🔇 TINNITUS RELIEF\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🎧 White Noise 40% + Brown Noise 60% — optimal mix for 8h+ sessions\n✅ Masks distractions • Deep ADHD focus • Soothes babies • Tinnitus relief • Deep sleep\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🌍 17 LANGUAGES / 17 IDIOMAS / 17 SPRACHEN\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🇺🇸 ENGLISH — White noise for sleep, ADHD focus music, brown noise study, baby sleep sounds, tinnitus relief sounds, black screen sleep, lofi sleep music, deep sleep sounds, relaxing noise for studying, noise masking, white noise for babies, focus music 8 hours\n\n🇧🇷 PORTUGUÊS — Ruído branco para dormir, ruído marrom foco TDAH, sons para bebê dormir, alívio zumbido, sons relaxantes, fundo preto, musica para dormir, sons para estudar, ruído branco 8 horas, ruído rosa sono profundo\n\n🇪🇸 ESPAÑOL — Ruido blanco para dormir, ruido marrón concentración TDAH, sonidos para bebés, alivio tinnitus, sonidos relajantes, pantalla negra, música para dormir, ruido blanco 8 horas, sonidos de estudio\n\n🇩🇪 DEUTSCH — Weißes Rauschen zum Schlafen, braunes Rauschen Konzentration ADHS, Babyschlafen Geräusche, Tinnitus Linderung, entspannende Geräusche, schwarzer Bildschirm schlafen, Schlafmusik 8 Stunden\n\n🇫🇷 FRANÇAIS — Bruit blanc pour dormir, bruit brun concentration TDAH, sons bébé sommeil, soulagement acouphènes, sons relaxants, écran noir, musique sommeil, bruit blanc 8 heures\n\n🇮🇹 ITALIANO — Rumore bianco per dormire, rumore marrone concentrazione ADHD, suoni neonato, sollievo acufeni, suoni rilassanti, schermo nero, musica per dormire\n\n🇯🇵 日本語 — 白色雑音 睡眠, ブラウンノイズ ADHD 集中, 赤ちゃん 眠る, 耳鳴り 緩和, リラックス 音, 黒画面, 睡眠音楽, 勉強 集中音楽, 8時間 睡眠\n\n🇰🇷 한국어 — 백색소음 수면, 브라운노이즈 ADHD 집중, 아기 수면 소리, 이명 완화, 집중 공부 음악, 검은 화면, 수면 음악 8시간\n\n🇨🇳 中文 — 白噪音睡眠, 棕色噪音专注 ADHD, 婴儿睡觉声音, 耳鸣缓解, 黑屏睡眠音乐, 学习专注音乐, 8小时睡眠\n\n🇸🇦 عربي — ضوضاء بيضاء للنوم, ضوضاء بنية للتركيز ADHD, أصوات نوم الأطفال, تخفيف طنين الأذن, موسيقى نوم, شاشة سوداء\n\n🇷🇺 РУССКИЙ — Белый шум для сна, коричневый шум концентрация СДВГ, звуки для сна младенца, облегчение тиннитуса, расслабляющие звуки, черный экран, музыка для сна\n\n🇮🇳 हिंदी — सोने के लिए सफेद शोर, ADHD ध्यान भूरा शोर, बच्चे की नींद, टिनिटस राहत, आराम की आवाजें\n\n🇮🇩 INDONESIA — Suara putih untuk tidur, suara cokelat fokus ADHD, suara bayi tidur, pereda tinnitus, musik tidur, layar hitam\n\n🇳🇱 NEDERLANDS — Witte ruis voor slapen, bruine ruis concentratie ADHD, baby slaapgeluiden, tinnitus verlichting, slaapscherm\n\n🇹🇷 TÜRKÇE — Beyaz gürültü uyku, kahverengi gürültü ADHD konsantrasyon, bebek uyku sesleri, tinnitus rahatlama, uyku müziği\n\n🇵🇱 POLSKI — Biały szum do spania, brązowy szum ADHD koncentracja, dźwięki dla niemowląt, ulga tinnitus, muzyka do snu\n\n🇻🇳 TIẾNG VIỆT — Tiếng ồn trắng ngủ, tiếng ồn nâu tập trung ADHD, âm thanh ngủ cho bé, giảm ù tai, màn hình đen\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n#whitenoise #brownnoise #sleep #blackscreen #ASMR #tinnitus #babysleep #ADHDfocus #studywithme #lofi #deepsleeep #focusmusic #ruiodobranco #ruidoblanco #weißesrauschen #백색소음 #白噪音 #ホワイトノイズ #수면 #sleepsounds #noiseblanc #raumorebianco #tidur #белыйшум #beyazgurultu #bialyazum'

print("Atualizando broadcast eterno...")
res,code=yt("PUT","liveBroadcasts",T=T,params={"part":"snippet"},data={
    "id":BID,
    "snippet":{"title":TITLE,"scheduledStartTime":"2026-01-01T00:00:00.000Z","description":DESC}
})
if code==200:
    sn=res.get("snippet",{})
    print(f"OK titulo: {sn.get('title','?')[:60]}")
    print(f"OK desc: {len(sn.get('description',''))} chars")
else:
    print(f"ERRO {code}: {str(res)[:300]}")
