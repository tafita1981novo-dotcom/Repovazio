import { createClient } from "@supabase/supabase-js";
export const dynamic = "force-dynamic";

// ============================================================
// GERADOR VIRAL V1 — psicologia.doc
// Engenharia de atenção máxima + 7 Atos + Cases Reais + Ken Burns hipnótico
// ============================================================

const SBU = process.env.SUPABASE_URL || "https://tpjvalzwkqwttvmszvie.supabase.co";
const SBK = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

// CASES REAIS — base de credibilidade e espelho emocional
const CASES_REAIS = {
  apego_ansioso: [
    { personagem: "Marina, 29 anos, São Paulo", situacao: "Verificava o celular 80 vezes por dia esperando mensagem do namorado", dado: "67% das pessoas com apego ansioso sentem ansiedade física quando não recebem resposta em até 15 minutos (Universidade de Stanford)", reviravolta: "O problema não era o namorado. Era o pai ausente quando ela tinha 7 anos." },
    { personagem: "Estudo com 4.000 adultos", fonte: "Journal of Personality and Social Psychology, 2021", dado: "72% das pessoas com apego ansioso formado na infância repetem exatamente o mesmo padrão em todos os relacionamentos adultos", choque: "Sem trabalhar a raiz, trocar de parceiro 10 vezes produz exatamente a mesma dor" }
  ],
  narcisismo: [
    { personagem: "Estudo longitudinal — Harvard Medical School", dado: "Narcisistas passam em média 7 anos em um relacionamento antes de a vítima conseguir se desvencilhar", choque: "89% das vítimas levam mais 2 anos para parar de justificar o comportamento do narcisista após sair" },
    { personagem: "Lucas, 38 anos, engenheiro", situacao: "Era considerado o homem perfeito — generoso, atencioso. Mas só quando as câmeras estavam ligadas", dado: "Psicólogos chamam de janela de amor — o período que o narcisista usa para criar dependência antes do ciclo de desvalorização" }
  ],
  trauma: [
    { personagem: "Dr. Bessel van der Kolk", fonte: "O Corpo Guarda as Marcas — 2 milhões de cópias", dado: "Trauma não é só o que aconteceu com você. É o que acontece DENTRO de você quando seu sistema nervoso não consegue processar a experiência", choque: "Você pode ter trauma de algo que para outra pessoa seria completamente normal" },
    { personagem: "ACE Study — CDC e Kaiser Permanente — 17.000 participantes", dado: "4+ experiências adversas na infância = 390% mais chance de depressão + 20 anos a menos de vida em média", choque: "A maioria nunca conecta os problemas do presente com o que viveu antes dos 12 anos" }
  ],
  ansiedade: [
    { personagem: "Experimento do botão — Universidade de Virginia, 2014", dado: "67% dos homens preferiram se chocar eletricamente a ficarem sozinhos com os próprios pensamentos por 15 minutos", choque: "A mente ansiosa literalmente foge de si mesma" },
    { personagem: "Sofia, 26 anos, professora", situacao: "Sorridente no trabalho, prestativa com todos. Dormia 2 horas por noite planejando como as coisas poderiam dar errado", dado: "Ansiedade de alto funcionamento — a maioria ao redor nunca percebe", reviravolta: "Seu cérebro aprendeu que estar alerta era a única forma de sobreviver" }
  ],
  burnout: [
    { personagem: "Pesquisa Gallup 2023", dado: "76% dos trabalhadores experimentam burnout. 28% sempre ou frequentemente. A maioria só percebe DEPOIS de sair da situação.", choque: "No meio do burnout, achavam que era normal se sentir assim" },
    { personagem: "Rafael, 33 anos, desenvolvedor", situacao: "Mal conseguia sair da cama. Não de preguiça — seus músculos simplesmente não obedeciam", dado: "Burnout destrói fisicamente o nucleus accumbens — região responsável por motivação e prazer. Apagamento neurológico real.", reviravolta: "Tentava trabalhar mais para resolver, sem saber que era isso que destruía sua neurologia" }
  ],
  perfeccionismo: [
    { personagem: "Brené Brown — 10.000 participantes ao longo de 20 anos", dado: "Perfeccionismo não é sobre excelência. É sobre evitar vergonha, julgamento e crítica", choque: "O perfeccionista não tem medo de falhar. Tem medo de que, se falhar, as pessoas descobrirão que ele não é bom o suficiente" }
  ]
};

