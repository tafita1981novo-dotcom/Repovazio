# psicologia.doc — Orquestração Swarm (Ruflo-style)

## Projeto
Canal @psidanicoelho | YouTube psicologia/comportamento humano  
Persona: **Daniela Coelho** — pesquisadora de comportamento humano  
⚠️ PROIBIDO: "psicóloga/psicólogo" até jan/2027

## Infra
- **GitHub**: tafita81/Repovazio  
- **Supabase**: tpjvalzwkqwttvmszvie  
- **Vercel**: repovazio.vercel.app  
- **LLM primário**: Groq Llama 3.3 70B (GRÁTIS)  
- **LLM fallback**: Nvidia DeepSeek V3 (GRÁTIS)

## Swarm de Agentes (100% grátis)

| Agente | Arquivo | Função |
|--------|---------|--------|
| script-writer (×5) | `scripts/agents/script_writer.py` | Gera scripts completos |
| seo-optimizer (×3) | `scripts/agents/seo_optimizer.py` | Títulos YouTube SEO |
| trend-researcher | `scripts/agents/trend_researcher.py` | Pesquisa tendências |
| quality-reviewer | `scripts/agents/quality_reviewer.py` | Revisão QUALITY_STANDARD |

## Executar Swarm

### Via GitHub Actions (recomendado)
```bash
# Disparar swarm completo (10 agentes em paralelo)
gh workflow run swarm-psidoc.yml --repo tafita81/Repovazio
```

### Via Claude Code + Ruflo
```bash
# Instalar Ruflo
npx ruflo@latest init wizard
claude mcp add ruflo -- npx ruflo@latest mcp start

# Prompt para Claude Code:
```
Use o Ruflo para orquestrar o swarm psicologia.doc:
1. swarm_init com topologia mesh
2. Spawn 5 script-writers em paralelo (scripts/agents/script_writer.py)
3. Spawn 3 seo-optimizers em paralelo (scripts/agents/seo_optimizer.py)  
4. Spawn 1 trend-researcher (scripts/agents/trend_researcher.py)
5. Após writers finalizarem, spawn quality-reviewer
6. Todos salvam na swarm_memory (Supabase) para acesso compartilhado
7. Modelo simples → Groq Llama 8B | Complexo → Groq Llama 70B | Raciocínio → DeepSeek R1
```

## Memória Compartilhada (Supabase)
```python
from agents.agent_base import memory_store, memory_get, memory_list

# Salvar descoberta
memory_store("script:123", conteudo_script, {"format": "short"})

# Ler de outro agente
script = memory_get("script:123")

# Listar tudo do swarm
mems = memory_list(agent_type="script-writer")
```

## Pipeline de Produção
```
pending_generation → [script-writer] → ready_tts → [quality-reviewer] → 
[tts-pipeline] → audio_ready → [render-mp4-v3] → mp4_ready → 
[seo-optimizer] → pending_credentials → [yt-oauth] → published
```

## Custo Total: R$0
- Groq API: free tier (6K RPM, Llama 3.3 70B)
- Nvidia API: free tier (DeepSeek V3/R1)
- Supabase: free tier (500MB)
- GitHub Actions: free tier (2K min/mês)
- Ruflo: MIT open source
