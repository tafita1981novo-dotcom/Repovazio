---
name: psicologia-doc-v27
description: Use esta SKILL sempre que o usuário mencionar: psicologia.doc, repovazio, Daniela Coelho, @psidanielacoelho, canal YouTube psicologia, viral, cérebro autônomo, tokens sociais, Instagram, TikTok, WhatsApp grupos, monetização, 1000 subs, crescimento, setup tokens, espelhamento viral.
version: 32.0 — API OMNIBUS
date: 2026-05-21
---

# SKILL psicologia.doc V32 — API OMNIBUS COMPLETA

> Integra milhares de APIs públicas de 7 diretórios globais, curadas e testadas para o pipeline de vídeo psicologia.doc

---

## ⚠️ REGRA DE OURO

```
NUNCA liberar vídeo sem testar #683 primeiro.
RMS trough = -inf obrigatório. Gate duplo por segmento + global.
```

---

## INFRA CORE

```
Supabase: tpjvalzwkqwttvmszvie | Vercel: repovazio.vercel.app | GitHub: tafita81/Repovazio
Canal ATIVO:   UCyCkIpsVgME9yCj_oXJFheA · @psidanielacoelho
Canal ⛔:      UCSH63tBfY6wEIdkC4u4zKdg — BLOQUEADO, NUNCA publicar
Módulo APIs:   scripts/psicologia_apis.py (51+ APIs integradas)
```

---

## 📚 OS 7 DIRETÓRIOS DE APIs PÚBLICAS (FONTE PRINCIPAL)

```python
API_DIRECTORIES = {
    "public_apis_github": {
        "url": "https://github.com/public-apis/public-apis",
        "total": "1400+ APIs",
        "categorias": 51,
        "destaque": "Mais completo e atualizado — mantido por comunidade",
        "uso": "Referência principal para descobrir novas APIs",
        "json_api": "https://api.publicapis.org/entries",  # buscar programaticamente
        "categorias_lista": [
            "Animals", "Anime", "Anti-Malware", "Art & Design",
            "Authentication", "Books", "Business", "Calendar",
            "Cloud Storage", "Cryptocurrency", "Currency Exchange",
            "Data Validation", "Development", "Dictionaries",
            "Documents & Productivity", "Email", "Environment",
            "Events", "Finance", "Food & Drink", "Games & Comics",
            "Geocoding", "Government", "Health", "Jobs",
            "Machine Learning", "Music", "News", "Open Data",
            "Patent", "Personality", "Photography",
            "Science & Math", "Security", "Shopping", "Social",
            "Sports & Fitness", "Text Analysis", "Tracking",
            "Transportation", "URL Shorteners", "Vehicle",
            "Video", "Weather"
        ]
    },
    "publicapis_dev": {
        "url": "https://publicapis.dev",
        "total": "1400+ APIs",
        "destaque": "Melhor UI, filtros avançados, uptime stats",
        "busca_prog": "https://publicapis.dev/api/search?query={termo}",
        "categorias_psico": [
            "personality", "text-analysis", "machine-learning",
            "health", "books", "science", "social"
        ]
    },
    "public_apis_io": {
        "url": "https://public-apis.io",
        "total": "1000+ APIs",
        "destaque": "Categorias: filmes, anime, clima, música, jogos",
        "busca": "https://public-apis.io/category/{categoria}"
    },
    "publicapis_io": {
        "url": "https://publicapis.io",
        "total": "1000+ APIs",
        "destaque": "Inclui chaves, exemplos de código, documentação",
        "busca": "https://publicapis.io/category/{categoria}"
    },
    "public_api_lists": {
        "url": "https://github.com/public-api-lists/public-api-lists",
        "total": "1000+ APIs",
        "categorias": 48,
        "destaque": "Pesquisável, com API JSON própria",
        "json_api": "https://public-api-lists.github.io/public-api-lists/apis.json"
    },
    "mixedanalytics": {
        "url": "https://mixedanalytics.com/blog/list-actually-free-open-no-auth-needed-apis/",
        "total": "~200 APIs",
        "destaque": "FOCO: APIs SEM AUTH — usar sem nenhuma chave",
        "uso": "Quando precisar de API para GitHub Actions sem configurar secrets"
    },
    "rapidapi": {
        "url": "https://rapidapi.com",
        "total": "40.000+ APIs",
        "destaque": "Maior marketplace — maioria tem free tier",
        "uso": "Quando não encontrar no gratuito puro — verificar free tier"
    }
}

# Como descobrir novas APIs programaticamente:
def find_api(category, no_auth=True):
    """Buscar API no diretório público sem autenticação"""
    import requests
    r = requests.get(
        f"https://api.publicapis.org/entries?category={category}&auth={'null' if no_auth else ''}",
        timeout=10
    )
    return r.json().get("entries", [])
```

