#!/usr/bin/env python3
"""
psicologia_apis.py — V31 API Hub
Todas as APIs públicas integradas ao pipeline psicologia.doc
Uso: from psicologia_apis import *
"""

import requests, json, urllib.parse, os, time

# ═══════════════════════════════════════════════════════════════════
# 1. QUOTES & FRASES PSICOLÓGICAS (SEM AUTH, ILIMITADO)
# ═══════════════════════════════════════════════════════════════════

def get_zen_quote(keyword=None):
    """ZenQuotes — citações por tema (sem auth)"""
    url = "https://zenquotes.io/api/random"
    if keyword:
        key = os.getenv("ZENQUOTES_API_KEY", "")
        url = f"https://zenquotes.io/api/quotes/{key}&keyword={keyword}" if key else url
    r = requests.get(url, timeout=10).json()
    return {"quote": r[0]["q"], "author": r[0]["a"]} if r else {}

def get_quotable(tags="psychology,wisdom", limit=5):
    """Quotable — citações por tag (open source, sem auth)"""
    url = f"https://api.quotable.io/quotes?tags={tags}&limit={limit}"
    r = requests.get(url, timeout=10).json()
    return [{"quote": q["content"], "author": q["author"]} for q in r.get("results", [])]

def get_advice():
    """AdviceSlip — conselhos aleatórios (sem auth)"""
    r = requests.get("https://api.adviceslip.com/advice", timeout=10).json()
    return r.get("slip", {}).get("advice", "")

def get_affirmation():
    """Affirmations.dev — afirmações positivas (sem auth)"""
    r = requests.get("https://www.affirmations.dev/", timeout=10).json()
    return r.get("affirmation", "")

def get_stoic_quote():
    """Stoic Quotes API — filosofia estoica (sem auth)"""
    r = requests.get("https://stoic-quotes.com/api/quote", timeout=10).json()
    return {"quote": r.get("text",""), "author": r.get("author","")}

QUOTE_KEYWORDS_PSICO = [
    "anxiety", "healing", "resilience", "emotion", "mind",
    "self", "pain", "courage", "change", "growth", "trauma", "peace"
]

# ═══════════════════════════════════════════════════════════════════
# 2. ANÁLISE DE SENTIMENTO & EMOÇÃO (SCRIPT OPTIMIZATION)
# ═══════════════════════════════════════════════════════════════════

def analyze_emotion_hf(text, lang="pt"):
    """HuggingFace — detecção de emoção PT-BR (free, key opcional)"""
    HF_TOKEN = os.getenv("HF_TOKEN", "")
    # Modelo PT-BR: pysentimiento/robertuito-emotion-analysis
    MODEL_PT = "pysentimiento/robertuito-emotion-analysis"
    MODEL_EN = "j-hartmann/emotion-english-distilroberta-base"
    model = MODEL_PT if lang == "pt" else MODEL_EN
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    r = requests.post(
        f"https://api-inference.huggingface.co/models/{model}",
        headers=headers,
        json={"inputs": text}, timeout=30
    )
    if r.status_code == 200:
        results = r.json()
        if isinstance(results, list) and results:
            return sorted(results[0], key=lambda x: x["score"], reverse=True)
    return []

def analyze_sentiment_groq(text, groq_key=None):
    """Groq — análise de sentimento/emoção via LLM (free, 14K req/dia)"""
    key = groq_key or os.getenv("GROQ_API_KEY", "")
    if not key: return {}
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "max_tokens": 100,
              "messages": [{"role": "user", "content":
                f"Classifique o texto em: IMPACTO/CHORO/REVELACAO/GANCHO/PAUSA/CTA/NORMAL. Responda só a palavra.\nTexto: {text}"}]},
        timeout=15
    )
    if r.status_code == 200:
        return {"label": r.json()["choices"][0]["message"]["content"].strip()}
    return {}

