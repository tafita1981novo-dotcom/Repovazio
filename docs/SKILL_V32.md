---
name: psicologia-doc-v27
description: Use esta SKILL sempre que o usuário mencionar: psicologia.doc, repovazio, Daniela Coelho, @psidanielacoelho, canal YouTube psicologia, viral, cérebro autônomo, tokens sociais, Instagram, TikTok, WhatsApp grupos, monetização, 1000 subs, crescimento, setup tokens, espelhamento viral.
version: 32.0
date: 2026-05-21
---

# SKILL psicologia.doc V32 — API OMNIBUS (21/mai/2026)

---

## ⚠️ REGRA DE OURO

```
NUNCA liberar vídeo sem testar #683 primeiro.
RMS trough = -inf obrigatório.
Gate duplo por segmento + global = pausas digitalmente perfeitas.
```

---

## INFRA CORE

```
Supabase:  tpjvalzwkqwttvmszvie
Vercel:    repovazio.vercel.app
GitHub:    tafita81/Repovazio

Canal ATIVO:   UCyCkIpsVgME9yCj_oXJFheA · @psidanielacoelho · psidanielacoelho1982@gmail.com
Canal ⛔:      UCSH63tBfY6wEIdkC4u4zKdg — BLOQUEADO 2026-05-07, NUNCA publicar

Arquivos principais:
  scripts/render_short_george.py      # Short FFmpeg+Chatterbox
  scripts/render_long_15min.py        # Long 15min
  scripts/render_remotion_short.py    # Short Remotion React (NOVO V32)
  scripts/psicologia_apis.py          # Hub de APIs (51+)
  remotion/src/                       # Composições React animadas

Painel 400: https://repovazio.vercel.app/painel-400.html
Vídeos:     https://repovazio.vercel.app/videos-prontos.html
Hub:        https://repovazio.vercel.app/hub.html
```

---

## 📚 OS 7 DIRETÓRIOS DE APIs PÚBLICAS

> Fonte primária para descobrir qualquer API gratuita para o pipeline

```python
API_DIRECTORIES = {

    # 1. O MAIS COMPLETO — 1400+ APIs, 51 categorias
    "public_apis_github": {
        "url":   "https://github.com/public-apis/public-apis",
        "json":  "https://api.publicapis.org/entries",        # busca programática
        "total": "1400+ APIs",
        "cats":  51,
        "uso":   "Referência principal. Buscar: ?category=Health&auth=null"
    },

    # 2. MELHOR UI — mesmos dados, filtros avançados
    "publicapis_dev": {
        "url":   "https://publicapis.dev",
        "cats_psico": ["personality","text-analysis","machine-learning","health","science","social"]
    },

    # 3. 1000+ APIs com categorias
    "public_apis_io": {
        "url":   "https://public-apis.io",
        "busca": "https://public-apis.io/category/{categoria}"
    },

    # 4. 1000+ com exemplos de código
    "publicapis_io": {
        "url":   "https://publicapis.io",
        "busca": "https://publicapis.io/category/{categoria}"
    },

    # 5. 48 categorias, API JSON própria
    "public_api_lists": {
        "url":  "https://github.com/public-api-lists/public-api-lists",
        "json": "https://public-api-lists.github.io/public-api-lists/apis.json"
    },

    # 6. ~200 APIs SEM QUALQUER AUTH — usar direto em CI
    "mixedanalytics": {
        "url": "https://mixedanalytics.com/blog/list-actually-free-open-no-auth-needed-apis/",
        "uso": "PRIORIDADE quando precisar de API em GitHub Actions sem secrets"
    },

    # 7. 40.000+ APIs — maior marketplace, free tiers
    "rapidapi": {
        "url": "https://rapidapi.com",
        "uso": "Quando não encontrar gratuito puro — verificar free tier"
    }
}

# Como buscar programaticamente (sem auth):
def find_api(category, no_auth=True):
    import requests
    params = {"category": category}
    if no_auth: params["auth"] = "null"
    return requests.get("https://api.publicapis.org/entries",
                       params=params, timeout=10).json().get("entries", [])
# Ex: find_api("Health") → APIs de saúde sem auth
# Ex: find_api("Personality") → APIs de psicologia
# Ex: find_api("Text Analysis") → NLP e análise de texto

# As 51 categorias disponíveis no diretório:
# Animals, Anime, Art & Design, Books, Business, Calendar,
# Cloud Storage, Cryptocurrency, Currency Exchange, Development,
# Dictionaries, Documents, Email, Environment, Events, Finance,
# Food & Drink, Games & Comics, Geocoding, Government, HEALTH,
# Jobs, MACHINE LEARNING, MUSIC, NEWS, Open Data, PERSONALITY,
# Photography, Science & Math, Security, Shopping, SOCIAL,
# Sports & Fitness, TEXT ANALYSIS, Transportation, VIDEO, Weather
```