---

## 🎯 APIs CURADAS POR USO NO PIPELINE (as 51 categorias aplicadas)

### CATEGORIA 1 — QUOTES & FRASES PSICOLÓGICAS

```python
# TODAS SEM AUTH — usar em qualquer contexto
QUOTE_APIS = {
    # ✅ TESTADAS AO VIVO
    "ZenQuotes":     "https://zenquotes.io/api/random",              # wisdom, healing, resilience
    "AdviceSlip":    "https://api.adviceslip.com/advice",            # conselhos aleatórios
    "Affirmations":  "https://www.affirmations.dev/",                # afirmações positivas
    "StoicQuotes":   "https://stoic-quotes.com/api/quote",           # Epicteto, Marco Aurélio
    "Quotable":      "https://api.quotable.io/quotes?tags=wisdom",   # por tag: psychology, healing
    "Forismatic":    "http://api.forismatic.com/api/1.0/?method=getQuote&format=json",

    # EXTRAS (publicapis.dev/category/personality)
    "BreakingBad":   "https://breakingbadquotes.xyz/v1/quotes",      # quotes dramáticas (estilo script)
    "KanyeRest":     "https://api.kanye.rest/",                      # quotes inesperadas (criatividade)
    "RonSwanson":    "https://ron-swanson-quotes.herokuapp.com/v2/quotes", # humor/sabieza
    "TarotAPI":      "https://tarotapi.dev/api/v1/cards/random",     # cartas simbólicas (visual)
    "EvilInsult":    "https://evilinsult.com/generate_insult.php?lang=en&type=json", # antagonista
    "YoMomma":       "https://api.yomomma.info/",                    # humor desconstruído
    "OnThisDay":     "https://history.muffinlabs.com/date",          # fatos históricos por data
    "NumbersFact":   "http://numbersapi.com/{n}/trivia",             # trivia numérica para roteiros
    "Uselessfacts":  "https://uselessfacts.jsph.pl/random.json?language=en", # fatos curiosos
    "CatFact":       "https://catfact.ninja/fact",                   # analogias com gatos (viral)
}

# Uso no script: enriquecer abertura com citação relevante
def get_opening_quote(tema):
    import requests
    kw_map = {
        "narcisismo":"relationship","ansiedade":"anxiety","depressao":"healing",
        "trauma":"resilience","impostor":"courage","cura":"peace","familia":"family",
        "gaslighting":"truth","codependencia":"love","apego":"connection"
    }
    kw = kw_map.get(tema, "wisdom")
    r = requests.get(f"https://zenquotes.io/api/quotes?apikey=&keyword={kw}", timeout=10)
    data = r.json() if r.status_code==200 else []
    return data[0] if data else {"q": "A cura começa pelo nome.", "a": "Daniela Coelho"}
```

---

### CATEGORIA 2 — ANÁLISE DE SENTIMENTO & NLP (TEXT ANALYSIS)

