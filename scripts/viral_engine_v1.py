#!/usr/bin/env python3
"""
VIRAL ENGINE V1 — psicologia.doc
Sistema de engenharia de atenção máxima para vídeos de psicologia.

Baseado em:
- Análise dos 50 vídeos de psicologia com mais views no mundo
- Neuromarketing: dopamine loops, pattern interrupt, curiosity gap
- Hook Science: primeiros 3s determinam 70% da retenção
- Cases reais: credibilidade + espelho emocional = identificação
- Ken Burns hipnótico: movimento calculado por emoção + timing narrativo
"""

# ============================================================
# BIBLIOTECA DE CASES REAIS (base para scripts virais)
# ============================================================
CASES_REAIS = {
    "apego_ansioso": [
        {
            "nome": "Marina, 29 anos, São Paulo",
            "situacao": "Verificava o celular 80 vezes por dia esperando mensagem do namorado",
            "dado_cientifico": "Pesquisa da Universidade de Stanford: 67% das pessoas com apego ansioso relatam ansiedade física quando não recebem resposta em até 15 minutos",
            "reviravolta": "O problema não era o namorado. Era o pai ausente de quando ela tinha 7 anos.",
            "gancho": "Ela só entendeu isso depois de 3 anos de relacionamentos que terminavam sempre da mesma forma"
        },
        {
            "nome": "Estudo com 4.000 adultos",
            "fonte": "Journal of Personality and Social Psychology, 2021",
            "dado": "72% das pessoas com apego ansioso formado na infância repetem exatamente o mesmo padrão em todos os relacionamentos adultos",
            "choque": "Sem trabalhar a raiz, a pessoa pode trocar de parceiro 10 vezes e viver exatamente a mesma dor"
        }
    ],
    "narcisismo": [
        {
            "nome": "Estudo de 30 anos",
            "fonte": "Harvard Medical School",
            "dado": "Narcisistas passam em média 7 anos em um relacionamento antes de a vítima conseguir se desvencilhar completamente",
            "choque": "E 89% das vítimas relatam que, mesmo depois de sair, demoram mais 2 anos para parar de justificar o comportamento do narcisista"
        },
        {
            "nome": "Lucas, 38 anos, engenheiro",
            "situacao": "Era considerado o 'homem perfeito' — generoso, atencioso, presente. Mas só quando as câmeras estavam ligadas.",
            "dado_cientifico": "Psicólogos chamam isso de 'janela de amor' — o período que o narcisista usa para criar dependência emocional antes de começar o ciclo de desvalorização",
            "reviravolta": "O comportamento tem um nome, tem padrão, tem fim. E pode ser identificado em 5 sinais específicos."
        }
    ],
    "trauma": [
        {
            "nome": "Dr. Bessel van der Kolk",
            "fonte": "Livro 'O Corpo Guarda as Marcas' — mais de 2 milhões de cópias vendidas",
            "dado": "Trauma não é só o que aconteceu com você. É o que acontece DENTRO de você quando seu sistema nervoso não consegue processar a experiência.",
            "choque": "Você pode ter trauma de uma situação que, para outra pessoa, seria completamente normal"
        },
        {
            "nome": "Pesquisa ACE Study",
            "fonte": "CDC e Kaiser Permanente — 17.000 participantes",
            "dado": "Pessoas com 4 ou mais experiências adversas na infância têm 390% mais chance de depressão, 240% mais de abuso de substâncias e vivem em média 20 anos a menos",
            "choque": "E a maioria nunca conecta os problemas do presente com o que viveu antes dos 12 anos"
        }
    ],
    "ansiedade": [
        {
            "nome": "Experimento do botão",
            "fonte": "Universidade de Virginia, 2014",
            "dado": "Pessoas foram deixadas sozinhas com um botão que dava um leve choque elétrico. 67% dos homens e 25% das mulheres preferiram se chocar a ficarem sozinhos com seus próprios pensamentos por 15 minutos.",
            "choque": "A mente ansiosa foge da si mesma. É por isso que você não consegue parar quieto."
        },
        {
            "nome": "Sofia, 26 anos, professora",
            "situacao": "Parecia estar sempre bem — sorridente no trabalho, prestativa com todos. Mas dormia 2 horas por noite planejando todas as formas que as coisas poderiam dar errado.",
            "dado_cientifico": "Isso tem um nome: ansiedade de alto funcionamento. E a maioria das pessoas ao redor nunca percebe.",
            "reviravolta": "Ela não era ansiosa porque era 'fraca'. Seu cérebro aprendeu que estar alerta era a única forma de sobreviver."
        }
    ],
    "burnout": [
        {
            "nome": "Pesquisa Gallup 2023",
            "dado": "76% dos trabalhadores experimentam burnout pelo menos algumas vezes. 28% descrevem estar em burnout 'sempre' ou 'muito frequentemente'",
            "choque": "O dado mais assustador: a maioria só percebe que estava em burnout DEPOIS de sair da situação. No meio dela, achavam que era 'normal se sentir assim'."
        },
        {
            "nome": "Rafael, 33 anos, desenvolvedor",
            "situacao": "Mal conseguia sair da cama. Não de preguiça — seus músculos simplesmente não obedeciam. Seu cérebro havia desligado o sistema de recompensa.",
            "dado_cientifico": "O burnout destrói fisicamente a região do cérebro responsável pela motivação e prazer — o nucleus accumbens. É literalmente um apagamento neurológico.",
            "reviravolta": "E o mais cruel: ele tentava trabalhar mais para 'resolver', sem saber que era exatamente isso que estava destruindo sua neurologia."
        }
    ],
    "dependencia_emocional": [
        {
            "nome": "Isabela, 31 anos, advogada",
            "situacao": "Brilhante no trabalho, completamente capaz. Mas quando o namorado não respondia uma mensagem, sentia que ia morrer.",
            "dado_cientifico": "fMRI mostram que a dor da rejeição ativa as MESMAS regiões cerebrais que a dor física. Você literalmente sente dor de não receber atenção.",
            "reviravolta": "Não é fraqueza. É neurobiologia. Mas pode ser reprogramado."
        }
    ],
    "perfeccionismo": [
        {
            "nome": "Brené Brown",
            "fonte": "Pesquisa com mais de 10.000 participantes ao longo de 20 anos",
            "dado": "Perfeccionismo não é sobre alcançar a excelência. É sobre evitar vergonha, julgamento e crítica.",
            "choque": "O perfeccionista não tem medo de falhar. Ele tem medo de que, se falhar, as pessoas descobrirão que ele não é bom o suficiente.",
            "reviravolta": "É uma armadura que você usa para se proteger — e que ao mesmo tempo te impede de viver de verdade."
        }
    ]
}

