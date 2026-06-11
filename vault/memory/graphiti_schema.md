---
tipo: referencia_tecnica
categoria: knowledge_graph
---

## Group IDs (multi-tenant Graphiti)
- channels: fatos sobre canais YouTube (subs, watch hours, acoes)
- affiliates: performance e status de programas afiliados
- rules: regras operacionais, politicas YouTube, compliance
- milestones: progresso de metas e shops
- system: estado do sistema, ultimas acoes executadas

## Entidades Principais
- Canal: id, nome, nicho, subs, watch_hours, status, last_short
- Afiliado: id, comissao, EPC, conversao, status, fit_niches
- Milestone: tipo, requisito_atual, progresso, elegivel_br, data_atingido
- Regra: categoria, resumo, data_descoberta, fonte
- AcaoExecutada: tipo, canal_id, data_utc, resultado, video_id

## Relacoes Temporais
- Canal HAS_AFFILIATE afiliado (ativo no canal)
- Canal ALCANCOU milestone (em data X)
- AcaoExecutada FOI_EM canal (em data Y)
- Regra APLICA_A canal / tipo_conteudo

## Como Consultar (quantum_master_v4.py)

### Verificar Short ja publicado hoje
already_posted_short_today("CH01")
=> graphiti_query("Short publicado CH01 2026-06-11", group_id="channels")

### Afiliados para niche
get_best_affiliates_for_niche("brown_noise adhd")
=> graphiti_query("afiliados tier 1 fit brown_noise", group_id="affiliates")

### Gravar milestone atingido
graphiti_add("Canal CH01 atingiu 500 subscribers em 2026-08-15", group_id="milestones")

### Buscar regra especifica
get_rule("anti-inauthentic")
=> graphiti_query("regra anti-inauthentic youtube", group_id="rules")

## Economia de Tokens (antes vs depois)
| Operacao | Antes Notion | Depois Graphiti | Reducao |
|---|---|---|---|
| Afiliados para niche | 3000 tokens | 150 tokens | 95% |
| Short ja publicado hoje? | 500 tokens | 50 tokens | 90% |
| Regra anti-inauthentic | 2000 tokens | 200 tokens | 90% |
| Status do canal CH01 | 1500 tokens | 100 tokens | 93% |

## Deploy
- FalkorDB porta 6379 (Redis protocol)
- Graphiti MCP porta 8765/sse
- Obsidian MCP porta 8766/sse
- docker-compose up -d na Oracle VM (sa-saopaulo-1)
- LLM provider: Groq (gratis, llama-3.3-70b)