```python
# Do diretório public-apis: categoria "Text Analysis" (21 APIs) + "Machine Learning" (30 APIs)
NLP_APIS = {
    # SEM AUTH OU FREE TIER GENEROSO
    "LanguageTool":     "https://api.languagetool.org/v2/check",           # ✅ gramática PT-BR
    "Lingva":           "https://lingva.ml/api/v1/{src}/{target}/{text}",  # ✅ tradução sem key
    "MyMemory":         "https://api.mymemory.translated.net/get",         # ✅ 10K palavras/dia
    "LibreTranslate":   "https://libretranslate.com/translate",            # open source
    "HF_Emotion_PT":    "https://api-inference.huggingface.co/models/pysentimiento/robertuito-emotion-analysis",
    "HF_NER":           "https://api-inference.huggingface.co/models/dslim/bert-base-NER",
    "HF_Summarize":     "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
    "HF_Zero_Shot":     "https://api-inference.huggingface.co/models/facebook/bart-large-mnli",

    # COM FREE KEY
    "Twinword_Emotion": "https://www.twinword.com/api/emotion_analysis.php",  # 300/mês
    "Sentino":          "https://api.sentino.org/v2/analyze",                 # Big5, DISC
    "PerspectiveAPI":   "https://commentanalyzer.googleapis.com/v1alpha1",    # toxicidade
    "Google_NLP":       "https://language.googleapis.com/v1/documents:analyzeSentiment",

    # FERRAMENTAS DE PARÁFRASE E REESCRITA
    "Quillbot":         "https://quillbot.com/api/paraphrase",               # (requer key)
    "Wordnik":          "https://api.wordnik.com/v4/word.json/{word}/definitions",  # definições
    "Datamuse":         "https://api.datamuse.com/words?rel_syn={word}",     # sinônimos sem auth
    "WordsAPI":         "https://wordsapiv1.p.rapidapi.com/words/{word}",    # RapidAPI free tier

    # ANÁLISE DE KEYWORDS
    "RAKE_local":       "pip install rake-nltk",                              # local, sem api
    "KeyBERT_local":    "pip install keybert",                                # local, sem api
}

# Mapeamento emoção → parâmetro de voz Chatterbox
EMOTION_TO_AUDIO = {
    "joy":         (0.74, 0.26),   # CTA style
    "sadness":     (0.95, 0.08),   # CHORO style
    "anger":       (0.93, 0.10),   # REVELACAO style
    "fear":        (0.87, 0.13),   # PAUSA style
    "surprise":    (0.96, 0.09),   # IMPACTO style
    "disgust":     (0.90, 0.11),   # PROBLEMA style
    "neutral":     (0.82, 0.17),   # NORMAL style
    "anticipation":(0.88, 0.12),   # GANCHO style
}
```

---

### CATEGORIA 3 — IMAGENS & ARTE (Art & Design + Photography)

```python
# Do diretório: "Art & Design" + "Photography" + "Placeholder Images"
IMAGE_APIS = {
    # SEM AUTH — PRODUÇÃO
    "Pollinations_FLUX":  "https://image.pollinations.ai/prompt/{prompt}?width=576&height=1024&model=flux&nologo=true",
    "Pollinations_Gen":   "https://gen.pollinations.ai/image/{prompt}",           # novo unified
    "DiceBear":           "https://api.dicebear.com/9.x/{style}/svg?seed={seed}", # avatares SVG
    "Picsum":             "https://picsum.photos/seed/{seed}/{w}/{h}",            # placeholder
    "Lorem_Picsum":       "https://picsum.photos/{w}/{h}",                        # simples
    "Unsplash_Source":    "https://source.unsplash.com/{w}x{h}/?{keyword}",      # fotos reais

    # GERAÇÃO IA (free tier)
    "HF_FLUX_Schnell":   "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
    "HF_SDXL":           "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
    "HF_Anime_Diffusion":"https://api-inference.huggingface.co/models/Linaqruf/animagine-xl-3.1",
    "Puter_AI_Img":      "CDN: https://cdn.puter.com/puter.js → puter.ai.txt2img()",
    "ZSky_Image":        "https://zsky.ai/api/v1/image/generate",                # 1080p

    # PROCESSAMENTO DE IMAGEM
    "Remove_BG_local":   "pip install rembg",                                     # remover fundo
    "Pillow_local":      "pip install Pillow",                                    # Ken Burns, resize
    "PhotoRoom_API":     "https://sdk.photoroom.com/v1/segment",                  # remoção bg (key)
    "TinyPNG":           "https://api.tinify.com",                                # compressão
    "Cloudinary":        "https://api.cloudinary.com/v1_1/demo/image/upload",    # free 25GB

    # BANCO INTERNO SUPABASE (PRIMÁRIO)
    "Supabase_Bank":     "https://tpjvalzwkqwttvmszvie.supabase.co/rest/v1/image_bank",
}

# Personagens → prompt base
CHAR_PROMPTS = {
    "daniela": "kawaii chibi anime girl, short dark bob hair, mint-green blouse, gold psi pin, warm smile, Psych2Go style, soft cream background",
    "sara":    "kawaii chibi anime girl, wavy auburn hair, round glasses, yellow cardigan, emotional eyes, crying or confused",
    "marcos":  "kawaii chibi anime man, styled dark hair, navy blazer, charming calculating smile, villainous expression",
    "ana":     "kawaii chibi anime woman, dark bun, white lab coat, clipboard, authoritative calm, scientific diagram",
    "julia":   "kawaii chibi anime girl, curly dark hair, orange sweater, warm caring expression",
    "lucas":   "kawaii chibi anime man, tired exhausted expression, casual clothes, can't get out of bed",
}
STYLE = "flat illustration, pastel colors, clean line art, no text, no watermarks, vertical 9:16"
```

