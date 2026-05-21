---
name: psicologia-doc-v27
description: Use esta SKILL sempre que o usuário mencionar: psicologia.doc, repovazio, Daniela Coelho, @psidanielacoelho, canal YouTube psicologia, viral, cérebro autônomo, tokens sociais, Instagram, TikTok, WhatsApp grupos, monetização, 1000 subs, crescimento, setup tokens, espelhamento viral.
version: 33.0 — OMNIBUS 40K APIs
date: 2026-05-21
---

# SKILL psicologia.doc V33 — OMNIBUS 40.000+ APIs (21/mai/2026)

---

## ⚠️ REGRA DE OURO
```
NUNCA liberar vídeo sem testar #683. RMS trough = -inf obrigatório.
Canal ATIVO: UCyCkIpsVgME9yCj_oXJFheA (@psidanielacoelho)
Canal ⛔ BLOQUEADO: UCSH63tBfY6wEIdkC4u4zKdg — NUNCA publicar
```

---

## INFRA CORE
```
Supabase: tpjvalzwkqwttvmszvie | Vercel: repovazio.vercel.app | GitHub: tafita81/Repovazio
scripts/psicologia_apis.py  — hub de APIs (51+ curadas)
remotion/src/               — animações React (Remotion V31)
docs/SKILL_V32.md           — versão anterior da skill
```

---

## 🌐 OS 7 DIRETÓRIOS + SISTEMA DE DESCOBERTA EM TEMPO REAL

```python
# ══════════════════════════════════════════════════════════════════
# DIRETÓRIOS DE APIs PÚBLICAS — ACESSO PROGRAMÁTICO
# ══════════════════════════════════════════════════════════════════

DIRECTORIES = {

    # ──────────────────────────────────────────────────────────────
    # 1. public-apis (GitHub) — O MAIS COMPLETO — 1400+ APIs, 51 cats
    # ──────────────────────────────────────────────────────────────
    "public_apis": {
        "url":    "https://github.com/public-apis/public-apis",
        "json":   "https://api.publicapis.org/entries",
        "cats":   "https://api.publicapis.org/categories",
        "random": "https://api.publicapis.org/random",
        "health": "https://api.publicapis.org/health",
        "uso":    "Principal referência — buscar por categoria e auth",
        "exemplo": "GET /entries?category=Health&auth=null → lista APIs de saúde sem auth",
        "total_apis": "1400+",
        "total_cats": 51,
    },

    # ──────────────────────────────────────────────────────────────
    # 2. publicapis.dev — MELHOR UI — 1400+ APIs
    # ──────────────────────────────────────────────────────────────
    "publicapis_dev": {
        "url":  "https://publicapis.dev",
        "busca": "https://publicapis.dev/api/search?query={termo}",
        "cats": "https://publicapis.dev/category/{cat}",
        "uso":  "Melhor UI + filtros avançados + uptime stats por API",
        "cats_psico": [
            "personality","text-analysis","machine-learning",
            "health","science","books","social","music","video"
        ]
    },

    # ──────────────────────────────────────────────────────────────
    # 3. public-apis.io — 1000+ APIs
    # ──────────────────────────────────────────────────────────────
    "public_apis_io": {
        "url":   "https://public-apis.io",
        "busca": "https://public-apis.io/category/{categoria}",
        "descr": "Movie, Anime, clima, música, jogos, câmbio, esportes, ciência, open data",
        "uso":   "Alternativa ao GitHub — boa para filmes e entretenimento"
    },

    # ──────────────────────────────────────────────────────────────
    # 4. publicapis.io — 1000+ com código de exemplo
    # ──────────────────────────────────────────────────────────────
    "publicapis_io": {
        "url":   "https://publicapis.io",
        "busca": "https://publicapis.io/category/{categoria}",
        "uso":   "Inclui exemplos de código prontos para Python/JS"
    },

    # ──────────────────────────────────────────────────────────────
    # 5. public-api-lists — 48 categorias + JSON API própria
    # ──────────────────────────────────────────────────────────────
    "public_api_lists": {
        "url":  "https://github.com/public-api-lists/public-api-lists",
        "json": "https://public-api-lists.github.io/public-api-lists/apis.json",
        "cats": 48,
        "uso":  "JSON direto — todas as APIs em um arquivo"
    },

    # ──────────────────────────────────────────────────────────────
    # 6. mixedanalytics — ~200 APIs SEM QUALQUER AUTH
    # ──────────────────────────────────────────────────────────────
    "mixedanalytics": {
        "url": "https://mixedanalytics.com/blog/list-actually-free-open-no-auth-needed-apis/",
        "uso": "PRIORIDADE para GitHub Actions — sem configurar secrets",
        "categories": [
            "Art & Illustrations", "Astronomy", "Books & Literature",
            "Business", "Climate & Environment", "Coding & Science",
            "Countries & Geography", "Crypto & Finance", "Entertainment",
            "Exercise & Nutrition", "Food & Drink", "Fun Facts",
            "Health", "Language & Etymology", "Music",
            "News & Media", "Open Government Data", "Random Data",
            "Sports", "Time & Calendar", "Transport & Travel", "Weather"
        ],
        # APIs confirmadas sem auth desta lista:
        "confirmadas": [
            "https://api.adviceslip.com/advice",
            "https://www.affirmations.dev/",
            "https://stoic-quotes.com/api/quote",
            "https://api.quotable.io/random",
            "https://uselessfacts.jsph.pl/random.json?language=en",
            "https://catfact.ninja/fact",
            "http://numbersapi.com/42/trivia",
            "https://zenquotes.io/api/random",
            "https://api.open-meteo.com/v1/forecast",
            "https://restcountries.com/v3.1/all",
            "https://date.nager.at/api/v3/publicholidays/2025/BR",
            "https://brasilapi.com.br/api/feriados/v1/2025",
            "https://api.coindesk.com/v1/bpi/currentprice.json",
            "https://api.exchangerate-api.com/v4/latest/USD",
            "https://tarotapi.dev/api/v1/cards/random",
            "https://history.muffinlabs.com/date",
            "https://poetrydb.org/random",
            "https://icanhazdadjoke.com/",
            "https://official-joke-api.appspot.com/random_joke",
            "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY",
            "https://dummyjson.com/quotes/random",
        ]
    },

    # ──────────────────────────────────────────────────────────────
    # 7. RapidAPI — 40.000+ APIs (maior marketplace)
    # ──────────────────────────────────────────────────────────────
    "rapidapi": {
        "url":       "https://rapidapi.com",
        "hub":       "https://rapidapi.com/hub",
        "busca":     "https://rapidapi.com/search/{termo}",
        "free_apis": "https://rapidapi.com/collection/list-of-free-apis",
        "total":     "40.000+",
        "uso":       "Quando não achar no gratuito puro — verificar free tier",
        "categorias_principais": [
            "AI/ML", "Data", "Finance", "Health", "Media", "Music",
            "News", "Science", "Social", "Sports", "Travel", "Video",
            "Translation", "NLP", "Image Recognition", "Analytics"
        ],
        "nota": "Free tier geralmente 100-1000 req/mês — suficiente para testes"
    },

    # ──────────────────────────────────────────────────────────────
    # 8. freepublicapis.com — CURADORIA SEMANAL (novo 2025)
    # ──────────────────────────────────────────────────────────────
    "freepublicapis": {
        "url":  "https://www.freepublicapis.com/",
        "cats": [
            "AI", "Animals", "Art", "Development", "Entertainment",
            "Environment", "Finance", "Food & Drink", "Gaming",
            "Geodata", "Health", "Language", "Music", "Nature",
            "Public Data", "Science", "Spiritual", "Sport",
            "Switzerland", "Transportation", "Travel", "Weather", "Work"
        ],
        "uso":  "Curadoria semanal — lista APIs novas e interessantes",
        "especial": "Categoria 'Spiritual' — tarot, astrologia, meditação (para conteúdo)"
    },
}

# ══════════════════════════════════════════════════════════════════
# FUNÇÕES DE DESCOBERTA (usar em qualquer script)
# ══════════════════════════════════════════════════════════════════

def find_api(category: str, no_auth: bool = True, limit: int = 20):
    """Busca APIs no diretório público-apis em tempo real"""
    import requests
    params = {"category": category, "https": "true"}
    if no_auth: params["auth"] = "null"
    r = requests.get("https://api.publicapis.org/entries", params=params, timeout=10)
    entries = r.json().get("entries", []) if r.status_code == 200 else []
    return entries[:limit]

def find_no_auth_api(keyword: str):
    """Busca API completamente sem auth pelo nome/descrição"""
    import requests
    all_entries = requests.get("https://api.publicapis.org/entries?auth=null", timeout=15).json().get("entries",[])
    return [e for e in all_entries if keyword.lower() in (e.get("Description","") + e.get("API","")).lower()]

def get_all_categories():
    """Retorna todas as 51 categorias disponíveis"""
    import requests
    r = requests.get("https://api.publicapis.org/categories", timeout=10)
    return r.json().get("categories",[]) if r.status_code == 200 else []

def get_random_api(auth: str = "null"):
    """Retorna uma API aleatória (ótimo para descoberta)"""
    import requests
    r = requests.get(f"https://api.publicapis.org/random?auth={auth}", timeout=10)
    return r.json().get("entries",[{}])[0] if r.status_code == 200 else {}

# Busca no public-api-lists (JSON direto):
def search_api_lists(keyword: str):
    """Busca em public-api-lists JSON direto"""
    import requests
    r = requests.get("https://public-api-lists.github.io/public-api-lists/apis.json", timeout=15)
    if r.status_code == 200:
        data = r.json()
        results = []
        for cat in data.get("categories", []):
            for api in cat.get("apis", []):
                if keyword.lower() in (api.get("name","") + api.get("description","")).lower():
                    results.append({**api, "category": cat.get("name","")})
        return results
    return []
```