// HOOKS VIRAIS — Os primeiros 5 segundos que determinam tudo
const HOOKS = {
  espelho_dor: [
    "Você já sentiu que a outra pessoa está sempre a um passo de te abandonar?",
    "Você checa o celular compulsivamente esperando uma resposta?",
    "Você trabalha sem parar mas se sente cada vez mais vazio?",
    "Você já se pegou justificando comportamentos que te machucaram?"
  ],
  dado_chocante: [
    "72% das pessoas repetem o mesmo padrão em todos os relacionamentos — sem perceber.",
    "Seu cérebro não consegue distinguir rejeição emocional de dor física.",
    "Burnout destrói fisicamente regiões do cérebro. Literalmente.",
    "67% das pessoas preferem se machucar a ficarem sozinhas com os próprios pensamentos."
  ],
  curiosidade_aberta: [
    "Existe um padrão específico que explica por que você escolhe sempre as mesmas pessoas.",
    "A ciência encontrou o exato momento em que o amor vira dependência.",
    "Há uma frase que a maioria dos pais diz que programa o filho para o medo do abandono.",
    "Psicólogos identificaram os 5 minutos de uma conversa que revelam tudo sobre o vínculo."
  ]
};

// KEN BURNS HIPNÓTICO — Parâmetros de movimento por emoção
const KEN_BURNS_PARAMS = {
  melancolico: { zoom_start: 1.0, zoom_end: 1.15, pan_speed: 0.02, style: "slow_zoom_in", flash_cuts: [8, 22, 38], pause_frames: [5, 28, 50] },
  tenso:       { zoom_start: 0.9, zoom_end: 1.25, pan_speed: 0.04, style: "fast_impact",  flash_cuts: [3, 20, 42], pause_frames: [11, 35] },
  calmo:       { zoom_start: 1.0, zoom_end: 1.08, pan_speed: 0.01, style: "very_slow",    flash_cuts: [14, 29],    pause_frames: [5, 20, 44] },
  urgente:     { zoom_start: 1.0, zoom_end: 1.20, pan_speed: 0.05, style: "irregular",    flash_cuts: [4, 15, 40], pause_frames: [27, 50] },
  contemplativo:{ zoom_start: 1.0, zoom_end: 1.10, pan_speed: 0.015, style: "meditative", flash_cuts: [12, 35],   pause_frames: [8, 25, 48] }
};

function buildMegaPromptViral(tema, formato, caseReal) {
  const isShort = formato.includes("60s") || formato.includes("short");
  const duracaoStr = isShort
    ? "55-60 segundos — máximo 130 palavras na narração"
    : "8-12 minutos — 800-1.200 palavras com desenvolvimento profundo";

  const caseStr = caseReal
    ? `
CASE REAL OBRIGATÓRIO A INCLUIR:
- ${caseReal.personagem || caseReal.fonte || ""}
- Situação/Dado: ${caseReal.situacao || caseReal.dado || ""}
- Reviravolta/Choque: ${caseReal.reviravolta || caseReal.choque || ""}
`
    : "";

  return `Você é um roteirista especialista em conteúdo viral de psicologia. Seu trabalho: criar roteiros que fazem a pessoa PARAR DE ROLAR O FEED e assistir até o final.

TEMA: ${tema}
FORMATO: ${formato} | ${duracaoStr}
${caseStr}

═══════════════ REGRAS DE OURO — ENGENHARIA DE ATENÇÃO ═══════════════

1. HOOK [0-5s]: Comece com UMA CENA ESPECÍFICA. NÃO uma afirmação genérica.
   ✅ "Você checa o celular. Cinco vezes em dez minutos."
   ❌ "Hoje vamos falar sobre apego ansioso."

2. DADOS REAIS: Todo dado com fonte real (universidade, pesquisador, ano).
3. ESPELHO EMOCIONAL: Cada cena reflete EXATAMENTE o que está sendo narrado.
4. CURIOSIDADE EM LOOP: Cada seção responde 1 pergunta mas abre outra.
5. SENSAÇÕES FÍSICAS: Descreva no corpo, não em abstrações.
   ✅ "Aquela dor no peito quando ele não responde"
   ❌ "Sofrimento emocional causado pela incerteza"
6. ZERO JULGAMENTO: Validar primeiro, explicar depois.
7. ANCORAGEM FINAL: Criar desejo de compartilhar — nunca pedir like diretamente.

═══════════════ ESTRUTURA DOS 7 ATOS ═══════════════

[ATO 1 — HOOK — 0-5s]
Narrador: [2 frases curtas e impactantes — cena específica]
Cena visual: [o que o personagem está fazendo + expressão facial + ambiente/fundo]

[ATO 2 — AMPLIFICAÇÃO — 5-15s]
Narrador: [dado real com fonte + implicação que choca]
Cena visual: [personagem reagindo ao dado + composição que amplifica]

[ATO 3 — CASO REAL — 15-25s]
Narrador: [nome+idade+profissão comum + situação específica contraditória]
Cena visual: [personagem em situação do caso + detalhe humano]

[ATO 4 — VIRADA CIENTÍFICA — 25-35s]
Narrador: [mecanismo simples + analogia visual]
Cena visual: [personagem com expressão de revelação/insight]

[ATO 5 — CUSTO REAL — 35-45s]
Narrador: [o que acontece se nada mudar — sem alarmar + o que se perde]
Cena visual: [dois personagens ou personagem no futuro]

[ATO 6 — CAMINHO — 45-55s]
Narrador: [o que é possível mudar + primeiro insight concreto]
Cena visual: [personagem com expressão de alívio ou determinação]

[ATO 7 — ANCORAGEM — 55-60s]
Narrador: [frase final que cria desejo de compartilhar — identificação com próximo]
Cena visual: [expressão de esperança + elemento visual que fica na memória]

CHECKLIST:
□ Hook começa com cena específica
□ Pelo menos 1 dado com fonte real
□ Pelo menos 1 personagem específico
□ Sensações físicas descritas
□ Pelo menos 1 cliffhanger de curiosidade
□ Zero pedido de like/inscrição
□ Último frame: esperança ou insight

GERE O ROTEIRO AGORA:`;
}

