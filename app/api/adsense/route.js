import { createClient } from "@supabase/supabase-js";
export const dynamic = "force-dynamic";
export const revalidate = 0;

// ================================================================
// ADSENSE CALCULATOR — psicologia.doc
// Meta: R$50.000/mês EXCLUSIVAMENTE de YouTube AdSense
// Baseado em: Psych2Go 12M | Dr. Ramani 2M | Kati Morton 1M
// ================================================================

// MATEMÁTICA REAL 2026
const CALC = {
  rpm_min: 22,    // R$/1000 views — conservador
  rpm_medio: 28,  // R$/1000 views — realista
  rpm_max: 45,    // R$/1000 views — otimista (meses Q4)
  meta_reais: 50000,
};

// Views necessárias para R$50K/mês
const views_conservador = Math.ceil(CALC.meta_reais / CALC.rpm_min * 1000);  // 2.27M
const views_realista    = Math.ceil(CALC.meta_reais / CALC.rpm_medio * 1000); // 1.79M
const views_otimista    = Math.ceil(CALC.meta_reais / CALC.rpm_max * 1000);   // 1.11M

// Receita por tipo de vídeo
const RECEITA_VIDEO = {
  long_15min: {
    anuncios: "pre-roll + 2 mid-roll + end screen",
    rpm_efetivo: 32,
    "10k_views": 320,
    "100k_views": 3200,
    "1M_views": 32000,
  },
  short_54s: {
    anuncios: "pool compartilhado de Shorts",
    rpm_efetivo: 5,
    "10k_views": 50,
    "100k_views": 500,
    "nota": "Shorts = crescimento, NÃO AdSense. RPM 6x menor que Long Form"
  }
};

// Trajetória de crescimento
const TRAJETORIA = [
  { fase: "Mês 1-3",   videos: 40,  views_mes: "10K-50K",    adsense_mes: "R$220-1.100",    nota: "Construindo base — sem monetização ainda" },
  { fase: "Mês 4-6",   videos: 80,  views_mes: "50K-300K",   adsense_mes: "R$1.100-6.600",  nota: "Canal monetizado — primeiros R$" },
  { fase: "Mês 7-12",  videos: 160, views_mes: "300K-1M",    adsense_mes: "R$6.600-22.000", nota: "Crescimento exponencial — algoritmo acelerou" },
  { fase: "Ano 2 H1",  videos: 280, views_mes: "1M-2M",      adsense_mes: "R$22K-44K",      nota: "Próximo da meta" },
  { fase: "Ano 2 H2",  videos: 400, views_mes: "2M-3.5M",    adsense_mes: "R$44K-77K ✅",   nota: "META R$50K ATINGIDA" },
];

// CPM por tema (para escolher quais gravar primeiro)
const CPM_POR_TEMA = [
  { tema: "Burnout e Trabalho",       cpm: "R$30-45", prioridade: 1, motivo: "Anunciantes corporativos pagam mais" },
  { tema: "TDAH e Produtividade",     cpm: "R$25-38", prioridade: 2, motivo: "Apps e cursos pagam bem" },
  { tema: "Relacionamentos e Terapia",cpm: "R$25-40", prioridade: 3, motivo: "Apps de terapia" },
  { tema: "Ansiedade",                cpm: "R$20-35", prioridade: 4, motivo: "Volume alto + saúde" },
  { tema: "Autoconhecimento",         cpm: "R$22-35", prioridade: 5, motivo: "Cursos e coaching" },
  { tema: "Depressão",                cpm: "R$18-32", prioridade: 6, motivo: "Farmacêuticas" },
  { tema: "Narcisismo",               cpm: "R$15-25", prioridade: 7, motivo: "Menos anunciantes diretos" },
];

// Alerta amarelo: temas com risco de restricted ads
const TEMAS_RISCO = [
  "Crise de pânico (mencionar crise)",
  "Suicídio (qualquer menção)",
  "Automutilação",
  "Overdose/medicação específica",
];

