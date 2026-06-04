#!/usr/bin/env python3
"""
seo_global_v1.py — Motor SEO Global para domínio de buscas mundial
FUNÇÕES EXPORTADAS:
  - get_seo_package(topic, lang, hour_utc) → {title, description, tags, hashtags}
  - get_live_seo(hour_utc) → {title, description, tags} para live atual
  - score_seo_package(pkg) → int 0-100 (qualidade SEO)
"""
# ─── BANCO DE KEYWORDS POR IDIOMA ──────────────────────────────────────────
KEYWORDS = {
    "pt": {
        "primary": ["narcisismo","psicologia","trauma","ansiedade","apego","autoconhecimento",
                    "comportamento humano","saúde mental","narcisista","gaslighting"],
        "secondary": ["narcisismo encoberto","trauma de infância","ansiedade social",
                      "apego ansioso","depressão silenciosa","manipulação psicológica",
                      "abuso emocional","relacionamento tóxico","cura emocional","autoestima"],
        "trending": ["dark psychology","psicologia quântica","neurociência","binaural 432hz",
                     "frequência 432hz","psicologia do trauma","teoria do apego","síndrome do impostor"],
        "longtail": ["como identificar um narcisista encoberto","sinais de trauma de infância no adulto",
                     "como sair de um relacionamento tóxico","o que é gaslighting na prática",
                     "ansiedade social como superar","depressão silenciosa sinais"],
        "binaural": ["432hz","binaural 432hz","frequências binaurais","ondas delta sono",
                     "meditação profunda","foco e concentração","binaural psicologia"],
        "cta": "Ative o sino 🔔 e descubra os próximos estudos!"
    },
    "en": {
        "primary": ["narcissism","psychology","trauma","anxiety","attachment","self-awareness",
                    "human behavior","mental health","narcissist","dark psychology"],
        "secondary": ["covert narcissism","childhood trauma","social anxiety",
                      "anxious attachment","silent depression","psychological manipulation",
                      "emotional abuse","toxic relationship","emotional healing","self-esteem"],
        "trending": ["dark psychology","quantum psychology","neuroscience","binaural beats 432hz",
                     "432hz frequency","trauma psychology","attachment theory","impostor syndrome"],
        "longtail": ["how to identify a covert narcissist","signs of childhood trauma in adults",
                     "how to leave a toxic relationship","what is gaslighting in practice",
                     "social anxiety how to overcome","silent depression signs 2024"],
        "binaural": ["432hz","binaural beats 432hz","binaural frequencies","delta waves sleep",
                     "deep meditation","focus and concentration","psychology binaural beats"],
        "cta": "Hit the bell 🔔 to never miss a new study!"
    },
    "de": {
        "primary": ["narzissmus","psychologie","trauma","angst","bindung","selbsterkenntnis",
                    "menschliches verhalten","mentale gesundheit","narzisst","dunkle psychologie"],
        "secondary": ["verdeckter narzissmus","kindheitstrauma","soziale angst",
                      "ängstliche bindung","stille depression","psychologische manipulation",
                      "emotionaler missbrauch","toxische beziehung","emotionale heilung","selbstwert"],
        "trending": ["dunkle psychologie","quantenpsychologie","neurowissenschaften","binaural 432hz",
                     "432hz frequenz","traumapsychologie","bindungstheorie","hochstapler-syndrom"],
        "longtail": ["wie erkenne ich einen verdeckten narzissten","zeichen von kindheitstrauma beim erwachsenen",
                     "wie verlasse ich eine toxische beziehung","was ist gaslighting"],
        "binaural": ["432hz","binaurale schwebungen 432hz","binaurale frequenzen","delta-wellen schlaf",
                     "tiefe meditation","fokus und konzentration","psychologie binaural"],
        "cta": "Glocke aktivieren 🔔 und keine Studie verpassen!"
    },
    "es": {
        "primary": ["narcisismo","psicología","trauma","ansiedad","apego","autoconocimiento",
                    "comportamiento humano","salud mental","narcisista","psicología oscura"],
        "secondary": ["narcisismo encubierto","trauma infantil","ansiedad social",
                      "apego ansioso","depresión silenciosa","manipulación psicológica",
                      "abuso emocional","relación tóxica","sanación emocional","autoestima"],
        "trending": ["psicología oscura","psicología cuántica","neurociencia","binaural 432hz",
                     "frecuencia 432hz","psicología del trauma","teoría del apego","síndrome del impostor"],
        "longtail": ["cómo identificar a un narcisista encubierto","señales de trauma infantil en adultos",
                     "cómo salir de una relación tóxica","qué es el gaslighting"],
        "binaural": ["432hz","binaural 432hz","frecuencias binaurales","ondas delta sueño",
                     "meditación profunda","concentración y enfoque","psicología binaural"],
        "cta": "Activa la campana 🔔 para no perderte ningún estudio!"
    },
    "fr": {
        "primary": ["narcissisme","psychologie","trauma","anxiété","attachement","conscience de soi",
                    "comportement humain","santé mentale","narcissique","psychologie sombre"],
        "secondary": ["narcissisme masqué","trauma d'enfance","anxiété sociale",
                      "attachement anxieux","dépression silencieuse","manipulation psychologique",
                      "abus émotionnel","relation toxique","guérison émotionnelle","estime de soi"],
        "trending": ["psychologie sombre","psychologie quantique","neurosciences","binaural 432hz",
                     "fréquence 432hz","psychologie du trauma","théorie de l'attachement"],
        "longtail": ["comment identifier un narcissique masqué","signes de trauma d'enfance chez l'adulte"],
        "binaural": ["432hz","binaural 432hz","fréquences binaurales","ondes delta sommeil",
                     "méditation profonde","concentration et focus","psychologie binaural"],
        "cta": "Activez la cloche 🔔 pour ne manquer aucune étude!"
    },
    "it": {
        "primary": ["narcisismo","psicologia","trauma","ansia","attaccamento","autoconsapevolezza",
                    "comportamento umano","salute mentale","narcisista","psicologia oscura"],
        "secondary": ["narcisismo mascherato","trauma infantile","ansia sociale",
                      "attaccamento ansioso","depressione silenziosa","manipolazione psicologica"],
        "binaural": ["432hz","binaural 432hz","frequenze binaurali","onde delta sonno",
                     "meditazione profonda","concentrazione"],
        "cta": "Attiva la campanella 🔔 per non perdere nessuno studio!"
    },
    "ja": {
        "primary": ["ナルシシズム","心理学","トラウマ","不安","愛着","自己認識",
                    "人間行動","メンタルヘルス","ナルシスト","ダーク心理学"],
        "secondary": ["隠れたナルシスト","幼少期のトラウマ","社会不安",
                      "不安定型愛着","無音の鬱","心理的操作"],
        "binaural": ["432hz","バイノーラルビート","デルタ波","瞑想","集中力"],
        "cta": "🔔ベルをオンにして最新の研究を逃さないでください!"
    },
    "ko": {
        "primary": ["나르시시즘","심리학","트라우마","불안","애착","자기인식",
                    "인간행동","정신건강","나르시스트","다크 심리학"],
        "secondary": ["은밀한 나르시스트","어린 시절 트라우마","사회불안",
                      "불안 애착","침묵의 우울","심리적 조종"],
        "binaural": ["432hz","바이노럴 비트","델타파","명상","집중력"],
        "cta": "🔔벨을 눌러 최신 연구를 놓치지 마세요!"
    }
}

