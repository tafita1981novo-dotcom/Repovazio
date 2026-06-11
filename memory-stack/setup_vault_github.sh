#!/bin/bash
# ============================================================
# SETUP VAULT NO GITHUB — executa no seu computador local
# Pré-requisito: git instalado, repo clonado
# ============================================================
set -e

# Detectar pasta do Repovazio
REPO_DIR="${1:-$(pwd)}"
echo "📁 Usando repo: $REPO_DIR"

# Criar estrutura de pastas
mkdir -p "$REPO_DIR/vault/channels"
mkdir -p "$REPO_DIR/vault/affiliates"
mkdir -p "$REPO_DIR/vault/rules"
mkdir -p "$REPO_DIR/vault/infra"
mkdir -p "$REPO_DIR/vault/milestones"
mkdir -p "$REPO_DIR/vault/memory"

echo "✅ Pastas criadas"

# ── channels/NEWLIFE.md ─────────────────────────────────────
cat > "$REPO_DIR/vault/channels/NEWLIFE.md" << 'EOF'
---
channel_id: NEWLIFE
name: newlife_2day
status: ativo
youtube_handle: "@newlife_2day"
niche: [brain, psychology, sleep, focus]
spectrum_color: rainbow
brand_color: "#7C3AED"
bg_color: "#06060F"
created: 2026-06-11
---

## Status Atual
- YT token: VALIDO (refresh token configurado)
- Live 24/7: verificar
- Subscribers: monitorar diariamente

## Configuracao
- Refresh token env: YOUTUBE_REFRESH_TOKEN2
- Spectrum: rainbow
- Metodo: edge-tts narracao + Ken Burns
EOF

# ── affiliates/portfolio.md ─────────────────────────────────
cat > "$REPO_DIR/vault/affiliates/portfolio.md" << 'EOF'
---
tipo: referencia
categoria: afiliados
updated: 2026-06-11
total_programas: 9
---

## Tier 1 High Ticket

### Billionaire Brain Wave (ClickBank)
- URL: https://tafita1981.attractbr.hop.clickbank.net
- Comissao: $63.73 APV
- EPC: $1.68 / Conversao: 3%
- Fit: sleep, brown_noise, adhd, brain, focus
- Status: ATIVO

### The Brain Song (ClickBank)
- URL: https://tafita1981.brainsong.hop.clickbank.net
- Comissao: $55 APV / EPC: $1.50
- Fit: sleep, adhd, focus, brain
- Status: ATIVO

### ADHD Brain Reset Kit (Gumroad - produto proprio)
- URL: env GUMROAD_KIT_URL
- Comissao: $47 (100% margem)
- Fit: adhd, brown_noise, focus
- Status: PENDENTE upload PDF

### Oura Ring (Impact.com)
- URL: env OURA_AFFILIATE_URL
- Comissao: $30/venda
- Fit: sleep, adhd
- Status: PENDENTE aprovacao 48h

## Tier 2 Volume Passivo

### BetterHelp
- URL: env BETTERHELP_URL
- Comissao: $15/referral
- Nota: substitui Wealth DNA Code (EPC $0.39 fraco)
- Status: PENDENTE cadastro

### Amazon Associates (4 produtos)
- weighted_blanket: env AMAZON_WEIGHTED_BLANKET = $4.50
- white_noise_machine: env AMAZON_NOISE_MACHINE = $1.47
- sleep_mask: env AMAZON_SLEEP_MASK = $0.87
- blue_light_glasses: env AMAZON_BLG = $2.37
- Status: PENDENTE cadastro Associates

## Regra de Substituicao
Wealth DNA Code (EPC $0.39) => BetterHelp ($15, fit perfeito ADHD/anxiety)
EOF

# ── rules/localizations.md ─────────────────────────────────
cat > "$REPO_DIR/vault/rules/localizations.md" << 'EOF'
---
tipo: regra_operacional
categoria: youtube_metadata
---

## 15 Idiomas
EN DE JA KO FR ES (Tier 1 completo) PT IT TR RU PL NL HI AR ZH (Tier 2 curto)

## defaultAudioLanguage
Usar "zxx" = sem conteudo linguistico (universal)
NUNCA JA/KO/ZH/AR/HI em titulos rotativos (causa bug confirmado)
Rotacao de titulos: APENAS EN

## CPM por idioma
EN $8-20 | DE $12-25 | JA $8-15 | KO $6-12 | FR $8-18 | ES $5-10
PT $3-6 | IT $6-12 | NL $8-15 | HI $1-2 | AR $2-5 | ZH $3-8

## Impacto
+195% views com metadata 8 idiomas (Cozy Relaxing Jazz validado)

## Tier 1 (completo)
Titulos + descricoes completos em EN DE JA KO FR ES

## Tier 2 (curto)
Titulos curtos apenas em PT IT TR RU PL NL HI AR ZH
EOF

# ── rules/producao.md ───────────────────────────────────────
cat > "$REPO_DIR/vault/rules/producao.md" << 'EOF'
---
tipo: regra_operacional
categoria: video_production
---

## Shorts 9:16 58s
- Resolucao: 1080x1920, FPS: 20, validado 57.82s/5MB
- Imagens: Pollinations FLUX sequential 4s delay
- NUNCA Pillow em videos publicados
- PROIBIDO psicologa no canal Daniela Coelho ate Jan 2027
- Usar: pesquisadora de comportamento humano

## Longs 15 min
- 100 imagens unicas x 3 variacoes Ken Burns = 300 segmentos
- Mid-rolls: 3/6/9/12 min
- render_long_from_bank.py validado 100/100 bank 15:03 runtime

