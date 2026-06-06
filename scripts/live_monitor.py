#!/usr/bin/env python3
"""
live_monitor.py — Agente watchdog 24/7
Checa a live a cada 60s, auto-corrige, usa Groq para análise inteligente
Grátis: GitHub Actions + Groq Llama 3.3 70B (14.400 req/dia)
"""
import os, json, urllib.request, urllib.parse, time, sys
from datetime import datetime, timezone

# ── Credentials ──────────────────────────────────────────────
GH_PAT          = os.environ["GH_PAT"]
GH_REPO         = "tafita81/Repovazio"
GROQ_API_KEY    = os.environ["GROQ_API_KEY"]
YT_CLIENT_ID    = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET= os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN= os.environ["YT_REFRESH_TOKEN"]
SUPABASE_URL    = os.environ.get("SUPABASE_URL","")
SUPABASE_KEY    = os.environ.get("SUPABASE_SERVICE_KEY","")
LIVE_WF_ID      = "288922095"   # live-global-v5.yml ID
CHECKS          = int(os.environ.get("CHECKS","5"))   # quantas verificações por execução
INTERVAL        = int(os.environ.get("INTERVAL","60")) # segundos entre checks

def log(m): print(f"[{datetime.now(timezone.utc):%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now(timezone.utc):%H:%M:%S}] ❌ {m}", flush=True)

# ── YouTube API ───────────────────────────────────────────────
def yt_token():
    data = urllib.parse.urlencode({
        "client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())["access_token"]

def yt_status(token):
    """Retorna dict com status completo do broadcast"""
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/liveBroadcasts"
        "?part=id,snippet,status,statistics&broadcastType=all&mine=true&maxResults=5"
    )
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())

    items = data.get("items", [])
    if not items:
        return {"live": False, "reason": "no_broadcast", "viewers": 0, "title": ""}

    item = items[0]
    lc      = item["status"]["lifeCycleStatus"]
    viewers = int(item.get("statistics", {}).get("concurrentViewers", 0))
    title   = item["snippet"]["title"][:80]
    bc_id   = item["id"]
    return {
        "live":    lc in ["live", "testing"],
        "status":  lc,
        "viewers": viewers,
        "title":   title,
        "bc_id":   bc_id,
        "reason":  lc
    }

def yt_stream_health(token):
    """Verifica saúde do stream RTMP"""
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/liveStreams"
        "?part=id,status,cdn&mine=true&maxResults=10"
    )
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())

    for item in data.get("items", []):
        key = item.get("cdn", {}).get("ingestionInfo", {}).get("streamName", "")
        if "ewme" in key:  # nosso stream key
            st = item.get("status", {})
            return {
                "stream_status": st.get("streamStatus", "?"),
                "health":        st.get("healthStatus", {}).get("status", "?"),
                "key":           key[:8] + "..."
            }
    return {"stream_status": "not_found", "health": "unknown", "key": "?"}

