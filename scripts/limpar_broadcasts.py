#!/usr/bin/env python3
"""Diagnóstico + correção imediata: lista e atualiza broadcast para EN correto"""
import os, json, urllib.request, time
from datetime import datetime, timezone

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
GH_PAT           = os.environ.get("GH_PAT","")
STREAM_ID        = "SH63tBfY6wEIdkC4u4zKdg1780543868590330"

TITULO_EN = "🔴 LIVE 24/7 | White Noise & Brown Noise for Sleep, Focus & Study | Daniela Coelho"
DESC_EN = """🔴 LIVE 24/7 | WHITE NOISE & BROWN NOISE | Sleep · Focus · Study · ADHD
Daniela Coelho — Human Behavior Researcher | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Use HEADPHONES for the best experience
🤍 WHITE NOISE — covers all background sounds, perfect for sleep & concentration
🟤 BROWN NOISE — deep, rumbling bass, loved by people with ADHD & anxiety
🌙 Mix: 40% White + 60% Brown — scientifically proven for deep sleep
😴 Deep sleep | 🧠 ADHD focus | 📚 Study | 🏢 Productivity | 👶 Baby sleep
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 AO VIVO 24H | Ruído Branco e Marrom para Dormir e Concentrar
🔴 EN VIVO 24H | Ruido Blanco y Marrón para Dormir y Estudiar
🔴 LIVE 24/7 | Weißes & Braunes Rauschen zum Schlafen & Lernen
🔴 EN DIRECT 24H | Bruit Blanc & Brun pour Dormir et Étudier
🔴 24時間ライブ | ホワイトノイズ＆ブラウンノイズ 睡眠・集中
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#whitenoise #brownnoise #sleep #focus #ADHD #study #liveradio
#noiseblanc #ruidobranco #weisesrauschen #whitenoisesleep #brownnoisefocus"""

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)

def get_token():
    body = json.dumps({"client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
                       "refresh_token":YT_REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token",data=body,
                                  headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=15) as r: return json.load(r)["access_token"]

def yt_get(tk,url):
    req=urllib.request.Request(url,headers={"Authorization":f"Bearer {tk}"})
    try:
        with urllib.request.urlopen(req,timeout=10) as r: return json.load(r)
    except Exception as e: return {"error":str(e)}

def yt_call(tk,url,body=None,method="POST"):
    data=json.dumps(body).encode() if body is not None else b"{}"
    req=urllib.request.Request(url,data=data,headers={
        "Authorization":f"Bearer {tk}","Content-Type":"application/json"},method=method)
    try:
        with urllib.request.urlopen(req,timeout=15) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        try: return json.load(e)
        except: return {"error":str(e)}
    except Exception as e: return {"error":str(e)}

def main():
    log("="*60)
    log(f"DIAGNÓSTICO + CORREÇÃO | {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    log("="*60)
    tk = get_token(); log("Token OK")
    
    # Listar TODOS os broadcasts
    log("\n=== TODOS OS BROADCASTS ===")
    todos = []
    for status in ["live","all"]:
        data = yt_get(tk, f"https://www.googleapis.com/youtube/v3/liveBroadcasts"
                         f"?part=id,status,snippet,contentDetails&broadcastStatus={status}&maxResults=50")
        for item in data.get("items",[]):
            bid = item["id"]
            if not any(x["id"]==bid for x in todos):
                lc  = item.get("status",{}).get("lifeCycleStatus","?")
                tit = item.get("snippet",{}).get("title","?")
                desc_start = item.get("snippet",{}).get("description","")[:80]
                lang = item.get("snippet",{}).get("defaultLanguage","?")
                stream_bound = item.get("contentDetails",{}).get("boundStreamId","none")[:20]
                todos.append({"id":bid,"lc":lc,"title":tit,"lang":lang,
                               "stream":stream_bound,"desc_start":desc_start})
    
    for b in todos:
        log(f"\n  ID: {b['id']}")
        log(f"  Status: {b['lc']}")
        log(f"  Título: {b['title'][:80]}")
        log(f"  Idioma: {b['lang']}")
        log(f"  Stream: {b['stream']}")
        log(f"  Desc início: {b['desc_start']}")
    
    log(f"\nTotal: {len(todos)} broadcast(s)")
    
    # Corrigir: atualizar TODOS para EN com título e descrição corretos
    log("\n=== CORRIGINDO PARA EN ===")
    for b in todos:
        body = {
            "id": b["id"],
            "snippet": {
                "title": TITULO_EN[:100],
                "description": DESC_EN[:4900],
                "defaultLanguage": "en",
            }
        }
        res = yt_call(tk,
            "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet",
            body, method="PUT")
        if "id" in res:
            log(f"  ✅ {b['id']} [{b['lc']}] → EN corrigido")
        else:
            log(f"  ⚠ {b['id']}: {str(res)[:100]}")
        time.sleep(0.5)
    
    # Confirmar estado final
    log("\n=== ESTADO FINAL ===")
    data_final = yt_get(tk, "https://www.googleapis.com/youtube/v3/liveBroadcasts"
                            "?part=id,status,snippet&broadcastStatus=all&maxResults=10")
    for item in data_final.get("items",[]):
        lc  = item.get("status",{}).get("lifeCycleStatus","?")
        tit = item.get("snippet",{}).get("title","?")[:80]
        log(f"  [{lc}] {item['id']} → {tit}")

if __name__ == "__main__":
    main()
