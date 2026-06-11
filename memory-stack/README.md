# QUANTUM BRAIN MEMORY STACK v4.0
## Graphiti MCP + Obsidian Vault — Memória de Tudo com ~0 Tokens Claude

### Arquitetura de 3 Camadas

```
TIER 1 — HOT (Graphiti + FalkorDB)
  Entidades: Canal, Afiliado, Milestone, Regra, AçãoExecutada
  Busca: BM25 + semântica + graph traversal (ZERO chamadas LLM)
  Multi-tenant: group_id por domínio (channels/affiliates/rules/milestones)
  Uso: "já publiquei Short hoje?" → resposta em <100ms, ~50 tokens

TIER 2 — WARM (Obsidian Vault no GitHub)
  Vault: tafita81/Repovazio/vault/
  Acesso: section-aware (lê só ## seção, não arquivo inteiro)
  Sync: automático via GitHub Actions a cada 6h
  Uso: regras, status canais, afiliados → ~100 tokens por seção

TIER 3 — COLD (Notion + Supabase)
  Notion: docs longos, histórico, estratégia
  Supabase: estado operacional KV (last_short_date, etc.)
  Uso: documentação longa (raro)
```

### Economia de Tokens (antes vs depois)
| Operação | Antes (Notion raw) | Depois (Graphiti+Vault) | Redução |
|---|---|---|---|
| "Quais afiliados usar?" | ~3.000 tokens (página inteira) | ~150 tokens (3 entidades) | 95% |
| "Já publiquei Short hoje?" | ~500 tokens (Supabase + lógica) | ~50 tokens (Graphiti query) | 90% |
| "Qual regra anti-inauthentic?" | ~2.000 tokens (Notion page) | ~200 tokens (vault section) | 90% |
| "Status do canal CH01" | ~1.500 tokens (page completa) | ~100 tokens (section Status) | 93% |

### Deploy Rápido (5 passos)

1. **Copiar para Oracle VM via SSH:**
   ```bash
   scp -r memory-stack/ ubuntu@SEU-IP:/home/ubuntu/
   scp obsidian_mcp_server.js ubuntu@SEU-IP:/home/ubuntu/obsidian-mcp/server.js
   ```

2. **Rodar deploy script:**
   ```bash
   ssh ubuntu@SEU-IP 'bash /home/ubuntu/memory-stack/DEPLOY_ORACLE_VM.sh'
   ```

3. **Adicionar GitHub Secrets:**
   - `GRAPHITI_MCP_URL` = `http://SEU-IP:8765/sse`
   - `OBSIDIAN_MCP_URL` = `http://SEU-IP:8766/sse`
   - `ORACLE_VM_IP` = IP da Oracle VM
   - `ORACLE_SSH_KEY` = chave SSH privada

4. **Popular vault inicial:**
   ```bash
   python3 vault_init.py  # na Oracle VM
   ```

5. **Popular Graphiti:**
   - GitHub Actions → workflow_memory_stack → Run → cmd: rebuild_graphiti

### Vault Structure
```
vault/
├── channels/
│   ├── CH01.md          ← Deep Brown Noise
│   └── NEWLIFE.md       ← newlife_2day
├── affiliates/
│   └── portfolio.md     ← todos os 9 programas
├── rules/
│   ├── anti-inauthentic.md
│   ├── localizations.md
│   └── producao.md
├── infra/
│   └── secrets_required.md
└── milestones/
    └── shops.md
```

### Arquivos do Pacote
- `docker-compose.yml` → FalkorDB + Graphiti MCP
- `obsidian_mcp_server.js` → Vault MCP (filesystem-first, sem app Obsidian)
- `graphiti_client.py` → Módulo Python para quantum_master.py
- `quantum_master_v4.py` → Quantum Master integrado com memória
- `vault_init.py` → Popula vault inicial com todo conhecimento
- `DEPLOY_ORACLE_VM.sh` → Deploy em 1 comando
- `workflow_memory_stack.yml` → GitHub Actions sync vault

### Uso no Claude (próximas sessões)
Quando Rafael perguntar algo que exige contexto, Claude consulta:
1. Graphiti primeiro (estruturado, rápido, ~50 tokens)
2. Vault section se precisar texto (~100-200 tokens)
3. Notion APENAS para documentos longos (raro, >500 tokens)

**Resultado: sessões Claude usam 80-95% menos tokens em contexto.**