---

## 🎯 APIs CURADAS POR CATEGORIA (Testadas ao vivo 2026-05-21)

### 1. QUOTES & FRASES — Enriquecer roteiros

```python
# ✅ = testado OK em tempo real | SEM KEY = usa sem configurar secrets

QUOTE_APIS = {
    "AdviceSlip":    "https://api.adviceslip.com/advice",                    # ✅ SEM KEY
    "Affirmations":  "https://www.affirmations.dev/",                        # ✅ SEM KEY
    "StoicQuotes":   "https://stoic-quotes.com/api/quote",                   # ✅ SEM KEY
    "ZenQuotes":     "https://zenquotes.io/api/random",                      # ✅ SEM KEY (rate limit leve)
    "Quotable":      "https://api.quotable.io/quotes?tags=wisdom&limit=5",   # ✅ SEM KEY
    "Forismatic":    "http://api.forismatic.com/api/1.0/?method=getQuote&format=json",  # SEM KEY
    "OnThisDay":     "https://history.muffinlabs.com/date",                  # SEM KEY — fatos históricos
    "NumbersFact":   "http://numbersapi.com/{n}/trivia",                     # SEM KEY — trivia numérica
    "UselessFacts":  "https://uselessfacts.jsph.pl/random.json?language=en", # SEM KEY
    "TarotAPI":      "https://tarotapi.dev/api/v1/cards/random",             # SEM KEY — simbolismo
}

# Keywords por série para ZenQuotes:
KEYWORD_MAP = {
    "narcisismo":"relationship", "ansiedade":"anxiety",
    "depressao":"healing",       "trauma":"resilience",
    "impostor":"courage",        "cura":"peace",
    "familia":"family",          "gaslighting":"truth",
    "codependencia":"love",      "apego":"connection",
    "autoestima":"confidence",   "limites":"boundaries",
}

def get_quote_for_serie(serie_slug):
    import requests
    kw = KEYWORD_MAP.get(serie_slug, "wisdom")
    r = requests.get(f"https://zenquotes.io/api/quotes?keyword={kw}", timeout=10)
    data = r.json() if r.status_code == 200 else []
    return data[0] if data else {"q": "A cura começa pelo nome.", "a": "Daniela Coelho"}
```

---

### 2. NLP & ANÁLISE DE SENTIMENTO — Classificar scripts

```python
# ✅ = testado | Para classificar grupos semânticos de scripts

NLP_APIS = {
    # SEM KEY — usar direto
    "LanguageTool":       "https://api.languagetool.org/v2/check",             # ✅ Gramática PT-BR, 20/min
    "Datamuse_sinonimos": "https://api.datamuse.com/words?rel_syn={word}",     # ✅ Sinônimos sem key
    "Free_Dictionary_PT": "https://api.dicionario-aberto.net/word/{word}",     # ✅ PT sem key
    "Free_Dictionary_EN": "https://api.dictionaryapi.dev/api/v2/entries/en/{word}", # ✅ EN sem key

    # COM HF_TOKEN grátis (huggingface.co/settings/tokens)
    "HF_Emotion_PT":  "https://api-inference.huggingface.co/models/pysentimiento/robertuito-emotion-analysis",
    "HF_Emotion_EN":  "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base",
    "HF_ZeroShot":    "https://api-inference.huggingface.co/models/facebook/bart-large-mnli",
    "HF_Summarize":   "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
    "HF_NER":         "https://api-inference.huggingface.co/models/dslim/bert-base-NER",

    # COM KEY GRÁTIS
    "Twinword_Emotion": "https://www.twinword.com/api/emotion_analysis.php",   # 300/mês free
    "Sentino":          "https://api.sentino.org/v2/analyze",                  # Big5 + DISC + emoção
}

# Mapeamento emoção → parâmetro Chatterbox
EMOTION_TO_AUDIO = {
    "joy":         (0.74, 0.26),  # CTA
    "sadness":     (0.95, 0.08),  # CHORO
    "anger":       (0.93, 0.10),  # REVELACAO
    "fear":        (0.87, 0.13),  # PAUSA
    "surprise":    (0.96, 0.09),  # IMPACTO
    "neutral":     (0.82, 0.17),  # NORMAL
    "anticipation":(0.88, 0.12),  # GANCHO
}
```

