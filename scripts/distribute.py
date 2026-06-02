#!/usr/bin/env python3
"""
psicologia.doc — Distribuidor automático multi-plataforma.
Roda 24/7 como cron. Pega pipelines `mp4_ready` e tenta publicar conforme
o `target_platform` de cada um. Se faltar OAuth/token de uma plataforma,
marca como `pending_credentials` e segue.

Plataformas suportadas:
  - youtube_long / youtube_shorts: YouTube Data API v3
  - instagram_reels:  Instagram Graph API (Business account via Facebook Page)
  - tiktok_short:     TikTok Content Posting API
  - pinterest_pin:    Pinterest API v5

Cada plataforma é OPCIONAL — se faltar token, pipeline fica em
`pending_credentials` aguardando o user conectar a conta.
"""
import os, sys, json, time, urllib.request, urllib.error, urllib.parse
from pathlib import Path

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

# ─── Ler credenciais do Supabase ia_cache (prioridade sobre env vars) ────────
def _load_yt_creds_from_supabase():
    """
    Lê YT_CLIENT_ID, YT_CLIENT_SECRET e YT_REFRESH_TOKEN do Supabase ia_cache.
    Prioridade sobre as env vars para permitir renovação via yt-oauth Edge Function.
    """
    try:
        keys = ("secret:YT_CLIENT_ID", "secret:YT_CLIENT_SECRET", "secret:YT_REFRESH_TOKEN",
                "secret:YT_CLIENT_ID", "secret:YT_CLIENT_SECRET", "secret:YT_REFRESH_TOKEN")
        q = "cache_key=in.(secret:YT_CLIENT_ID,secret:YT_CLIENT_SECRET,secret:YT_REFRESH_TOKEN)&select=cache_key,value"
        s, b, _ = http_json(f"{SBU}/rest/v1/ia_cache?{q}", headers=H_SB)
        if s == 200:
            creds = {}
            for row in json.loads(b):
                k = row["cache_key"].replace("secret:", "")
                v = (row.get("value") or "").strip()
                if v:
                    creds[k] = v
            if creds:
                log(f"  [yt_creds] loaded from Supabase: {list(creds.keys())}")
            return creds
    except Exception as e:
        log(f"  [yt_creds] Supabase read failed (using env vars): {e}")
    return {}

# ─── Optional platform credentials (env vars como fallback) ─────────────────
_yt_creds_cache = {}
def _get_yt(key: str) -> str:
    global _yt_creds_cache
    if not _yt_creds_cache:
        _yt_creds_cache = _load_yt_creds_from_supabase()
    return _yt_creds_cache.get(key) or os.environ.get(key, "")

IG_USER_ID       = os.environ.get("IG_USER_ID", "")
IG_ACCESS_TOKEN  = os.environ.get("IG_ACCESS_TOKEN", "")
TT_CLIENT_KEY    = os.environ.get("TT_CLIENT_KEY", "")
TT_ACCESS_TOKEN  = os.environ.get("TT_ACCESS_TOKEN", "")
PIN_ACCESS_TOKEN = os.environ.get("PIN_ACCESS_TOKEN", "")
PIN_BOARD_ID     = os.environ.get("PIN_BOARD_ID", "")

