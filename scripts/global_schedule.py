#!/usr/bin/env python3
"""
global_schedule.py — Horários otimizados por país (prime time real)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Baseado em dados reais do YouTube Analytics:
  - Segunda a quinta: pico às 20-23h local
  - Sexta: pico às 18-22h local
  - Sábado/Domingo: pico às 10-12h e 20-22h local
  - Ásia: +12h de diferença do Brasil

JANELAS DE PUBLICAÇÃO IDEAIS (horário local de cada país):
"""
from datetime import datetime, timezone, timedelta

FUSOS = {
    "Brasil":      {"offset":-3,  "prime":[19,20,21], "lang":"PT", "pop_mm":215},
    "USA_East":    {"offset":-5,  "prime":[19,20,21], "lang":"EN", "pop_mm":330},
    "USA_West":    {"offset":-8,  "prime":[19,20,21], "lang":"EN", "pop_mm":330},
    "UK":          {"offset":0,   "prime":[19,20,21], "lang":"EN", "pop_mm":67},
    "Alemanha":    {"offset":1,   "prime":[19,20,21], "lang":"DE", "pop_mm":84},
    "França":      {"offset":1,   "prime":[20,21],    "lang":"FR", "pop_mm":68},
    "Espanha":     {"offset":1,   "prime":[21,22],    "lang":"ES", "pop_mm":47},
    "México":      {"offset":-6,  "prime":[20,21,22], "lang":"ES", "pop_mm":130},
    "Argentina":   {"offset":-3,  "prime":[21,22],    "lang":"ES", "pop_mm":46},
    "Japão":       {"offset":9,   "prime":[20,21,22], "lang":"JP", "pop_mm":125},
    "Coreia":      {"offset":9,   "prime":[20,21,22], "lang":"KO", "pop_mm":52},
    "Austrália":   {"offset":10,  "prime":[19,20,21], "lang":"EN", "pop_mm":26},
    "India":       {"offset":5.5, "prime":[20,21],    "lang":"EN", "pop_mm":1400},
    "Portugal":    {"offset":0,   "prime":[20,21],    "lang":"PT", "pop_mm":10},
}

def calcular_proximos_primes():
    agora_utc = datetime.now(timezone.utc)
    print("=== JANELAS PRIME TIME GLOBAL ===")
    print(f"  Agora UTC: {agora_utc.strftime('%H:%M')}")
    print()
    janelas = []
    for pais, info in FUSOS.items():
        offset_h  = int(info["offset"])
        agora_local = agora_utc + timedelta(hours=offset_h)
        hora_local  = agora_local.hour
        for prime in info["prime"]:
            diff = (prime - hora_local) % 24
            utc_hora = (prime - offset_h) % 24
            janelas.append({
                "pais": pais, "lang": info["lang"],
                "hora_local": prime, "utc": utc_hora,
                "diff_h": diff, "pop_mm": info["pop_mm"],
            })
    janelas.sort(key=lambda x: x["diff_h"])
    print("  PRÓXIMAS JANELAS DE PUBLICAÇÃO:")
    seen_utc = set()
    for j in janelas[:15]:
        if j["utc"] in seen_utc: continue
        seen_utc.add(j["utc"])
        alerta = "🔥 AGORA!" if j["diff_h"] < 1 else f"em {j['diff_h']}h"
        print(f"  {alerta:12s} {j['pais']:15s} {j['hora_local']}h local = {j['utc']:02d}h UTC [{j['lang']}] {j['pop_mm']}M pessoas")
    print()
    print("  CRON JOBS RECOMENDADOS (UTC):")
    utcs_prime = sorted(set(j["utc"] for j in janelas))
    horas_str = ",".join(str(h) for h in utcs_prime[:8])
    print(f"  - cron: "0 {horas_str} * * *"")

if __name__=="__main__": calcular_proximos_primes()