---

### CATEGORIA 4 — ÁUDIO & MÚSICA (Music + Audio)

```python
# Do diretório: "Music" (33 APIs) + Audio generation
AUDIO_APIS = {
    # TTS — PADRÃO (ver seção dedicada)
    "Chatterbox":     "MIT — pip install chatterbox-tts",                  # P1: clone George
    "Qwen3_TTS":      "HF: Qwen/Qwen3-TTS — Apache 2.0",                  # P2: PT-BR nativo
    "EdgeTTS":        "pip install edge-tts",                              # P3: ThalitaNeural
    "Kokoro":         "pip install kokoro-onnx",                           # P4: offline 82M
    "Pollinations_Au":"https://gen.pollinations.ai/audio",                 # P5: OpenAI voices
    "F5_TTS":         "pip install f5-tts",                                # P6: zero-shot PT
    "IndexTTS":       "pip install indextts",                              # P7: Bilibili Apache
    "Coqui_TTS":      "pip install TTS",                                   # P8: open source

    # MÚSICA DE FUNDO (para Longs 15min)
    "Free_Music_Archive": "https://freemusicarchive.org/api/",             # CC licensed
    "Jamendo":        "https://api.jamendo.com/v3.0/tracks/",              # free CC music
    "Incompetech":    "https://incompetech.filmmusic.io/",                 # Kevin MacLeod CC
    "ccMixter":       "https://ccmixter.org/api/",                         # CC remixable
    "Pixabay_Audio":  "https://pixabay.com/api/?key={key}&type=music",    # free tier
    "Freesound":      "https://freesound.org/apiv2/search/text/",          # CC sounds
    "OpenGameArt":    "https://opengameart.org/api/",                      # CC game audio
    "SoundHelix":     "https://www.soundhelix.com/audio-examples/",        # procedural music

    # ANÁLISE DE ÁUDIO
    "AudD":           "https://api.audd.io/",                             # reconhecimento de música
    "ACRCloud":       "https://identify-eu-west-1.acrcloud.com/",         # fingerprinting
    "Essentia_local": "pip install essentia",                              # análise offline

    # EFEITOS SONOROS
    "Zapsplat":       "https://api.zapsplat.com/",                        # SFX (key grátis)
    "SoundBible":     "https://soundbible.com/",                          # CC sound effects
}
```

---

### CATEGORIA 5 — PESQUISA CIENTÍFICA (Science & Math + Health)

```python
# Do diretório: "Science & Math" (34 APIs) + "Health" (30 APIs)
SCIENCE_APIS = {
    # SEM AUTH — PRODUÇÃO
    "PubMed":         "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",  # ✅
    "Semantic_Scholar":"https://api.semanticscholar.org/graph/v1/paper/search",       # ✅
    "CrossRef":       "https://api.crossref.org/works",                               # ✅
    "OpenAlex":       "https://api.openalex.org/works?search={query}",               # 250M artigos
    "Europe_PMC":     "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
    "arXiv":          "http://export.arxiv.org/api/query?search_query=ti:{query}",   # preprints
    "CORE_API":       "https://api.core.ac.uk/v3/search/works",                      # open access
    "Unpaywall":      "https://api.unpaywall.org/v2/{doi}?email=test@test.com",      # PDF grátis

    # DADOS SAÚDE MENTAL
    "WHO_API":        "https://ghoapi.azureedge.net/api/",                           # OMS dados
    "DataSUS":        "https://servicodados.ibge.gov.br/api/v3/",                   # IBGE Brasil
    "OpenFDA":        "https://api.fda.gov/drug/event.json",                         # FDA dados
    "CDC_API":        "https://data.cdc.gov/resource/",                              # CDC EUA

    # EDUCAÇÃO & REFERÊNCIAS
    "Wikipedia":      "https://en.wikipedia.org/api/rest_v1/page/summary/{title}",  # resumos
    "WikiData":       "https://www.wikidata.org/w/api.php",                          # dados estruturados
    "OpenLibrary":    "https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&jscmd=data&format=json",
    "GoogleBooks":    "https://www.googleapis.com/books/v1/volumes?q={query}",       # key grátis
    "InternetArchive":"https://archive.org/advancedsearch.php",                      # livros históricos

    # VOCABULÁRIO PSICOLÓGICO
    "Wordnik":        "https://api.wordnik.com/v4/word.json/{word}/definitions",
    "MerriamWebster": "https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}",
    "Free_Dictionary":"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",      # sem auth
    "PT_Dictionary":  "https://api.dicionario-aberto.net/word/{word}",               # PT sem auth
}

# Queries específicas para psicologia.doc
PSICO_ACADEMIC_QUERIES = {
    "narcisismo":     "narcissistic personality disorder covert Malkin Harvard 2015",
    "apego":          "attachment theory adult Ainsworth Bowlby secure anxious avoidant",
    "gaslighting":    "gaslighting psychological manipulation Robin Stern Yale",
    "ansiedade":      "high functioning anxiety Brené Brown prefrontal cortex burnout",
    "depressao":      "masked depression functional anhedonia dopamine serotonin",
    "trauma":         "complex PTSD van der Kolk body memory somatic",
    "impostor":       "impostor phenomenon Clance 1978 competence high achievers",
    "codependencia":  "codependency emotional dependency Melody Beattie relationships",
    "resiliencia":    "post-traumatic growth resilience Tedeschi Calhoun psychological",
    "neurociencia":   "emotion regulation prefrontal amygdala Siegel UCLA Daniel",
    "limites":        "healthy boundaries Nedra Tawwab self-care relationships",
    "abandono":       "fear of abandonment anxious attachment relationship patterns",
}
```

