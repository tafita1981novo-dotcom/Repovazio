#!/usr/bin/env python3
"""
research_agent.py — Pesquisa 16 tópicos de psicologia com score
LLM: Gemini 2.0 Flash (grátis, 1M tokens/dia)
Fallback: Groq DeepSeek R1
Output: → research_opportunities (Supabase)
Cron: 6h00 UTC diário
"""
import sys, os, json, time
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_base import *

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

WEEK_ID = datetime.now(timezone.utc).strftime("%Y-W%V")

SYSTEM = """Você é um especialista em tendências de conteúdo psicologia no YouTube Brasil 2026.
Analise o que está crescendo: trauma, narcisismo, TDAH adulto, apego ansioso, autossabotagem,
burnout, relacionamentos tóxicos, neurociência comportamental, regulação emocional.
NUNCA use a palavra "psicóloga" — use "pesquisadora de comportamento humano".
Foco em PT-BR mas considere oportunidades EN para audiência global."""

def gemini_llm(prompt: str, max_tokens: int = 4000) -> str:
    """Gemini 2.0 Flash — 1M tokens/dia grátis."""
    if not GEMINI_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.8}
    }
    s, r = _http(url, method="POST", body=body)
    if s == 200:
        return r["candidates"][0]["content"]["parts"][0]["text"].strip()
    raise RuntimeError(f"Gemini fail {s}: {r}")

def smart_llm(prompt: str, max_tokens: int = 4000) -> str:
    """Gemini primeiro, DeepSeek R1 como fallback."""
    try:
        return gemini_llm(prompt, max_tokens)
    except Exception as e:
        log(f"Gemini fail ({e}) — usando DeepSeek R1")
        return llm(prompt, system=SYSTEM, model=MODEL_DEEP, max_tokens=max_tokens)

def run():
    log(f"=== RESEARCH AGENT | Semana {WEEK_ID} ===")
    swarm_register("research-agent")

    # Verificar se já rodou esta semana
    existing = sb_select("research_opportunities",
        f"week_id=eq.{WEEK_ID}&select=id&limit=1")
    if existing:
        log(f"Semana {WEEK_ID} já pesquisada — {len(existing)} oportunidades")
        swarm_report({"status": "already_done", "week_id": WEEK_ID})
        return

    # Puxar performance histórica para contextualizar
    top_videos = sb_select("content_pipeline",
        "status=eq.published&select=title,viral_score,quality_score_current"
        "&order=viral_score.desc&limit=10")
    top_context = "\n".join([f"- {v.get('title','')[:60]} (score: {v.get('viral_score',0)})"
                              for v in top_videos]) if top_videos else "Sem dados históricos"

    prompt = f"""Pesquise 16 tópicos de psicologia comportamental para YouTube Brasil — semana {WEEK_ID}.

TOP vídeos históricos do canal (para não repetir e entender o que funciona):
{top_context}

Para cada tópico, analise:
1. Volume de busca estimado no YouTube Brasil
2. Concorrência (quantos canais grandes cobrem o tema)
3. Ângulo único que nos diferencia
4. Score de oportunidade 0-100

Responda SOMENTE em JSON válido, sem markdown:
{{
  "topics": [
    {{
      "topic": "tema central em 1 frase",
      "title_suggestion": "título YouTube viral (gancho forte, max 60 chars)",
      "search_volume": "alto|médio|baixo",
      "trend_score": 85,
      "competition": "alta|média|baixa",
      "content_angle": "ângulo único de 1 frase que nos diferencia",
      "researcher_ref": "nome do pesquisador ou instituição a citar",
      "hook": "primeira frase do vídeo (prende em 3s)",
      "format": "short|long",
      "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
  ]
}}

Priorizar: trauma + TDAH + narcisismo + autossabotagem + sono + ansiedade performance.
Incluir 4 tópicos em EN para audiência global.
Total: exatamente 16 tópicos."""

    log("Chamando Gemini 2.0 Flash...")
    raw = smart_llm(prompt, max_tokens=4000)

    try:
        start = raw.find("{"); end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])
        topics = data.get("topics", [])
        log(f"Parseado: {len(topics)} tópicos")
    except Exception as e:
        log(f"JSON parse error: {e}\nRaw: {raw[:200]}")
        swarm_report({"status": "parse_error"})
        return

    # Salvar em research_opportunities
    saved = 0
    for t in topics:
        if not t.get("topic"): continue
        row = {
            "week_id":         WEEK_ID,
            "topic":           t.get("topic", ""),
            "title_suggestion": t.get("title_suggestion", ""),
            "search_volume":   t.get("search_volume", "médio"),
            "trend_score":     float(t.get("trend_score", 50)),
            "competition":     t.get("competition", "média"),
            "content_angle":   t.get("content_angle", ""),
            "researcher_ref":  t.get("researcher_ref", ""),
            "hook":            t.get("hook", ""),
            "format":          t.get("format", "short"),
            "keywords":        json.dumps(t.get("keywords", [])),
        }
        s, r = _http(f"{SBU}/rest/v1/research_opportunities",
                     method="POST", body=row, headers=H_SB)
        if s in (200, 201):
            saved += 1
            log(f"  ✅ [{t.get('trend_score',0):.0f}] {t.get('topic','')[:60]}")
        else:
            log(f"  ❌ Erro {s}: {str(r)[:80]}")
        time.sleep(0.2)

    memory_store(f"research:{WEEK_ID}", json.dumps({"saved": saved, "week": WEEK_ID}))
    swarm_report({"status": "done", "week_id": WEEK_ID, "topics_saved": saved})
    log(f"✅ Research concluído: {saved} oportunidades salvas para semana {WEEK_ID}")

if __name__ == "__main__":
    run()