# ─── TÍTULOS VIRAIS POR IDIOMA E HORÁRIO ───────────────────────────────────
# Formato: {idioma: {tipo_topico: [lista de títulos com CTR alto]}}
TITULOS = {
    "pt": {
        "narcisismo": [
            "Narcisista Encoberto: 7 Sinais Que Você Está Sendo Manipulado AGORA",
            "O Que o Narcisista Faz Quando Descobre Que Você Sabe Quem Ele É",
            "3 Frases Que TODO Narcisista Diz — Reconheça Antes Que Seja Tarde",
            "Por Que o Narcisista Volta Sempre? A Ciência de Harvard Explica",
            "Narcisismo Encoberto: A Manipulação Invisível Que Destrói Sua Sanidade",
        ],
        "trauma": [
            "Seu Corpo Guarda o Trauma Que Sua Mente Esqueceu — van der Kolk",
            "7 Sinais Que Você Tem Trauma de Infância (e Não Sabia)",
            "Por Que Você Sabota Sua Própria Felicidade? A Ciência Responde",
            "Trauma de Infância: Como o Passado Controla Suas Decisões de Hoje",
            "O Trauma Que Você Não Lembra Está Destruindo Seus Relacionamentos",
        ],
        "ansiedade": [
            "Ansiedade Alta Função: Você Parece Bem Mas Por Dentro Está Destruído",
            "7 Sinais de Ansiedade Que Passam Despercebidos (o #3 é Chocante)",
            "Por Que Sua Ansiedade Piora à Noite? A Neurociência Explica",
            "Ansiedade Social: O Medo de Ser Julgado Que Paralisa Sua Vida",
        ],
        "apego": [
            "Apego Ansioso: Por Que Você Sempre Tem Medo de Ser Abandonado",
            "Teoria do Apego: Como Sua Infância Sabotou Seus Relacionamentos",
            "3 Padrões de Apego Que Explicam TUDO Sobre Seus Relacionamentos",
        ],
        "binaural": [
            "ψ 432Hz + Psicologia | Foco Profundo | Estudo e Trabalho 24h",
            "ψ Binaural 40Hz | Concentração Máxima | Psicologia da Mente",
            "ψ 528Hz + Cura Emocional | Psicologia Quântica | 24h AO VIVO",
        ]
    },
    "en": {
        "narcissism": [
            "Covert Narcissist: 7 Signs You're Being Manipulated RIGHT NOW",
            "What Narcissists Do When They Find Out You've Figured Them Out",
            "3 Phrases EVERY Narcissist Says — Harvard Psychology Research",
            "Why Narcissists Always Come Back: The Science Behind It",
            "Covert Narcissism: The Invisible Manipulation That Destroys Your Mind",
        ],
        "trauma": [
            "Your Body Keeps the Score — Signs Your Body Holds Hidden Trauma",
            "7 Signs You Have Childhood Trauma (You Might Not Realize #3)",
            "Why You Sabotage Your Own Happiness: The Psychology Behind It",
            "Childhood Trauma: How Your Past Controls Your Decisions Today",
        ],
        "anxiety": [
            "High-Functioning Anxiety: You Look Fine But Inside You're Broken",
            "7 Signs of Anxiety That Go Unnoticed (Harvard Research)",
            "Why Your Anxiety Gets Worse at Night: Neuroscience Explains",
        ],
        "binaural": [
            "ψ 432Hz Binaural + Dark Psychology | Deep Focus | 24h LIVE",
            "ψ 40Hz Binaural | Maximum Concentration | Psychology of the Mind",
            "ψ 528Hz + Emotional Healing | Quantum Psychology | 24h LIVE",
        ]
    },
    "de": {
        "narzissmus": [
            "Verdeckter Narzisst: 7 Zeichen, dass du JETZT manipuliert wirst",
            "Was Narzissten tun, wenn sie merken, dass du sie durchschaut hast",
            "3 Sätze, die JEDER Narzisst sagt — Harvard-Psychologie-Forschung",
        ],
        "binaural": [
            "ψ 432Hz Binaural + Dunkle Psychologie | Tiefes Fokus | 24h LIVE",
            "ψ 40Hz Binaural | Maximale Konzentration | Psychologie des Geistes",
        ]
    },
    "es": {
        "narcisismo": [
            "Narcisista Encubierto: 7 señales de que te manipulan AHORA MISMO",
            "Qué hace el narcisista cuando descubre que lo has descubierto",
            "3 frases que dice TODO narcisista — Investigación de Harvard",
        ],
        "binaural": [
            "ψ 432Hz Binaural + Psicología Oscura | Foco Profundo | 24h EN VIVO",
        ]
    }
}

