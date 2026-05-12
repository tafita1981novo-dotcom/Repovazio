import { createClient } from "@supabase/supabase-js";
export const dynamic = "force-dynamic";
export const revalidate = 0;

// ================================================================
// CEREBRO V14 — API de Status e Controle
// Memória Eterna | Auto-melhoria | Padrão Quântico Obrigatório
// Long=15min | Short=50-58s | APENAS Flux+KB V2
// ================================================================

const VERSAO = "v14";
const REGRAS_IMUTAVEIS = {
  long_target_minutos: 15,
  long_range_min: 14,
  long_range_max: 16,
  short_target_segundos: 54,
  short_range: "50-58s",
  render_exclusivo: "Flux.1 Schnell NVIDIA + Ken Burns 30fps H.264 1080p AAC 192kbps",
  gate_score_render: 90,
  gate_score_publicar: 92,
  imagens: "ZERO texto ZERO marcas personagem BR 2D flat vector",
  personagens: "8 personagens brasileiros diversos (etnias/gênero/idade)",
  series_ativas: [
    "Apego Ansioso — A Ciência do Medo de Perder",
    "Mentes Narcisistas — O Que Está Por Trás da Manipulação",
    "Trauma Invisível — O Que Ninguém Te Contou Sobre o Passado",
    "Ansiedade e Pânico — A Ciência Por Trás do Medo",
    "Burnout — Por Que Você Está Esgotado e Não Sabe Por Quê",
  ],
  publicar_apenas: "vídeos com mp4_url contendo /v2/ (Flux+KB)",
  decisao_data: "2026-05-12",
  autonomia: "TOTAL — cérebro toma decisões sozinho",
};

export async function GET(request) {
  const sbUrl = process.env.SUPABASE_URL || "https://tpjvalzwkqwttvmszvie.supabase.co";
  const sbKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
  const sb = createClient(sbUrl, sbKey);
  const url = new URL(request.url);
  const action = url.searchParams.get("action") || "status";

  try {
    if (action === "regras") {
      return Response.json({ regras: REGRAS_IMUTAVEIS, versao: VERSAO });
    }

    // Status completo do pipeline
    const { data: pipe } = await sb.from("content_pipeline").select("status,mp4_url,score,metadata");
    
    const stats = { total: 0, quantum_prontos: 0, v8_bloqueados: 0, score_95: 0, em_render: 0 };
    const por_status = {};
    
    (pipe||[]).forEach(v => {
      stats.total++;
      por_status[v.status] = (por_status[v.status]||0) + 1;
      if (v.mp4_url?.includes("/v2/")) stats.quantum_prontos++;
      if (v.mp4_url?.includes("_v8.mp4")) stats.v8_bloqueados++;
      if (v.status === "mp4_ready") stats.em_render++;
      const s = parseFloat(v.metadata?.gate_score || v.score || 0);
      if (s >= 95) stats.score_95++;
    });

    const { data: evolucoes } = await sb.from("cerebro_evolucao")
      .select("versao,tipo,descricao,criado_em").order("criado_em",{ascending:false}).limit(5);
    
    const { data: tarefas } = await sb.from("cerebro_tarefas")
      .select("tipo,prioridade,status").eq("status","pendente").order("prioridade",{ascending:false}).limit(5);

    const { data: memorias } = await sb.from("cerebro_memoria")
      .select("topic,score,ultimo_ciclo").order("score",{ascending:false}).limit(5);

    return Response.json({
      cerebro: {
        versao: VERSAO,
        status: "ATIVO — AUTONOMIA TOTAL",
        decisoes_autonomas: true,
        ultima_decisao: "2026-05-12: Padrão Quântico Obrigatório + Long=15min + Short=50-58s",
      },
      regras_imutaveis: REGRAS_IMUTAVEIS,
      pipeline: {
        stats,
        por_status,
        nota: "APENAS vídeos /v2/ (Flux+KB) são publicados",
        proibido: "mp4_url _v8.mp4 — bloqueado permanentemente",
      },
      auto_melhoria: {
        tarefas_pendentes: (tarefas||[]).length,
        proximas: (tarefas||[]).map(t=>t.tipo),
        evolucoes_recentes: (evolucoes||[]).slice(0,3).map(e=>({
          versao:e.versao, tipo:e.tipo, descricao:e.descricao?.substring(0,80)
        })),
      },
      memoria_eterna: {
        total_memorias: (memorias||[]).length,
        top: (memorias||[]).map(m=>m.topic),
      },
      links: {
        galeria_quantica: "https://repovazio.vercel.app/galeria-quantica.html",
        dashboard: "https://repovazio.vercel.app/dashboard",
        hub: "https://repovazio.vercel.app/hub.html",
        social_manager: "https://repovazio.vercel.app/api/social",
      }
    });

  } catch(e) {
    return Response.json({ error: e.message }, { status: 500 });
  }
}