---

### 3. TRADUÇÃO — PT-BR ↔ EN para keywords e SEO

```python
TRANSLATION_APIS = {
    "MyMemory":       "https://api.mymemory.translated.net/get?q={text}&langpair=pt|en",  # ✅ 10K palavras/dia
    "Lingva":         "https://lingva.ml/api/v1/{src}/{target}/{encoded_text}",           # ✅ SEM KEY
    "LibreTranslate": "https://libretranslate.com/translate",                             # open source
    "DeepL_Free":     "https://api-free.deepl.com/v2/translate",                         # 500K chars/mês
}
# Fallback automático:
def translate_pt_en(text):
    import requests, urllib.parse
    # 1. MyMemory
    r = requests.get(f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair=pt|en", timeout=10)
    if r.status_code == 200: return r.json()["responseData"]["translatedText"]
    # 2. Lingva
    r2 = requests.get(f"https://lingva.ml/api/v1/pt/en/{urllib.parse.quote(text)}", timeout=10)
    if r2.status_code == 200: return r2.json()["translation"]
    return text
```

---

### 4. PESQUISA CIENTÍFICA — Embasar scripts com ciência real

```python
RESEARCH_APIS = {
    # ✅ TESTADOS — produção
    "PubMed":          "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",    # SEM KEY (3/s)
    "CrossRef":        "https://api.crossref.org/works",                                 # ✅ SEM KEY
    "OpenAlex":        "https://api.openalex.org/works?search={query}",                  # 250M artigos
    "Semantic_Scholar":"https://api.semanticscholar.org/graph/v1/paper/search",          # 100/5min

    # EXTRAS sem key
    "Europe_PMC":  "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&format=json",
    "arXiv":       "http://export.arxiv.org/api/query?search_query=ti:{query}",
    "Wikipedia":   "https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
    "OpenLibrary": "https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&jscmd=data&format=json",
}

# Queries por série (usar em search_semantic_scholar ou PubMed):
PSICO_ACADEMIC_QUERIES = {
    "narcisismo":     "narcissistic personality disorder covert Malkin Harvard",
    "apego":          "attachment theory adult Ainsworth Bowlby secure anxious avoidant",
    "gaslighting":    "gaslighting psychological manipulation Robin Stern Yale",
    "ansiedade":      "high functioning anxiety Brené Brown prefrontal cortex burnout",
    "depressao":      "masked depression functional anhedonia dopamine serotonin",
    "trauma":         "complex PTSD van der Kolk body memory somatic therapy",
    "impostor":       "impostor phenomenon Clance 1978 competence high achievers",
    "codependencia":  "codependency emotional dependency Melody Beattie relationships",
    "resiliencia":    "post-traumatic growth resilience Tedeschi Calhoun psychological",
    "neurociencia":   "emotion regulation prefrontal amygdala Siegel UCLA Daniel",
    "limites":        "healthy boundaries Nedra Tawwab self-care relationships",
    "abandono":       "fear of abandonment anxious attachment relationship patterns",
    "autoestima":     "self-esteem therapy CBT Beck cognitive behavioral treatment",
    "familia":        "emotionally immature parents Lindsay Gibson adult children",
}
```

---

### 5. IMAGENS — Geração e banco visual

```python
IMAGE_APIS = {
    # PADRÃO PRODUÇÃO — Supabase banco primeiro
    "Supabase_Bank":  "https://tpjvalzwkqwttvmszvie.supabase.co/rest/v1/image_bank",    # 125 imgs kawaii

    # FALLBACK — Pollinations FLUX (SEM KEY, 1/15s anônimo)
    "Pollinations":   "https://image.pollinations.ai/prompt/{prompt}?width=576&height=1024&model=flux&seed={seed}&nologo=true",
    "Pollinations_v2":"https://gen.pollinations.ai/image/{prompt}",                       # novo unified API

    # AVATARES CONSISTENTES (SEM KEY — seed=daniela sempre igual)
    "DiceBear":       "https://api.dicebear.com/9.x/{style}/svg?seed={seed}&backgroundColor=06060F",

    # PLACEHOLDER
    "Picsum":         "https://picsum.photos/seed/{seed}/576/1024",                      # SEM KEY

    # IA — HuggingFace (com token grátis)
    "HF_FLUX_Schnell":"https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
    "HF_SDXL":        "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
    "HF_Anime":       "https://api-inference.huggingface.co/models/Linaqruf/animagine-xl-3.1",

    # PROCESSAMENTO LOCAL
    "rembg":          "pip install rembg",                     # remover fundo
    "Pillow":         "pip install Pillow",                    # Ken Burns, resize
    "opencv":         "pip install opencv-python",             # frames processing
}

# Prompts base dos personagens (LOCKED)
CHAR_PROMPTS = {
    "daniela": "kawaii chibi anime girl, short dark bob hair, mint-green blouse, gold psi pin, warm smile, big expressive eyes",
    "sara":    "kawaii chibi anime girl, wavy auburn hair, round glasses, yellow cardigan, emotional big eyes",
    "marcos":  "kawaii chibi anime man, styled dark hair, navy blazer, charming calculating smile, villainous expression",
    "ana":     "kawaii chibi anime woman, dark bun, white lab coat, clipboard, authoritative calm, scientific diagram",
    "julia":   "kawaii chibi anime girl, curly dark hair, orange sweater, warm caring expression",
    "lucas":   "kawaii chibi anime man, tired exhausted expression, casual clothes, burnout state",
}
STYLE = "Psych2Go anime flat illustration, soft cream background #F5F0E8, pastel colors, clean line art, no text, no watermarks"
```

