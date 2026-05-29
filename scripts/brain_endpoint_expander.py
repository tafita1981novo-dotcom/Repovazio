#!/usr/bin/env python3
"""
brain_endpoint_expander.py
ENTRA EM CADA LINK de API ja conhecida e extrai todos os endpoints individualmente.
Uma API com 100 endpoints vira 100 linhas no banco.
Meta: 40.000 endpoints. 2529 APIs × 50 avg = 126.000+
Roda a cada hora, processa 500 APIs por vez = ~25.000 endpoints/hora.
"""
import os, json, requests, time, hashlib, random
from datetime import datetime

SB  = os.getenv("SUPABASE_URL", "https://tpjvalzwkqwttvmszvie.supabase.co")
SK  = os.getenv("SUPABASE_SERVICE_KEY", "")

def sbh():
    return {"apikey":SK,"Authorization":f"Bearer {SK}","Content-Type":"application/json"}

def total():
    r = requests.get(f"{SB}/rest/v1/api_brain?select=count",
                     headers={**sbh(),"Prefer":"count=exact"}, timeout=5)
    return int(r.headers.get("Content-Range","0/0").split("/")[-1])

def inserir_batch(apis):
    if not apis or not SK: return 0
    ok = 0
    for i in range(0, len(apis), 30):
        batch = apis[i:i+30]
        r = requests.post(f"{SB}/rest/v1/api_brain",
            headers={**sbh(),"Prefer":"resolution=ignore-duplicates"},
            json=batch, timeout=30)
        if r.status_code in (200,201,204):
            ok += len(batch)
        time.sleep(0.2)
    return ok

# ── Buscar APIs.guru (link principal: JSON com 2529 specs reais) ──
def buscar_apis_guru_todas():
    """Retorna dict {api_name: swagger_url} de TODAS as 2529 APIs"""
    print("  Buscando lista de APIs do APIs.guru...")
    r = requests.get("https://api.apis.guru/v2/list.json", timeout=45)
    if r.status_code != 200: return {}
    resultado = {}
    for api_name, api_info in r.json().items():
        for ver, vdata in api_info.get("versions",{}).items():
            url = (vdata.get("swaggerUrl","") or
                   vdata.get("swaggerYamlUrl","") or "")
            if url:
                cats = api_info.get("categories",["general"])
                resultado[api_name] = {
                    "url": url,
                    "cat": cats[0] if cats else "general",
                    "cats": cats
                }
            break
    print(f"  APIs.guru: {len(resultado)} APIs com URLs de spec")
    return resultado

# ── Entrar em cada URL e extrair endpoints ──
def expandir_spec(api_name, spec_url, cat, cats, max_endpoints=200):
    """
    Faz GET na URL da spec OpenAPI/Swagger.
    Extrai cada path como uma entrada separada.
    Retorna lista de dicts prontos para inserir.
    """
    try:
        r = requests.get(spec_url, timeout=20)
        if r.status_code != 200: return []
        
        # Suporte a JSON e YAML
        try:
            if spec_url.endswith(".yaml") or spec_url.endswith(".yml"):
                import yaml
                spec = yaml.safe_load(r.text)
            else:
                spec = r.json()
        except:
            return []
        
        paths = spec.get("paths", {})
        info = spec.get("info", {})
        api_title = (info.get("title","") or api_name)[:100]
        api_desc  = (info.get("description","") or "")[:200].replace("\n"," ")
        servers   = spec.get("servers",[])
        base_url  = servers[0].get("url","") if servers else ""
        
        # Coletar componentes/schemas para contexto
        schemas = list(spec.get("components",{}).get("schemas",{}).keys())[:5]
        schema_ctx = ", ".join(schemas) if schemas else ""
        
        apis = []
        for path, path_item in list(paths.items())[:max_endpoints]:
            if not isinstance(path_item, dict): continue
            methods = [m for m in ["get","post","put","delete","patch"] if m in path_item]
            for method in methods[:3]:  # Max 3 métodos por path
                op = path_item[method]
                if not isinstance(op, dict): continue
                op_id    = op.get("operationId","")[:80]
                op_desc  = (op.get("summary","") or op.get("description","") or "")[:200].replace("\n"," ")
                op_tags  = op.get("tags",cats[:2])[:3]
                endpoint = f"{base_url}{path}" if base_url else spec_url.split("/openapi")[0] + path
                
                name = op_id or f"{api_title} {method.upper()} {path.split('/')[-1]}"[:100]
                desc = op_desc or f"{method.upper()} {path} — {api_title}"[:250]
                
                # Tags combinadas
                all_tags = list(set(
                    [t.lower()[:20].replace(" ","-") for t in op_tags] +
                    ["apis-guru", "endpoint", method, cat[:15].replace(" ","-")]
                ))[:8]
                
                apis.append({
                    "name": name[:100],
                    "category": (op_tags[0] if op_tags else cat)[:50],
                    "subcategory": cat[:50],
                    "endpoint": endpoint[:500],
                    "auth_type": "apiKey",
                    "description": desc[:300],
                    "relevance": 2,
                    "use_case": f"{api_title} — {method.upper()} endpoint",
                    "source": "apis-guru",
                    "tags": all_tags
                })
        
        return apis
    except Exception as e:
        return []

# ── MOTOR PRINCIPAL ──────────────────────────────────────────────
def run():
    inicio = datetime.now()
    total_antes = total()
    print(f"BRAIN ENDPOINT EXPANDER — {inicio:%Y-%m-%d %H:%M}")
    print(f"APIs no banco: {total_antes} | Meta: 40.000 | Gap: {max(0,40000-total_antes)}")
    print("="*55)
    
    if total_antes >= 40000:
        print("META JA ATINGIDA!")
        return
    
    # 1. Buscar todas as APIs.guru com URLs de spec
    todas = buscar_apis_guru_todas()
    lista = list(todas.items())
    random.shuffle(lista)  # Randomizar para nao processar sempre as mesmas
    
    # 2. Processar 500 APIs por hora (suficiente para +25K endpoints/hora)
    LIMITE = 500
    inseridas = 0
    processadas = 0
    
    print(f"\nExpandindo endpoints de {min(LIMITE,len(lista))} APIs...")
    for api_name, info in lista[:LIMITE]:
        url = info["url"]
        cat = info["cat"]
        cats = info["cats"]
        
        endpoints = expandir_spec(api_name, url, cat, cats, max_endpoints=100)
        if endpoints:
            ok = inserir_batch(endpoints)
            inseridas += ok
            processadas += 1
            if processadas % 50 == 0:
                total_agora = total()
                print(f"  [{processadas}/{LIMITE}] Total: {total_agora} | +{inseridas} nesta execucao")
                if total_agora >= 40000:
                    print("META ATINGIDA!")
                    break
        time.sleep(0.1)  # Rate limit gentil
    
    # 3. Tambem processar Public-APIs e HuggingFace (fontes ja implementadas)
    # [reutiliza funcoes do brain_mass_ingestor.py]
    
    total_depois = total()
    duracao = (datetime.now() - inicio).seconds
    print(f"\n{'='*55}")
    print(f"RESULTADO: +{total_depois - total_antes} endpoints inseridos")
    print(f"Total agora: {total_depois} | Meta: 40.000")
    print(f"Processadas: {processadas} APIs | Duracao: {duracao}s")
    eta_horas = max(0, 40000 - total_depois) // max(1, total_depois - total_antes)
    print(f"Previsao 40K: {eta_horas} horas")

if __name__ == "__main__":
    run()
