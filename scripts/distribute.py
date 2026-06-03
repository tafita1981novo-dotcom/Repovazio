#!/usr/bin/env python3
"""
psicologia.doc — Distribuidor v3
- Quota manager: para quando esgota, retoma amanhã
- Tag sanitizer
- Agendamento por horário de pico (18-20h BRT)
- Suporte a múltiplos clientes OAuth (round-robin para dobrar quota)
"""
import os, sys, json, time, re, urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone

SBU = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
H_SB = {"apikey": SBK, "Authorization": f"Bearer {SBK}"}
H_SB_J = {**H_SB, "Content-Type": "application/json"}
MAX_VIDEOS = int(os.environ.get("MAX_VIDEOS", "20"))
QUOTA_KEY = "quota:yt_used_today"

def log(*a): print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)

def http_json(url, method="GET", body=None, headers=None, timeout=300, raw_body=False):
    h = dict(headers or {})
    data = None
    if body is not None:
        if raw_body or isinstance(body, (bytes, bytearray)):
            data = body if isinstance(body, (bytes, bytearray)) else body.encode()
        else:
            data = json.dumps(body).encode()
            h.setdefault("Content-Type", "application/json")
    h.setdefault("User-Agent", "psicologia-doc-dist/3.0")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else b"", dict(e.headers or {})

def sb_select(table, q):
    s, b, _ = http_json(f"{SBU}/rest/v1/{table}?{q}", headers=H_SB)
    if s != 200: raise RuntimeError(f"select {table} {s}: {b[:200]}")
    return json.loads(b)

def sb_patch(table, q, payload):
    s, b, _ = http_json(f"{SBU}/rest/v1/{table}?{q}", method="PATCH",
                       body=payload, headers=H_SB_J)
    if s not in (200, 204): raise RuntimeError(f"patch {table} {s}: {b[:200]}")

def get_cache(key):
    rows = sb_select("ia_cache", f"cache_key=eq.{urllib.parse.quote(key)}&select=value")
    return rows[0]["value"] if rows else None

def set_cache(key, value):
    s, _, _ = http_json(f"{SBU}/rest/v1/ia_cache", method="POST",
        body={"cache_key": key, "value": str(value), "expires_at": "2030-01-01T00:00:00Z"},
        headers={**H_SB_J, "Prefer": "resolution=merge-duplicates"})
    return s

# ── Quota Manager ─────────────────────────────────────────────────────────────
QUOTA_PER_UPLOAD = 1600
QUOTA_DAILY = 9500  # margem de segurança (10000 - 500)