# ═══════════════════════════════════════════════════════════════════
# 3. TRADUÇÃO (EXPANDIR PARA OUTROS IDIOMAS)
# ═══════════════════════════════════════════════════════════════════

def translate_libre(text, source="pt", target="en"):
    """LibreTranslate — open source, PT→EN gratuito (sem auth no host público)"""
    hosts = [
        "https://libretranslate.com",
        "https://translate.argosopentech.com",
        "https://translate.terraprint.co",
    ]
    for host in hosts:
        try:
            r = requests.post(f"{host}/translate",
                json={"q": text, "source": source, "target": target, "format": "text"},
                timeout=15)
            if r.status_code == 200:
                return r.json().get("translatedText", "")
        except: continue
    return text

def translate_mymemory(text, source="pt-br", target="en"):
    """MyMemory — grátis 10K palavras/dia (sem auth)"""
    url = f"https://api.mymemory.translated.net/get"
    r = requests.get(url, params={"q": text, "langpair": f"{source}|{target}"}, timeout=15)
    if r.status_code == 200:
        return r.json().get("responseData", {}).get("translatedText", text)
    return text

def translate_lingva(text, source="pt", target="en"):
    """Lingva — alternativa Google Translate (sem auth)"""
    encoded = urllib.parse.quote(text)
    r = requests.get(f"https://lingva.ml/api/v1/{source}/{target}/{encoded}", timeout=15)
    if r.status_code == 200:
        return r.json().get("translation", text)
    return text

# ═══════════════════════════════════════════════════════════════════
# 4. CONTEÚDO CIENTÍFICO (PESQUISA PSICOLÓGICA)
# ═══════════════════════════════════════════════════════════════════

def search_pubmed(query, max_results=5):
    """PubMed E-utilities — artigos de psicologia (sem auth)"""
    # Buscar IDs
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    r = requests.get(search_url, params={
        "db": "pubmed", "term": query, "retmax": max_results,
        "retmode": "json", "sort": "relevance"
    }, timeout=15)
    ids = r.json().get("esearchresult", {}).get("idlist", [])
    if not ids: return []
    # Buscar detalhes
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    r2 = requests.get(fetch_url, params={
        "db": "pubmed", "id": ",".join(ids), "retmode": "xml"
    }, timeout=15)
    return {"raw": r2.text[:3000], "ids": ids}

def search_semantic_scholar(query, limit=5):
    """Semantic Scholar — IA para busca acadêmica (sem auth, gratuito)"""
    r = requests.get("https://api.semanticscholar.org/graph/v1/paper/search",
        params={"query": query, "limit": limit,
                "fields": "title,authors,year,abstract,citationCount"},
        timeout=15)
    if r.status_code == 200:
        return r.json().get("data", [])
    return []

def search_crossref(query, limit=5):
    """CrossRef — citações acadêmicas (sem auth)"""
    r = requests.get("https://api.crossref.org/works",
        params={"query": query, "rows": limit, "select": "title,author,published,DOI"},
        timeout=15)
    if r.status_code == 200:
        return r.json().get("message", {}).get("items", [])
    return []

PSICO_QUERIES = {
    "narcisismo":     "narcissistic personality disorder covert narcissism relationships",
    "apego":          "attachment theory adult attachment relationships Ainsworth",
    "gaslighting":    "gaslighting psychological manipulation memory distortion",
    "ansiedade":      "high functioning anxiety functional anxiety productivity",
    "depressao":      "masked depression functional depression workplace",
    "trauma":         "complex PTSD van der Kolk body trauma therapy",
    "impostor":       "impostor syndrome competence high achievers Clance",
    "codependencia":  "codependency emotional dependency relationships patterns",
    "resilencia":     "resilience post-traumatic growth psychological recovery",
    "neurociencia":   "emotion regulation prefrontal cortex stress burnout neuroscience",
}

# ═══════════════════════════════════════════════════════════════════
# 5. GERAÇÃO DE IMAGENS (TODOS OS PROVIDERS)
# ═══════════════════════════════════════════════════════════════════

