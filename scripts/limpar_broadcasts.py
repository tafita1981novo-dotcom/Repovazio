#!/usr/bin/env python3
"""
limpar_broadcasts.py — Apaga TODOS os broadcasts e cria 1 único eterno em EN
"""
import os, json, urllib.request, time, sys
from datetime import datetime, timezone, timedelta

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
ST_KEY_VAL       = "ewme-91sq-yae7-yj1q-5skw"
RTMP             = f"rtmp://a.rtmp.youtube.com/live2/{ST_KEY_VAL}"
STREAM_ID        = "SH63tBfY6wEIdkC4u4zKdg1780543868590330"

TITULO_EN = "🔴 LIVE 24/7 | White Noise & Brown Noise for Sleep, Focus & Study | Daniela Coelho"
DESC_EN = """🔴 LIVE 24/7 | WHITE NOISE & BROWN NOISE | Sleep · Focus · Study · ADHD
Daniela Coelho — Human Behavior Researcher | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Use HEADPHONES for the best experience
🤍 WHITE NOISE — covers all background sounds, perfect for sleep & concentration
🟤 BROWN NOISE — deep, rumbling bass, loved by people with ADHD & anxiety
🌙 Mix: 40% White + 60% Brown — scientifically proven for deep sleep
😴 Deep sleep & insomnia | 🧠 ADHD focus | 📚 Study | 🏢 Productivity | 👶 Baby
#whitenoise #brownnoise #sleep #focus #ADHD #study #liveradio #psychoacoustics"""

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)

def get_token():
    body = json.dumps({
        "client_id": YT_CLIENT_ID,
        "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token",
                                  data=body, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)["access_token"]

def yt_get(tk, url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tk}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.load(r)
    except Exception as e:
        return {"error": str(e)}

def yt_call(tk, url, body=None, method="POST"):
    data = json.dumps(body).encode() if body is not None else b"{}"
    req = urllib.request.Request(url, data=data,
                                  headers={"Authorization": f"Bearer {tk}",
                                           "Content-Type": "application/json"},
                                  method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try: return json.load(e)
        except: return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}

def apagar_todos(tk):
    """Apaga TODOS os broadcasts sem exceção"""
    log("=== APAGANDO TODOS OS BROADCASTS ===")
    total = 0
    for status in ["live", "active", "testing", "all"]:
        url = (f"https://www.googleapis.com/youtube/v3/liveBroadcasts"
               f"?part=id,status,snippet&broadcastStatus={status}&maxResults=50")
        data = yt_get(tk, url)
        items = data.get("items", [])
        if status == "all":
            log(f"  all: {len(items)} broadcasts")
        for item in items:
            bid = item["id"]
            lc  = item.get("status", {}).get("lifeCycleStatus", "?")
            tit = item.get("snippet", {}).get("title", "?")[:50]
            log(f"  [{lc}] {bid} — {tit}")
            # Tentar encerrar se estiver ao vivo
            if lc in ["live", "testing", "testStarting", "liveStarting"]:
                yt_call(tk,
                    f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition"
                    f"?broadcastStatus=complete&id={bid}&part=id", {})
                time.sleep(1.5)
            # Deletar
            req = urllib.request.Request(
                f"https://www.googleapis.com/youtube/v3/liveBroadcasts?id={bid}",
                method="DELETE")
            req.add_header("Authorization", f"Bearer {tk}")
            try:
                urllib.request.urlopen(req, timeout=10)
                log(f"  ✅ Deletado: {bid}")
                total += 1
            except Exception as e:
                log(f"  ⚠ Erro deletar {bid}: {e}")
            time.sleep(0.3)
    log(f"Total deletados: {total}")
    return total

def criar_broadcast_en(tk):
    """Cria 1 único broadcast em EN — eterno, sem rotação de idioma"""
    start = (datetime.now(timezone.utc) + timedelta(minutes=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "snippet": {
            "title": TITULO_EN[:100],
            "description": DESC_EN[:4900],
            "scheduledStartTime": start,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        },
        "contentDetails": {
            "enableAutoStart": True,
            "enableAutoStop": False,
            "enableDvr": True,
            "enableEmbed": True,
            "recordFromStart": True,
            "startWithSlate": False,
            "monitorStream": {"enableMonitorStream": False}
        }
    }
    res = yt_call(tk,
        "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails",
        body)
    if "id" in res:
        log(f"✅ Broadcast criado: {res['id']} — {TITULO_EN[:60]}")
        return res["id"]
    log(f"❌ Falha criar broadcast: {res}")
    return None

def bind(tk, bc_id):
    url = (f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind"
           f"?id={bc_id}&part=id,contentDetails&streamId={STREAM_ID}")
    res = yt_call(tk, url)
    log(f"Bind: {bc_id} → {STREAM_ID} | {res.get('id','?')}")
    return res

def listar(tk):
    log("=== ESTADO FINAL ===")
    for status in ["live", "all"]:
        data = yt_get(tk,
            f"https://www.googleapis.com/youtube/v3/liveBroadcasts"
            f"?part=id,status,snippet&broadcastStatus={status}&maxResults=20")
        items = data.get("items", [])
        if items:
            log(f"  [{status}] {len(items)} broadcasts:")
            for i in items:
                lc  = i.get("status",{}).get("lifeCycleStatus","?")
                tit = i.get("snippet",{}).get("title","?")[:60]
                log(f"    {i['id']} | {lc} | {tit}")

def main():
    log("="*55)
    log(f"LIMPAR BROADCASTS | {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    log("="*55)
    tk = get_token()
    log("Token OK")
    
    # 1. Listar o que existe
    listar(tk)
    
    # 2. Apagar tudo
    apagar_todos(tk)
    time.sleep(3)
    
    # 3. Criar 1 único broadcast EN
    bc_id = criar_broadcast_en(tk)
    if not bc_id:
        sys.exit(1)
    time.sleep(2)
    
    # 4. Bind ao stream key
    bind(tk, bc_id)
    time.sleep(2)
    
    # 5. Confirmar estado final
    listar(tk)
    log("✅ CONCLUÍDO — 1 broadcast EN criado e vinculado")

if __name__ == "__main__":
    main()