---

## 📋 AS 51 CATEGORIAS — MAPEAMENTO COMPLETO COM APIs E USO

```python
# ══════════════════════════════════════════════════════════════════
# TAXONOMIA COMPLETA — public-apis GitHub (51 categorias)
# Para cada: relevância psicologia.doc + APIs conhecidas + endpoints
# ══════════════════════════════════════════════════════════════════

FULL_TAXONOMY = {

    # ────────────────────────────────────────────────────────────
    # ★★★ ALTA RELEVÂNCIA — usar no pipeline diariamente
    # ────────────────────────────────────────────────────────────

    "Personality": {
        "relevancia": "★★★ MÁXIMA — categoria central do projeto",
        "uso_psico":  "Análise de personalidade Big5, DISC, HEXACO nos scripts",
        "apis_sem_auth": [],
        "apis_key_free": [
            {"name":"Sentino Personality API","url":"https://api.sentino.org/v2/analyze","descr":"Big5+DISC+HEXACO+emoção via NLP","limit":"100/dia"},
        ],
        "apis_paid": [
            {"name":"IBM Personality Insights","url":"deprecated — use Watson NLU"},
            {"name":"Crystal Knows","url":"https://crystal.biz/api","descr":"DISC via LinkedIn"},
        ],
        "buscar_mais": "find_api('Personality') ou publicapis.dev/category/personality"
    },

    "Text Analysis": {
        "relevancia": "★★★ MÁXIMA — classificar scripts em IMPACTO/CHORO/REVELACAO etc",
        "uso_psico":  "Sentiment, emoção, keywords, gramática PT-BR",
        "apis_sem_auth": [
            {"name":"LanguageTool","url":"https://api.languagetool.org/v2/check","limit":"20/min","descr":"Gramática PT-BR"},
            {"name":"Datamuse","url":"https://api.datamuse.com/words","descr":"Sinônimos/rimas sem auth"},
            {"name":"Free Dictionary EN","url":"https://api.dictionaryapi.dev/api/v2/entries/en/{word}","descr":"Definições EN"},
            {"name":"PT Dictionary","url":"https://api.dicionario-aberto.net/word/{w}","descr":"Definições PT"},
        ],
        "apis_hf": [
            {"name":"HF Emotion PT","model":"pysentimiento/robertuito-emotion-analysis","lang":"PT-BR"},
            {"name":"HF Emotion EN","model":"j-hartmann/emotion-english-distilroberta-base","lang":"EN"},
            {"name":"HF Zero-Shot","model":"facebook/bart-large-mnli","descr":"Classificar qualquer label"},
            {"name":"HF Summarize","model":"facebook/bart-large-cnn","descr":"Resumo automático"},
            {"name":"HF NER","model":"dslim/bert-base-NER","descr":"Entidades nomeadas"},
            {"name":"HF Paraphrase","model":"sentence-transformers/paraphrase-multilingual-mpnet-base-v2"},
        ],
        "outros": [
            {"name":"Twinword Emotion","url":"https://www.twinword.com/api/emotion_analysis.php","auth":"key_free","limit":"300/mês"},
            {"name":"Google Cloud NLP","url":"https://language.googleapis.com/v1/documents:analyzeSentiment","auth":"key_free_quota"},
            {"name":"Perspective API","url":"https://commentanalyzer.googleapis.com/v1alpha1","descr":"Toxicidade"},
            {"name":"AYLIEN","url":"https://api.aylien.com/","descr":"NLP + News AI","tier":"free_trial"},
            {"name":"MeaningCloud","url":"https://api.meaningcloud.com/","descr":"Análise semântica PT","tier":"free"},
            {"name":"Cohere","url":"https://api.cohere.com/v1/classify","descr":"Classificação texto","tier":"free_generous"},
            {"name":"TextRazor","url":"https://api.textrazor.com/","descr":"Entity+concept extraction","tier":"free"},
            {"name":"Tisane","url":"https://api.tisane.ai/parse","descr":"Hate speech, abuse detection","tier":"key_free"},
            {"name":"NLPAPI","url":"https://nlpapi.io/","descr":"Sentiment+classification","tier":"free_trial"},
        ],
        "buscar_mais": "find_api('Text Analysis') ou publicapis.dev/category/text-analysis"
    },

    "Machine Learning": {
        "relevancia": "★★★ MÁXIMA — LLMs, imagem, voz, vídeo",
        "uso_psico":  "Gerar scripts, classificar, resumir, criar imagens",
        "apis_sem_auth": [
            {"name":"Pollinations LLM","url":"https://gen.pollinations.ai/v1","descr":"Claude/GPT/Gemini sem key"},
            {"name":"Ollama API","url":"http://localhost:11434/api","descr":"Local — sem internet"},
        ],
        "llms_free_key": [
            "NVIDIA NIM: integrate.api.nvidia.com/v1 — deepseek-v4-pro",
            "Groq: api.groq.com/openai/v1 — 14400 req/dia",
            "Google AI Studio: generativelanguage.googleapis.com — Gemini 2.5",
            "Cerebras: api.cerebras.ai/v1 — 1M tokens/dia",
            "OpenRouter free: openrouter.ai/api/v1 — qwen3-235b:free",
            "Mistral: api.mistral.ai/v1 — 1B tokens/mês",
            "GitHub Models: models.inference.ai.azure.com — gpt-5",
            "SambaNova: api.sambanova.ai/v1 — DeepSeek-R1-671B",
            "HuggingFace: api-inference.huggingface.co — 1K/hora",
            "Cloudflare Workers AI: api.cloudflare.com — 10K neurons/dia",
            "Cohere: api.cohere.com — command-r-plus grátis",
            "Together AI: api.together.xyz — $5 crédito inicial",
            "Fireworks AI: api.fireworks.ai — free tier",
            "Perplexity: api.perplexity.ai — Sonar grátis limitado",
            "AI21 Labs: api.ai21.com — Jamba grátis",
        ],
        "imagem_gen": [
            "Pollinations FLUX: image.pollinations.ai — sem auth ilimitado",
            "HF FLUX Schnell: api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
            "HF SDXL: api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            "HF Animagine: api-inference.huggingface.co/models/Linaqruf/animagine-xl-3.1",
            "Stability AI: api.stability.ai — 25 créditos/dia grátis",
            "Ideogram: api.ideogram.ai — free tier",
            "Puter.js: puter.ai.txt2img() — DALL-E sem key no browser",
        ],
        "visao_comp": [
            "Google Vision: vision.googleapis.com — 1K/mês grátis",
            "HF CLIP: api-inference.huggingface.co/models/openai/clip-vit-base-patch32",
            "Roboflow: api.roboflow.com — detecção objetos free",
        ],
        "buscar_mais": "find_api('Machine Learning') ou publicapis.dev/category/machine-learning"
    },

    "Health": {
        "relevancia": "★★★ MÁXIMA — dados saúde mental, medicamentos, CID-10",
        "uso_psico":  "Dados epidemiológicos saúde mental, terminologia psicológica",
        "apis_sem_auth": [
            {"name":"Open Disease","url":"https://disease.sh/v3/covid-19/all","descr":"Dados doenças COVID"},
            {"name":"USDA FoodData","url":"https://api.nal.usda.gov/fdc/v1/","descr":"Nutrição (saúde geral)"},
            {"name":"MedlinePlus Connect","url":"https://connect.medlineplus.gov/application","descr":"Info médica EUA"},
        ],
        "apis_key_free": [
            {"name":"Open FDA","url":"https://api.fda.gov/drug/event.json","descr":"Eventos adversos medicamentos"},
            {"name":"Infermedica","url":"https://api.infermedica.com","descr":"IA diagnóstico sintomas"},
            {"name":"WHO GHO","url":"https://ghoapi.azureedge.net/api/","descr":"OMS dados globais saúde"},
            {"name":"BetterDoctor","url":"https://api.betterdoctor.com","descr":"Médicos e especialistas EUA"},
            {"name":"Covacine","url":"https://github.com/owid/covid-19-data","descr":"Dados vacinação mundial"},
            {"name":"RxNorm","url":"https://rxnav.nlm.nih.gov/REST/rxcui","descr":"Medicamentos+interações"},
            {"name":"DrugBank","url":"https://go.drugbank.com/releases/latest#open-data","descr":"Base farmacológica"},
            {"name":"Mental Health News","url":"https://gnews.io/api/v4/search?q=mental+health","descr":"Notícias saúde mental"},
        ],
        "brasil": [
            "DataSUS: datasus.saude.gov.br — dados SUS",
            "IBGE: servicodados.ibge.gov.br/api/v3/ — populacionais",
            "ANS: dadosabertos.ans.gov.br — saúde suplementar",
            "CFP: site.cfp.org.br — Conselho Federal de Psicologia",
        ],
        "buscar_mais": "find_api('Health') ou publicapis.dev/category/health"
    },

    "Science & Math": {
        "relevancia": "★★★ ALTA — pesquisa científica para embasar scripts",
        "uso_psico":  "Artigos psicologia, neurociência, pesquisa acadêmica",
        "apis_sem_auth": [
            {"name":"PubMed E-utilities","url":"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi","descr":"NCBI artigos psicologia"},
            {"name":"CrossRef","url":"https://api.crossref.org/works","descr":"DOIs e citações"},
            {"name":"OpenAlex","url":"https://api.openalex.org/works","descr":"250M artigos abertos"},
            {"name":"Europe PMC","url":"https://www.ebi.ac.uk/europepmc/webservices/rest/search","descr":"Literatura médica EU"},
            {"name":"arXiv","url":"http://export.arxiv.org/api/query","descr":"Preprints psicologia/neuro"},
            {"name":"Semantic Scholar","url":"https://api.semanticscholar.org/graph/v1/paper/search","descr":"IA busca acadêmica"},
            {"name":"CORE API","url":"https://api.core.ac.uk/v3/","descr":"Open access papers"},
            {"name":"Unpaywall","url":"https://api.unpaywall.org/v2/{doi}","descr":"PDFs gratuitos por DOI"},
            {"name":"NASA","url":"https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY","descr":"NASA APOD (inspiração visual)"},
            {"name":"Numbers API","url":"http://numbersapi.com/{n}/trivia","descr":"Trivia numérica para scripts"},
            {"name":"Open Notify (ISS)","url":"http://api.open-notify.org/iss-now.json","descr":"Posição ISS (analogias)"},
            {"name":"Wikipedia REST","url":"https://en.wikipedia.org/api/rest_v1/page/summary/{title}","descr":"Resumos Wikipedia"},
        ],
        "buscar_mais": "find_api('Science & Math') ou publicapis.dev/category/science"
    },

    "Music": {
        "relevancia": "★★★ ALTA — trilha sonora para Longs + inspiração",
        "uso_psico":  "Música de fundo CC para vídeos 15min + tags de humor",
        "apis_sem_auth": [
            {"name":"Beets API","url":"https://beets.io/","descr":"Gerenciar biblioteca musical local"},
            {"name":"Radio Browser","url":"https://de1.api.radio-browser.info/json/stations","descr":"Rádios online sem auth"},
            {"name":"iTunes Search","url":"https://itunes.apple.com/search?media=music&term={q}","descr":"Busca músicas Apple"},
        ],
        "apis_cc_musica": [
            {"name":"Jamendo","url":"https://api.jamendo.com/v3.0/tracks/","descr":"CC música para vídeos","auth":"key_free"},
            {"name":"Free Music Archive","url":"https://freemusicarchive.org/api/","descr":"FMA — CC music","auth":"key_free"},
            {"name":"ccMixter","url":"https://ccmixter.org/api/","descr":"CC remixable music","auth":"none"},
            {"name":"Incompetech","url":"https://incompetech.filmmusic.io/","descr":"Kevin MacLeod CC music","auth":"none"},
            {"name":"Freesound","url":"https://freesound.org/apiv2/search/text/","descr":"CC sounds+music","auth":"key_free","limit":"60/dia"},
            {"name":"YouTube Audio Library","url":"https://studio.youtube.com/channel/UC/music","descr":"CC música YouTube"},
            {"name":"Pixabay Music","url":"https://pixabay.com/api/?type=music","descr":"Royalty-free music","auth":"key_free"},
            {"name":"SoundHelix","url":"https://www.soundhelix.com/audio-examples/","descr":"Procedural ambient music","auth":"none"},
        ],
        "apis_dados_musica": [
            {"name":"MusicBrainz","url":"https://musicbrainz.org/ws/2/","descr":"Base de dados músicas","auth":"none"},
            {"name":"Last.fm","url":"https://ws.audioscrobbler.com/2.0/","descr":"Tendências musicais","auth":"key_free"},
            {"name":"Spotify API","url":"https://api.spotify.com/v1/","descr":"Busca músicas + audio features","auth":"OAuth"},
            {"name":"Discogs","url":"https://api.discogs.com/","descr":"Discografia completa","auth":"key_free"},
            {"name":"AudD","url":"https://api.audd.io/","descr":"Reconhecimento de música","auth":"key_free"},
            {"name":"Genius","url":"https://api.genius.com/","descr":"Letras e anotações","auth":"key_free"},
            {"name":"Deezer","url":"https://api.deezer.com/chart","descr":"Charts BR + preview 30s","auth":"none"},
            {"name":"SoundCloud","url":"https://api.soundcloud.com/tracks","descr":"Upload/stream","auth":"OAuth"},
        ],
        "geracao_musica_ia": [
            "Suno AI: suno.com — geração de música por prompt (beta API)",
            "Udio: udio.com — geração por prompt",
            "MusicGen: api-inference.huggingface.co/models/facebook/musicgen-small (HF)",
            "AudioCraft: github.com/facebookresearch/audiocraft (local)",
            "Riffusion: riffusion.com — música estável por imagem",
            "Mubert: api.mubert.com — música generativa (key grátis)",
        ],
        "buscar_mais": "find_api('Music') ou publicapis.dev/category/music"
    },

    # ────────────────────────────────────────────────────────────
    # ★★ MÉDIA RELEVÂNCIA — usar conforme necessidade
    # ────────────────────────────────────────────────────────────

    "Books": {
        "relevancia": "★★ ALTA — referências bibliográficas para scripts",
        "apis_sem_auth": [
            {"name":"Open Library","url":"https://openlibrary.org/api/books","descr":"6M livros"},
            {"name":"PoetryDB","url":"https://poetrydb.org/random","descr":"Poesia aleatória — inspiração"},
            {"name":"Gutenberg","url":"https://gutendex.com/books/","descr":"Livros domínio público"},
            {"name":"Bible API","url":"https://bible-api.com/john+3:16","descr":"Versículos bíblicos"},
            {"name":"Quran API","url":"https://api.alquran.cloud/v1/ayah/random","descr":"Versículos Al-Quran"},
        ],
        "apis_key_free": [
            {"name":"Google Books","url":"https://www.googleapis.com/books/v1/volumes?q={q}","descr":"5M livros"},
            {"name":"WorldCat","url":"https://www.worldcat.org/webservices/catalog/","descr":"Maior biblioteca mundial"},
        ],
        "buscar_mais": "find_api('Books') ou publicapis.dev/category/books"
    },

    "Social": {
        "relevancia": "★★ ALTA — analytics e publicação",
        "apis": {
            "YouTube":    "googleapis.com/youtube/v3 — 10K units/dia",
            "Instagram":  "graph.instagram.com — auth OAuth",
            "TikTok":     "open.tiktokapis.com — research + creator API",
            "Twitter/X":  "api.twitter.com/2/ — free basic",
            "Reddit":     "reddit.com/r/{sub}/top.json — sem auth básico",
            "LinkedIn":   "api.linkedin.com — OAuth",
            "Pinterest":  "api.pinterest.com — OAuth",
            "Mastodon":   "mastodon.social/api/v1/ — sem auth",
            "Tumblr":     "api.tumblr.com — key grátis",
            "Discord":    "discord.com/api/v10/ — bot token",
            "Telegram":   "api.telegram.org/bot{token}/ — bot API grátis",
            "WhatsApp":   "graph.facebook.com/v20.0/{id}/messages — Business API",
        },
        "monitoramento": [
            "Social Searcher: api.social-searcher.com — 100/dia sem key",
            "Brand24: api.brand24.com — free trial",
            "Mention: api.mention.com — free trial",
            "Keyhole: keyhole.co — social analytics",
        ],
        "buscar_mais": "find_api('Social') ou publicapis.dev/category/social"
    },

    "Video": {
        "relevancia": "★★ ALTA — upload, analytics, geração",
        "apis": {
            "YouTube Data v3": "googleapis.com/youtube/v3 — upload+analytics",
            "YouTube Analytics": "youtubeanalytics.googleapis.com/v2",
            "yt-dlp": "pip install yt-dlp — download local",
            "YT Transcript": "pip install youtube-transcript-api",
            "Vimeo": "api.vimeo.com — hosting alternativo",
            "Dailymotion": "api.dailymotion.com — distribuição BR",
            "Twitch": "api.twitch.tv/helix/ — lives",
            "Wistia": "api.wistia.com — analytics video",
            "Video Intelligence (Google)": "videointelligence.googleapis.com",
        },
        "geracao_ia": [
            "Remotion: npx remotion render — React animações (PADRÃO)",
            "FFmpeg: local — Ken Burns atual",
            "HF CogVideoX: THUDM/CogVideoX-5b — open source video AI",
            "Runway Gen-3: api.runwayml.com — pago",
            "Pika Labs: api.pika.art — pago",
            "Stable Video Diffusion: stabilityai/stable-video-diffusion — HF",
        ],
        "buscar_mais": "find_api('Video') ou publicapis.dev/category/video"
    },

    "News": {
        "relevancia": "★★ ALTA — tendências saúde mental, viral topics",
        "apis_sem_auth": [
            {"name":"HackerNews","url":"https://hacker-news.firebaseio.com/v0/topstories.json","descr":"Tech news"},
            {"name":"Guardian API","url":"https://content.guardianapis.com/search","auth":"key_free","descr":"Psicologia/saúde mental"},
            {"name":"GNews","url":"https://gnews.io/api/v4/search?q=saude+mental","descr":"Free 10 artigos/dia"},
            {"name":"MediaStack","url":"https://api.mediastack.com/v1/news","auth":"key_free","descr":"1000/mês grátis"},
        ],
        "pagos_com_free": [
            "NewsAPI: newsapi.org — 100 req/dia dev plan",
            "The News API: thenewsapi.com — 100/dia",
            "AYLIEN News: aylien.com/news-api — free trial",
            "Contextual Web: rapidapi.com/contextualwebsearch — free tier",
        ],
        "buscar_mais": "find_api('News') ou publicapis.dev/category/news"
    },

    "Open Data": {
        "relevancia": "★★ ALTA — dados abertos governo Brasil",
        "apis_sem_auth": [
            {"name":"World Bank","url":"https://api.worldbank.org/v2/","descr":"Dados econômicos globais"},
            {"name":"IBGE","url":"https://servicodados.ibge.gov.br/api/v3/","descr":"Brasil: população, economia"},
            {"name":"BrasilAPI","url":"https://brasilapi.com.br/api/","descr":"CEP, bancos, feriados BR"},
            {"name":"Portal Dados Gov","url":"https://dados.gov.br/api/3/action/","descr":"Dados abertos Brasil"},
            {"name":"Our World in Data","url":"https://ourworldindata.org/data","descr":"Dados globais visualmente"},
            {"name":"UN Data","url":"http://data.un.org/Host.aspx?Content=API","descr":"Dados ONU"},
            {"name":"Eurostat","url":"https://ec.europa.eu/eurostat/api/dissemination/","descr":"Dados EU"},
            {"name":"US Data.gov","url":"https://catalog.data.gov/api/3/","descr":"Dados abertos EUA"},
        ],
        "buscar_mais": "find_api('Open Data') ou publicapis.dev/category/open-data"
    },

    # ────────────────────────────────────────────────────────────
    # ★ BAIXA/MÉDIA RELEVÂNCIA — disponível mas uso específico
    # ────────────────────────────────────────────────────────────

    "Anime": {
        "relevancia": "★ BAIXA — mas estilo kawaii é central nos personagens",
        "apis_sem_auth": [
            {"name":"Jikan","url":"https://api.jikan.moe/v4/","descr":"MyAnimeList API — personagens anime"},
            {"name":"Waifu.pics","url":"https://api.waifu.pics/sfw/waifu","descr":"Imagens waifu aleatórias"},
            {"name":"Nekos.life","url":"https://nekos.life/api/v2/img/neko","descr":"Anime images"},
            {"name":"Danbooru","url":"https://danbooru.donmai.us/posts.json","descr":"Banco de arte anime"},
            {"name":"AniList","url":"https://graphql.anilist.co","descr":"GraphQL — anime data"},
        ],
        "uso_psico": "Referência visual para estilo dos personagens kawaii chibi"
    },

    "Art & Design": {
        "relevancia": "★ MÉDIA — para thumbnails e identidade visual",
        "apis_sem_auth": [
            {"name":"Metropolitan Museum","url":"https://collectionapi.metmuseum.org/public/collection/v1/objects","descr":"500K obras arte domínio público"},
            {"name":"Harvard Art","url":"https://api.harvardartmuseums.org/object","descr":"Obras Harvard"},
            {"name":"The Colour API","url":"https://www.thecolorapi.com/id?hex=06060F","descr":"Paleta de cores psico"},
            {"name":"Colormind","url":"http://colormind.io/api/","descr":"Gerar paletas harmônicas"},
            {"name":"Open Doodles","url":"https://opendoodles.com/","descr":"SVG personagens grátis"},
            {"name":"DiceBear","url":"https://api.dicebear.com/9.x/{style}/svg","descr":"Avatares SVG por seed"},
            {"name":"Lorem Picsum","url":"https://picsum.photos/","descr":"Placeholder imgs"},
        ],
        "uso_psico": "DiceBear para avatares consistentes dos personagens psicologia.doc"
    },

    "Geocoding": {
        "relevancia": "★ BAIXA para conteúdo, mas útil para analytics de audiência",
        "apis_sem_auth": [
            {"name":"Nominatim","url":"https://nominatim.org/","descr":"OpenStreetMap geocoding"},
            {"name":"ipapi","url":"https://ipapi.co/json/","descr":"Geo por IP sem auth"},
            {"name":"GeoJS","url":"https://get.geojs.io/v1/ip/geo.json","descr":"Geo grátis"},
        ],
        "uso_psico": "Detectar localização dos viewers para adaptar conteúdo BR"
    },

    "Weather": {
        "relevancia": "★ BAIXA para conteúdo, mas útil para hooks sazonais",
        "apis_sem_auth": [
            {"name":"Open-Meteo","url":"https://api.open-meteo.com/v1/forecast?latitude=-23.5&longitude=-46.6","descr":"Clima São Paulo sem auth"},
            {"name":"wttr.in","url":"https://wttr.in/SaoPaulo?format=j1","descr":"Clima formatado sem auth"},
            {"name":"MetaWeather","url":"https://www.metaweather.com/api/","descr":"Histórico clima"},
        ],
        "uso_psico": "Hooks sazonais: 'O inverno piora a depressão?' (dados reais)"
    },

    "Calendar": {
        "relevancia": "★ BAIXA — mas útil para schedule de publicações",
        "apis_sem_auth": [
            {"name":"Nager.Date","url":"https://date.nager.at/api/v3/publicholidays/2025/BR","descr":"Feriados BR sem auth"},
            {"name":"BrasilAPI Feriados","url":"https://brasilapi.com.br/api/feriados/v1/2025","descr":"Feriados nacionais"},
            {"name":"Abstract Holidays","url":"https://holidays.abstractapi.com/v1/","descr":"Feriados globais","auth":"key_free"},
        ],
        "uso_psico": "Ajustar publicações para datas especiais (Dia da Saúde Mental, etc)"
    },

    "Cryptocurrency": {
        "relevancia": "★ MUITO BAIXA — não relevante diretamente",
        "nota": "Útil apenas se projeto aceitar doações em cripto no futuro"
    },

    "Currency Exchange": {
        "relevancia": "★ BAIXA — útil para calcular RPM em BRL",
        "apis_sem_auth": [
            {"name":"ExchangeRate-API","url":"https://api.exchangerate-api.com/v4/latest/USD","descr":"USD→BRL sem auth"},
            {"name":"Frankfurter","url":"https://api.frankfurter.app/latest?to=BRL","descr":"EUR→BRL sem auth"},
            {"name":"CoinDesk","url":"https://api.coindesk.com/v1/bpi/currentprice.json","descr":"BTC price"},
        ],
        "uso_psico": "Calcular RPM: views × RPM_USD × taxa_cambio = receita_BRL"
    },

    "Development": {
        "relevancia": "★★ MÉDIA — ferramentas de desenvolvimento do pipeline",
        "apis_sem_auth": [
            {"name":"GitHub API","url":"https://api.github.com/repos/tafita81/Repovazio","descr":"Status do repo/actions"},
            {"name":"JSONPlaceholder","url":"https://jsonplaceholder.typicode.com/","descr":"API fake para testes"},
            {"name":"HTTPBin","url":"https://httpbin.org/","descr":"Testar requests HTTP"},
            {"name":"IP-API","url":"http://ip-api.com/json/","descr":"Info de IP sem HTTPS (HTTP só)"},
        ],
        "buscar_mais": "find_api('Development')"
    },

    "URL Shorteners": {
        "relevancia": "★ BAIXA — links das descrições YouTube",
        "apis_sem_auth": [
            {"name":"TinyURL","url":"https://tinyurl.com/api-create.php?url={url}","descr":"Encurtar sem auth"},
            {"name":"is.gd","url":"https://is.gd/create.php?format=json&url={url}","descr":"Encurtar sem auth"},
        ]
    },

    "Government": {
        "relevancia": "★★ ALTA — dados Brasil para contexto",
        "brasil": [
            "Portal Dados: dados.gov.br",
            "ANS: dadosabertos.ans.gov.br",
            "DataSUS: datasus.saude.gov.br",
            "IBGE: servicodados.ibge.gov.br",
            "CFP: site.cfp.org.br — regulação psicologia",
            "CFM: portal.cfm.org.br — regulação médica",
        ],
        "buscar_mais": "find_api('Government')"
    },

    "Food & Drink": {
        "relevancia": "★ BAIXA — mas analogias com alimentação e psicologia",
        "apis_sem_auth": [
            {"name":"Open Food Facts","url":"https://world.openfoodfacts.org/api/v0/product/{barcode}.json","descr":"Nutrição"},
            {"name":"TheMealDB","url":"https://www.themealdb.com/api/json/v1/1/random.php","descr":"Receitas aleatórias"},
            {"name":"Cocktail DB","url":"https://www.thecocktaildb.com/api/json/v1/1/random.php","descr":"Drinks"},
        ],
        "uso_psico": "Séries sobre alimentação emocional, compulsão alimentar"
    },

    "Sports & Fitness": {
        "relevancia": "★ BAIXA — mas série sobre exercício e saúde mental",
        "apis_sem_auth": [
            {"name":"ExerciseDB","url":"https://exercisedb.io/api/exercises","descr":"Banco de exercícios"},
            {"name":"Calorie Ninjas","url":"https://calorieninjas.com/api/","auth":"key_free","descr":"Calorias por alimento"},
        ],
        "uso_psico": "Série: 'Como o exercício cura a ansiedade' — dados científicos"
    },

    "Photography": {
        "relevancia": "★ MÉDIA — fotos reais para thumbnails e backgrounds",
        "apis_sem_auth": [
            {"name":"Unsplash Source","url":"https://source.unsplash.com/{w}x{h}/?{keyword}","descr":"Fotos reais sem auth"},
            {"name":"Lorem Picsum","url":"https://picsum.photos/{w}/{h}","descr":"Placeholder fotos"},
            {"name":"Pexels","url":"https://api.pexels.com/v1/search?query={q}","auth":"key_free","descr":"Fotos royalty-free"},
        ]
    },

    "Anime → Art Design mapping": {
        "nota": "Para kawaii chibi usar Pollinations + DiceBear como primário"
    },

    # Categorias com menor relevância — listadas por completude
    "Anti-Malware": {"relevancia":"★ NÃO RELEVANTE"},
    "Authentication": {"relevancia":"★ RELEVANTE para OAuth YouTube/Instagram"},
    "Blockchain": {"relevancia":"★ NÃO RELEVANTE"},
    "Business": {"relevancia":"★ BAIXA — CNPJ via BrasilAPI"},
    "Cloud Storage": {"relevancia":"★★ Supabase Storage é o principal"},
    "Continuous Integration": {"relevancia":"★★★ GitHub Actions — core do pipeline"},
    "Data Validation": {"relevancia":"★ BAIXA"},
    "Dictionaries": {"relevancia":"★★ Free Dictionary PT/EN já usados"},
    "Documents & Productivity": {"relevancia":"★ BAIXA"},
    "Email": {"relevancia":"★ BAIXA — sem email marketing por ora"},
    "Environment": {"relevancia":"★ BAIXA"},
    "Events": {"relevancia":"★ BAIXA"},
    "Finance": {"relevancia":"★ BAIXA — câmbio USD/BRL útil"},
    "Games & Comics": {"relevancia":"★ BAIXA"},
    "Jobs": {"relevancia":"★ NÃO RELEVANTE"},
    "Patent": {"relevancia":"★ NÃO RELEVANTE"},
    "Phone": {"relevancia":"★ BAIXA"},
    "Security": {"relevancia":"★ BAIXA"},
    "Shopping": {"relevancia":"★ NÃO RELEVANTE"},
    "Test Data": {"relevancia":"★ BAIXA — para testes de desenvolvimento"},
    "Tracking": {"relevancia":"★ BAIXA"},
    "Transportation": {"relevancia":"★ NÃO RELEVANTE"},
    "Vehicle": {"relevancia":"★ NÃO RELEVANTE"},
}
```