---

### CATEGORIA 6 — VÍDEO & ANIMAÇÃO

```python
# Do diretório: "Video" (50 APIs)
VIDEO_APIS = {
    # RENDER & ANIMAÇÃO
    "Remotion":       "npx remotion render — React spring physics word-by-word",  # PADRÃO NOVO
    "FFmpeg_local":   "apt install ffmpeg — Ken Burns concat gate",               # PADRÃO ATUAL
    "Shotstack":      "https://api.shotstack.io/edit/stage/render",              # cloud render
    "ZSky_Video":     "https://zsky.ai/api/v1/video/generate",                  # 1080p + áudio
    "HF_CogVideoX":   "THUDM/CogVideoX-5b — Apache 2.0 open source",
    "RunwayML":       "https://api.runwayml.com/v1/",                           # Gen2 (pago)
    "Pika_Labs":      "https://api.pika.art/",                                  # (pago)
    "HeyGen":         "https://api.heygen.com/",                               # avatar falante

    # YOUTUBE
    "YouTube_Data_v3":"https://www.googleapis.com/youtube/v3",                  # upload, search
    "YouTube_Analytics":"https://youtubeanalytics.googleapis.com/v2",           # métricas canal
    "yt_dlp":         "pip install yt-dlp",                                     # download/análise
    "pytube":         "pip install pytube",                                     # metadata
    "YT_Transcript":  "pip install youtube-transcript-api",                     # legendas

    # PROCESSAMENTO
    "OpenCV_local":   "pip install opencv-python",                              # processamento frames
    "MoviePy_local":  "pip install moviepy",                                    # edição Python
    "Scenedetect":    "pip install scenedetect",                                # detectar cenas

    # THUMBNAIL
    "Thumbo":         "https://thumbo.io/api/",                                 # thumbnails
    "Placeholders":   "https://via.placeholder.com/{w}x{h}",                   # sem auth
    "Canva_API":      "https://api.canva.com/rest/v1/",                        # design prog
}
```

---

### CATEGORIA 7 — SOCIAL MEDIA & ANALYTICS

