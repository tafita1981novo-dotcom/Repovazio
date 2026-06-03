#!/usr/bin/env python3
"""
Agente: seo-optimizer
Responsabilidade: Gerar youtube_title SEO + description + tags otimizados
Processa vídeos mp4_ready/pending_credentials sem título otimizado.
LLM: Groq Llama 3.1 8B (rápido, grátis)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_base import *

SEO_SYSTEM = """Você é especialista em SEO para YouTube no nicho de psicologia/comportamento humano (PT-BR).
REGRAS DO TÍTULO:
- 60-70 caracteres ideais
- Começa com situação específica ou número (ex: "Você checa o celular 80x ao dia?" / "5 Sinais Que")
- Inclui emoção + curiosidade
- NÃO "psicóloga" — use "pesquisadora" se necessário
- Exemplos BONS: "Dormia 2 Horas e Entregava Tudo. Isso Tem Nome", "O Narcisista Não Grita. Ele Chora"
- Exemplos RUINS: "Aprenda sobre X", "Como fazer Y", "Dicas de Z"

REGRAS DA DESCRIÇÃO:
- 150-200 palavras
- Primeiras 2 linhas = hook (aparecem no preview)
- Inclui palavras-chave naturalmente
- CTA para assinar
- Hashtags ao final: #psicologia #comportamentohumano #saúdeemental + 3 específicas do tema

REGRAS DAS TAGS: 8-12 tags, mix de broad + específicas"""

def run():
    # Pegar vídeos com título genérico (igual ao title ou muito curto)  
    rows = sb_select("content_pipeline",
        "status=in.(mp4_ready,pending_credentials,audio_ready)"
        "&select=id,title,topic,script,youtube_title"
        "&order=id.asc&limit=20")
    
    # Filtrar os que têm título genérico (= title ou < 30 chars)
    to_optimize = [r for r in rows if
        not r.get("youtube_title") or 
        r.get("youtube_title") == r.get("title") or
        len(r.get("youtube_title","")) < 30]

    if not to_optimize:
        log("Sem vídeos para otimizar SEO")
        swarm_report({"status": "idle", "optimized": 0})
        return

    swarm_register(f"seo-optimizer: {len(to_optimize)} vídeos")
    optimized = []

    for row in to_optimize[:10]:  # max 10 por run
        vid_id = row["id"]
        titulo = row["title"]
        script_preview = (row.get("script") or "")[:300]
        
        log(f"SEO #{vid_id}: {titulo[:50]}")
        
        # Cache check
        cached = memory_get(f"seo:{vid_id}")
        if cached:
            seo = json.loads(cached)
        else:
            prompt = f"""Crie SEO otimizado para este vídeo psicologia.doc:

Título atual: {titulo}
Tema: {row.get('topic') or titulo}
Preview do script: {script_preview}

Responda APENAS em JSON válido com estas chaves:
{{
  "youtube_title": "título otimizado (60-70 chars)",
  "youtube_description": "descrição completa (150-200 palavras)",
  "youtube_tags": ["tag1", "tag2", ..., "tag12"],
  "pinned_comment": "comentário fixado com CTA (2-3 linhas)"
}}"""
            
            raw = llm(prompt, system=SEO_SYSTEM, model=MODEL_FAST, max_tokens=800)
            
            # Parse JSON
            try:
                start = raw.find("{")
                end = raw.rfind("}") + 1
                seo = json.loads(raw[start:end])
            except:
                log(f"  JSON parse error, usando title original")
                continue
            
            memory_store(f"seo:{vid_id}", json.dumps(seo), {"vid_id": vid_id})

        sb_patch("content_pipeline", f"id=eq.{vid_id}", {
            "youtube_title": seo.get("youtube_title", titulo)[:100],
            "youtube_description": seo.get("youtube_description", ""),
            "youtube_tags": seo.get("youtube_tags", [])[:12],
            "pinned_comment": seo.get("pinned_comment", ""),
        })
        log(f"  ✅ SEO #{vid_id}: '{seo.get('youtube_title','')[:50]}'")
        optimized.append(vid_id)
        time.sleep(1)

    swarm_report({"status": "done", "optimized": optimized})
    log(f"seo-optimizer: {len(optimized)} vídeos otimizados")

if __name__ == "__main__":
    run()
