#!/usr/bin/env python3
"""Criar 1 broadcast EN — apaga residuais e cria 1 eterno. Auto-dispara live ao criar."""
import os, json, urllib.request, time, sys
from datetime import datetime, timezone, timedelta

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
GH_PAT           = os.environ.get("GH_PAT", "")
STREAM_ID        = "SH63tBfY6wEIdkC4u4zKdg1780543868590330"
LIVE_WF_ID       = "288922095"
CRON_WF_FILE     = "criar-broadcast-unico.yml"
REPO             = "tafita81/Repovazio"

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

def get_yt_token():
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
            if not any(x["id"]==bid for x in todos):
                todos.append({"id":bid,
                               "lc":item.get("status",{}).get("lifeCycleStatus","?"),
                               "title":item.get("snippet",{}).get("title","?")[:60]})
    return todos

def apagar_residuais(tk, broadcasts):
    for b in broadcasts:
        if b["lc"] in ["live","testing","testStarting","liveStarting"]:
            yt_call(tk,f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={b['id']}&part=id",{})
            time.sleep(1.5)
        req = urllib.request.Request(f"https://www.googleapis.com/youtube/v3/liveBroadcasts?id={b['id']}",method="DELETE")
        req.add_header("Authorization",f"Bearer {tk}")
        try: urllib.request.urlopen(req,timeout=10); log(f"  ✅ Deletado: {b['id']}")
        except Exception as e: log(f"  ⚠ Erro: {e}")
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
    err = res.get("error",{})
    reason = err.get("errors",[{}])[0].get("reason","?") if "errors" in err else "?"
    log(f"❌ Falha [{reason}]: {err.get('message','?')[:80]}")
    return None

def dispatch_live(gh_token):
    """Dispara o workflow principal da live"""
    if not gh_token: return
    body = json.dumps({"ref":"main"}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/workflows/{LIVE_WF_ID}/dispatches",
        data=body, headers={"Authorization":f"token {gh_token}","Content-Type":"application/json"},
        method="POST")
    try:
        urllib.request.urlopen(req,timeout=10)
        log(f"✅ Live dispatch enviado (wf {LIVE_WF_ID})")
    except Exception as e:
        log(f"⚠ Dispatch live falhou: {e}")

def desabilitar_cron(gh_token):
    """Desabilita este workflow de cron após sucesso"""
    if not gh_token: return
    raw = urllib.request.urlopen(urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/workflows",
        headers={"Authorization":f"token {gh_token}"}),timeout=10).read()
    wfs = json.loads(raw).get("workflows",[])
    for w in wfs:
        if CRON_WF_FILE in w.get("path",""):
            wid = w["id"]
            req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/actions/workflows/{wid}/disable",
                data=b"{}",headers={"Authorization":f"token {gh_token}","Content-Type":"application/json"},method="PUT")
            try:
                urllib.request.urlopen(req,timeout=10)
                log(f"✅ Cron desabilitado (wf {wid})")
            except Exception as e:
                log(f"⚠ Desabilitar cron: {e}")
            break

def bind(tk, bc_id):
    url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id,contentDetails&streamId={STREAM_ID}"
    res = yt_call(tk, url)
    ok = "id" in res
    log(f"Bind {bc_id}: {'✅' if ok else '❌ ' + str(res)[:60]}")
    return ok

def main():
    log("="*55)
    log(f"CRIAR BROADCAST EN | {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    log("="*55)
    
    tk = get_yt_token(); log("Token OK")
    
    # Verificar se já existe um broadcast
    atual = listar_todos(tk)
    if len(atual) == 1:
        b = atual[0]
        log(f"✅ Já existe 1 broadcast [{b['lc']}]: {b['id']} — {b['title']}")
        log("Disparando live e encerrando...")
        dispatch_live(GH_PAT)
        desabilitar_cron(GH_PAT)
        return
    
    log(f"Broadcasts existentes: {len(atual)}")
    if len(atual) > 1:
        log("Apagando residuais extras...")
        apagar_residuais(tk, atual)
        time.sleep(5)
    
    # Criar com 1 tentativa (cron vai retentar a cada 30min se falhar)
    log("Tentando criar broadcast EN...")
    bc_id = criar_en(tk)
    
    if not bc_id:
        log("Rate limit ativo — cron vai retentar em 30min automaticamente")
        sys.exit(0)  # Exit 0 para não falhar o run (cron vai tentar de novo)
    
    time.sleep(2)
    bind(tk, bc_id)
    time.sleep(2)
    
    # Confirmar
    final = listar_todos(tk)
    log(f"Estado final: {len(final)} broadcast(s)")
    for b in final: log(f"  [{b['lc']}] {b['id']} — {b['title']}")
    
    if any(b["id"]==bc_id for b in final):
        log("✅ SUCESSO — 1 broadcast EN criado!")
        dispatch_live(GH_PAT)   # Inicia a live imediatamente
        desabilitar_cron(GH_PAT)  # Desabilita este cron
    else:
        log("⚠ Broadcast não confirmado na listagem — cron vai verificar")

if __name__ == "__main__":
    main()
