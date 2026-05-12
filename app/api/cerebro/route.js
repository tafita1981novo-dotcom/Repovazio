import { createClient } from "@supabase/supabase-js";
export const dynamic = "force-dynamic";
export const revalidate = 0;

const VERSAO = "v14";
const REGRAS = {
  long_target_minutos: 15,
  long_range: "14-16 min",
  short_target_segundos: 54,
  short_range: "50-58s",
  render_exclusivo: "Flux.1 Schnell NVIDIA + Ken Burns 30fps H.264 1080p AAC 192kbps",
  gate_score_render: 90,
  gate_score_publicar: 92,
  imagens: "ZERO texto ZERO marcas personagem BR 2D flat vector Psych2Go",
  series_ativas: ["Apego Ansioso","Mentes Narcisistas","Trauma Invisivel","Ansiedade e Panico","Burnout"],
  publicar_apenas: "mp4_url com /v2/ (Flux+KB)",
  identidade: "Psicologia (NUNCA psicologa ate jan/2027)",
  decisao_data: "2026-05-12",
  autonomia: "TOTAL",
};

export async function GET(request) {
  try {
    const sbUrl = process.env.SUPABASE_URL || "https://tpjvalzwkqwttvmszvie.supabase.co";
    const sbKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
    const sb = createClient(sbUrl, sbKey);
    const url = new URL(request.url);
    const action = url.searchParams.get("action") || "status";

    if (action === "regras") return Response.json({ regras: REGRAS, versao: VERSAO });

    const { data: pipe } = await sb.from("content_pipeline").select("status,mp4_url,score,metadata");
    const stats = { total:0, quantum:0, v8_bloqueado:0, em_render:0, publicados:0 };
    const por_status = {};
    (pipe||[]).forEach(v => {
      stats.total++;
      por_status[v.status] = (por_status[v.status]||0)+1;
      if ((v.mp4_url||"").includes("/v2/")) stats.quantum++;
      if ((v.mp4_url||"").includes("_v8.mp4")) stats.v8_bloqueado++;
      if (v.status === "mp4_ready") stats.em_render++;
      if (v.status === "published") stats.publicados++;
    });

    const { data: tarefas } = await sb.from("cerebro_tarefas")
      .select("tipo,prioridade").eq("status","pendente").order("prioridade",{ascending:false}).limit(7);

    const { data: evolucoes } = await sb.from("cerebro_evolucao")
      .select("versao,tipo,descricao,criado_em").order("criado_em",{ascending:false}).limit(3);

    return Response.json({
      cerebro: { versao:VERSAO, status:"ATIVO — AUTONOMIA TOTAL", ultima_decisao:"2026-05-12: Padrao Quantico + Long=15min + Short=50-58s" },
      regras_imutaveis: REGRAS,
      pipeline: { stats, por_status },
      auto_melhoria: {
        tarefas_pendentes: (tarefas||[]).length,
        proximas: (tarefas||[]).map(t=>t.tipo),
        evolucoes: (evolucoes||[]).map(e=>({versao:e.versao,tipo:e.tipo,descricao:(e.descricao||"").substring(0,80)})),
      },
      links: {
        qg: "https://repovazio.vercel.app/qg.html",
        galeria: "https://repovazio.vercel.app/galeria-quantica.html",
        dashboard: "https://repovazio.vercel.app/dashboard",
        social: "https://repovazio.vercel.app/api/social",
      }
    });
  } catch(e) {
    return Response.json({ cerebro:{ versao:VERSAO, status:"ATIVO" }, regras_imutaveis:REGRAS, error:e.message });
  }
}
