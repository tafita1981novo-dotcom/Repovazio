#!/usr/bin/env python3
"""
analytics_agent.py — Analisa stats reais do YouTube + atualiza cerebro_knowledge
LLM: Groq DeepSeek R1 (raciocínio, grátis)
Input: YouTube Data API v3 (stats reais) + content_pipeline publicados
Output: → cerebro_knowledge (memória atualizada com novos padrões)
Cron: 8h00 UTC diário
"""
import sys, os, json, time
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_base import *

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
CHANNEL_ID      = "UCSH63tBfY6wEIdkC4u4zKdg"
WEEK_ID         = datetime.now(timezone.utc).strftime("%Y-W%V")

SYSTEM = """Você é o analista de performance do canal psicologia.doc.
Sua função: identificar padrões reais de sucesso e fracasso nos vídeos publicados,
e extrair insights acionáveis para o time de produção.
Foque em: o que faz um vídeo passar de 1k para 10k views? Quais formatos, temas,
horários e títulos geram mais watch time? Seja específico e baseado em dados."""

def yt_stats(video_ids: list) -> dict:
    """Busca stats reais via YouTube Data API v3."""
    if not YOUTUBE_API_KEY or not video_ids:
        return {}
    ids_str = ",".join(video_ids[:50])
    url = (f"https://www.googleapis.com/youtube/v3/videos"
           f"?part=statistics,snippet&id={ids_str}&key={YOUTUBE_API_KEY}")
    s, r = _http(url)
    if s != 200:
        log(f"YouTube API error {s}: {r}")
        return {}
    stats = {}
    for item in r.get("items", []):
        vid_id = item["id"]
        st = item.get("statistics", {})
        sn = item.get("snippet", {})
        stats[vid_id] = {
            "title":           sn.get("title", ""),
            "published":       sn.get("publishedAt", ""),
            "views":           int(st.get("viewCount", 0)),
            "likes":           int(st.get("likeCount", 0)),
            "comments":        int(st.get("commentCount", 0)),
            "like_ratio":      round(int(st.get("likeCount",0)) / max(int(st.get("viewCount",1)),1) * 100, 2),
        }
    return stats