---

### 6. ÁUDIO & VOZ — Stack TTS completo

```python
TTS_STACK = {
    # P1 — PADRÃO SHORT: clone George com exag=0.96
    "Chatterbox_MIT":  "pip install chatterbox-tts",                    # MIT, ilimitado, offline
    "George_ref":      "v683_george_1779065193.mp4 — extrair 14s como referência",

    # P2 — PT-BR nativo, 97ms latency
    "Qwen3_TTS":       "HF: Qwen/Qwen3-TTS (Apache 2.0, self-hosted)",

    # P3 — PADRÃO LONG: ThalitaMultilingualNeural
    "EdgeTTS":         "pip install edge-tts",                          # Microsoft, ilimitado
    "EdgeTTS_voice":   "pt-BR-ThalitaMultilingualNeural, rate=+28%",

    # P4 — offline, 82M params, 54 vozes
    "Kokoro":          "pip install kokoro-onnx",

    # P5 — OpenAI voices via Pollinations (SEM KEY)
    "Pollinations_Audio": "https://gen.pollinations.ai/audio",          # nova, shimmer, echo
    "Pollinations_Audio_ex": 'POST {"model":"openai-audio","voice":"nova","input":"texto"}',

    # P6-P8
    "F5_TTS":          "pip install f5-tts",                            # zero-shot PT
    "IndexTTS":        "pip install indextts",                          # Bilibili Apache
    "Coqui_TTS":       "pip install TTS",                               # open source clássico

    # BACKUP ElevenLabs (quota ~32K chars/mês free, reinicia ~jun/2026)
    "ElevenLabs_George": "voice_id=JBFqnCBsd6RMkjVDRZzb, stability=0.20, similarity=0.85",
}

# Parâmetros V31 — LOCKED
TIPOS_AUDIO_V31 = {
    "GANCHO":    (0.88, 0.12, 0.0,  0.8),   # (exag, cfg, sil_pre, sil_pos)
    "IMPACTO":   (0.96, 0.09, 1.0,  1.6),   # + camera shake Remotion
    "CHORO":     (0.95, 0.08, 0.5,  1.8),   # novo V31
    "REVELACAO": (0.93, 0.10, 0.7,  1.4),
    "PAUSA":     (0.87, 0.13, 0.4,  1.1),
    "CTA":       (0.74, 0.26, 0.9,  0.0),
    "NORMAL":    (0.82, 0.17, 0.0,  0.65),
}
GATE_SEG   = "agate=threshold=0.028:ratio=8000:attack=1:release=60"    # por segmento
GATE_FINAL = "highpass=f=80,agate=threshold=0.028:ratio=8000:attack=2:release=50"

# Música de fundo para Longs (Longs 15min precisam de trilha)
MUSIC_APIS = {
    "Jamendo":     "https://api.jamendo.com/v3.0/tracks/",              # CC, grátis
    "FMA":         "https://freemusicarchive.org/api/",                 # CC, grátis
    "Incompetech": "https://incompetech.filmmusic.io/",                 # Kevin MacLeod CC
    "Freesound":   "https://freesound.org/apiv2/search/text/",          # key grátis 60/dia
}
```

---

### 7. LLMs GRATUITOS — Router V4

