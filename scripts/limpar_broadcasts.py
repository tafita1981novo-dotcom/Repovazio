#!/usr/bin/env python3
"""Criar 1 broadcast EN + dispara live imediatamente"""
import os, json, urllib.request, time, sys
from datetime import datetime, timezone, timedelta

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
GH_PAT           = os.environ.get("GH_PAT","")
STREAM_ID        = "SH63tBfY6wEIdkC4u4zKdg1780543868590330"
LIVE_WF_ID       = "288922095"
REPO             = "tafita81/Repovazio"
CRON_WF_FILE     = "criar-broadcast-unico.yml"

TITULO_EN = "🔴 LIVE 24/7 | White Noise & Brown Noise for Sleep, Focus & Study | Daniela Coelho"
DESC_EN = """🔴 LIVE 24/7 | WHITE NOISE & BROWN NOISE | Sleep · Focus · Study · ADHD
Daniela Coelho — Human Behavior Researcher | @psidanicoelho
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Use HEADPHONES for the best experience
🤍 WHITE NOISE — covers all background sounds, perfect for sleep & concentration
🟤 BROWN NOISE — deep, rumbling bass, loved by people with ADHD & anxiety
🌙 Mix: 40% White + 60% Brown — scientifically proven for deep sleep
😴 Deep sleep & insomnia | 🧠 ADHD focus | 📚 Study | 🏢 Productivity | 👶 Baby sleep
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 AO VIVO 24H | Ruído Branco e Marrom para Dormir e Concentrar
🔴 EN VIVO 24H | Ruido Blanco y Marrón para Dormir y Estudiar
🔴 LIVE 24/7 | Weißes & Braunes Rauschen zum Schlafen & Lernen
🔴 EN DIRECT 24H | Bruit Blanc & Brun pour Dormir et Étudier
🔴 24時間ライブ | ホワイトノイズ＆ブラウンノイズ 睡眠・集中
🔴 24小时直播 | 白噪音和棕噪音 助眠专注学习
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#whitenoise #brownnoise #sleep #focus #ADHD #study #liveradio
#noiseblanc #ruidobranco #weisesrauschen #whitenoisesleep #brownnoisefocus
#睡眠 #집중 #수면 #whitenoise24hours #brownnoisesleep"""

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
    req=urllib.request.Request(url,data=data,headers={
        "Authorization":f"Bearer {tk}","Content-Type":"application/json"},method=method)
    try:
        with urllib.request.urlopen(req,timeout=15) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        try: return json.load(e)
        except: return {"error":str(e)}
    except Exception as e: return {"error":str(e)}

def listar(tk):
    todos=[]
    for status in ["live","all"]:
        data=yt_get(tk,f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,status,snippet&broadcastStatus={status}&maxResults=20")
        for item in data.get("items",[]):
            bid=item["id"]
            if not any(x["id"]==bid for x in todos):
                todos.append({"id":bid,"lc":item.get("status",{}).get("lifeCycleStatus","?"),
                               "title":item.get("snippet",{}).get("title","?")[:70]})
    return todos

def criar_en(tk):
    start=(datetime.now(timezone.utc)+timedelta(minutes=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body={
        "snippet":{"title":TITULO_EN[:100],"description":DESC_EN[:4900],
                   "scheduledStartTime":start,"defaultLanguage":"en"},
        "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False},
        "contentDetails":{"enableAutoStart":True,"enableAutoStop":False,"enableDvr":True,
                          "enableEmbed":True,"recordFromStart":True,"startWithSlate":False,
                          "monitorStream":{"enableMonitorStream":False}}
    }
    res=yt_call(tk,"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails",body)
    if "id" in res:
        log(f"✅ Broadcast criado: {res['id']} — EN")
        return res["id"]
    err=res.get("error",{})
    log(f"❌ [{err.get('errors',[{}])[0].get('reason','?')}] {err.get('message','?')[:80]}")
    return None

def bind(tk,bc_id):
    url=f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id,contentDetails&streamId={STREAM_ID}"
    res=yt_call(tk,url)
    log(f"Bind: {'✅' if 'id' in res else '❌ '+str(res)[:60]}")
    return "id" in res

def dispatch_live(gh):
    if not gh: return
    body=json.dumps({"ref":"main"}).encode()
    req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/actions/workflows/{LIVE_WF_ID}/dispatches",
                                data=body,headers={"Authorization":f"token {gh}","Content-Type":"application/json"},method="POST")
    try:
        urllib.request.urlopen(req,timeout=10)
        log("✅ Live disparada!")
    except Exception as e: log(f"⚠ Dispatch: {e}")

def desabilitar_cron(gh):
    if not gh: return
    try:
        raw=urllib.request.urlopen(urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/actions/workflows",
            headers={"Authorization":f"token {gh}"}),timeout=10).read()
        for w in json.loads(raw).get("workflows",[]):
            if CRON_WF_FILE in w.get("path",""):
                req=urllib.request.Request(
                    f"https://api.github.com/repos/{REPO}/actions/workflows/{w['id']}/disable",
                    data=b"{}",headers={"Authorization":f"token {gh}","Content-Type":"application/json"},method="PUT")
                urllib.request.urlopen(req,timeout=10)
                log(f"✅ Cron desabilitado ({w['id']})")
                break
    except Exception as e: log(f"⚠ Desabilitar cron: {e}")

def main():
    log("="*55)
    log(f"CRIAR BROADCAST EN | {datetime.now(timezone.utc):%H:%M} UTC")
    log("="*55)
    tk=get_yt_token(); log("Token OK")

    # Ver o que existe
    atual=listar(tk)
    log(f"Broadcasts existentes: {len(atual)}")
    for b in atual: log(f"  [{b['lc']}] {b['id']} — {b['title']}")

    # Se já tem 1 em EN, só dispara live
    if len(atual)==1 and "LIVE 24/7 | White Noise" in atual[0]["title"]:
        log("Já existe 1 broadcast EN correto — só disparando live")
        dispatch_live(GH_PAT)
        desabilitar_cron(GH_PAT)
        return

    # Criar EN (com retry)
    bc_id=None
    for t in range(1,8):
        log(f"Tentativa {t}/7...")
        bc_id=criar_en(tk)
        if bc_id: break
        log("Rate limit — aguardando 60s...")
        time.sleep(60)

    if not bc_id:
        log("Rate limit persiste — cron vai retentar em 30min"); sys.exit(0)

    time.sleep(2)
    bind(tk,bc_id)
    time.sleep(2)

    # Confirmar
    final=listar(tk)
    log(f"\nEstado final: {len(final)} broadcast(s)")
    for b in final: log(f"  [{b['lc']}] {b['id']} — {b['title']}")

    if any(b["id"]==bc_id for b in final):
        log("✅ SUCESSO!")
        dispatch_live(GH_PAT)
        desabilitar_cron(GH_PAT)
    else:
        log("⚠ Não confirmado — cron vai verificar")

if __name__=="__main__":
    main()
