#!/usr/bin/env python3
"""
Script Gen Direct V3 — Consulta memoria eterna Supabase em tempo real
Gera scripts virais para os top 10 priorizados
Stack 100% gratis: Groq Llama 3.3 70B
"""
import os, json, urllib.request, urllib.parse, time, sys, re

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, GROQ_KEY]):
    print("ERRO: env vars faltando")
    sys.exit(1)

def supabase_request(method, path, body=None, params=None):
    url = f"{SUPABASE_URL}/rest/v1{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode()
            return json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:300]}")
        return None

def carregar_memoria():
    """Carrega padroes virais + regras eternas em tempo real"""
    padroes = supabase_request("GET", "/padroes_virais",
        params={"select": "chave,conteudo", "ativo": "eq.true"}) or []
    regras = supabase_request("GET", "/regras_eternas",
        params={"select": "codigo,regra,categoria", "prioridade": "eq.10"}) or []
    return {"padroes": padroes, "regras": regras}

def chamar_groq(prompt, max_tokens=3500):
    """Chama Groq Llama 3.3 70B - 100% gratis"""
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps({
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.75
        }).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode())
            return d["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Groq error: {e}")
        return None

def build_prompt(tema, formato, emocao, personagem, memoria):
    is_long = "15" in formato or "long" in formato.lower()
    duracao = "12-15 minutos (1000 palavras)" if is_long else "55-60 segundos (130 palavras max)"
    
    regras_abs = "\n".join([
        f"- {r['codigo']}: {r['regra'][:200]}"
        for r in memoria["regras"][:10]
    ])
    
    estrutura = """
ESTRUTURA 4 ATOS (15 MINUTOS):
ATO 1 (0-3min): SUPER HOOK preview da cena mais intensa + amplificacao com dado + promessa
ATO 2 (3-8min): mecanismo neurologico + CASO REAL completo + MID-VIDEO HOOK em 7-8min
ATO 3 (8-13min): VIRADA principal + framework pratico 3-5 passos + segundo caso real
ATO 4 (13-15min): sintese emocional + identidade coletiva + teaser proximo video

RETENTION HOOKS a cada 90s: 45s, 90s, 150s, 270s, 360s, 480s(MID-HOOK), 600s, 720s, 840s, 900s
""" if is_long else """
ESTRUTURA 7 ATOS (60 SEGUNDOS):
ATO 1 (0-5s) HOOK: cena especifica
ATO 2 (5-15s) AMPLIFICACAO: dado real com fonte
ATO 3 (15-25s) CASO REAL: nome+idade+profissao+situacao
ATO 4 (25-35s) VIRADA CIENTIFICA: mecanismo simples
ATO 5 (35-45s) CUSTO REAL: consequencia sem alarmar
ATO 6 (45-55s) CAMINHO: insight especifico
ATO 7 (55-60s) ANCORAGEM: identificacao coletiva
"""

    return f"""Voce e o cerebro autonomo psicologia.doc — canal brasileiro mirando 1M subscribers ate 2027.
Referencia: Psych2Go (28M views), Therapy in a Nutshell (68% retencao), Kati Morton (71% retencao).

TEMA: {tema}
FORMATO: {formato} | {duracao}
EMOCAO: {emocao}
PERSONAGEM: {personagem}

REGRAS ABSOLUTAS DA MEMORIA ETERNA (NUNCA VIOLAR):
{regras_abs}

ESTRATEGIA DE SUCESSO GLOBAL:
- Audio sempre PT-BR (default eterno)
- Nome BR (Marina/Lucas/Sofia/Rafael/Isabela/Lara) mantido em todos os idiomas
- Situacao UNIVERSAL que ressoa em qualquer cultura
- Dado cientifico com fonte real (universidade + pesquisador + ano)
- Hook = cena especifica + sensacao fisica nos primeiros 5s
- Zero pedido direto de like/inscricao
- Zero julgamento — validar antes de explicar
{estrutura}

GERE EXATAMENTE NESTE FORMATO:
TITULO: titulo viral PT-BR
DESCRICAO_YT: 150 palavras com keywords
TAGS: 15 tags separadas por virgula
SCRIPT:
roteiro completo narrado em pt-BR autentico
CENAS_VISUAIS:
descricao por cena para gerar imagem Flux ZERO TEXTO

GERE AGORA — roteiro completo de producao:"""

