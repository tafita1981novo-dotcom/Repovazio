# Evolution API — Railway Deploy

## Variáveis obrigatórias no Railway:

| Variável | Valor |
|----------|-------|
| `AUTHENTICATION_API_KEY` | `evo_cffedffed1d618b64504d314a0d3561f` |
| `AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES` | `true` |
| `SERVER_PORT` | `8080` |
| `DATABASE_PROVIDER` | `postgresql` |
| `DATABASE_CONNECTION_URI` | `${{Postgres.DATABASE_URL}}` |
| `CACHE_REDIS_ENABLED` | `false` |
| `DEL_INSTANCE` | `false` |

## Após deploy — configurar instância:

```bash
pip install requests
export EVOLUTION_URL=https://SEU_APP.up.railway.app
export EVOLUTION_APIKEY=evo_cffedffed1d618b64504d314a0d3561f
export WEBHOOK_URL=https://repovazio.vercel.app/api/wa-webhook
export WEBHOOK_SECRET=evo_cffedffed1d618b64504d314a0d3561f
python scripts/setup_evolution.py
```

Depois abra `qrcode.html` e escaneie com o WhatsApp.

## Página de status:
https://repovazio.vercel.app/whatsapp-connect

