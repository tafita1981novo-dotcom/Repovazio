#!/usr/bin/env python3
"""
VAULT INITIALIZER — Quantum Brain Knowledge Base
Cria toda a estrutura do vault Obsidian no GitHub (tafita81/Repovazio/vault/)
Roda UMA VEZ para popular o vault com todo o conhecimento existente.
"""
import os, json, datetime

VAULT_STRUCTURE = {
    # ── CANAL CH01 ──────────────────────────────────────────────────────────
    "channels/CH01.md": """---
channel_id: CH01
name: Deep Brown Noise
status: aguardando_setup
youtube_id: ""
niche: [brown_noise, adhd, sleep, focus]
spectrum_color: fire
brand_color: "#7C3AED"
bg_color: "#06060F"
ypp_tier1_req: "500 subs + 3000h watch"
ypp_full_req: "1000 subs + 4000h watch"
created: 2026-06-11
---

## Status Atual
- Stream key: PENDENTE (criar Brand Account primeiro)
- Live 24/7: INATIVO
- Subscribers: 0
- Watch hours: 0h

## Setup Pendente
1. Criar Brand Account "Deep Brown Noise" no YouTube
2. Verificar telefone em youtube.com/verify
3. Ativar live → aguardar 24h
4. Copiar stream key → GitHub Secret YOUTUBE_STREAM_KEY_CH01
5. Deploy quantum_master.py + workflow → git push

## Afiliados Ativos
- Tier 1: billionaire_brain_wave ($63.73), brain_song ($55), adhd_kit ($47)
- Tier 2: betterhelp ($15), white_noise_machine ($1.47), weighted_blanket ($4.50)

## Roteiros Shorts (rotação dia % 7)
- Dia 1: "POV: Your Brain Finally Goes Quiet" → ADHD Kit $47
- Dia 2: "If You Have ADHD, Listen for 30 Seconds" → ADHD Kit $47
- Dia 3: "The Sound 200 MILLION People Use to Sleep" → Oura Ring $30
- Dia 4: "Brown Noise vs White Noise" → White Noise Machine
- Dia 5: "Can't Sleep Because of Noisy Neighbors?" → Weighted Blanket
- Dia 6: "Study With Me ADHD-Friendly" → ADHD Kit $47
- Dia 7: "Tonight: Try This ONE Thing" → Sleep Mask
""",

    # ── CANAL NEWLIFE ───────────────────────────────────────────────────────
    "channels/NEWLIFE.md": """---
channel_id: NEWLIFE
name: newlife_2day
status: ativo
youtube_handle: "@newlife_2day"
channel_id_yt: ""
niche: [brain, psychology, sleep, focus]
spectrum_color: rainbow
brand_color: "#7C3AED"
bg_color: "#06060F"
created: 2026-06-11
---

## Status Atual
- YT token: VÁLIDO (refresh token configurado)
- Live 24/7: ativo (verificar)
- Subscribers: monitorar diariamente

## Configuração
- Refresh token: env YOUTUBE_REFRESH_TOKEN2
- Spectrum: rainbow
- Método: edge-tts narração + Ken Burns
""",

    # ── AFILIADOS ───────────────────────────────────────────────────────────
    "affiliates/portfolio.md": """---
updated: 2026-06-11
total_programs: 9
---

## Tier 1 — High Ticket

### Billionaire Brain Wave (ClickBank)
- URL: https://tafita1981.attractbr.hop.clickbank.net
- Comissão: $63.73 APV
- EPC: $1.68
- Conversão: ~3%
- Fit: sleep, brown_noise, adhd, brain, focus
- Status: ATIVO

### The Brain Song (ClickBank)
- URL: https://tafita1981.brainsong.hop.clickbank.net
- Comissão: $55 APV
- EPC: $1.50
- Fit: sleep, adhd, focus, brain
- Status: ATIVO

### ADHD Brain Reset Kit (Gumroad — produto próprio)
- URL: env GUMROAD_KIT_URL
- Comissão: $47 (100% margem)
- Fit: adhd, brown_noise, focus
- Status: PENDENTE (upload PDF no Gumroad)
- PDF criado: /mnt/user-data/outputs/ADHD_Brain_Reset_Kit.pdf

### Oura Ring (Impact.com)
- URL: env OURA_AFFILIATE_URL
- Comissão: $30/venda
- Fit: sleep, adhd
- Status: PENDENTE (aprovação 48h após cadastro)

## Tier 2 — Volume Passivo

### BetterHelp
- URL: env BETTERHELP_URL
- Comissão: $15/referral
- Fit: sleep, adhd, anxiety
- Nota: substitui Wealth DNA Code (EPC $0.39 fraco)
- Status: PENDENTE (cadastro)

### Amazon Associates (4 produtos)
- Weighted Blanket: env AMAZON_WEIGHTED_BLANKET → $4.50
- White Noise Machine: env AMAZON_NOISE_MACHINE → $1.47
- Sleep Mask BT: env AMAZON_SLEEP_MASK → $0.87
- Blue Light Glasses: env AMAZON_BLG → $2.37
- Status: PENDENTE (cadastro Associates)

## Regra de Substituição
Wealth DNA Code (EPC $0.39) → BetterHelp ($15, fit perfeito ADHD/anxiety)
""",

    # ── REGRAS ANTI-INAUTHENTIC ─────────────────────────────────────────────
    "rules/anti-inauthentic.md": """---
tipo: regra_critica
categoria: youtube_policy
data_descoberta: 2026-06-11
fonte: YouTube Help + FABLE 5 audit
---

## Resumo da Política
YouTube mira "mass-produced content easily replicable at scale" (jul/2025).
Regra de ouro: "if the average viewer can clearly tell that content differs from video to video, it's fine to monetize"

## O QUE É PROIBIDO
- 30 canais de tela preta + noise idêntico → rejeição YPP em massa + flag na conta
- Tela preta como único formato do canal (black screen = variante, NÃO o canal todo)
- +3 canais novos por semana (parece spam farm)
- Publicar noise no Spotify com categoria "noise" (vale 1/5 do royalty)

## O QUE É OBRIGATÓRIO POR CANAL
- Visualizer ffmpeg com cor única por canal (fire/magma/cool/moss/rainbow/nebulae)
- Mínimo 3 formatos diferentes (live 24/7 + upload + Short)
- Mascote Pollinations único por flagship (efeito Lofi Girl)
- Community tab: 2 posts/semana via API (sinal humano para reviewer YPP)

## CHECKLIST PRÉ-YPP (obrigatório antes de aplicar)
- [ ] Visual único? (cor de spectrum diferente de todos os outros canais)
- [ ] 3+ formatos? (live + upload + Short)
- [ ] Mascote definido?
- [ ] Community tab ativa?
- [ ] Descrições educacionais? (não só "sleep sounds")
- [ ] "Viewer percebe diferença?" → SIM obrigatório

## SPOTIFY
- NUNCA publicar como "noise" → vale 1/5
- Publicar como "Ambient Sleep MUSIC" (432Hz pads + piano = MÚSICA = royalty cheio)
- Plataforma: RouteNote grátis
- Início: Mês 4+
""",

    # ── REGRAS DE IDIOMAS ───────────────────────────────────────────────────
    "rules/localizations.md": """---
tipo: regra_operacional
categoria: youtube_metadata
---

## 15 Idiomas Configurados
EN (base), DE, JA, KO, FR, ES (Tier 1 completo), PT, IT, TR, RU, PL, NL, HI, AR, ZH (Tier 2 curto)

## defaultAudioLanguage
Usar "zxx" = sem conteúdo linguístico (universal, não penaliza em nenhum idioma)

## Hierarquia por CPM
Tier 1 (EN $8-20, DE $12-25, JA $8-15, KO $6-12, FR $8-18, ES $5-10): títulos e descrições COMPLETOS
Tier 2 (PT $3-6, IT $6-12, TR $2-5, RU $2-4, PL $2-4, NL $8-15, HI $1-2, AR $2-5, ZH $3-8): títulos curtos apenas

## Impacto Validado
+195% views com metadata 8 idiomas (Cozy Relaxing Jazz - caso documentado)

## API Call
Usar YouTube.videos.update() com localizations dict
NUNCA usar JA/KO/ZH/AR/HI em títulos rotativos (causou bug em sessão anterior)
Rotação de títulos: APENAS EN
""",

    # ── REGRAS DE PRODUÇÃO ──────────────────────────────────────────────────
    "rules/producao.md": """---
tipo: regra_operacional
categoria: video_production
---

## Shorts (9:16, 58s)
- Resolução: 1080x1920
- FPS: 20 (valida em 57.82s/5MB)
- Rate: +37%
- Imagens: Pollinations FLUX sequential, 4s delay
- Duração validada: 57.82s / 5MB
- NUNCA usar Pillow em vídeos publicados
- PROIBIDO: psicóloga/psicóloga no canal Daniela Coelho até Jan 2027
- Usar: "pesquisadora de comportamento humano"

## Longs (15 min)
- 100 imagens únicas × 3 variações Ken Burns = 300 segmentos
- Mid-rolls em: 3/6/9/12 min
- render_long_from_bank.py validado (100/100 bank, 15:03 runtime)

## Live 24/7 — Comando Master (visualizer)
ffmpeg -re -f lavfi -i "anoisesrc=color=brown:sample_rate=48000" \\
  -filter_complex "[0:a]asplit=2[a1][a2];[a1]showspectrum=size=1920x540:mode=combined:color=fire:scale=log:slide=scroll[spec];color=c=0x06060F:size=1920x1080[bg];[bg][spec]overlay=0:270[v1];[v1]drawtext=text='NOME — LIVE 24/7':fontcolor=0x7C3AED@0.6:fontsize=36:x=60:y=60[vout]" \\
  -map "[vout]" -map "[a2]" -c:v libx264 -preset veryfast -b:v 2500k -g 60 \\
  -c:a aac -b:a 192k -f flv rtmp://a.rtmp.youtube.com/live2/KEY

## Sons Suportados (ffmpeg anoisesrc)
- Brown: anoisesrc=color=brown:sample_rate=48000
- Pink: anoisesrc=color=pink:sample_rate=48000
- White: anoisesrc=color=white:sample_rate=48000
- Rain: anoisesrc=brown → highpass=200,lowpass=8000,volume=1.2
- 432Hz: sine=frequency=432
""",

    # ── INFRA / SECRETS ─────────────────────────────────────────────────────
    "infra/secrets_required.md": """---
tipo: referencia
categoria: github_secrets
---

## Secrets Obrigatórios (GitHub → Settings → Secrets)

### Já existentes (não reconfigurar)
- SUPABASE_URL, SUPABASE_SERVICE_KEY
- YOUTUBE_REFRESH_TOKEN2 (canal newlife)
- NVIDIA_API_KEY2, GROQ_API_KEY2
- YT_CLIENT_ID, YT_CLIENT_SECRET

### Pendentes para CH01
- YOUTUBE_STREAM_KEY_CH01 (obter após criar Brand Account)
- YOUTUBE_REFRESH_TOKEN_CH01 (após OAuth)
- YT_CHANNEL_ID_CH01 (após criar canal)

### Pendentes para afiliados
- OURA_AFFILIATE_URL (Impact.com → 48h aprovação)
- GUMROAD_KIT_URL (após upload PDF)
- BETTERHELP_URL (após cadastro)
- AMAZON_WEIGHTED_BLANKET (Amazon Associates)
- AMAZON_NOISE_MACHINE
- AMAZON_SLEEP_MASK
- AMAZON_BLG

### Memory Stack (após deploy Oracle VM)
- GRAPHITI_MCP_URL=http://SEU-IP:8765/sse
- OBSIDIAN_MCP_URL=http://SEU-IP:8766/sse

## Infra
- GitHub: tafita81/Repovazio
- Supabase: tpjvalzwkqwttvmszvie
- Vercel: repovazio.vercel.app
- Oracle Cloud: ARM 4 OCPU 24GB, sa-saopaulo-1
""",

    # ── SHOPS / MILESTONES ──────────────────────────────────────────────────
    "milestones/shops.md": """---
tipo: monitoramento
categoria: monetizacao
ultima_atualizacao: 2026-06-11
---

## Shops por Milestone

| Shop | Requisito | BR Elegível | Status |
|---|---|---|---|
| Instagram Shop | 0 followers + conta Profissional | ✅ | CONFIGURAR AGORA |
| YouTube YPP Tier 1 + Shopping Affiliate | 500 subs + 3.000h/12m | ✅ BR desde mar/2026 | Monitorar |
| YouTube YPP Full (ad revenue) | 1.000 subs + 4.000h | ✅ | Monitorar |
| Instagram Creator Marketplace | 1.000 followers | ✅ | Monitorar |
| YouTube Channel Membership | 500 subs + YPP ativo | ✅ | Monitorar |
| TikTok Creator Rewards | 10K followers + 100K views/28d | ✅ | Monitorar |
| TikTok Shop Affiliate | 5.000 followers | ⚠️ BR sem acesso jun/2026 | Aguardar |

## Projeção de Receita (5 canais ALPHA+BETA)
- Mês 3: $500-2.800
- Mês 6: $2.500-12.500
- Mês 12: $7.500-34.000
- Mês 18: $18K-65K

## Nota Crítica BR
YouTube Shopping Affiliate: BR ESTÁ ELEGÍVEL desde mar/2026
12 países: US, KR, ID, IN, TH, VN, MY, PH, SG, BR, TW, JP
""",

    # ── GRAPHITI SCHEMA ─────────────────────────────────────────────────────
    "memory/graphiti_schema.md": """---
tipo: referencia_tecnica
categoria: knowledge_graph
---

## Group IDs (multi-tenant Graphiti)
- channels: fatos sobre canais YouTube
- affiliates: performance e status de afiliados
- rules: regras operacionais e políticas
- milestones: progresso de metas e shops
- system: estado do sistema, últimas ações

## Entidades Principais
- Canal: id, nome, nicho, subs, watch_hours, status
- Afiliado: id, comissão, EPC, status, fit
- Milestone: tipo, requisito, atual, elegivel_br
- Regra: categoria, texto, data_descoberta
- AcaoExecutada: tipo, canal, data, resultado

## Relações Temporais (Graphiti rastreia "quando mudou")
- Canal HAS_AFFILIATE → afiliado ativo no canal
- Canal ALCANCOU → milestone atingido em data X
- AcaoExecutada FOI_EM → canal em data Y
- Regra APLICA_A → canal / tipo de conteúdo

## Como Consultar (quantum_master.py)
```python
# Verificar se Short já foi publicado hoje
resp = graphiti_query("Short publicado hoje CH01", group_id="channels")
if resp: return  # já publicado

# Recuperar afiliados ativos para canal
resp = graphiti_query("afiliados tier 1 fit brown_noise", group_id="affiliates")

# Gravar milestone atingido
graphiti_add("Canal CH01 atingiu 500 subscribers em 2026-08-15", group_id="channels")
```
""",
}

# ── GERAR ARQUIVOS ────────────────────────────────────────────────────────────

import os
BASE = "/home/claude/memory-stack/vault"
os.makedirs(BASE, exist_ok=True)

for rel_path, content in VAULT_STRUCTURE.items():
    full_path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ {rel_path}")

print(f"\n✅ Vault criado: {len(VAULT_STRUCTURE)} arquivos em {BASE}")
