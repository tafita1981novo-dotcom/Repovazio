#!/usr/bin/env python3
"""gerar_scripts.py — Gerador de scripts virais via LLM (NVIDIA/Groq)"""
import os, sys, json, requests, time

SBU = os.environ["SUPABASE_URL"]
SBK = os.environ["SUPABASE_KEY"]
NVIDIA_KEY = os.environ.get("NVIDIA_API_KEY","")
GROQ_KEY = os.environ.get("GROQ_API_KEY","")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY","")

hdrs = {"Authorization": f"Bearer {SBK}", "apikey": SBK}

TOPICOS_VIRAIS = [
    "Síndrome do Impostor: Por Que Pessoas Competentes Sentem que São Uma Fraude",
    "Apego Evitativo: Os Sinais Que Você Está Se Afastando de Quem Ama",
    "Manipulação Emocional: 5 Táticas Sutis Que Pessoas Tóxicas Usam",
    "Trauma de Rejeição: Por Que Você Tem Medo de Ser Abandonado",
    "Narcisismo Oculto: A Diferença Entre Autoestima e Narcisismo",
    "Colapso Emocional: Quando o Corpo Diz BASTA Antes da Mente",
    "Pessoas Pleasers: O Perigo de Priorizar Todos Menos Você Mesmo",
    "Dissociação: Por Que Você Se Sente Desconectado de Si Mesmo",
    "Vício em Drama: Por Que Algumas Pessoas Criam Crises Constantemente",
    "Parentificação: Quando a Criança Vira o Adulto da Família",
]

def gerar_via_llm(topico):
    prompt = f"""Crie um roteiro de vídeo YouTube estilo Psych2Go em português brasileiro sobre:
"{topico}"

Formato obrigatório JSON:
{{
  "youtube_title": "título viral com número ou pergunta (máx 80 chars)",
  "youtube_description": "descrição SEO 200 palavras com #hashtags",
  "script": "roteiro completo de 800 palavras, 5 seções com hook forte na abertura"
}}

Regras: sem jargão técnico, linguagem acessível, tom empático, fatos reais.
Responda APENAS com o JSON, sem markdown."""

    # Tentar NVIDIA primeiro
    if NVIDIA_KEY:
        for model in ["nvidia/llama-3.3-nemotron-70b-instruct", "meta/llama-3.3-70b-instruct"]:
            try:
                r = requests.post("https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"},
                    json={"model": model, "messages": [{"role": "user", "content": prompt}],
                          "max_tokens": 2000, "temperature": 0.7},
                    timeout=90)
                if r.ok:
                    txt = r.json()["choices"][0]["message"]["content"].strip()
                    if txt.startswith("```"): txt = txt.split("```")[1].lstrip("json").strip()
                    return json.loads(txt), model
            except Exception as e:
                print(f"NVIDIA {model}: {e}")

    # Groq fallback
    if GROQ_KEY:
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile",
                      "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 2000, "temperature": 0.7},
                timeout=60)
            if r.ok:
                txt = r.json()["choices"][0]["message"]["content"].strip()
                if txt.startswith("```"): txt = txt.split("```")[1].lstrip("json").strip()
                return json.loads(txt), "groq/llama-3.3-70b"
        except Exception as e:
            print(f"Groq: {e}")

    return None, None

def salvar_no_supabase(topico, dados, model):
    payload = {
        "title": topico,
        "youtube_title": dados.get("youtube_title", topico[:100]),
        "youtube_description": dados.get("youtube_description", ""),
        "script": dados.get("script", ""),
        "status": "script_ready",
        "target_platform": "youtube_long",
        "llm_model": model,
        "seo_score": 75
    }
    r = requests.post(f"{SBU}/rest/v1/content_pipeline",
        headers={**hdrs, "Content-Type": "application/json", "Prefer": "return=minimal"},
        json=payload, timeout=15)
    return r.status_code

# Verificar quantos pending_generation temos
total = requests.get(
    f"{SBU}/rest/v1/content_pipeline?status=eq.pending_generation&select=id&limit=1",
    headers=hdrs, timeout=15)
count = len(total.json())
print(f"Scripts pending_generation: {count}")

# Gerar 3 scripts novos por execução
gerados = 0
for topico in TOPICOS_VIRAIS[:3]:
    # Verificar se já existe
    existe = requests.get(
        f"{SBU}/rest/v1/content_pipeline?title=eq.{requests.utils.quote(topico)}&select=id",
        headers=hdrs, timeout=10)
    if existe.json():
        print(f"Pulando (existe): {topico[:40]}")
        continue
    
    print(f"Gerando: {topico[:60]}")
    dados, model = gerar_via_llm(topico)
    
    if dados:
        status = salvar_no_supabase(topico, dados, model)
        print(f"  Salvo HTTP {status} via {model}")
        gerados += 1
    else:
        # Salvar apenas título para geração posterior
        r = requests.post(f"{SBU}/rest/v1/content_pipeline",
            headers={**hdrs, "Content-Type": "application/json", "Prefer": "return=minimal"},
            json={"title": topico, "status": "pending_generation",
                  "target_platform": "youtube_long"},
            timeout=15)
        print(f"  Enfileirado ({r.status_code})")
    
    time.sleep(2)

print(f"\nGerados: {gerados}")
