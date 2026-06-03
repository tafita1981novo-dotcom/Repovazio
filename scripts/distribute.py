#!/usr/bin/env python3
"""
psicologia.doc — Distribuidor automático multi-plataforma.
Prioridade: lê YT_REFRESH_TOKEN do Supabase ia_cache (bypass GitHub Secret).
Usa video_url como fallback para mp4_url.
"""
import os, sys, json, time, urllib.request, urllib.error, urllib.parse

SBU = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
H_SB = {"apikey": SBK, "Authorization": f"Bearer {SBK}"}
H_SB_J = {**H_SB, "Content-Type": "application/json"}

def log(*a): print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)

def http_json(url, method="GET", body=None, headers=None, timeout=180, raw_body=False):
    h = dict(headers or {})
    data = None
    if body is not None:
        if raw_body or isinstance(body, (bytes, bytearray)):
            data = body if isinstance(body, (bytes, bytearray)) else body.encode()
        else:
            data = json.dumps(body).encode()
            h.setdefault("Content-Type", "application/json")
    h.setdefault("User-Agent", "psicologia-doc-dist/1.0")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else b"", dict(e.headers or {})

def sb_select(table, q):
    s, b, _ = http_json(f"{SBU}/rest/v1/{table}?{q}", headers=H_SB)
    if s != 200: raise RuntimeError(f"select {table} {s}")
    return json.loads(b)

def sb_patch(table, q, payload):
    s, b, _ = http_json(f"{SBU}/rest/v1/{table}?{q}", method="PATCH",
                       body=payload, headers=H_SB_J)
    if s not in (200, 204): raise RuntimeError(f"patch {table} {s}: {b[:200]}")

# ─── Credenciais YT do Supabase ia_cache (prioridade) ────────────────────────
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

# ─── Plataformas extras (env vars) ────────────────────────────────────────────
IG_USER_ID       = os.environ.get("IG_USER_ID", "")
IG_ACCESS_TOKEN  = os.environ.get("IG_ACCESS_TOKEN", "")
TT_ACCESS_TOKEN  = os.environ.get("TT_ACCESS_TOKEN", "")
PIN_ACCESS_TOKEN = os.environ.get("PIN_ACCESS_TOKEN", "")
PIN_BOARD_ID     = os.environ.get("PIN_BOARD_ID", "")

