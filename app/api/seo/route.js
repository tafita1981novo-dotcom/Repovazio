export const runtime = 'edge';

import { createClient } from "@supabase/supabase-js";
export const dynamic = "force-dynamic";
export const revalidate = 0;

// ================================================================
// SEO MASTER 2026 — psicologia.doc
// Baseado em cases: Psych2Go 12M | Dr. Ramani 2M | MrBeast formula
// ================================================================

const KEYWORDS_VOLUME_BR = {
  "ansiedade":200000, "depressao":150000, "tdah":110000, "burnout":80000,
  "narcisismo":74000, "autoconhecimento":70000, "apego ansioso":65000,
  "trauma":60000, "relacionamento toxico":58000, "inteligencia emocional":55000,
  "gaslighting":45000, "borderline":40000, "luto":40000, "autossabotagem":35000,
};

const DESCRICAO_TEMPLATE = (serie, titulo, kw, episodio, gancho) => `${titulo}

Neste episódio de ${serie}, você vai entender como ${kw} funciona e o que fazer a respeito.

⏱️ CAPÍTULOS:
00:00 Introdução
02:00 O que é ${kw}
05:00 Como se desenvolve
09:00 Sinais que você pode ter
12:00 O que fazer agora

📌 SÉRIE COMPLETA: ${serie}
${gancho ? `👉 PRÓXIMO EPISÓDIO: ${gancho}` : ""}

🔔 Inscreva-se para novos episódios toda semana
📱 Instagram: @psidanielacoelho
💬 Grupo WhatsApp: Link na bio

#${kw.replace(/ /g,"")} #psicologia #saudemental #psidanielacoelho #psicologiadoc
`.trim();

export async function GET(request) {
  try {
    const sbUrl = process.env.SUPABASE_URL || "https://tpjvalzwkqwttvmszvie.supabase.co";
    const sbKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
    const sb = createClient(sbUrl, sbKey);
    const url = new URL(request.url);
    const action = url.searchParams.get("action") || "status";
    const id = url.searchParams.get("id");

    // SEO para um vídeo específico
    if (action === "video" && id) {
      const { data: v } = await sb.from("content_pipeline")
        .select("id,title,metadata,script").eq("id", id).single();
      if (!v) return Response.json({ error: "Video não encontrado" }, { status: 404 });
      
      const serie = v.metadata?.serie || "";
      const kw = v.metadata?.seo_keyword || serie.toLowerCase();
      const gancho = v.metadata?.gancho_final || "";
      const ep = v.metadata?.episodio || "S01";
      
      return Response.json({
        video_id: v.id,
        titulo_atual: v.title,
        seo: {
          titulo_seo: v.metadata?.titulo_seo || v.title,
          descricao_seo: v.metadata?.descricao_seo || DESCRICAO_TEMPLATE(serie, v.title, kw, ep, gancho),
          tags: v.metadata?.tags || [kw, serie.toLowerCase(), "psicologia", "saude mental", "daniela coelho"],
          hashtags_instagram: v.metadata?.hashtags_instagram || ["#psicologia","#saudemental","#"+kw.replace(/ /g,"")],
          caption_tiktok: v.metadata?.caption_tiktok || `${v.title.substring(0,80)} | ${kw} | @psidanielacoelho`,
          capitulos: v.metadata?.capitulos || "00:00 Introdução | 02:00 Desenvolvimento | 10:00 Solução",
          gancho_final: gancho,
        }
      });
    }

    // Dashboard de SEO geral
    const { data: videos_sem_seo } = await sb.from("content_pipeline")
      .select("id,title,metadata->seo_otimizado").filter("metadata->>seo_otimizado","neq","true")
      .in("status",["pending_generation","mp4_ready","published"]).limit(5);

    const { data: videos_com_seo } = await sb.from("content_pipeline")
      .select("id").filter("metadata->>seo_otimizado","eq","true");

    return Response.json({
      seo_status: "Ativo — SEO 2026 baseado em Psych2Go + Dr. Ramani + MrBeast",
      videos_otimizados: (videos_com_seo||[]).length,
      aguardando_otimizacao: (videos_sem_seo||[]).length,
      keywords_top_br: Object.entries(KEYWORDS_VOLUME_BR)
        .sort((a,b)=>b[1]-a[1]).slice(0,10).map(([k,v])=>({keyword:k,volume_mes:v})),
      regras_seo_2026: {
        titulo: "Keyword nas 3 primeiras palavras | máx 60 chars | gatilho emocional",
        thumbnail: "Rosto grande + expressão extrema + máx 3 palavras | testar A/B cada 48h",
        descricao: "Keyword nas 2 primeiras linhas (snippet Google) | 400-500 palavras | chapters obrigatório",
        tags: "15-20 tags: keyword exata + variações + nicho + série + canal",
        upload: "Qui 21h | Sex 18h | Sáb 11h | Dom 10h (picos BR)",
        retencao_meta: "Acima de 50% = algoritmo distribui | primeiros 30s sem intro",
      },
      monetizacao: {
        "0_ate_monetizar": "Afiliados Hotmart/Zenklub/Vittude: R$50-200 por venda",
        "1k_10k": "CPM psicologia BR: R$8-25/1000views | Micro patrocínios: R$300-1000",
        "10k_100k": "Patrocínios: R$2K-8K/video | Curso próprio: R$197 × 100 = R$19.700/mes",
        "100k_plus": "R$18K adsense + R$15K patrocínios + R$17K infoprodutos = R$50K+",
      },
      proximos_passos: [
        "1. Configurar YOUTUBE_REFRESH_TOKEN (5 min) → publicação automática",
        "2. Google Ads R$200 → campanha In-stream → @psidanielacoelho",
        "3. Publicar EP01 Ansiedade (200K buscas) → maior keyword do nicho",
        "4. Cross-post em Instagram Reels + TikTok + Pinterest Pin",
        "5. Responder TODOS os comentários nas primeiras 2h"
      ]
    });

  } catch(e) {
    return Response.json({ error: e.message }, { status: 500 });
  }
}
