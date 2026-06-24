# OMNIBRAIN — Transcript Fetcher

## Situação atual
- **2.595 vídeos** na tabela `yt_transcripts` com `status='pending'`
- YouTube bloqueia IPs de cloud (GitHub Actions, AWS, etc.)
- Precisa rodar **localmente** com IP residencial

## Scripts disponíveis

### Opção A — Com service_role key (mais fácil)
**Arquivo:** `omnibrain/fetch_transcripts_local.py`

```bash
# 1. Pega a service_role key em:
#    https://supabase.com/dashboard/project/tpjvalzwkqwttvmszvie/settings/api

# 2. Exporta a key
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...."

# 3. Instala dependências
pip install requests supabase

# 4. Roda
python omnibrain/fetch_transcripts_local.py
```

**Velocidade:** ~15 threads paralelas, ~200 vídeos/5min → 2.595 vídeos em ~65 minutos

---

### Opção B — Sem configurar nada (salva em JSON)
**Arquivo:** `omnibrain/fetch_transcripts_json.py`

```bash
pip install requests
python omnibrain/fetch_transcripts_json.py
```

Salva os resultados em `/tmp/transcripts_batch_001.json`, `_002.json`, etc.
Depois fazer o upload desses JSONs para o Supabase.

---

## Técnica usada
1. Busca a API key do YouTube na página `youtube.com`
2. Faz POST para `youtubei/v1/player` com `clientName: ANDROID`  
3. Extrai a URL da legenda do `captionTracks`
4. Baixa o XML com `User-Agent: com.google.android.youtube`
5. Parseia o XML `timedtext` e extrai o texto

## Por que não GitHub Actions?
YouTube bloqueia requisições de IPs de cloud. Só funciona com IP residencial.

## Tabela Supabase: `yt_transcripts`
| campo | descrição |
|-------|-----------|
| video_id | PK |
| status | pending / done / no_captions / error |
| transcript | texto completo (max 60k chars) |
| lang | código do idioma (pt, en, etc.) |
| word_count | número de palavras |
| error_msg | motivo do erro |
| fetched_at | timestamp |
