export const runtime = 'edge';

import { createClient } from "@supabase/supabase-js";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const SBU = process.env.SUPABASE_URL || "https://tpjvalzwkqwttvmszvie.supabase.co";
const SBK = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

// LLM CHAIN 100% GRÁTIS — 4 providers em paralelo
const LLM_PROVIDERS = [
  { name: "groq",       url: "https://api.groq.com/openai/v1/chat/completions",      key_env: "GROQ_API_KEY",       model: "llama-3.3-70b-versatile",        limit: "14400/dia" },
  { name: "cerebras",   url: "https://api.cerebras.ai/v1/chat/completions",          key_env: "CEREBRAS_API_KEY",   model: "llama-3.3-70b",                  limit: "ilimitado/dia" },
  { name: "nvidia",     url: "https://integrate.api.nvidia.com/v1/chat/completions", key_env: "NVIDIA_API_KEY",     model: "deepseek-ai/deepseek-r1",        limit: "1000/dia" },
  { name: "openrouter", url: "https://openrouter.ai/api/v1/chat/completions",        key_env: "OPENROUTER_API_KEY", model: "deepseek/deepseek-r1:free",      limit: "ilimitado/dia" }
];

async function chamarLLMGratis(prompt, maxTokens = 3000) {
  for (const p of LLM_PROVIDERS) {
    const key = process.env[p.key_env];
    if (!key) continue;
    try {
      const r = await fetch(p.url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${key}` },
        body: JSON.stringify({
          model: p.model,
          messages: [{ role: "user", content: prompt }],
          max_tokens: maxTokens,
          temperature: 0.75
        }),
        signal: AbortSignal.timeout(45000)
      });
      if (!r.ok) {
        const errText = await r.text();
        console.log(`${p.name} falhou: ${r.status} ${errText.substring(0,200)}`);
        continue;
      }
      const d = await r.json();
      const text = d.choices?.[0]?.message?.content || "";
      if (text.length > 200) return { texto: text, provider: p.name, modelo: p.model, custo: "$0.00" };
    } catch (e) {
      console.log(`${p.name} erro: ${e.message}`);
      continue;
    }
  }
  return null;
}

async function carregarMemoriaEterna(sb) {
  const [{ data: padroes }, { data: regras }] = await Promise.all([
    sb.from("padroes_virais").select("chave,conteudo").eq("ativo", true),
    sb.from("regras_eternas").select("codigo,regra,categoria").eq("prioridade", 10)
  ]);
  return { padroes: padroes || [], regras: regras || [] };
}

function buildPromptViral(tema, formato, emocao, personagem, memoria) {
  const isLong = formato.includes("15") || formato.includes("long");
  const duracao = isLong ? "12-15 minutos (1.000 palavras)" : "55-60 segundos (130 palavras max)";
  
  const regrasAbs = (memoria.regras || [])
    .map(r => `• ${r.codigo}: ${r.regra}`)
    .slice(0, 10).join("\n");
  
  const estrutura = isLong ? `
ESTRUTURA 4 ATOS (15 MINUTOS) — ENGENHARIA DE ATENÇÃO:

[ATO 1 — 0-3min — A FERIDA ABERTA]
0-30s SUPER HOOK: mostrar a CENA mais intensa antes de explicar
30s-90s: dado real universalizando o problema
90s-3min: promessa específica + mapa do que vem

[ATO 2 — 3-8min — A ANATOMIA DO PROBLEMA]
3-5min: mecanismo neurológico em linguagem acessível
4min30s: pattern interrupt — pergunta direta ao viewer
5-7min: CASO REAL com arco completo (apresentação→conflito→virada→insight)
7-8min: MID-VIDEO HOOK — o mais forte do vídeo (Existe algo que ninguém fala...)

[ATO 3 — 8-13min — O QUE MUDA TUDO]
8-10min: virada principal — viewer vê o problema de ângulo novo
10-12min: framework prático 3-5 perguntas/passos específicos
12-13min: segundo caso real com resultado concreto

[ATO 4 — 13-15min — O LEGADO]
13-14min: síntese emocional (você veio pensando X, descobriu Y)
14-14min30s: identidade coletiva (compartilhar com quem ama)
14min30s-15min: teaser específico do próximo vídeo

RETENTION HOOKS a cada 90s: 45s(espelho), 90s(dado), 150s(curiosity), 270s(pattern_interrupt), 360s(pergunta), 480s(MID-HOOK), 600s(revelação), 720s(dado_2), 840s(validação), 900s(teaser)
` : `
ESTRUTURA 7 ATOS (60 SEGUNDOS):
[ATO 1 — HOOK — 0-5s]: cena específica, NUNCA afirmação genérica
[ATO 2 — AMPLIFICAÇÃO — 5-15s]: dado real com fonte universidade/pesquisa
[ATO 3 — CASO REAL — 15-25s]: nome+idade+profissão+situação específica
[ATO 4 — VIRADA CIENTÍFICA — 25-35s]: mecanismo neurológico simples
[ATO 5 — CUSTO REAL — 35-45s]: consequência sem alarmar
[ATO 6 — CAMINHO — 45-55s]: insight específico, não conselho vago
[ATO 7 — ANCORAGEM — 55-60s]: identificação coletiva, zero pedido de like
`;

  return `Você é o cérebro autônomo psicologia.doc — canal brasileiro de psicologia visando 1M subscribers em 2027.
Sua missão: criar roteiros virais que hipnotizam o viewer e maximizam retenção mundial.
Padrões dos canais referência: Psych2Go (28M views), Therapy in a Nutshell (68% retenção), Kati Morton (71% retenção).

TEMA: ${tema}
FORMATO: ${formato} | ${duracao}
EMOÇÃO PRINCIPAL: ${emocao}
PERSONAGEM/FONTE: ${personagem}

REGRAS ABSOLUTAS DA MEMÓRIA ETERNA (NUNCA VIOLAR):
${regrasAbs}

ESTRATÉGIA DE SUCESSO GLOBAL:
- Áudio em PT-BR (default eterno)
- Personagem mantém nome BR em todos os idiomas (Marina/Lucas/Sofia/Rafael/Isabela/Lara)
- Situação UNIVERSAL que ressoa em qualquer cultura
- Dado científico com fonte real (universidade + pesquisador + ano)
- Hook nos primeiros 5 segundos = cena específica + sensação física

${estrutura}

GERAR EXATAMENTE NESTE FORMATO:
TITULO: [título viral PT-BR otimizado para CTR]
DESCRICAO_YT: [150 palavras com keywords + CTA cultural]
TAGS: [15 tags PT-BR separadas por vírgula]
SCRIPT: [roteiro completo narrado em pt-BR autêntico, seguindo a estrutura acima]
CENAS_VISUAIS: [para cada cena: descrição completa do personagem + expressão + ambiente + paleta — usado para gerar imagem Flux ZERO TEXTO]

GERE AGORA — roteiro completo de produção, não resumo:`;
}

function parsearScript(texto) {
  const lines = texto.split("\n");
  let titulo = "", descricao = "", tags = "", script = "", cenas = "";
  let mode = "";
  for (const line of lines) {
    if (line.match(/^T[IÍ]TULO:/i)) { titulo = line.replace(/^T[IÍ]TULO:/i, "").trim(); continue; }
    if (line.match(/^DESCRICAO_YT:/i) || line.match(/^DESCRIÇÃO_YT:/i)) { descricao = line.replace(/^DESCRI[CÇ]AO_YT:/i, "").trim(); mode = "desc"; continue; }
    if (line.match(/^TAGS:/i)) { tags = line.replace(/^TAGS:/i, "").trim(); mode = ""; continue; }
    if (line.match(/^SCRIPT:/i)) { mode = "script"; continue; }
    if (line.match(/^CENAS/i)) { mode = "cenas"; continue; }
    if (mode === "desc") descricao += " " + line.trim();
    if (mode === "script") script += line + "\n";
    if (mode === "cenas") cenas += line + "\n";
  }
  return {
    titulo: titulo || "Vídeo psicologia.doc",
    descricao: descricao.trim(),
    tags: tags.split(/[,;]/).map(t=>t.trim()).filter(Boolean).slice(0,15),
    script: script.trim(),
    cenas: cenas.trim()
  };
}

export async function GET(request) {
  const url = new URL(request.url);
  const action = url.searchParams.get("action") || "status";
  const sb = createClient(SBU, SBK);

  if (action === "gerar_proximo") {
    // Pegar o próximo da fila de prioridade
    const { data: video } = await sb.from("content_pipeline")
      .select("id,title,metadata,status")
      .eq("status", "pending_generation")
      .not("metadata->>prioridade_geracao", "is", null)
      .order("metadata->>prioridade_geracao", { ascending: true })
      .limit(1).single();

    if (!video) return Response.json({ ok: true, mensagem: "Nenhum vídeo prioritário pendente" });

    const tema = video.metadata?.tema || video.title;
    const emocao = video.metadata?.emocao || "contemplativo";
    const formato = video.metadata?.formato || "short_60s";
    const personagem = video.metadata?.personagem || "Personagem brasileiro";

    const memoria = await carregarMemoriaEterna(sb);
    const prompt = buildPromptViral(tema, formato, emocao, personagem, memoria);
    const llmResult = await chamarLLMGratis(prompt);

    if (!llmResult) {
      return Response.json({ ok: false, video_id: video.id, erro: "Nenhum LLM grátis respondeu" });
    }

    const parsed = parsearScript(llmResult.texto);

    const { error } = await sb.from("content_pipeline")
      .update({
        title: parsed.titulo,
        script: parsed.script,
        status: "script_ready",
        metadata: {
          ...video.metadata,
          descricao_yt: parsed.descricao,
          tags_yt: parsed.tags,
          cenas_visuais: parsed.cenas,
          llm_provider: llmResult.provider,
          llm_modelo: llmResult.modelo,
          llm_custo: "$0.00",
          gerado_em: new Date().toISOString(),
          stack_gratuita: true
        }
      })
      .eq("id", video.id);

    return Response.json({
      ok: !error,
      video_id: video.id,
      titulo_novo: parsed.titulo,
      formato, emocao, personagem,
      provider: llmResult.provider,
      modelo: llmResult.modelo,
      custo: "$0.00",
      script_length: parsed.script.length,
      tags_count: parsed.tags.length
    });
  }

  if (action === "gerar_lote") {
    const limit = parseInt(url.searchParams.get("limit") || "3");
    const resultados = [];
    for (let i = 0; i < limit; i++) {
      try {
        const r = await fetch(`${url.origin}/api/cerebro-gerador?action=gerar_proximo`);
        const d = await r.json();
        resultados.push(d);
        if (!d.ok || !d.video_id) break;
        await new Promise(r => setTimeout(r, 3000));
      } catch (e) {
        resultados.push({ erro: e.message });
        break;
      }
    }
    return Response.json({ total_processados: resultados.length, resultados });
  }

  if (action === "status") {
    const { data: prioritarios } = await sb.from("content_pipeline")
      .select("id,title,status,metadata")
      .eq("status", "pending_generation")
      .not("metadata->>prioridade_geracao", "is", null)
      .order("metadata->>prioridade_geracao", { ascending: true });

    const { data: scriptReady } = await sb.from("content_pipeline")
      .select("id,title").eq("status", "script_ready");

    return Response.json({
      sistema: "Cérebro Gerador V2 — Stack 100% Grátis",
      providers_llm: LLM_PROVIDERS.map(p => ({ nome: p.name, modelo: p.model, configurado: !!process.env[p.key_env], limite: p.limit })),
      providers_ativos: LLM_PROVIDERS.filter(p => process.env[p.key_env]).length,
      fila_prioritaria: (prioritarios || []).length,
      script_ready: (scriptReady || []).length,
      acoes: {
        "gerar_proximo": "/api/cerebro-gerador?action=gerar_proximo",
        "gerar_lote_3": "/api/cerebro-gerador?action=gerar_lote&limit=3",
        "gerar_lote_10": "/api/cerebro-gerador?action=gerar_lote&limit=10"
      }
    });
  }

  return Response.json({
    sistema: "Cérebro Gerador V2",
    stack: "100% grátis — Groq + Cerebras + NVIDIA + OpenRouter (fallback chain)",
    custo: "$0.00 por vídeo gerado"
  });
}
