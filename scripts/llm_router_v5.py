#!/usr/bin/env python3
"""
llm_router_v5.py — Apenas modelos GRATUITOS, melhores primeiro
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CUSTO TOTAL: R$ 0,00

RANKING (melhor → fallback):
  #1  Groq LLaMA 3.3 70B       14.400 req/dia  GRÁTIS  ← mais rápido
  #2  NVIDIA DeepSeek V4 Pro   créditos grátis  GRÁTIS  ← mais inteligente
  #3  Gemini 2.5 Flash           500 req/dia   GRÁTIS  ← mais capaz
  #4  Gemini 2.0 Flash          2000 req/dia   GRÁTIS  ← mais rápido Google
  #5  Open Router DeepSeek      free tier       GRÁTIS  ← backup

REMOVIDOS (eram pagos):
  ✗ DeepSeek direct (api.deepseek.com)  — pago + risco segurança (empresa chinesa)
  ✗ OpenAI gpt-4o-mini                  — pago
"""
import os, requests, time
import urllib3; urllib3.disable_warnings()

GROQ    = os.getenv("GROQ_API_KEY", "")
NVIDIA  = os.getenv("NVIDIA_API_KEY", "")
GEMINI  = os.getenv("GEMINI_API_KEY", "AIzaSyDzCea_65Al-vy342xslBSVmKPv0qzTuXY")
GEMINI2 = os.getenv("GEMINI_API_KEY_NEW", "AIzaSyCo-YEPjEw3KaOllUIpJKpVwdDZA-Mr5xg")
OR      = os.getenv("OPENROUTER_API_KEY", "")

# ── MODELOS GRATUITOS RANKEADOS ────────────────────────────────────────────
MODELOS = [
    {
        "id": "groq_llama33",
        "nome": "Groq LLaMA 3.3 70B",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
        "key_env": GROQ,
        "tipo": "openai",
        "max_tokens": 8000,
        "req_dia": 14400,
        "custo": 0.0,
        "nota": "⚡ mais rápido — 14.400 req/dia grátis",
    },
    {
        "id": "nvidia_deepseek",
        "nome": "NVIDIA DeepSeek V4 Pro",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "deepseek-ai/deepseek-v3-0324",
        "key_env": NVIDIA,
        "tipo": "openai",
        "max_tokens": 4000,
        "req_dia": 1000,   # créditos free tier NVIDIA
        "custo": 0.0,
        "nota": "🧠 mais inteligente — créditos grátis NVIDIA",
    },
    {
        "id": "gemini25_flash",
        "nome": "Gemini 2.5 Flash",
        "url": None,  # usa key diretamente
        "model": "gemini-2.5-flash-preview-04-17",
        "key_env": GEMINI,
        "tipo": "gemini",
        "max_tokens": 4096,
        "req_dia": 500,
        "custo": 0.0,
        "nota": "🔮 mais capaz — 500 req/dia grátis",
    },
    {
        "id": "gemini20_flash",
        "nome": "Gemini 2.0 Flash",
        "url": None,
        "model": "gemini-2.0-flash",
        "key_env": GEMINI,
        "tipo": "gemini",
        "max_tokens": 4096,
        "req_dia": 2000,
        "custo": 0.0,
        "nota": "⚡ rápido Google — 2.000 req/dia grátis",
    },
    {
        "id": "gemini20_flash_backup",
        "nome": "Gemini 2.0 Flash (key2)",
        "url": None,
        "model": "gemini-2.0-flash",
        "key_env": GEMINI2,
        "tipo": "gemini",
        "max_tokens": 4096,
        "req_dia": 2000,
        "custo": 0.0,
        "nota": "🔄 backup key2 — +2.000 req/dia",
    },
    {
        "id": "openrouter_free",
        "nome": "Open Router DeepSeek (free)",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "key_env": OR,
        "tipo": "openai",
        "max_tokens": 2000,
        "req_dia": 999,
        "custo": 0.0,
        "nota": "🌐 Open Router free tier — backup final",
    },
]

