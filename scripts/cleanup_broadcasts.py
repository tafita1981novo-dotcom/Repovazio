#!/usr/bin/env python3
"""
cleanup_broadcasts.py — Apaga TODOS os broadcasts exceto o único ativo
Roda uma vez para limpar o acúmulo histórico
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
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def main():
    token = get_token()
    log("Token OK")

    # Listar TODOS os broadcasts
    all_bc = {}
    for status in ["active","live","ready","created","complete","testStarting","testing"]:
        url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status&broadcastStatus={status}&maxResults=50"
        try:
            data = yt_get(token, url)
            for item in data.get("items", []):
                bc_id = item["id"]
                lc    = item["status"]["lifeCycleStatus"]
                title = item["snippet"]["title"][:60]
                all_bc[bc_id] = {"lc": lc, "title": title}
        except Exception as e:
            log(f"  Erro listar {status}: {e}")

    log(f"\nTotal broadcasts encontrados: {len(all_bc)}")

    # Identificar o broadcast ATIVO (live ou testing)
    ativo = [(bc_id, info) for bc_id, info in all_bc.items()
             if info["lc"] in ["live", "testing", "testStarting", "liveStarting"]]

    log(f"Broadcasts ativos: {len(ativo)}")
    for bc_id, info in ativo:
        log(f"  MANTER → {bc_id} [{info['lc']}] {info['title']}")

    manter_ids = {bc_id for bc_id, _ in ativo}

    # Deletar todos os outros
    deletados = 0
    erros = 0
    for bc_id, info in all_bc.items():
        if bc_id in manter_ids:
            continue
        lc = info["lc"]
        log(f"  Deletando {bc_id} [{lc}] {info['title'][:40]}...")

        # Transicionar para complete se necessário
        if lc in ["ready", "created", "testStarting", "testing"]:
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
                pass

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
            log(f"    Erro: {e}")
            erros += 1
        time.sleep(0.3)

    log(f"\n✅ Limpeza concluída: {deletados} deletados | {erros} erros | {len(manter_ids)} mantidos")

if __name__ == "__main__":
    main()
