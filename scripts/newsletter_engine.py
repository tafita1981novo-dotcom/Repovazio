#!/usr/bin/env python3
"""
newsletter_engine.py — Email newsletter automatica
Acao 6: Brevo 300 emails/dia gratis → lista propria → monetizacao
"""
import os, requests
from datetime import datetime
BREVO_KEY = os.getenv("BREVO_API_KEY","")
SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY","")

SEQUENCES = [
    {"dia": 1, "assunto": "O sinal #1 que voce esta num relacionamento narcisista", "cta": "artigo_blog"},
    {"dia": 3, "assunto": "A ciencia por tras do trauma de relacionamento", "cta": "video_youtube"},
    {"dia": 7, "assunto": "5 ferramentas que uso com meus clientes", "cta": "curso_afiliado"},
    {"dia": 14, "assunto": "Sua pergunta mais comum: como eu sei se sou a vitima ou o problema?", "cta": "consulta"},
    {"dia": 30, "assunto": "Atualizacao mensal: novidades de psicologia", "cta": "comunidade"},
]

def enviar_email_brevo(para, assunto, html):
    if not BREVO_KEY: return
    requests.post("https://api.brevo.com/v3/smtp/email",
        headers={"api-key": BREVO_KEY, "Content-Type": "application/json"},
        json={"sender": {"name":"Daniela Coelho","email":"psidanielacoelho1982@gmail.com"},
              "to": [{"email": para}], "subject": assunto, "htmlContent": html},
        timeout=15)

def run():
    print("ACAO 6: Newsletter Engine")
    print(f"Sequences configuradas: {len(SEQUENCES)}")
    for s in SEQUENCES:
        print(f"  Dia {s['dia']:3d}: {s['assunto'][:50]} | CTA: {s['cta']}")
    print("\n  Configurar: BREVO_API_KEY no GitHub Secrets")
    print("  300 emails/dia gratis | Tally form captura leads")

if __name__ == "__main__":
    run()