# ─── PAÍSES E TIMEZONES PARA PUBLICAÇÃO ────────────────────────────────────
PAISES_CPM = {
    # (país, timezone_offset_utc, CPM_medio, idioma_primario)
    "US": ( "United States",   -5,  18.0, "en"),
    "DE": ( "Germany",         +1,  14.0, "de"),
    "GB": ( "United Kingdom",   0,  12.0, "en"),
    "CA": ( "Canada",          -5,  12.0, "en"),
    "AU": ( "Australia",      +10,  11.0, "en"),
    "AT": ( "Austria",         +1,  11.0, "de"),
    "CH": ( "Switzerland",     +1,  11.0, "de"),
    "FR": ( "France",          +1,   9.0, "fr"),
    "NL": ( "Netherlands",     +1,   9.0, "en"),
    "SE": ( "Sweden",          +1,   9.0, "en"),
    "NO": ( "Norway",          +1,   9.0, "en"),
    "DK": ( "Denmark",         +1,   9.0, "en"),
    "IT": ( "Italy",           +1,   8.0, "it"),
    "ES": ( "Spain",           +1,   7.0, "es"),
    "JP": ( "Japan",           +9,   7.0, "ja"),
    "NZ": ( "New Zealand",    +12,   7.0, "en"),
    "SG": ( "Singapore",       +8,   6.0, "en"),
    "HK": ( "Hong Kong",       +8,   6.0, "en"),
    "KR": ( "South Korea",     +9,   5.0, "ko"),
    "MX": ( "Mexico",          -6,   4.0, "es"),
    "AR": ( "Argentina",       -3,   3.0, "es"),
    "BR": ( "Brazil",          -3,   2.5, "pt"),
    "CL": ( "Chile",           -4,   3.0, "es"),
    "CO": ( "Colombia",        -5,   3.0, "es"),
    "PT": ( "Portugal",         0,   4.0, "pt"),
    "PL": ( "Poland",          +1,   4.0, "en"),
    "CZ": ( "Czech Republic",  +1,   4.0, "en"),
    "RO": ( "Romania",         +2,   3.0, "en"),
    "IN": ( "India",         +5.5,   2.0, "en"),
    "PH": ( "Philippines",     +8,   2.0, "en"),
    "MY": ( "Malaysia",        +8,   2.0, "en"),
    "ID": ( "Indonesia",       +7,   1.5, "en"),
    "TH": ( "Thailand",        +7,   2.0, "en"),
    "VN": ( "Vietnam",         +7,   1.5, "en"),
    "NG": ( "Nigeria",          +1,   1.5, "en"),
    "ZA": ( "South Africa",    +2,   2.5, "en"),
    "EG": ( "Egypt",           +2,   1.5, "en"),
    "SA": ( "Saudi Arabia",    +3,   3.0, "en"),
    "AE": ( "UAE",             +4,   4.0, "en"),
    "IL": ( "Israel",          +2,   4.0, "en"),
    "TR": ( "Turkey",          +3,   2.0, "en"),
    "UA": ( "Ukraine",         +2,   2.0, "en"),
    "RU": ( "Russia",          +3,   2.0, "en"),
}

