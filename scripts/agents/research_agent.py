#!/usr/bin/env python3
"""
research_agent.py - Pesquisa 16 topicos de psicologia com score
LLM: Gemini 2.0 Flash (gratis, 1M tokens/dia)
Fallback: Groq llama-3.1-8b-instant
Output: research_opportunities (Supabase)
Cron: 6h00 UTC diario
"""
import sys, os, json, time, urllib.request, urllib.error
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_base import (
    log, llm, sb_select, sb_upsert, sb_patch, swarm_register, swarm_report,
    memory_store, SBU, H_SB, SWARM_ID, AGENT_ID, MODEL_FAST, MODEL_DEFAULT
)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
WEEK_ID    = datetime.now(timezone.utc).strftime("%Y-W%V")

SYSTEM = """Voce e especialista em tendencias de conteudo psicologia no YouTube Brasil 2026.
Analise: trauma, narcisismo, TDAH adulto, apego ansioso, autossabotagem,
burnout, relacionamentos toxicos, neuociencia comportamental, regulacao emocional.
NUNCA use "psicologa" - use "pesquisadora de comportamento humano".
Foco PT-BR mas inclua oportunidades EN para audiencia global."""


def gemini_llm(prompt, max_tokens=3000):
    """Gemini 2.0 Flash - urllib direto, sem _http."""
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
        log("Gemini fail (" + str(e)[:60] + ") - fallback Groq")
        for attempt in range(3):
            try:
                return llm(prompt, system=SYSTEM,
                           model=MODEL_FAST, max_tokens=max_tokens)
            except Exception as err:
                log("Groq attempt " + str(attempt + 1) + " fail: " + str(err)[:60])
                time.sleep(20)
        raise RuntimeError("Todos os LLMs falharam")


def run():
    log("=== RESEARCH AGENT | Semana " + WEEK_ID + " ===")
    swarm_register("research-agent")

    # Verificar se ja rodou esta semana
    existing = sb_select("research_opportunities",
                         "week_id=eq." + WEEK_ID + "&select=id&limit=1")
    if existing:
        log("Semana " + WEEK_ID + " ja pesquisada (" +
            str(len(existing)) + " oportunidades)")
        swarm_report({"status": "already_done", "week_id": WEEK_ID})
        return

    # Performance historica
    top_videos = sb_select(
        "content_pipeline",
        "status=eq.published&select=title,viral_score"
        "&order=viral_score.desc&limit=10")
    top_ctx = "\n".join(
        "- " + v.get("title", "")[:55] + " (score: " + str(v.get("viral_score", 0)) + ")"
        for v in top_videos
    ) if top_videos else "Sem dados historicos"

    prompt = (
        "Pesquise 16 topicos de psicologia comportamental para YouTube Brasil - semana "
        + WEEK_ID + ".\n\n"
        "TOP videos historicos do canal (nao repetir):\n" + top_ctx + "\n\n"
        "Para cada topico retorne JSON com:\n"
        "topic, title_suggestion (max 60 chars), search_volume (alto/medio/baixo), "
        "trend_score (0-100), competition (alta/media/baixa), content_angle (1 frase), "
        "researcher_ref, hook (1 frase), format (short ou long), keywords (lista 3-5)\n\n"
        "Responda SOMENTE em JSON valido:\n"
        "{\"topics\": [{...}, ...]}\n\n"
        "Priorizar: trauma, TDAH, narcisismo, autossabotagem, sono, ansiedade performance.\n"
        "Incluir 4 topicos em EN. Total: exatamente 16 topicos."
    )

    log("Chamando LLM...")
    raw = smart_llm(prompt, max_tokens=2500)

    try:
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        data  = json.loads(raw[start:end])
        topics = data.get("topics", [])
        log("Parseado: " + str(len(topics)) + " topicos")
    except Exception as e:
        log("JSON parse error: " + str(e) + " | raw: " + raw[:200])
        swarm_report({"status": "parse_error"})
        return

    saved = 0
    for t in topics:
        if not t.get("topic"):
            continue
        row = {
            "week_id":         WEEK_ID,
            "topic":           t.get("topic", ""),
            "title_suggestion": t.get("title_suggestion", ""),
            "search_volume":   t.get("search_volume", "medio"),
            "trend_score":     float(t.get("trend_score", 50)),
            "competition":     t.get("competition", "media"),
            "content_angle":   t.get("content_angle", ""),
            "researcher_ref":  t.get("researcher_ref", ""),
            "hook":            t.get("hook", ""),
            "format":          t.get("format", "short"),
            "keywords":        json.dumps(t.get("keywords", [])),
        }
        s, _ = __import__("agents.agent_base", fromlist=["_http"])._http(
            SBU + "/rest/v1/research_opportunities",
            method="POST", body=row, headers=H_SB)
        if s in (200, 201):
            saved += 1
            log("  OK [" + str(t.get("trend_score", 0)) + "] " + t.get("topic", "")[:55])
        time.sleep(0.2)

    memory_store("research:" + WEEK_ID,
                 json.dumps({"saved": saved, "week": WEEK_ID}))
    swarm_report({"status": "done", "week_id": WEEK_ID, "topics_saved": saved})
    log("Research concluido: " + str(saved) + " oportunidades salvas")


if __name__ == "__main__":
    run()
