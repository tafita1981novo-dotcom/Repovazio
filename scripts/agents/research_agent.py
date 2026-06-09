#!/usr/bin/env python3
"""
research_agent.py - Pesquisa 16 topicos de psicologia com score
LLM: Gemini 2.0 Flash -> Groq llama-3.1-8b (fallback)
Output: research_opportunities (Supabase)
Cron: 6h00 UTC diario
"""
import sys, os, json, time, urllib.request, urllib.error
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_base import (
    log, llm, sb_select, swarm_register, swarm_report, memory_store,
    SBU, H_SB, MODEL_FAST
)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
WEEK_ID    = datetime.now(timezone.utc).strftime("%Y-W%V")

SYSTEM = ("Voce e especialista em tendencias YouTube psicologia Brasil 2026. "
          "NUNCA use psicologa - use pesquisadora de comportamento humano. "
          "Responda SOMENTE em JSON valido, sem markdown, sem texto extra.")


def supabase_insert(table, row):
    url = SBU + "/rest/v1/" + table
    body = json.dumps(row).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers=H_SB)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = e.read() or b"{}"
        return e.code, (json.loads(raw) if raw.strip() else {})


def clean_json(raw):
    """Remove markdown e extrai JSON."""
    s = raw.strip()
    # Remover ```json...```
    if s.startswith("```"):
        parts = s.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{") or p.startswith("["):
                s = p
                break
    start = s.find("{")
    end   = s.rfind("}") + 1
    if start >= 0 and end > start:
        return s[start:end]
    return s


def gemini_llm(prompt, max_tokens=3000):
    if not GEMINI_KEY:
        raise RuntimeError("GEMINI_API_KEY ausente")
    url = ("https://generativelanguage.googleapis.com/v1beta"
           "/models/gemini-2.0-flash:generateContent?key=" + GEMINI_KEY)
    body_bytes = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.6}
    }).encode()
    req = urllib.request.Request(url, data=body_bytes,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.load(r)
            return resp["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        raise RuntimeError("Gemini HTTP " + str(e.code) + ": " +
                           e.read().decode(errors="replace")[:80])


def smart_llm(prompt, max_tokens=3000):
    """Gemini -> Groq fallback."""
    try:
        return gemini_llm(prompt, max_tokens)
    except Exception as e:
        log("Gemini fail - fallback Groq: " + str(e)[:60])
        for attempt in range(3):
            try:
                return llm(prompt, system=SYSTEM, model=MODEL_FAST,
                           max_tokens=max_tokens)
            except Exception as err:
                log("Groq attempt " + str(attempt + 1) + ": " + str(err)[:60])
                time.sleep(15)
        raise RuntimeError("Todos LLMs falharam")


def pedir_batch(n, idioma, top_ctx, week):
    """Pede N topicos de uma vez (menor prompt = menos truncamento)."""
    prompt = (
        "Gere " + str(n) + " topicos para YouTube psicologia " + idioma + " - " + week + ".\n"
        "Evitar (ja temos): " + top_ctx[:200] + "\n\n"
        "JSON somente, sem markdown:\n"
        "{\"topics\": ["
        "{\"topic\": \"tema 1 frase\", "
        "\"title_suggestion\": \"titulo max 58 chars\", "
        "\"search_volume\": \"alto|medio|baixo\", "
        "\"trend_score\": 80, "
        "\"competition\": \"alta|media|baixa\", "
        "\"content_angle\": \"diferencial 1 frase\", "
        "\"researcher_ref\": \"pesquisador\", "
        "\"hook\": \"primeira frase\", "
        "\"format\": \"short|long\", "
        "\"keywords\": [\"k1\",\"k2\",\"k3\"]}]}"
    )
    raw = smart_llm(prompt, max_tokens=2500)
    cleaned = clean_json(raw)
    data = json.loads(cleaned)
    return data.get("topics", [])


def run():
    log("=== RESEARCH AGENT | Semana " + WEEK_ID + " ===")
    swarm_register("research-agent")

    existing = sb_select("research_opportunities",
                         "week_id=eq." + WEEK_ID + "&select=id&limit=1")
    if existing:
        log("Semana " + WEEK_ID + " ja pesquisada")
        swarm_report({"status": "already_done", "week_id": WEEK_ID})
        return

    top_videos = sb_select(
        "content_pipeline",
        "status=eq.published&select=title&order=viral_score.desc&limit=8")
    top_ctx = ", ".join(v.get("title", "")[:30] for v in top_videos) if top_videos else ""

    all_topics = []
    # Batch 1: 8 topicos PT-BR
    try:
        log("Batch 1: 8 topicos PT-BR...")
        t1 = pedir_batch(8, "PT-BR", top_ctx, WEEK_ID)
        all_topics.extend(t1)
        log("  OK: " + str(len(t1)) + " topicos")
    except Exception as e:
        log("Batch 1 falhou: " + str(e)[:100])
    time.sleep(3)

    # Batch 2: 6 PT-BR + 2 EN
    try:
        log("Batch 2: 6 PT-BR + 2 EN...")
        t2 = pedir_batch(8, "PT-BR e 2 em EN", top_ctx, WEEK_ID)
        all_topics.extend(t2)
        log("  OK: " + str(len(t2)) + " topicos")
    except Exception as e:
        log("Batch 2 falhou: " + str(e)[:100])

    log("Total topicos obtidos: " + str(len(all_topics)))

    saved = 0
    for t in all_topics:
        if not t.get("topic"):
            continue
        row = {
            "week_id":          WEEK_ID,
            "topic":            t.get("topic", "")[:200],
            "title_suggestion": t.get("title_suggestion", "")[:100],
            "search_volume":    t.get("search_volume", "medio"),
            "trend_score":      float(t.get("trend_score", 50)),
            "competition":      t.get("competition", "media"),
            "content_angle":    t.get("content_angle", "")[:300],
            "researcher_ref":   t.get("researcher_ref", "")[:200],
            "hook":             t.get("hook", "")[:300],
            "format":           t.get("format", "short"),
            "keywords":         json.dumps(t.get("keywords", [])),
        }
        status, _ = supabase_insert("research_opportunities", row)
        if status in (200, 201):
            saved += 1
            log("  OK [" + str(int(t.get("trend_score", 0))) + "] " +
                t.get("topic", "")[:55])
        time.sleep(0.3)

    memory_store("research:" + WEEK_ID,
                 json.dumps({"saved": saved, "week": WEEK_ID}))
    swarm_report({"status": "done", "week_id": WEEK_ID, "topics_saved": saved})
    log("Research concluido: " + str(saved) + " topicos salvos para " + WEEK_ID)


if __name__ == "__main__":
    run()