def get_quota_used():
    """Retorna quota usada hoje (UTC). Reseta automaticamente à meia-noite."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw = get_cache(f"quota:yt:{today}")
    if not raw:
        return 0
    try:
        return int(raw)
    except:
        return 0

def add_quota(units):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    current = get_quota_used()
    set_cache(f"quota:yt:{today}", current + units)

def quota_available():
    used = get_quota_used()
    remaining = QUOTA_DAILY - used
    log(f"  [quota] {used}/{QUOTA_DAILY} units usadas hoje | {remaining} restantes | ~{remaining//QUOTA_PER_UPLOAD} uploads possíveis")
    return remaining >= QUOTA_PER_UPLOAD

# ── YT creds (suporte a múltiplos projetos OAuth) ─────────────────────────────
def _load_yt_creds(prefix=""):
    """Carrega credenciais YT. prefix vazio = projeto 1, '2_' = projeto 2"""
    keys = [f"secret:YT_CLIENT_ID{prefix}", f"secret:YT_CLIENT_SECRET{prefix}", f"secret:YT_REFRESH_TOKEN{prefix}"]
    q = "cache_key=in.(" + ",".join(urllib.parse.quote(k) for k in keys) + ")&select=cache_key,value"
    s, b, _ = http_json(f"{SBU}/rest/v1/ia_cache?{q}", headers=H_SB)
    if s != 200: return {}
    creds = {}
    for row in json.loads(b):
        k = row["cache_key"].replace("secret:YT_", "").replace(prefix, "")
        if row.get("value"): creds[k] = row["value"].strip()
    return creds

def get_yt_token(creds):
    if not all(creds.get(k) for k in ["CLIENT_ID","CLIENT_SECRET","REFRESH_TOKEN"]):
        return None
    body = urllib.parse.urlencode({
        "client_id": creds["CLIENT_ID"], "client_secret": creds["CLIENT_SECRET"],
        "refresh_token": creds["REFRESH_TOKEN"], "grant_type": "refresh_token",
    }).encode()
    s, raw, _ = http_json("https://oauth2.googleapis.com/token", method="POST",
        body=body, raw_body=True,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    if s != 200:
        log(f"  YT token fail {s}: {raw[:200]}")
        return None
    return json.loads(raw)["access_token"]

def get_best_token():
    """Tenta projeto 1, depois projeto 2 se disponível"""
    creds1 = _load_yt_creds("")
    if creds1:
        tok = get_yt_token(creds1)
        if tok: return tok, "proj1"
    creds2 = _load_yt_creds("_2")
    if creds2:
        tok = get_yt_token(creds2)
        if tok: return tok, "proj2"
    return None, None

# ── Tag Sanitizer ─────────────────────────────────────────────────────────────
def sanitize_tags(tags):
    if not tags: return []
    cleaned, total = [], 0
    base = ["psicologia", "saude mental", "comportamento humano", "psicologia doc", "Daniela Coelho"]
    all_tags = list(tags) + base
    for tag in all_tags:
        tag = re.sub(r'[#@&<>"\'/\\|!?.,;:(){}[\]+=*^%$~`]', '', str(tag)).strip()
        tag = re.sub(r'\s+', ' ', tag)
        if 2 <= len(tag) <= 30 and tag not in cleaned:
            if total + len(tag) + 1 <= 490:
                cleaned.append(tag)
                total += len(tag) + 1
    return cleaned[:15]

# ── YouTube Upload ─────────────────────────────────────────────────────────────
def yt_publish(mp4_url, title, description, tags, is_shorts=False):
    if not mp4_url: return None, "NO_MP4_URL"
    if not quota_available(): return None, "QUOTA_ESGOTADA"
    tok, proj = get_best_token()
    if not tok: return None, "YT_CREDENTIALS_MISSING"
    log(f"  usando {proj}")
    log(f"  downloading {mp4_url[:60]}…")
    try:
        with urllib.request.urlopen(mp4_url, timeout=300) as r:
            mp4_bytes = r.read()
    except Exception as e:
        return None, f"DOWNLOAD_FAIL: {e}"
    log(f"  downloaded {len(mp4_bytes):,} bytes")
    if is_shorts and "#Shorts" not in (description or ""):
        description = (description or "") + "\n\n#Shorts"
    metadata = {
        "snippet": {
            "title": (title or "")[:100],
            "description": (description or "")[:5000],
            "tags": sanitize_tags(tags or []),
            "categoryId": "27",
            "defaultLanguage": "pt-BR",
            "defaultAudioLanguage": "pt-BR",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    s1, raw1, hdrs1 = http_json(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        method="POST", body=metadata,
        headers={"Authorization": f"Bearer {tok}",
                 "X-Upload-Content-Type": "video/mp4",
                 "X-Upload-Content-Length": str(len(mp4_bytes))})
    if s1 != 200:
        err = raw1[:300].decode(errors='ignore')
        if "uploadLimitExceeded" in err or "exceeded" in err:
            add_quota(QUOTA_DAILY)  # marcar quota como esgotada
            return None, "QUOTA_ESGOTADA"
        return None, f"YT_INIT_FAIL_{s1}_{err}"
    upload_url = hdrs1.get("location") or hdrs1.get("Location")
    if not upload_url: return None, "YT_NO_UPLOAD_URL"
    s2, raw2, _ = http_json(upload_url, method="PUT", body=mp4_bytes, raw_body=True,
                            headers={"Content-Type": "video/mp4",
                                     "Content-Length": str(len(mp4_bytes))})
    if s2 not in (200, 201): return None, f"YT_UPLOAD_FAIL_{s2}_{raw2[:200].decode(errors='ignore')}"
    video_id = json.loads(raw2).get("id", "")
    add_quota(QUOTA_PER_UPLOAD)
    return f"https://youtu.be/{video_id}", None

def get_video_url(r):
    return r.get("mp4_url") or r.get("video_url")

PUBLISHERS = {
    "youtube_long":   lambda r: yt_publish(get_video_url(r), r.get("youtube_title") or r["title"], r.get("youtube_description"), r.get("youtube_tags"), is_shorts=False),
    "youtube_shorts": lambda r: yt_publish(get_video_url(r), r.get("youtube_title") or r["title"], r.get("youtube_description"), r.get("youtube_tags"), is_shorts=True),
    "youtube":        lambda r: yt_publish(get_video_url(r), r.get("youtube_title") or r["title"], r.get("youtube_description"), r.get("youtube_tags"), is_shorts=r.get("format")=="short"),
}

def main():
    # Verificar quota ANTES de buscar vídeos
    if not quota_available():
        log("QUOTA ESGOTADA para hoje. Aguardando reset às 00:00 UTC.")
        return

    rows = sb_select("content_pipeline",
        f"status=eq.mp4_ready&select=id,title,target_platform,format,mp4_url,video_url,"
        f"youtube_title,youtube_description,youtube_tags,metadata"
        f"&order=id.asc&limit={MAX_VIDEOS}")
    log(f"found {len(rows)} mp4_ready pipelines (max={MAX_VIDEOS})")
    published = failed = quota_hit = 0
    for r in rows:
        if not quota_available():
            log(f"  Quota esgotada após {published} publicações.")
            quota_hit += 1
            break
        fmt = r.get("format", "short")
        target = r.get("target_platform") or ("youtube_shorts" if fmt == "short" else "youtube_long")
        pub = PUBLISHERS.get(target) or PUBLISHERS.get("youtube")
        if not pub:
            log(f"  [{r['id']}] sem publisher para target={target}"); continue
        log(f"  [{r['id']}] {target} → {(get_video_url(r) or 'NONE')[:50]}")
        try:
            yt_url, err = pub(r)
            if err:
                if "QUOTA" in err:
                    log(f"    QUOTA ESGOTADA — parando")
                    quota_hit += 1
                    break
                log(f"    FAILED: {err[:120]}")
                sb_patch("content_pipeline", f"id=eq.{r['id']}", {"error": err[:400]})
                failed += 1
            else:
                log(f"    PUBLISHED → {yt_url}")
                sb_patch("content_pipeline", f"id=eq.{r['id']}", {
                    "status": "published", "youtube_url": yt_url,
                    "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "error": None
                })
                published += 1
                time.sleep(3)
        except Exception as e:
            log(f"    EXCEPTION: {e}")
            sb_patch("content_pipeline", f"id=eq.{r['id']}", {"error": str(e)[:400]})
            failed += 1
    log(f"DONE: {published} published | {failed} failed | {quota_hit} quota_hit")

if __name__ == "__main__":
    main()
