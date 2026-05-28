#!/usr/bin/env python3
"""
provision_stream_keys.py (v2) - Agente autonomo: stream key + broadcast 24/7.

Para cada idioma alvo sem secret YOUTUBE_STREAM_KEY_<LANG>:
  1. tenta cada conjunto de credenciais OAuth (YOUTUBE_* e, p/ PT, YT_* como fallback);
  2. liveStreams.insert -> stream id + stream key;
  3. grava a key como GitHub secret (libsodium) e espelha no Supabase ia_cache;
  4. se CREATE_BROADCAST=1: liveBroadcasts.insert (public, enableAutoStart) + bind -> canal entra ao vivo sozinho;
  5. grava relatorio JSON em ia_cache (agent:provision_report).

LIMITE IRREDUTIVEL: o consentimento OAuth e por canal, no navegador, feito por humano 1x.
Sem refresh token valido daquele canal o idioma e PULADO com log de remediacao.
"""
import os, sys, json, base64, time
from datetime import datetime, timezone
import requests
from nacl import encoding, public

REPO     = os.getenv("GH_REPO", "tafita81/Repovazio")
GH_PAT   = os.getenv("GH_PAT", "").strip()
SUPA_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPA_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
CREATE_BROADCAST = os.getenv("CREATE_BROADCAST", "0").strip() == "1"
TARGETS  = [x.strip().upper() for x in (os.getenv("TARGET_LANGS") or
            "PT,EN,ES,DE,FR,IT,JA,KO,AR,ZH,RU,HI").split(",") if x.strip()]
GH = {"Authorization": "Bearer " + GH_PAT, "Accept": "application/vnd.github+json",
      "User-Agent": "psidoc-provisioner", "X-GitHub-Api-Version": "2022-11-28"}

def secret_name(lang):  return "YOUTUBE_STREAM_KEY" if lang == "PT" else "YOUTUBE_STREAM_KEY_" + lang
def refresh_name(lang): return "YOUTUBE_REFRESH_TOKEN" if lang == "PT" else "YOUTUBE_REFRESH_TOKEN_" + lang

def cred_sets(lang):
    out = [(os.getenv("YOUTUBE_CLIENT_ID","").strip(), os.getenv("YOUTUBE_CLIENT_SECRET","").strip(), os.getenv(refresh_name(lang),"").strip())]
    if lang == "PT":
        out.append((os.getenv("YT_CLIENT_ID","").strip(), os.getenv("YT_CLIENT_SECRET","").strip(), os.getenv("YT_REFRESH_TOKEN","").strip()))
    return [c for c in out if all(c)]

def existing_secret_names():
    names, page = set(), 1
    while True:
        r = requests.get("https://api.github.com/repos/%s/actions/secrets?per_page=100&page=%d" % (REPO, page), headers=GH, timeout=30)
        r.raise_for_status()
        chunk = r.json().get("secrets", [])
        names.update(s["name"] for s in chunk)
        if len(chunk) < 100: break
        page += 1
    return names

def get_access_token(cid, csec, rt):
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": cid, "client_secret": csec, "refresh_token": rt, "grant_type": "refresh_token"})
    if r.status_code != 200:
        raise RuntimeError("oauth %d: %s" % (r.status_code, r.text[:140]))
    return r.json()["access_token"]

def create_stream(access_token, lang):
    hdr = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
    body = {"snippet": {"title": "psicologia.doc %s 24/7" % lang},
            "cdn": {"frameRate": "variable", "ingestionType": "rtmp", "resolution": "variable"}}
    r = requests.post("https://www.googleapis.com/youtube/v3/liveStreams?part=snippet,cdn", headers=hdr, data=json.dumps(body), timeout=30)
    if r.status_code not in (200,201):
        raise RuntimeError("liveStreams.insert %d: %s" % (r.status_code, r.text[:200]))
    j = r.json()
    return j["id"], j["cdn"]["ingestionInfo"]["streamName"]

def create_and_bind_broadcast(access_token, stream_id, lang):
    hdr = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {"snippet": {"title": "psicologia.doc %s - LIVE 24/7" % lang, "scheduledStartTime": now},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
            "contentDetails": {"enableAutoStart": True, "enableAutoStop": False, "latencyPreference": "ultraLow"}}
    r = requests.post("https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet,status,contentDetails", headers=hdr, data=json.dumps(body), timeout=30)
    if r.status_code not in (200,201):
        raise RuntimeError("liveBroadcasts.insert %d: %s" % (r.status_code, r.text[:200]))
    bid = r.json()["id"]
    rb = requests.post("https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?part=id,contentDetails&id=%s&streamId=%s" % (bid, stream_id), headers=hdr, timeout=30)
    if rb.status_code not in (200,201):
        raise RuntimeError("liveBroadcasts.bind %d: %s" % (rb.status_code, rb.text[:200]))
    return bid