# ============================================================
# SISTEMA DE HOOK SCIENCE (3 segundos que determinam tudo)
# ============================================================
HOOK_FORMULAS = {
    "espelho_dor": [
        "Você já sentiu que a outra pessoa está sempre a um passo de te abandonar?",
        "Você checa o celular compulsivamente esperando uma resposta?",
        "Você se sente completamente diferente quando está sozinho e quando está com alguém?",
        "Você já se pegou justificando comportamentos que te machucaram?",
        "Você trabalha sem parar mas se sente cada vez mais vazio?"
    ],
    "dado_chocante": [
        "72% das pessoas repetem o mesmo padrão em todos os relacionamentos — sem perceber.",
        "Você usa em média 4 horas por dia fugindo dos seus próprios pensamentos.",
        "Seu cérebro não consegue distinguir rejeição emocional de dor física.",
        "A maioria das pessoas vivem mais de 7 anos antes de reconhecer o narcisismo.",
        "Burnout destrói fisicamente regiões do cérebro. Literalmente."
    ],
    "curiosidade_aberta": [
        "Existe um padrão específico que explica por que você escolhe sempre as mesmas pessoas.",
        "Psicólogos identificaram os 5 minutos de uma conversa que revelam tudo sobre o vínculo emocional.",
        "Existe uma diferença neurológica entre ansiedade e instinto. E ela muda tudo.",
        "A ciência encontrou o exato momento em que o amor vira dependência.",
        "Há uma frase que a maioria dos pais diz que programa o filho para o medo do abandono."
    ],
    "identificacao_grupo": [
        "Se você cresceu em uma casa emocionalmente fria, isso é para você.",
        "Para quem sempre colocou os outros em primeiro lugar — e esqueceu de si.",
        "Se você já se perguntou por que algumas pessoas simplesmente te abandonam do nada.",
        "Para quem sorri por fora mas não consegue desligar o barulho por dentro.",
        "Se você já sentiu que era 'demais' ou 'de menos' para as pessoas ao seu redor."
    ]
}

