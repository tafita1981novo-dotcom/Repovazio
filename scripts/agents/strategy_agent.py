#!/usr/bin/env python3
"""
strategy_agent.py — Escolhe Top 5 tópicos da semana + plano de publicação
LLM: Groq DeepSeek R1 (raciocínio profundo, grátis)
Input: research_opportunities + content_pipeline histórico
Output: → strategy_decisions (Supabase)
Cron: 6h30 UTC diário
"""
import sys, os, json, time
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_base import *

WEEK_ID = datetime.now(timezone.utc).strftime("%Y-W%V")

SYSTEM = """Você é o estrategista de conteúdo do canal psicologia.doc.
Seu trabalho: escolher os 5 tópicos com MAIOR potencial de crescimento desta semana,
considerando algoritmo YouTube, sazonalidade, performance histórica do canal e 
tendências de busca. Pense como um editor de canal que já teve vídeos com 100k+ views.
Raciocine passo a passo antes de decidir."""

def run():
    log(f"=== STRATEGY AGENT | Semana {WEEK_ID} ===")
    swarm_register("strategy-agent")

    # Verificar se já existe decisão esta semana
    existing = sb_select("strategy_decisions", f"week_id=eq.{WEEK_ID}&select=id&limit=1")
    if existing:
        log(f"Estratégia {WEEK_ID} já definida")
        swarm_report({"status": "already_done", "week_id": WEEK_ID})
        return

    # 1. Pegar oportunidades da semana atual
    opportunities = sb_select("research_opportunities",
        f"week_id=eq.{WEEK_ID}&used=eq.false"
        "&select=id,topic,title_suggestion,trend_score,search_volume,competition,content_angle,format,keywords"
        "&order=trend_score.desc&limit=20")

    if not opportunities:
        log("Sem research_opportunities para esta semana — aguardando research_agent")
        swarm_report({"status": "waiting_research"})
        return

    log(f"{len(opportunities)} oportunidades encontradas")

    # 2. Performance histórica dos últimos 30 vídeos
    history = sb_select("content_pipeline",
        "status=in.(published,mp4_ready)&select=title,format,viral_score,quality_score_current,pub_order"
        "&order=viral_score.desc&limit=30")

    # 3. Conhecimento do cérebro autônomo
    cerebro = sb_select("cerebro_knowledge",
        "select=insight,category,confidence&order=confidence.desc&limit=10")
    cerebro_ctx = "\n".join([f"- [{c.get('category','')}] {c.get('insight','')[:100]}"
                              for c in cerebro]) if cerebro else "Sem dados"

    history_ctx = "\n".join([
        f"- {h.get('title','')[:50]} | score={h.get('viral_score',0)} | format={h.get('format','?')}"
        for h in history
    ]) if history else "Sem histórico"

    opps_ctx = "\n".join([
        f"  {i+1}. [{o.get('trend_score',0):.0f}pts] {o.get('topic','')} | "
        f"busca={o.get('search_volume','')} concorrência={o.get('competition','')} | "
        f"formato={o.get('format','')} | ângulo: {o.get('content_angle','')[:60]}"
        for i, o in enumerate(opportunities)
    ])

    prompt = f"""Analise e escolha os TOP 5 tópicos para publicar esta semana ({WEEK_ID}).

=== OPORTUNIDADES DE PESQUISA ({len(opportunities)} candidatos) ===
{opps_ctx}

=== PERFORMANCE HISTÓRICA (top 30 vídeos) ===
{history_ctx}

=== INSIGHTS DO CÉREBRO AUTÔNOMO ===
{cerebro_ctx}

Critérios de seleção (em ordem de prioridade):
1. Oportunidade de busca alta + concorrência média/baixa = melhor ROI
2. Diversidade de formatos (mix shorts + longs)
3. Progressão narrativa (tópicos que se complementam na semana)
4. Alinhamento com padrões de sucesso histórico

Responda em JSON válido (sem markdown):
{{
  "selected_topics": [
    {{
      "rank": 1,
      "topic": "...",
      "title_suggestion": "...",
      "format": "short|long",
      "publish_day": "segunda|terça|quarta|quinta|sexta",
      "reason": "por que este tópico esta semana (1 frase)"
    }}
  ],
  "rationale": "raciocínio geral da seleção (3-4 frases)",
  "expected_views": 15000
}}"""

    log("Consultando DeepSeek R1...")
    raw = llm(prompt, system=SYSTEM, model=MODEL_DEEP, max_tokens=2000)

    try:
        start = raw.find("{"); end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])
    except Exception as e:
        log(f"JSON parse error: {e}")
        swarm_report({"status": "parse_error"})
        return

    selected = data.get("selected_topics", [])
    log(f"Top {len(selected)} tópicos selecionados")
    for t in selected:
        log(f"  #{t.get('rank',0)} [{t.get('format','')}] {t.get('topic','')[:60]}")

    # Salvar decisão
    row = {
        "week_id":          WEEK_ID,
        "selected_topics":  json.dumps(selected),
        "rationale":        data.get("rationale", ""),
        "expected_views":   int(data.get("expected_views", 0)),
        "performance_data": json.dumps({"history_count": len(history), "opps_count": len(opportunities)})
    }
    s, r = _http(f"{SBU}/rest/v1/strategy_decisions",
                 method="POST", body=row, headers=H_SB)
    if s not in (200, 201):
        log(f"❌ Erro salvar strategy: {s} {r}")
        swarm_report({"status": "db_error"})
        return

    strategy_id = r.get("id") if isinstance(r, dict) else None
    log(f"✅ Decisão salva (id={strategy_id})")

    # Marcar oportunidades como usadas
    for t in selected:
        topic = t.get("topic", "")
        matching = [o for o in opportunities if o.get("topic","") == topic]
        for m in matching:
            _http(f"{SBU}/rest/v1/research_opportunities?id=eq.{m['id']}",
                  method="PATCH", body={"used": True}, headers=H_SB)

    memory_store(f"strategy:{WEEK_ID}",
                 json.dumps({"topics": [t["topic"] for t in selected], "id": strategy_id}))
    swarm_report({"status": "done", "week_id": WEEK_ID, "topics": len(selected),
                  "strategy_id": strategy_id})
    log(f"✅ Estratégia {WEEK_ID} definida: {len(selected)} tópicos")

if __name__ == "__main__":
    run()