```python
# Do diretório: "Social" (44 APIs) + "News"
SOCIAL_ANALYTICS_APIS = {
    # YOUTUBE (principal canal)
    "YouTube_OAuth":  "https://accounts.google.com/o/oauth2/v2/auth",       # ⚠️ PENDENTE
    "YT_Upload_URL":  "https://www.googleapis.com/upload/youtube/v3/videos",

    # INSTAGRAM (futuro)
    "Instagram_Basic":"https://graph.instagram.com/me",                      # básico display
    "Instagram_Graph":"https://graph.facebook.com/v20.0/{id}/media",        # business

    # TIKTOK (futuro)
    "TikTok_Research":"https://open.tiktokapis.com/v2/research/",           # research API
    "TikTok_Creator": "https://open.tiktokapis.com/v2/post/publish/",       # publicar

    # MONITORAMENTO
    "Social_Searcher":"https://api.social-searcher.com/v2/posts?q={q}&network=instagram",
    "Mention_API":    "https://api.mention.com/api/",                       # monitorar marca
    "Brand24":        "https://api.brand24.com/v3/",                        # free trial

    # TENDÊNCIAS
    "GoogleTrends":   "pip install pytrends",                               # sem auth key
    "Twitter_v2":     "https://api.twitter.com/2/tweets/search/recent",    # free basic
    "Reddit_API":     "https://www.reddit.com/r/{sub}/top.json",            # sem auth básico

    # ANALYTICS GERAL
    "Plausible":      "https://plausible.io/api/v1/",                      # open source analytics
    "Matomo":         "https://matomo.org/docs/analytics-api/",             # self-hosted
    "Open_Web_Analytics": "https://github.com/padams/Open-Web-Analytics",  # open source
}
```

---

### CATEGORIA 8 — LLMs GRATUITOS (Machine Learning)

```python
# Do diretório: "Machine Learning" (30 APIs via publicapis.dev)
LLM_FREE_APIS = {
    # TIER FREE PERMANENTE (sem cartão)
    "groq": {
        "url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile","llama-4-maverick","deepseek-r1-distill-llama-70b"],
        "limit": "14.400 req/dia", "speed": "315 tokens/s",
        "key_url": "console.groq.com"
    },
    "nvidia_nim": {
        "url": "https://integrate.api.nvidia.com/v1",
        "models": ["deepseek-ai/deepseek-v4-pro","meta/llama-3.3-70b","qwen3-coder"],
        "limit": "40 req/min", "key_url": "build.nvidia.com"
    },
    "google_aistudio": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": ["gemini-2.5-flash","gemini-2.5-pro","gemma-3"],
        "limit": "1.500 req/dia", "key_url": "aistudio.google.com"
    },
    "cerebras": {
        "url": "https://api.cerebras.ai/v1",
        "models": ["Meta-Llama-3.1-405B","DeepSeek-R1-671B"],
        "limit": "1M tokens/dia", "key_url": "cloud.cerebras.ai"
    },
    "openrouter_free": {
        "url": "https://openrouter.ai/api/v1",
        "models": ["qwen/qwen3-235b:free","meta-llama/llama-3.3-70b:free","deepseek/deepseek-r1:free"],
        "limit": "50 req/dia sem compra", "key_url": "openrouter.ai"
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1",
        "models": ["mistral-small-latest","codestral-2501"],
        "limit": "1B tokens/mês", "key_url": "console.mistral.ai"
    },
    "cloudflare_workers_ai": {
        "url": "https://api.cloudflare.com/client/v4/accounts/{id}/ai/v1",
        "models": ["llama-3.3-70b","deepseek-r1","qwen3-coder"],
        "limit": "10K neurons/dia", "key_url": "dash.cloudflare.com"
    },
    "sambanova": {
        "url": "https://api.sambanova.ai/v1",
        "models": ["Meta-Llama-3.1-405B","DeepSeek-R1-671B","Qwen3-235B"],
        "limit": "$5 grátis 3 meses", "key_url": "cloud.sambanova.ai"
    },
    "github_models": {
        "url": "https://models.inference.ai.azure.com",
        "models": ["gpt-5","gpt-4.1","gpt-4o","o4-mini","Llama-3.3-70B"],
        "limit": "50 chat + 2K completions/mês", "key_url": "github.com/settings/tokens"
    },
    "huggingface": {
        "url": "https://api-inference.huggingface.co/v1",
        "models": ["meta-llama/Llama-3.3-70B-Instruct","Qwen/Qwen3-235B-A22B"],
        "limit": "1K req/hora com token grátis", "key_url": "huggingface.co/settings/tokens"
    },
    "pollinations_llm": {
        "url": "https://gen.pollinations.ai/v1",
        "models": ["openai-large","claude","gemini","deepseek","qwen3-coder"],
        "limit": "1 req/15s SEM KEY", "key_url": "Nenhuma"
    },
    "ollama_local": {
        "url": "http://localhost:11434/api",
        "models": ["llama3.3","qwen3","deepseek-r1","phi4","gemma3"],
        "limit": "Ilimitado local", "key_url": "Nenhuma — instalar ollama.ai"
    },
}

# LLMRouter V4 — fallback automático
LLM_ROUTER = [
    ("nvidia",  "deepseek-ai/deepseek-v4-pro"),    # 1. PRIMARY
    ("nvidia",  "meta/llama-3.3-70b-instruct"),    # 2. fallback NVIDIA
    ("groq",    "llama-3.3-70b-versatile"),         # 3. fallback Groq
    ("openai",  "gpt-4o-mini"),                     # 4. fallback OpenAI
]
```

