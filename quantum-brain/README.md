# 🧠 QUANTUM BRAIN — Setup em 15 minutos

Sistema 100% gratuito que publica conteúdo todo dia e gera renda passiva.
Roda sozinho no GitHub Actions. Você só configura uma vez.

---

## O QUE ESTE SISTEMA FAZ (todo dia às 3h UTC, sem você tocar)

1. Pesquisa trending topics no seu nicho
2. Gera roteiro completo com IA (NVIDIA/Groq — grátis)
3. Gera narração em português (ElevenLabs free / gTTS grátis)
4. Cria imagens com Pollinations FLUX (ilimitado e grátis)
5. Monta vídeo completo com MoviePy
6. Gera thumbnail otimizada para CTR
7. Publica no YouTube via API oficial
8. Distribui para 6 plataformas (Buffer free)
9. Reporta ganhos do dia

**Custo total: $0/mês**

---

## SETUP — 4 PASSOS

### Passo 1 — Fork/Clone este repositório
```bash
# No GitHub: fork de tafita81/Repovazio
# ou clone direto:
git clone https://github.com/tafita81/Repovazio.git
cd Repovazio
```

### Passo 2 — Criar tabelas no Supabase
```
1. app.supabase.com → seu projeto → SQL Editor
2. Copiar conteúdo de: quantum-brain/config/supabase_setup.sql
3. Clicar "Run"
```

### Passo 3 — Adicionar chaves como GitHub Secrets
```
github.com/tafita81/Repovazio → Settings → Secrets and variables → Actions

Secrets obrigatórios (todos gratuitos):
  NVIDIA_API_KEY        → build.nvidia.com
  GROQ_API_KEY          → console.groq.com
  SUPABASE_URL          → app.supabase.com → Project Settings → API
  SUPABASE_KEY          → app.supabase.com → Project Settings → API (anon key)

Secrets opcionais (para publicar no YouTube):
  YOUTUBE_CLIENT_ID     → console.cloud.google.com
  YOUTUBE_CLIENT_SECRET → console.cloud.google.com
  YOUTUBE_REFRESH_TOKEN → gerar com o script abaixo

Secrets opcionais (para distribuir nas redes):
  BUFFER_ACCESS_TOKEN   → buffer.com → developers
  ELEVENLABS_API_KEY    → elevenlabs.io → Profile
```

### Passo 4 — Ativar o workflow
```
github.com/tafita81/Repovazio → Actions
→ "Quantum Brain — Pipeline Diário"
→ "Enable workflow"
→ "Run workflow" (para testar agora)
```

---

## COMO GERAR O YOUTUBE_REFRESH_TOKEN

Após ter CLIENT_ID e CLIENT_SECRET:

```bash
pip install google-auth-oauthlib
python3 -c "
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_config(
    {'installed': {
        'client_id': 'SEU_CLIENT_ID',
        'client_secret': 'SEU_CLIENT_SECRET',
        'redirect_uris': ['urn:ietf:wg:oauth:2.0:oob'],
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token'
    }},
    scopes=['https://www.googleapis.com/auth/youtube.upload']
)
creds = flow.run_local_server(port=0)
print('REFRESH TOKEN:', creds.refresh_token)
"
```

Copie o refresh_token → adicione como secret YOUTUBE_REFRESH_TOKEN

---

## CONTAS PARA RECEBER DÓLARES (criar uma vez, grátis)

| Plataforma | Onde criar | Para que serve |
|---|---|---|
| Wise | wise.com | Receber de ClickBank, Impact, AdSense — melhor câmbio |
| PayPal | paypal.com | Gumroad, Skool afiliados, clientes |
| Hotmart | hotmart.com | Vender produtos digitais, PIX instantâneo |
| Kiwify | kiwify.com.br | Alternativa ao Hotmart, taxa menor |
| AdSense | adsense.google.com | YouTube monetization |

---

## AFILIADOS PARA CADASTRAR (todos gratuitos)

1. **ClickBank** → clickbank.com → 50-75% comissão
2. **Impact.com** → impact.com → $50-500/referral
3. **PartnerStack** → partnerstack.com → recorrente mensal
4. **Hotmart** → hotmart.com → 30-80% por venda
5. **Amazon** → associados.amazon.com.br → 1-10%

---

## CRONOGRAMA DE EXECUÇÃO

```
3h UTC  — Pipeline de conteúdo (vídeo completo)
4h UTC  — Distribuição 6 plataformas
5h UTC  — Otimização de monetização
6h UTC  — Descoberta de novas oportunidades
7h UTC  — Verificação de afiliados
8h UTC  — Relatório de ganhos no log
```

---

## PROJEÇÃO DE RECEITA (baseada em casos reais do Notion AIPB)

| Mês | Ação | Receita Esperada |
|---|---|---|
| 1-2 | Setup + primeiros vídeos | $0-50 |
| 3 | Pipeline rodando, afiliados ativos | $50-300 |
| 6 | AdSense ativo + clientes LinkedIn | $1.000-5.000 |
| 12 | Multi-canal + recorrente | $5.000-20.000 |

**Custo em todos os meses: $0**
