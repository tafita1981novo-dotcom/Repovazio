import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SUPABASE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || Deno.env.get('SUPABASE_ANON_KEY')!;

Deno.serve(async (req: Request) => {
  const headers = { 'Content-Type': 'application/json', 'Connection': 'keep-alive' };

  try {
    // Calcular semana atual
    const startDate = new Date('2026-05-16');
    const today = new Date();
    const diffDays = Math.floor((today.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
    const semanaAtual = Math.max(1, Math.floor(diffDays / 7) + 1);

    // Calcular datas da semana
    const semanaInicio = new Date(startDate);
    semanaInicio.setDate(startDate.getDate() + (semanaAtual - 1) * 7);
    const semanaFim = new Date(semanaInicio);
    semanaFim.setDate(semanaInicio.getDate() + 6);

    // Calcular metas
    let metaSubs, metaViews, metaReceita, metaVideos;
    if (semanaAtual <= 6) {
      metaSubs = semanaAtual * 200; metaViews = semanaAtual * 15000; metaReceita = 0; metaVideos = 3;
    } else if (semanaAtual <= 12) {
      metaSubs = 1000 + (semanaAtual - 6) * 1200; metaViews = 80000 + (semanaAtual - 6) * 30000;
      metaReceita = (semanaAtual - 6) * 250; metaVideos = 4;
    } else if (semanaAtual <= 20) {
      metaSubs = 8200 + (semanaAtual - 12) * 2500; metaViews = 250000 + (semanaAtual - 12) * 80000;
      metaReceita = 1500 + (semanaAtual - 12) * 1200; metaVideos = 5;
    } else if (semanaAtual <= 28) {
      metaSubs = 28000 + (semanaAtual - 20) * 6000; metaViews = 890000 + (semanaAtual - 20) * 200000;
      metaReceita = 11100 + (semanaAtual - 20) * 4500; metaVideos = 6;
    } else {
      metaSubs = 76000 + (semanaAtual - 28) * 8000; metaViews = 2490000 + (semanaAtual - 28) * 300000;
      metaReceita = 47100 + (semanaAtual - 28) * 5000; metaVideos = 7;
    }

    // Upsert semana atual
    const upsert = await fetch(`${SUPABASE_URL}/rest/v1/monetizacao_semanal`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_KEY,
        'Authorization': `Bearer ${SUPABASE_KEY}`,
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
      },
      body: JSON.stringify({
        semana: semanaAtual,
        data_inicio: semanaInicio.toISOString().split('T')[0],
        data_fim: semanaFim.toISOString().split('T')[0],
        meta_inscritos: metaSubs,
        meta_views: metaViews,
        meta_receita_r: metaReceita,
        meta_videos: metaVideos
      })
    });

    // Buscar semana anterior para avaliar
    let statusAnterior = null;
    if (semanaAtual > 1) {
      const prev = await fetch(`${SUPABASE_URL}/rest/v1/monetizacao_semanal?semana=eq.${semanaAtual-1}`, {
        headers: { 'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}` }
      });
      const prevData = await prev.json();
      if (prevData.length > 0) {
        const d = prevData[0];
        const pctSubs = d.meta_inscritos > 0 ? (d.inscritos_fim / d.meta_inscritos) * 100 : 0;
        let status, ajuste, foco;
        
        if (pctSubs >= 100) {
          status = 'acelerado';
          ajuste = 'Aumentar publicação em 1 vídeo/semana. Antecipar próximo marco de monetização.';
          foco = 'Capitalizar momentum: nova série viral + prospectar sponsors ativamente.';
        } else if (pctSubs >= 80) {
          status = 'no_rumo';
          ajuste = 'Manter cadência. Otimizar thumbnails dos últimos 3 vídeos.';
          foco = 'Série de maior viral score esta semana. Responder 100% comentários nas primeiras 2h.';
        } else if (pctSubs >= 50) {
          status = 'atrasado';
          ajuste = 'Publicar SHORT extra na sexta. Repostar Short de maior viral score.';
          foco = 'Dobrar Shorts de narcisismo e apego (refs 28M e 22M). Revisar hooks dos títulos.';
        } else {
          status = 'critico';
          ajuste = 'EMERGÊNCIA: publicar 2 Shorts extras. Narcisismo + Apego apenas. Revisar thumbnails urgente.';
          foco = 'FOCO TOTAL: Narcisismo + Apego. Hook nos primeiros 2 segundos é decisivo agora.';
        }

        // Atualizar semana anterior com análise
        await fetch(`${SUPABASE_URL}/rest/v1/monetizacao_semanal?semana=eq.${semanaAtual-1}`, {
          method: 'PATCH',
          headers: {
            'apikey': SUPABASE_KEY,
            'Authorization': `Bearer ${SUPABASE_KEY}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            status_geral: status,
            ajuste_cerebro: ajuste,
            proximo_foco: foco,
            percentual_meta_inscritos: Math.round(pctSubs * 10) / 10
          })
        });
        statusAnterior = { status, pctSubs: Math.round(pctSubs), ajuste };
      }
    }

    // Verificar marcos próximos
    const marcos = await fetch(
      `${SUPABASE_URL}/rest/v1/monetizacao_marcos?atingido=eq.false&semana_alvo=lte.${semanaAtual+4}&order=semana_alvo.asc&limit=3`,
      { headers: { 'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}` } }
    );
    const marcosData = await marcos.json();

    return new Response(JSON.stringify({
      ok: true,
      semana: semanaAtual,
      periodo: `${semanaInicio.toISOString().split('T')[0]} → ${semanaFim.toISOString().split('T')[0]}`,
      metas: { subs: metaSubs, views: metaViews, receita_r: metaReceita, videos: metaVideos },
      analise_anterior: statusAnterior,
      proximos_marcos: marcosData.map((m: any) => ({ s: m.semana_alvo, desc: m.descricao })),
      meta_global: 'R$50.000/mês na Semana 28 (28/nov/2026)',
      links: {
        calendario: 'https://repovazio.vercel.app/calendario-anual.html',
        estrategia: 'https://repovazio.vercel.app/estrategia-r50k.html',
        galeria: 'https://repovazio.vercel.app/galeria-videos.html'
      }
    }), { headers });

  } catch (err: any) {
    return new Response(JSON.stringify({ ok: false, erro: err.message }), { headers, status: 500 });
  }
});
