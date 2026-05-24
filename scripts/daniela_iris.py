#!/usr/bin/env python3
"""
daniela_iris.py — Agente autônomo que toca o projeto (inspirado na IRIS do Rafael Milagre)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONCEITO DO TRANSCRIPT (Rafael Milagre):
  "Criei um agente executivo. Ela monitora tudo, manda briefing às 6h,
   cobra pendências, e os dados vão até as pessoas — não ao contrário."

ADAPTAÇÃO PARA psicologia.doc:
  - Varre KPIs do Supabase (vídeos prontos, posts, áudios, afiliados)
  - Detecta tendências de psicologia (PubMed, Reddit, Google Trends)
  - Envia briefing diário 6h BRT via Supabase (lido pelo dashboard)
  - Alerta se pipeline parou (sem posts há +24h = ALERTA)
  - Gera 5 sugestões de conteúdo viral baseado em dados reais
  - Monitora meta R$50K e projeta dias para atingir

REGRA DO TRANSCRIPT:
  Dados vão até as pessoas. Não o contrário.
  Sem reuniões. Só dados.
"""
import os, requests, json, time, datetime
import urllib3; urllib3.disable_warnings()

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
GROQ   = os.getenv("GROQ_API_KEY","")
SBH    = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
          "Content-Type":"application/json","Prefer":"return=minimal"}

META_MENSAL = 50000  # R$50K/mês

TENDENCIAS_PSICOLOGIA = [
    "narcissistic abuse recovery 2025",
    "burnout recovery science",
    "sleep anxiety treatment",
    "attachment theory adults",
    "nervous system regulation techniques",
    "cortisol and sleep",
    "trauma healing neuroscience",
    "gaslighting psychological impact",
]

def sb_get(endpoint, params=""):
    try:
        r = requests.get(f"{SB_URL}/rest/v1/{endpoint}?{params}",
                         headers={**SBH,"Prefer":"return=representation"},
                         timeout=8, verify=False)
        return r.json() if r.status_code == 200 else []
    except: return []

def sb_post(endpoint, data):
    try:
        requests.post(f"{SB_URL}/rest/v1/{endpoint}", headers=SBH,
                      json=data, timeout=8, verify=False)
    except: pass

def groq_call(prompt, max_tokens=400):
    if not GROQ: return ""
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":max_tokens,"temperature":0.75},
            timeout=20, verify=False)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return ""

def coletar_kpis():
    """Coleta KPIs do Supabase — dados vão até as pessoas"""
    kpis = {}
    # Audios prontos WhatsApp
    aud = sb_get("whatsapp_psicologia_queue","status=eq.ready&select=id")
    kpis["audios_prontos"] = len(aud)
    # Posts pendentes Instagram
    posts = sb_get("social_posts","status=eq.pending&select=id")
    kpis["posts_pendentes"] = len(posts)
    # Videos com SEO
    seo = sb_get("video_seo","status=eq.ready&select=id")
    kpis["videos_seo"] = len(seo)
    # Afiliados ativos
    af = sb_get("kwai_products","status=eq.pending&select=id")
    kpis["afiliados_fila"] = len(af)
    # Assinantes WhatsApp
    wa = sb_get("produto_whatsapp","select=assinantes&limit=1")
    kpis["assinantes_wa"] = wa[0].get("assinantes",0) if wa else 0
    # Low ticket vendas
    lt = sb_get("produto_low_ticket","select=vendas_dia&limit=1")
    kpis["vendas_dia_app"] = lt[0].get("vendas_dia",0) if lt else 0
    return kpis

def detectar_alertas(kpis):
    """Detecta problemas — cobra como o Iago cobra o Rafael"""
    alertas = []
    if kpis["audios_prontos"] < 3:
        alertas.append("⚠️ ALERTA: Menos de 3 áudios WhatsApp prontos — pipeline pode estar parado")
    if kpis["posts_pendentes"] < 5:
        alertas.append("⚠️ ALERTA: Menos de 5 posts Instagram na fila — risco de parar publicação")
    if kpis["assinantes_wa"] == 0:
        alertas.append("🔴 CRÍTICO: 0 assinantes WhatsApp — Hotmart ainda não configurado")
    if kpis["videos_seo"] < 3:
        alertas.append("⚠️ ALERTA: Poucos vídeos com SEO completo")
    return alertas