export async function GET(request) {
  try {
    const sbUrl = process.env.SUPABASE_URL || "https://tpjvalzwkqwttvmszvie.supabase.co";
    const sbKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
    const sb = createClient(sbUrl, sbKey);
    const url = new URL(request.url);
    const views = parseInt(url.searchParams.get("views") || "0");

    // Calcular receita para um número específico de views
    if (views > 0) {
      return Response.json({
        views_mes: views,
        receita_conservadora: `R$${(views * CALC.rpm_min / 1000).toLocaleString("pt-BR", {minimumFractionDigits:0, maximumFractionDigits:0})}`,
        receita_realista:     `R$${(views * CALC.rpm_medio / 1000).toLocaleString("pt-BR", {minimumFractionDigits:0, maximumFractionDigits:0})}`,
        receita_otimista:     `R$${(views * CALC.rpm_max / 1000).toLocaleString("pt-BR", {minimumFractionDigits:0, maximumFractionDigits:0})}`,
        meta_50k_atingida: views >= views_realista,
        falta_para_meta: views >= views_realista ? "META ATINGIDA!" : `${(views_realista - views).toLocaleString("pt-BR")} views/mês`,
      });
    }

    // Buscar dados reais do pipeline
    const { data: publicados } = await sb.from("content_pipeline")
      .select("id").eq("status","published");
    const { data: fila } = await sb.from("content_pipeline")
      .select("id").eq("status","pending_generation");
    const total_pub = (publicados||[]).length;
    const total_fila = (fila||[]).length;

    // Estimar views mensais baseado em vídeos publicados
    const views_estimado = total_pub * 15000; // 15K views médio por vídeo/mês
    const receita_estimada = views_estimado * CALC.rpm_medio / 1000;
    const progresso_pct = Math.min(Math.round(receita_estimada / 50000 * 100), 100);

    return Response.json({
      meta: "R$50.000/mês EXCLUSIVAMENTE de YouTube AdSense",
      
      matematica: {
        rpm_medio_psicologia_br: `R$${CALC.rpm_medio}/1000 views`,
        views_necessarias_por_mes: {
          conservador: `${views_conservador.toLocaleString("pt-BR")} views`,
          realista:    `${views_realista.toLocaleString("pt-BR")} views`,
          otimista:    `${views_otimista.toLocaleString("pt-BR")} views`,
        },
        logica_acumulativa: `${total_pub} vídeos × 15K views médio = ${views_estimado.toLocaleString("pt-BR")} views/mês estimado`,
        receita_atual_estimada: `R$${receita_estimada.toLocaleString("pt-BR", {minimumFractionDigits:0, maximumFractionDigits:0})}/mês`,
        progresso_para_meta: `${progresso_pct}%`,
      },

      receita_por_video: RECEITA_VIDEO,
      
      trajetoria: TRAJETORIA,
      
      cpm_por_tema: CPM_POR_TEMA,
      
      alerta_restricted_ads: {
        aviso: "⚠️ CRÍTICO: Estes temas causam YELLOW MONEY (anúncios restritos = -40-60% receita)",
        evitar: TEMAS_RISCO,
        solucao: "Focar em linguagem educacional: 'entender', 'superar', 'sinais de' — não clínica"
      },

      configuracoes_adsense_obrigatorias: [
        "✅ Ativar TODOS os formatos de anúncio no YouTube Studio",
        "✅ Ativar mid-roll AUTOMÁTICO em todos os vídeos >8 min",
        "✅ Posicionar mid-rolls nos momentos de maior tensão (viewer não pula)",
        "✅ Revisar monetização de cada vídeo após upload",
        "✅ Apelar revisão manual se vídeo for restrito incorretamente",
      ],

      sazonalidade_cpm: {
        melhor_mes: "Dezembro (CPM +35%) e Outubro/Novembro (CPM +25%)",
        pior_mes: "Janeiro (CPM -20%) e Julho/Agosto (CPM -15%)",
        estrategia: "Publicar MAIS em set-dez para maximizar receita do Q4"
      },

      pipeline: {
        videos_publicados: total_pub,
        videos_na_fila: total_fila,
        meses_de_conteudo: Math.round(total_fila / 20),
        nota: "487 vídeos na fila = 24 meses de conteúdo automático"
      },

      proximos_passos: [
        "🔴 1. YOUTUBE_REFRESH_TOKEN (5 min) → publicação automática começa",
        "🟡 2. Google Ads R$200 → campanha In-stream → 0→1K subs em 30 dias",
        "🟡 3. EP01 Ansiedade primeiro (200K buscas/mês = mais chance de viral)",
        "🟢 4. Ativar todos os formatos de anúncio no YouTube Studio quando aprovado",
        "🟢 5. Priorizar upload de Burnout e TDAH (CPM mais alto do canal)"
      ],

      url_calculadora: "repovazio.vercel.app/api/adsense?views=NUMERO",
    });

  } catch(e) {
    return Response.json({ error: e.message }, { status: 500 });
  }
}