def get_paises_ativos(hour_utc):
    """Retorna países onde está em horário nobre (09h-22h local)"""
    from datetime import datetime, timezone, timedelta
    ativos = []
    for code, (nome, offset, cpm, lang) in PAISES_CPM.items():
        local_hour = (hour_utc + offset) % 24
        if 9 <= local_hour <= 22:
            ativos.append((cpm, code, nome, lang, local_hour))
    return sorted(ativos, reverse=True)

def get_tags_globais(lang, topico=""):
    """Retorna lista de até 500 chars de tags para o YouTube"""
    base = KEYWORDS.get(lang, KEYWORDS["en"])
    todas = []
    todas.extend(base.get("primary",[]))
    todas.extend(base.get("secondary",[]))
    todas.extend(base.get("trending",[]))
    todas.extend(base.get("binaural",[])[:5])
    if topico:
        todas.insert(0, topico)
    # Deduplicar e limitar
    seen = set(); final = []
    for t in todas:
        if t.lower() not in seen: seen.add(t.lower()); final.append(t)
    return final[:30]

def get_hashtags(lang, topico=""):
    """Gera hashtags otimizadas para cada idioma"""
    bases = {
        "pt": "#psicologia #narcisismo #trauma #ansiedade #comportamentohumano #danielacoelho #psidanicoelho #saúdementalimporta",
        "en": "#psychology #narcissism #trauma #anxiety #darkpsychology #danielacoelho #mentalhealth #selfawareness",
        "de": "#psychologie #narzissmus #trauma #angst #dunkle_psychologie #danielacoelho #mentalegesundheit",
        "es": "#psicologia #narcisismo #trauma #ansiedad #psicologiaoscura #danielacoelho #saludmental",
        "fr": "#psychologie #narcissisme #trauma #anxiete #psychologiesombre #danielacoelho #santemental",
        "it": "#psicologia #narcisismo #trauma #ansia #danielacoelho #salutementale",
        "ja": "#心理学 #ナルシシズム #トラウマ #不安 #danielacoelho #メンタルヘルス",
        "ko": "#심리학 #나르시시즘 #트라우마 #불안 #danielacoelho #정신건강",
    }
    h = bases.get(lang, bases["en"])
    if topico:
        # Adicionar hashtag do tópico
        h = f"#{topico.replace(' ','').lower()} " + h
    return h