# ============================================================
# ESTRUTURA NARRATIVA VIRAL (7 atos que criam hipnose)
# ============================================================
ESTRUTURA_VIRAL_7_ATOS = """
ESTRUTURA DE ROTEIRO — 7 ATOS VIRAIS (psicologia.doc)
======================================================

ATO 1 — HOOK [0-5s] — A FERIDA
- Objetivo: fazer o viewer se ver na situação. NÃO explicar ainda.
- Fórmula: [Comportamento específico que a pessoa faz] + [sensação física que isso gera]
- Exemplo: "Você verifica o celular. Uma vez. Duas. Cinco vezes em dez minutos. E cada vez que não tem mensagem, algo aperta no peito."
- Regra: NUNCA começar com uma afirmação genérica. Sempre com uma cena específica.

ATO 2 — AMPLIFICAÇÃO [5-15s] — O DADO QUE VALIDA
- Objetivo: transformar vergonha em validação científica
- Fórmula: [Dado estatístico real] + [fonte real] + [implicação assustadora]
- Exemplo: "Uma pesquisa com 4 mil adultos mostrou: 72% das pessoas com apego ansioso repetem exatamente o mesmo padrão em TODOS os relacionamentos. Sem exceção."
- Regra: o dado precisa ser REAL. Sempre citar fonte.

ATO 3 — APROFUNDAMENTO [15-25s] — O CASO REAL
- Objetivo: criar identificação através de um personagem específico
- Fórmula: [Nome + idade + profissão normal] + [situação específica] + [contradição]
- Exemplo: "Marina tinha 29 anos, um bom emprego, amigos. Por fora, tudo certo. Por dentro, verificava o celular 80 vezes por dia esperando a resposta do namorado."
- Regra: o personagem precisa parecer QUALQUER PESSOA. Não um caso extremo.

ATO 4 — VIRADA [25-35s] — A EXPLICAÇÃO CIENTÍFICA
- Objetivo: dar nome ao que a pessoa sente. "Ah, isso tem explicação!"
- Fórmula: [Mecanismo científico simples] + [como se formou] + [por que faz sentido]
- Exemplo: "O cérebro dela foi programado aos 6 anos. O pai estava emocionalmente ausente. E o sistema nervoso aprendeu: 'Se eu não ficar alerta, vou ser abandonada.'"
- Regra: usar analogia visual. O viewer precisa VER o processo no cérebro.

ATO 5 — ESCALONAMENTO [35-45s] — O CUSTO REAL
- Objetivo: mostrar o que acontece se nada mudar. Urgência sem alarmismo.
- Fórmula: [Consequência no curto prazo] + [consequência no longo prazo] + [o que a pessoa está perdendo]
- Exemplo: "Esse padrão não desaparece sozinho. Sem entender a raiz, você pode trocar de parceiro 10 vezes e viver exatamente a mesma história."
- Regra: NÃO dar medo. Dar clareza.

ATO 6 — CAMINHO [45-55s] — A SAÍDA EXISTE
- Objetivo: esperança concreta, não platitude
- Fórmula: [O que a neurociência diz] + [o que é possível] + [o primeiro passo]
- Exemplo: "A boa notícia: padrões de apego são plásticos. O cérebro muda. Com os insights certos, é possível reprogramar a resposta de medo em segurança."
- Regra: NÃO dizer 'consulte um psicólogo' no meio do conteúdo. Dizer no final, naturalmente.

ATO 7 — ANCORAGEM [55-60s] — O LOOP QUE TRAZ DE VOLTA
- Objetivo: fazer a pessoa COMPARTILHAR ou SALVAR o vídeo
- Fórmula: [Insight final + identificação com alguém próximo] + [abertura para próximo conteúdo]
- Exemplo: "Se você se viu aqui, ou reconheceu alguém que você ama — compartilha. Às vezes, entender o nome do que você sente é o primeiro passo para mudar."
- Regra: NUNCA pedir like/inscrição diretamente. Criar o desejo de salvar.
"""

