import { createClient } from "@supabase/supabase-js";
export const dynamic = "force-dynamic";
export const revalidate = 0;

// ================================================================
// MEMÓRIA ETERNA V2 — Consulta em Tempo Real pelo Cérebro
// Inclui: 60s + 15min | cases reais | KB hipnótico | canais virais
// Tudo consultado do Supabase antes de cada geração
// ================================================================

const SBU = process.env.SUPABASE_URL || "https://tpjvalzwkqwttvmszvie.supabase.co";
const SBK = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

function detectarEmocao(tema="") {
  const t = tema.toLowerCase();
  if (t.includes("apego")||t.includes("abandono")||t.includes("depend")) return "melancolico";
  if (t.includes("narcis")||t.includes("manipula")||t.includes("abuso")) return "tenso";
  if (t.includes("trauma")||t.includes("cura")||t.includes("integra")) return "calmo";
  if (t.includes("ansied")||t.includes("panico")||t.includes("hipervigi")) return "urgente";
  if (t.includes("burnout")||t.includes("esgotamento")) return "melancolico";
  return "contemplativo";
}

function detectarTemaKey(tema="") {
  const t = tema.toLowerCase();
  if (t.includes("apego")) return "apego_ansioso";
  if (t.includes("narcis")) return "narcisismo";
  if (t.includes("trauma")) return "trauma";
  if (t.includes("ansied")) return "ansiedade";
  if (t.includes("burnout")) return "burnout";
  if (t.includes("depend")) return "dependencia_emocional";
  if (t.includes("perfec")||t.includes("impostor")) return "perfeccionismo";
  return null;
}