def get_descricao_seo(title, lang, script_preview="", series="psicologia"):
    """Gera descrição SEO completa com timestamps, fontes e CTAs"""
    templates = {
        "pt": f"""🔬 PESQUISA EM PSICOLOGIA | {title}

Daniela Coelho — Pesquisadora de Comportamento Humano
Baseado em pesquisa científica peer-reviewed

📌 NESTE VÍDEO:
00:00 — Introdução e hook
00:15 — O sinal que ninguém percebe
00:35 — O que a neurociência descobriu
00:50 — O dado chocante (você vai se surpreender)
00:55 — Como aplicar isso na sua vida

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 FONTES CIENTÍFICAS:
• Dr. Craig Malkin (Harvard Medical School) — Narcissistic Spectrum
• Bessel van der Kolk — The Body Keeps the Score
• Dr. Daniel Siegel (UCLA) — Interpersonal Neurobiology
• Brené Brown (University of Texas) — Vulnerability Research
• Mary Ainsworth — Attachment Theory
• Aaron Beck — Cognitive Behavioral Therapy

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 ATIVE O SINO para ser notificado dos próximos estudos!

📱 @psidanicoelho em todas as redes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ AVISO: Este conteúdo é baseado em pesquisa científica publicada.
Não substitui acompanhamento profissional.

#psicologia #comportamentohumano #narcisismo #trauma #ansiedade
#danielacoelho #psidanicoelho #saúdementalimporta #neurociencia
#harvard #psicologiadotrauma #apego #autoconhecimento""",

        "en": f"""🔬 PSYCHOLOGY RESEARCH | {title}

Daniela Coelho — Human Behavior Researcher
Based on peer-reviewed scientific research

📌 IN THIS VIDEO:
00:00 — Introduction and hook
00:15 — The sign nobody notices
00:35 — What neuroscience discovered
00:50 — The shocking data (you'll be surprised)
00:55 — How to apply this in your life

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 SCIENTIFIC SOURCES:
• Dr. Craig Malkin (Harvard Medical School) — Narcissistic Spectrum
• Bessel van der Kolk — The Body Keeps the Score
• Dr. Daniel Siegel (UCLA) — Interpersonal Neurobiology
• Brené Brown (University of Texas) — Vulnerability Research

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 HIT THE BELL to never miss a new study!

📱 @psidanicoelho on all social media

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ DISCLAIMER: This content is based on published scientific research.
It does not replace professional advice.

#psychology #humanbehavior #narcissism #trauma #anxiety
#darkpsychology #danielacoelho #mentalhealth #neuroscience
#harvard #attachmenttheory #selfawareness #healing""",

        "de": f"""🔬 PSYCHOLOGIEFORSCHUNG | {title}

Daniela Coelho — Verhaltensforscherin
Basiert auf wissenschaftlich anerkannter Forschung

📌 IN DIESEM VIDEO:
00:00 — Einführung
00:15 — Das Zeichen, das niemand bemerkt
00:35 — Was die Neurowissenschaft entdeckte
00:50 — Die schockierenden Daten
00:55 — Wie du das in deinem Leben anwendest

📚 WISSENSCHAFTLICHE QUELLEN:
• Dr. Craig Malkin (Harvard) | • Bessel van der Kolk | • Dr. Daniel Siegel (UCLA)

🔔 Aktiviere die Glocke um keine Studie zu verpassen!

#psychologie #narzissmus #trauma #angst #dunkle_psychologie
#danielacoelho #mentalegesundheit #neurowissenschaften #harvard""",

        "es": f"""🔬 INVESTIGACIÓN EN PSICOLOGÍA | {title}

Daniela Coelho — Investigadora del Comportamiento Humano
Basado en investigación científica revisada por pares

📌 EN ESTE VIDEO:
00:00 — Introducción
00:15 — La señal que nadie nota
00:35 — Lo que la neurociencia descubrió
00:50 — El dato impactante
00:55 — Cómo aplicar esto en tu vida

📚 FUENTES CIENTÍFICAS: Harvard | UCLA | University of Texas

🔔 ¡Activa la campana para no perderte ningún estudio!

#psicologia #narcisismo #trauma #ansiedad #psicologiaoscura
#danielacoelho #saludmental #neurociencia #harvard""",
    }
    return templates.get(lang, templates["en"])