---

## 🔥 RAPIDAPI — 40.000+ APIs (As mais relevantes por categoria)

```python
# RapidAPI Free Tiers — as mais úteis para psicologia.doc
# Acessar: rapidapi.com → criar conta grátis → subscribe free tier

RAPIDAPI_FREE = {
    "NLP & Texto": [
        "Text Analysis API (Twinword) — emoção 6 categorias — 300/mês",
        "Language Detection API — detectar idioma — 1K/mês",
        "Paraphrase & Rephrase API — reescrever scripts — 100/mês",
        "Grammar Check API — verificar PT-BR — var",
        "Keyword Extraction API — keywords de scripts — 500/mês",
        "Text Summarization API — resumir artigos — 100/mês",
        "Fake News Detection — verificar fontes — 100/mês",
        "Toxicity Detection — verificar conteúdo — 1K/mês",
        "Wordnik Words API — vocab em inglês — 15K/dia",
        "Words to Definitions API — definições — 1K/mês",
    ],
    "Psicologia & Personalidade": [
        "Sentino Personality API — Big5+HEXACO+DISC — 100/dia",
        "Personality Profiler — MBTI estimado — 500/mês",
        "Emotion Recognition Text — 8 emoções — 100/dia",
        "Psychological Test API — testes validados — var",
    ],
    "Imagem & Vídeo": [
        "Remove Background API — rembg cloud — 50/mês free",
        "Image Enhancement API — upscale — 100/mês",
        "Face Detection API — detectar expressões — 500/mês",
        "Deepface — reconhecimento facial — 100/mês",
        "AI Image Generator (DALL-E 3) — 100 imagens/mês free",
        "Text to Image (Stability AI) — 25 créditos/dia",
    ],
    "Áudio & TTS": [
        "VoiceRSS TTS API — PT-BR gratuito — 350 req/dia",
        "IBM Watson TTS — PT-BR — free tier",
        "Speechify API — narração — free trial",
        "AssemblyAI — transcrição — $50 crédito grátis",
        "Deepgram — STT+análise — $200 crédito",
        "ACRCloud — reconhecimento musical — free tier",
    ],
    "Tradução": [
        "DeepL API Free — 500K chars/mês",
        "Microsoft Translator — 2M chars/mês Azure free",
        "LibreTranslate API — open source host público",
        "MyMemory Translation — 10K palavras/dia",
        "Yandex Translate — 1M chars/mês",
        "Argos Translate — local Python",
    ],
    "Pesquisa & Notícias": [
        "Google Custom Search API — 100 busca/dia",
        "Bing Search API — 3/seg Azure free",
        "News API — 100 req/dia dev",
        "NewsData.io — 200 req/dia free",
        "GDELT Project — eventos mundiais sem auth",
        "Reddit API — posts/trends",
        "Wikipedia API — sem auth",
    ],
    "Analytics & SEO": [
        "YouTube Analytics API — próprio canal grátis",
        "Google Search Console — próprio site grátis",
        "SerpAPI — 100/mês free",
        "Moz API — 25K rows/mês limited",
        "Ahrefs API — pago",
        "SpyFu API — competitor keywords",
    ],
    "Social Media": [
        "Instagram Basic Display — auth OAuth",
        "TikTok Research API — trends",
        "Twitter API v2 — 500K tweets/mês free",
        "Reddit API — r/psychology r/mentalhealth",
        "Pinterest API — visual content",
        "LinkedIn API — professional content",
    ],
    "Dados & BI": [
        "Datausa.io — dados EUA sem auth",
        "World Bank API — dados globais sem auth",
        "UN Comtrade — comércio mundial",
        "FRED API — Federal Reserve Economics",
        "Quandl — dados financeiros",
    ],
}
```