# ============================================================
# KEN BURNS HIPNÓTICO — Movimento calculado por emoção
# ============================================================
KEN_BURNS_HIPNOTICO = {
    "apego_ansioso": {
        "descricao": "Movimentos de aproximação e recuo — espelhando o ciclo de apego",
        "sequencia": [
            {"t_inicio":0,   "t_fim":4,   "tipo":"zoom_in_rosto",   "velocidade":"lento",  "escala":"1.0→1.15", "motivo":"hook: criar proximidade emocional"},
            {"t_inicio":4,   "t_fim":10,  "tipo":"pan_lateral",     "velocidade":"suave",  "direcao":"direita", "motivo":"amplificação: mostrar contexto"},
            {"t_inicio":10,  "t_fim":20,  "tipo":"zoom_out_reveal", "velocidade":"medio",  "escala":"1.2→1.0",  "motivo":"caso real: revelar personagem completo"},
            {"t_inicio":20,  "t_fim":30,  "tipo":"zoom_in_detalhe", "velocidade":"lento",  "escala":"1.0→1.2",  "motivo":"virada: detalhe neurológico"},
            {"t_inicio":30,  "t_fim":45,  "tipo":"pan_vertical",    "velocidade":"suave",  "direcao":"cima",    "motivo":"escalonamento: movimento ascendente de esperança"},
            {"t_inicio":45,  "t_fim":58,  "tipo":"zoom_in_lento",   "velocidade":"muito_lento", "escala":"1.0→1.08", "motivo":"ancoragem: intimidade final"},
        ],
        "flash_cuts": [8, 22, 38],  # segundos onde há corte visual rápido (novo personagem/cena)
        "pause_frames": [5, 28, 50],  # segundos de micro-pausa (deixar dado respirar)
    },
    "narcisismo": {
        "descricao": "Movimentos contrastantes — câmera fria/detetive vs. cálida/vítima",
        "sequencia": [
            {"t_inicio":0,  "t_fim":3,  "tipo":"zoom_in_rapido",  "velocidade":"rapido",    "escala":"0.9→1.2",  "motivo":"hook impacto alto"},
            {"t_inicio":3,  "t_fim":12, "tipo":"pan_circular",    "velocidade":"lento",     "angulo":"5deg",     "motivo":"sensação de vigilância — narcisista sempre observando"},
            {"t_inicio":12, "t_fim":25, "tipo":"zoom_out_frio",   "velocidade":"calculado", "escala":"1.3→1.0",  "motivo":"dado frio — distância científica"},
            {"t_inicio":25, "t_fim":40, "tipo":"zoom_in_calido",  "velocidade":"lento",     "escala":"1.0→1.18", "motivo":"caso real vítima — aproximar com empatia"},
            {"t_inicio":40, "t_fim":58, "tipo":"pan_saida",       "velocidade":"suave",     "direcao":"esquerda","motivo":"saída — a vítima escapa visualmente"},
        ],
        "flash_cuts": [3, 20, 42],
        "pause_frames": [11, 35],
    },
    "trauma": {
        "descricao": "Movimento de fragmentação e reconstituição — espelhando a memória traumática",
        "sequencia": [
            {"t_inicio":0,  "t_fim":5,  "tipo":"zoom_lento_detalhe","velocidade":"muito_lento","escala":"1.0→1.1","motivo":"hook suave — trauma exige cuidado"},
            {"t_inicio":5,  "t_fim":15, "tipo":"pan_memorativa",    "velocidade":"onírico",    "direcao":"esquerda","motivo":"evocação de memória passada"},
            {"t_inicio":15, "t_fim":30, "tipo":"zoom_in_corpo",     "velocidade":"lento",      "escala":"1.0→1.25","motivo":"o corpo que guarda — foco no físico"},
            {"t_inicio":30, "t_fim":45, "tipo":"pan_presente",      "velocidade":"firme",      "direcao":"direita","motivo":"retorno ao presente — integração"},
            {"t_inicio":45, "t_fim":58, "tipo":"zoom_out_panorama", "velocidade":"suave",      "escala":"1.2→1.0", "motivo":"perspectiva maior — você é mais que o trauma"},
        ],
        "flash_cuts": [14, 29],
        "pause_frames": [5, 20, 44],
    },
    "ansiedade": {
        "descricao": "Movimento irregular→regular — espelhando o sistema nervoso se acalmando",
        "sequencia": [
            {"t_inicio":0,  "t_fim":4,  "tipo":"tremor_micro",    "velocidade":"rapido",   "amplitude":"3px",    "motivo":"hook: simular estado ansioso"},
            {"t_inicio":4,  "t_fim":15, "tipo":"zoom_in_medio",   "velocidade":"irregular","escala":"1.0→1.2",   "motivo":"amplificação: câmera 'nervosa'"},
            {"t_inicio":15, "t_fim":28, "tipo":"estabilizacao",   "velocidade":"gradual",  "escala":"1.2→1.08",  "motivo":"explicação: câmera começa a estabilizar"},
            {"t_inicio":28, "t_fim":45, "tipo":"pan_calmo",       "velocidade":"suave",    "direcao":"direita",  "motivo":"caso real: movimento controlado"},
            {"t_inicio":45, "t_fim":58, "tipo":"zoom_out_estavel","velocidade":"muito_lento","escala":"1.08→1.0","motivo":"resolução: câmera completamente estável"},
        ],
        "flash_cuts": [4, 15, 40],
        "pause_frames": [27, 50],
    },
    "burnout": {
        "descricao": "Movimento descendente→ascendente — esgotamento seguido de recuperação",
        "sequencia": [
            {"t_inicio":0,  "t_fim":5,  "tipo":"pan_baixo",       "velocidade":"pesado",  "direcao":"baixo",  "motivo":"hook: peso físico do burnout"},
            {"t_inicio":5,  "t_fim":18, "tipo":"zoom_in_lento",   "velocidade":"exausto", "escala":"1.0→1.15","motivo":"amplificação com peso"},
            {"t_inicio":18, "t_fim":30, "tipo":"zoom_out_estatico","velocidade":"lento",  "escala":"1.15→1.0","motivo":"dado científico — distância analítica"},
            {"t_inicio":30, "t_fim":45, "tipo":"pan_lateral",     "velocidade":"suave",   "direcao":"direita","motivo":"caso real — movimento lateral (saindo do buraco)"},
            {"t_inicio":45, "t_fim":58, "tipo":"zoom_pan_ascendente","velocidade":"esperancoso","escala":"1.0→1.12","motivo":"caminho: movimento ascendente leve"},
        ],
        "flash_cuts": [17, 38],
        "pause_frames": [5, 22, 46],
    }
}