# ─── YouTube ──────────────────────────────────────────────────────────────────
def yt_get_access_token():
    client_id     = _get_yt("YT_CLIENT_ID")
    client_secret = _get_yt("YT_CLIENT_SECRET")
    refresh_token = _get_yt("YT_REFRESH_TOKEN")
    if not (client_id and client_secret and refresh_token):
        log(f"  [yt] creds faltando: id={bool(client_id)} secret={bool(client_secret)} refresh={bool(refresh_token)}")
        return None
    body = urllib.parse.urlencode({
        "client_id": client_id, "client_secret": client_secret,
        "refresh_token": refresh_token, "grant_type": "refresh_token",
    }).encode()
    s, raw, _ = http_json("https://oauth2.googleapis.com/token", method="POST",
        body=body, raw_body=True,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    if s != 200:
        log(f"  YT token fail {s}: {raw[:300]}")
        return None
    return json.loads(raw)["access_token"]

def yt_publish(mp4_url, title, description, tags, is_shorts=False):
    if not mp4_url:
        return None, "NO_MP4_URL"
    tok = yt_get_access_token()
    if not tok:
        return None, "YT_CREDENTIALS_MISSING"
    log(f"  downloading {mp4_url[:60]}…")
    with urllib.request.urlopen(mp4_url, timeout=300) as r:
        mp4_bytes = r.read()
    log(f"  downloaded {len(mp4_bytes):,} bytes")
    if is_shorts and "#Shorts" not in (description or ""):
        description = (description or "") + "\n\n#Shorts"
    metadata = {
        "snippet": {
            "title": (title or "")[:100],
            "description": (description or "")[:5000],
            "tags": (tags or [])[:30],
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
    if s1 != 200: return None, f"YT_INIT_FAIL_{s1}_{raw1[:200].decode(errors='ignore')}"
    upload_url = hdrs1.get("location") or hdrs1.get("Location")
    if not upload_url: return None, "YT_NO_UPLOAD_URL"
    s2, raw2, _ = http_json(upload_url, method="PUT", body=mp4_bytes, raw_body=True,
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "video/mp4"},
        timeout=600)
    if s2 not in (200, 201): return None, f"YT_PUT_FAIL_{s2}_{raw2[:200].decode(errors='ignore')}"
    vid = json.loads(raw2).get("id")
    return f"https://youtu.be/{vid}", None

# ─── Instagram ────────────────────────────────────────────────────────────────
def ig_publish(mp4_url, caption):
    if not (IG_USER_ID and IG_ACCESS_TOKEN): return None, "IG_CREDENTIALS_MISSING"
    body = urllib.parse.urlencode({
        "media_type": "REELS", "video_url": mp4_url,
        "caption": caption[:2200], "share_to_feed": "true",
        "access_token": IG_ACCESS_TOKEN,
    }).encode()
    s1, raw1, _ = http_json(f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media",
        method="POST", body=body, raw_body=True,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    if s1 != 200: return None, f"IG_CONTAINER_FAIL_{s1}_{raw1[:200].decode(errors='ignore')}"
    cid = json.loads(raw1)["id"]
    for _ in range(30):
        time.sleep(10)
        s, raw, _ = http_json(
            f"https://graph.facebook.com/v21.0/{cid}?fields=status_code&access_token={IG_ACCESS_TOKEN}",
            headers={})
        if s == 200 and json.loads(raw).get("status_code") == "FINISHED": break
    body = urllib.parse.urlencode({"creation_id": cid, "access_token": IG_ACCESS_TOKEN}).encode()
    s3, raw3, _ = http_json(f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish",
        method="POST", body=body, raw_body=True,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    if s3 != 200: return None, f"IG_PUBLISH_FAIL_{s3}_{raw3[:200].decode(errors='ignore')}"
    pub = json.loads(raw3)
    return f"https://instagram.com/reel/{pub.get('id')}", None

# ─── TikTok ───────────────────────────────────────────────────────────────────
def tt_publish(mp4_url, title):
    if not TT_ACCESS_TOKEN: return None, "TT_CREDENTIALS_MISSING"
    s, raw, _ = http_json("https://open.tiktokapis.com/v2/post/publish/video/init/",
        method="POST",
        body={"post_info": {"title": title[:150], "privacy_level": "PUBLIC_TO_EVERYONE",
              "disable_duet": False, "disable_comment": False, "disable_stitch": False},
              "source_info": {"source": "PULL_FROM_URL", "video_url": mp4_url}},
        headers={"Authorization": f"Bearer {TT_ACCESS_TOKEN}"})
    if s != 200: return None, f"TT_INIT_FAIL_{s}_{raw[:200].decode(errors='ignore')}"
    return f"tiktok://publish/{json.loads(raw)['data']['publish_id']}", None

# ─── Main ─────────────────────────────────────────────────────────────────────
def get_video_url(r):
    """video_url fallback quando mp4_url é null"""
    return r.get("mp4_url") or r.get("video_url") or ""

PUBLISHERS = {
    "youtube_long":    lambda r: yt_publish(get_video_url(r), r.get("youtube_title") or r["title"], r.get("youtube_description"), r.get("youtube_tags"), is_shorts=False),
    "youtube_shorts":  lambda r: yt_publish(get_video_url(r), r.get("youtube_title") or r["title"], r.get("youtube_description"), r.get("youtube_tags"), is_shorts=True),
    "instagram_reels": lambda r: ig_publish(get_video_url(r), r.get("youtube_description") or r["title"]),
    "tiktok_short":    lambda r: tt_publish(get_video_url(r), r.get("youtube_title") or r["title"]),
}

def main():
    rows = sb_select("content_pipeline",
        "status=eq.mp4_ready&select=id,title,target_platform,mp4_url,video_url,"
        "youtube_title,youtube_description,youtube_tags,metadata"
        "&order=id.asc&limit=20")
    log(f"found {len(rows)} mp4_ready pipelines")
    for r in rows:
        target = r.get("target_platform") or "youtube_long"
        pub = PUBLISHERS.get(target)
        if not pub:
            log(f"  [{r['id']}] sem publisher para target={target}"); continue
        url_preview = get_video_url(r)[:50] if get_video_url(r) else "NONE"
        log(f"  [{r['id']}] {target} → {url_preview}")
        try:
            url, err = pub(r)
        except Exception as e:
            url, err = None, f"EXCEPTION:{e}"
        if url:
            sb_patch("content_pipeline", f"id=eq.{r['id']}", {
                "status": "published",
                "youtube_url": url if "youtube" in target else None,
                "metadata": {**(r.get("metadata") or {}),
                             "published_url": url,
                             "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
            })
            log(f"    PUBLISHED → {url}")
        elif err and "CREDENTIALS_MISSING" in err:
            sb_patch("content_pipeline", f"id=eq.{r['id']}", {
                "status": "pending_credentials", "error": err})
            log(f"    PENDING OAuth: {err}")
        else:
            sb_patch("content_pipeline", f"id=eq.{r['id']}", {"error": err or "UNKNOWN"})
            log(f"    FAILED: {err}")

if __name__ == "__main__":
    main()
