export const runtime = 'edge';

import { createClient } from "@supabase/supabase-js";
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request) {
  try {
    const sbUrl = process.env.SUPABASE_URL || "https://tpjvalzwkqwttvmszvie.supabase.co";
    const sbKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
    const sb = createClient(sbUrl, sbKey);
    const url = new URL(request.url);
    const action = url.searchParams.get("action") || "status";

    const { data: grupos } = await sb.from("whatsapp_grupos").select("*").order("serie");

    if (action === "grupos") return Response.json({ total:(grupos||[]).length, grupos });

    const total_membros = (grupos||[]).reduce((s,g)=>s+(g.membros||0),0);
    const total_msgs    = (grupos||[]).reduce((s,g)=>s+(g.mensagens_enviadas||0),0);
    const aguardando    = (grupos||[]).filter(g=>!g.grupo_id).length;
    const ativos        = (grupos||[]).filter(g=> g.grupo_id).length;

    return Response.json({
      cerebro: "V14 — WhatsApp Autonomo 19 Grupos",
      total_grupos: (grupos||[]).length,
      grupos_ativos: ativos,
      grupos_pendentes: aguardando,
      total_membros,
      total_mensagens: total_msgs,
      configurar: {
        passo1: "Meta Business API → developers.facebook.com",
        passo2: "Criar app WhatsApp Business",
        passo3: "WHATSAPP_TOKEN + WHATSAPP_PHONE_ID no Vercel",
        passo4: "Criar 19 grupos e salvar grupo_id no banco"
      },
      grupos: (grupos||[]).map(g=>({
        serie: g.serie,
        nome: g.nome_grupo,
        membros: g.membros,
        msgs: g.mensagens_enviadas,
        ativo: !!g.grupo_id,
        ultimo_post: g.ultimo_post
      }))
    });
  } catch(e) {
    return Response.json({ error: e.message }, { status: 500 });
  }
}
