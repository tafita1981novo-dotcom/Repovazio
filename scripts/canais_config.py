#!/usr/bin/env python3
"""
canais_config.py — Nomes, títulos e configurações de todos os canais
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Configura automaticamente título da live, descrição e tags via YouTube API
RTMP Primary: rtmp://a.rtmp.youtube.com/live2/{KEY}
RTMP Backup:  rtmp://b.rtmp.youtube.com/live2/{KEY}?backup=1
"""
import os, requests, json, time
import urllib3; urllib3.disable_warnings()

YT_REFRESH  = os.getenv("YT_REFRESH_TOKEN","")
YT_CLIENT   = os.getenv("YT_CLIENT_ID","")
YT_SECRET   = os.getenv("YT_CLIENT_SECRET","")
GROQ_KEY    = os.getenv("GROQ_API_KEY","")

# ── NOMES DEFINITIVOS DOS CANAIS ─────────────────────────────────────────
CANAIS = {
    "PT": {
        "nome":        "Daniela Coelho — Psicologia",
        "handle":      "@psidanielacoelho",
        "canal_id":    "UCyCkIpsVgME9yCj_oXJFheA",
        "stream_key":  os.getenv("YOUTUBE_STREAM_KEY",""),
        "idioma":      "pt-BR",
        "rpm_est":     7,
        "descricao":   "Pesquisa de comportamento humano | Narcisismo, Apego, Sono, Burnout",
        "keywords":    "psicologia,narcisismo,apego ansioso,sono,burnout,comportamento humano",
        "pais":        "BR",
        "temas": [
            "Narcisismo Encoberto — Os 8 Sinais Que Você Ignora | AO VIVO",
            "Por Que Você Acorda Às 3h — Ciência do Sono | LIVE",
            "Apego Ansioso — Por Que Você Escolhe Quem Te Machuca | AO VIVO",
            "Burnout Invisível — 3 Fases Antes do Colapso | LIVE",
            "Gaslighting — Quando Fazem Você Duvidar da Sua Realidade | AO VIVO",
            "Síndrome do Impostor — Harvard Explica | LIVE",
            "Cortisol e Ansiedade — A Conexão Que Ninguém Te Conta | AO VIVO",
            "Trauma de Apego — Como a Infância Ainda Controla Você | LIVE",
        ],
    },
    "EN": {
        "nome":        "Psychology Frequencies",
        "handle":      "@psychologyfrequencies",
        "canal_id":    "",  # criar em youtube.com/create
        "stream_key":  os.getenv("YOUTUBE_STREAM_KEY_EN",""),
        "idioma":      "en-US",
        "rpm_est":     28,
        "descricao":   "Human behavior research | Narcissism, Attachment, Sleep, Burnout",
        "keywords":    "psychology,narcissism,anxious attachment,sleep science,burnout,dark psychology",
        "pais":        "US",
        "temas": [
            "Covert Narcissist: 8 Signs Harvard Research Confirms | LIVE NOW",
            "Why You Wake at 3AM — The Cortisol Science | LIVE",
            "Anxious Attachment: Why You Choose Who Hurts You | LIVE NOW",
            "Burnout Before The Crash — 3 Stages | SCIENCE LIVE",
            "Gaslighting: When They Make You Doubt Reality | LIVE NOW",
            "Impostor Syndrome: What Stanford Research Found | LIVE",
            "Trauma Bonding: Why You Can't Leave | LIVE NOW",
            "The Science of Loneliness — Modern Epidemic | LIVE",
        ],
    },
    "ES": {
        "nome":        "Psicología Frecuencias",
        "handle":      "@psicologiafrecuencias",
        "canal_id":    "",
        "stream_key":  os.getenv("YOUTUBE_STREAM_KEY_ES",""),
        "idioma":      "es-419",
        "rpm_est":     12,
        "descricao":   "Investigación del comportamiento humano | Narcisismo, Apego, Sueño",
        "keywords":    "psicologia,narcisismo,apego ansioso,sueno,burnout,psicologia oscura",
        "pais":        "MX",
        "temas": [
            "Narcisista Encubierto: Las 8 Señales Que Ignoras | EN VIVO",
            "Por Qué Te Despiertas a las 3am — La Ciencia | EN VIVO",
            "Apego Ansioso: Por Qué Eliges Quien Te Lastima | EN VIVO",
            "Burnout Silencioso — 3 Fases Antes del Colapso | EN VIVO",
        ],
    },
    "DE": {
        "nome":        "Psychologie Frequenzen",
        "handle":      "@psychologiefrequenzen",
        "canal_id":    "",
        "stream_key":  os.getenv("YOUTUBE_STREAM_KEY_DE",""),
        "idioma":      "de-DE",
        "rpm_est":     18,
        "descricao":   "Forschung zum menschlichen Verhalten | Narzissmus, Bindung, Schlaf",
        "keywords":    "psychologie,narzissmus,angstliche bindung,schlaf,burnout",
        "pais":        "DE",
        "temas": [
            "Verdeckter Narzisst: 8 Zeichen Laut Harvard | LIVE",
            "Warum Du Um 3 Uhr Aufwachst — Die Wissenschaft | LIVE",
            "Ängstliche Bindung: Bindungstheorie Erklärt | LIVE",
            "Burnout Vor Dem Zusammenbruch | LIVE",
        ],
    },
    "JP": {
        "nome":        "心理学周波数",
        "handle":      "@psychology-frequencies-jp",
        "canal_id":    "",
        "stream_key":  os.getenv("YOUTUBE_STREAM_KEY_JP",""),
        "idioma":      "ja-JP",
        "rpm_est":     15,
        "descricao":   "人間行動の研究 | ナルシシズム、愛着、睡眠、バーンアウト",
        "keywords":    "心理学,ナルシシズム,愛着不安,睡眠科学,バーンアウト",
        "pais":        "JP",
        "temas": [
            "隠れたナルシストの8つのサイン — ハーバード研究 | ライブ",
            "なぜ午前3時に目が覚めるのか — コルチゾールの科学 | ライブ",
            "不安型愛着スタイル — なぜ傷つける人を選ぶのか | ライブ",
            "バーンアウトの3段階 — 崩壊の前に | ライブ",
        ],
    },
    "FR": {
        "nome":        "Psychologie Fréquences",
        "handle":      "@psychologiefrequences",
        "canal_id":    "",
        "stream_key":  os.getenv("YOUTUBE_STREAM_KEY_FR",""),
        "idioma":      "fr-FR",
        "rpm_est":     14,
        "descricao":   "Recherche sur le comportement humain | Narcissisme, Attachement, Sommeil",
        "keywords":    "psychologie,narcissisme,attachement anxieux,sommeil,burnout",
        "pais":        "FR",
        "temas": [
            "Narcissiste Masqué: 8 Signes Que Vous Ignorez | EN DIRECT",
            "Pourquoi Vous Réveillez à 3h — La Science | EN DIRECT",
            "Attachement Anxieux — La Recherche Harvard | EN DIRECT",
            "Burnout Silencieux — 3 Phases | EN DIRECT",
        ],
    },
}

