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
          "Analise: trauma, narcisismo, TDAH adulto, apego ansioso, autossabotagem, "
          "burnout, relacionamentos toxicos, neurociencia, regulacao emocional. "
          "NUNCA use psicologa - use pesquisadora de comportamento humano.")


def supabase_insert(table, row):
    """Insert no Supabase sem depender de _http (que nao exporta com import *)."""
    url = SBU + "/rest/v1/" + table
    body = json.dumps(row).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers=H_SB)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = e.read() or b"{}"
        return e.code, (json.loads(raw) if raw.strip() else {})


def gemini_llm(prompt, max_tokens=2500):
    """Gemini 2.0 Flash - urllib direto."""
    if not GEMINI_KEY:
        raise RuntimeError("GEMINI_API_KEY ausente")
    url = ("https://generativelanguage.googleapis.com/v1beta"
           "/models/gemini-2.0-flash:generateContent?key=" + GEMINI_KEY)
    body_bytes = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7}
    }).encode()
    req = urllib.request.Request(url, data=body_bytes,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.load(r)
            return resp["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        raise RuntimeError("Gemini HTTP " + str(e.code) + ": " +
                           e.read().decode(errors="replace")[:120])


def smart_llm(prompt, max_tokens=2000):
    """Gemini Flash -> Groq llama-3.1-8b fallback."""
    try:
        return gemini_llm(prompt, max_tokens)
    except Exception as e:
        log("Gemini fail (" + str(e)[:60] + ") - fallback Groq llama-3.1-8b")
        for attempt in range(3):
            try:
                return llm(prompt, system=SYSTEM,
                           model=MODEL_FAST, max_tokens=max_tokens)
            except Exception as err:
                log("Groq attempt " + str(attempt + 1) + ": " + str(err)[:60])
                time.sleep(15 * (attempt + 1))
        raise RuntimeError("Todos LLMs falharam")


def run():
    log("=== RESEARCH AGENT | Semana " + WEEK_ID + " ===")
    swarm_register("research-agent")

    # Verificar se ja rodou esta semana
    existing = sb_select("research_opportunities",
                         "week_id=eq." + WEEK_ID + "&select=id&limit=1")
    if existing:
        log("Semana " + WEEK_ID + " ja pesquisada")
        swarm_report({"status": "already_done", "week_id": WEEK_ID})
        return

    # Performance historica para contexto
    top_videos = sb_select(
        "content_pipeline",
        "status=eq.published&select=title,viral_score"
        "&order=viral_score.desc&limit=8")
    top_ctx = "\n".join(
        "- " + v.get("title", "")[:55] + " (score: " + str(v.get("viral_score", 0)) + ")"
        for v in top_videos
    ) if top_videos else "Sem dados historicos ainda"

    prompt = (
        "Gere 16 topicos de psicologia comportamental para YouTube Brasil - semana "
        + WEEK_ID + ".\n\n"
        "TOP videos historicos (evitar repeticao):\n" + top_ctx + "\n\n"
        "Responda SOMENTE com JSON valido, sem markdown:\n"
        "{\"topics\": ["
        "{\"topic\": \"tema em 1 frase\", "
        "\"title_suggestion\": \"titulo YouTube viral max 58 chars\", "
        "\"search_volume\": \"alto|medio|baixo\", "
        "\"trend_score\": 85, "
        "\"competition\": \"alta|media|baixa\", "
        "\"content_angle\": \"angulo diferenciador 1 frase\", "
        "\"researcher_ref\": \"pesquisador ou instituicao\", "
        "\"hook\": \"primeira frase do video\", "
        "\"format\": \"short|long\", "
        "\"keywords\": [\"kw1\", \"kw2\", \"kw3\"]}, ...]\n\n"
        "Mix: 10 PT-BR + 4 EN + 2 ES. Total: exatamente 16."
    )

    log("Chamando Gemini / Groq...")
    raw = smart_llm(prompt, max_tokens=2000)

    try:
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        data  = json.loads(raw[start:end])
        topics = data.get("topics", [])
        log("Parseado: " + str(len(topics)) + " topicos")
    except Exception as e:
        log("JSON parse error: " + str(e) + " | raw[:200]: " + raw[:200])
        swarm_report({"status": "parse_error"})
        return

    saved = 0
    for t in topics:
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
        else:
            log("  SKIP status " + str(status))
        time.sleep(0.2)

    memory_store("research:" + WEEK_ID,
                 json.dumps({"saved": saved, "week": WEEK_ID}))
    swarm_report({"status": "done", "week_id": WEEK_ID, "topics_saved": saved})
    log("Research concluido: " + str(saved) + " oportunidades | semana " + WEEK_ID)


if __name__ == "__main__":
    run()