---

## 🚀 SISTEMA DE DESCOBERTA INTELIGENTE (usar no pipeline)

```python
# ══════════════════════════════════════════════════════════════════
# MOTOR DE BUSCA DE APIs — chama múltiplos diretórios
# ══════════════════════════════════════════════════════════════════

import requests, json

class APIdiscovery:
    """Descobre APIs em tempo real de todos os 7 diretórios"""

    @staticmethod
    def find(category: str, no_auth: bool = True) -> list:
        """Busca em public-apis JSON endpoint"""
        params = {"category": category, "https": "true"}
        if no_auth: params["auth"] = "null"
        try:
            r = requests.get("https://api.publicapis.org/entries", params=params, timeout=10)
            return r.json().get("entries", []) if r.status_code == 200 else []
        except: return []

    @staticmethod
    def random(no_auth: bool = True) -> dict:
        """API aleatória (para descoberta criativa)"""
        try:
            auth = "null" if no_auth else ""
            r = requests.get(f"https://api.publicapis.org/random?auth={auth}", timeout=10)
            return r.json().get("entries", [{}])[0] if r.status_code == 200 else {}
        except: return {}

    @staticmethod
    def all_no_auth() -> list:
        """Todas as APIs sem qualquer auth (~300)"""
        try:
            r = requests.get("https://api.publicapis.org/entries?auth=null&https=true", timeout=15)
            return r.json().get("entries", []) if r.status_code == 200 else []
        except: return []

    @staticmethod
    def categories() -> list:
        """Lista todas as 51 categorias"""
        try:
            r = requests.get("https://api.publicapis.org/categories", timeout=10)
            return r.json().get("categories", []) if r.status_code == 200 else []
        except: return []

    @staticmethod
    def from_json_list(keyword: str) -> list:
        """Busca em public-api-lists JSON (48 categorias)"""
        try:
            r = requests.get(
                "https://public-api-lists.github.io/public-api-lists/apis.json",
                timeout=15
            )
            if r.status_code != 200: return []
            results = []
            for cat in r.json().get("categories", []):
                for api in cat.get("apis", []):
                    if keyword.lower() in json.dumps(api).lower():
                        results.append({**api, "category": cat.get("name","")})
            return results[:20]
        except: return []

    @staticmethod
    def no_auth_confirmed() -> list:
        """Lista curada de APIs 100% confirmadas sem auth"""
        return [
            # Quotes
            {"name":"AdviceSlip","url":"https://api.adviceslip.com/advice","cat":"Quotes"},
            {"name":"Affirmations","url":"https://www.affirmations.dev/","cat":"Quotes"},
            {"name":"StoicQuotes","url":"https://stoic-quotes.com/api/quote","cat":"Quotes"},
            {"name":"ZenQuotes","url":"https://zenquotes.io/api/random","cat":"Quotes"},
            {"name":"Quotable","url":"https://api.quotable.io/random","cat":"Quotes"},
            {"name":"Forismatic","url":"http://api.forismatic.com/api/1.0/?method=getQuote&format=json","cat":"Quotes"},
            {"name":"UselessFacts","url":"https://uselessfacts.jsph.pl/random.json?language=en","cat":"Facts"},
            {"name":"CatFact","url":"https://catfact.ninja/fact","cat":"Animals"},
            {"name":"NumbersFact","url":"http://numbersapi.com/{n}/trivia","cat":"Science"},
            {"name":"OnThisDay","url":"https://history.muffinlabs.com/date","cat":"History"},
            {"name":"PoetryDB","url":"https://poetrydb.org/random","cat":"Books"},
            {"name":"TarotAPI","url":"https://tarotapi.dev/api/v1/cards/random","cat":"Spiritual"},
            {"name":"icanhazdadjoke","url":"https://icanhazdadjoke.com/","cat":"Humor"},
            {"name":"DadJokes","url":"https://official-joke-api.appspot.com/random_joke","cat":"Humor"},
            # Science
            {"name":"PubMed","url":"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi","cat":"Science"},
            {"name":"CrossRef","url":"https://api.crossref.org/works","cat":"Science"},
            {"name":"OpenAlex","url":"https://api.openalex.org/works","cat":"Science"},
            {"name":"arXiv","url":"http://export.arxiv.org/api/query","cat":"Science"},
            {"name":"Wikipedia","url":"https://en.wikipedia.org/api/rest_v1/page/summary/{title}","cat":"Science"},
            {"name":"NASA_APOD","url":"https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY","cat":"Science"},
            # Translation
            {"name":"MyMemory","url":"https://api.mymemory.translated.net/get","cat":"Translation"},
            {"name":"Lingva","url":"https://lingva.ml/api/v1/pt/en/{text}","cat":"Translation"},
            # NLP
            {"name":"LanguageTool","url":"https://api.languagetool.org/v2/check","cat":"NLP","method":"POST"},
            {"name":"Datamuse","url":"https://api.datamuse.com/words","cat":"NLP"},
            {"name":"FreeDictionaryEN","url":"https://api.dictionaryapi.dev/api/v2/entries/en/{word}","cat":"NLP"},
            # Images
            {"name":"PollinationsFLUX","url":"https://image.pollinations.ai/prompt/{prompt}","cat":"Images"},
            {"name":"DiceBear","url":"https://api.dicebear.com/9.x/micah/svg","cat":"Images"},
            {"name":"Picsum","url":"https://picsum.photos/576/1024","cat":"Images"},
            # Brazil
            {"name":"BrasilAPI","url":"https://brasilapi.com.br/api/feriados/v1/2025","cat":"Brazil"},
            {"name":"IBGE","url":"https://servicodados.ibge.gov.br/api/v3/localidades/estados","cat":"Brazil"},
            {"name":"ViaCEP","url":"https://viacep.com.br/ws/01310100/json/","cat":"Brazil"},
            # Weather
            {"name":"OpenMeteo","url":"https://api.open-meteo.com/v1/forecast?latitude=-23.5&longitude=-46.6&hourly=temperature_2m","cat":"Weather"},
            {"name":"wttr","url":"https://wttr.in/SaoPaulo?format=j1","cat":"Weather"},
            # Currency
            {"name":"ExchangeRate","url":"https://api.exchangerate-api.com/v4/latest/USD","cat":"Finance"},
            {"name":"Frankfurter","url":"https://api.frankfurter.app/latest?to=BRL","cat":"Finance"},
            # Social (sem auth básico)
            {"name":"Reddit_Top","url":"https://www.reddit.com/r/psychology/top.json?limit=10","cat":"Social"},
            {"name":"HackerNews","url":"https://hacker-news.firebaseio.com/v0/topstories.json","cat":"News"},
            # Misc
            {"name":"TinyURL","url":"https://tinyurl.com/api-create.php?url={url}","cat":"Util"},
            {"name":"ipapi","url":"https://ipapi.co/json/","cat":"Util"},
            {"name":"IsGd","url":"https://is.gd/create.php?format=json&url={url}","cat":"Util"},
        ]

# Usar:
# from psicologia_apis import APIdiscovery as API
# APIs_saude = API.find("Health", no_auth=True)
# API_aleatoria = API.random()
# todas_sem_auth = API.all_no_auth()
# confirmadas = API.no_auth_confirmed()
```