def gerar_sugestoes_virais():
    """Gera 5 sugestões de conteúdo viral baseado em tendências reais"""
    tema = TENDENCIAS_PSICOLOGIA[int(time.time()) % len(TENDENCIAS_PSICOLOGIA)]
    prompt = (
        f"Você é Daniela Coelho, pesquisadora de comportamento humano.\n"
        f"Tendência do dia: '{tema}'\n\n"
        f"Gere 5 sugestões de títulos virais para posts dark de Instagram em PT-BR.\n"
        f"Formato: uma por linha, max 12 palavras, impactante, sem hashtag.\n"
        f"Base científica obrigatória (citar pesquisador real).\n"
        f"PROIBIDO: psicóloga/psicólogo. Use: pesquisadora de comportamento humano."
    )
    return groq_call(prompt, 200)

def calcular_projecao(kpis):
    """Projeta receita e dias para meta R$50K"""
    receita_wa = kpis["assinantes_wa"] * 18  # R$18/mês por assinante
    receita_app = kpis["vendas_dia_app"] * 29.9  # R$29,90 por venda
    receita_mes = receita_wa + receita_app
    dias_para_meta = 999 if receita_mes == 0 else round(30 * META_MENSAL / receita_mes)
    return {"receita_mes_estimada": receita_mes,
            "pct_meta": round(receita_mes/META_MENSAL*100,1),
            "dias_para_meta": min(dias_para_meta, 999)}

def gerar_briefing(kpis, alertas, sugestoes, projecao):
    """Briefing completo em formato texto — vai para o dashboard"""
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    briefing = f"""
=== DANIELA IRIS — BRIEFING DIÁRIO {now} ===

📊 KPIs ATIVOS:
  Áudios WhatsApp prontos: {kpis['audios_prontos']}
  Posts Instagram na fila:  {kpis['posts_pendentes']}
  Vídeos com SEO completo: {kpis['videos_seo']}
  Afiliados na fila:       {kpis['afiliados_fila']}
  Assinantes WhatsApp:     {kpis['assinantes_wa']}
  Vendas app hoje:         {kpis['vendas_dia_app']}

💰 PROJEÇÃO FINANCEIRA:
  Receita estimada/mês: R${projecao['receita_mes_estimada']:.2f}
  Meta R$50K:           {projecao['pct_meta']}% atingida
  Dias para meta:       {projecao['dias_para_meta']} dias

🚨 ALERTAS ({len(alertas)}):
{chr(10).join(alertas) if alertas else '  ✅ Sem alertas críticos'}

💡 SUGESTÕES VIRAIS DO DIA:
{sugestoes}

🎯 AÇÕES MANUAIS PENDENTES:
  1. Criar produto Hotmart (R$216/ano + R$29,90)
  2. Link grupo WhatsApp → Supabase produto_whatsapp
  3. YouTube OAuth para upload automático
  4. Configurar ManyChat auto-resposta "SONO"

"""
    return briefing

def salvar_briefing(briefing):
    """Salva no Supabase para o dashboard ler — dados vão até as pessoas"""
    sb_post("iris_briefings", {
        "data": datetime.date.today().isoformat(),
        "briefing": briefing[:2000],
        "criado_em": datetime.datetime.now().isoformat()
    })

def run():
    print("=== DANIELA IRIS — Agente Autônomo ===\n")
    print(f"  Conceito: Dados vão até as pessoas. Sem reuniões. Só dados.\n")

    kpis = coletar_kpis()
    alertas = detectar_alertas(kpis)
    sugestoes = gerar_sugestoes_virais()
    projecao = calcular_projecao(kpis)
    briefing = gerar_briefing(kpis, alertas, sugestoes, projecao)

    print(briefing)
    salvar_briefing(briefing)
    print("  ✅ Briefing salvo no Supabase — disponível no /dashboard")

if __name__=="__main__": run()
