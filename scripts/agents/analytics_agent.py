#!/usr/bin/env python3
"""
analytics_agent.py - Stats YouTube reais + atualiza cerebro_knowledge
LLM: Groq llama-3.3-70b
Cron: 8h00 UTC diario
"""
import sys, os, json, time, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_base import (
    log, llm, sb_select, swarm_register, swarm_report, memory_store,
    SBU, H_SB, MODEL_DEFAULT, MODEL_FAST
)

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY","")
WEEK_ID = datetime.now(timezone.utc).strftime("%Y-W%V")
TODAY   = datetime.now(timezone.utc).strftime("%Y-%m-%d")
SYSTEM  = ("Analista de performance canal psicologia.doc. "
           "Identifique padroes sucesso/fracasso baseados em dados reais. "
           "Responda SOMENTE JSON valido sem markdown.")

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

def yt_stats(ids):
    if not YOUTUBE_API_KEY or not ids: return {}
    url = ("https://www.googleapis.com/youtube/v3/videos"
           "?part=statistics,snippet&id="+",".join(ids[:50])+"&key="+YOUTUBE_API_KEY)
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.load(r)
    except Exception as e: log("YouTube API: "+str(e)[:80]); return {}
    return {item["id"]: {
        "title": item.get("snippet",{}).get("title",""),
        "views": int(item.get("statistics",{}).get("viewCount",0)),
        "likes": int(item.get("statistics",{}).get("likeCount",0)),
    } for item in data.get("items",[])}

def run():
    log("=== ANALYTICS AGENT | "+TODAY+" ===")
    try: swarm_register("analytics-agent")
    except Exception as e: log("swarm_register skip: "+str(e)[:50])

    cutoff = (datetime.now(timezone.utc)-timedelta(days=30)).isoformat()
    published = sb_select("content_pipeline",
        "status=eq.published&published_at=gte."+cutoff
        +"&select=id,title,youtube_id,youtube_long_id,format,viral_score"
        "&order=published_at.desc&limit=50")
    log("Videos 30d: "+str(len(published)))
    if not published: swarm_report({"status":"no_data"}); return

    yt_ids = list({v.get("youtube_id") or v.get("youtube_long_id","") for v in published if v.get("youtube_id") or v.get("youtube_long_id")})
    real   = yt_stats(yt_ids)
    log("Stats reais: "+str(len(real)))

    video_data = []
    for v in published:
        vid = v.get("youtube_id") or v.get("youtube_long_id","")
        yt  = real.get(vid,{})
        video_data.append({"title":v.get("title","")[:55],"format":v.get("format","?"),
                           "score":v.get("viral_score",0),"views":yt.get("views","N/A")})

    wv = sorted([x for x in video_data if isinstance(x["views"],int)], key=lambda x:x["views"], reverse=True)
    top_ctx = "\n".join("+"+str(v["views"])+"v | "+v["title"]+" | "+v["format"] for v in wv[:5]) or "Sem dados reais"
    bot_ctx = "\n".join("-"+str(v["views"])+"v | "+v["title"]+" | "+v["format"] for v in wv[-5:]) if len(wv)>=5 else ""

    cerebro = sb_select("cerebro_knowledge","select=titulo,categoria,confidence_score&order=confidence_score.desc&limit=8")
    cerebro_ctx = "\n".join("["+c.get("categoria","")+"| "+str(c.get("confidence_score",0))+"] "+c.get("titulo","")[:80] for c in cerebro) if cerebro else "Sem dados"

    prompt = ("Analise performance 30d canal psicologia.doc.\n\n"
              "TOP 5:\n"+top_ctx+"\n\nBOTTOM 5:\n"+(bot_ctx or "sem dados")+
              "\n\nCEREBRO ATUAL:\n"+cerebro_ctx+
              "\n\nTotal: "+str(len(published))+" videos | "+str(len(wv))+" com dados.\n\n"
              "Extraia 3-5 insights NOVOS (que o cerebro ainda nao sabe).\n"
              'JSON: {"insights":[{"category":"title|format|topic|timing|thumbnail|engagement",'
              '"insight":"max 100 chars","confidence":75,"evidence":"1 frase","action":"1 frase"}],'
              '"weekly_summary":"2 frases"}')

    log("Analisando...")
    try:
        raw  = llm(prompt, system=SYSTEM, model=MODEL_DEFAULT, max_tokens=1000)
        data = json.loads(clean_json(raw))
        insights = data.get("insights",[]); summary = data.get("weekly_summary","")
    except Exception as e: log("LLM/parse: "+str(e)[:100]); swarm_report({"status":"error"}); return

    log(str(len(insights))+" insights extraidos")
    saved = 0
    for ins in insights:
        if not ins.get("insight"): continue
        status, _ = sb_insert("cerebro_knowledge", {
            "categoria":          ins.get("category","performance"),
            "subcategoria":       ins.get("category","algorithm"),
            "titulo":             ins["insight"][:120],
            "conteudo":           {"insight":ins["insight"],"evidence":ins.get("evidence",""),
                                   "action":ins.get("action",""),"week":WEEK_ID},
            "fonte":              "analytics-agent-"+WEEK_ID,
            "confidence_score":   int(ins.get("confidence",70)),
            "aprendido_em":       TODAY,
            "ultima_verificacao": TODAY,
            "ativo":              True,
        })
        if status in (200,201):
            saved+=1; log("  OK ["+ins.get("category","")+"] "+ins["insight"][:55])

    memory_store("analytics:"+WEEK_ID, json.dumps({"summary":summary,"insights":saved}))
    swarm_report({"status":"done","week_id":WEEK_ID,"insights_saved":saved,"videos":len(published)})
    log("Resumo: "+summary[:100])
    log("Analytics concluido: "+str(saved)+" insights -> cerebro_knowledge")

if __name__ == "__main__":
    run()
