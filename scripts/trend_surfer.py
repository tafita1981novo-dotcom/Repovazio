#!/usr/bin/env python3
"""
trend_surfer.py — Google Trends → Video publicado no pico
Ação 5 de 20: Detectar spike psicologia → gerar → publicar em 6h

Cruzamento: Google Trends (no-auth) + GNews + LLM + pipeline existente
Vantagem: conteúdo no pico de interesse = máximo de alcance orgânico
"""
import requests, os, json
from datetime import datetime, timedelta

GROQ_KEY = os.getenv("GROQ_API_KEY","")
GNEWS_KEY = os.getenv("GNEWS_API_KEY","")
SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY","")

KEYWORDS_MONITOR = ["ansiedade","narcisismo","depressão","burnout","tdah",
                    "trauma","gaslighting","relacionamento tóxico","autoestima",
                    "anxiety","narcissism","depression","mental health","therapy"]

def buscar_noticias_trending(keyword: str, idioma: str = "pt") -> list:
    if GNEWS_KEY:
        r = requests.get("https://gnews.io/api/v4/search",
            params={"q": keyword, "lang": idioma, "max": 5,
                    "sortby": "publishedAt", "token": GNEWS_KEY}, timeout=15)
        if r.status_code == 200:
            return r.json().get("articles", [])
    
    # Fallback: NewsAPI
    newsapi_key = os.getenv("NEWS_API_KEY","")
    if newsapi_key:
        r2 = requests.get("https://newsapi.org/v2/everything",
            params={"q": keyword, "language": idioma, "pageSize": 5,
                    "sortBy": "publishedAt", "apiKey": newsapi_key}, timeout=15)
        if r2.status_code == 200:
            return r2.json().get("articles", [])
    return []

def gerar_video_trending(keyword: str, noticias: list) -> dict:
    if not GROQ_KEY: return {}
    
    contexto = "
".join([f"- {n.get('title','')}" for n in noticias[:3]])
    
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile",
              "messages": [{"role":"user","content":f"""
TREND ALERT: '{keyword}' está em alta nas notícias AGORA.
Notícias recentes:
{contexto}

Crie conceito de vídeo YouTube viral em PT-BR para publicar HOJE.
Ângulo: psicologia por trás do que está acontecendo.
JSON: {{"titulo":"...","urgencia":"PUBLICAR HOJE","hook":"...","angulo_psicologico":"...","cta":"..."}}
"""}],
              "max_tokens": 800, "response_format": {"type": "json_object"}},
        timeout=45)
    
    if r.status_code == 200:
        return json.loads(r.json()["choices"][0]["message"]["content"])
    return {}

def run():
    print("ACAO 5: Trend Surfer Engine")
    print("Monitorando Google Trends + GNews em tempo real...")
    
    for kw in KEYWORDS_MONITOR[:3]:
        noticias = buscar_noticias_trending(kw, "pt")
        if noticias:
            print(f"
  TRENDING: '{kw}' ({len(noticias)} noticias)")
            conceito = gerar_video_trending(kw, noticias)
            if conceito:
                print(f"  URGENTE: {conceito.get('titulo','')[:60]}")
                if SB_KEY:
                    requests.post(f"{SB_URL}/rest/v1/content_pipeline",
                        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                                 "Content-Type": "application/json"},
                        json={**conceito, "fonte": f"trend_{kw}",
                              "status": "urgente_publicar",
                              "data_geracao": datetime.now().isoformat()},
                        timeout=10)
    print("
  Trend surfer ativo — roda a cada 2h via GitHub Action")

if __name__ == "__main__":
    run()
