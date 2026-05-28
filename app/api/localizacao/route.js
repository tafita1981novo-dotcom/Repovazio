export const runtime = 'edge';

import { createClient } from "@supabase/supabase-js";
export const dynamic = "force-dynamic";

const SBU = process.env.SUPABASE_URL || "https://tpjvalzwkqwttvmszvie.supabase.co";
const SBK = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
const GROQ_KEY = process.env.GROQ_API_KEY || "";
const NVIDIA_KEY = process.env.NVIDIA_API_KEY || "";
const OPENAI_KEY = process.env.OPENAI_API_KEY || "";

const IDIOMAS = {
  "pt-BR": { nome: "Português Brasileiro", papel: "DEFAULT", yt_code: "pt-BR", cpm: "$2-4",  prioridade: 1 },
  "en":    { nome: "English",              papel: "PRIORITARIO_1", yt_code: "en",  cpm: "$10-25", prioridade: 2 },
  "es":    { nome: "Español",              papel: "PRIORITARIO_2", yt_code: "es",  cpm: "$3-6",  prioridade: 3 },
  "fr":    { nome: "Français",             papel: "PRIORITARIO_3", yt_code: "fr",  cpm: "$7-12", prioridade: 4 },
  "de":    { nome: "Deutsch",              papel: "PREMIUM",        yt_code: "de",  cpm: "$8-18", prioridade: 5 },
  "it":    { nome: "Italiano",             papel: "EMERGENTE",      yt_code: "it",  cpm: "$5-9",  prioridade: 6 },
  "ja":    { nome: "日本語",                papel: "PREMIUM_NICHO",  yt_code: "ja",  cpm: "$10-22",prioridade: 7 }
};

