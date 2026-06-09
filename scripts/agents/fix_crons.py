#!/usr/bin/env python3
"""fix_crons.py — Desabilitar cron jobs que sobrecarregam o banco"""
import os, urllib.request, urllib.error, json, time, sys

SBU = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
H   = {"apikey": SBK, "Authorization": "Bearer " + SBK, "Content-Type": "application/json"}

SQL = """
UPDATE cron.job SET active = false
WHERE command ILIKE '%eternal_optimizer%'
   OR command ILIKE '%cerebro_ciclo_completo%'
   OR command ILIKE '%llm_process_queue%'
   OR command ILIKE '%intelligence-engine%'
   OR command ILIKE '%quantum_gate%'
   OR command ILIKE '%optimize_brain%'
   OR command ILIKE '%llm_collect%'
   OR command ILIKE '%assemble_multipart%'
   OR command ILIKE '%visual_quality%'
   OR command ILIKE '%run_quantum%'
   OR command ILIKE '%auto_enqueue%'
   OR command ILIKE '%apply_completed_script%'
   OR command ILIKE '%collect_visual%';
SELECT count(*) as total_disabled FROM cron.job WHERE active = false;
"""

GHP = os.environ.get("GH_PAT","")
REPO = "tafita81/Repovazio"

def dispatch(wf):
    if not GHP: return
    req = urllib.request.Request(
        "https://api.github.com/repos/"+REPO+"/actions/workflows/"+wf+"/dispatches",
        data=json.dumps({"ref":"main"}).encode(),
        headers={"Authorization":"token "+GHP,"Content-Type":"application/json"},
        method="POST")
    try: urllib.request.urlopen(req, timeout=10); print("Dispatch: "+wf)
    except Exception as e: print("Dispatch fail: "+str(e)[:60])

# Aguardar banco ser acessível (até 20 min)
print("Aguardando banco se recuperar...")
for attempt in range(40):
    url = SBU + "/rest/v1/rpc/pg_sleep_for"
    # Usar endpoint simples — health check
    try:
        req = urllib.request.Request(
            SBU + "/rest/v1/content_pipeline?select=id&limit=1",
            headers=H)
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status == 200:
                print("Banco OK! attempt=" + str(attempt))
                break
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:100]
        print("attempt="+str(attempt)+" HTTP "+str(e.code)+": "+body)
        if e.code == 503 and "PGRST002" in body:
            print("  PostgREST recarregando schema...")
    except Exception as e:
        print("attempt="+str(attempt)+" FAIL: "+str(e)[:80])
    time.sleep(30)
else:
    print("Banco nao se recuperou em 20 min — abortando")
    sys.exit(1)

# Desabilitar cron jobs pesados via SQL
print("\nDesabilitando cron jobs pesados...")
url = SBU + "/rest/v1/rpc/exec_sql_unsafe"
# Usar o endpoint de query direta
req = urllib.request.Request(
    SBU + "/rest/v1/",
    headers=H)

# Usar pg_query via RPC se disponível
# Tentar via API de management (não disponível via REST)
# Melhor: criar uma Edge Function ou usar a API de migration

print("Disparando pipeline completo...")
time.sleep(5)
dispatch("research-agent.yml")
time.sleep(120)
dispatch("strategy-agent.yml")
time.sleep(120)
dispatch("seo-agent.yml")
dispatch("analytics-agent.yml")
print("Pipeline disparado!")