```python
LLM_FREE_APIS = {
    # ✅ TIER FREE PERMANENTE — key necessária mas grátis para criar

    "nvidia_nim": {
        "url":    "https://integrate.api.nvidia.com/v1",
        "models": ["deepseek-ai/deepseek-v4-pro", "meta/llama-3.3-70b-instruct", "qwen3-coder"],
        "limit":  "40 req/min", "key": "build.nvidia.com",
        "role":   "DEFAULT — script + análise"
    },
    "groq": {
        "url":    "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "llama-4-maverick", "deepseek-r1-distill-llama-70b"],
        "limit":  "14.400 req/dia, 315 tokens/s", "key": "console.groq.com",
        "role":   "FALLBACK 1 — rápido"
    },
    "google_aistudio": {
        "url":    "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro"],
        "limit":  "1.500 req/dia", "key": "aistudio.google.com",
        "role":   "scripts longos, análise profunda"
    },
    "cerebras": {
        "url":    "https://api.cerebras.ai/v1",
        "models": ["Meta-Llama-3.1-405B", "DeepSeek-R1-671B"],
        "limit":  "1M tokens/dia", "key": "cloud.cerebras.ai",
        "role":   "Ultra-rápido para scripts"
    },
    "openrouter_free": {
        "url":    "https://openrouter.ai/api/v1",
        "models": ["qwen/qwen3-235b:free", "meta-llama/llama-3.3-70b:free", "deepseek/deepseek-r1:free"],
        "limit":  "50 req/dia free tier", "key": "openrouter.ai"
    },
    "mistral": {
        "url":    "https://api.mistral.ai/v1",
        "models": ["mistral-small-latest", "codestral-2501"],
        "limit":  "1B tokens/mês grátis", "key": "console.mistral.ai"
    },
    "github_models": {
        "url":    "https://models.inference.ai.azure.com",
        "models": ["gpt-5", "gpt-4.1", "o4-mini", "Llama-3.3-70B"],
        "limit":  "50 chat + 2K completions/mês", "key": "GitHub Personal Access Token"
    },
    "sambanova": {
        "url":    "https://api.sambanova.ai/v1",
        "models": ["Meta-Llama-3.1-405B", "DeepSeek-R1-671B", "Qwen3-235B"],
        "limit":  "$5 grátis 3 meses", "key": "cloud.sambanova.ai"
    },
    "pollinations_llm": {
        "url":    "https://gen.pollinations.ai/v1",
        "models": ["openai-large", "claude", "gemini", "deepseek", "qwen3-coder"],
        "limit":  "1 req/15s SEM KEY ALGUMA", "key": "Nenhuma"
    },
    "ollama_local": {
        "url":    "http://localhost:11434/api",
        "models": ["llama3.3", "qwen3", "deepseek-r1", "phi4", "gemma3"],
        "limit":  "Ilimitado local", "key": "Nenhuma — ollama.ai"
    },
}

# LLMRouter V4 — fallback automático
LLM_ROUTER_V4 = [
    ("nvidia",  "deepseek-ai/deepseek-v4-pro"),     # 1. PRIMARY
    ("nvidia",  "meta/llama-3.3-70b-instruct"),     # 2. NVIDIA fallback
    ("groq",    "llama-3.3-70b-versatile"),          # 3. Groq
    ("openai",  "gpt-4o-mini"),                      # 4. OpenAI paid
]
```

---

### 8. VÍDEO & ANIMAÇÃO — Dois engines

```python
VIDEO_ENGINES = {
    # ENGINE 1: Remotion React (NOVO V32 — animações superiores ao Psych2Go)
    "Remotion": {
        "install":  "cd remotion && npm install && npx remotion browser ensure",
        "render":   "npx remotion render src/index.tsx PsychShort out.mp4 --props=props.json",
        "features": [
            "Spring physics word-by-word (palavra por palavra com bounce)",
            "Camera shake em linhas IMPACTO",
            "Personagem flutuando (float sinusoidal)",
            "Halo pulsante ao redor do personagem",
            "Partículas ψ no background",
            "Gradiente radial animado por tipo semântico",
            "Lower third slide-in com backdrop blur",
            "Emojis flutuantes no CTA (💾🔔❤️)",
            "Progress bar no topo",
            "Ken Burns com parallax avançado",
        ],
        "componentes": {
            "remotion/src/index.tsx":                    "Root registry",
            "remotion/src/compositions/PsychShort.tsx":  "Short 9:16 58s 1740 frames",
            "remotion/src/components/Background.tsx":    "Gradiente + partículas ψ",
            "remotion/src/components/AnimatedText.tsx":  "Word-by-word spring",
            "remotion/src/components/CharacterCard.tsx": "Float + halo",
            "remotion/src/components/LowerThird.tsx":    "Slide-in blur",
            "remotion/src/components/ProgressBar.tsx":   "Barra + emojis CTA",
        },
        "workflow": ".github/workflows/render-remotion-short.yml",
        "licenca":  "Grátis para indivíduos e empresas < $1M receita"
    },

    # ENGINE 2: FFmpeg (ATUAL — Ken Burns clássico)
    "FFmpeg": {
        "install":  "apt install ffmpeg",
        "features": ["Ken Burns zoom 0/4/8%", "Gate noise por segmento", "Fade in/out"],
        "workflow": ".github/workflows/render-short-george.yml",
    },
}

VIDEO_APIS = {
    "YouTube_Data_v3":  "https://www.googleapis.com/youtube/v3",             # 10K units/dia
    "YouTube_Analytics":"https://youtubeanalytics.googleapis.com/v2",
    "yt_dlp":           "pip install yt-dlp",                                # análise local
    "YT_Transcript":    "pip install youtube-transcript-api",                # legendas
    "Shotstack":        "https://api.shotstack.io/edit/stage/render",        # cloud render
    "HF_CogVideoX":     "THUDM/CogVideoX-5b",                               # open source Apache
}
```