def gen_image_pollinations(prompt, w=576, h=1024, model="flux", seed=42):
    """Pollinations FLUX — sem auth, ilimitado"""
    enc = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{enc}?width={w}&height={h}&model={model}&seed={seed}&nologo=true"

def gen_image_dicebear(style="micah", seed="daniela", bg="06060F"):
    """DiceBear — avatares consistentes sem auth (para personagens)"""
    return f"https://api.dicebear.com/9.x/{style}/svg?seed={seed}&backgroundColor={bg}&radius=50"

def gen_image_picsum(w=576, h=1024, seed=42):
    """Lorem Picsum — imagens aleatórias sem auth"""
    return f"https://picsum.photos/seed/{seed}/{w}/{h}"

def gen_image_unsplash(query, w=576, h=1024):
    """Unsplash Source — imagens reais sem auth (uso educacional)"""
    enc = urllib.parse.quote(query)
    return f"https://source.unsplash.com/{w}x{h}/?{enc}"

# ═══════════════════════════════════════════════════════════════════
# 6. VERIFICAÇÃO & GRAMÁTICA (QUALIDADE DO SCRIPT)
# ═══════════════════════════════════════════════════════════════════

def check_grammar_languagetool(text, lang="pt-BR"):
    """LanguageTool — correção gramatical PT-BR (sem auth, 20 req/min)"""
    r = requests.post("https://api.languagetool.org/v2/check",
        data={"text": text, "language": lang}, timeout=20)
    if r.status_code == 200:
        matches = r.json().get("matches", [])
        return [{"message": m["message"], "offset": m["offset"],
                 "length": m["length"], "replacement": m.get("replacements",[])}
                for m in matches]
    return []

def detect_language(text):
    """DetectLanguage API (free tier)"""
    # Alternativa sem key: usar HuggingFace
    r = requests.post(
        "https://api-inference.huggingface.co/models/papluca/xlm-roberta-base-language-detection",
        json={"inputs": text}, timeout=15)
    if r.status_code == 200:
        results = r.json()
        if isinstance(results, list) and results:
            return results[0][0] if isinstance(results[0], list) else results[0]
    return {}

# ═══════════════════════════════════════════════════════════════════
# 7. TENDÊNCIAS & SEO
# ═══════════════════════════════════════════════════════════════════

def get_youtube_trending_tags(topic, region="BR"):
    """YouTube Data API — trending videos por tema (grátis 10K/dia)"""
    api_key = os.getenv("YOUTUBE_API_KEY", "")
    if not api_key: return []
    r = requests.get("https://www.googleapis.com/youtube/v3/search",
        params={"part": "snippet", "q": topic, "type": "video",
                "regionCode": region, "maxResults": 10, "key": api_key},
        timeout=15)
    if r.status_code == 200:
        return [{"title": i["snippet"]["title"], "tags": i["snippet"].get("tags",[])}
                for i in r.json().get("items", [])]
    return []

def get_twitter_trends(woeid=23424768):
    """Twitter/X v2 — trends BR (woeid=23424768)"""
    # Bearer token necessário para v2
    bearer = os.getenv("TWITTER_BEARER_TOKEN", "")
    if not bearer: return []
    r = requests.get(f"https://api.twitter.com/1.1/trends/place.json?id={woeid}",
        headers={"Authorization": f"Bearer {bearer}"}, timeout=15)
    if r.status_code == 200:
        return r.json()[0].get("trends", [])[:10]
    return []

def get_google_trends_related(keyword):
    """pytrends — Google Trends (sem auth oficial, via biblioteca)"""
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="pt-BR", tz=180)
        pt.build_payload([keyword], geo="BR")
        return pt.related_queries()[keyword]["top"].to_dict("records")
    except: return []

# ═══════════════════════════════════════════════════════════════════
# 8. DADOS SOBRE SAÚDE MENTAL (BRASIL)
# ═══════════════════════════════════════════════════════════════════