# Rotas por tipo de tarefa — sempre free, melhor primeiro
ROTAS = {
    "script":    ["groq_llama33", "nvidia_deepseek", "gemini25_flash", "gemini20_flash"],
    "titulo":    ["groq_llama33", "nvidia_deepseek", "gemini20_flash"],
    "analise":   ["nvidia_deepseek", "gemini25_flash", "groq_llama33"],
    "imersivo":  ["groq_llama33", "nvidia_deepseek", "gemini25_flash"],
    "reflexivo": ["groq_llama33", "nvidia_deepseek", "gemini20_flash"],
    "afiliado":  ["groq_llama33", "gemini20_flash"],
    "cientifico":["nvidia_deepseek", "gemini25_flash", "groq_llama33"],
    "default":   ["groq_llama33", "nvidia_deepseek", "gemini25_flash", "gemini20_flash"],
}

_stats = {"chamadas":0, "successes":0, "por_modelo":{}}

def _modelo_by_id(mid):
    return next((m for m in MODELOS if m["id"]==mid), None)

def _chamar_openai(m, prompt, max_tokens, temperature):
    if not m["key_env"]: return None
    r = requests.post(m["url"],
        headers={"Authorization":f"Bearer {m['key_env']}",
                 "Content-Type":"application/json"},
        json={"model":m["model"],
              "messages":[{"role":"user","content":prompt}],
              "max_tokens":min(max_tokens, m["max_tokens"]),
              "temperature":temperature},
        timeout=25, verify=False)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"].strip()
    return None

def _chamar_gemini(m, prompt, max_tokens, temperature):
    key = m["key_env"]
    if not key: return None
    model = m["model"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    r = requests.post(url,
        json={"contents":[{"role":"user","parts":[{"text":prompt}]}],
              "generationConfig":{"maxOutputTokens":min(max_tokens, m["max_tokens"]),
                                  "temperature":temperature}},
        timeout=25, verify=False)
    if r.status_code == 200:
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    return None

def completar(prompt, tarefa="default", max_tokens=300, temperature=0.82):
    """Chama modelos gratuitos em ordem até obter resposta."""
    cadeia = ROTAS.get(tarefa, ROTAS["default"])
    _stats["chamadas"] += 1
    for mid in cadeia:
        m = _modelo_by_id(mid)
        if not m or not m["key_env"]: continue
        try:
            if m["tipo"] == "gemini":
                texto = _chamar_gemini(m, prompt, max_tokens, temperature)
            else:
                texto = _chamar_openai(m, prompt, max_tokens, temperature)
            if texto:
                _stats["successes"] += 1
                _stats["por_modelo"][m["nome"]] = _stats["por_modelo"].get(m["nome"],0)+1
                return texto
        except Exception as e:
            pass  # tenta próximo
        time.sleep(0.3)
    return None

def listar_modelos():
    """Imprime ranking dos modelos gratuitos."""
    print("\n=== LLM ROUTER V5 — APENAS GRÁTIS ===")
    for i, m in enumerate(MODELOS, 1):
        key_ok = "✅" if m["key_env"] else "❌"
        print(f"  #{i} {key_ok} {m['nome']:30} {m['req_dia']:6} req/dia  {m['nota']}")
    print(f"\n  Custo total: R$ 0,00")
    print("="*45)

def stats():
    return {
        "chamadas": _stats["chamadas"],
        "successes": _stats["successes"],
        "por_modelo": _stats["por_modelo"],
        "custo_usd": 0.0,
    }

if __name__ == "__main__":
    listar_modelos()
    print("\n--- Testando cadeia ---")
    testes = [
        ("script",    "Escreva 1 frase sobre narcisismo em PT-BR, reflexivo."),
        ("titulo",    "Dê 2 títulos virais sobre burnout em PT-BR, máx 10 palavras."),
        ("cientifico","O que é apego ansioso? Responda em 40 palavras PT-BR."),
    ]
    for tarefa, prompt in testes:
        print(f"\n  [{tarefa}]")
        resp = completar(prompt, tarefa=tarefa, max_tokens=150, temperature=0.82)
        print(f"  → {resp[:100] if resp else 'sem resposta'}...")
        time.sleep(1)
    s = stats()
    print(f"\n  ✅ {s['successes']}/{s['chamadas']} OK | $0,00")
    print(f"  Uso: {s['por_modelo']}")