export async function GET(request) {
  const sb = createClient(SBU, SBK);
  const url = new URL(request.url);
  const action = url.searchParams.get("action") || "completo";
  const tema   = url.searchParams.get("tema") || "";
  const formato= url.searchParams.get("formato") || "short_60s";
  const cat    = url.searchParams.get("categoria") || "";
  const chave  = url.searchParams.get("chave") || "";

  // Carrega tudo do Supabase em tempo real
  const [{ data: padroes }, { data: regras }] = await Promise.all([
    sb.from("padroes_virais").select("*").eq("ativo", true).order("prioridade", { ascending: false }),
    sb.from("regras_eternas").select("*").order("prioridade", { ascending: false })
  ]);

  const ALL_PADROES = padroes || [];
  const ALL_REGRAS  = regras  || [];

  // Helper para buscar padrao por chave
  const padrao = (k) => ALL_PADROES.find(p => p.chave === k)?.conteudo;

  // ── AÇÃO: gerar_video ───────────────────────────────────────
  if (action === "gerar_video" && tema) {
    const emocao  = detectarEmocao(tema);
    const temaKey = detectarTemaKey(tema);
    const isLong  = formato.includes("15") || formato.includes("long");

    // Buscar padrão correto
    const estrutura = isLong
      ? padrao("long_form_15min_engenharia_atencao")
      : padrao("sete_atos_virais");

    // Case real
    const casesBase = padrao("biblioteca_cases_reais");
    const caseReal  = temaKey ? casesBase?.[temaKey]?.[0] : null;

    // Ken Burns
    const kbBase = padrao("movimento_por_emocao");
    const kbPerf = isLong
      ? estrutura?.ken_burns_5_perfis_15min
      : kbBase?.perfis?.[emocao];

    // Hooks
    const hooksBase = padrao("formulas_hook_por_tipo");
    const hookEx    = hooksBase?.tipos?.espelho_dor?.exemplos?.[0] || "";

    // Imagens
    const imgBase   = padrao("prompts_flux_por_emocao");
    const imgPaleta = imgBase?.paletas_por_emocao?.[emocao];
    const imgShots  = isLong
      ? estrutura?.imagens_15min
      : imgBase?.shots_por_contexto;

    // Planejamento
    const planej    = padrao("pre_producao_cerebro_completo");
    const etapa4    = isLong
      ? planej?.etapa_4_retention_hooks?.formato_15min
      : planej?.etapa_4_retention_hooks?.formato_60s;

    // Canais referência
    const canais    = padrao("mapeamento_padroes_top_canais");

    // Regras absolutas
    const regrasAbs = ALL_REGRAS.filter(r => r.prioridade === 10).map(r => ({
      codigo: r.codigo,
      regra: r.regra,
      ok: r.exemplo_ok,
      nao: r.exemplo_nao
    }));

    // Áudio long form
    const audioConfig = isLong ? estrutura?.audio_variacao_obrigatoria : null;

    // Thumbnails
    const thumbs = isLong
      ? estrutura?.thumbnails_long_form
      : null;

    return Response.json({
      ok: true,
      tema, formato, emocao, tema_key: temaKey,
      is_long_form: isLong,
      fonte: "supabase_tempo_real",
      total_padroes_carregados: ALL_PADROES.length,
      total_regras_carregadas:  ALL_REGRAS.length,

      // TUDO QUE O CÉREBRO PRECISA PARA GERAR
      estrutura_narrativa:  estrutura,
      retention_hooks:      etapa4,
      case_real:            caseReal,
      ken_burns:            kbPerf,
      imagem_config:        { paleta: imgPaleta, shots: imgShots, sufixo: imgBase?.sufixo_obrigatorio },
      hook_exemplo:         hookEx,
      audio_config:         audioConfig,
      thumbnails:           thumbs,
      canais_referencia:    canais?.["10_denominadores_comuns_de_sucesso"],
      regras_absolutas:     regrasAbs,

      checklist_pre_render: isLong ? planej?.etapa_8_qa?.checklist : [
        "Hook cena especifica?", "Dado com fonte real?", "Personagem nome+idade?",
        "Sensacoes fisicas?", "Curiosity gap?", "Zero pedido like?",
        "Imagens sem texto?", "Progressao emocional dark→warm?",
        "KB correto?", "Canal UCyCkIpsVgME9yCj_oXJFheA?"
      ],

      planejamento_completo: planej
    });
  }

  // ── AÇÃO: regras_absolutas ────────────────────────────────
  if (action === "regras_absolutas") {
    return Response.json({
      total: ALL_REGRAS.filter(r=>r.prioridade===10).length,
      regras_absolutas: ALL_REGRAS.filter(r=>r.prioridade===10)
    });
  }

  // ── AÇÃO: long_form ───────────────────────────────────────
  if (action === "long_form") {
    return Response.json({
      estrutura: padrao("long_form_15min_engenharia_atencao"),
      planejamento: padrao("pre_producao_cerebro_completo"),
      canais: padrao("mapeamento_padroes_top_canais")
    });
  }

  // ── AÇÃO: canais ─────────────────────────────────────────
  if (action === "canais") {
    return Response.json(padrao("mapeamento_padroes_top_canais"));
  }

  // ── AÇÃO: planejamento ────────────────────────────────────
  if (action === "planejamento") {
    return Response.json(padrao("pre_producao_cerebro_completo"));
  }

  // ── AÇÃO: por_chave ──────────────────────────────────────
  if (action === "chave" && chave) {
    return Response.json({ chave, conteudo: padrao(chave) });
  }

  // ── STATUS COMPLETO ───────────────────────────────────────
  const { data: evolucoes } = await sb.from("cerebro_evolucao")
    .select("versao,tipo,descricao,criado_em")
    .order("criado_em", { ascending: false }).limit(5);

  return Response.json({
    sistema: "Memória Eterna V2 — psicologia.doc",
    versao: "2.0",
    descricao: "Consultada em tempo real pelo cérebro antes de QUALQUER geração",
    totais: {
      padroes_virais: ALL_PADROES.length,
      regras_eternas: ALL_REGRAS.length,
      regras_absolutas: ALL_REGRAS.filter(r=>r.prioridade===10).length
    },
    padroes_disponiveis: ALL_PADROES.map(p=>({
      chave: p.chave, categoria: p.categoria, titulo: p.titulo, prioridade: p.prioridade
    })),
    regras_absolutas_resumo: ALL_REGRAS.filter(r=>r.prioridade===10).map(r=>({
      codigo: r.codigo, categoria: r.categoria, resumo: r.descricao
    })),
    evolucoes_recentes: evolucoes || [],
    acoes: {
      "gerar_60s":         "/api/memoria?action=gerar_video&tema=apego+ansioso&formato=short_60s",
      "gerar_15min":       "/api/memoria?action=gerar_video&tema=trauma+invisivel&formato=long_15min",
      "ver_long_form":     "/api/memoria?action=long_form",
      "ver_canais":        "/api/memoria?action=canais",
      "ver_planejamento":  "/api/memoria?action=planejamento",
      "regras_absolutas":  "/api/memoria?action=regras_absolutas",
      "por_chave":         "/api/memoria?action=chave&chave=sete_atos_virais"
    },
    regras_nunca_violar: [
      "ZERO texto nas imagens (Flux.1 Schnell)",
      "Estilo flat 2D vector — nunca fotorrealista",
      "Hook com cena específica — nunca afirmação genérica",
      "Dado científico com fonte real obrigatória",
      "Case real com nome+idade+profissão em todo vídeo",
      "Retention hook a cada 60-90 segundos",
      "5 perfis KB distintos para 15min | 3 perfis para 60s",
      "Psicologia (não psicóloga) até 01/01/2027",
      "Canal UCyCkIpsVgME9yCj_oXJFheA — NUNCA UCSH63tBfY6wEIdkC4u4zKdg"
    ]
  });
}