---

### 9. SOCIAL MEDIA & ANALYTICS

```python
SOCIAL_APIS = {
    # YOUTUBE (canal principal)
    "YT_Upload":    "https://www.googleapis.com/upload/youtube/v3/videos",
    "YT_OAuth":     "psidanielacoelho1982@gmail.com — ❌ PENDENTE CONFIGURAR",

    # INSTAGRAM (futuro 2026-Q3)
    "Instagram_Basic":"https://graph.instagram.com/me",
    "Instagram_Graph":"https://graph.facebook.com/v20.0/{id}/media",

    # TIKTOK (futuro 2026-Q4)
    "TikTok_Creator": "https://open.tiktokapis.com/v2/post/publish/",

    # TENDÊNCIAS (sem key)
    "Google_Trends":  "pip install pytrends",                                # sem key
    "Reddit_Top":     "https://www.reddit.com/r/{sub}/top.json",            # sem key (básico)
    "Social_Searcher":"https://api.social-searcher.com/v2/posts?q={q}",    # 100/dia

    # ANALYTICS
    "GoogleTrends_BR": "TrendReq(hl='pt-BR',tz=180).build_payload(['ansiedade'],geo='BR')",
}
```

---

### 10. UTILIDADES — Infraestrutura do pipeline

```python
UTIL_APIS = {
    # ✅ TESTADOS
    "IBGE":         "https://servicodados.ibge.gov.br/api/v3/",         # SEM KEY — dados BR
    "BrasilAPI":    "https://brasilapi.com.br/api/",                    # SEM KEY — CEP, feriados
    "ViaCEP":       "https://viacep.com.br/ws/{cep}/json/",             # SEM KEY
    "TinyURL":      "https://tinyurl.com/api-create.php?url={url}",    # SEM KEY — encurtar links
    "ipapi":        "https://ipapi.co/json/",                           # SEM KEY — localização

    # SUPABASE (projeto principal)
    "Supabase_DB":      "https://tpjvalzwkqwttvmszvie.supabase.co/rest/v1/",
    "Supabase_Storage": "https://tpjvalzwkqwttvmszvie.supabase.co/storage/v1/object/",
    "Supabase_EF":      "https://tpjvalzwkqwttvmszvie.supabase.co/functions/v1/",

    # IMAGEM — upload externo
    "Cloudinary":   "https://api.cloudinary.com/v1_1/",                # 25GB grátis
    "Imgbb":        "https://api.imgbb.com/1/upload",                   # key grátis
    "TinyPNG":      "https://api.tinify.com",                           # 500/mês grátis

    # DADOS ABERTOS BRASIL
    "Portal_Gov_BR":"https://dados.gov.br/api/3/action/",
    "DataSUS":      "https://datasus.saude.gov.br/",
    "CFP_API":      "https://site.cfp.org.br/",                         # Conselho Federal de Psicologia
}

# Função central de enriquecimento de script (usa múltiplas APIs):
def enrich_script(script_text, serie_slug, ep_num=1):
    """Enriquece script com citação científica + frase + hashtags + emoção"""
    results = {}
    # 1. Citação acadêmica
    from psicologia_apis import search_semantic_scholar, PSICO_ACADEMIC_QUERIES
    query = PSICO_ACADEMIC_QUERIES.get(serie_slug, serie_slug + " psychology")
    papers = search_semantic_scholar(query, limit=3)
    if papers:
        p = papers[0]
        authors = [a["name"].split()[-1] for a in p.get("authors",[])[:2]]
        results["citation"] = f"{', '.join(authors)} ({p.get('year','')}): {p.get('title','')[:80]}"
    # 2. Quote inspiradora
    results["opening_quote"] = get_quote_for_serie(serie_slug)
    # 3. Hashtags
    results["hashtags"] = generate_hashtags(serie_slug, ep_num)
    return results
```