# ─── YouTube ─────────────────────────────────────────────────────────────────
def yt_get_access_token():
    client_id     = _get_yt("YT_CLIENT_ID")
    client_secret = _get_yt("YT_CLIENT_SECRET")
    refresh_token = _get_yt("YT_REFRESH_TOKEN")

    if not (client_id and client_secret and refresh_token):
        log(f"  [yt] missing creds: id={bool(client_id)} secret={bool(client_secret)} refresh={bool(refresh_token)}")
        return None
    body = urllib.parse.urlencode({
        "client_id": client_id, "client_secret": client_secret,
        "refresh_token": refresh_token, "grant_type": "refresh_token",
    }).encode()
    s, raw, _ = http_json("https://oauth2.googleapis.com/token", method="POST",
        body=body, raw_body=True,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    if s != 200: log(f"  YT token fail {s}: {raw[:200]}"); return None
    return json.loads(raw)["access_token"]

def yt_publish(mp4_url, title, description, tags, is_shorts=False):
    tok = yt_get_access_token()
    if not tok:
        return None, "YT_CREDENTIALS_MISSING"
    # Download MP4 to memory (small — already <30MB target)
    log(f"  downloading {mp4_url}…")
    with urllib.request.urlopen(mp4_url, timeout=300) as r:
        mp4_bytes = r.read()
    log(f"  downloaded {len(mp4_bytes):,} bytes")

    # Resumable upload init
    if is_shorts and "#Shorts" not in (description or ""):
        description = (description or "") + "\n\n#Shorts"
    metadata = {
        "snippet": {
            "title": title[:100],
            "description": (description or "")[:5000],
            "tags": (tags or [])[:30],
            "categoryId": "27",  # Education
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
    rj = json.loads(raw2)
    vid = rj.get("id")
    return f"https://youtu.be/{vid}", None

# ─── Instagram Reels ──────────────────────────────────────────────────────────
def ig_publish(mp4_url, caption):
    if not (IG_USER_ID and IG_ACCESS_TOKEN):
        return None, "IG_CREDENTIALS_MISSING"
    body = urllib.parse.urlencode({
        "media_type": "REELS",
        "video_url": mp4_url,
        "caption": caption[:2200],
        "share_to_feed": "true",
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
        if s == 200 and json.loads(raw).get("status_code") == "FINISHED":
            break
    body = urllib.parse.urlencode({"creation_id": cid, "access_token": IG_ACCESS_TOKEN}).encode()
    s3, raw3, _ = http_json(f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish",
        method="POST", body=body, raw_body=True,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    if s3 != 200: return None, f"IG_PUBLISH_FAIL_{s3}_{raw3[:200].decode(errors='ignore')}"
    pub = json.loads(raw3)
    return f"https://instagram.com/reel/{pub.get('id')}", None

# ─── TikTok ───────────────────────────────────────────────────────────────────
def tt_publish(mp4_url, title):
    if not TT_ACCESS_TOKEN:
        return None, "TT_CREDENTIALS_MISSING"
    init_body = {
        "post_info": {
            "title": title[:150],
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False, "disable_comment": False, "disable_stitch": False,
            "video_cover_timestamp_ms": 1000,
        },
        "source_info": {"source": "PULL_FROM_URL", "video_url": mp4_url},
    }
    s, raw, _ = http_json("https://open.tiktokapis.com/v2/post/publish/video/init/",
        method="POST", body=init_body,
        headers={"Authorization": f"Bearer {TT_ACCESS_TOKEN}"})
    if s != 200: return None, f"TT_INIT_FAIL_{s}_{raw[:200].decode(errors='ignore')}"
    pid = json.loads(raw)["data"]["publish_id"]
    return f"tiktok://publish/{pid}", None

# ─── Pinterest ────────────────────────────────────────────────────────────────
def pin_publish(mp4_url, title, description, board_id):
    if not (PIN_ACCESS_TOKEN and (board_id or PIN_BOARD_ID)):
        return None, "PIN_CREDENTIALS_MISSING"
    return None, "PIN_VIDEO_UPLOAD_FLOW_PENDING"

# ─── Main ─────────────────────────────────────────────────────────────────────
PUBLISHERS = {
    "youtube_long":    lambda r: yt_publish(r["mp4_url"], r["youtube_title"] or r["title"], r["youtube_description"], r["youtube_tags"], is_shorts=False),
    "youtube_shorts":  lambda r: yt_publish(r["mp4_url"], r["youtube_title"] or r["title"], r["youtube_description"], r["youtube_tags"], is_shorts=True),
    "instagram_reels": lambda r: ig_publish(r["mp4_url"], r["youtube_description"] or r["title"]),
    "tiktok_short":    lambda r: tt_publish(r["mp4_url"], r["youtube_title"] or r["title"]),
    "pinterest_pin":   lambda r: pin_publish(r["mp4_url"], r["youtube_title"] or r["title"], r["youtube_description"] or "", r.get("metadata",{}).get("pin_board_id","")),
}

def main():
    rows = sb_select("content_pipeline",
        "status=eq.mp4_ready&select=id,title,target_platform,mp4_url,"
        "youtube_title,youtube_description,youtube_tags,metadata"
        "&order=id.asc&limit=20")
    log(f"found {len(rows)} mp4_ready pipelines")
    for r in rows:
        target = r.get("target_platform") or "youtube_long"
        pub = PUBLISHERS.get(target)
        if not pub:
            log(f"  [{r['id']}] no publisher for target={target}, skipping"); continue
        log(f"  [{r['id']}] {target} → {r['mp4_url']}")
        try:
            url, err = pub(r)
        except Exception as e:
            url, err = None, f"EXCEPTION:{e}"
        if url:
            sb_patch("content_pipeline", f"id=eq.{r['id']}", {
                "status": "published",
                "youtube_url": url if "youtube" in target else None,
                "metadata": {**(r.get("metadata") or {}), "published_url": url, "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
            })
            log(f"    PUBLISHED → {url}")
        elif err and "CREDENTIALS_MISSING" in err:
            sb_patch("content_pipeline", f"id=eq.{r['id']}", {
                "status": "pending_credentials",
                "error": err,
            })
            log(f"    PENDING (need OAuth): {err}")
        else:
            sb_patch("content_pipeline", f"id=eq.{r['id']}", {
                "error": err or "UNKNOWN",
            })
            log(f"    FAILED: {err}")

if __name__ == "__main__":
    main()