---

## 🎯 MAPEAMENTO APIs → SÉRIES (O QUE USAR EM CADA EPISÓDIO)

```python
# Para cada série, as APIs mais relevantes por função
SERIE_API_MAP = {
    "narcisismo": {
        "pesquisa":    "search_semantic_scholar('narcissistic personality disorder covert Malkin')",
        "citação":     "get_zen_quote(keyword='relationship')",
        "dados_BR":    "IBGE dados transtornos personalidade",
        "hashtags":    "generate_hashtags('narcisismo', 1)",
        "imagem_char": "CHAR_PROMPTS['marcos'] + ' villainous expression'",
        "audio_tipo":  "IMPACTO: exag=0.96, cfg=0.09",
        "viral_ref":   "Psych2Go Covert Narcissist 28M views",
    },
    "ansiedade": {
        "pesquisa":    "search_pubmed('high functioning anxiety burnout cortisol')",
        "citação":     "get_zen_quote(keyword='anxiety')",
        "dados_BR":    "DataSUS CID-10 F41 — Outros transtornos ansiosos",
        "hashtags":    "generate_hashtags('ansiedade', 1)",
        "imagem_char": "CHAR_PROMPTS['daniela'] + ' worried expression, notebook'",
        "audio_tipo":  "CHORO: exag=0.95, cfg=0.08",
        "viral_ref":   "Psych2Go Anxiety 18M views",
    },
    "trauma": {
        "pesquisa":    "search_crossref('van der Kolk trauma body keeps score')",
        "citação":     "get_stoic_quote()",
        "dados_BR":    "DataSUS CID-10 F43 — Reações ao estresse",
        "hashtags":    "generate_hashtags('trauma', 1)",
        "imagem_char": "CHAR_PROMPTS['sara'] + ' PTSD flashback, trembling'",
        "audio_tipo":  "CHORO: exag=0.95 + REVELACAO: exag=0.93",
    },
    # [todas as 20 séries seguem o mesmo padrão]
    "_default": {
        "pesquisa":    "search_semantic_scholar(PSICO_ACADEMIC_QUERIES[serie_slug])",
        "citação":     "get_advice() ou get_affirmation()",
        "hashtags":    "generate_hashtags(serie_slug, ep_num)",
        "viral_ref":   "get_viral_mirror_instruction(serie_slug)",
    }
}
```