def run():
    log(f"=== ANALYTICS AGENT | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC ===")
    swarm_register("analytics-agent")

    # 1. Pegar vídeos publicados dos últimos 30 dias
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    published = sb_select("content_pipeline",
        f"status=eq.published&published_at=gte.{cutoff}"
        "&select=id,title,youtube_id,youtube_long_id,format,viral_score,quality_score_current,published_at,target_platform"
        "&order=published_at.desc&limit=50")

    log(f"Vídeos publicados (30d): {len(published)}")

    if not published:
        log("Sem vídeos para analisar")
        swarm_report({"status": "no_data"})
        return

    # 2. Coletar YouTube IDs para buscar stats reais
    yt_ids = []
    for v in published:
        vid = v.get("youtube_id") or v.get("youtube_long_id")
        if vid and vid not in yt_ids:
            yt_ids.append(vid)

    log(f"Buscando stats de {len(yt_ids)} vídeos via YouTube API...")
    real_stats = yt_stats(yt_ids) if yt_ids else {}
    log(f"Stats recebidas: {len(real_stats)} vídeos")

    # 3. Montar contexto de análise
    video_data = []
    for v in published:
        vid_id = v.get("youtube_id") or v.get("youtube_long_id", "")
        yt = real_stats.get(vid_id, {})
        video_data.append({
            "title":   v.get("title", "")[:60],
            "format":  v.get("format", "?"),
            "platform": v.get("target_platform","?"),
            "score_viral":   v.get("viral_score", 0),
            "score_quality": v.get("quality_score_current", 0),
            "views":   yt.get("views", "N/A"),
            "likes":   yt.get("likes", "N/A"),
            "like_pct": yt.get("like_ratio", "N/A"),
        })

    # Top e bottom performers
    with_views = [v for v in video_data if isinstance(v["views"], int)]
    with_views.sort(key=lambda x: x["views"], reverse=True)
    top5     = with_views[:5]
    bottom5  = with_views[-5:] if len(with_views) >= 5 else with_views

    top_ctx = "\n".join([f"  +{v['views']}views | {v['title']} | {v['format']} | score={v['score_viral']}"
                          for v in top5])
    bot_ctx = "\n".join([f"  -{v['views']}views | {v['title']} | {v['format']} | score={v['score_viral']}"
                          for v in bottom5])

    # 4. Pegar cerebro_knowledge existente
    cerebro = sb_select("cerebro_knowledge",
        "select=id,insight,category,confidence,created_at&order=confidence.desc&limit=20")
    cerebro_ctx = "\n".join([f"  [{c.get('category','')}|{c.get('confidence',0):.0f}%] {c.get('insight','')[:100]}"
                              for c in cerebro]) if cerebro else "Sem dados"

    prompt = f"""Analise a performance dos últimos 30 dias do canal psicologia.doc.

=== TOP 5 VÍDEOS (mais views) ===
{top_ctx if top_ctx else "Sem dados de views (API não configurada)"}

=== BOTTOM 5 VÍDEOS (menos views) ===
{bot_ctx if bot_ctx else "Sem dados"}

=== CEREBRO_KNOWLEDGE ATUAL ===
{cerebro_ctx}

=== TOTAL ===
{len(published)} vídeos publicados | {len(with_views)} com dados reais de views

Extraia de 3 a 7 novos insights acionáveis baseados nestes dados.
Foque em padrões que o cérebro autônomo ainda NÃO conhece ou pode atualizar.

Responda em JSON válido (sem markdown):
{{
  "insights": [
    {{
      "category": "title|format|topic|timing|thumbnail|engagement|algorithm",
      "insight": "aprendizado específico e acionável (max 150 chars)",
      "confidence": 75,
      "evidence": "o que nos dados justifica isso",
      "action": "o que mudar na próxima semana"
    }}
  ],
  "weekly_summary": "resumo executivo da semana em 2-3 frases"
}}"""

    log("Analisando com DeepSeek R1...")
    raw = llm(prompt, system=SYSTEM, model=MODEL_DEEP, max_tokens=2000)

    try:
        start = raw.find("{"); end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])
        insights = data.get("insights", [])
        summary  = data.get("weekly_summary", "")
    except Exception as e:
        log(f"JSON parse error: {e}")
        swarm_report({"status": "parse_error"})
        return

    log(f"{len(insights)} novos insights extraídos")

    # 5. Salvar em cerebro_knowledge (upsert por insight único)
    saved = 0
    for ins in insights:
        if not ins.get("insight"): continue
        row = {
            "insight":    ins["insight"][:200],
            "category":   ins.get("category", "general"),
            "confidence": float(ins.get("confidence", 70)),
            "evidence":   ins.get("evidence", ""),
            "action":     ins.get("action", ""),
            "source":     f"analytics-agent-{WEEK_ID}",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        # Tentar upsert por insight
        s, r = _http(f"{SBU}/rest/v1/cerebro_knowledge",
                     method="POST", body=row,
                     headers={**H_SB, "Prefer": "resolution=merge-duplicates"})
        if s in (200, 201):
            saved += 1
            log(f"  ✅ [{ins.get('category','')}|{ins.get('confidence',0):.0f}%] {ins['insight'][:60]}")
        else:
            log(f"  ⚠ {s}: {str(r)[:60]}")

    # 6. Guardar sumário na swarm memory
    memory_store(f"analytics:weekly:{WEEK_ID}", json.dumps({
        "summary":       summary,
        "insights_added": saved,
        "videos_analyzed": len(published),
        "with_real_data":  len(with_views),
    }))

    log(f"\n📊 RESUMO SEMANAL: {summary}")
    swarm_report({
        "status": "done", "week_id": WEEK_ID,
        "insights_saved": saved, "videos_analyzed": len(published),
        "real_stats": len(with_views)
    })
    log(f"✅ Analytics concluído: {saved} insights → cerebro_knowledge")

if __name__ == "__main__":
    run()