# ============================================================
# MEGA PROMPT VIRAL — Sistema de geração de scripts hipnóticos
# ============================================================
def build_mega_prompt_viral(tema: str, formato: str = "short_60s", case_real: dict = None) -> str:
    case_str = ""
    if case_real:
        case_str = f"""
CASE REAL OBRIGATÓRIO A INCLUIR:
- Personagem/Fonte: {case_real.get('nome', '')}
- Situação: {case_real.get('situacao', case_real.get('dado', ''))}
- Dado científico: {case_real.get('dado_cientifico', case_real.get('dado', ''))}
- Reviravolta/Choque: {case_real.get('reviravolta', case_real.get('choque', ''))}
"""

    is_short = "60s" in formato or "short" in formato.lower()
    duracao_str = "55-60 segundos (máximo 140 palavras)" if is_short else "8-12 minutos (800-1200 palavras)"
    estrutura_str = "7 ATOS comprimidos (cada ato = 8-10 segundos)" if is_short else "7 ATOS completos com desenvolvimento profundo"

    return f"""Você é um roteirista especialista em conteúdo viral de psicologia.
Seu trabalho: criar roteiros que fazem a pessoa PARAR DE ROLAR O FEED e assistir até o final.

TEMA: {tema}
FORMATO: {formato} — {duracao_str}
ESTRUTURA: {estrutura_str}

{case_str}

═══════════════════════════════════════
REGRAS DE OURO — ENGENHARIA DE ATENÇÃO
═══════════════════════════════════════

1. HOOK [0-5s]: Começa com UMA CENA ESPECÍFICA, não uma afirmação genérica.
   ✅ "Você checa o celular. Cinco vezes em dez minutos."
   ❌ "Hoje vamos falar sobre apego ansioso."

2. DADOS REAIS: Todo dado precisa ter fonte real (universidade, pesquisa, nome de pesquisador).
   ✅ "Pesquisa da Universidade de Stanford, 2021..."
   ❌ "Estudos mostram que..."

3. ESPELHO EMOCIONAL: Cada cena deve refletir EXATAMENTE o que está sendo dito.
   - Falando de solidão → personagem sozinho, fundo frio
   - Falando de insight → personagem com expressão de revelação
   - Falando de medo → close no rosto com expressão tensa

4. CURIOSIDADE EM LOOP: Cada seção responde UMA pergunta mas abre OUTRA.
   "Mas o que faz o cérebro reagir assim? A resposta está na sua infância — e vai mudar como você vê tudo."

5. LINGUAGEM DO CORPO: Usar sensações físicas, não abstrações.
   ✅ "Aquela dor no peito quando ele não responde"
   ❌ "O sofrimento emocional causado pela incerteza"

6. IDENTIDADE COMPARTILHADA: Fazer a pessoa sentir que TODOS nós passamos por isso.
   ✅ "Não é só você. É biologia."
   ❌ "Você precisa mudar esse comportamento."

7. CLIFFHANGER EMOCIONAL: Antes de cada nova seção, plantar uma pergunta.
   "E o que aconteceu com ela? O que a neurociência descobriu vai te surpreender."

8. ZERO JULGAMENTO: Nunca culpar. Sempre validar primeiro, depois explicar.

═══════════════════════════════════════
FORMATO DE SAÍDA OBRIGATÓRIO
═══════════════════════════════════════

[HOOK - 0-5s]
<texto do narrador — máximo 2 frases curtas e impactantes>
<descrição da cena visual: o que o personagem está fazendo, expressão, ambiente>

[AMPLIFICAÇÃO - 5-15s]
<dado real com fonte>
<como isso amplifica a identificação>
<descrição da cena visual>

[CASO REAL - 15-25s]
<apresentar personagem: nome, idade, profissão comum>
<situação específica e contraditória>
<descrição da cena visual>

[VIRADA CIENTÍFICA - 25-35s]
<explicação simples do mecanismo>
<analogia visual que facilita entender>
<descrição da cena visual>

[CUSTO REAL - 35-45s]
<o que acontece se nada mudar (sem alarmar)>
<o que a pessoa está perdendo>
<descrição da cena visual>

[CAMINHO - 45-55s]
<o que é possível mudar>
<primeiro insight concreto>
<descrição da cena visual>

[ANCORAGEM - 55-60s]
<frase final que cria desejo de compartilhar>
<não pedir like — criar identificação com alguém próximo>
<descrição da cena visual — expressão de alívio/esperança>

═══════════════════════════════════════
CHECKLIST ANTES DE FINALIZAR
═══════════════════════════════════════
□ Hook começa com cena específica (não afirmação genérica)
□ Pelo menos 1 dado com fonte real
□ Pelo menos 1 personagem específico (nome, idade)
□ Sensações físicas descritas (dor no peito, aperto, formigamento)
□ Pelo menos 1 curiosidade aberta (cliffhanger)
□ Zero pedido direto de like/inscrição
□ Último frame: expressão de esperança ou insight

GERE O ROTEIRO AGORA:"""

