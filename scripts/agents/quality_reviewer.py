#!/usr/bin/env python3
"""
Agente: quality-reviewer
Responsabilidade: Revisar scripts contra QUALITY_STANDARD.md e aprovar/rejeitar
Scripts reprovados voltam para pending_generation com feedback.
LLM: Groq Llama 3.3 70B
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_base import *

REVIEW_SYSTEM = """Você é revisor de qualidade do canal psicologia.doc.
Critérios para APROVAÇÃO (todos obrigatórios):
✅ Palavra "psicóloga/psicólogo" AUSENTE
✅ Hook = perigo que parece seguro (NÃO pergunta genérica)
✅ Revelação contra-intuitiva presente no início
✅ Pesquisador real citado com universidade
✅ Mecanismo neural específico (amígdala/cortisol/dopamina)
✅ Final restaura agência (NÃO vitimiza)
✅ Nenhuma frase começa com "Você já sentiu", "É normal se sentir", "Todo mundo"

Critérios para REJEIÇÃO (qualquer um reprovado):
❌ Usa "psicóloga" ou "psicólogo"
❌ Hook é pergunta genérica
❌ Sem pesquisador real ou pesquisador vago ("estudos mostram")
❌ Vitimiza o espectador
❌ Conclusão não restaura agência"""

def run():
    swarm_register("quality-reviewer")
    
    # Pegar scripts ready_tts que ainda não foram revisados
    rows = sb_select("content_pipeline",
        "status=eq.ready_tts&select=id,title,script"
        "&order=id.asc&limit=5")
    
    # Filtrar apenas os que têm script E não foram revisados
    to_review = [r for r in rows if r.get("script") and len(r.get("script","")) > 200]
    
    if not to_review:
        log("Sem scripts para revisar")
        swarm_report({"status": "idle"})
        return

    approved, rejected = [], []
    
    for row in to_review:
        vid_id = row["id"]
        script = row.get("script","")
        log(f"Revisando #{vid_id}: {row['title'][:50]}")
        
        prompt = f"""Revise este script do canal psicologia.doc:

TÍTULO: {row['title']}

SCRIPT (primeiros 600 chars):
{script[:600]}

Responda APENAS em JSON:
{{
  "aprovado": true/false,
  "score": 0-100,
  "problemas": ["lista de problemas encontrados"] ou [],
  "sugestao_hook": "sugestão de hook melhor se aprovado=false" ou null,
  "feedback_resumido": "1 linha de feedback"
}}"""

        raw = llm(prompt, system=REVIEW_SYSTEM, model=MODEL_DEFAULT, max_tokens=400)
        
        try:
            start, end = raw.find("{"), raw.rfind("}") + 1
            review = json.loads(raw[start:end])
        except:
            log(f"  JSON error, pulando #{vid_id}")
            continue
        
        score = review.get("score", 50)
        aprovado = review.get("aprovado", score >= 70)
        
        # Salvar review na memória
        memory_store(f"review:{vid_id}", json.dumps(review), {"vid_id": vid_id, "score": score})
        
        if aprovado:
            # Manter status ready_tts (já aprovado)
            sb_patch("content_pipeline", f"id=eq.{vid_id}", {
                "metadata": {"quality_review": review, "quality_approved": True},
                "score": score
            })
            approved.append(vid_id)
            log(f"  ✅ APROVADO #{vid_id} (score={score}): {review.get('feedback_resumido','')}")
        else:
            # Voltar para pending_generation com feedback
            sb_patch("content_pipeline", f"id=eq.{vid_id}", {
                "status": "pending_generation",
                "script": None,  # Limpar script para regenerar
                "error": f"QUALITY_REJECTED: {'; '.join(review.get('problemas',[])[:2])}",
                "metadata": {"quality_review": review, "quality_approved": False}
            })
            rejected.append(vid_id)
            log(f"  ❌ REPROVADO #{vid_id}: {'; '.join(review.get('problemas',[])[:2])}")
        
        time.sleep(1)

    swarm_report({"status": "done", "approved": approved, "rejected": rejected})
    log(f"quality-reviewer: {len(approved)} aprovados, {len(rejected)} reprovados")

if __name__ == "__main__":
    run()
