#!/usr/bin/env python3
"""
master_engine.py — Orquestrador Master de todos os 20 sistemas
Executa: pesquisa → gera → posta → monitora → escala → lucra

RECEITAS GERADAS AUTOMATICAMENTE:
  - YouTube AdSense (PT-BR + EN + DE + ES + JA)
  - Hotmart/Clickbank/JVZoo afiliados
  - Gumroad produtos digitais ($9 audio packs)
  - Redbubble/Society6 POD arte
  - Amazon KDP ebooks 5 idiomas
  - Micro-SaaS PsiScript Pro API $19/mes
  - B2B licensing clinicas R$500-2000/mes
  - Newsletter Brevo/Mailchimp assinaturas
  - ManyChat DM bot afiliados Instagram
  - Campanha Reddit-based content
"""

import os, sys, subprocess, json, time
from datetime import datetime

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY","")

SISTEMAS = [
    # (script, nome, prioridade, mercados)
    ("scripts/youtube_growth_engine.py",    "YouTube Growth",    1, ["BR","EN","DE","ES"]),
    ("scripts/affiliate_ugc_engine.py",     "Affiliate UGC",     1, ["BR"]),
    ("scripts/research_monitor.py",         "Research Monitor",  2, ["BR","EN"]),
    ("scripts/quote_pod_engine.py",         "Quote POD",         2, ["GLOBAL"]),
    ("scripts/en_channel_engine.py",        "EN Channel",        2, ["USA","UK","AU"]),
    ("scripts/trend_surfer.py",             "Trend Surfer",      1, ["BR","EN"]),
    ("scripts/reddit_video_engine.py",      "Reddit Video",      2, ["USA","BR"]),
    ("scripts/newsletter_engine.py",        "Newsletter",        3, ["BR"]),
    ("scripts/manychat_bot.py",             "ManyChat Bot",      3, ["BR"]),
    ("scripts/bannerbear_thumbnails.py",    "Thumbnails A/B",    3, ["BR","EN"]),
    ("scripts/fix_22_videos.py",            "Fix 22 Videos",     1, ["BR"]),
    ("scripts/multi_canal_setup.py",        "Multi Canal",       1, ["BR","EN","DE","ES","JA"]),
    ("scripts/b2b_licensing.py",            "B2B Licensing",     3, ["BR"]),
    ("scripts/micro_saas_api.py",           "Micro SaaS",        3, ["GLOBAL"]),
    ("scripts/gdelt_psychology.py",         "GDELT Events",      2, ["BR","EN"]),
    ("scripts/kdp_multilingual.py",         "KDP 5 idiomas",     2, ["USA","DE","ES","FR","JP"]),
    ("scripts/gumroad_product_engine.py",   "Gumroad Audio",     1, ["USA","UK","BR"]),
    ("scripts/redbubble_batch_engine.py",   "Redbubble POD",     1, ["GLOBAL"]),
    ("scripts/hotmart_affiliate_engine.py", "Hotmart Afiliados", 1, ["BR"]),
    ("scripts/smolagents_orchestrator.py",  "SmolAgents",        2, ["GLOBAL"]),
]

def status_receita():
    """Busca receita total no Supabase"""
    if not SB_KEY: return {}
    try:
        r = requests.get(f"{SB_URL}/rest/v1/v_receita_total?select=*",
            headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"}, timeout=15)
        if r.status_code == 200:
            return r.json()
    except: pass
    return {}

def run_sistema(script_path, nome):
    """Roda um sistema e retorna status"""
    if not os.path.exists(script_path):
        return {"status": "file_not_found", "nome": nome}
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, timeout=120,
            env={**os.environ}
        )
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "nome": nome,
            "output": result.stdout[-500:] if result.stdout else "",
            "error": result.stderr[-200:] if result.stderr else ""
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "nome": nome}
    except Exception as e:
        return {"status": "exception", "nome": nome, "error": str(e)}

def log_supabase(resultados):
    """Salva log de execucao no Supabase"""
    if not SB_KEY: return
    import requests
    requests.post(f"{SB_URL}/rest/v1/master_engine_log",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                 "Content-Type": "application/json"},
        json={"resultados": json.dumps(resultados), "data": datetime.now().isoformat(),
              "sistemas_ok": sum(1 for r in resultados if r.get("status")=="ok"),
              "sistemas_total": len(resultados)},
        timeout=10)

def run(modo="status"):
    print(f"\n{'='*60}")
    print(f"QUANTUM BRAIN MASTER ENGINE — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Modo: {modo} | Sistemas: {len(SISTEMAS)}")
    print("="*60)
    
    if modo == "status":
        print("\nSistemas configurados:")
        for script, nome, prio, mercados in sorted(SISTEMAS, key=lambda x: x[2]):
            existe = "✅" if os.path.exists(script) else "⚠️ "
            print(f"  [{prio}] {existe} {nome:30s} → {','.join(mercados)}")
        
        receita = status_receita()
        if receita:
            print(f"\nReceita registrada:")
            for r in receita:
                print(f"  {r.get('fonte','?'):20s}: ${r.get('receita_usd',0):.2f} USD")
        
        print(f"\nDashboard: repovazio.vercel.app/cerebro.html")
        print(f"GitHub Actions: 14 workflows ativos")
        print(f"APIs no banco: 1780+ (crescendo para 40K)")
        
    elif modo == "run_all":
        resultados = []
        for script, nome, prio, mercados in SISTEMAS:
            print(f"\n▶ {nome}...")
            r = run_sistema(script, nome)
            resultados.append(r)
            status = "✅" if r["status"] == "ok" else "⚠️"
            print(f"  {status} {r['status']} | {r.get('output','')[:100]}")
            time.sleep(2)
        
        log_supabase(resultados)
        ok = sum(1 for r in resultados if r["status"] == "ok")
        print(f"\n{'='*60}")
        print(f"RESULTADO: {ok}/{len(resultados)} sistemas executados com sucesso")
        
    elif modo == "gerar_video":
        import sys
        topic = sys.argv[2] if len(sys.argv) > 2 else "narcisismo encoberto"
        run_sistema("scripts/youtube_growth_engine.py", "YouTube Growth")

if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "status"
    run(modo)
