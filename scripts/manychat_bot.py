#!/usr/bin/env python3
"""
manychat_bot.py — ManyChat bot para DM automatico Instagram
Acao 7: Comentario 'quero saber mais' → DM com link afiliado

Cruzamento: ManyChat API + Instagram Graph + Hotmart links
"""
import os, requests
MANYCHAT_KEY = os.getenv("MANYCHAT_API_KEY","")
FLOWS = {
    "narcisismo": {"gatilho": "narcisista", "link": "https://go.hotmart.com/SEU_ID_NARCISISMO", "msg": "Oi! Vi seu comentario sobre narcisismo. Tenho uma indicacao especial pra voce: {link}"},
    "ansiedade": {"gatilho": "ansiedade", "link": "https://go.hotmart.com/SEU_ID_ANSIEDADE", "msg": "Oi! Para aprofundar sobre ansiedade, separei isso pra voce: {link}"},
    "geral": {"gatilho": "quero", "link": "https://go.hotmart.com/SEU_ID_GERAL", "msg": "Oi! Obrigada pelo interesse. Aqui esta o que voce pediu: {link}"},
}
def run():
    print("ACAO 7: ManyChat Bot Instagram")
    for k,v in FLOWS.items():
        print(f"  Gatilho '{v['gatilho']}' -> DM com link {k}")
    print("\n  Setup: manychat.com -> conectar Instagram -> criar fluxo")
    print("  Custo: gratis ate 1000 contatos | ROI: alto")
if __name__ == "__main__":
    run()
