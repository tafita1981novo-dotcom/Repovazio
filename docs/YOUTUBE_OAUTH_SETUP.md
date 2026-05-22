# YouTube OAuth Setup — psidanielacoelho1982@gmail.com

## Por que é necessário
A publicação automática de vídeos no YouTube requer OAuth 2.0 com a conta
psidanielacoelho1982@gmail.com. É um processo de 5 minutos, feito 1 vez.

## Passo a Passo

### 1. Google Cloud Console
1. Acesse: https://console.cloud.google.com
2. Login com: psidanielacoelho1982@gmail.com
3. Criar projeto: "psicologia-doc-pipeline"
4. Ativar: YouTube Data API v3

### 2. Credenciais OAuth
1. APIs & Services → Credentials → Create Credentials → OAuth Client ID
2. Application type: Desktop Application
3. Nome: psicologia-doc
4. Download JSON → salvar como `client_secrets.json`

### 3. Gerar refresh_token (1 vez)
```bash
pip install google-auth-oauthlib google-api-python-client
python3 scripts/youtube_oauth_setup.py
# Abre browser → autorizar → colar o código → salvar refresh_token
```

### 4. Salvar no GitHub Secrets
- `YOUTUBE_CLIENT_ID` = client_id do JSON
- `YOUTUBE_CLIENT_SECRET` = client_secret do JSON  
- `YOUTUBE_REFRESH_TOKEN` = token gerado no passo 3

### 5. Testar
```bash
python3 scripts/youtube_publisher.py --video output/video_683.mp4
```

## Script de setup OAuth
Ver: `scripts/youtube_oauth_setup.py`

## Após configurado
O pipeline publica automaticamente todo dia às 18h BRT via GitHub Actions.