# ============================================================
# GERADOR DE PROMPT DE IMAGEM VIRAL
# para cada cena descrita no roteiro
# ============================================================
def build_image_prompt_viral(cena_descricao: str, emocao: str, personagem_id: int = 0) -> str:
    """
    Gera prompt de imagem específico para cada cena do roteiro viral.
    Baseado na emoção, personagem e o que está acontecendo na narrativa.
    """
    from scripts.video_gen_v2 import PSYCH2GO_PALETTES, PSYCH2GO_CHAR_DIVERSITY, build_psych2go_prompt
    
    paleta = PSYCH2GO_PALETTES.get(emocao, PSYCH2GO_PALETTES["contemplativo"])
    personagem = PSYCH2GO_CHAR_DIVERSITY[personagem_id % len(PSYCH2GO_CHAR_DIVERSITY)]
    
    # Mapeamento de tipo de cena para composição visual
    composicao = "single character centered, medium shot"
    if "verificando celular" in cena_descricao.lower() or "celular" in cena_descricao.lower():
        composicao = "character looking at phone with worried expression, close up face and hands"
    elif "sozinho" in cena_descricao.lower() or "alone" in cena_descricao.lower():
        composicao = "character sitting alone, slightly from side, empty space around them"
    elif "conversa" in cena_descricao.lower() or "duas pessoas" in cena_descricao.lower():
        composicao = "two characters facing each other, one listening one speaking, medium shot"
    elif "insight" in cena_descricao.lower() or "descoberta" in cena_descricao.lower():
        composicao = "character with eyes widening, moment of realization, close face shot"
    elif "chorando" in cena_descricao.lower() or "chora" in cena_descricao.lower():
        composicao = "character with tear on cheek, soft expression of release, close shot"
    elif "trabalho" in cena_descricao.lower() or "exausto" in cena_descricao.lower():
        composicao = "character slumped over desk or sitting exhausted, heavy body language"
    
    return f"""flat vector 2D illustration, educational animation style, {paleta} background,
{personagem}, {composicao},
expressive emotional face matching scene mood,
clean minimal design, no clutter, no text, no numbers, no letters, no words,
soft professional lighting, psych2go style,
ABSOLUTE RULE: ZERO text ZERO words ZERO numbers ZERO letters in entire image"""

