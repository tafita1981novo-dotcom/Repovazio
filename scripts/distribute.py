#!/usr/bin/env python3
"""
psicologia.doc — Distribuidor automático v2.
- Tag sanitizer (fix YT_INIT_FAIL_400 invalid keywords)
- Publica até 20 vídeos por run
- Rate limiting inteligente (3s entre uploads)
- Lê YT creds do Supabase ia_cache
"""
import os, sys, json, time, re, urllib.request, urllib.error, urllib.parse

SBU = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
H_SB = {"apikey": SBK, "Authorization": f"Bearer {SBK}"}
H_SB_J = {**H_SB, "Content-Type": "application/json"}
MAX_VIDEOS = int(os.environ.get("MAX_VIDEOS", "20"))

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
    h.setdefault("User-Agent", "psicologia-doc-dist/2.0")
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

# ── YT creds do Supabase (prioridade sobre env vars) ─────────────────────────
_yt_creds = {}
def _get_yt(key: str) -> str:
    global _yt_creds
    if not _yt_creds:
        try:
            q = "cache_key=in.(secret:YT_CLIENT_ID,secret:YT_CLIENT_SECRET,secret:YT_REFRESH_TOKEN)&select=cache_key,value"
            s, b, _ = http_json(f"{SBU}/rest/v1/ia_cache?{q}", headers=H_SB)
            if s == 200:
                for row in json.loads(b):
                    k = row["cache_key"].replace("secret:", "")
                    v = (row.get("value") or "").strip()
                    if v: _yt_creds[k] = v
                log(f"  [yt_creds] Supabase: {list(_yt_creds.keys())}")
        except Exception as e:
            log(f"  [yt_creds] Supabase fail: {e}")
    return _yt_creds.get(key) or os.environ.get(key, "")

# ── Tag Sanitizer ─────────────────────────────────────────────────────────────
def sanitize_tags(tags):
    """YouTube aceita: max 500 chars total, cada tag max 30 chars, sem chars especiais"""
    if not tags: return []
    cleaned = []
    total = 0
    for tag in tags:
        tag = re.sub(r'[#@&<>"\'/\\|!?.,;:(){}[\]+=*^%$~`]', '', str(tag)).strip()
        tag = re.sub(r'\s+', ' ', tag)
        if 2 <= len(tag) <= 30:
            if total + len(tag) + 1 <= 490:
                cleaned.append(tag)
                total += len(tag) + 1
    return cleaned[:15]

# ── YouTube ──────────────────────────────────────────────────────────────────
def yt_get_access_token():
    client_id     = _get_yt("YT_CLIENT_ID")
    client_secret = _get_yt("YT_CLIENT_SECRET")
    refresh_token = _get_yt("YT_REFRESH_TOKEN")
    if not (client_id and client_secret and refresh_token):
        log(f"  [yt] creds faltando")
        return None
    body = urllib.parse.urlencode({
        "client_id": client_id, "client_secret": client_secret,
        "refresh_token": refresh_token, "grant_type": "refresh_token",
    }).encode()
    s, raw, _ = http_json("https://oauth2.googleapis.com/token", method="POST",
        body=body, raw_body=True,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    if s != 200:
        log(f"  YT token fail {s}: {raw[:200]}")
        return None
    return json.loads(raw)["access_token"]

def yt_publish(mp4_url, title, description, tags, is_shorts=False):
    if not mp4_url: return None, "NO_MP4_URL"
    tok = yt_get_access_token()
    if not tok: return None, "YT_CREDENTIALS_MISSING"
    log(f"  downloading {mp4_url[:60]}…")
    try:
        with urllib.request.urlopen(mp4_url, timeout=300) as r:
            mp4_bytes = r.read()
    except Exception as e:
        return None, f"DOWNLOAD_FAIL: {e}"
    log(f"  downloaded {len(mp4_bytes):,} bytes")
    if is_shorts and "#Shorts" not in (description or ""):
        description = (description or "") + "\n\n#Shorts"
    clean_tags = sanitize_tags(tags or [])
    # Adicionar tags padrão do canal
    base_tags = ["psicologia", "comportamento humano", "saude mental", "psicologia doc"]
    for t in base_tags:
        if t not in clean_tags: clean_tags.append(t)
    clean_tags = sanitize_tags(clean_tags)
    metadata = {
        "snippet": {
            "title": (title or "")[:100],
            "description": (description or "")[:5000],
            "tags": clean_tags,
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
    if s1 != 200: return None, f"YT_INIT_FAIL_{s1}_{raw1[:300].decode(errors='ignore')}"
    upload_url = hdrs1.get("location") or hdrs1.get("Location")
    if not upload_url: return None, "YT_NO_UPLOAD_URL"
    s2, raw2, _ = http_json(upload_url, method="PUT", body=mp4_bytes, raw_body=True,
                            headers={"Content-Type": "video/mp4",
                                     "Content-Length": str(len(mp4_bytes))})
    if s2 not in (200, 201): return None, f"YT_UPLOAD_FAIL_{s2}_{raw2[:200].decode(errors='ignore')}"
    video_id = json.loads(raw2).get("id", "")
    return f"https://youtu.be/{video_id}", None

def get_video_url(r):
    return r.get("mp4_url") or r.get("video_url")

PUBLISHERS = {
    "youtube_long":    lambda r: yt_publish(get_video_url(r), r.get("youtube_title") or r["title"], r.get("youtube_description"), r.get("youtube_tags"), is_shorts=False),
    "youtube_shorts":  lambda r: yt_publish(get_video_url(r), r.get("youtube_title") or r["title"], r.get("youtube_description"), r.get("youtube_tags"), is_shorts=True),
    "youtube":         lambda r: yt_publish(get_video_url(r), r.get("youtube_title") or r["title"], r.get("youtube_description"), r.get("youtube_tags"), is_shorts=r.get("format")=="short"),
}

def main():
    rows = sb_select("content_pipeline",
        f"status=eq.mp4_ready&select=id,title,target_platform,format,mp4_url,video_url,"
        f"youtube_title,youtube_description,youtube_tags,metadata"
        f"&order=id.asc&limit={MAX_VIDEOS}")
    log(f"found {len(rows)} mp4_ready pipelines (max={MAX_VIDEOS})")
    published = 0
    failed = 0
    for r in rows:
        fmt = r.get("format", "short")
        target = r.get("target_platform") or ("youtube_shorts" if fmt == "short" else "youtube_long")
        pub = PUBLISHERS.get(target) or PUBLISHERS.get("youtube")
        if not pub:
            log(f"  [{r['id']}] sem publisher para target={target}")
            continue
        url_preview = (get_video_url(r) or "NONE")[:50]
        log(f"  [{r['id']}] {target} → {url_preview}")
        try:
            yt_url, err = pub(r)
            if err:
                log(f"    FAILED: {err[:150]}")
                sb_patch("content_pipeline", f"id=eq.{r['id']}", {"error": err[:500]})
                failed += 1
            else:
                log(f"    PUBLISHED → {yt_url}")
                sb_patch("content_pipeline", f"id=eq.{r['id']}", {
                    "status": "published",
                    "youtube_url": yt_url,
                    "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "error": None
                })
                published += 1
                time.sleep(3)  # rate limiting
        except Exception as e:
            log(f"    EXCEPTION: {e}")
            sb_patch("content_pipeline", f"id=eq.{r['id']}", {"error": str(e)[:500]})
            failed += 1
    log(f"DONE: {published} published, {failed} failed")

if __name__ == "__main__":
    main()
