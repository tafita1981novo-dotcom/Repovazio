#!/usr/bin/env python3
"""
update_broadcast_title.py — Atualiza título/descrição do broadcast ativo
Faz GET do broadcast atual para pegar scheduledStartTime, depois PUT
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
    "en": "🎧 White Noise 40% + Brown Noise 60% — Sleep · Focus · ADHD · Study | Daniela Coelho @psidanicoelho",
    "pt": "🎧 Ruído Branco 40% + Ruído Marrom 60% — Dormir · Focar · TDAH · Estudar | Daniela Coelho @psidanicoelho",
    "de": "🎧 Weißes Rauschen 40% + Braunes Rauschen 60% — Schlafen · Fokus · ADHS | Daniela Coelho @psidanicoelho",
    "es": "🎧 Ruido Blanco 40% + Ruido Marrón 60% — Dormir · Concentrarse · TDAH | Daniela Coelho @psidanicoelho",
    "fr": "🎧 Bruit Blanc 40% + Bruit Brun 60% — Dormir · Focus · TDAH | Daniela Coelho @psidanicoelho",
    "ja": "🎧 ホワイトノイズ40% + ブラウンノイズ60% — 睡眠·集中·ADHD | ダニエラ @psidanicoelho",
    "ko": "🎧 화이트노이즈 40% + 브라운노이즈 60% — 수면·집중·ADHD | 다니엘라 @psidanicoelho",
    "zh": "🎧 白噪音40% + 棕噪音60% — 睡眠·专注·ADHD | 达尼埃拉 @psidanicoelho",
    "it": "🎧 Rumore Bianco 40% + Marrone 60% — Dormire · Studiare · ADHD | Daniela Coelho",
    "nl": "🎧 Witte Ruis 40% + Bruine Ruis 60% — Slapen · Studeren · ADHD | Daniela Coelho",
    "pl": "🎧 Biały Szum 40% + Brązowy 60% — Spanie · Nauka · ADHD | Daniela Coelho",
    "tr": "🎧 Beyaz Gürültü 40% + Kahverengi 60% — Uyku · Çalışma · DEHB | Daniela Coelho",
    "id": "🎧 White Noise 40% + Brown Noise 60% — Tidur · Fokus · ADHD | Daniela Coelho",
    "hi": "🎧 व्हाइट नॉइज़ 40% + ब्राउन 60% — नींद · फोकस | डेनियला @psidanicoelho",
    "ar": "🎧 ضجيج أبيض 40% + بني 60% — نوم · تركيز · ADHD | دانييلا @psidanicoelho",
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

def main():
    token = get_token()
    log("Token OK")

    lang = idioma_por_hora()
    h    = datetime.now(timezone.utc).hour
    log(f"{h:02d}h UTC → idioma: {lang}")

    titulo = TITULOS.get(lang, TITULOS["en"])
    descricao = DESCRICOES_CURTAS.get(lang, DESCRICOES_CURTAS["en"])

    # Buscar broadcast ativo (broadcastStatus=all para pegar qualquer estado)
    url = "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status&broadcastStatus=all&maxResults=5"
    data = yt_get(token, url)
    bc = None
    for item in data.get("items", []):
        lc = item["status"]["lifeCycleStatus"]
        if lc in ["live", "testing", "testStarting", "liveStarting", "ready"]:
            bc = item
            break
    # Se não achou, pegar o mais recente
    if not bc and data.get("items"):
        bc = data["items"][0]

    if not bc:
        log("Nenhum broadcast encontrado!")
        return

    bc_id = bc["id"]
    lc    = bc["status"]["lifeCycleStatus"]
    cur_t = bc["snippet"]["title"]
    sched = bc["snippet"].get("scheduledStartTime","")
    log(f"Broadcast: {bc_id} [{lc}]")
    log(f"  Título atual: {cur_t}")
    log(f"  scheduledStartTime: {sched}")

    if cur_t == titulo:
        log(f"✅ Já está no idioma correto ({lang})!")
        return

    # PUT com scheduledStartTime do broadcast original (obrigatório)
    body = json.dumps({
        "id": bc_id,
        "snippet": {
            "title": titulo[:100],
            "description": descricao[:4900],
            "scheduledStartTime": sched,   # Manter o original
        }
    }).encode()
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet",
        data=body, method="PUT"
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            new_title = result.get("snippet", {}).get("title","")
            log(f"✅ Atualizado: {new_title}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        log(f"❌ Erro {e.code}: {err_body[:300]}")
        # Tentar sem description
        body2 = json.dumps({
            "id": bc_id,
            "snippet": {
                "title": titulo[:100],
                "scheduledStartTime": sched,
            }
        }).encode()
        req2 = urllib.request.Request(
            "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet",
            data=body2, method="PUT"
        )
        req2.add_header("Authorization", f"Bearer {token}")
        req2.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req2, timeout=15) as resp2:
                result2 = json.loads(resp2.read())
                log(f"✅ Atualizado (sem desc): {result2.get('snippet',{}).get('title','')}")
        except urllib.error.HTTPError as e2:
            log(f"❌ Erro 2: {e2.code} {e2.read().decode()[:200]}")

if __name__ == "__main__":
    main()
