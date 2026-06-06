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
    """Verifica se live-global-v5 está in_progress"""
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
        return True, runs[0]["id"], runs[0]["created_at"]
    return False, None, None

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
def groq_analyze(status_dict: dict) -> str:
    """Usa Groq Llama 3.3 70B para análise e recomendação"""
    prompt = f"""Você é um agente de monitoramento de live YouTube 24/7.
Analise o status atual em 1 linha curta e diga se precisa de ação:

Status: {json.dumps(status_dict, ensure_ascii=False)}
Hora UTC: {datetime.now(timezone.utc).strftime('%H:%M')}

Responda APENAS: [OK|ALERTA|CRÍTICO] + uma frase curta de diagnóstico."""

    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 60,
        "temperature": 0
    }).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload
    )
    req.add_header("Authorization", f"Bearer {GROQ_API_KEY}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[GROQ_ERR] {e}"

# ── Supabase — logging ────────────────────────────────────────
def supa_log(data: dict):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    try:
        payload = json.dumps({
            "key":   "live:monitor:last",
            "value": json.dumps({**data, "ts": datetime.now(timezone.utc).isoformat()})
        }).encode()
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/ia_cache",
            data=payload, method="POST"
        )
        req.add_header("apikey", SUPABASE_KEY)
        req.add_header("Authorization", f"Bearer {SUPABASE_KEY}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Prefer", "resolution=merge-duplicates")
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        pass  # log falhou — não crítico

# ── Check único ───────────────────────────────────────────────
def run_check(token_cache: list) -> dict:
    result = {"ok": True, "actions": []}

    # 1. GitHub Actions — workflow rodando?
    try:
        running, run_id, started_at = gh_live_running()
        result["gh_running"]  = running
        result["gh_run_id"]   = run_id
        result["gh_started"]  = started_at
    except Exception as e:
        result["gh_running"] = False
        result["gh_error"]   = str(e)

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

    # 4. Auto-correção
    if not result.get("gh_running"):
        log("⚠️  Workflow da live NÃO está rodando! Disparando...")
        ok = gh_dispatch_live()
        result["actions"].append(f"dispatch:{'ok' if ok else 'fail'}")
        result["ok"] = ok
        time.sleep(5)
    elif not result.get("live") and result.get("status") not in ["created","ready","testStarting"]:
        log(f"⚠️  Broadcast não está live (status={result.get('status','?')}) — re-dispatch...")
        gh_dispatch_live()
        result["actions"].append("dispatch:broadcast_dead")

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

            if r.get("ok") and r.get("live"):
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
