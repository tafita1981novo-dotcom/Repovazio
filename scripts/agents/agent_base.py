#!/usr/bin/env python3
"""
AgentBase — Classe base para todos os agentes do swarm psicologia.doc
Usa GROQ API (GRÁTIS) como LLM. Memória compartilhada via Supabase.
Custo: R$0. Open source (MIT), inspirado no Ruflo/claude-flow.
"""
import os, json, time, urllib.request, urllib.error, urllib.parse, uuid

# ── Config ──────────────────────────────────────────────────────────────────
SBU = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
H_SB = {"apikey": SBK, "Authorization": f"Bearer {SBK}", "Content-Type": "application/json"}

GROQ_KEY   = os.environ.get("GROQ_API_KEY", "")
NVIDIA_KEY = os.environ.get("NVIDIA_API_KEY", "")

# Roteamento de modelos — 100% grátis
MODEL_FAST    = "llama-3.1-8b-instant"        # Groq: respostas simples, rápido
MODEL_DEFAULT = "llama-3.3-70b-versatile"     # Groq: padrão
MODEL_DEEP    = "deepseek-r1-distill-llama-70b"  # Groq: raciocínio profundo

AGENT_ID   = os.environ.get("AGENT_ID", f"agent-{uuid.uuid4().hex[:8]}")
AGENT_TYPE = os.environ.get("AGENT_TYPE", "generic")
SWARM_ID   = os.environ.get("SWARM_ID", f"swarm-{uuid.uuid4().hex[:8]}")

def log(msg): print(f"[{time.strftime('%H:%M:%S')}][{AGENT_TYPE}:{AGENT_ID}] {msg}", flush=True)

# ── HTTP ─────────────────────────────────────────────────────────────────────
def _http(url, method="GET", body=None, headers=None, timeout=60):
    h = dict(headers or {})
    h.setdefault("User-Agent", "psidoc-swarm/1.0")
    data = json.dumps(body).encode() if body is not None else None
    if data: h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = e.read() or b"{}"
        return e.code, (json.loads(raw) if raw.strip() else {})

# ── LLM call (Groq → Nvidia fallback, ambos gratuitos) ──────────────────────
def llm(prompt: str, system: str = "", model: str = MODEL_DEFAULT, max_tokens: int = 2000) -> str:
    """Chama LLM grátis. Groq primeiro, Nvidia como fallback."""
    messages = []
    if system: messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    # Tentativa 1: Groq
    if GROQ_KEY:
        s, r = _http("https://api.groq.com/openai/v1/chat/completions",
            method="POST",
            body={"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.7},
            headers={"Authorization": f"Bearer {GROQ_KEY}"}, timeout=30)
        if s == 200:
            return r["choices"][0]["message"]["content"].strip()
        log(f"Groq fail {s} — tentando Nvidia")

    # Fallback 2: Nvidia DeepSeek (também grátis)
    if NVIDIA_KEY:
        s, r = _http("https://integrate.api.nvidia.com/v1/chat/completions",
            method="POST",
            body={"model": "deepseek-ai/deepseek-r1", "messages": messages, "max_tokens": max_tokens},
            headers={"Authorization": f"Bearer {NVIDIA_KEY}"}, timeout=60)
        if s == 200:
            return r["choices"][0]["message"]["content"].strip()
        log(f"Nvidia fail {s}")

    raise RuntimeError("Todos os LLMs falharam — checar GROQ_API_KEY e NVIDIA_API_KEY")

# ── Memória compartilhada (Supabase como vector store) ────────────────────────
def memory_store(key: str, value: str, metadata: dict = None):
    """Salva na memória compartilhada do swarm."""
    _http(f"{SBU}/rest/v1/swarm_memory",
        method="POST",
        body={"swarm_id": SWARM_ID, "agent_id": AGENT_ID, "agent_type": AGENT_TYPE,
              "key": key, "value": value, "metadata": metadata or {}},
        headers={**H_SB, "Prefer": "resolution=merge-duplicates"})
    log(f"memory_store: {key} ({len(value)} chars)")

def memory_get(key: str, agent_id: str = None) -> str:
    """Lê da memória compartilhada."""
    q = f"swarm_id=eq.{SWARM_ID}&key=eq.{key}"
    if agent_id: q += f"&agent_id=eq.{agent_id}"
    s, r = _http(f"{SBU}/rest/v1/swarm_memory?{q}&select=value&limit=1", headers=H_SB)
    return r[0]["value"] if s == 200 and r else ""

def memory_list(agent_type: str = None) -> list:
    """Lista todas as memórias do swarm atual."""
    q = f"swarm_id=eq.{SWARM_ID}"
    if agent_type: q += f"&agent_type=eq.{agent_type}"
    s, r = _http(f"{SBU}/rest/v1/swarm_memory?{q}&select=agent_type,key,value&order=created_at.desc", headers=H_SB)
    return r if s == 200 else []

# ── Supabase helpers ──────────────────────────────────────────────────────────
def sb_select(table: str, q: str) -> list:
    s, r = _http(f"{SBU}/rest/v1/{table}?{q}", headers=H_SB)
    return r if s == 200 else []

def sb_upsert(table: str, data: dict | list):
    _http(f"{SBU}/rest/v1/{table}", method="POST",
          body=data, headers={**H_SB, "Prefer": "resolution=merge-duplicates"})

def sb_patch(table: str, q: str, data: dict):
    _http(f"{SBU}/rest/v1/{table}?{q}", method="PATCH", body=data, headers=H_SB)

# ── Swarm registro ────────────────────────────────────────────────────────────
def swarm_register(objective: str = ""):
    """Registra este agente no swarm."""
    s, r = _http(f"{SBU}/rest/v1/swarm_runs?swarm_id=eq.{SWARM_ID}", headers=H_SB)
    if s == 200 and r:
        existing = r[0].get("agents", [])
        sb_patch("swarm_runs", f"swarm_id=eq.{SWARM_ID}",
                 {"agents": existing + [{"id": AGENT_ID, "type": AGENT_TYPE, "started": time.time()}]})
    else:
        sb_upsert("swarm_runs",
                  {"swarm_id": SWARM_ID, "objective": objective,
                   "agents": [{"id": AGENT_ID, "type": AGENT_TYPE}]})
    log(f"Swarm {SWARM_ID} — registrado")

def swarm_report(result: dict):
    """Reporta resultado final do agente."""
    s, r = _http(f"{SBU}/rest/v1/swarm_runs?swarm_id=eq.{SWARM_ID}&select=results", headers=H_SB)
    results = r[0].get("results", {}) if s == 200 and r else {}
    results[AGENT_ID] = result
    sb_patch("swarm_runs", f"swarm_id=eq.{SWARM_ID}", {"results": results})
    log(f"Resultado reportado: {list(result.keys())}")
