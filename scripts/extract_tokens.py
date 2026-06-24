import requests, os

SB_URL = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY = os.environ["SB_KEY"]
SB_H = {
    "apikey": SB_KEY,
    "Authorization": f"Bearer {SB_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

TOKENS = {
    "secret:YOUTUBE_RT_DBN":     os.environ.get("RT_DBN",""),
    "secret:YOUTUBE_RT_ADHD":    os.environ.get("RT_ADHD",""),
    "secret:YOUTUBE_RT_WNV":     os.environ.get("RT_WNV",""),
    "secret:YOUTUBE_RT_BSN":     os.environ.get("RT_BSN",""),
    "secret:YOUTUBE_RT_PINK":    os.environ.get("RT_PINK",""),
    "secret:YOUTUBE_RT_TINNITUS":os.environ.get("RT_TINNITUS",""),
    "secret:YOUTUBE_RT_RAIN":    os.environ.get("RT_RAIN",""),
    "secret:YT_CLIENT_ID_2":     os.environ.get("YT_CID",""),
    "secret:YT_CLIENT_SECRET_2": os.environ.get("YT_CS",""),
}

for key, val in TOKENS.items():
    if val:
        r = requests.post(f"{SB_URL}/rest/v1/ia_cache", headers=SB_H,
                          json={"cache_key": key, "value": val})
        print(f"{'OK' if r.status_code in (200,201) else 'ERR '+str(r.status_code)}: {key}")
    else:
        print(f"VAZIO: {key}")
