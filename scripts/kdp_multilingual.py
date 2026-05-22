#!/usr/bin/env python3
"""
kdp_multilingual.py — Scripts psicologia → KDP 5 idiomas
Acao 14: 1 roteiro → 5 ebooks = 5 mercados globais USD/EUR/GBP/JPY/CAD

Cruzamento: DeepL + LLM + Amazon KDP × 5 idiomas
"""
import os, requests
DEEPL_KEY = os.getenv("DEEPL_API_KEY","")
IDIOMAS_TARGET = [
    {"codigo":"EN-US","nome":"English","mercado":"USA","moeda":"USD","royalty":"70%"},
    {"codigo":"DE","nome":"Deutsch","mercado":"Germany","moeda":"EUR","royalty":"70%"},
    {"codigo":"ES","nome":"Español","mercado":"Spain/LATAM","moeda":"EUR","royalty":"70%"},
    {"codigo":"FR","nome":"Français","mercado":"France","moeda":"EUR","royalty":"70%"},
    {"codigo":"JA","nome":"Japanese","mercado":"Japan","moeda":"JPY","royalty":"70%"},
]
def traduzir_deepl(texto, idioma_alvo):
    if not DEEPL_KEY: return f"[TRADUZIR PARA {idioma_alvo}]: {texto[:100]}"
    r = requests.post("https://api-free.deepl.com/v2/translate",
        headers={"Authorization": f"DeepL-Auth-Key {DEEPL_KEY}"},
        json={"text":[texto],"target_lang":idioma_alvo,"source_lang":"PT"},
        timeout=30)
    return r.json()["translations"][0]["text"] if r.status_code == 200 else texto
def run():
    print("ACAO 14: KDP Multi-idioma")
    for i in IDIOMAS_TARGET:
        print(f"  {i['nome']}: {i['mercado']} | {i['moeda']} | {i['royalty']} royalty")
    print("\n  1 script PT-BR → 5 ebooks = 5 fluxos de royalties simultâneos")
    print("  Configurar: DEEPL_API_KEY (500K chars/mes gratis)")
if __name__ == "__main__":
    run()
