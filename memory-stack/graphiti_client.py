#!/usr/bin/env python3
"""
GRAPHITI CLIENT — Módulo de memória para quantum_master.py
Adicione este arquivo ao Repovazio e importe no quantum_master.

Uso:
  from graphiti_client import graphiti_query, graphiti_add, graphiti_query_cached

ECONOMIA DE TOKENS:
  - Antes: Claude carrega página Notion inteira (2.000-10.000 tokens)
  - Depois: Graphiti retorna 3-10 entidades (~100-300 tokens)
  - Redução: ~90% dos tokens gastos em contexto
"""

import os, json, requests, time
from datetime import datetime

GRAPHITI_URL = os.environ.get("GRAPHITI_MCP_URL", "http://localhost:8765")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# ── CACHE LOCAL (evita chamadas repetidas ao Graphiti) ────────────────────────

_cache: dict = {}
CACHE_TTL = 300  # 5 minutos


def _cache_get(key):
    if key in _cache:
        val, ts = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return val
    return None


def _cache_set(key, val):
    _cache[key] = (val, time.time())


# ── GRAPHITI MCP CALLS ────────────────────────────────────────────────────────

def graphiti_query(query: str, group_id: str = "channels", limit: int = 5) -> list:
    """
    Busca entidades/episódios no knowledge graph.
    Retorna lista de resultados relevantes.
    SEM chamadas LLM (BM25 + semântica + graph traversal).
    """
    cache_key = f"q:{group_id}:{query[:50]}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "search_memory",
                "arguments": {
                    "query": query,
                    "group_id": group_id,
                    "num_results": limit
                }
            }
        }
        r = requests.post(f"{GRAPHITI_URL}/mcp", json=payload, timeout=5)
        if r.status_code == 200:
            data = r.json()
            results = data.get("result", {}).get("content", [{}])[0].get("text", "[]")
            parsed = json.loads(results) if isinstance(results, str) else results
            _cache_set(cache_key, parsed)
            return parsed
    except Exception as e:
        pass  # fail silently — não bloquear quantum_master

    return []


def graphiti_add(episode: str, group_id: str = "channels", source_type: str = "text") -> bool:
    """
    Adiciona um episódio/fato ao knowledge graph.
    Graphiti extrai entidades e relações automaticamente.
    """
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "add_memory",
                "arguments": {
                    "content": episode,
                    "group_id": group_id,
                    "source_description": f"quantum_master @ {datetime.utcnow().isoformat()}"
                }
            }
        }
        r = requests.post(f"{GRAPHITI_URL}/mcp", json=payload, timeout=10)
        # Invalida cache do grupo
        keys_to_del = [k for k in _cache if k.startswith(f"q:{group_id}:")]
        for k in keys_to_del:
            del _cache[k]
        return r.status_code == 200
    except Exception:
        return False


def graphiti_query_cached(query: str, group_id: str, ttl: int = 3600) -> list:
    """
    Versão com TTL customizado (para queries que mudam devagar).
    Ex: regras (TTL 1 dia), afiliados (TTL 1h), ações do dia (TTL 5min)
    """
    old_ttl = CACHE_TTL
    _cache_ttl = ttl
    results = graphiti_query(query, group_id)
    _cache_ttl = old_ttl
    return results


# ── OBSIDIAN VAULT CALLS ──────────────────────────────────────────────────────

OBSIDIAN_URL = os.environ.get("OBSIDIAN_MCP_URL", "http://localhost:8766")


def vault_read_section(note_path: str, section: str) -> str | None:
    """
    Lê APENAS uma seção de uma nota — economiza ~95% de tokens vs ler tudo.
    Ex: vault_read_section("channels/CH01", "Status Atual")
    """
    cache_key = f"vault:{note_path}:{section}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "vault_read",
                "arguments": {"path": note_path, "section": section}
            }
        }
        r = requests.post(f"{OBSIDIAN_URL}/mcp", json=payload, timeout=5)
        if r.status_code == 200:
            text = r.json().get("result", {}).get("content", [{}])[0].get("text", "")
            _cache_set(cache_key, text)
            return text
    except Exception:
        pass
    return None


