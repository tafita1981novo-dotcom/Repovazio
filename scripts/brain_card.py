#!/usr/bin/env python3
"""
brain_card.py — Gerador do Cartão do Cérebro Quântico
Execute este script para gerar o bloco de contexto que deve
ser colado em qualquer novo chat do Claude para carregar o
cérebro quântico completo.

Uso:
  python3 scripts/brain_card.py
  python3 scripts/brain_card.py --full   # com lista de APIs
  python3 scripts/brain_card.py --stats  # só estatísticas
"""

import requests, json, sys, os

SB_URL = os.getenv("SUPABASE_URL", "https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

CARD_TEMPLATE = """
╔══════════════════════════════════════════════════════════════╗
║  🧠 CÉREBRO QUÂNTICO psicologia.doc — CONTEXTO ATIVO       ║
╚══════════════════════════════════════════════════════════════╝

PROJETO: psicologia.doc (@psidanielacoelho)
INFRA:   Supabase tpjvalzwkqwttvmszvie | Vercel repovazio.vercel.app
         GitHub tafita81/Repovazio

API BRAIN (banco vivo Supabase):
  ✅ {total} APIs mapeadas
  ✅ {sem_auth} sem autenticação
  ✅ {alta_rel} alta relevância (★★★)
  ✅ {categorias} categorias
  ✅ {fontes} diretórios/fontes
  ✅ {testadas} testadas ao vivo

CONSULTAR O CÉREBRO:
  SQL:    SELECT * FROM find_api('tts', no_auth:=true);
  Python: from scripts.api_brain import Brain; Brain.search('quotes')
  REST:   GET {sb_url}/rest/v1/v_apis_psico

TOP 10 CATEGORIAS:
{top_cats}

PIPELINE ATIVO:
  LLM:   NVIDIA DeepSeek V4 Pro → Groq → OpenAI (LLMRouter V2)
  TTS:   Chatterbox (Short) | Edge TTS Thalita (Long)
  IMG:   Pollinations FLUX sequential
  VIDEO: FFmpeg Ken Burns | Remotion React (novo)
  DB:    Supabase | CI: GitHub Actions

CANAL: UCyCkIpsVgME9yCj_oXJFheA (psidanielacoelho1982@gmail.com)
⛔ NUNCA publicar em: UCSH63tBfY6wEIdkC4u4zKdg (BLOQUEADO)

Script Brain: https://github.com/tafita81/Repovazio/blob/main/scripts/api_brain.py
═══════════════════════════════════════════════════════════════
"""

def get_stats():
    if not SB_KEY:
        return {"total": "?", "sem_auth": "?", "alta_rel": "?",
                "categorias": "?", "fontes": "?", "testadas": "?",
                "sb_url": SB_URL, "top_cats": "  (conecte ao Supabase)"}
    
    h = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"}
    r = requests.get(f"{SB_URL}/rest/v1/api_brain",
        headers=h, params={"select": "category,auth_type,relevance,tested,working,source",
                           "limit": "2000"}, timeout=15)
    
    if r.status_code != 200:
        return {"total": "erro", "sem_auth": "erro", "alta_rel": "erro",
                "categorias": "erro", "fontes": "erro", "testadas": "erro",
                "sb_url": SB_URL, "top_cats": "  (erro de conexão)"}
    
    data = r.json()
    cats = {}
    for row in data:
        c = row["category"]
        cats[c] = cats.get(c, 0) + 1
    
    top10 = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:10]
    top_str = "\n".join(f"  {cat:30s} {n:4d} APIs" for cat, n in top10)
    
    return {
        "total":     len(data),
        "sem_auth":  sum(1 for x in data if x["auth_type"] == "none"),
        "alta_rel":  sum(1 for x in data if x["relevance"] == 3),
        "categorias":len(set(x["category"] for x in data)),
        "fontes":    len(set(x.get("source","?") for x in data)),
        "testadas":  sum(1 for x in data if x.get("tested") and x.get("working")),
        "sb_url":    SB_URL,
        "top_cats":  top_str
    }

def generate_card(full=False, stats_only=False):
    s = get_stats()
    card = CARD_TEMPLATE.format(**s)
    
    if stats_only:
        print(f"Total: {s['total']} | Sem auth: {s['sem_auth']} | ★★★: {s['alta_rel']} | Cats: {s['categorias']}")
        return
    
    if full and SB_KEY:
        h = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"}
        r = requests.get(f"{SB_URL}/rest/v1/v_apis_psico",
            headers=h, params={"limit": "100"}, timeout=15)
        if r.status_code == 200:
            apis = r.json()
            card += "\nAPIs ALTA RELEVÂNCIA (★★★):\n"
            for a in apis:
                card += f"  [{a['category']}] {a['name']:30s} {a.get('rate_limit','')}\n"
    
    print(card)
    return card

if __name__ == "__main__":
    full  = "--full"  in sys.argv
    stats = "--stats" in sys.argv
    generate_card(full=full, stats_only=stats)
