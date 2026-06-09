#!/usr/bin/env python3
"""
fix_crons.py — Aguarda Supabase, recupera secrets do ia_cache, dispara pipeline
"""
import os, urllib.request, urllib.error, json, time, sys, base64

SBU  = os.environ["SUPABASE_URL"].rstrip("/")
SBK  = os.environ["SUPABASE_SERVICE_KEY"]
GHP  = os.environ.get("GH_PAT","")
H    = {"apikey": SBK, "Authorization": "Bearer " + SBK, "Content-Type": "application/json"}
REPO = "tafita81/Repovazio"


def sb_ok():
    req = urllib.request.Request(
        SBU + "/rest/v1/content_pipeline?select=id&limit=1", headers=H)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            print("Supabase resp: " + str(r.status))
            return r.status == 200
    except urllib.error.HTTPError as e:
        print("sb_ok HTTP " + str(e.code) + ": " + e.read().decode()[:100])
        return False
    except Exception as e:
        print("sb_ok fail: " + str(e)[:80])
        return False


def get_secret_from_cache(name):
    """Recupera um secret do ia_cache do Supabase."""
    url = SBU + "/rest/v1/ia_cache?cache_key=eq.secret:" + name + "&select=value&limit=1"
    req = urllib.request.Request(url, headers=H)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            rows = json.loads(r.read())
            if rows:
                val = rows[0].get("value") or rows[0].get("cache_value","")
                if isinstance(val, dict): val = val.get("value","")
                return str(val).strip()
    except Exception as e:
        print("get_secret " + name + ": " + str(e)[:60])
    return ""


def set_github_secret(name, value):
    """Configura um secret no GitHub via API."""
    if not GHP or not value:
        return False
    # Pegar public key do repo
    req = urllib.request.Request(
        "https://api.github.com/repos/" + REPO + "/actions/secrets/public-key",
        headers={"Authorization": "token " + GHP})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            pk_data = json.load(r)
    except Exception as e:
        print("get_pubkey fail: " + str(e)[:60]); return False

    key_id  = pk_data["key_id"]
    pub_key = pk_data["key"]

    # Encriptar com PyNaCl
    try:
        from nacl import encoding, public
        pk = public.PublicKey(pub_key.encode(), encoding.Base64Encoder())
        box = public.SealedBox(pk)
        encrypted = base64.b64encode(box.encrypt(value.encode())).decode()
    except ImportError:
        # Fallback: instalar nacl
        import subprocess as sp
        sp.run(["pip","install","PyNaCl","-q"], capture_output=True)
        from nacl import encoding, public
        pk = public.PublicKey(pub_key.encode(), encoding.Base64Encoder())
        box = public.SealedBox(pk)
        encrypted = base64.b64encode(box.encrypt(value.encode())).decode()

    payload = json.dumps({"encrypted_value": encrypted, "key_id": key_id}).encode()
    req = urllib.request.Request(
        "https://api.github.com/repos/" + REPO + "/actions/secrets/" + name,
        data=payload,
        headers={"Authorization": "token " + GHP, "Content-Type": "application/json"},
        method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print("Secret " + name + " configurado (HTTP " + str(r.status) + ")")
            return True
    except Exception as e:
        print("set_secret " + name + " fail: " + str(e)[:60])
        return False


def dispatch(wf):
    if not GHP: return
    req = urllib.request.Request(
        "https://api.github.com/repos/" + REPO + "/actions/workflows/" + wf + "/dispatches",
        data=json.dumps({"ref":"main"}).encode(),
        headers={"Authorization":"token " + GHP, "Content-Type":"application/json"},
        method="POST")
    try:
        urllib.request.urlopen(req, timeout=10)
        print("Dispatch: " + wf)
    except Exception as e:
        print("Dispatch fail " + wf + ": " + str(e)[:60])


def has_strategy():
    from datetime import datetime, timezone
    week_id = datetime.now(timezone.utc).strftime("%Y-W%V")
    req = urllib.request.Request(
        SBU + "/rest/v1/strategy_decisions?week_id=eq." + week_id + "&select=id&limit=1",
        headers=H)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return len(json.loads(r.read())) > 0
    except:
        return False


def main():
    print("=== FIX + PIPELINE | aguardando banco ===")

    # Aguardar banco (até 20 minutos)
    for attempt in range(40):
        print("Tentativa " + str(attempt+1) + "/40...")
        if sb_ok():
            break
        time.sleep(30)
    else:
        print("TIMEOUT — banco nao se recuperou em 20 minutos")
        sys.exit(1)

    print("\nBanco OK! Recuperando secrets do ia_cache...")

    # Recuperar YOUTUBE_API_KEY e outros secrets do ia_cache → GitHub Secrets
    secrets_to_sync = [
        "YOUTUBE_API_KEY",
        "YOUTUBE_ACCESS_TOKEN",
    ]
    for sname in secrets_to_sync:
        val = get_secret_from_cache(sname)
        if val and len(val) > 10:
            print("  " + sname + ": " + val[:12] + "..." + val[-4:] + " (" + str(len(val)) + " chars)")
            set_github_secret(sname, val)
        else:
            print("  " + sname + ": nao encontrado no ia_cache")

    # Verificar e disparar pipeline
    print("\nVerificando pipeline...")
    if not has_strategy():
        print("Disparando pipeline completo...")
        dispatch("research-agent.yml")
        time.sleep(180)
        dispatch("strategy-agent.yml")
        time.sleep(180)
        dispatch("seo-agent.yml")
        time.sleep(5)
        dispatch("analytics-agent.yml")
        print("Pipeline disparado!")
    else:
        print("Pipeline desta semana ja concluido")
        dispatch("analytics-agent.yml")


if __name__ == "__main__":
    main()
