#!/usr/bin/env python3
"""
seo_9idiomas.py — SEO DOMINANTE MUNDIAL 9 IDIOMAS
Estratégia: superar canais com bilhões de views no nicho black screen
Idiomas: EN, PT-BR, DE, ES, FR, IT, JA, KO, AR
CPM por idioma: US/DE=$14-18 | UK/AU=$11-14 | FR/IT=$8-10 | BR=$4-6
"""
import json, random
from datetime import datetime, timezone

# ─── TÍTULOS VIRAIS POR IDIOMA E HORÁRIO ─────────────────────────
TITULOS = {
    "en": [
        "🔴 LIVE 24/7 | BLACK SCREEN for Sleep 8 Hours | Binaural Beats 432Hz | Dark Psychology",
        "🔴 LIVE | BLACK SCREEN 10 Hours | Binaural Beats 432Hz | Sleep Study Meditation",
        "🔴 24/7 LIVE | BLACK SCREEN for Insomnia | Binaural 432Hz | Narcissism Psychology",
        "🔴 LIVE | BLACK SCREEN Sleep Music | 432Hz Binaural Beats | Deep Sleep Now",
        "🔴 LIVE 24H | PURE BLACK SCREEN | Binaural Beats 432Hz | Dark Psychology Research",
    ],
    "pt": [
        "🔴 AO VIVO 24H | TELA PRETA para Dormir 8 Horas | Binaural 432Hz | Dark Psychology",
        "🔴 LIVE | TELA PRETA 10 Horas | Binaural 432Hz | Sono Estudo Meditação",
        "🔴 AO VIVO | TELA PRETA para Insônia | Binaural 432Hz | Narcisismo Psicologia",
        "🔴 LIVE 24H | TELA PRETA Pura | Binaural 432Hz | Psicologia Dark",
    ],
    "de": [
        "🔴 LIVE 24/7 | SCHWARZER BILDSCHIRM 8 Stunden Schlafen | Binaural 432Hz | Psychologie",
        "🔴 LIVE | SCHWARZER BILDSCHIRM 10 Stunden | Binaural 432Hz | Schlaf Fokus Meditation",
        "🔴 24H LIVE | SCHWARZER BILDSCHIRM | Binaural 432Hz | Dunkle Psychologie Forschung",
    ],
    "es": [
        "🔴 EN VIVO 24H | PANTALLA NEGRA 8 Horas Dormir | Binaural 432Hz | Psicología Oscura",
        "🔴 EN VIVO | PANTALLA NEGRA 10 Horas | Binaural 432Hz | Sueño Estudio Meditación",
        "🔴 LIVE 24/7 | PANTALLA NEGRA | Binaural 432Hz | Psicología Dark | Narcisismo",
    ],
    "fr": [
        "🔴 EN DIRECT 24H | ÉCRAN NOIR 8 Heures Dormir | Binaural 432Hz | Psychologie Sombre",
        "🔴 LIVE | ÉCRAN NOIR 10 Heures | Binaural 432Hz | Sommeil Étude Méditation",
        "🔴 24H DIRECT | ÉCRAN NOIR | Binaural 432Hz | Psychologie Obscure | Narcissisme",
    ],
    "it": [
        "🔴 IN DIRETTA 24H | SCHERMO NERO 8 Ore Dormire | Binaural 432Hz | Psicologia Oscura",
        "🔴 LIVE | SCHERMO NERO 10 Ore | Binaural 432Hz | Sonno Studio Meditazione",
        "🔴 LIVE 24/7 | SCHERMO NERO | Binaural 432Hz | Psicologia Oscura | Narcisismo",
    ],
    "ja": [
        "🔴 24時間ライブ | 真っ黒画面 8時間 睡眠 | バイノーラル432Hz | 心理学 ダーク",
        "🔴 ライブ | 黒い画面 10時間 | バイノーラル432Hz | 睡眠 勉強 瞑想 集中",
        "🔴 24H ライブ | 黒い画面 | バイノーラル432Hz | 心理学研究 ナルシシズム",
    ],
    "ko": [
        "🔴 24시간 라이브 | 검은 화면 8시간 수면 | 바이노럴 432Hz | 심리학 다크",
        "🔴 라이브 | 검은 화면 10시간 | 바이노럴 432Hz | 수면 공부 명상 집중",
        "🔴 24H 라이브 | 검은 화면 | 바이노럴 432Hz | 심리학 연구 나르시시즘",
    ],
    "ar": [
        "🔴 بث مباشر 24 ساعة | شاشة سوداء للنوم 8 ساعات | بيناورال 432Hz | علم النفس",
        "🔴 مباشر | شاشة سوداء 10 ساعات | بيناورال 432Hz | نوم دراسة تأمل تركيز",
    ],
}

