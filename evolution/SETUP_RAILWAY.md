# Evolution API — Railway (último passo)

## O que já está pronto (feito automaticamente)
- ✅ `evolution/Dockerfile` e `railway.toml` no repo
- ✅ Webhook `https://repovazio.vercel.app/api/wa-webhook` deployado e testado
- ✅ Tabelas `claude_knowledge` no Supabase criadas
- ✅ `WEBHOOK_SECRET = evo_cffedffed1d618b64504d314a0d3561f`

## Único passo manual: Railway (5 min)

### 1. Deploy
- Acesse https://railway.app → New Project
- **Deploy from GitHub repo** → tafita81/Repovazio
- **Root directory**: /evolution
- Adicione plugin **PostgreSQL**

### 2. Variáveis no Railway
| Variável | Valor |
|----------|-------|
| AUTHENTICATION_API_KEY | evo_cffedffed1d618b64504d314a0d3561f |
| AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES | true |
| SERVER_PORT | 8080 |
| DATABASE_PROVIDER | postgresql |
| DATABASE_CONNECTION_URI | ${{Postgres.DATABASE_URL}} |
| CACHE_REDIS_ENABLED | false |
| DEL_INSTANCE | false |

### 3. Configurar instância
```bash
pip install requests
export EVOLUTION_URL=https://SEU_APP.up.railway.app
export EVOLUTION_APIKEY=evo_cffedffed1d618b64504d314a0d3561f
export WEBHOOK_URL=https://repovazio.vercel.app/api/wa-webhook
export WEBHOOK_SECRET=evo_cffedffed1d618b64504d314a0d3561f
python scripts/setup_evolution.py
```
Abre qrcode.html → escaneie com WhatsApp → pronto!