---

### CATEGORIA 9 — UTILIDADES & INFRAESTRUTURA

```python
# Categories: Development, Documents & Productivity, URL Shorteners, Security
UTIL_APIS = {
    # TRADUÇÃO
    "MyMemory":       "https://api.mymemory.translated.net/get",          # ✅ 10K/dia
    "Lingva":         "https://lingva.ml/api/v1/{src}/{target}/{text}",   # ✅ sem auth
    "DeepL_Free":     "https://api-free.deepl.com/v2/translate",          # 500K chars/mês
    "LibreTranslate": "https://libretranslate.com/translate",             # open source

    # GRAMÁTICA & TEXTO
    "LanguageTool":   "https://api.languagetool.org/v2/check",            # ✅ PT-BR
    "Datamuse":       "https://api.datamuse.com/words",                   # ✅ sinônimos sem auth
    "Free_Dictionary":"https://api.dictionaryapi.dev/api/v2/entries",     # ✅ sem auth
    "PT_Dictionary":  "https://api.dicionario-aberto.net/word/{w}",      # ✅ PT sem auth

    # STORAGE & PROCESSAMENTO
    "Supabase":       "https://tpjvalzwkqwttvmszvie.supabase.co",         # ✅ storage + DB
    "Cloudinary_Free":"https://api.cloudinary.com/v1_1/",                 # 25GB grátis
    "Imgbb":          "https://api.imgbb.com/1/upload",                   # imagens (key grátis)
    "TinyPNG":        "https://api.tinify.com",                           # compressão 500/mês

    # DADOS BRASIL
    "IBGE":           "https://servicodados.ibge.gov.br/api/v3/",        # ✅ sem auth
    "BrasilAPI":      "https://brasilapi.com.br/api/",                   # ✅ CEP, banks, feriados
    "ReceitaWS":      "https://receitaws.com.br/v1/cnpj/{cnpj}",         # ✅ CNPJ sem auth
    "ViaCEP":         "https://viacep.com.br/ws/{cep}/json/",            # ✅ CEP sem auth

    # IP & GEOLOCALIZAÇÃO
    "ipapi":          "https://ipapi.co/json/",                          # ✅ location sem auth
    "FreeGeoIP":      "https://freegeoip.app/json/",                     # ✅ geo sem auth
    "IP_Geolocation": "https://ipgeolocation.io/ip-location/",           # free tier

    # URL & PERFORMANCE
    "TinyURL":        "https://tinyurl.com/api-create.php?url={url}",   # ✅ sem auth
    "Rebrandly":      "https://api.rebrandly.com/v1/links",              # free tier
    "PageSpeed":      "https://www.googleapis.com/pagespeedonline/v5/",  # key grátis

    # NOTIFICAÇÕES (para WhatsApp bot futuro)
    "Twilio":         "https://api.twilio.com/2010-04-01/",             # WhatsApp (pago, trial)
    "CallMeBot":      "https://api.callmebot.com/whatsapp.php",          # WhatsApp sem key
    "WhatsApp_Business":"https://graph.facebook.com/v20.0/{id}/messages",# Meta oficial
}
```

---

### CATEGORIA 10 — GOVERNO & DADOS ABERTOS

```python
# Do diretório: "Government" + "Open Data" (Brasil)
OPEN_DATA_BR = {
    "Portal_Dados_BR": "https://dados.gov.br/api/3/action/",              # dados.gov.br
    "IBGE_API":        "https://servicodados.ibge.gov.br/api/v3/",        # população, economia
    "BrasilAPI":       "https://brasilapi.com.br/api/",                   # feriados, bancos
    "ANS":             "https://dadosabertos.ans.gov.br/api/3/action/",   # saúde suplementar
    "CFM_CRM":         "https://portal.cfm.org.br/",                     # médicos e psicólogos
    "CFP_API":         "https://site.cfp.org.br/",                       # Conselho Fed Psicologia
    "DATASUS":         "https://datasus.saude.gov.br/",                  # saúde pública Brasil
}
```

---

