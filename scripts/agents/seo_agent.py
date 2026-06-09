#!/usr/bin/env python3
"""
seo_agent.py — Gera 3 variações de título + description + tags + thumbnail_text
LLM: Groq Llama 3.3 70B (volume, grátis)
Input: strategy_decisions (Top 5 da semana)
Output: → seo_metadata + atualiza content_pipeline
Cron: 7h00 UTC diário
"""
import sys, os, json, time
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_base import *

WEEK_ID = datetime.now(timezone.utc).strftime("%Y-W%V")

SYSTEM = """Você é especialista em SEO para YouTube — canais de psicologia PT-BR.
Suas fórmulas de títulos que funcionam:
  A) "Por que [comportamento comum] é sinal de [problema psicológico]"
  B) "O que [pesquisador famoso] descobriu sobre [tema] vai te surpreender"  
  C) "Você faz isso? [comportamento] = [diagnóstico indireto]"
  D) "Como [trauma/problema] te impede de [coisa desejada]"
  E) "O erro que [pessoas inteligentes] cometem sobre [tema]"
Descrições: 150-200 palavras, primeiras 2 linhas com keywords principais.
Tags: 10-15 tags, mistura PT-BR + EN.
Thumbnail text: máximo 4 palavras, impacto visual."""

def gerar_seo(topic: str, title_suggestion: str, content_angle: str,
              hook: str, keywords: list, fmt: str, strategy_id: str) -> dict:
    """Gera SEO completo para 1 tópico."""
    kw_str = ", ".join(keywords[:5]) if keywords else topic

    prompt = f"""Gere SEO completo para este vídeo de psicologia:

Tópico: {topic}
Título sugerido: {title_suggestion}
Ângulo: {content_angle}
Hook (abertura): {hook}
Keywords: {kw_str}
Formato: {fmt}

Retorne JSON válido (sem markdown):
{{
  "title_a": "título fórmula A (máx 60 chars)",
  "title_b": "título fórmula B (máx 60 chars)",
  "title_c": "título fórmula C (máx 60 chars)",
  "best_title": "o título com maior CTR estimado (copie um dos 3 acima)",
  "description": "150-200 palavras. Linha 1: gancho com keyword principal. Linha 2: o que você vai aprender. Depois: contexto + call-to-action + hashtags no final",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
  "hashtags": "#psicologia #comportamento #saude_mental",
  "thumbnail_text": "3-4 PALAVRAS IMPACTO"
}}"""

    raw = llm(prompt, system=SYSTEM, model=MODEL_DEFAULT, max_tokens=1500)
    start = raw.find("{"); end = raw.rfind("}") + 1
    return json.loads(raw[start:end])

def run():
    log(f"=== SEO AGENT | Semana {WEEK_ID} ===")
    swarm_register("seo-agent")

    # Pegar decisão estratégica da semana
    decisions = sb_select("strategy_decisions",
        f"week_id=eq.{WEEK_ID}&select=id,selected_topics&limit=1")
    if not decisions:
        log("Sem strategy_decision para esta semana — aguardando strategy_agent")
        swarm_report({"status": "waiting_strategy"})
        return

    decision = decisions[0]
    strategy_id = decision["id"]
    selected_topics = decision.get("selected_topics", [])
    if isinstance(selected_topics, str):
        selected_topics = json.loads(selected_topics)

    log(f"Strategy {strategy_id}: {len(selected_topics)} tópicos")

    # Verificar se já geramos SEO para este strategy
    existing = sb_select("seo_metadata",
        f"strategy_decision_id=eq.{strategy_id}&select=id&limit=1")
    if existing:
        log("SEO já gerado para esta semana")
        swarm_report({"status": "already_done"})
        return

    # Pegar dados completos de cada tópico selecionado
    saved = 0
    for t in selected_topics:
        topic = t.get("topic", "")
        if not topic: continue

        # Buscar dados da research_opportunity
        opp = sb_select("research_opportunities",
            f"week_id=eq.{WEEK_ID}&topic=eq.{urllib.parse.quote(topic)}&select=*&limit=1")
        opp_data = opp[0] if opp else {}

        log(f"Gerando SEO: {topic[:50]}...")
        try:
            seo = gerar_seo(
                topic=topic,
                title_suggestion=t.get("title_suggestion", opp_data.get("title_suggestion", topic)),
                content_angle=opp_data.get("content_angle", ""),
                hook=opp_data.get("hook", ""),
                keywords=json.loads(opp_data.get("keywords", "[]")) if isinstance(opp_data.get("keywords"), str) else opp_data.get("keywords", []),
                fmt=t.get("format", "short"),
                strategy_id=strategy_id
            )
        except Exception as e:
            log(f"  ❌ Erro gerar SEO: {e}")
            time.sleep(2)
            continue

        # Salvar em seo_metadata
        row = {
            "week_id":               WEEK_ID,
            "topic":                 topic,
            "title_variants":        json.dumps([seo.get("title_a",""), seo.get("title_b",""), seo.get("title_c","")]),
            "best_title":            seo.get("best_title", seo.get("title_a", "")),
            "description":           seo.get("description", ""),
            "tags":                  json.dumps(seo.get("tags", [])),
            "hashtags":              seo.get("hashtags", ""),
            "thumbnail_text":        seo.get("thumbnail_text", ""),
            "strategy_decision_id":  strategy_id,
        }
        s, r = _http(f"{SBU}/rest/v1/seo_metadata", method="POST", body=row, headers=H_SB)
        if s in (200, 201):
            saved += 1
            log(f"  ✅ SEO salvo: {seo.get('best_title','')[:60]}")
        else:
            log(f"  ❌ DB error {s}: {str(r)[:80]}")

        # Opcional: criar entrada em content_pipeline se não existe
        pipeline_existing = sb_select("content_pipeline",
            f"title=eq.{urllib.parse.quote(seo.get('best_title','')[:100])}&select=id&limit=1")
        if not pipeline_existing and seo.get("best_title"):
            pipeline_row = {
                "title":         seo["best_title"][:100],
                "topic":         topic,
                "status":        "pending_generation",
                "format":        t.get("format", "short"),
                "target_platform": "youtube_shorts" if t.get("format") == "short" else "youtube_long",
                "metadata": {
                    "seo_description": seo.get("description", "")[:500],
                    "tags":            seo.get("tags", []),
                    "thumbnail_text":  seo.get("thumbnail_text", ""),
                    "source":          f"seo-agent-{WEEK_ID}",
                }
            }
            _http(f"{SBU}/rest/v1/content_pipeline", method="POST",
                  body=pipeline_row, headers=H_SB)
            log(f"  📋 Pipeline criado para: {seo['best_title'][:50]}")

        time.sleep(1)  # Rate limit

    memory_store(f"seo:{WEEK_ID}", json.dumps({"saved": saved, "week": WEEK_ID}))
    swarm_report({"status": "done", "week_id": WEEK_ID, "seo_generated": saved})
    log(f"✅ SEO Agent concluído: {saved} registros salvos")

if __name__ == "__main__":
    run()