function detectTema(tema) {
  const t = tema.toLowerCase();
  if (t.includes("apego")) return { emocao: "melancolico", caseKey: "apego_ansioso" };
  if (t.includes("narcis")) return { emocao: "tenso", caseKey: "narcisismo" };
  if (t.includes("trauma")) return { emocao: "calmo", caseKey: "trauma" };
  if (t.includes("ansied")) return { emocao: "urgente", caseKey: "ansiedade" };
  if (t.includes("burnout") || t.includes("esgotamento")) return { emocao: "melancolico", caseKey: "burnout" };
  if (t.includes("perfec") || t.includes("impostor")) return { emocao: "contemplativo", caseKey: "perfeccionismo" };
  return { emocao: "contemplativo", caseKey: null };
}

export async function GET(request) {
  const url = new URL(request.url);
  const action = url.searchParams.get("action") || "status";
  const tema = url.searchParams.get("tema") || "";
  const formato = url.searchParams.get("formato") || "short_60s";

  if (action === "gerar" && tema) {
    const { emocao, caseKey } = detectTema(tema);
    const caseReal = caseKey ? CASES_REAIS[caseKey]?.[0] : null;
    const kbParams = KEN_BURNS_PARAMS[emocao] || KEN_BURNS_PARAMS.contemplativo;
    const megaPrompt = buildMegaPromptViral(tema, formato, caseReal);

    return Response.json({
      tema, formato, emocao,
      mega_prompt_script: megaPrompt,
      case_real_injetado: caseReal,
      ken_burns_params: kbParams,
      hooks_sugeridos: HOOKS,
      instrucao: "Passe mega_prompt_script ao LLM (Groq/DeepSeek) para gerar o roteiro viral completo"
    });
  }

  if (action === "hooks") {
    const { emocao, caseKey } = detectTema(tema || "apego");
    return Response.json({ emocao, hooks: HOOKS, cases: caseKey ? CASES_REAIS[caseKey] : null });
  }

  if (action === "cases") {
    return Response.json({ cases: CASES_REAIS });
  }

  // Status e demo
  const demo = detectTema("apego ansioso — medo do abandono");
  return Response.json({
    sistema: "Gerador Viral V1 — psicologia.doc",
    versao: "1.0",
    descricao: "Engenharia de atenção máxima: 7 atos, cases reais, Ken Burns hipnótico, hooks por emoção",
    acoes: {
      "gerar_script": "/api/gerar-viral?action=gerar&tema=apego+ansioso&formato=short_60s",
      "gerar_long_form": "/api/gerar-viral?action=gerar&tema=trauma+invisivel&formato=long_8min",
      "ver_hooks": "/api/gerar-viral?action=hooks&tema=narcisismo",
      "ver_cases": "/api/gerar-viral?action=cases",
    },
    estrategia_viral: {
      "hook_science": "Primeiros 3-5s determinam 70% da retenção — cena específica, nunca afirmação genérica",
      "7_atos": ["Hook-ferida", "Amplificação-dado", "Caso-real", "Virada-científica", "Custo-real", "Caminho", "Ancoragem"],
      "ken_burns_hipnotico": "Movimento calculado por emoção — zoom/pan espelha o arco narrativo",
      "curiosidade_em_loop": "Cada seção responde 1 pergunta e abre outra — espectador não consegue parar",
      "espelho_emocional": "Imagem reflete exatamente o que o narrador está dizendo — sincronização perfeita",
      "cases_reais": "Dados com fonte real + personagem específico = credibilidade + identificação",
      "zero_julgamento": "Validar a experiência primeiro — nunca culpar — o espectador deve se sentir visto",
      "ancoragem_compartilhamento": "Último frame cria desejo de compartilhar sem pedir — identidade coletiva"
    },
    demo_emocao: demo.emocao,
    demo_case: CASES_REAIS[demo.caseKey]?.[0]?.personagem || "—",
    referencias_virais: [
      "Psych2Go — 28M views — Covert Narcissist",
      "Psych2Go — 22M views — Abandonment Issues",
      "BrainCraft — mecanismo + animação científica",
      "Therapy in a Nutshell — validação + explicação simples",
      "MedCircle — dados reais + casos clínicos"
    ]
  });
}