RTMP_PRIMARY = "rtmp://a.rtmp.youtube.com/live2"
RTMP_BACKUP  = "rtmp://b.rtmp.youtube.com/live2"

def get_yt_token():
    """Obtém access token via refresh token"""
    if not all([YT_REFRESH, YT_CLIENT, YT_SECRET]): return None
    try:
        r = requests.post("https://oauth2.googleapis.com/token",
            data={"client_id":YT_CLIENT,"client_secret":YT_SECRET,
                  "refresh_token":YT_REFRESH,"grant_type":"refresh_token"},
            timeout=10)
        if r.status_code == 200:
            return r.json().get("access_token")
    except: pass
    return None

def atualizar_titulo_live(canal_id, titulo, descricao, token):
    """Atualiza título e descrição da live via YouTube API"""
    if not token or not canal_id: return False
    try:
        # Buscar live broadcast ativa
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/liveBroadcasts",
            params={"part":"id,snippet","broadcastStatus":"active","broadcastType":"all"},
            headers={"Authorization":f"Bearer {token}"},
            timeout=10
        )
        if r.status_code != 200: return False
        items = r.json().get("items",[])
        if not items: return False
        broadcast_id = items[0]["id"]
        # Atualizar título
        r2 = requests.put(
            "https://www.googleapis.com/youtube/v3/liveBroadcasts",
            params={"part":"snippet"},
            headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
            json={"id":broadcast_id,"snippet":{
                "title":titulo[:100],
                "description":descricao[:5000],
                "scheduledStartTime":items[0]["snippet"].get("scheduledStartTime",""),
            }},
            timeout=10
        )
        return r2.status_code == 200
    except: return False

def rtmp_url(canal, backup=False):
    key = canal["stream_key"]
    if not key: return None
    if backup:
        return f"{RTMP_BACKUP}/{key}?backup=1"
    return f"{RTMP_PRIMARY}/{key}"

def print_configuracao():
    print("=== CANAIS CONFIGURADOS ===\n")
    receita_total = 0
    for lang, canal in CANAIS.items():
        tem_key = "✅" if canal["stream_key"] else "❌ sem key"
        print(f"  [{lang}] {canal['nome']}")
        print(f"         Handle:  {canal['handle']}")
        print(f"         Idioma:  {canal['idioma']}")
        print(f"         RPM:     ~${canal['rpm_est']}/1K views")
        print(f"         Key:     {tem_key}")
        print(f"         RTMP:    {rtmp_url(canal) or 'configurar YOUTUBE_STREAM_KEY_'+lang}")
        print(f"         Temas:   {len(canal['temas'])} programados")
        print()
        if canal["stream_key"]:
            receita_total += canal["rpm_est"]
    print(f"  RPM combinado estimado: ${receita_total}/1K views")
    print(f"  Com 1K views/canal/dia: ${receita_total*1:.0f}/mês")
    print(f"  Com 10K views/canal/dia: ${receita_total*10:.0f}/mês")

def run():
    print_configuracao()
    token = get_yt_token()
    if token:
        canal_pt = CANAIS["PT"]
        tema = canal_pt["temas"][0]
        ok = atualizar_titulo_live(canal_pt["canal_id"], tema,
             canal_pt["descricao"], token)
        print(f"\n  YouTube API título atualizado: {'OK' if ok else 'sem live ativa'}")

if __name__=="__main__": run()