def get_public_key():
    pk = requests.get("https://api.github.com/repos/%s/actions/secrets/public-key" % REPO, headers=GH, timeout=30)
    pk.raise_for_status(); return pk.json()

def put_repo_secret(name, value, pkj):
    sealed = public.SealedBox(public.PublicKey(pkj["key"].encode(), encoding.Base64Encoder))
    enc = base64.b64encode(sealed.encrypt(value.encode())).decode()
    r = requests.put("https://api.github.com/repos/%s/actions/secrets/%s" % (REPO, name), headers=GH,
                     data=json.dumps({"encrypted_value": enc, "key_id": pkj["key_id"]}), timeout=30)
    if r.status_code not in (201,204):
        raise RuntimeError("put secret %d: %s" % (r.status_code, r.text[:140]))

def supa_upsert(cache_key, value):
    if not (SUPA_URL and SUPA_KEY): return
    h = {"apikey": SUPA_KEY, "Authorization": "Bearer " + SUPA_KEY, "Content-Type": "application/json"}
    try:
        up = requests.patch("%s/rest/v1/ia_cache?cache_key=eq.%s" % (SUPA_URL, cache_key),
                            headers={"apikey": SUPA_KEY, "Authorization": "Bearer " + SUPA_KEY, "Content-Type": "application/json", "Prefer": "return=representation"},
                            data=json.dumps({"value": value}), timeout=20)
        if up.status_code in (200,204) and up.text not in ("[]",""): return
        requests.post("%s/rest/v1/ia_cache" % SUPA_URL, headers=h, data=json.dumps({"cache_key": cache_key, "value": value}), timeout=20)
    except Exception as e:
        print("   (supabase upsert nao critico: %s)" % e)

def main():
    report = {"ts": datetime.now(timezone.utc).isoformat(), "results": {}}
    if not GH_PAT:
        print("ABORT: GH_PAT ausente."); supa_upsert("agent:provision_report", json.dumps({"error": "no GH_PAT"})); return
    existing = existing_secret_names()
    print("Stream-key secrets existentes:", sorted(n for n in existing if "STREAM_KEY" in n))
    pkj = None; criadas = pulei = falhei = 0
    for lang in TARGETS:
        sn = secret_name(lang)
        if sn in existing:
            report["results"][lang] = "skip:secret_exists"; pulei += 1
            print("[%s] ja existe %s -> pulo." % (lang, sn)); continue
        sets = cred_sets(lang)
        if not sets:
            report["results"][lang] = "skip:no_refresh_token"; pulei += 1
            print("[%s] sem %s (precisa consentimento OAuth) -> pulo." % (lang, refresh_name(lang))); continue
        at = None; last_err = ""
        for (cid, csec, rt) in sets:
            try:
                at = get_access_token(cid, csec, rt); break
            except Exception as e:
                last_err = str(e)
        if not at:
            report["results"][lang] = "fail:oauth:" + last_err[:90]; falhei += 1
            print("[%s] OAuth FALHOU (todos cred sets): %s" % (lang, last_err)); continue
        try:
            stream_id, key = create_stream(at, lang)
        except Exception as e:
            report["results"][lang] = "fail:stream:" + str(e)[:90]; falhei += 1
            print("[%s] liveStreams.insert FALHOU: %s" % (lang, e)); continue
        try:
            if pkj is None: pkj = get_public_key()
            put_repo_secret(sn, key, pkj)
        except Exception as e:
            report["results"][lang] = "fail:secret:" + str(e)[:90]; falhei += 1
            print("[%s] gravacao secret FALHOU: %s" % (lang, e)); continue
        supa_upsert("secret:" + sn, key)
        bc = ""
        if CREATE_BROADCAST:
            try:
                bid = create_and_bind_broadcast(at, stream_id, lang); bc = " + broadcast " + bid
            except Exception as e:
                bc = " (broadcast falhou: %s)" % str(e)[:90]
        report["results"][lang] = "ok" + bc; criadas += 1
        print("[%s] OK key+secret %s%s" % (lang, sn, bc)); time.sleep(1)
    report["summary"] = {"criadas": criadas, "puladas": pulei, "falhas": falhei}
    supa_upsert("agent:provision_report", json.dumps(report, ensure_ascii=False))
    print("=== RESUMO: criadas=%d puladas=%d falhas=%d ===" % (criadas, pulei, falhei))

if __name__ == "__main__":
    main()