def get_datasus_info(code="F40"):
    """DataSUS — dados do SUS (sem auth, dados CID-10)"""
    # CID-10 relacionados à psicologia
    PSICO_CIDS = {
        "F40": "Transtornos ansiosos fóbicos",
        "F41": "Outros transtornos ansiosos",
        "F32": "Episódios depressivos",
        "F60": "Transtornos específicos de personalidade",
        "F43": "Reações ao estresse grave e transtornos de adaptação",
        "F20": "Esquizofrenia",
    }
    return PSICO_CIDS.get(code, f"CID-10: {code}")

# ═══════════════════════════════════════════════════════════════════
# 9. MULTIMÍDIA & UTILIDADES
# ═══════════════════════════════════════════════════════════════════

def get_color_from_emotion(emotion):
    """Mapear emoção → cor da paleta psicologia.doc"""
    COLOR_MAP = {
        "joy":        "#F59E0B",  # gold
        "sadness":    "#8B5CF6",  # purple
        "anger":      "#E11D48",  # crimson
        "fear":       "#2563EB",  # blue
        "surprise":   "#7C3AED",  # violet
        "disgust":    "#DC2626",  # red
        "neutral":    "#94a3b8",  # gray
        "anticipation":"#F59E0B", # gold
    }
    return COLOR_MAP.get(emotion.lower(), "#7C3AED")

def text_to_ssml(text):
    """Converter texto com CAPS em SSML com emphasis para EdgeTTS"""
    import re
    def replace_caps(m):
        word = m.group(0)
        return f'<emphasis level="strong">{word.lower()}</emphasis>'
    text_ssml = re.sub(r'\b[A-ZÁÉÍÓÚÃÕÂÊÔÇ]{2,}\b', replace_caps, text)
    return f'<speak><prosody rate="slow">{text_ssml}</prosody></speak>'

def generate_hashtags(series_slug, ep_num, extra=None):
    """Gerar hashtags otimizadas para YouTube/Instagram BR"""
    BASE = {
        "narcisismo":    ["narcisismo","relacionamentotoxico","manipulacao","narcisistaencoberto"],
        "apego":         ["apegoansioso","apego","relacionamentos","estilodeapego"],
        "gaslighting":   ["gaslighting","manipulacaoemocional","abusoemocional"],
        "infancia":      ["traumadeinfancia","familiadisfuncional","curaemocional"],
        "ansiedade":     ["ansiedade","ansiedadealtofuncional","saudemental"],
        "depressao":     ["depressao","depressaosilenciosa","saudemental"],
        "limites":       ["limitessaudaveis","limites","autoestima"],
        "autoestima":    ["autoestima","autossabotagem","desenvolvimentopessoal"],
        "relacionamentos":["relacionamentotoxico","padroes","relacionamentos"],
        "codependencia": ["codependencia","dependenciaemocional","limites"],
        "impostor":      ["sindromedoimpostor","perfeccionismo","autoconhecimento"],
        "abandono":      ["medodeabandono","apego","relacionamentos"],
        "cura":          ["cura","curaemocional","jornadadecura"],
        "amorporprio":   ["amorporprio","autoconhecimento","autocuidado"],
        "trauma":        ["trauma","traumacomplexo","tept"],
        "manipulacao":   ["manipulacao","manipulacaoemocional","narcisismo"],
        "cerebro":       ["neurociencia","cerebro","psicologia"],
        "vicoemocional": ["vicoemocional","dependenciaemocional","relacionamentos"],
        "familia":       ["familiadisfuncional","familia","trauma"],
        "resiliencia":   ["resiliencia","curaemocional","recomeco"],
    }
    tags = BASE.get(series_slug, [])
    base_tags = ["psicologia","saudemental","psicologiadoc","danielacoelho","autoconhecimento"]
    all_tags = list(dict.fromkeys(tags + base_tags + (extra or [])))
    return ["#"+t for t in all_tags[:30]]