async function chamarLLM(prompt) {
  const providers = [
    { name: "groq", url: "https://api.groq.com/openai/v1/chat/completions", key: GROQ_KEY, model: "llama-3.3-70b-versatile" },
    { name: "nvidia", url: "https://integrate.api.nvidia.com/v1/chat/completions", key: NVIDIA_KEY, model: "deepseek-ai/deepseek-r1" },
    { name: "openai", url: "https://api.openai.com/v1/chat/completions", key: OPENAI_KEY, model: "gpt-4o-mini" }
  ];
  for (const p of providers) {
    if (!p.key) continue;
    try {
      const r = await fetch(p.url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${p.key}` },
        body: JSON.stringify({ model: p.model, messages: [{ role: "user", content: prompt }], max_tokens: 2500, temperature: 0.4 }),
        signal: AbortSignal.timeout(50000)
      });
      if (!r.ok) continue;
      const d = await r.json();
      const text = d.choices?.[0]?.message?.content || "";
      if (text.length > 100) return { texto: text, provider: p.name };
    } catch { continue; }
  }
  return null;
}

function buildPromptLocalizacao(titulo, descricao, tags, formato) {
  return `Você é o sistema de localização SEO do canal psicologia.doc. Sua missão: localizar conteúdo para SEO mundial em 6 idiomas estratégicos, mantendo a identidade brasileira do canal.

CONTEÚDO ORIGINAL EM PORTUGUÊS BRASILEIRO (DEFAULT — mantém intacto):
TÍTULO: ${titulo}
DESCRIÇÃO: ${descricao || "(gerar descrição se vazio)"}
TAGS: ${tags || "(gerar tags se vazio)"}
FORMATO: ${formato}

REGRAS ABSOLUTAS:
1. Manter nomes brasileiros (Marina, Lucas, Sofia, Rafael, Isabela, Lara) em TODAS as traduções
2. Adaptar expressões idiomáticas culturalmente (não traduzir literalmente)
3. Cada idioma deve maximizar CTR no seu mercado — usar fórmulas virais nativas
4. Tags: priorizar termos de busca mais procurados em cada idioma
5. Descrição: 150 palavras com keywords + CTA cultural apropriado
6. Tom: manter calidez brasileira (não imitar tom anglo-saxão clínico)

GERAR PARA 6 IDIOMAS:
- en (English): mercado EUA/UK/Global, CPM mais alto, máximo CTR
- es (Español): LATAM + Espanha, tom próximo BR
- fr (Français): França + África francófona + Quebec
- de (Deutsch): DACH, CPM premium, tom respeitoso intelectual
- it (Italiano): Itália emergente, tom emocional caloroso
- ja (日本語): Japão premium, tom indireto e respeitoso, evitar diretividade

FORMATO DE SAÍDA EXATAMENTE ASSIM (JSON limpo, nada antes ou depois):
{
  "en": {"title": "...", "description": "...", "tags": ["tag1","tag2",...15]},
  "es": {"title": "...", "description": "...", "tags": [...15]},
  "fr": {"title": "...", "description": "...", "tags": [...15]},
  "de": {"title": "...", "description": "...", "tags": [...15]},
  "it": {"title": "...", "description": "...", "tags": [...15]},
  "ja": {"title": "...", "description": "...", "tags": [...15]}
}

GERE AGORA — apenas o JSON, nada mais:`;
}

function parsearLocalizacao(texto) {
  // Extrair JSON do texto da resposta
  let json = texto.trim();
  // Remover possíveis markdown
  json = json.replace(/^```json\s*/i, "").replace(/^```\s*/, "").replace(/```\s*$/, "");
  // Pegar do primeiro { até o último }
  const start = json.indexOf("{");
  const end = json.lastIndexOf("}");
  if (start >= 0 && end > start) json = json.substring(start, end + 1);
  try {
    return JSON.parse(json);
  } catch (e) {
    return null;
  }
}

export async function GET(request) {
  const sb = createClient(SBU, SBK);
  const url = new URL(request.url);
  const action = url.searchParams.get("action") || "status";

  if (action === "localizar_video") {
    const videoId = parseInt(url.searchParams.get("video_id") || "0");
    if (!videoId) return Response.json({ error: "video_id obrigatório" }, { status: 400 });

    const { data: video, error } = await sb.from("content_pipeline")
      .select("id,title,script,status,metadata")
      .eq("id", videoId).single();
    if (error || !video) return Response.json({ error: "vídeo não encontrado" }, { status: 404 });

    const titulo = video.title || "";
    const descricao = video.metadata?.descricao_yt || video.script?.substring(0, 500) || "";
    const tags = (video.metadata?.tags_yt || []).join(", ");
    const formato = video.metadata?.formato || "short_60s";

    const prompt = buildPromptLocalizacao(titulo, descricao, tags, formato);
    const llmResult = await chamarLLM(prompt);
    if (!llmResult) return Response.json({ error: "LLM indisponível" }, { status: 503 });

    const localizacoes = parsearLocalizacao(llmResult.texto);
    if (!localizacoes) return Response.json({ error: "parse falhou", raw: llmResult.texto.substring(0, 500) }, { status: 500 });

    // Salvar no metadata do vídeo
    const novosMeta = {
      ...video.metadata,
      localizations: localizacoes,
      localizacao_provider: llmResult.provider,
      localizado_em: new Date().toISOString(),
      idiomas: ["pt-BR","en","es","fr","de","it","ja"]
    };

    const { error: upErr } = await sb.from("content_pipeline")
      .update({ metadata: novosMeta }).eq("id", videoId);

    return Response.json({
      ok: !upErr,
      video_id: videoId,
      titulo_default_pt_BR: titulo,
      total_idiomas_gerados: Object.keys(localizacoes).length,
      provider: llmResult.provider,
      preview_idiomas: Object.fromEntries(
        Object.entries(localizacoes).map(([k,v]) => [k, { title: v.title, tags_count: v.tags?.length }])
      ),
      localizacoes_completas: localizacoes,
      erro_update: upErr?.message
    });
  }

  if (action === "localizar_todos_prontos") {
    // Localizar todos os videos com status mp4_ready ou audio_ready que ainda não foram localizados
    const { data: videos } = await sb.from("content_pipeline")
      .select("id,title,metadata,status")
      .in("status", ["mp4_ready","audio_ready","script_ready"])
      .limit(10);

    const resultados = [];
    for (const v of (videos || [])) {
      if (v.metadata?.localizations) {
        resultados.push({ id: v.id, status: "ja_localizado" });
        continue;
      }
      // Localizar este vídeo (via mesma lógica acima — simplificado: chamar API)
      try {
        const r = await fetch(`${url.origin}/api/localizacao?action=localizar_video&video_id=${v.id}`);
        const d = await r.json();
        resultados.push({ id: v.id, titulo: v.title?.substring(0,40), ok: d.ok, idiomas: d.total_idiomas_gerados });
        await new Promise(r => setTimeout(r, 1500));
      } catch (e) {
        resultados.push({ id: v.id, erro: e.message });
      }
    }
    return Response.json({ total_processados: resultados.length, resultados });
  }

  if (action === "ver_localizacao") {
    const videoId = parseInt(url.searchParams.get("video_id") || "0");
    const { data: video } = await sb.from("content_pipeline")
      .select("id,title,metadata").eq("id", videoId).single();
    return Response.json({
      video_id: videoId,
      titulo_pt_BR: video?.title,
      localizations: video?.metadata?.localizations || null,
      idiomas_disponiveis: video?.metadata?.localizations ? Object.keys(video.metadata.localizations) : []
    });
  }

  if (action === "stats") {
    const { data: todos } = await sb.from("content_pipeline").select("metadata");
    const totalLocalizados = (todos || []).filter(v => v.metadata?.localizations).length;
    const totalGeral = (todos || []).length;
    return Response.json({
      sistema: "Localização Global SEO — psicologia.doc",
      total_videos: totalGeral,
      total_localizados: totalLocalizados,
      pct_localizados: totalGeral > 0 ? `${Math.round(100*totalLocalizados/totalGeral)}%` : "0%",
      idiomas_alvo: 7,
      cpm_esperado_mix: "$5-12 USD (mix global dos 7 idiomas)"
    });
  }

  return Response.json({
    sistema: "Localização Global Multi-Idioma — psicologia.doc",
    versao: "1.0",
    descricao: "Default eterno PT-BR + SEO localizado em 6 idiomas estratégicos para descobribilidade mundial",
    idiomas: IDIOMAS,
    acoes: {
      "localizar_um_video": "/api/localizacao?action=localizar_video&video_id=294",
      "localizar_todos_prontos": "/api/localizacao?action=localizar_todos_prontos",
      "ver_localizacao_video": "/api/localizacao?action=ver_localizacao&video_id=294",
      "stats_globais": "/api/localizacao?action=stats"
    },
    pipeline: [
      "1. Vídeo gerado em PT-BR (default eterno)",
      "2. Whisper transcribe → SRT pt-BR",
      "3. /api/localizacao traduz título+descrição+tags para 6 idiomas via LLM",
      "4. /api/distribute publica em YouTube com snippet.localizations + captions",
      "5. YouTube auto-traduz legendas para outros 90+ idiomas",
      "6. Instagram: caption em camadas multilíngues (PT > EN > ES)",
      "7. TikTok: captions PT-BR + auto-translation nativa",
      "8. Monitorar CTR/retenção por idioma → priorizar próximos temas"
    ],
    monetizacao: {
      "cpm_so_BR": "$2-4 USD",
      "cpm_mix_global": "$5-12 USD",
      "multiplicador_views": "3-5x via legendas auto-traduzidas"
    }
  });
}
