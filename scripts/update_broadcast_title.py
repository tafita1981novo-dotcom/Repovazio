#!/usr/bin/env python3
"""
update_broadcast_title.py — Atualiza título/descrição do broadcast LIVE ativo
Prioridade: live > testing > liveStarting > ready (mais recente)
"""
import os, json, urllib.request, urllib.parse
from datetime import datetime, timezone

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]

def log(m): print(m, flush=True)

TITULOS = {
    "en": "🔴 LIVE 24/7 | White Noise & Brown Noise for Sleep, Focus & Study | Daniela Coelho",
    "pt": "🔴 AO VIVO 24H | Ruído Branco e Marrom para Dormir e Concentrar | Daniela Coelho",
    "de": "🔴 LIVE 24/7 | Weißes & Braunes Rauschen zum Schlafen & Lernen | Daniela Coelho",
    "es": "🔴 EN VIVO 24H | Ruido Blanco y Marrón para Dormir y Estudiar | Daniela Coelho",
    "fr": "🔴 EN DIRECT 24H | Bruit Blanc & Brun pour Dormir et Étudier | Daniela Coelho",
    "ja": "🔴 24時間ライブ | ホワイトノイズ＆ブラウンノイズ 睡眠・集中・勉強 | ダニエラ",
    "ko": "🔴 24시간 라이브 | 화이트노이즈 & 브라운노이즈 수면 집중 공부 | 다니엘라",
    "zh": "🔴 24小时直播 | 白噪音和棕噪音助眠专注学习 | 达尼埃拉·科埃略",
    "it": "🔴 LIVE 24H | Rumore Bianco e Marrone per Dormire e Studiare | Daniela Coelho",
    "nl": "🔴 LIVE 24H | Witte & Bruine Ruis voor Slapen en Studeren | Daniela Coelho",
    "pl": "🔴 NA ŻYWO 24H | Biały i Brązowy Szum do Spania i Nauki | Daniela Coelho",
    "tr": "🔴 CANLI 24H | Beyaz ve Kahverengi Gürültü Uyku ve Çalışma | Daniela Coelho",
    "id": "🔴 LIVE 24H | White Noise & Brown Noise untuk Tidur & Fokus | Daniela Coelho",
    "hi": "🔴 24 घंटे लाइव | व्हाइट नॉइज़ और ब्राउन नॉइज़ नींद के लिए | डेनियला",
    "ar": "🔴 بث مباشر 24 ساعة | ضجيج أبيض وبني للنوم والتركيز والدراسة | دانييلا كويلو",
}

DESCRICOES_CURTAS = {
    "en": "🎧 White Noise 40% + Brown Noise 60% — Sleep · Focus · ADHD · Study\nDaniela Coelho | @psidanicoelho\n#whitenoise #brownnoise #sleep #adhd #focus",
    "pt": "🎧 Ruído Branco 40% + Ruído Marrom 60% — Dormir · Focar · TDAH · Estudar\nDaniela Coelho | @psidanicoelho\n#ruidobranco #ruidomarrom #dormir #tdah #foco",
    "de": "🎧 Weißes Rauschen 40% + Braunes Rauschen 60% — Schlafen · Fokus · ADHS\nDaniela Coelho | @psidanicoelho\n#weißesrauschen #schlafen #adhs #konzentration",
    "es": "🎧 Ruido Blanco 40% + Ruido Marrón 60% — Dormir · Concentrarse · TDAH\nDaniela Coelho | @psidanicoelho\n#ruidoblanco #dormir #tdah #concentracion",
    "fr": "🎧 Bruit Blanc 40% + Bruit Brun 60% — Dormir · Focus · TDAH\nDaniela Coelho | @psidanicoelho\n#bruitblanc #dormir #tdah #concentration",
    "ja": "🎧 ホワイトノイズ40% + ブラウンノイズ60% — 睡眠·集中·ADHD\nダニエラ | @psidanicoelho\n#ホワイトノイズ #睡眠 #集中 #ADHD",
    "ko": "🎧 화이트노이즈 40% + 브라운노이즈 60% — 수면·집중·ADHD\n다니엘라 | @psidanicoelho\n#화이트노이즈 #수면 #집중 #ADHD",
    "zh": "🎧 白噪音40% + 棕噪音60% — 睡眠·专注·ADHD\n达尼埃拉 | @psidanicoelho\n#白噪音 #睡眠 #专注 #ADHD",
}

def idioma_por_hora():
    h = datetime.now(timezone.utc).hour
    if   5  <= h < 8:  return "de"
    elif 8  <= h < 10: return "fr"
    elif 10 <= h < 12: return "ja"
    elif 12 <= h < 15: return "en"
    elif 15 <= h < 18: return "en"
    elif 18 <= h < 20: return "es"
    elif 20 <= h < 22: return "pt"
    elif 22 <= h < 24: return "pt"
    else:              return "en"

def get_token():
    data = urllib.parse.urlencode({
        "client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())["access_token"]

def yt_get(token, url):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def atualizar(token, bc):
    bc_id = bc["id"]
    lc    = bc["status"]["lifeCycleStatus"]
    sched = bc["snippet"].get("scheduledStartTime", "")
    cur_t = bc["snippet"]["title"]
    lang  = idioma_por_hora()
    titulo = TITULOS.get(lang, TITULOS["en"])
    desc   = DESCRICOES_CURTAS.get(lang, DESCRICOES_CURTAS.get("en", ""))
    
    log(f"\nBroadcast: {bc_id} [{lc}] scheduledStartTime={sched}")
    log(f"  Atual:    {cur_t}")
    log(f"  Desejado: {titulo}")
    
    if cur_t == titulo:
        log(f"  ✅ Já correto!")
        return True
    
    body = {"id": bc_id, "snippet": {"title": titulo[:100]}}
    if sched:
        body["snippet"]["scheduledStartTime"] = sched
    if desc:
        body["snippet"]["description"] = desc[:4900]
    
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet",
        data=json.dumps(body).encode(), method="PUT"
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            log(f"  ✅ Atualizado: {result.get('snippet',{}).get('title','')}")
            return True
    except urllib.error.HTTPError as e:
        log(f"  ❌ Erro {e.code}: {e.read().decode()[:200]}")
        return False

def main():
    token = get_token()
    log("Token OK")
    h = datetime.now(timezone.utc).hour
    log(f"{h:02d}h UTC → idioma: {idioma_por_hora()}")

    # Listar TODOS os broadcasts (broadcastStatus=all)
    all_bc = []
    url = "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status&broadcastStatus=all&maxResults=10"
    data = yt_get(token, url)
    all_bc.extend(data.get("items", []))
    log(f"\nTotal broadcasts: {len(all_bc)}")
    for item in all_bc:
        log(f"  {item['id']} [{item['status']['lifeCycleStatus']}] {item['snippet']['title'][:50]}")

    # Prioridade: live > testing > liveStarting > ready (mais recente)
    prioridade = {"live": 0, "testing": 1, "liveStarting": 2, "testStarting": 3, "ready": 4, "created": 5}
    all_bc_sorted = sorted(all_bc, key=lambda x: prioridade.get(x["status"]["lifeCycleStatus"], 99))

    if all_bc_sorted:
        atualizar(token, all_bc_sorted[0])
    else:
        log("Nenhum broadcast encontrado!")

if __name__ == "__main__":
    main()