def get_titulo_viral(topico, lang, is_live=False):
    """Seleciona ou gera título viral para o tópico e idioma"""
    import random
    from datetime import datetime
    
    if is_live:
        titulos_live = TITULOS.get(lang, TITULOS["en"])
        opcs = titulos_live.get("binaural", titulos_live.get("narcissism", []))
        if opcs: return random.choice(opcs)
    
    # Mapear tópico para categoria
    mapa = {
        "narcis": {"pt":"narcisismo","en":"narcissism","de":"narzissmus","es":"narcisismo"},
        "trauma": {"pt":"trauma","en":"trauma","de":"narzissmus","es":"narcisismo"},
        "ansied": {"pt":"ansiedade","en":"anxiety","de":"narzissmus","es":"narcisismo"},
        "apego":  {"pt":"apego","en":"anxiety","de":"narzissmus","es":"narcisismo"},
    }
    cat = None
    for key, val in mapa.items():
        if key in topico.lower():
            cat = val.get(lang, val.get("en",""))
            break
    if not cat: cat = "narcissism" if lang=="en" else "narcisismo" if lang in ("pt","es") else "narzissmus"
    
    titulos_idioma = TITULOS.get(lang, TITULOS["en"])
    opcs = titulos_idioma.get(cat, [])
    if opcs: return random.choice(opcs)
    return topico

def get_seo_package(topico, lang="pt", hour_utc=12):
    """Pacote SEO completo para um vídeo"""
    title = get_titulo_viral(topico, lang)
    desc  = get_descricao_seo(title, lang, topico)
    tags  = get_tags_globais(lang, topico)
    hts   = get_hashtags(lang, topico)
    ativos = get_paises_ativos(hour_utc)[:5]
    
    return {
        "title": title,
        "description": desc + "\n\n" + hts,
        "tags": tags,
        "hashtags": hts,
        "countries_active": [(c, n, l) for _, c, n, l, _ in ativos],
        "best_lang": ativos[0][3] if ativos else lang,
        "est_cpm": ativos[0][0] if ativos else 2.5,
    }

