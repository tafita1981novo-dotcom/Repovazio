#!/usr/bin/env python3
"""
update_broadcast_title.py — Atualiza todos os broadcasts encontrados para o idioma correto
Faz query separada por: live, testing, active, all
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
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERR GET: {e}")
        return {}

def update_bc(token, bc_id, sched, titulo, descricao=""):
    body = {"id": bc_id, "snippet": {"title": titulo[:100]}}
    if sched:
        body["snippet"]["scheduledStartTime"] = sched
    if descricao:
        body["snippet"]["description"] = descricao[:4900]
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet",
        data=json.dumps(body).encode(), method="PUT"
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            return result.get("snippet", {}).get("title", "")
    except urllib.error.HTTPError as e:
        return f"ERR {e.code}: {e.read().decode()[:100]}"

def main():
    token = get_token()
    lang = idioma_por_hora()
    titulo = TITULOS.get(lang, TITULOS["en"])
    h = datetime.now(timezone.utc).hour
    log(f"Token OK | {h:02d}h UTC → {lang} | Desejado: {titulo[:50]}")

    # Buscar por TODOS os status possíveis incluindo live separado
    all_bc = {}
    for bs in ["live", "active", "all"]:
        url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status&broadcastStatus={bs}&maxResults=50"
        data = yt_get(token, url)
        count = 0
        for item in data.get("items", []):
            bc_id = item["id"]
            if bc_id not in all_bc:
                all_bc[bc_id] = item
                count += 1
        log(f"  broadcastStatus={bs}: {count} novos | total {len(all_bc)}")

    log(f"\nTotal único: {len(all_bc)}")
    for bc_id, item in all_bc.items():
        lc = item["status"]["lifeCycleStatus"]
        t  = item["snippet"]["title"][:60]
        sched = item["snippet"].get("scheduledStartTime","")
        log(f"  {bc_id} [{lc}] {t}")

        if t != titulo:
            result = update_bc(token, bc_id, sched, titulo)
            log(f"    → UPDATE: {result[:60]}")
        else:
            log(f"    → ✅ Já correto")

if __name__ == "__main__":
    main()
