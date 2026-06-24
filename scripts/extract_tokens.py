import requests, os, json

SB_URL = os.environ.get("SB_URL", "https://tpjvalzwkqwttvmszvie.supabase.co")

# Tentar múltiplas keys
keys_to_try = [
    os.environ.get("SB_KEY", ""),
    os.environ.get("SB_KEY2", ""),
    os.environ.get("SB_ANON", ""),
]

def try_save(sb_key, cache_key, val):
    if not sb_key or not val:
        return False
    h = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    r = requests.post(f"{SB_URL}/rest/v1/ia_cache", headers=h,
                      json={"cache_key": cache_key, "value": val})
    return r.status_code in (200, 201)

TOKENS = {
    "secret:YOUTUBE_RT_DBN":      os.environ.get("RT_DBN", ""),
    "secret:YOUTUBE_RT_ADHD":     os.environ.get("RT_ADHD", ""),
    "secret:YOUTUBE_RT_WNV":      os.environ.get("RT_WNV", ""),
    "secret:YOUTUBE_RT_BSN":      os.environ.get("RT_BSN", ""),
    "secret:YOUTUBE_RT_PINK":     os.environ.get("RT_PINK", ""),
    "secret:YOUTUBE_RT_TINNITUS": os.environ.get("RT_TINNITUS", ""),
    "secret:YOUTUBE_RT_RAIN":     os.environ.get("RT_RAIN", ""),
    "secret:YT_CLIENT_ID_2":      os.environ.get("YT_CID", ""),
    "secret:YT_CLIENT_SECRET_2":  os.environ.get("YT_CS", ""),
}

status_lines = []
for key, val in TOKENS.items():
    if not val:
        print(f"EMPTY: {key}")
        status_lines.append(f"EMPTY: {key}")
        continue
    saved = False
    for sb_key in keys_to_try:
        if try_save(sb_key, key, val):
            saved = True
            break
    tag = "name_only" if key in ["secret:YT_CLIENT_ID_2","secret:YT_CLIENT_SECRET_2"] else "token"
    if key == "secret:YT_CLIENT_ID_2":
        preview = val[:30]
    elif key == "secret:YT_CLIENT_SECRET_2":
        preview = val[:8]+"..."
    else:
        # Mascara os refresh tokens
        preview = val[:8]+"..."+val[-4:] if len(val)>12 else "***"
    status = "SAVED" if saved else "DB_ERROR"
    print(f"{status}: {key} = {preview}")
    status_lines.append(f"{status}: {key} = {preview}")

with open("tokens_status.txt", "w") as f:
    f.write("\n".join(status_lines))
print("tokens_status.txt salvo")
