#!/usr/bin/env python3
"""
reddit_video_engine.py — Reddit questions → Viral psychology video
Ação 4 de 20: r/NarcissisticAbuse + r/relationship_advice → roteiro → vídeo

Cruzamento: Reddit Pushshift (no-auth) + LLM + Edge TTS + pipeline existente
Formato: Psych2Go style — responde perguntas reais com ciência real
"""
import requests, os, json, time
from datetime import datetime

GROQ_KEY = os.getenv("GROQ_API_KEY","")
SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY","")

SUBREDDITS_PSICO = [
    "NarcissisticAbuse","relationship_advice","AnxietySupport",
    "BPD","CPTSD","raisedbynarcissists","emotionalabuse"
]

def buscar_posts_reddit(subreddit: str, limite: int = 5) -> list:
    try:
        r = requests.get(
            f"https://api.pushshift.io/reddit/search/submission",
            params={"subreddit": subreddit, "size": limite,
                    "sort": "score", "score": ">100",
                    "fields": "title,selftext,score,url"},
            headers={"User-Agent": "psicologia-doc-research/1.0"},
            timeout=15)
        if r.status_code == 200:
            return r.json().get("data", [])
    except:
        pass
    
    # Fallback: Reddit JSON público
    try:
        r2 = requests.get(
            f"https://www.reddit.com/r/{subreddit}/top/.json",
            params={"t": "month", "limit": limite},
            headers={"User-Agent": "psicologia-doc-research/1.0"},
            timeout=15)
        if r2.status_code == 200:
            posts = r2.json().get("data",{}).get("children",[])
            return [p["data"] for p in posts]
    except:
        pass
    return []

def transformar_em_roteiro(posts: list, idioma: str = "PT-BR") -> dict:
    if not GROQ_KEY or not posts: return {}
    
    posts_texto = "
".join([f"- {p.get('title','')} (score: {p.get('score',0)})" for p in posts[:5]])
    
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile",
              "messages": [{"role":"user","content": f"""
Você é Daniela Coelho, pesquisadora de comportamento humano brasileira.
Estas são perguntas reais de pessoas em sofrimento no Reddit:
{posts_texto}

Crie um roteiro viral em {idioma} para YouTube (12 min) respondendo essas dúvidas reais.
Use pesquisa: Malkin/Harvard, van der Kolk, Ainsworth, Gottman, Beck.
Tom: íntimo, científico, não-vitimizante, esperançoso.
JSON: {{"titulo":"...","hook":"...","roteiro_bullets":["b1","b2"],"pesquisadores":"...","cta":"..."}}
"""}],
              "max_tokens": 2000, "response_format": {"type": "json_object"}},
        timeout=60)
    
    if r.status_code == 200:
        return json.loads(r.json()["choices"][0]["message"]["content"])
    return {}

def run():
    print("ACAO 4: Reddit → Video Pipeline")
    print("Formato: Psych2Go style — perguntas reais + ciência real")
    
    for sub in SUBREDDITS_PSICO[:2]:
        print(f"
  Buscando r/{sub}...")
        posts = buscar_posts_reddit(sub, 5)
        print(f"  Posts encontrados: {len(posts)}")
        
        if posts:
            for p in posts[:3]:
                print(f"    • {p.get('title','')[:70]} (score: {p.get('score',0)})")
            
            print(f"  Gerando roteiro...")
            roteiro = transformar_em_roteiro(posts)
            if roteiro:
                print(f"  Titulo: {roteiro.get('titulo','')[:60]}")
                
                if SB_KEY:
                    requests.post(f"{SB_URL}/rest/v1/content_pipeline",
                        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                                 "Content-Type": "application/json"},
                        json={**roteiro, "fonte": f"reddit_{sub}", 
                              "status": "roteiro_pronto",
                              "data_geracao": datetime.now().isoformat()},
                        timeout=10)
        time.sleep(2)
    
    print("
  Status: Reddit pipeline ativo")
    print("  Roda via GitHub Action: research-monitor.yml")

if __name__ == "__main__":
    run()
