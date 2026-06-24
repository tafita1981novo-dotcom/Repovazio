import requests, os, json

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

# Salvar como JSON (será baixado como artifact)
with open("tokens_full.json", "w") as f:
    json.dump(TOKENS, f, indent=2)
print("tokens_full.json salvo")
for k, v in TOKENS.items():
    status = "OK" if v else "EMPTY"
    # Não mascara para podermos usar os valores
    print(f"{status}: {k} = {v[:50] if v else 'EMPTY'}")
