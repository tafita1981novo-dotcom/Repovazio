#!/usr/bin/env python3
"""Criar 1 broadcast EN — apaga duplicatas residuais e cria 1 eterno"""
import os, json, urllib.request, time, sys
from datetime import datetime, timezone, timedelta

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
STREAM_ID = "SH63tBfY6wEIdkC4u4zKdg1780543868590330"

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
    req=urllib.request.Request(url,data=data,headers={"Authorization":f"Bearer {tk}","Content-Type":"application/json"},method=method)
    try:
        with urllib.request.urlopen(req,timeout=15) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        try: return json.load(e)
        except: return {"error":str(e)}
    except Exception as e: return {"error":str(e)}

def listar_todos(tk):
    todos = []
    for status in ["live","all"]:
        data = yt_get(tk, f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,status,snippet&broadcastStatus={status}&maxResults=50")
        for item in data.get("items",[]):
            bid = item["id"]
            lc  = item.get("status",{}).get("lifeCycleStatus","?")
            tit = item.get("snippet",{}).get("title","?")[:60]
            if not any(x["id"]==bid for x in todos):
                todos.append({"id":bid,"lc":lc,"title":tit})
    return todos

def apagar_residuais(tk, broadcasts):
    for b in broadcasts:
        if b["lc"] in ["live","testing","testStarting","liveStarting"]:
            yt_call(tk,f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={b['id']}&part=id",{})
            time.sleep(1.5)
        req = urllib.request.Request(f"https://www.googleapis.com/youtube/v3/liveBroadcasts?id={b['id']}",method="DELETE")
        req.add_header("Authorization",f"Bearer {tk}")
        try: urllib.request.urlopen(req,timeout=10); log(f"  Deletado residual: {b['id']}")
        except Exception as e: log(f"  Erro deletar {b['id']}: {e}")
        time.sleep(0.5)

def criar_en(tk):
    start = (datetime.now(timezone.utc)+timedelta(minutes=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "snippet":{"title":TITULO_EN[:100],"description":DESC_EN[:4900],
                   "scheduledStartTime":start,"defaultLanguage":"en"},
        "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False},
        "contentDetails":{"enableAutoStart":True,"enableAutoStop":False,"enableDvr":True,
                          "enableEmbed":True,"recordFromStart":True,"startWithSlate":False,
                          "monitorStream":{"enableMonitorStream":False}}
    }
    res = yt_call(tk,"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails",body)
    if "id" in res:
        log(f"✅ Broadcast EN criado: {res['id']}")
        return res["id"]
    log(f"❌ Falha: {res}")
    return None

def bind(tk, bc_id):
    url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id,contentDetails&streamId={STREAM_ID}"
    res = yt_call(tk, url)
    log(f"Bind {bc_id} → stream: {res.get('id','?')}")
    return "id" in res

def main():
    log("="*55)
    log(f"CRIAR 1 BROADCAST EN | {datetime.now(timezone.utc):%H:%M} UTC")
    log("="*55)
    
    tk = get_token(); log("Token OK")
    time.sleep(3)  # aguardar rate limit esfriar
    
    # Listar o que ainda existe
    atual = listar_todos(tk)
    log(f"Broadcasts existentes: {len(atual)}")
    for b in atual: log(f"  [{b['lc']}] {b['id']} — {b['title']}")
    
    # Apagar residuais
    if atual:
        log("Apagando residuais...")
        apagar_residuais(tk, atual)
        time.sleep(5)
    
    # Criar broadcast EN com retry
    bc_id = None
    for tentativa in range(1, 6):
        log(f"Tentativa {tentativa}/5 criar broadcast EN...")
        bc_id = criar_en(tk)
        if bc_id: break
        log("Rate limit — aguardando 30s...")
        time.sleep(30)
    
    if not bc_id:
        log("❌ FALHA após 5 tentativas"); sys.exit(1)
    
    time.sleep(2)
    ok = bind(tk, bc_id)
    time.sleep(2)
    
    # Confirmar
    final = listar_todos(tk)
    log(f"Estado final: {len(final)} broadcast(s)")
    for b in final: log(f"  [{b['lc']}] {b['id']} — {b['title']}")
    
    if len(final) == 1:
        log("✅ SUCESSO — 1 único broadcast EN pronto")
    else:
        log(f"⚠ {len(final)} broadcasts — verificar")

if __name__ == "__main__":
    main()
