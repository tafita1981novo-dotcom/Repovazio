#!/usr/bin/env python3
"""
seo_tester.py — Testa e valida pacotes SEO de forma autônoma
Roda a cada hora para garantir qualidade dos vídeos próximos a publicar
"""
import sys, os, json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)

try:
    from seo_global_v1 import get_live_seo, get_seo_package, score_seo_package, get_paises_ativos
    
    hour = datetime.now(timezone.utc).hour
    log(f"=== SEO GLOBAL TEST | {hour}h UTC ===")

    # Teste 1: Live SEO
    live = get_live_seo(hour)
    s1 = score_seo_package(live)
    log(f"Live title: {live['title'][:70]}")
    log(f"Live score: {s1}/100 | Countries: {live['countries_watching']}")
    log(f"Live CPM top: {live['est_cpm']:.1f} ({live['top_country']})")

    # Teste 2: Video SEO por tópico
    topicos = ["narcisismo encoberto","trauma de infancia","ansiedade social","apego ansioso"]
    for topic in topicos:
        for lang in ["pt","en","de"]:
            pkg = get_seo_package(topic, lang, hour)
            s = score_seo_package(pkg)
            log(f"  [{lang}] {topic[:25]:25}: score={s}/100 CPM={pkg['est_cpm']:.1f}")

    # Teste 3: Países ativos agora
    ativos = get_paises_ativos(hour)[:15]
    log(f"\nPAISES ATIVOS AGORA ({len(ativos)} paises em horario nobre):")
    total_cpm = 0
    for cpm, code, nome, lang, local_h in ativos:
        log(f"  {code:3} {nome:20} {local_h:02d}h CPM={cpm:.1f}")
        total_cpm += cpm
    log(f"CPM combinado top 15: {total_cpm:.1f}")

    # Verificar padrão mínimo
    ok_count = sum(1 for t in topicos for l in ['pt','en','de']
                   if score_seo_package(get_seo_package(t, l, hour)) >= 70)
    total = len(topicos) * 3
    pct = ok_count * 100 // total
    log(f"\nSCORE GERAL: {ok_count}/{total} ({pct}%) acima de 70")
    log(f"STATUS: {'✅ APROVADO' if pct >= 80 else '⚠️  MELHORAR'}")

    sys.exit(0 if pct >= 70 else 1)

except Exception as e:
    log(f"ERRO: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)