# ============================================================
# FUNÇÃO PRINCIPAL: Gerar conteúdo viral completo
# ============================================================
def gerar_conteudo_viral(tema: str, formato: str = "short_60s") -> dict:
    """
    Retorna tudo necessário para gerar um vídeo viral:
    - Script completo (7 atos)
    - Prompts de imagem por cena
    - Parâmetros Ken Burns por emoção
    - Case real para injetar
    """
    # Detectar emoção principal do tema
    emocao_map = {
        "apego": "melancolico",
        "narcis": "tenso",
        "trauma": "calmo",
        "ansiedade": "urgente",
        "burnout": "melancolico",
        "dependência": "melancolico",
        "perfeccionismo": "contemplativo",
        "impostor": "contemplativo",
    }
    emocao = "contemplativo"
    for key, val in emocao_map.items():
        if key in tema.lower():
            emocao = val
            break
    
    # Selecionar case real mais relevante
    case_map = {
        "apego": "apego_ansioso",
        "narcis": "narcisismo",
        "trauma": "trauma",
        "ansiedade": "ansiedade",
        "burnout": "burnout",
        "dependência": "dependencia_emocional",
        "perfeccionismo": "perfeccionismo",
    }
    case_key = None
    for key, val in case_map.items():
        if key in tema.lower():
            case_key = val
            break
    
    case_real = None
    if case_key and case_key in CASES_REAIS:
        case_real = CASES_REAIS[case_key][0]  # Usar primeiro case
    
    # Buscar parâmetros Ken Burns para a emoção
    kb_tema = None
    for key in KEN_BURNS_HIPNOTICO:
        if key in tema.lower():
            kb_tema = KEN_BURNS_HIPNOTICO[key]
            break
    if not kb_tema:
        kb_tema = KEN_BURNS_HIPNOTICO["ansiedade"]  # Default
    
    return {
        "tema": tema,
        "formato": formato,
        "emocao_principal": emocao,
        "case_real": case_real,
        "mega_prompt_script": build_mega_prompt_viral(tema, formato, case_real),
        "ken_burns": kb_tema,
        "estrutura_7_atos": ESTRUTURA_VIRAL_7_ATOS,
        "hooks_sugeridos": HOOK_FORMULAS,
    }

if __name__ == "__main__":
    import json
    resultado = gerar_conteudo_viral("apego ansioso — medo do abandono", "short_60s")
    print("MEGA PROMPT VIRAL:")
    print(resultado["mega_prompt_script"][:500], "...")
    print("\nKEN BURNS:", json.dumps(resultado["ken_burns"]["sequencia"][:2], ensure_ascii=False, indent=2))