# ═══════════════════════════════════════════════════════════════════
# 10. SCRIPT ENRICHER (USA TODAS AS APIS PARA MELHORAR SCRIPTS)
# ═══════════════════════════════════════════════════════════════════

def enrich_script(script_text, series_slug, ep_num=1):
    """
    Enriquece um script com dados de múltiplas APIs:
    1. Busca citação científica relevante via Semantic Scholar
    2. Adiciona frase de abertura via ZenQuotes
    3. Verifica gramática via LanguageTool
    4. Analisa emoção dominante via HuggingFace
    5. Gera hashtags otimizadas
    """
    results = {}

    # 1. Citação científica
    query = PSICO_QUERIES.get(series_slug, series_slug + " psychology research")
    papers = search_semantic_scholar(query, limit=3)
    if papers:
        p = papers[0]
        authors = [a["name"].split()[-1] for a in p.get("authors",[])][:2]
        year = p.get("year", "")
        results["citation"] = f"{', '.join(authors)} ({year}): {p.get('title','')[:80]}"

    # 2. Frase inspiradora relacionada
    keyword_map = {
        "narcisismo": "relationship", "ansiedade": "anxiety",
        "depressao": "healing", "trauma": "resilience",
        "impostor": "courage", "cura": "peace",
    }
    kw = keyword_map.get(series_slug, "wisdom")
    try:
        quote = get_zen_quote(kw)
        results["opening_quote"] = quote
    except: pass

    # 3. Análise de emoção do script
    try:
        emotions = analyze_emotion_hf(script_text[:500], lang="pt")
        results["dominant_emotion"] = emotions[0] if emotions else {}
    except: pass

    # 4. Hashtags
    results["hashtags"] = generate_hashtags(series_slug, ep_num)

    # 5. SSML para TTS
    results["ssml"] = text_to_ssml(script_text[:200])

    return results


if __name__ == "__main__":
    print("=== TESTE psicologia_apis.py ===")

    print("\n[1] ZenQuotes:")
    q = get_zen_quote("healing")
    print(f"  '{q.get('quote','...')}' — {q.get('author','')}")

    print("\n[2] Affirmation:")
    try:
        a = get_affirmation()
        print(f"  '{a}'")
    except: print("  (offline)")

    print("\n[3] Quotable (psychology tag):")
    quotes = get_quotable("wisdom", 2)
    for q in quotes:
        print(f"  '{q['quote'][:60]}' — {q['author']}")

    print("\n[4] Stoic Quote:")
    s = get_stoic_quote()
    print(f"  '{s.get('quote','...')}'")

    print("\n[5] LanguageTool BR:")
    errs = check_grammar_languagetool("Isso é uma frase com um erros", "pt-BR")
    print(f"  {len(errs)} problemas encontrados")

    print("\n[6] Semantic Scholar (narcissism):")
    papers = search_semantic_scholar("narcissistic personality disorder covert", 2)
    for p in papers:
        print(f"  {p.get('year','')} {p.get('title','')[:60]}")

    print("\n[7] Hashtags Narcisismo:")
    tags = generate_hashtags("narcisismo", 1)
    print(f"  {' '.join(tags[:8])}")

    print("\n[8] Pollinations URL:")
    url = gen_image_pollinations("kawaii chibi anime Daniela psicologia", 576, 1024)
    print(f"  {url[:80]}...")

    print("\n[9] SSML:")
    ssml = text_to_ssml("Isso tem NOME. É narcisismo ENCOBERTO.")
    print(f"  {ssml}")

    print("\n[10] Enrichment:")
    enriched = enrich_script("Você conhece a Laís? Isso tem NOME.", "narcisismo", 1)
    print(f"  Citation: {enriched.get('citation','N/A')[:60]}")
    print(f"  Hashtags: {' '.join(enriched.get('hashtags',[])[:5])}")