# ── GitHub API ────────────────────────────────────────────────
def gh_live_running():
    """Verifica se live-global-v5 está in_progress + quanto tempo rodando"""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{GH_REPO}/actions/runs"
        f"?workflow_id={LIVE_WF_ID}&status=in_progress&per_page=5"
    )
    req.add_header("Authorization", f"token {GH_PAT}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    runs = data.get("workflow_runs", [])
    if runs:
        # Calcular tempo de execução
        from datetime import datetime, timezone
        started_str = runs[0]["created_at"].replace("Z", "+00:00")
        started_dt  = datetime.fromisoformat(started_str)
        elapsed_min = (datetime.now(timezone.utc) - started_dt).total_seconds() / 60
        return True, runs[0]["id"], runs[0]["created_at"], elapsed_min
    return False, None, None, 0

def gh_dispatch_live():
    """Dispara o workflow da live"""
    payload = json.dumps({"ref": "main", "inputs": {"duration_h": "6"}}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{GH_REPO}/actions/workflows/{LIVE_WF_ID}/dispatches",
        data=payload, method="POST"
    )
    req.add_header("Authorization", f"token {GH_PAT}")
    req.add_header("Content-Type", "application/json")
    try:
        urllib.request.urlopen(req, timeout=15)
        return True
    except Exception as e:
        err(f"Dispatch falhou: {e}")
        return False

# ── Groq — análise inteligente ────────────────────────────────
# Modelos Groq em ordem de preferência (todos gratuitos)
GROQ_MODELS = [
    "llama3-8b-8192",
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

def groq_analyze(status_dict: dict) -> str:
    """Usa Groq (modelo grátis) para análise inteligente da live"""
    gh_ok  = status_dict.get("gh_running", False)
    yt_ok  = status_dict.get("live", False)
    stream = status_dict.get("stream_health", "?")
    viewers= status_dict.get("viewers", 0)

    # Diagnóstico rápido sem IA se possível
    if gh_ok and yt_ok and stream in ["good","ok","OK"]:
        return f"[OK] Live saudável | {viewers} viewers | stream={stream}"
    if gh_ok and not yt_ok and stream in ["noData","inactive"]:
        return f"[OK] Inicializando — workflow rodando, broadcast conectando"

    prompt = (
        f"Live YouTube status: gh_running={gh_ok}, yt_live={yt_ok}, "
        f"stream={stream}, viewers={viewers}, "
        f"hora={datetime.now(timezone.utc).strftime('%H:%M')} UTC. "
        f"Responda APENAS: [OK|ALERTA|CRITICO] + diagnóstico em 1 frase."
    )
    payload = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 60, "temperature": 0
    })

    for model in GROQ_MODELS:
        try:
            body = json.loads(payload)
            body["model"] = model
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(body).encode()
            )
            req.add_header("Authorization", f"Bearer {GROQ_API_KEY}")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=12) as r:
                txt = json.loads(r.read())["choices"][0]["message"]["content"].strip()
                return f"[{model.split('-')[0]}] {txt}"
        except Exception:
            continue

    # Fallback: diagnóstico local sem IA
    if not gh_ok: return "[CRITICO] Workflow parado — redispatch necessário"
    if not yt_ok: return "[ALERTA] Broadcast offline mas workflow OK"
    return "[OK] Status nominal"

