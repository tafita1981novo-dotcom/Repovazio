#!/usr/bin/env python3
import os, requests, smtplib, json
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import urllib3; urllib3.disable_warnings()

SB_URL     = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY     = os.getenv("SUPABASE_SERVICE_KEY","")
GMAIL_USER = os.getenv("GMAIL_USER","tafita81@gmail.com")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD","")
NOTIFY_TO  = "tafita81@gmail.com"
SBH = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Prefer":"return=representation"}

def get_vendas_novas():
    cutoff = (datetime.utcnow() - timedelta(minutes=35)).isoformat()
    try:
        r = requests.get(
            f"{SB_URL}/rest/v1/vendas?criado_em=gte.{cutoff}&status=eq.confirmada&select=*",
            headers=SBH, timeout=8, verify=False)
        return r.json() if r.status_code == 200 else []
    except: return []

def enviar_email(vendas):
    if not GMAIL_PASS:
        print("  GMAIL_APP_PASSWORD nao configurado")
        return False
    try:
        total = sum(v.get("preco",0) for v in vendas)
        corpo = f"VENDA(S) REGISTRADA(S)\n\nHora: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        corpo += f"Quantidade: {len(vendas)}\nTotal: R${total:.2f}\n\nDetalhes:\n"
        for v in vendas:
            corpo += f"  {v.get('produto','?')} R${v.get('preco',0):.2f}\n"
        corpo += "\nDashboard: https://repovazio.vercel.app/dashboard"
        msg = MIMEText(corpo, 'plain', 'utf-8')
        msg['Subject'] = f"VENDA {len(vendas)}x R${total:.2f} psicologia.doc"
        msg['From']    = GMAIL_USER
        msg['To']      = NOTIFY_TO
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
        print(f"  Email enviado: {len(vendas)} venda(s) R${total:.2f}")
        return True
    except Exception as e:
        print(f"  Erro email: {e}")
        return False

def run():
    print(f"=== NOTIFICACAO VENDA {datetime.now().strftime('%H:%M')} ===")
    vendas = get_vendas_novas()
    if not vendas:
        print("  Sem vendas novas nos ultimos 35min")
        return
    print(f"  {len(vendas)} venda(s) nova(s)!")
    for v in vendas:
        print(f"  {v.get('produto')} R${v.get('preco')}")
    enviar_email(vendas)

if __name__=="__main__": run()
