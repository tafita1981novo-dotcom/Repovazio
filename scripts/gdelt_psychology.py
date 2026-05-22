#!/usr/bin/env python3
"""
gdelt_psychology.py — GDELT eventos globais → video psicologia viral
Acao 13: Evento noticiario + angulo psicologico = conteudo trending

Cruzamento: GDELT Project (no-auth) + LLM + pipeline
"""
import requests, os, json
from datetime import datetime, timedelta
GROQ_KEY = os.getenv("GROQ_API_KEY","")
def buscar_eventos_gdelt(keyword="mental health", dias=1):
    desde = (datetime.now()-timedelta(days=dias)).strftime("%Y%m%d%H%M%S")
    try:
        r = requests.get("https://api.gdeltproject.org/api/v2/doc/doc",
            params={"query": keyword, "mode": "artlist", "maxrecords": 10,
                    "startdatetime": desde, "format": "json", "sourcelang": "Portuguese"},
            timeout=20)
        if r.status_code == 200:
            return r.json().get("articles", [])
    except: pass
    return []
def run():
    print("ACAO 13: GDELT Psychology Engine")
    print("Monitorando eventos globais com angulo psicologico")
    eventos = buscar_gdelt_eventos("saude mental")
    print(f"Eventos encontrados: {len(eventos)}")
    for e in eventos[:3]:
        print(f"  • {e.get('title','')[:70]}")
if __name__ == "__main__":
    run()