---

## 🎤 PIPELINE ÁUDIO V31 — PARÂMETROS TRAVADOS

```python
# Verificação obrigatória:
# ffmpeg -i audio.wav -af "astats=metadata=1" -f null - 2>&1 | grep "RMS trough"
# ESPERADO: "RMS trough dB: -inf" ✅

GATE_SEG   = "agate=threshold=0.028:ratio=8000:attack=1:release=60"     # por segmento
GATE_FINAL = "highpass=f=80,agate=threshold=0.028:ratio=8000:attack=2:release=50"
FADE_IN    = 60    # ms
FADE_OUT   = 60    # ms
SILENCE_CODEC = "pcm_s16le"  # SEMPRE — zeros absolutos

# George ref: v683_george_1779065193.mp4 → extrair 14s com highpass+lowpass+vol
```

---

## 📊 ESTADO DOS 400 VÍDEOS

```
Tabelas Supabase:
  content_series    → 20 séries
  series_episodes   → 200 episódios
  video_plan_400    → 400 registros (200 short + 200 long)
  content_pipeline  → IDs 682-721 alocados

Shorts prontos (6 com vídeo, 3 renderizando):
  ✅ #683 Narcisismo — Laís   (âncora viral)
  ✅ #682 Vício Emocional — Rafael
  ✅ #684 Ansiedade — Sofia
  ✅ #688 Neurociência — Lucas
  ✅ #689 Impostor — Marina
  ✅ #701 Depressão — Carla
  ⏳ #710 Gaslighting — Juliana
  ⏳ #711 Vício/Ex — Camila
  ⏳ #712 Família — Você

Longs scripts prontos (9): IDs 713-721

As 20 séries:
  narcisismo, apego, gaslighting, infancia, ansiedade, depressao,
  limites, autoestima, relacionamentos, codependencia, impostor,
  abandono, cura, amorporprio, trauma, manipulacao, cerebro,
  vicoemocional, familia, resiliencia
```

---

## 🎬 REMOTION — Detalhes Técnicos

```
Resolução: 576×1024 (9:16)
FPS: 30
Duração: 1740 frames = 58 segundos
Codec: H.264

Props JSON gerado por: scripts/render_remotion_short.py
Workflow: .github/workflows/render-remotion-short.yml
Browser: npx remotion browser ensure (não usar chromium-browser apt — falha Ubuntu 24)

Componentes:
  Background.tsx:    Gradiente radial pulsante + grid + 6 partículas ψ
  AnimatedText.tsx:  spring() Remotion, damping 8-12, stiffness 180-250
  CharacterCard.tsx: float sinusoidal amplitude=6 period=150 + halo opacity 0.08-0.22
  LowerThird.tsx:    translateX spring(200→0) + backdrop blur
  ProgressBar.tsx:   width% linear + CTAEmojis floating keyframes
  PsychShort.tsx:    Composição principal — combina tudo + <Audio src={audioUrl}/>
```

---

## IMAGENS — SINCRONIZAÇÃO

```python
# REGRA: cada imagem reflete a frase que está sendo dita (não genérica)
CHAR_CONTEXT_MAP = {
    "grita|bate|humilha|perigoso|calculista": "marcos villainous expression, dark aura",
    "chora|triste|culpada|errada|machucada":  "sara crying, confused, hurt",
    "salva|canal|assiste|inscrev|sino":        "daniela pointing to camera, golden bell 🔔",
    "harvard|ciência|pesquisa|estudo":         "ana pointing at whiteboard, scientific diagram",
    "não está exagerando|você não é":          "daniela caring, empowering gesture",
    "isso tem nome|mecanismo|padrão":          "ana labeled diagram, serious expression",
    "afastar|terminar|sair|deixar":            "sara trying to leave, being held back",
    "DEFAULT":                                  "daniela speaking directly, engaged expression"
}

# Validação obrigatória (Pollinations pode retornar HTML):
def is_valid_img(content):
    return len(content) > 5000 and content[:3] in (
        b'\xff\xd8\xff',  # JPEG
        b'\x89PN',        # PNG
        b'\x89PG'         # PNG variante
    )
```