def parse_response(texto):
    titulo, descricao, tags, script, cenas = "", "", "", "", ""
    mode = ""
    for line in texto.split("\n"):
        s = line.strip()
        if re.match(r"^T[IÍ]TULO:", s, re.I):
            titulo = re.sub(r"^T[IÍ]TULO:\s*", "", s, flags=re.I).strip()
        elif re.match(r"^DESCRI[CÇ]AO_YT:", s, re.I):
            descricao = re.sub(r"^DESCRI[CÇ]AO_YT:\s*", "", s, flags=re.I).strip()
            mode = "desc"
        elif re.match(r"^TAGS:", s, re.I):
            tags = re.sub(r"^TAGS:\s*", "", s, flags=re.I).strip()
            mode = ""
        elif re.match(r"^SCRIPT:", s, re.I):
            mode = "script"
        elif re.match(r"^CENAS", s, re.I):
            mode = "cenas"
        else:
            if mode == "desc":
                descricao += " " + line.strip()
            elif mode == "script":
                script += line + "\n"
            elif mode == "cenas":
                cenas += line + "\n"
    return {
        "titulo": titulo or "Video psicologia.doc",
        "descricao": descricao.strip(),
        "tags": [t.strip() for t in tags.split(",") if t.strip()][:15],
        "script": script.strip(),
        "cenas": cenas.strip()
    }

def main():
    print("=== Script Gen Direct V3 — Stack 100% Gratis ===\n")
    
    memoria = carregar_memoria()
    print(f"Memoria carregada: {len(memoria['padroes'])} padroes, {len(memoria['regras'])} regras absolutas\n")
    
    # Buscar videos prioritarios (TOP 10)
    videos = supabase_request("GET", "/content_pipeline",
        params={
            "select": "id,title,metadata",
            "status": "eq.pending_generation",
            "metadata->>prioridade_geracao": "not.is.null",
            "order": "(metadata->>prioridade_geracao)::int.asc",
            "limit": "10"
        })
    
    if not videos:
        print("Nenhum video prioritario pendente — pegando fila normal")
        videos = supabase_request("GET", "/content_pipeline",
            params={"select": "id,title,metadata", "status": "eq.pending_generation",
                    "order": "id.asc", "limit": "5"})
    
    if not videos:
        print("Fila vazia.")
        return
    
    print(f"Processando {len(videos)} videos prioritarios:\n")
    
    sucesso = 0
    for v in videos:
        vid = v["id"]
        meta = v.get("metadata", {}) or {}
        tema = meta.get("tema", v["title"])
        emocao = meta.get("emocao", "contemplativo")
        formato = meta.get("formato", "short_60s")
        personagem = meta.get("personagem", "Personagem brasileiro")
        
        print(f"#{vid}: {v['title'][:55]}")
        print(f"     formato={formato} | emocao={emocao}")
        
        prompt = build_prompt(tema, formato, emocao, personagem, memoria)
        resposta = chamar_groq(prompt)
        
        if not resposta:
            print("     ✗ Groq nao respondeu\n")
            continue
        
        parsed = parse_response(resposta)
        if len(parsed["script"]) < 200:
            print(f"     ✗ Script curto: {len(parsed['script'])} chars\n")
            continue
        
        update_data = {
            "title": parsed["titulo"][:200],
            "script": parsed["script"],
            "status": "script_ready",
            "metadata": {
                **meta,
                "descricao_yt": parsed["descricao"],
                "tags_yt": parsed["tags"],
                "cenas_visuais": parsed["cenas"],
                "llm_provider": "groq",
                "llm_modelo": "llama-3.3-70b-versatile",
                "llm_custo": "$0.00",
                "stack_gratuita": True,
                "gerado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "memoria_eterna_aplicada": True,
                "regras_carregadas": len(memoria["regras"]),
                "padroes_carregados": len(memoria["padroes"])
            }
        }
        
        result = supabase_request("PATCH", "/content_pipeline",
            body=update_data, params={"id": f"eq.{vid}"})
        
        if result is not None:
            sucesso += 1
            print(f"     ✓ Script gerado: {len(parsed['script'])} chars, {len(parsed['tags'])} tags")
            print(f"     ✓ Titulo: {parsed['titulo'][:60]}")
        else:
            print(f"     ✗ Falha ao salvar")
        print()
        
        time.sleep(3)  # rate limit Groq
    
    print(f"\n=== TOTAL: {sucesso}/{len(videos)} scripts gerados ===")
    print(f"Custo total: $0.00")

if __name__ == "__main__":
    main()