# ─── DESCRIÇÕES POR IDIOMA ────────────────────────────────────────
DESC = {
    "en": """🔴 LIVE 24 HOURS — BLACK SCREEN | BINAURAL BEATS 432Hz | DARK PSYCHOLOGY
Daniela Coelho — Human Behavior Researcher | @psidanicoelho

🖤 PURE BLACK SCREEN — 100% dark, zero pixels illuminated
🎵 TRUE BINAURAL 432Hz (430Hz L + 432Hz R = 2Hz DELTA beat)
🧠 DARK PSYCHOLOGY — Narcissism, Trauma, Anxiety research

★ HEADPHONES for true binaural effect
★ Perfect: Deep Sleep • Study • Meditation • Work • Focus
★ NO logos, NO watermarks, NO brightness — 100% pure black

Research: Harvard • UCLA • van der Kolk • Ainsworth • Gottman

💬 Super Chat: Ask your psychology question LIVE!
❤️ Super Thanks: Support this research!
🔔 SUBSCRIBE + BELL — Never miss a video!

BLACK SCREEN • TELA PRETA • SCHWARZER BILDSCHIRM • PANTALLA NEGRA
ÉCRAN NOIR • SCHERMO NERO • 黒い画面 • 검은 화면 • شاشة سوداء

#blackscreen #blackscreenforsleep #blackscreen8hours #blackscreen10hours
#binauralbeats #binauralbeats432hz #432hz #sleepmusic #studymusic
#focusmusic #meditationmusic #darkpsychology #narcissism #trauma
#anxiety #psychology #danielacoelho #psidanicoelho""",

    "pt": """🔴 AO VIVO 24 HORAS — TELA PRETA | BINAURAL 432Hz | DARK PSYCHOLOGY
Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho

🖤 TELA 100% PRETA — zero pixels iluminados
🎵 BINAURAL REAL 432Hz (430Hz E + 432Hz D = beat 2Hz DELTA)
🧠 DARK PSYCHOLOGY — Narcisismo, Trauma, Ansiedade

★ Use FONES para efeito binaural real
★ Ideal: Sono Profundo • Estudo • Meditação • Trabalho • Foco

Fontes: Harvard • UCLA • van der Kolk • Ainsworth • Gottman

💬 Super Chat: sua pergunta de psicologia ao vivo!
❤️ Super Thanks: apoie a pesquisa!
🔔 INSCREVA-SE + SINO!

#telapreta #telapretatrableceraelm #binaural432hz #432hz #psicologia
#narcisismo #trauma #ansiedade #darkpsychology #danielacoelho""",

    "de": """🔴 LIVE 24 STUNDEN — SCHWARZER BILDSCHIRM | BINAURAL 432Hz | PSYCHOLOGIE
Daniela Coelho — Verhaltensforscherin | @psidanicoelho

🖤 100% SCHWARZER BILDSCHIRM — null Pixel beleuchtet
🎵 ECHTER BINAURAL 432Hz (430Hz L + 432Hz R = 2Hz DELTA)
🧠 DUNKLE PSYCHOLOGIE — Narzissmus, Trauma, Angst

★ KOPFHÖRER für echten Binaural-Effekt
★ Perfekt für: Tiefer Schlaf • Lernen • Meditation • Arbeit

Quellen: Harvard • UCLA • van der Kolk • Ainsworth • Gottman

💬 Super Chat: Ihre Psychologie-Frage LIVE!
🔔 ABONNIEREN + GLOCKE!

#schwarzerbildschirm #binauralbeats432hz #432hz #schlafmusik
#psychologie #narzissmus #danielacoelho #telapreta #blackscreen""",

    "es": """🔴 EN VIVO 24 HORAS — PANTALLA NEGRA | BINAURAL 432Hz | PSICOLOGÍA
Daniela Coelho — Investigadora de Comportamiento Humano | @psidanicoelho

🖤 PANTALLA 100% NEGRA — cero píxeles iluminados
🎵 BINAURAL REAL 432Hz (430Hz I + 432Hz D = beat 2Hz DELTA)
🧠 PSICOLOGÍA OSCURA — Narcisismo, Trauma, Ansiedad

★ AURICULARES para efecto binaural real
★ Perfecto: Sueño Profundo • Estudio • Meditación • Trabajo

Fuentes: Harvard • UCLA • van der Kolk • Ainsworth • Gottman

💬 Super Chat: ¡tu pregunta de psicología en vivo!
🔔 ¡SUSCRÍBETE + CAMPANA!

#pantallanegra #binauralbeats432hz #432hz #musicapararelajarse
#psicologia #narcisismo #danielacoelho #blackscreen #telapreta""",

    "fr": """🔴 EN DIRECT 24 HEURES — ÉCRAN NOIR | BINAURAL 432Hz | PSYCHOLOGIE
Daniela Coelho — Chercheuse en Comportement Humain | @psidanicoelho

🖤 ÉCRAN 100% NOIR — zéro pixel illuminé
🎵 BINAURAL RÉEL 432Hz (430Hz G + 432Hz D = beat 2Hz DELTA)
🧠 PSYCHOLOGIE SOMBRE — Narcissisme, Trauma, Anxiété

★ ÉCOUTEURS pour effet binaural réel
★ Parfait: Sommeil Profond • Études • Méditation • Travail

Sources: Harvard • UCLA • van der Kolk • Ainsworth • Gottman

💬 Super Chat: votre question de psychologie en direct!
🔔 ABONNEZ-VOUS + CLOCHE!

#ecransombre #binauralbeats432hz #432hz #musiquesommeil
#psychologie #narcissisme #danielacoelho #blackscreen""",
}