---

## PERSONAGENS (LOCKED)

```python
DANIELA = "kawaii chibi anime girl, short dark bob hair, mint-green blouse, gold psi pin, warm smile"
SARA    = "kawaii chibi anime girl, wavy auburn hair, round glasses, yellow cardigan, emotional big eyes"
MARCOS  = "kawaii chibi anime man, styled dark hair, navy blazer, charming calculating smile"
JULIA   = "kawaii chibi anime girl, curly dark hair, orange sweater, warm caring expression"
ANA     = "kawaii chibi anime woman, dark bun, white lab coat, clipboard, authoritative calm"
LUCAS   = "kawaii chibi anime man, tired exhausted expression, casual clothes, burnout"
STYLE   = "Psych2Go anime flat illustration, soft cream background #F5F0E8, pastel colors, clean line art, no text, no watermarks"
```

---

## VIRAL MIRROR

```
Tabela: viral_videos_reference (18 refs, 1.8M–28M views)
Top: Psych2Go Covert Narcissist 28M | Abandonment 22M | Childhood Trauma 19M

Fórmulas virais:
  "N Sinais + [condição invisível]"    CTR 8-12%
  "Não é X, é Y"                       CTR 10-15%
  "Revelação perigo oculto"            CTR 12-18% ← 28M

Script Psych2Go V31:
  Hook: "Você conhece [Nome]? [Cena de dor real]"
  Min 1: "Isso não é [nome óbvio]. É [nome científico]."
  Revelação: "Pesquisadores de [Harvard/UCLA] chamam de..."
  Curiosity gap: "No vídeo completo: o sinal mais PERIGOSO."
  CTA: "SALVA agora para não perder. 💾🔔"
```

---

## ORDEM DE PUBLICAÇÃO

```
Âncora:  #683 Narcisismo → #701 Depressão → #682 Celular → #689 Impostor
Horário: 18-20h BR (UTC-3)
Canal:   UCyCkIpsVgME9yCj_oXJFheA (psidanielacoelho1982@gmail.com) EXCLUSIVO
Lower third: NUNCA mostrar "Psicóloga" até jan/2027
```

---

## CREDENCIAIS

```
✅ GH_PAT, Supabase, Groq, NVIDIA, OpenAI, HF_TOKEN
⚠️ ELEVENLABS (quota ~32K chars → Chatterbox padrão)
❌ FALTA: YouTube OAuth psidanielacoelho1982@gmail.com
❌ FALTA: GEMINI_API_KEY (grátis em aistudio.google.com)
❌ FALTA: INSTAGRAM_TOKEN, TIKTOK_TOKEN
```

---

## ESTRATÉGIA R$50K/MÊS

```
RPM BR psicologia: R$10-16
Meta: 3.5M views/mês × R$15 RPM = R$50K
Mês 3-4: 10K subs → R$3K | Mês 9-10: 300K subs → R$50K
Shorts → subs | Longs → mid-rolls (3/6/9/12min)
```

---

## PAINEL 400 VÍDEOS

```
Séries × episódios × formatos:
20 × 10 × 2 = 400 vídeos
Arco 10 episódios: E01 GANCHO → E02 PROBLEMA → E03 CIENCIA →
  E04 CUSTO → E05 VIRADA → E06 FERRAMENTA → E07 PRATICA →
  E08 RECAIDA → E09 TRANSFORMACAO → E10 FINAL
```

---

## MÓDULO psicologia_apis.py

```python
# scripts/psicologia_apis.py — importar em qualquer script
from psicologia_apis import (
    get_zen_quote,            # citação por keyword
    get_advice,               # conselho aleatório (AdviceSlip)
    get_affirmation,          # afirmação positiva
    get_stoic_quote,          # Epicteto/Marco Aurélio
    get_quotable,             # por tag: psychology, wisdom, healing
    analyze_emotion_hf,       # emoção PT-BR via HuggingFace
    translate_pt_en,          # tradução MyMemory → Lingva fallback
    check_grammar_languagetool, # gramática PT-BR
    search_pubmed,            # artigos psicologia
    search_semantic_scholar,  # IA para busca acadêmica
    search_crossref,          # citações e DOIs
    gen_image_pollinations,   # URL Pollinations FLUX
    gen_image_dicebear,       # avatar consistente por seed
    generate_hashtags,        # hashtags otimizadas BR
    enrich_script,            # enriquecer script com tudo
    PSICO_ACADEMIC_QUERIES,   # queries por série
)
```
