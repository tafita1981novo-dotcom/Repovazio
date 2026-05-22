# 🧠 QUANTUM BRAIN — Skill Universal de APIs

> Este skill carrega automaticamente o contexto do Cérebro Quântico
> em QUALQUER chat, sobre QUALQUER assunto.

## Ativar em qualquer chat novo:

Cole este bloco no início do chat:

```
QUANTUM BRAIN ATIVO
Supabase: tpjvalzwkqwttvmszvie | tabela: api_brain
APIs: 1183+ mapeadas | Sem auth: 493 | Alta relevância: 350
Dashboard: repovazio.vercel.app/cerebro.html

Para qualquer tarefa, primeiro verificar:
SELECT * FROM find_api('tema', no_auth:=true, lim:=5);
```

## Como o cérebro serve qualquer assunto:

### 📝 Escrita / Conteúdo
```
Brain.search("grammar pt-br") → LanguageTool, Datamuse
Brain.search("quotes inspiration") → ZenQuotes, Quotable, StoicQuotes
Brain.search("translation") → MyMemory, Lingva, DeepL
Brain.search("nlp summary") → HF BART, MeaningCloud
```

### 🎥 Vídeo / Mídia
```
Brain.search("image ai") → Pollinations FLUX, HF FLUX, Leonardo.ai
Brain.search("tts voice") → Chatterbox, Edge TTS, Pollinations Audio
Brain.search("video stock") → Pexels Video, Pixabay, Coverr
Brain.search("music cc") → Jamendo, Incompetech, FMA
```

### 🔬 Pesquisa / Ciência
```
Brain.search("academic papers") → PubMed, CrossRef, OpenAlex, arXiv
Brain.search("psychology research") → PsyArXiv, APA, OSF
Brain.search("statistics data") → Our World in Data, WHO, World Bank
Brain.search("fact check") → CrossRef, ORCID, Altmetric
```

### 💻 Desenvolvimento / Tech
```
Brain.search("llm api") → NVIDIA, Groq, Cerebras, GitHub Models
Brain.search("database") → Supabase, PlanetScale, Railway
Brain.search("cdn storage") → Cloudflare R2, Backblaze B2, Bunny.net
Brain.search("deploy hosting") → Vercel, Netlify, Render, Fly.io
```

### 📊 Analytics / SEO
```
Brain.search("seo keywords") → Semrush, Google Trends, Ahrefs
Brain.search("social analytics") → Social Blade, BuzzSumo, SparkToro
Brain.search("youtube data") → YouTube Data v3, YouTube oEmbed
Brain.search("news monitoring") → GNews, NewsAPI, The Guardian
```

### 🌍 Dados Brasil
```
Brain.search("brazil data") → IBGE, BrasilAPI, Portal Transparência
Brain.search("brazil health") → ANVISA, DataSUS, CFP
Brain.search("brazil payments") → Mercado Pago, PagSeguro, Iugu
Brain.search("brazil holidays") → Nager.Date, BrasilAPI Feriados
```

### 🧠 Psicologia / Saúde Mental
```
Brain.search("psychology") → PsyArXiv, APA, ClinicalTrials.gov
Brain.search("mental health") → WHO Atlas, NIMH, SAMHSA
Brain.search("personality") → Crystal DISC, Sentino Big5, 16Personalities
Brain.search("emotion") → Symanto, Twinword, HF Emotion PT-BR
```

## API Brain — SQL direto (funciona em qualquer projeto)

```sql
-- Buscar APIs sem auth para qualquer tema:
SELECT name, endpoint, description, use_case 
FROM find_api('image generation', no_auth:=true, lim:=5);

-- APIs alta relevância por categoria:
SELECT name, category, endpoint, rate_limit
FROM api_brain 
WHERE category = 'Machine Learning' AND relevance = 3
ORDER BY name;

-- Ver todas as categorias disponíveis:
SELECT category, COUNT(*) as total 
FROM api_brain 
GROUP BY category 
ORDER BY total DESC;
```

## Metodologia QUANTUM TRUTH

Para qualquer vídeo ou conteúdo:
1. **TRUTH ENGINE**: Verificar ciência (PubMed/CrossRef/arXiv)
2. **VIRAL INTEL**: Confirmar tendência (Google Trends/Reddit/BuzzSumo)  
3. **EMOTIONAL ARCH**: Estruturar 7 camadas emocionais
4. **QUALITY GATE**: 7 filtros automáticos antes de publicar
5. **LIVING DIST**: Distribuição automática pós-publicação
6. **SELF-LEARNING**: Brain.add() com aprendizado do vídeo

## Links sempre ativos

- Dashboard: https://repovazio.vercel.app/cerebro.html
- Brain script: https://github.com/tafita81/Repovazio/blob/main/scripts/api_brain.py
- Metodologia: https://github.com/tafita81/Repovazio/blob/main/docs/QUANTUM_TRUTH.md
- Supabase: https://tpjvalzwkqwttvmszvie.supabase.co

---
*Skill universal — funciona para psicologia, finanças, tech, saúde, educação, qualquer nicho*
*1183+ APIs | 53 categorias | 12 fontes | Sempre crescendo*