# ─── TAGS VIRAIS UNIVERSAIS ───────────────────────────────────────
TAGS_UNIVERSAL = [
    "black screen","black screen for sleep","black screen 8 hours","black screen 10 hours",
    "black screen sleep","black screen tv","black screen 4k","pure black screen",
    "binaural beats","binaural beats 432hz","432hz","binaural beats sleep","binaural 432",
    "sleep music","deep sleep music","sleep sounds","sleeping music",
    "study music","focus music","concentration music","work music",
    "meditation music","relaxing music","calm music",
    "dark psychology","narcissism","covert narcissist","trauma","anxiety",
    "tela preta","schwarzer bildschirm","pantalla negra","écran noir",
    "daniela coelho","psidanicoelho",
]

def get_titulo(lang="en"):
    opts=TITULOS.get(lang,TITULOS["en"])
    return random.choice(opts)

def get_desc(lang="en"):
    return DESC.get(lang, DESC["en"])

def get_tags():
    return ",".join(TAGS_UNIVERSAL[:15])

def seo_por_hora():
    """Retorna lang ideal baseado no horário UTC (audiência com maior CPM)"""
    h=datetime.now(timezone.utc).hour
    # Mapeamento hora UTC → idioma ideal (CPM máximo)
    if h in range(5,12):   return "de"   # Europa acordando (DE $14)
    elif h in range(12,17): return "en"  # EUA acordando ($18)
    elif h in range(17,22): return "en"  # EUA tarde + BR noite
    elif h in range(22,24): return "pt"  # BR noite
    else: return "pt"  # madrugada BR

if __name__=="__main__":
    lang=seo_por_hora()
    print(f"Idioma ideal agora: {lang}")
    print(f"Título: {get_titulo(lang)}")
    print(f"Tags: {get_tags()[:100]}")
