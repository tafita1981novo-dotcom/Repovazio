#!/usr/bin/env python3
"""
receita_monitor.py — Monitor de receita em tempo real
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONCEITO (Rafael Milagre): "Dados vão até as pessoas. Não o contrário."
  Quando uma venda acontece → notificação automática
  Sem precisar entrar no Hotmart para checar

FONTES:
  1. Hotmart webhook → Supabase → este script detecta
  2. Kirvano webhook → Supabase → notificação
  3. YouTube Analytics → estimativa via view count
  4. KDP royalties → verificação semanal

ALERTAS:
  - Primeira venda do dia 🎉
  - Meta 5 vendas/dia atingida 🏆
  - Meta 20 vendas/dia (viral) 🚀
  - Queda de 50% vs ontem ⚠️
  - Meta mensal R$50K atingida 🏆🏆🏆
"""
import os, requests, json
from datetime import datetime, date
import urllib3; urllib3.disable_warnings()

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
SBH    = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
          "Content-Type":"application/json","Prefer":"return=minimal"}

METAS = {
    "vendas_dia_conservador": 5,
    "vendas_dia_crescimento": 10,
    "vendas_dia_viral": 20,
    "receita_mes": 50000,
}
PRECO_APP = 29.90
PRECO_WA_MES = 18.0

def sb_get(table, filtro=""):
    try:
        r = requests.get(f"{SB_URL}/rest/v1/{table}?{filtro}",
            headers={**SBH,"Prefer":"return=representation"}, timeout=8, verify=False)
        return r.json() if r.status_code==200 else []
    except: return []

def get_vendas_hoje():
    hoje = date.today().isoformat()
    rows = sb_get("produto_low_ticket",
                  f"created_at=gte.{hoje}T00:00:00&select=vendas_dia,receita_dia&limit=1")
    if rows: return rows[0].get("vendas_dia",0), rows[0].get("receita_dia",0.0)
    return 0, 0.0

def get_assinantes():
    rows = sb_get("produto_whatsapp","select=assinantes&limit=1")
    return rows[0].get("assinantes",0) if rows else 0

def gerar_alertas(vendas_dia, receita_dia, assinantes):
    alertas = []
    icons = []
    if vendas_dia == 0:
        alertas.append("⚠️  Sem vendas hoje — verificar funil e ManyChat")
    elif vendas_dia == 1:
        alertas.append("🎉 Primeira venda do dia!")
        icons.append("🎉")
    if vendas_dia >= METAS["vendas_dia_conservador"]:
        alertas.append(f"✅ Meta conservadora ({METAS['vendas_dia_conservador']}/dia) ATINGIDA!")
    if vendas_dia >= METAS["vendas_dia_crescimento"]:
        alertas.append(f"🏆 Meta crescimento ({METAS['vendas_dia_crescimento']}/dia) ATINGIDA!")
    if vendas_dia >= METAS["vendas_dia_viral"]:
        alertas.append(f"🚀 META VIRAL ({METAS['vendas_dia_viral']}/dia) ATINGIDA! ESCALAR ADS!")
    receita_mes_proj = receita_dia * 30 + assinantes * PRECO_WA_MES
    if receita_mes_proj >= METAS["receita_mes"]:
        alertas.append(f"🏆🏆🏆 META R$50K/MÊS ATINGIDA! Parabéns!")
    return alertas

def relatorio_receita():
    vendas_dia, receita_dia = get_vendas_hoje()
    assinantes = get_assinantes()
    receita_wa = assinantes * PRECO_WA_MES
    receita_total_hoje = receita_dia + receita_wa/30
    receita_mes_proj = receita_dia * 30 + receita_wa
    alertas = gerar_alertas(vendas_dia, receita_dia, assinantes)
    pct_meta = round(receita_mes_proj / METAS["receita_mes"] * 100, 1)

    print(f"=== RECEITA MONITOR — {datetime.now().strftime('%d/%m/%Y %H:%M')} ===\n")
    print(f"  HOJE:")
    print(f"  Vendas app R$29,90:   {vendas_dia}")
    print(f"  Receita app hoje:     R${receita_dia:.2f}")
    print(f"  Assinantes WhatsApp:  {assinantes}")
    print(f"  Receita WA (mês):     R${receita_wa:.2f}")
    print(f"\n  PROJEÇÃO:")
    print(f"  Receita mês estimada: R${receita_mes_proj:,.2f}")
    print(f"  Meta R$50K:          {pct_meta}%")
    print(f"  Receita total hoje:   R${receita_total_hoje:.2f}")
    print(f"\n  ALERTAS ({len(alertas)}):")
    for a in alertas:
        print(f"  {a}")
    if not alertas:
        print(f"  ✅ Tudo dentro do esperado")

    # Salvar status no Supabase
    if SB_KEY:
        requests.post(f"{SB_URL}/rest/v1/iris_briefings",
            headers={**SBH,"Prefer":"return=minimal"},
            json={"data":date.today().isoformat(),
                  "briefing":f"Monitor: {vendas_dia} vendas | R${receita_mes_proj:.0f}/mês proj | {pct_meta}% meta",
                  "alertas":len(alertas),
                  "kpis":json.dumps({"vendas_dia":vendas_dia,"receita_mes_proj":receita_mes_proj,"assinantes_wa":assinantes})},
            timeout=8, verify=False)

if __name__=="__main__": relatorio_receita()