def get_live_seo(hour_utc=12):
    """SEO otimizado para live 24/7 baseado no horário"""
    ativos = get_paises_ativos(hour_utc)
    if not ativos: ativos = [(2.5, "BR", "Brazil", "pt", 12)]
    top_cpm, top_code, top_nome, top_lang, local_h = ativos[0]
    
    import random
    titulos_live = {
        "manha": [
            "🔴 AO VIVO 24H | ψ Psicologia + 432Hz | Foco Matinal | @psidanicoelho",
            "🔴 LIVE | ψ Binaural 432Hz + Dark Psychology | Manhã de Estudos",
        ],
        "tarde": [
            "🔴 AO VIVO 24H | ψ 432Hz + Psicologia do Trauma | Foco Total",
            "🔴 LIVE | ψ Narcisismo + Binaural 40Hz | Tarde Produtiva",
        ],
        "noite": [
            "🔴 AO VIVO 24H | ψ Binaural Delta 432Hz | Psicologia da Mente",
            "🔴 LIVE | ψ 432Hz + Cura Emocional | Noite de Reflexão",
        ],
    }
    periodo = "manha" if 6<=local_h<12 else "tarde" if 12<=local_h<20 else "noite"
    
    title = random.choice(titulos_live[periodo])
    
    desc = f"""🔴 AO VIVO 24 HORAS | Psicologia e Comportamento Humano

ψ Binaural 432Hz + Psicologia Quântica | Daniela Coelho
Pesquisadora de Comportamento Humano | @psidanicoelho

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎵 FREQUÊNCIAS BINAURAIS:
• 432Hz — Frequência Natural da Terra (harmonia celular)
• 40Hz — Ondas Gamma (foco e concentração máxima)
• Delta — Ondas de Sono Profundo (relaxamento absoluto)

🧠 CONTEÚDO DE PSICOLOGIA ATIVO:
• Narcisismo Encoberto e Manipulação Psicológica
• Trauma de Infância e Comportamento Adulto
• Ansiedade Social e Apego Ansioso
• Dark Psychology: Sinais e Proteção

📚 FONTES: Harvard • UCLA • University of Texas • van der Kolk
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 Super Chat: Faça suas perguntas sobre psicologia!
❤️ Super Thanks: Apoie a pesquisa!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AGORA ACESSANDO DE:
🇺🇸 United States | 🇩🇪 Germany | 🇬🇧 UK | 🇦🇺 Australia
🇫🇷 France | 🇧🇷 Brasil | 🇪🇸 España | 🇮🇹 Italy

#psicologia #binaural #432hz #narcisismo #trauma #ansiedade
#darkpsychology #danielacoelho #psidanicoelho #ao_vivo #live
#binaural432hz #focototal #harvard #neurociencia #comportamentohumano"""

    tags = [
        "binaural beats 432hz","432hz","dark psychology","psicologia","narcissism",
        "trauma","anxiety","covert narcissist","binaural","focus music","study music",
        "meditation","psychology live","comportamento humano","daniel coelho live",
        "psychological manipulation","mental health","attachment theory","gaslighting",
        "healing frequencies","solfeggio frequencies","432 hz","binaural beats sleep",
        "binaural beats focus","binaural beats study","narcisismo encoberto","apego ansioso",
        "trauma de infancia","ansiedade social","saude mental","autoconhecimento"
    ]
    
    return {
        "title": title,
        "description": desc,
        "tags": tags[:30],
        "top_country": top_nome,
        "top_lang": top_lang,
        "est_cpm": top_cpm,
        "countries_watching": len([a for a in ativos if a[0] > 5]),
    }

def score_seo_package(pkg):
    """Score de qualidade SEO 0-100"""
    score = 0
    title = pkg.get("title","")
    desc  = pkg.get("description","")
    tags  = pkg.get("tags",[])
    
    # Título: 35 pts
    if len(title) >= 40: score += 10
    if len(title) <= 100: score += 5
    if any(e in title for e in ["🔴","ψ","🧠","🔬"]): score += 5
    if any(w in title.lower() for w in ["narcis","trauma","ansied","dark","binaural","432hz"]): score += 10
    if any(w in title for w in ["?","!","—","("]): score += 5
    
    # Descrição: 35 pts  
    if len(desc) >= 1000: score += 15
    if "harvard" in desc.lower() or "ucla" in desc.lower(): score += 10
    if "00:00" in desc: score += 5
    if "#" in desc: score += 5
    
    # Tags: 30 pts
    if len(tags) >= 20: score += 15
    if len(tags) >= 30: score += 5
    if "432hz" in str(tags).lower(): score += 5
    if "binaural" in str(tags).lower(): score += 5
    
    return min(100, score)

if __name__ == "__main__":
    from datetime import datetime, timezone
    hour = datetime.now(timezone.utc).hour
    print(f"=== SEO GLOBAL ENGINE TEST === UTC:{hour}h")
    pkg = get_live_seo(hour)
    print(f"Título: {pkg['title']}")
    print(f"Tags ({len(pkg['tags'])}): {', '.join(pkg['tags'][:5])}...")
    print(f"Países ativos com CPM>5: {pkg['countries_watching']}")
    print(f"Top CPM: {pkg['est_cpm']} ({pkg['top_country']})")
    score = score_seo_package(pkg)
    print(f"Score SEO: {score}/100")
