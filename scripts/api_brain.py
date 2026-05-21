#!/usr/bin/env python3
"""
api_brain.py — Cérebro Quântico de APIs V33
Módulo central de descoberta e uso de APIs para psicologia.doc
Base: 145 APIs no Supabase | 40K+ descobríveis via diretórios

Uso:
  from api_brain import Brain
  
  # Buscar APIs por query
  Brain.search("quotes pt-br", no_auth=True)
  
  # APIs prontas para usar (alta relevância, sem auth)
  Brain.ready_to_use()
  
  # Descobrir novas (live, dos diretórios)
  Brain.discover("Health", no_auth=True)
  
  # Chamar uma API diretamente
  Brain.call("ZenQuotes")
  Brain.call("AdviceSlip")
  Brain.call("LanguageTool", method="POST", data={"text":"Ola", "language":"pt-BR"})
"""

import requests, json, time, os
from functools import lru_cache

SB_URL = os.getenv("SUPABASE_URL", "https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ══════════════════════════════════════════════════════════════════
# APIs CONFIRMADAS — cache local (sem depender de rede)
# ══════════════════════════════════════════════════════════════════

CONFIRMED_APIS = {
    # Quotes (sem auth, testadas ao vivo)
    "AdviceSlip":    {"url":"https://api.adviceslip.com/advice",                    "parse": lambda r: r["slip"]["advice"],              "cat":"Quotes"},
    "Affirmations":  {"url":"https://www.affirmations.dev/",                        "parse": lambda r: r["affirmation"],                  "cat":"Quotes"},
    "StoicQuotes":   {"url":"https://stoic-quotes.com/api/quote",                   "parse": lambda r: f"{r['text']} — {r['author']}", "cat":"Quotes"},
    "ZenQuotes":     {"url":"https://zenquotes.io/api/random",                      "parse": lambda r: f"{r[0]['q']} — {r[0]['a']}", "cat":"Quotes"},
    "Quotable":      {"url":"https://api.quotable.io/random?tags=wisdom",           "parse": lambda r: f"{r['content']} — {r['author']}", "cat":"Quotes"},
    "UselessFacts":  {"url":"https://uselessfacts.jsph.pl/random.json?language=en", "parse": lambda r: r["text"],                         "cat":"Facts"},
    "DummyQuote":    {"url":"https://dummyjson.com/quotes/random",                  "parse": lambda r: f"{r['quote']} — {r['author']}", "cat":"Quotes"},
    # Science (sem auth)
    "Wikipedia":     {"url":"https://en.wikipedia.org/api/rest_v1/page/summary/{title}", "parse": lambda r: r.get("extract",""), "cat":"Science"},
    "Numbers":       {"url":"http://numbersapi.com/{n}/trivia",                     "parse": lambda r: r,                                 "cat":"Science"},
    # Translation
    "MyMemory":      {"url":"https://api.mymemory.translated.net/get",              "parse": lambda r: r["responseData"]["translatedText"], "cat":"Translation"},
    "Lingva":        {"url":"https://lingva.ml/api/v1/{src}/{target}/{text}",       "parse": lambda r: r["translation"],                  "cat":"Translation"},
    # Utilities
    "TinyURL":       {"url":"https://tinyurl.com/api-create.php?url={url}",         "parse": lambda r: r,                                 "cat":"Util"},
    "ExchangeRate":  {"url":"https://api.exchangerate-api.com/v4/latest/USD",       "parse": lambda r: r["rates"]["BRL"],                 "cat":"Finance"},
    "OpenMeteo":     {"url":"https://api.open-meteo.com/v1/forecast?latitude=-23.5&longitude=-46.6&current=temperature_2m,precipitation", "parse": lambda r: r["current"], "cat":"Weather"},
    "BrasilAPI_Feri":{"url":"https://brasilapi.com.br/api/feriados/v1/{ano}",       "parse": lambda r: r,                                 "cat":"Brazil"},
    # NLP (com POST)
    "LanguageTool":  {"url":"https://api.languagetool.org/v2/check",                "parse": lambda r: r.get("matches",[]),               "cat":"NLP", "method":"POST"},
    "Datamuse":      {"url":"https://api.datamuse.com/words?rel_syn={word}",        "parse": lambda r: [x["word"] for x in r[:5]],        "cat":"NLP"},
    # Brazil
    "IBGE_Estado":   {"url":"https://servicodados.ibge.gov.br/api/v3/localidades/estados","parse": lambda r: [x["nome"] for x in r], "cat":"Brazil"},
}

class Brain:
    """Cérebro Quântico de APIs — acesso unificado a 145+ APIs"""

    @staticmethod
    def search(query: str, no_auth: bool = False, relevance: int = 0, limit: int = 20) -> list:
        """Busca APIs no Supabase por query"""
        if not SB_KEY:
            # Fallback: busca local em CONFIRMED_APIS
            q = query.lower()
            return [{"name":k,"cat":v["cat"],"url":v["url"]} 
                    for k,v in CONFIRMED_APIS.items() 
                    if q in k.lower() or q in v.get("cat","").lower()]
        
        headers = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"}
        params = {"or": f"(name.ilike.%{query}%,description.ilike.%{query}%,use_case.ilike.%{query}%)",
                  "order": "relevance.desc", "limit": str(limit)}
        if no_auth: params["auth_type"] = "eq.none"
        if relevance > 0: params["relevance"] = f"gte.{relevance}"
        
        r = requests.get(f"{SB_URL}/rest/v1/api_brain", headers=headers, params=params, timeout=10)
        return r.json() if r.status_code == 200 else []

    @staticmethod
    def ready_to_use() -> list:
        """APIs alta relevância sem auth — prontas para produção"""
        if not SB_KEY: return list(CONFIRMED_APIS.values())
        
        headers = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"}
        r = requests.get(f"{SB_URL}/rest/v1/v_apis_no_auth", 
            headers=headers, params={"relevance": "eq.3", "limit": "50"}, timeout=10)
        return r.json() if r.status_code == 200 else []

    @staticmethod
    def discover(category: str, no_auth: bool = True) -> list:
        """Descobre APIs live no diretório público-apis"""
        try:
            auth = "null" if no_auth else ""
            r = requests.get(
                f"https://api.publicapis.org/entries?category={category}&auth={auth}&https=true",
                timeout=10
            )
            if r.status_code == 200:
                return r.json().get("entries", [])
        except Exception as e:
            print(f"⚠️ Discover falhou: {e}")
        return []

    @staticmethod
    def call(name: str, timeout: int = 10, **kwargs) -> any:
        """Chama uma API confirmada pelo nome"""
        api = CONFIRMED_APIS.get(name)
        if not api:
            raise ValueError(f"API '{name}' não encontrada. Use Brain.search()")
        
        url = api["url"]
        # Substituir placeholders
        for k, v in kwargs.items():
            url = url.replace(f"{{{k}}}", str(v))
        
        method = api.get("method", "GET")
        if method == "POST":
            data = kwargs.get("data", {})
            r = requests.post(url, data=data, timeout=timeout)
        else:
            r = requests.get(url, timeout=timeout)
        
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}: {r.text[:100]}")
        
        result = r.json() if "json" in r.headers.get("content-type","") else r.text
        
        parse = api.get("parse")
        if parse:
            try: return parse(result)
            except: return result
        return result

    @staticmethod
    def stats() -> dict:
        """Estatísticas do cérebro de APIs"""
        if SB_KEY:
            headers = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"}
            r = requests.get(f"{SB_URL}/rest/v1/api_brain?select=category,auth_type,relevance,tested,working",
                headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return {
                    "total":          len(data),
                    "sem_auth":       sum(1 for x in data if x["auth_type"] == "none"),
                    "alta_relevancia":sum(1 for x in data if x["relevance"] == 3),
                    "testadas_ok":    sum(1 for x in data if x.get("tested") and x.get("working")),
                    "categorias":     len(set(x["category"] for x in data)),
                }
        return {"local_apis": len(CONFIRMED_APIS)}

    @staticmethod
    def add(api_data: dict) -> bool:
        """Adiciona nova API ao cérebro (Supabase)"""
        if not SB_KEY: return False
        headers = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                   "Content-Type": "application/json", "Prefer": "return=minimal"}
        r = requests.post(f"{SB_URL}/rest/v1/api_brain", headers=headers, json=api_data, timeout=15)
        return r.status_code < 300

    @staticmethod
    def quick_quote(tema: str = None) -> str:
        """Retorna uma citação rápida — fallback em cascata"""
        sources = ["AdviceSlip", "Affirmations", "StoicQuotes", "UselessFacts"]
        import random
        random.shuffle(sources)
        for src in sources:
            try:
                return f"[{src}] {Brain.call(src)}"
            except: pass
        return "A cura começa pelo nome. — Daniela Coelho"

    @staticmethod
    def translate_pt_en(text: str) -> str:
        """Traduz PT→EN com fallback automático"""
        # 1. MyMemory
        try:
            import urllib.parse
            r = requests.get(
                f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair=pt|en",
                timeout=10
            )
            if r.status_code == 200:
                return r.json()["responseData"]["translatedText"]
        except: pass
        # 2. Lingva
        try:
            import urllib.parse
            r = requests.get(
                f"https://lingva.ml/api/v1/pt/en/{urllib.parse.quote(text)}",
                timeout=10
            )
            if r.status_code == 200:
                return r.json()["translation"]
        except: pass
        return text

    @staticmethod
    def check_grammar(text: str, lang: str = "pt-BR") -> list:
        """Verifica gramática via LanguageTool"""
        r = requests.post("https://api.languagetool.org/v2/check",
            data={"text": text, "language": lang}, timeout=15)
        if r.status_code == 200:
            return r.json().get("matches", [])
        return []

    @staticmethod
    def test_all_no_auth(verbose: bool = False) -> dict:
        """Testa todas as APIs sem auth — atualiza banco"""
        results = {"ok": [], "fail": [], "total": len(CONFIRMED_APIS)}
        for name, api in CONFIRMED_APIS.items():
            try:
                url = api["url"].split("{")[0]  # remove placeholders
                method = api.get("method", "GET")
                start = time.time()
                if method == "POST":
                    r = requests.post(url, data={"text":"teste","language":"pt-BR"}, timeout=8)
                else:
                    r = requests.get(url, timeout=8)
                latency = int((time.time()-start)*1000)
                ok = r.status_code < 400
                if ok: results["ok"].append(name)
                else:  results["fail"].append(name)
                if verbose: print(f"  {"✅" if ok else "❌"} {name}: {r.status_code} ({latency}ms)")
            except Exception as e:
                results["fail"].append(name)
                if verbose: print(f"  ❌ {name}: {e}")
        return results


if __name__ == "__main__":
    print("=== CÉREBRO QUÂNTICO DE APIs V33 ===\n")
    
    s = Brain.stats()
    print(f"Total no banco: {s.get('total', s.get('local_apis',0))}")
    
    print("\n[Quote rápida]:")
    print(f"  {Brain.quick_quote()}")
    
    print("\n[Tradução]:")
    print(f"  ansiedade → {Brain.translate_pt_en('ansiedade')}")
    
    print("\n[Teste APIs sem auth]:")
    r = Brain.test_all_no_auth(verbose=True)
    print(f"  ✅ {len(r['ok'])}/{r['total']} funcionando")
