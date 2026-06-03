#!/usr/bin/env python3
"""
Agente: script-writer
Responsabilidade: Gerar scripts completos de vídeo para o canal psicologia.doc
LLM: Groq Llama 3.3 70B (grátis)
Memória: Salva script na swarm_memory para outros agentes usarem
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_base import *

SYSTEM_PROMPT = """Você é Daniela Coelho, pesquisadora de comportamento humano do canal psicologia.doc.
REGRAS ABSOLUTAS:
1. NUNCA use "psicóloga" ou "psicólogo" — use sempre "pesquisadora de comportamento humano"
2. Hook = perigo que parece seguro (NÃO pergunta genérica)
3. Revelação contra-intuitiva no min 1
4. Cite pesquisador real com universidade: Malkin/Harvard, van der Kolk, Ainsworth, Gottman, Siegel/UCLA, Brown/U.Texas, Beck
5. Mecanismo neural específico (amígdala, cortisol, dopamina)
6. Final restaura agência — NÃO vitimiza
7. PROIBIDO: perguntas genéricas, "você já sentiu", "é normal se sentir", sinalizações vagas
8. Cada frase = micro-tensão que puxa a próxima (watch time)
9. Estrutura: Hook (0-30s) → Revelação (1min) → Sinal 1 → Sinal 2 → Sinal 3 → Mecanismo Neural → Pesquisador → Saída com agência
10. ~800-1200 palavras para SHORT (58s) | ~3000-4000 para LONG (15min)"""

def run():
    # Pegar topic do Supabase (pending_generation sem script)
    rows = sb_select("content_pipeline",
        "status=eq.pending_generation&script=is.null&select=id,title,topic,format"
        "&order=id.asc&limit=3")

    if not rows:
        log("Nenhum pending_generation sem script — verificando ready_tts")
        rows = sb_select("content_pipeline",
            "status=eq.ready_tts&script=is.null&select=id,title,topic,format"
            "&order=id.asc&limit=3")

    if not rows:
        log("Sem trabalho para script-writer")
        swarm_report({"status": "idle", "processed": 0})
        return

    swarm_register(f"script-writer: {len(rows)} scripts")
    processed = []

    for row in rows:
        vid_id = row["id"]
        titulo = row["title"]
        topico = row.get("topic") or titulo
        formato = row.get("format") or "short"
        
        log(f"Gerando script #{vid_id}: {titulo[:50]}")

        # Verificar se outro agente já gerou esse script (memória compartilhada)
        cached = memory_get(f"script:{vid_id}")
        if cached:
            log(f"  Cache hit na swarm_memory!")
            script = cached
        else:
            prompt = f"""Escreva um script completo de vídeo psicologia.doc sobre: "{topico}"

Formato: {formato.upper()} {"(~58 segundos = ~800 palavras)" if formato == "short" else "(~15 minutos = ~3500 palavras)"}

Título do episódio: {titulo}

Siga TODAS as regras do SYSTEM_PROMPT. Comece direto com o roteiro, sem introdução ou cabeçalho.
Escreva na primeira pessoa como Daniela."""

            script = llm(prompt, system=SYSTEM_PROMPT, 
                        model=MODEL_DEFAULT if formato == "short" else MODEL_DEEP,
                        max_tokens=1500 if formato == "short" else 5000)
            
            # Salvar na memória compartilhada
            memory_store(f"script:{vid_id}", script, {"vid_id": vid_id, "format": formato})

        # Atualizar no Supabase
        sb_patch("content_pipeline", f"id=eq.{vid_id}", {
            "script": script,
            "status": "ready_tts",
            "model_used": f"groq/{MODEL_DEFAULT}",
            "tokens_used": len(script) // 4,
        })
        log(f"  ✅ Script #{vid_id} gerado ({len(script)} chars) → ready_tts")
        processed.append(vid_id)
        time.sleep(2)  # Rate limit Groq

    swarm_report({"status": "done", "processed": processed, "count": len(processed)})
    log(f"script-writer finalizado: {len(processed)} scripts")

if __name__ == "__main__":
    run()
