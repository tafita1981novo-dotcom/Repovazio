#!/usr/bin/env python3
"""pipeline_watcher.py — Verifica Supabase e dispara pipeline completo"""
import os, urllib.request, urllib.error, json, time
from datetime import datetime, timezone

SBU = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
GHP = os.environ.get("GH_PAT","")
H   = {"apikey": SBK, "Authorization": "Bearer " + SBK}
REPO = "tafita81/Repovazio"
WEEK_ID = datetime.now(timezone.utc).strftime("%Y-W%V")

def sb_ok():
    req = urllib.request.Request(
        SBU + "/rest/v1/content_pipeline?select=id&limit=1", headers=H)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            print("Supabase resp: " + str(r.status))
            return r.status == 200
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:120]
        print("sb_ok HTTP " + str(e.code) + ": " + body)
        # PGRST002 = PostgREST recarregando schema (aguardar)
        return False
    except Exception as e:
        print("sb_ok fail: " + str(e)[:80])
        return False

def dispatch(wf):
    if not GHP: return
    req = urllib.request.Request(
        "https://api.github.com/repos/"+REPO+"/actions/workflows/"+wf+"/dispatches",
        data=json.dumps({"ref":"main"}).encode(),
        headers={"Authorization":"token "+GHP,"Content-Type":"application/json"},
        method="POST")
    try:
        urllib.request.urlopen(req, timeout=10)
        print("Dispatched: " + wf)
    except Exception as e:
        print("Dispatch fail " + wf + ": " + str(e)[:60])

def has_research():
    req = urllib.request.Request(
        SBU+"/rest/v1/research_opportunities?week_id=eq."+WEEK_ID+"&select=id&limit=1",
        headers=H)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return len(json.loads(r.read())) > 0
    except: return False

def has_strategy():
    req = urllib.request.Request(
        SBU+"/rest/v1/strategy_decisions?week_id=eq."+WEEK_ID+"&select=id&limit=1",
        headers=H)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return len(json.loads(r.read())) > 0
    except: return False

def has_seo():
    req = urllib.request.Request(
        SBU+"/rest/v1/seo_metadata?week_id=eq."+WEEK_ID+"&select=id&limit=1",
        headers=H)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return len(json.loads(r.read())) > 0
    except: return False

def disable_self():
    if not GHP: return
    req = urllib.request.Request(
        "https://api.github.com/repos/"+REPO+"/actions/workflows/pipeline-watcher.yml/disable",
        data=b"{}",
        headers={"Authorization":"token "+GHP,"Content-Type":"application/json"},
        method="PUT")
    try: urllib.request.urlopen(req, timeout=10); print("Watcher desabilitado")
    except Exception as e: print("Disable fail: "+str(e)[:60])


def invoke_kill_overload():
    """Invoca a Edge Function que mata queries longas e NOTIFY PostgREST."""
    req = urllib.request.Request(
        SBU + "/functions/v1/kill-overload",
        headers=H)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
            print("kill-overload: " + json.dumps(result)[:120])
    except Exception as e:
        pass  # Non-fatal


def main():
    print("=== PIPELINE WATCHER | " + WEEK_ID + " ===")
    invoke_kill_overload()  # Forcar NOTIFY + desabilitar crons
    print("Testando Supabase...")
    if not sb_ok():
        print("Supabase ainda indisponivel")
        return
    print("Supabase OK!")

    research = has_research()
    strategy = has_strategy()
    seo      = has_seo()
    print("Estado: research=" + str(research) + " strategy=" + str(strategy) + " seo=" + str(seo))

    if not research:
        print("Falta research — disparando...")
        dispatch("research-agent.yml")
        time.sleep(180)

    if not strategy:
        print("Falta strategy — disparando...")
        dispatch("strategy-agent.yml")
        time.sleep(180)

    if not seo:
        print("Falta SEO — disparando...")
        dispatch("seo-agent.yml")
        time.sleep(5)

    dispatch("analytics-agent.yml")

    print("Pipeline disparado!")
    if has_strategy():
        print("Strategy OK — desabilitando watcher")
        disable_self()

if __name__ == "__main__":
    main()