---

## ✅ APIs CONFIRMADAS AO VIVO (Testadas 2026-05-21)

```
✅ AdviceSlip      adviceslip.com/advice
✅ Affirmations    affirmations.dev
✅ StoicQuotes     stoic-quotes.com/api/quote
✅ LanguageTool    api.languagetool.org/v2/check
✅ MyMemory        api.mymemory.translated.net/get
✅ CrossRef        api.crossref.org/works
✅ PubMed          eutils.ncbi.nlm.nih.gov/entrez
✅ DiceBear        api.dicebear.com/9.x/micah/svg
✅ Lingva          lingva.ml/api/v1/pt/en/{text}
✅ Pollinations    image.pollinations.ai/prompt
```

---

## PIPELINE ÁUDIO V31
```python
TIPOS = {
    "GANCHO":    (0.88, 0.12, 0.0,  0.8),
    "IMPACTO":   (0.96, 0.09, 1.0,  1.6),
    "CHORO":     (0.95, 0.08, 0.5,  1.8),
    "REVELACAO": (0.93, 0.10, 0.7,  1.4),
    "PAUSA":     (0.87, 0.13, 0.4,  1.1),
    "CTA":       (0.74, 0.26, 0.9,  0.0),
    "NORMAL":    (0.82, 0.17, 0.0,  0.65),
}
GATE_SEG   = "agate=threshold=0.028:ratio=8000:attack=1:release=60"
GATE_FINAL = "highpass=f=80,agate=threshold=0.028:ratio=8000:attack=2:release=50"
# Verificação: RMS trough dB = -inf ✅
```

---

## ESTRATÉGIA R$50K/MÊS
```
RPM BR psicologia: R$10-16 | Meta: 3.5M views/mês × R$15 = R$52K
Mês 3-4: 10K subs → R$3K | Mês 9-10: 300K subs → R$50K
Canal: UCyCkIpsVgME9yCj_oXJFheA | Horário: 18-20h BR
```

---

## CREDENCIAIS STATUS
```
✅ GH_PAT, Supabase, Groq, NVIDIA, OpenAI, HF_TOKEN
⚠️ ElevenLabs (quota) → Chatterbox padrão
❌ FALTA: YouTube OAuth, GEMINI_API_KEY, Instagram, TikTok
```

## LINKS
```
Hub:     https://repovazio.vercel.app/hub.html
Vídeos:  https://repovazio.vercel.app/videos-prontos.html
Painel:  https://repovazio.vercel.app/painel-400.html
Skill:   https://github.com/tafita81/Repovazio/blob/main/docs/SKILL_V32.md
```
