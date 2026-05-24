#!/usr/bin/env python3
"""
master_orchestrator.py — Une todos os pipelines
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SISTEMAS ATIVOS:
  1. knowledge_fusion     — 27 APIs em paralelo (4x/dia)
  2. canal_dark_pipeline  — Daniela reflexiva (3x/dia)
  3. global_render        — 5 temas × 5 idiomas (3x/dia)
  4. kwai_shop_affiliate  — 4 produtos × 2 idiomas (2x/dia)
  5. kwai_short_video     — Shorts 60-90s Kwai (2x/dia)
  6. competitive_radar    — 6 canais virais (toda segunda)
  7. auto_refresh_loop    — Scripts atualizados (toda quarta)

ARQUITETURA:
  Groq LLaMA 3.3 70B → scripts reflexivos
  NVIDIA DeepSeek V4 → análise profunda
  Edge TTS           → voz natural (GRATUITO)
  Pollinations FLUX  → imagens (GRATUITO)
  Pexels API         → b-roll (GRATUITO)
  PubMed/CrossRef    → ciência (GRATUITO)
  27 APIs adicionais → contexto (GRATUITO)
  Kwai Shop          → monetização afiliado
  YouTube            → R$7/RPM PT | $25 EN | $18 DE
"""
import os, subprocess, time, pathlib
import urllib3; urllib3.disable_warnings()

def run_script(name, timeout=300):
    p = pathlib.Path(f"scripts/{name}")
    if not p.exists():
        print(f"  ⚠️  {name} não encontrado")
        return False
    print(f"  🔄 {name}...")
    r = subprocess.run(["python3",str(p)], capture_output=True, timeout=timeout, text=True)
    ok = r.returncode == 0
    print(f"  {'✅' if ok else '⚠️ '} {name} {'OK' if ok else r.stderr[:60]}")
    if r.stdout: print(f"     {r.stdout[:100]}")
    return ok

def get_mode():
    """Determina modo baseado na hora"""
    import datetime
    h = datetime.datetime.utcnow().hour
    # 3h: radar (segunda)
    # 4h: refresh (quarta)
    # 5h: knowledge fusion
    # 6-8h: global render + canal dark
    # 10h/18h: kwai + shorts
    return h

def run():
    print("=" * 55)
    print("  PSICOLOGIA.DOC — MASTER ORCHESTRATOR")
    print("  Canal: @psidanielacoelho | UCyCkIpsVgME9yCj_oXJFheA")
    print("=" * 55)
    import datetime
    now = datetime.datetime.utcnow()
    print(f"  UTC: {now.strftime('%Y-%m-%d %H:%M')}")
    print()

    # Sempre rodar: knowledge fusion (27 APIs)
    run_script("knowledge_fusion.py", timeout=600)
    time.sleep(5)

    # Canal dark (Daniela reflexiva)
    run_script("canal_dark_pipeline.py", timeout=600)
    time.sleep(5)

    # Kwai affiliate scripts
    run_script("kwai_shop_affiliate.py", timeout=300)
    time.sleep(5)

    # Kwai short video render
    run_script("kwai_short_video_renderer.py", timeout=600)

    print()
    print("=" * 55)
    print(f"  ✅ Orquestrador concluído")
    print(f"  📊 Dashboard: repovazio.vercel.app")
    print(f"  🧠 Quantum Brain: repovazio.vercel.app/cerebro.html")
    print("=" * 55)

if __name__=="__main__": run()