## Sons ffmpeg
- Brown: anoisesrc=color=brown:sample_rate=48000
- Rain: anoisesrc=brown highpass=200 lowpass=8000 volume=1.2
- 432Hz: sine=frequency=432
- 528Hz: sine=frequency=528
- Cat purr: sine=26Hz tremolo=26:0.7 lowpass=150
- Fan: anoisesrc=brown lowpass=400 volume=0.8
EOF

# ── infra/secrets.md ────────────────────────────────────────
cat > "$REPO_DIR/vault/infra/secrets.md" << 'EOF'
---
tipo: referencia
categoria: github_secrets
---

## Secrets Ja Existentes
- SUPABASE_URL, SUPABASE_SERVICE_KEY
- YOUTUBE_REFRESH_TOKEN2 (canal newlife)
- NVIDIA_API_KEY2, GROQ_API_KEY2
- YT_CLIENT_ID, YT_CLIENT_SECRET

## Secrets Pendentes CH01
- YOUTUBE_STREAM_KEY_CH01 (obter apos criar Brand Account)
- YOUTUBE_REFRESH_TOKEN_CH01 (apos OAuth)
- YT_CHANNEL_ID_CH01 (apos criar canal)

## Secrets Pendentes Afiliados
- OURA_AFFILIATE_URL (Impact.com 48h aprovacao)
- GUMROAD_KIT_URL (apos upload PDF)
- BETTERHELP_URL (apos cadastro)
- AMAZON_WEIGHTED_BLANKET, AMAZON_NOISE_MACHINE
- AMAZON_SLEEP_MASK, AMAZON_BLG

## Memory Stack
- GRAPHITI_MCP_URL = http://IP:8765/sse
- OBSIDIAN_MCP_URL = http://IP:8766/sse
- ORACLE_VM_IP = IP da Oracle VM
- ORACLE_SSH_KEY = chave SSH privada

## Infra
- GitHub: tafita81/Repovazio
- Supabase: tpjvalzwkqwttvmszvie
- Vercel: repovazio.vercel.app
- Oracle Cloud: ARM 4 OCPU 24GB sa-saopaulo-1
EOF

# ── milestones/shops.md ─────────────────────────────────────
cat > "$REPO_DIR/vault/milestones/shops.md" << 'EOF'
---
tipo: monitoramento
categoria: monetizacao
ultima_atualizacao: 2026-06-11
---

## Shops por Milestone

| Shop | Requisito | BR Elegivel | Status |
|---|---|---|---|
| Instagram Shop | 0 followers + conta Profissional | SIM | CONFIGURAR AGORA |
| YouTube YPP Tier 1 + Shopping Affiliate | 500 subs + 3000h/12m | SIM BR desde mar/2026 | Monitorar |
| YouTube YPP Full (ad revenue) | 1000 subs + 4000h | SIM | Monitorar |
| Instagram Creator Marketplace | 1000 followers | SIM | Monitorar |
| YouTube Channel Membership | 500 subs + YPP ativo | SIM | Monitorar |
| TikTok Creator Rewards | 10K followers + 100K views/28d | SIM | Monitorar |
| TikTok Shop Affiliate | 5000 followers | BR sem acesso jun/2026 | Aguardar |

## Nota Critica BR
YouTube Shopping Affiliate: BR ELEGIVEL desde mar/2026
12 paises: US KR ID IN TH VN MY PH SG BR TW JP

## Projecao de Receita (5 canais ALPHA+BETA)
- Mes 3: $500-2800
- Mes 6: $2500-12500
- Mes 12: $7500-34000
- Mes 18: $18K-65K
EOF

# ── memory/graphiti_schema.md ───────────────────────────────
cat > "$REPO_DIR/vault/memory/graphiti_schema.md" << 'EOF'
---
tipo: referencia_tecnica
categoria: knowledge_graph
---

## Group IDs (multi-tenant Graphiti)
- channels: fatos sobre canais YouTube
- affiliates: performance e status de afiliados
- rules: regras operacionais e politicas
- milestones: progresso de metas e shops
- system: estado do sistema, ultimas acoes

## Entidades Principais
- Canal: id, nome, nicho, subs, watch_hours, status
- Afiliado: id, comissao, EPC, status, fit
- Milestone: tipo, requisito, atual, elegivel_br
- Regra: categoria, texto, data_descoberta
- AcaoExecutada: tipo, canal, data, resultado

## Como Consultar (quantum_master.py)
# Verificar se Short ja foi publicado hoje
resp = graphiti_query("Short publicado hoje CH01", group_id="channels")
if resp: return  # ja publicado, zero tokens gastos

# Recuperar afiliados para niche
resp = graphiti_query("afiliados tier 1 fit brown_noise", group_id="affiliates")

# Gravar milestone atingido
graphiti_add("Canal CH01 atingiu 500 subscribers em 2026-08-15", group_id="channels")

## Economia de Tokens
- Antes (Notion raw): 2000-10000 tokens por consulta
- Depois (Graphiti): 50-300 tokens por consulta
- Reducao media: 90-95%

## Deploy
docker-compose up -d (FalkorDB + Graphiti MCP na Oracle VM)
Porta Graphiti: 8765/sse
Porta Obsidian: 8766/sse
EOF

# ── Copiar arquivos Python do memory stack ──────────────────
# (se estiver rodando da raiz do Repovazio)
mkdir -p "$REPO_DIR/memory-stack"

# quantum_master_v4.py e graphiti_client.py devem vir do zip
echo ""
echo "✅ Vault criado com sucesso!"
echo ""
echo "Arquivos criados:"
find "$REPO_DIR/vault" -name "*.md" | sed "s|$REPO_DIR/||"
echo ""
echo "Próximo passo:"
echo "  cd $REPO_DIR"
echo "  git add vault/"
echo "  git commit -m 'feat: add quantum brain memory vault'"
echo "  git push"
