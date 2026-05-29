#!/usr/bin/env python3
# master_quantum_orchestrator.py
# ORQUESTRADOR QUÂNTICO MESTRE — psicologia.doc
# Usa TODOS os secrets configurados como agentes em paralelo:
# GROQ + NVIDIA + GEMINI + OPENAI + ELEVENLABS + HF + DEEPSEEK
# Executa: pesquisa APIs -> gera conteudo -> publica -> monitora

import os, json, requests, time, random, threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── TODOS os secrets disponíveis ─────────────────────────
GROQ   = os.getenv("GROQ_API_KEY","")
NVIDIA = os.getenv("NVIDIA_API_KEY","")
GEMINI = os.getenv("GEMINI_API_KEY","")
OPENAI = os.getenv("OPENAI_API_KEY","")
ELEVEN = os.getenv("ELEVENLABS_API_KEY","")
HF     = os.getenv("HF_TOKEN","")
DEEP   = os.getenv("DEEPSEEK_API_KEY","")
SB     = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SK     = os.getenv("SUPABASE_SERVICE_KEY","")

def sbh():
    return {"apikey":SK,"Authorization":f"Bearer {SK}","Content-Type":"application/json"}

# ── AGENTES DISPONÍVEIS (gratuitos) ──────────────────────
AGENTES = {
    "groq_llama": {"url":"https://api.groq.com/openai/v1/chat/completions",
                   "key":GROQ,"model":"llama-3.3-70b-versatile","rpm":30},
    "groq_gemma":  {"url":"https://api.groq.com/openai/v1/chat/completions",
                   "key":GROQ,"model":"gemma2-9b-it","rpm":30},
    "groq_mixtral":{"url":"https://api.groq.com/openai/v1/chat/completions",
                   "key":GROQ,"model":"mixtral-8x7b-32768","rpm":30},
    "nvidia_deep": {"url":"https://integrate.api.nvidia.com/v1/chat/completions",
                   "key":NVIDIA,"model":"deepseek-ai/deepseek-r1","rpm":60},
    "gemini_flash":{"url":f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI}",
                   "key":GEMINI,"model":"gemini-2.0-flash","rpm":60},
}

def call_llm(agente_id, prompt, max_tokens=800):
    a = AGENTES.get(agente_id)
    if not a or not a["key"]: return None
    try:
        if "gemini" in agente_id:
            r = requests.post(a["url"], json={"contents":[{"parts":[{"text":prompt}]}]},
                             timeout=45)
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            r = requests.post(a["url"],
                headers={"Authorization":f"Bearer {a['key']}","Content-Type":"application/json"},
                json={"model":a["model"],"messages":[{"role":"user","content":prompt}],
                      "max_tokens":max_tokens},
                timeout=45)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  [{agente_id}] erro: {e}")
    return None

# ── MISSÃO 1: Descobrir novas APIs ───────────────────────
def descobrir_apis_com_ia(categoria):
    prompt = (f"Liste 10 APIs publicas reais e verificaveis na categoria {categoria} "
              "para criacao de conteudo psicologia. "
              "Para cada API: nome, endpoint URL, auth_type (none/apiKey/OAuth), "
              "descricao curta em portugues. "
              "Formato JSON array: [{"name","endpoint","auth_type","descricao"}]. "
              "Apenas JSON, sem explicacao.")
    agente = random.choice(["groq_llama","groq_gemma","nvidia_deep"])
    resultado = call_llm(agente, prompt, 1000)
    if not resultado: return []
    try:
        txt = resultado.strip()
        if "```" in txt: txt = txt.split("```")[1].replace("json","").strip()
        apis = json.loads(txt)
        return apis if isinstance(apis, list) else []
    except: return []

def salvar_apis(apis, categoria):
    if not SK or not apis: return 0
    ok = 0
    for a in apis[:10]:
        r = requests.post(f"{SB}/rest/v1/api_brain",
            headers={**sbh(),"Prefer":"resolution=ignore-duplicates"},
            json={"name":a.get("name","?")[:100],"category":categoria,
                  "subcategory":a.get("name","?")[:50],
                  "endpoint":a.get("endpoint","")[:500],
                  "auth_type":a.get("auth_type","apiKey"),
                  "description":a.get("descricao","")[:300],
                  "relevance":2,"use_case":categoria,"source":"ia-discovery",
                  "tags":[categoria.lower(),"ia-discovered"]},
            timeout=10)
        if r.status_code in (200,201): ok+=1
    return ok

# ── MISSÃO 2: Gerar script psicologia com multi-agente ───
def gerar_script_multiagente(topico):
    prompt = (f"Crie um roteiro de 300 palavras sobre psicologia: {topico}. "
              "Formato: Hook impactante (1 frase) + 4 paragrafos cientificos + "
              "CTA que retorna agencia ao espectador. "
              "Cite 1 pesquisador real. Tom: Daniela Coelho, pesquisadora de comportamento humano brasileira. "
              "Apenas o roteiro, sem explicacao.")
    agentes = ["groq_llama","nvidia_deep","gemini_flash"]
    for ag in agentes:
        resultado = call_llm(ag, prompt, 600)
        if resultado and len(resultado) > 100:
            return {"agente":ag, "topico":topico, "script":resultado}
    return None

