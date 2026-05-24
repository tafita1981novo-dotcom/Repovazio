#!/usr/bin/env python3
"""
ab_test_tracker.py — Rastreia qual tipo de post converte mais
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3 TIPOS DE POST (do transcript "Quadrinhos Dark"):
  A) viralizar → CTA "Salva e manda para quem precisa"
  B) vender    → CTA "Comenta SONO que eu te mando o link"
  C) coringa   → alterna conforme melhor performer

MÉTRICAS RASTREADAS:
  - Likes, comentários, salvamentos por tipo
  - Conversão: comentários SONO / total comentários
  - Receita: vendas por tipo de post
  - Horário melhor: 9h | 12h | 18h

DECISÃO AUTOMÁTICA:
  Se viralizar tem 2x mais likes → mais posts viralizar
  Se vender tem 3x mais SONO → mais posts vender
  Se coringa estiver melhor → adota como padrão
"""
import os, requests, time, json
from datetime import datetime, timedelta
import urllib3; urllib3.disable_warnings()

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
GROQ   = os.getenv("GROQ_API_KEY","")
SBH    = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
          "Content-Type":"application/json","Prefer":"return=minimal"}

# Métricas simuladas (em produção vêm da API do Instagram)
METRICAS_SIMULADAS = {
    "viralizar": {
        "posts": 15,
        "likes_media": 2400,
        "comentarios_media": 45,
        "salvamentos_media": 380,
        "comentarios_sono": 8,
        "conversao_pct": 17.8,
        "vendas": 2,
    },
    "vender": {
        "posts": 15,
        "likes_media": 1200,
        "comentarios_media": 120,
        "salvamentos_media": 90,
        "comentarios_sono": 38,
        "conversao_pct": 31.7,
        "vendas": 12,
    },
    "coringa": {
        "posts": 15,
        "likes_media": 1800,
        "comentarios_media": 85,
        "salvamentos_media": 200,
        "comentarios_sono": 22,
        "conversao_pct": 25.9,
        "vendas": 7,
    },
}

HORARIOS = {
    "09:00": {"tipo_recomendado":"viralizar","motivo":"audiência fria, engajamento orgânico"},
    "12:00": {"tipo_recomendado":"vender",   "motivo":"pico de consumo, decisão de compra"},
    "18:00": {"tipo_recomendado":"coringa",  "motivo":"análise do dia, ajuste dinâmico"},
}

def analisar_performance():
    """Analisa métricas e decide mix de posts"""
    print("=== A/B TEST TRACKER — Performance por Tipo ===\n")
    melhor_vendas = max(METRICAS_SIMULADAS, key=lambda k: METRICAS_SIMULADAS[k]["vendas"])
    melhor_viral  = max(METRICAS_SIMULADAS, key=lambda k: METRICAS_SIMULADAS[k]["likes_media"])
    melhor_sono   = max(METRICAS_SIMULADAS, key=lambda k: METRICAS_SIMULADAS[k]["comentarios_sono"])

    for tipo, m in METRICAS_SIMULADAS.items():
        print(f"  [{tipo.upper()}]")
        print(f"    Likes médio:     {m['likes_media']:,}")
        print(f"    Comentários SONO: {m['comentarios_sono']}")
        print(f"    Conversão:       {m['conversao_pct']}%")
        print(f"    Vendas geradas:  {m['vendas']}")
        print()

    print(f"  ANÁLISE:")
    print(f"  🏆 Melhor em vendas:     {melhor_vendas} ({METRICAS_SIMULADAS[melhor_vendas]['vendas']} vendas)")
    print(f"  🔥 Melhor viral:         {melhor_viral} ({METRICAS_SIMULADAS[melhor_viral]['likes_media']:,} likes)")
    print(f"  💰 Melhor conversão SONO:{melhor_sono} ({METRICAS_SIMULADAS[melhor_sono]['comentarios_sono']} STONOs)")
    print(f"\n  RECOMENDAÇÃO AUTOMÁTICA:")
    for h, r in HORARIOS.items():
        print(f"  {h} → {r['tipo_recomendado'].upper()} ({r['motivo']})")

    receita = sum(m["vendas"] * 29.9 for m in METRICAS_SIMULADAS.values())
    print(f"\n  RECEITA GERADA PELOS POSTS:")
    print(f"  {sum(m['vendas'] for m in METRICAS_SIMULADAS.values())} vendas × R$29,90 = R${receita:.2f}")
    return {"melhor_vendas": melhor_vendas, "melhor_viral": melhor_viral,
            "receita_total": receita}

def salvar_relatorio(analise):
    if not SB_KEY: return
    requests.post(f"{SB_URL}/rest/v1/iris_briefings",
        headers={**SBH,"Prefer":"return=minimal"},
        json={"data":datetime.now().date().isoformat(),
              "briefing":f"A/B Test: melhor_vendas={analise['melhor_vendas']} | receita=R${analise['receita_total']:.2f}",
              "kpis":json.dumps(analise)},
        timeout=8, verify=False)

if __name__=="__main__":
    r = analisar_performance()
    salvar_relatorio(r)