# ── Supabase — logging ────────────────────────────────────────
def supa_log(data: dict):
    """Grava status no Supabase ia_cache via upsert"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    try:
        record = {
            "key":   "live:monitor:last",
            "value": json.dumps({**data, "ts": datetime.now(timezone.utc).isoformat()})
        }
        payload = json.dumps(record).encode()
        # Tentar upsert via PATCH (update se existe)
        for method, url_suffix, prefer in [
            ("POST",  "/rest/v1/ia_cache",                          "resolution=merge-duplicates"),
            ("PATCH", "/rest/v1/ia_cache?key=eq.live%3Amonitor%3Alast", ""),
        ]:
            try:
                req = urllib.request.Request(
                    f"{SUPABASE_URL}{url_suffix}",
                    data=payload, method=method
                )
                req.add_header("apikey", SUPABASE_KEY)
                req.add_header("Authorization", f"Bearer {SUPABASE_KEY}")
                req.add_header("Content-Type", "application/json")
                if prefer:
                    req.add_header("Prefer", prefer)
                urllib.request.urlopen(req, timeout=8)
                return  # sucesso
            except Exception:
                continue
    except Exception:
        pass  # silencioso — log não é crítico

# ── Check único ───────────────────────────────────────────────
def run_check(token_cache: list) -> dict:
    result = {"ok": True, "actions": []}

    # 1. GitHub Actions — workflow rodando?
    try:
        running, run_id, started_at, elapsed_min = gh_live_running()
        result["gh_running"]     = running
        result["gh_run_id"]      = run_id
        result["gh_started"]     = started_at
        result["gh_elapsed_min"] = round(elapsed_min, 1)
    except Exception as e:
        result["gh_running"] = False
        result["gh_error"]   = str(e)
        result["gh_elapsed_min"] = 0

    # 2. YouTube — broadcast ativo?
    try:
        if not token_cache:
            token_cache.append(yt_token())
        token = token_cache[0]

        yt = yt_status(token)
        result.update(yt)

        sh = yt_stream_health(token)
        result["stream_status"] = sh["stream_status"]
        result["stream_health"] = sh["health"]
    except Exception as e:
        result["yt_error"] = str(e)
        result["live"] = False
        # Forçar refresh do token no próximo check
        if token_cache: token_cache.clear()

    # 3. Diagnóstico via Groq
    try:
        groq_result = groq_analyze(result)
        result["groq"] = groq_result
    except Exception as e:
        result["groq"] = f"err:{e}"

    # 4. Auto-correção inteligente
    gh_running = result.get("gh_running", False)
    yt_live    = result.get("live", False)
    stream_st  = result.get("stream_status", "")
    stream_h   = result.get("stream_health", "")

    if not gh_running:
        # Workflow parado = live morreu definitivamente → re-dispatch
        log("⚠️  Workflow da live PARADO → re-dispatch imediato!")
        ok = gh_dispatch_live()
        result["actions"].append(f"dispatch:workflow_dead:{'ok' if ok else 'fail'}")
        result["ok"] = ok
        time.sleep(5)
    elif gh_running and not yt_live and stream_h in ["noData","","good"] and result.get("gh_elapsed_min",0) > 8:
        # Run >8min sem stream → TRAVADO → forçar restart
        elapsed = result.get("gh_elapsed_min",0)
        log(f"⚠️  Run TRAVADO {elapsed:.1f}min sem dados → re-dispatch forçado!")
        ok = gh_dispatch_live()
        result["actions"].append(f"dispatch:stuck_{elapsed:.0f}min:{'ok' if ok else 'fail'}")
        result["ok"] = ok
    elif gh_running and not yt_live and stream_h in ["noData", ""] and stream_st == "inactive":
        # Inicializando normalmente (<8min) → aguardar
        elapsed = result.get("gh_elapsed_min",0)
        log(f"ℹ️  Inicializando {elapsed:.1f}min — aguardando stream conectar...")
        result["ok"] = True
    elif gh_running and not yt_live and stream_st not in ["active","inactive","not_found",""]:
        log(f"ℹ️  Broadcast não live (status={result.get('status')}) — workflow OK, auto-recuperando...")
        result["ok"] = True
    elif gh_running and not yt_live and stream_h in ["noData",""] and result.get("gh_elapsed_min", 0) > 8:
        # Run há mais de 8 min e stream ainda sem dados → travado → forçar restart
        log(f"⚠️  Run travado há {result.get('gh_elapsed_min')}min sem stream! Forçando restart...")
        gh_dispatch_live()
        result["actions"].append(f"dispatch:stuck_run:{result.get('gh_elapsed_min')}min")

    # 5. Stream RTMP com problema?
    if result.get("stream_status") not in ["active", "inactive", "not_found"]:
        log(f"⚠️  Stream health: {result.get('stream_health','?')}")
        result["actions"].append(f"stream_warn:{result.get('stream_health')}")

    return result

# ── Main ──────────────────────────────────────────────────────
def main():
    log("=" * 55)
    log(f"LIVE MONITOR — Groq Llama 3.3 70B | {CHECKS} checks × {INTERVAL}s")
    log("=" * 55)

    token_cache = []
    consecutive_ok = 0
    consecutive_fail = 0

    for i in range(CHECKS):
        log(f"\n── Check {i+1}/{CHECKS} ──────────────────────────────────")

        try:
            r = run_check(token_cache)

            # Log compacto
            live_icon  = "🟢" if r.get("live") else "🔴"
            gh_icon    = "✅" if r.get("gh_running") else "❌"
            viewers    = r.get("viewers", 0)
            stream_h   = r.get("stream_health", "?")
            groq_diag  = r.get("groq", "?")
            actions    = r.get("actions", [])

            log(f"{live_icon} YT broadcast | {gh_icon} GH workflow | 👥 {viewers} viewers")
            log(f"   Stream: {r.get('stream_status','?')} ({stream_h})")
            log(f"   🤖 Groq: {groq_diag}")
            if actions:
                log(f"   ⚙️  Ações: {', '.join(actions)}")

            # Logar no Supabase
            supa_log({
                "check": i+1,
                "live": r.get("live"),
                "viewers": viewers,
                "stream": stream_h,
                "groq": groq_diag,
                "actions": actions,
                "gh_running": r.get("gh_running")
            })

            # OK = workflow rodando (live pode estar inicializando)
            if r.get("gh_running"):
                consecutive_ok += 1
                consecutive_fail = 0
            else:
                consecutive_fail += 1
                consecutive_ok = 0

        except Exception as e:
            err(f"Check {i+1} falhou: {e}")
            consecutive_fail += 1

        # Não dormir no último check
        if i < CHECKS - 1:
            log(f"   Próximo check em {INTERVAL}s...")
            time.sleep(INTERVAL)

    log(f"\n✅ Ciclo concluído | OK={consecutive_ok} FAIL={consecutive_fail}")

if __name__ == "__main__":
    main()
