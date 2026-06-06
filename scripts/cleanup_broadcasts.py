#!/usr/bin/env python3
"""
cleanup_broadcasts.py — Apaga TODOS os broadcasts exceto o único ativo
Usa broadcastStatus=all para pegar absolutamente todos
"""
import os, json, urllib.request, urllib.parse, time

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]

def log(m): print(m, flush=True)

def get_token():
    data = urllib.parse.urlencode({
        "client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())["access_token"]

def yt_get(token, url):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  GET err: {e}")
        return {}

def main():
    token = get_token()
    log("Token OK")

    # Usar broadcastStatus=all para pegar absolutamente todos
    all_bc = {}
    next_token = None
    page = 0
    while True:
        page += 1
        url = "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status&broadcastStatus=all&maxResults=50"
        if next_token:
            url += f"&pageToken={next_token}"
        data = yt_get(token, url)
        for item in data.get("items", []):
            bc_id = item["id"]
            lc    = item["status"]["lifeCycleStatus"]
            title = item["snippet"]["title"][:60]
            all_bc[bc_id] = {"lc": lc, "title": title}
        log(f"  Página {page}: {len(data.get('items',[]))} broadcasts")
        next_token = data.get("nextPageToken")
        if not next_token:
            break

    log(f"\nTotal broadcasts: {len(all_bc)}")
    for bc_id, info in all_bc.items():
        log(f"  {bc_id} [{info['lc']}] {info['title'][:50]}")

    # Identificar o broadcast ATIVO (live/testing)
    ESTADOS_ATIVOS = {"live","testing","testStarting","liveStarting"}
    ativos = {bc_id: info for bc_id, info in all_bc.items()
              if info["lc"] in ESTADOS_ATIVOS}

    log(f"\nAtivos ({len(ativos)}): {list(ativos.keys())}")

    if len(ativos) > 1:
        log("⚠️  Múltiplos broadcasts ativos! Manter apenas o mais recente.")
        # Manter apenas o último (mapeado por ordem no dict — preserva ordem de inserção)
        manter_id = list(ativos.keys())[-1]
        manter_ids = {manter_id}
        log(f"   Mantendo: {manter_id}")
    elif len(ativos) == 1:
        manter_ids = set(ativos.keys())
        log(f"   Mantendo: {list(manter_ids)[0]}")
    else:
        manter_ids = set()
        log("   Nenhum broadcast ativo — limpando tudo")

    # Deletar todos os outros
    deletados = 0
    erros = 0
    for bc_id, info in all_bc.items():
        if bc_id in manter_ids:
            log(f"  ✅ MANTER: {bc_id} [{info['lc']}]")
            continue
        lc = info["lc"]
        log(f"  🗑  Deletando {bc_id} [{lc}] {info['title'][:35]}...")

        # Transicionar para complete se necessário
        if lc in ["ready","created","testStarting","testing","liveStarting"]:
            try:
                req = urllib.request.Request(
                    f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bc_id}&part=id",
                    data=b"{}", method="POST"
                )
                req.add_header("Authorization", f"Bearer {token}")
                req.add_header("Content-Type", "application/json")
                urllib.request.urlopen(req, timeout=10)
                time.sleep(1)
            except Exception as e:
                pass  # Ignorar erros de transição

        # Deletar
        req = urllib.request.Request(
            f"https://www.googleapis.com/youtube/v3/liveBroadcasts?id={bc_id}",
            method="DELETE"
        )
        req.add_header("Authorization", f"Bearer {token}")
        try:
            urllib.request.urlopen(req, timeout=10)
            deletados += 1
        except Exception as e:
            log(f"    Err deletar: {e}")
            erros += 1
        time.sleep(0.3)

    log(f"\n✅ Concluído: {deletados} deletados | {erros} erros | {len(manter_ids)} mantidos")

if __name__ == "__main__":
    main()
