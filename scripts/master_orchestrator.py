#!/usr/bin/env python3
"""
master_orchestrator.py — Orquestra todos os pipelines psicologia.doc
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
6 FONTES DE RECEITA:
  1. YouTube AdSense PT-BR (RPM R$7)
  2. YouTube AdSense EN ($25)
  3. WhatsApp Assinatura R$216/ano — Hotmart
  4. Kwai+TikTok Shop afiliados 15-25%
  5. Amazon Associados livros 4-10%
  6. Hotmart Cursos afiliados 30-70%

PIPELINES (executados em paralelo):
  calendar     → 10 dias de conteúdo (WhatsApp + Instagram + Afiliados)
  funil_seo    → títulos A/B + descrição SEO + tags + TikTok
  reels        → 3 legendas/dia Instagram "Comenta SONO"
  audio_wa     → áudio diário Daniela + binaural 528Hz
  narrativa    → 5 nichos dark/geo/neuro/arq/eco
  afiliados    → 4 produtos Kwai × 2 idiomas
"""
import os, subprocess, sys, time, threading

SCRIPTS = [
    ("WhatsApp Áudio Diário",    "scripts/whatsapp_produto.py"),
    ("Calendário 30 Dias",       "scripts/calendario_30dias.py"),
    ("Funil SEO Completo",       "scripts/funil_completo.py"),
    ("Instagram Reels",          "scripts/instagram_reels_producer.py"),
    ("Narrativa Engine",         "scripts/narrativa_engine.py"),
    ("Canal Dark",               "scripts/canal_dark_pipeline.py"),
    ("Kwai Afiliados",           "scripts/kwai_shop_affiliate.py"),
]

RESULTS = {}

def rodar(nome, script):
    try:
        r = subprocess.run([sys.executable, script], capture_output=True, timeout=120, text=True)
        ok = r.returncode == 0
        RESULTS[nome] = {"ok": ok, "output": r.stdout[-200:] if r.stdout else ""}
        print(f"  {'✅' if ok else '⚠️ '} {nome}")
    except Exception as e:
        RESULTS[nome] = {"ok": False, "output": str(e)}
        print(f"  ❌ {nome}: {e}")

def run():
    print("=== MASTER ORCHESTRATOR — psicologia.doc ===\n")
    print("  6 fontes de receita | pipeline 100% autônomo\n")
    threads = []
    for nome, script in SCRIPTS:
        if os.path.exists(script):
            t = threading.Thread(target=rodar, args=(nome, script), daemon=True)
            threads.append(t)
            t.start()
            time.sleep(0.5)
        else:
            print(f"  ⚠️  {script} não encontrado (ok)")
    for t in threads: t.join(timeout=130)

    print(f"\n  RESULTADO: {sum(1 for v in RESULTS.values() if v['ok'])}/{len(RESULTS)} pipelines OK")
    print(f"  WhatsApp 19:30 BRT | Reels publicar 3x | Afiliados ativos")
    print(f"\n  META:")
    print(f"  100 assinantes WhatsApp → R$1.800/mês")
    print(f"  1K assinantes → R$18.000/mês → Meta R$50K")

if __name__ == "__main__": run()