## 🔍 COMO DESCOBRIR NOVAS APIS (AUTOMÁTICO)

```python
# 1. API do diretório público-apis (sem auth)
import requests

def search_public_apis(category=None, no_auth=True):
    """Busca APIs no repositório público-apis"""
    params = {}
    if category: params["category"] = category
    if no_auth: params["auth"] = "null"
    r = requests.get("https://api.publicapis.org/entries", params=params, timeout=15)
    return r.json().get("entries", [])

def get_api_categories():
    """Lista todas as categorias disponíveis"""
    r = requests.get("https://api.publicapis.org/categories", timeout=15)
    return r.json().get("count", 0), r.json().get("categories", [])

# 2. Buscar em publicapis.dev
def search_publicapis_dev(query):
    """Busca em publicapis.dev"""
    r = requests.get(f"https://publicapis.dev/api/search?query={query}", timeout=15)
    return r.json() if r.status_code == 200 else []

# 3. API do public-api-lists
def get_api_list():
    """Busca no public-api-lists (JSON direto)"""
    r = requests.get("https://public-api-lists.github.io/public-api-lists/apis.json", timeout=15)
    return r.json() if r.status_code == 200 else []

# Uso:
# search_public_apis(category="Health", no_auth=True)  # APIs de saúde sem auth
# search_public_apis(category="Personality")            # APIs de psicologia
# search_public_apis(category="Text Analysis")          # APIs NLP
```

---

## 📊 ESTADO DOS 400 VÍDEOS

```
Shorts V31 prontos:  9/200 (IDs 682-712)
Longs V31 scripts:   9/200 (IDs 713-721, #713 em render)
Remotion render:     1 workflow ativo (run 26238248258)
video_plan_400:      400 registros no Supabase
```

---

## 🔐 CREDENCIAIS

```
✅ GH_PAT, Supabase, Groq, NVIDIA, OpenAI, HF_TOKEN
⚠️ ELEVENLABS (quota) → Chatterbox padrão
❌ FALTA: YouTube OAuth (psidanielacoelho1982@gmail.com)
❌ FALTA: GEMINI_API_KEY (grátis: aistudio.google.com)
❌ FALTA: INSTAGRAM_TOKEN, TIKTOK_TOKEN
```

---

## 🎤 PIPELINE ÁUDIO V31

```python
TIPOS_AUDIO = {
    "GANCHO":    (0.88, 0.12, 0.0, 0.8),
    "IMPACTO":   (0.96, 0.09, 1.0, 1.6),   # Camera shake
    "REVELACAO": (0.93, 0.10, 0.7, 1.4),
    "CHORO":     (0.95, 0.08, 0.5, 1.8),
    "PAUSA":     (0.87, 0.13, 0.4, 1.1),
    "CTA":       (0.74, 0.26, 0.9, 0.0),
    "NORMAL":    (0.82, 0.17, 0.0, 0.65),
}
GATE_SEG = "agate=threshold=0.028:ratio=8000:attack=1:release=60"
GATE_FINAL= "highpass=f=80,agate=threshold=0.028:ratio=8000:attack=2:release=50"
```

---

## 🎬 REMOTION — Stack V31

```
remotion/src/
  index.tsx              # Root composition registry
  compositions/
    PsychShort.tsx       # Short 9:16 58s 1740 frames
  components/
    Background.tsx       # Gradiente + partículas ψ
    AnimatedText.tsx     # Word-by-word spring physics
    CharacterCard.tsx    # Float + halo pulsante
    LowerThird.tsx       # Slide-in com blur
    ProgressBar.tsx      # Barra + emojis CTA

Workflow: .github/workflows/render-remotion-short.yml
```

---

## 💰 ESTRATÉGIA R$50K/MÊS

```
RPM BR psicologia: R$10-16 | Meta: 3.5M views/mês
Mês 3-4: 10K subs → R$3K | Mês 9-10: 300K subs → R$50K
Shorts → subs | Longs → mid-rolls (3/6/9/12min)
Horário: 18-20h BR | Canal: UCyCkIpsVgME9yCj_oXJFheA
```

---

## 🔗 LINKS

```
Hub:           https://repovazio.vercel.app/hub.html
Vídeos:        https://repovazio.vercel.app/videos-prontos.html
Painel 400:    https://repovazio.vercel.app/painel-400.html
API Hub:       scripts/psicologia_apis.py
GitHub:        https://github.com/tafita81/Repovazio
```
