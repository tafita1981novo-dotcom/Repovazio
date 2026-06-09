#!/usr/bin/env python3
"""
strategy_agent.py - Escolhe Top 5 topicos da semana
LLM: Groq llama-3.3-70b fallback llama-3.1-8b
Cron: 6h30 UTC diario
"""
import sys, os, json, time, urllib.request, urllib.error
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_base import (
    log, llm, sb_select, swarm_register, swarm_report, memory_store,
    SBU, H_SB, MODEL_DEFAULT, MODEL_FAST
)

WEEK_ID = datetime.now(timezone.utc).strftime("%Y-W%V")
SYSTEM  = "Estrategista YouTube psicologia.doc. Escolha TOP 5 topicos da semana por potencial de crescimento. Responda SOMENTE JSON valido sem markdown."

def sb_insert(table, row):
    req = urllib.request.Request(SBU+"/rest/v1/"+table,
          data=json.dumps(row).encode(), method="POST", headers=H_SB)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw=r.read(); return r.status,(json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw=e.read() or b"{}"; return e.code,(json.loads(raw) if raw.strip() else {})

def clean_json(s):
    s=s.strip()
    if s.startswith("```"):
        for p in s.split("```"):
            p=p.strip()
            if p.startswith("json"): p=p[4:].strip()
            if p.startswith("{"): return p
    i=s.find("{"); j=s.rfind("}")+1
    return s[i:j] if i>=0 and j>i else s

def smart_llm(prompt, max_tokens=1200):
    for m in [MODEL_DEFAULT, MODEL_FAST]:
        try:
            r=llm(prompt, system=SYSTEM, model=m, max_tokens=max_tokens)
            if r: return r
        except Exception as e:
            log("LLM "+m+": "+str(e)[:60]); time.sleep(8)
    raise RuntimeError("Todos LLMs falharam")

def run():
    log("=== STRATEGY AGENT | Semana "+WEEK_ID+" ===")
    try: swarm_register("strategy-agent")
    except Exception as e: log("swarm_register skip: "+str(e)[:50])

    if sb_select("strategy_decisions","week_id=eq."+WEEK_ID+"&select=id&limit=1"):
        log("Ja decidido"); swarm_report({"status":"already_done"}); return

    opps = sb_select("research_opportunities",
        "week_id=eq."+WEEK_ID+"&used=eq.false"
        "&select=id,topic,title_suggestion,trend_score,search_volume,competition,format"
        "&order=trend_score.desc&limit=16")
    if not opps:
        log("Sem oportunidades"); swarm_report({"status":"waiting_research"}); return

    hist = sb_select("content_pipeline",
        "status=in.(published,mp4_ready)&select=title,format,viral_score"
        "&order=viral_score.desc&limit=10")
    hist_ctx = ", ".join(h.get("title","")[:30] for h in hist) if hist else "sem dados"
    opps_ctx = "\n".join(
        str(i+1)+". ["+str(int(o.get("trend_score",50)))+"pts] "+o.get("topic","")[:55]+
        " | busca="+o.get("search_volume","")+" | "+o.get("competition","")+" | "+o.get("format","short")
        for i,o in enumerate(opps))

    prompt = ("TOP 5 topicos para semana "+WEEK_ID+".\n\nOPORTUNIDADES:\n"+opps_ctx+
              "\n\nHISTORICO: "+hist_ctx+
              "\n\nCriterios: busca alta, concorrencia baixa/media, diversidade formatos.\n\n"
              'JSON: {"selected_topics":[{"rank":1,"topic":"...","title_suggestion":"...","format":"short|long","publish_day":"segunda|terca|quarta|quinta|sexta","reason":"1 frase"}],"rationale":"2 frases","expected_views":10000}')

    log("Consultando LLM..."); 
    try: data = json.loads(clean_json(smart_llm(prompt)))
    except Exception as e: log("Erro: "+str(e)[:100]); swarm_report({"status":"error"}); return

    selected = data.get("selected_topics",[])
    log("Selecionados: "+str(len(selected)))
    for t in selected: log("  #"+str(t.get("rank",0))+" "+t.get("topic","")[:55])

    status, resp = sb_insert("strategy_decisions", {
        "week_id":          WEEK_ID,
        "selected_topics":  json.dumps(selected),
        "rationale":        data.get("rationale","")[:500],
        "expected_views":   int(data.get("expected_views",0)),
        "performance_data": json.dumps({"opps":len(opps),"hist":len(hist)})
    })
    if status not in (200,201): log("DB error "+str(status)); swarm_report({"status":"db_error"}); return

    strategy_id = resp.get("id","")
    # Marcar opps como usadas
    for t in selected:
        for o in opps:
            if o.get("topic","") == t.get("topic",""):
                try:
                    req=urllib.request.Request(SBU+"/rest/v1/research_opportunities?id=eq."+o["id"],
                        data=json.dumps({"used":True}).encode(),method="PATCH",headers=H_SB)
                    urllib.request.urlopen(req,timeout=10)
                except: pass

    memory_store("strategy:"+WEEK_ID, json.dumps({"topics":[t["topic"] for t in selected],"id":strategy_id}))
    swarm_report({"status":"done","week_id":WEEK_ID,"topics":len(selected)})
    log("Strategy concluido: "+str(len(selected))+" topicos | id="+str(strategy_id)[:8])

if __name__ == "__main__":
    run()