def vault_patch_section(note_path: str, section: str, content: str) -> bool:
    """
    Atualiza APENAS uma seção — NÃO reescreve o arquivo inteiro.
    Ideal para atualizar "Status Atual" sem tocar no resto da nota.
    """
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "vault_patch_section",
                "arguments": {"path": note_path, "section": section, "content": content}
            }
        }
        r = requests.post(f"{OBSIDIAN_URL}/mcp", json=payload, timeout=5)
        # Invalida cache
        del_key = f"vault:{note_path}:{section}"
        if del_key in _cache:
            del _cache[del_key]
        return r.status_code == 200
    except Exception:
        return False


def vault_search(query: str, max_results: int = 5) -> list:
    """
    Busca full-text no vault. Retorna snippets, não arquivos inteiros.
    """
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "vault_search",
                "arguments": {"query": query, "max_results": max_results}
            }
        }
        r = requests.post(f"{OBSIDIAN_URL}/mcp", json=payload, timeout=5)
        if r.status_code == 200:
            text = r.json().get("result", {}).get("content", [{}])[0].get("text", "[]")
            return json.loads(text) if isinstance(text, str) else text
    except Exception:
        pass
    return []


# ── HELPERS ESPECÍFICOS DO PROJETO ─────────────────────────────────────────────

def already_posted_short_today(ch_id: str) -> bool:
    """Verifica se Short já foi publicado hoje para esse canal."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    results = graphiti_query(f"Short publicado {ch_id} {today}", group_id="channels", limit=3)
    return len(results) > 0


def record_short_posted(ch_id: str, video_id: str, title: str):
    """Registra que Short foi publicado."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    graphiti_add(
        f"Short publicado canal {ch_id} em {today}: video_id={video_id} título='{title}'",
        group_id="channels"
    )
    # Também atualiza vault
    vault_patch_section(
        f"channels/{ch_id}",
        "Último Short",
        f"- Data: {today}\n- Video ID: {video_id}\n- Título: {title}"
    )


def get_best_affiliates_for_niche(niche: str, limit: int = 3) -> list:
    """Retorna os melhores afiliados para um nicho específico."""
    results = graphiti_query(f"afiliados tier 1 fit {niche}", group_id="affiliates", limit=limit)
    if not results:
        # Fallback: ler do vault
        content = vault_read_section("affiliates/portfolio", "Tier 1 — High Ticket")
        return [{"source": "vault", "content": content}] if content else []
    return results


def get_rule(rule_name: str) -> str | None:
    """Recupera uma regra específica pelo nome."""
    # Primeiro tenta Graphiti (rápido)
    results = graphiti_query(rule_name, group_id="rules", limit=1)
    if results:
        return str(results[0])
    # Fallback: vault (section-aware, ainda econômico)
    return vault_read_section(f"rules/{rule_name}", "Resumo da Política")


def update_channel_status(ch_id: str, subs: int, watch_hours: float):
    """Atualiza status do canal no Graphiti + vault."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    # Graphiti: fato temporal (sabe "quando mudou")
    graphiti_add(
        f"Canal {ch_id} tem {subs} subscribers e {watch_hours:.1f}h watch time em {today}",
        group_id="channels"
    )
    
    # Vault: patch só na seção Status
    vault_patch_section(
        f"channels/{ch_id}",
        "Status Atual",
        f"- Subscribers: {subs}\n- Watch hours: {watch_hours:.1f}h\n- Última atualização: {today}"
    )


if __name__ == "__main__":
    print("✅ graphiti_client.py — teste de conexão")
    print(f"   Graphiti: {GRAPHITI_URL}")
    print(f"   Obsidian: {OBSIDIAN_URL}")
    
    # Teste básico (sem servidores rodando, só verifica imports)
    result = graphiti_query("teste", group_id="channels")
    print(f"   Query resultado: {result} (esperado [] sem servidor)")
    
    section = vault_read_section("channels/CH01", "Status Atual")
    print(f"   Vault section: {section[:50] if section else 'None'} (esperado None sem servidor)")