def salvar_script(script_data):
    if not SK or not script_data: return
    requests.post(f"{SB}/rest/v1/content_pipeline",
        headers={**sbh(),"Prefer":"return=minimal"},
        json={"titulo":script_data["topico"],"tipo":"script",
              "status":"script_ready","script":script_data["script"],
              "agente_gerador":script_data["agente"],
              "criado_em":datetime.now().isoformat()},
        timeout=10)

# ── MISSÃO 3: Gerar combinacao quântica com contexto ─────
def gerar_combinacao_quantica():
    r = requests.get(f"{SB}/rest/v1/api_brain?select=name,category&limit=50&order=random()",
                    headers=sbh(),timeout=10)
    if r.status_code != 200: return
    apis = r.json()
    random.shuffle(apis)
    combo = random.sample(apis, min(10, len(apis)))
    nomes = [a["name"] for a in combo]
    prompt = (f"Voce e um expert em startups. Estas 10 APIs foram combinadas: "
              f"{', '.join(nomes)}. "
              "Invente 1 produto/sistema UNICO que usa TODAS elas para gerar "
              "renda passiva sem ninguem precisar comprar (AdSense, streaming royalties, "
              "KENP pages, Content ID). "
              "JSON: {"produto","mecanismo","receita_mes_usd","prazo_dias"}")
    resultado = call_llm("groq_llama", prompt, 400)
    if not resultado: return
    try:
        txt = resultado.strip()
        if "```" in txt: txt = txt.split("```")[1].replace("json","").strip()
        data = json.loads(txt)
        import hashlib
        cid = hashlib.md5("|".join(nomes).encode()).hexdigest()[:8]
        requests.post(f"{SB}/rest/v1/quantum_combinations",
            headers={**sbh(),"Prefer":"resolution=ignore-duplicates"},
            json={"combo_id":f"Q_{cid}","n_apis":len(combo),
                  "apis_nomes":nomes,"score":75,
                  "produto":data.get("produto","?"),
                  "mecanismo":data.get("mecanismo","?"),
                  "receita_90d_usd":data.get("receita_mes_usd",0)*3,
                  "case_real":data.get("prazo_dias","?"),
                  "gerado_em":datetime.now().isoformat()},
            timeout=10)
        print(f"  Combo: {data.get('produto','?')[:40]} | ${data.get('receita_mes_usd',0):,}/mes")
    except: pass

# ── MOTOR PRINCIPAL ───────────────────────────────────────
def run():
    print(f"QUANTUM ORCHESTRATOR — {datetime.now():%Y-%m-%d %H:%M}")
    print(f"Agentes ativos: {sum(1 for a in AGENTES.values() if a['key'])}/{len(AGENTES)}")
    print("="*55)

    # 1. Descoberta paralela de APIs (5 categorias ao mesmo tempo)
    cats = ["Neuroscience","Music Streaming","Podcast Distribution",
            "Content Creator Tools","AI Audio Generation"]
    print(f"\n[1/4] Descobrindo APIs em {len(cats)} categorias...")
    total_apis = 0
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(descobrir_apis_com_ia, c): c for c in cats}
        for f in as_completed(futures):
            cat = futures[f]
            apis = f.result()
            if apis:
                ok = salvar_apis(apis, cat)
                total_apis += ok
                print(f"  {cat}: +{ok} APIs")
    print(f"  Total: +{total_apis} novas APIs")

    # 2. Gerar scripts em paralelo (5 topicos)
    topicos = ["Como a solidão cronica afeta o cerebro",
               "Psicologia do perfeccionismo e procrastinacao",
               "Neurociencia do habito: como mudar comportamentos",
               "Apego evitativo: quando aproximar-se parece perigoso",
               "Burnout: o que acontece no sistema nervoso"]
    print(f"\n[2/4] Gerando {len(topicos)} scripts com multi-agente...")
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = [ex.submit(gerar_script_multiagente, t) for t in topicos]
        for f in as_completed(futures):
            s = f.result()
            if s:
                salvar_script(s)
                print(f"  Script: {s['topico'][:40]} [{s['agente']}]")

    # 3. Gerar 10 combinacoes quânticas
    print(f"\n[3/4] Gerando 10 combinacoes quanticas...")
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = [ex.submit(gerar_combinacao_quantica) for _ in range(10)]
        for f in as_completed(futures):
            f.result()

    # 4. Status final
    r = requests.get(f"{SB}/rest/v1/api_brain?select=count",
                    headers={**sbh(),"Prefer":"count=exact"},timeout=5)
    total = r.headers.get("Content-Range","?").split("/")[-1]
    r2 = requests.get(f"{SB}/rest/v1/quantum_combinations?select=count",
                     headers={**sbh(),"Prefer":"count=exact"},timeout=5)
    combos = r2.headers.get("Content-Range","?").split("/")[-1]
    r3 = requests.get(f"{SB}/rest/v1/content_pipeline?select=count&status=eq.script_ready",
                     headers={**sbh(),"Prefer":"count=exact"},timeout=5)
    scripts = r3.headers.get("Content-Range","?").split("/")[-1]

    print(f"\n[4/4] STATUS CEREBRO QUANTICO:")
    print(f"  APIs totais:        {total}")
    print(f"  Combinacoes salvas: {combos}")
    print(f"  Scripts prontos:    {scripts}")
    print(f"\nCerebro funcionando. Proxima rodada: agendada automaticamente.")

if __name__ == "__main__":
    run()
