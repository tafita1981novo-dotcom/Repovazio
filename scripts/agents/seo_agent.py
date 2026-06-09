#!/usr/bin/env python3
"""seo_agent.py - 3 variacoes titulo+desc+tags | Cron 7h00 UTC"""
import sys, os, json, time, urllib.request, urllib.error
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_base import log, llm, memory_store, SBU, H_SB, MODEL_DEFAULT, MODEL_FAST

WEEK_ID = datetime.now(timezone.utc).strftime("%Y-W%V")
SYSTEM = ("Especialista SEO YouTube psicologia PT-BR. "
          "Formulas: A)Por que X e sinal de Y  B)O que [pesquisador] descobriu  C)Voce faz isso? "
          "Descricoes 150-200 palavras. JSON valido sem markdown.")


def report(result):
    """Reporta resultado sem travar (swarm_report substituido)."""
    log("RESULTADO: " + json.dumps(result))


def sb_get(table, qs, lim=20):
    url = SBU + "/rest/v1/" + table + "?" + qs + "&limit=" + str(lim)
    req = urllib.request.Request(url, headers=H_SB)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                raw = r.read()
                return json.loads(raw) if raw.strip() else []
        except Exception as e:
            log("sb_get " + table + " (" + str(attempt+1) + "/3): " + str(e)[:60])
            time.sleep(3)
    return []


def sb_put(table, row):
    req = urllib.request.Request(SBU + "/rest/v1/" + table,
          data=json.dumps(row).encode(), method="POST", headers=H_SB)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = e.read() or b"{}"
        return e.code, (json.loads(raw) if raw.strip() else {})
    except Exception as e:
        log("sb_put: " + str(e)[:60])
        return 0, {}


def clean_json(s):
    s = s.strip()
    if s.startswith("```"):
        for p in s.split("```"):
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{"):
                return p
    i = s.find("{")
    j = s.rfind("}") + 1
    return s[i:j] if i >= 0 and j > i else s


def gerar_seo(topic, title_sug, angle, hook, keywords, fmt):
    kw = ", ".join(keywords[:4]) if keywords else topic
    prompt = ("SEO video psicologia:\nTopico: " + topic +
              "\nTitulo base: " + title_sug +
              "\nAngulo: " + angle +
              "\nHook: " + hook +
              "\nKeywords: " + kw +
              "\nFormato: " + fmt +
              '\n\n{"title_a":"max 58 chars","title_b":"max 58 chars","title_c":"max 58 chars",'
              '"best_title":"melhor dos 3","description":"150-200 palavras",'
              '"tags":["t1","t2","t3","t4","t5","t6","t7","t8"],'
              '"hashtags":"#psicologia #comportamento","thumbnail_text":"3-4 PALAVRAS"}')
    for m in [MODEL_DEFAULT, MODEL_FAST]:
        try:
            raw = llm(prompt, system=SYSTEM, model=m, max_tokens=900)
            if raw:
                return json.loads(clean_json(raw))
        except Exception as e:
            log("  LLM " + m + ": " + str(e)[:60])
            time.sleep(5)
    return None


def run():
    log("=== SEO AGENT | Semana " + WEEK_ID + " ===")

    decisions = sb_get("strategy_decisions",
                       "week_id=eq." + WEEK_ID + "&select=id,selected_topics", 1)
    if not decisions:
        log("Sem strategy — aguardando")
        report({"status": "waiting_strategy"})
        return

    decision = decisions[0]
    strategy_id = decision["id"]
    selected = decision.get("selected_topics", [])
    if isinstance(selected, str):
        selected = json.loads(selected)
    log("Strategy " + str(strategy_id)[:8] + ": " + str(len(selected)) + " topicos")

    if sb_get("seo_metadata", "strategy_decision_id=eq." + str(strategy_id) + "&select=id", 1):
        log("SEO ja gerado")
        report({"status": "already_done"})
        return

    opps_all = sb_get("research_opportunities",
                      "week_id=eq." + WEEK_ID + "&select=*", 20)
    saved = 0
    for t in selected:
        topic = t.get("topic", "")
        if not topic:
            continue
        opp = next((o for o in opps_all if topic[:25] in o.get("topic", "")),
                   opps_all[0] if opps_all else {})
        kws = opp.get("keywords", "[]")
        if isinstance(kws, str):
            kws = json.loads(kws)

        log("SEO: " + topic[:50] + "...")
        seo = gerar_seo(topic,
                        t.get("title_suggestion", opp.get("title_suggestion", topic)),
                        opp.get("content_angle", ""),
                        opp.get("hook", ""),
                        kws,
                        t.get("format", "short"))
        if not seo:
            log("  SKIP")
            continue

        status, _ = sb_put("seo_metadata", {
            "week_id":               WEEK_ID,
            "topic":                 topic[:200],
            "title_variants":        json.dumps([
                seo.get("title_a", ""),
                seo.get("title_b", ""),
                seo.get("title_c", "")
            ]),
            "best_title":            seo.get("best_title", seo.get("title_a", ""))[:100],
            "description":           seo.get("description", "")[:4900],
            "tags":                  json.dumps(seo.get("tags", [])),
            "hashtags":              seo.get("hashtags", "")[:200],
            "thumbnail_text":        seo.get("thumbnail_text", "")[:50],
            "strategy_decision_id":  strategy_id,
        })
        if status in (200, 201):
            saved += 1
            log("  OK: " + seo.get("best_title", "")[:55])
            best = seo.get("best_title", "")
            if best:
                sb_put("content_pipeline", {
                    "title":           best[:100],
                    "topic":           topic[:200],
                    "status":          "pending_generation",
                    "format":          t.get("format", "short"),
                    "target_platform": "youtube_shorts" if t.get("format") == "short" else "youtube_long",
                    "metadata": {
                        "seo_description": seo.get("description", "")[:300],
                        "tags":            seo.get("tags", []),
                        "thumbnail":       seo.get("thumbnail_text", ""),
                        "source":          "seo-agent-" + WEEK_ID,
                    }
                })
        time.sleep(1)

    memory_store("seo:" + WEEK_ID, json.dumps({"saved": saved}))
    report({"status": "done", "week_id": WEEK_ID, "seo_generated": saved})
    log("SEO concluido: " + str(saved) + " registros")


if __name__ == "__main__":
    run()
