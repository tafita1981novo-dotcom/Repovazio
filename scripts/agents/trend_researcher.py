#!/usr/bin/env python3
"""
Agente: trend-researcher
Responsabilidade: Pesquisar tendências psicologia PT-BR e enfileirar novos tópicos
LLM: Groq DeepSeek R1 (raciocínio, grátis)
Output: Insere novos registros em content_pipeline com status=pending_generation
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_base import *

TREND_SYSTEM = """Você é pesquisador de tendências de psicologia e comportamento humano para YouTube PT-BR.
Foco: tópicos que geram alto watch time e engajamento em 2025-2026.
Áreas quentes: trauma de apego, narcisismo encoberto, ansiedade de alta performance, 
regulação emocional, neurociência do comportamento, relacionamentos tóxicos, 
síndrome do impostor, automutilação emocional, autossabotagem.
NUNCA sugira temas que precisem de "psicóloga" — use "pesquisadora de comportamento"."""

def run():
    swarm_register("trend-researcher")

    # Ver quantos pending_generation temos
    rows = sb_select("content_pipeline", "status=eq.pending_generation&select=id&limit=1")
    pending_count = len(sb_select("content_pipeline", "status=in.(pending_generation,pending)&select=id"))
    
    log(f"pending_generation atual: {pending_count}")
    
    # Só gerar novos tópicos se estiver abaixo de 30
    if pending_count >= 30:
        log("Pipeline cheio — sem necessidade de novos tópicos agora")
        swarm_report({"status": "idle", "pending": pending_count})
        return

    # Verificar se já pesquisamos recentemente (evitar duplicatas)
    recent = memory_get("trend-research:latest")
    
    needed = max(0, 30 - pending_count)
    log(f"Gerando {needed} novos tópicos")

    prompt = f"""Gere {needed} ideias de vídeo ORIGINAIS e VIRAIS para o canal psicologia.doc (PT-BR).

Cada ideia deve ter:
- Gancho específico (situação real, não abstrata)  
- Revelação contra-intuitiva
- Pesquisador real que pode ser citado
- Alta busca no YouTube Brasil

Responda SOMENTE em JSON:
{{
  "topics": [
    {{
      "title": "título do vídeo (gancho forte)",
      "topic": "descrição do tema central (1 frase)",
      "researcher": "Nome/Instituição do pesquisador a citar",
      "hook": "primeira frase do vídeo (a que prende em 3s)",
      "format": "short"
    }}
  ]
}}

Temas recentes que já temos (NÃO repetir): trauma apego, narcisismo, perfeccionismo, 
depressão silenciosa, ansiedade, gaslighting, síndrome impostor"""

    raw = llm(prompt, system=TREND_SYSTEM, model=MODEL_DEEP, max_tokens=3000)
    
    try:
        start, end = raw.find("{"), raw.rfind("}") + 1
        data = json.loads(raw[start:end])
        topics = data.get("topics", [])
    except:
        log("JSON parse error na pesquisa de tendências")
        swarm_report({"status": "error"})
        return

    # Inserir novos tópicos no pipeline
    inserted = []
    for t in topics:
        title = t.get("title", "")
        if not title: continue
        
        # Checar se já existe
        existing = sb_select("content_pipeline", f"title=eq.{urllib.parse.quote(title)}&select=id")
        if existing: continue
        
        row = {
            "title": title,
            "topic": t.get("topic", title),
            "status": "pending_generation",
            "format": t.get("format", "short"),
            "metadata": {
                "researcher": t.get("researcher", ""),
                "hook": t.get("hook", ""),
                "source": f"swarm-trend-{SWARM_ID}",
            }
        }
        s, r = _http(f"{SBU}/rest/v1/content_pipeline", method="POST", body=row, headers=H_SB)
        if s in (200, 201):
            inserted.append(title[:50])
            log(f"  ✅ Novo tópico: {title[:60]}")
        time.sleep(0.5)

    memory_store("trend-research:latest", json.dumps(inserted[:5]))
    swarm_report({"status": "done", "inserted": len(inserted), "topics": inserted})
    log(f"trend-researcher: {len(inserted)} novos tópicos adicionados")

if __name__ == "__main__":
    run()
