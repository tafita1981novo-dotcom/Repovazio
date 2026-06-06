#!/usr/bin/env python3
"""
cleanup_broadcasts.py — Apaga broadcasts ANTIGOS, preserva o ativo
Regra: se o canal está ao vivo, manter o broadcast com scheduled mais recente.
Se não está ao vivo, deletar tudo (próximo run vai criar 1 novo).
"""
import os, json, urllib.request, urllib.parse, time, sys

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

def canal_ao_vivo(token):
    """Verifica se o canal está ao vivo agora via liveBroadcasts/list broadcastStatus=active"""
    # Status active = está recebendo stream de dados
    for bs in ["active", "live"]:
        url = f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,status&broadcastStatus={bs}&maxResults=5"
        data = yt_get(token, url)
        for item in data.get("items", []):
            lc = item["status"]["lifeCycleStatus"]
            if lc in ["live", "testing", "liveStarting", "testStarting"]:
                return item["id"]
    return None

def main():
    token = get_token()
    log("Token OK")

    # Verificar se tem broadcast ativo AGORA
    ativo_id = canal_ao_vivo(token)
    if ativo_id:
        log(f"✅ Broadcast ativo detectado: {ativo_id}")
    else:
        log("  Nenhum broadcast ativo no momento")

    # Listar TODOS com broadcastStatus=all
    all_bc = {}
    next_token = None
    while True:
        url = "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status&broadcastStatus=all&maxResults=50"
        if next_token:
            url += f"&pageToken={next_token}"
        data = yt_get(token, url)
        for item in data.get("items", []):
            bc_id = item["id"]
            lc    = item["status"]["lifeCycleStatus"]
            sched = item["snippet"].get("scheduledStartTime","")
            title = item["snippet"]["title"][:60]
            all_bc[bc_id] = {"lc": lc, "title": title, "scheduled": sched}
        next_token = data.get("nextPageToken")
        if not next_token:
            break

    log(f"\nTotal broadcasts: {len(all_bc)}")

    if len(all_bc) <= 1:
        log("Já está limpo (<=1 broadcast). Nada a fazer.")
        return

    # Definir o que MANTER:
    # 1. O broadcast ativo (se existe)
    # 2. O broadcast com scheduledStartTime mais recente (para o próximo start)
    manter_ids = set()
    if ativo_id and ativo_id in all_bc:
        manter_ids.add(ativo_id)
        log(f"  Manter ativo: {ativo_id}")

    # Manter o mais recente por scheduledStartTime
    nao_ativos = {k: v for k, v in all_bc.items() if k not in manter_ids}
    if nao_ativos:
        # Ordenar por scheduled desc, pegar o mais recente
        mais_recente = sorted(nao_ativos.items(),
                               key=lambda x: x[1]["scheduled"], reverse=True)[0]
        # Só manter se não tiver broadcast ativo
        if not manter_ids:
            manter_ids.add(mais_recente[0])
            log(f"  Manter mais recente: {mais_recente[0]} [{mais_recente[1]['lc']}]")

    log(f"\nManter: {manter_ids}")
    log(f"Deletar: {len(all_bc) - len(manter_ids)} broadcasts\n")

    deletados = 0
    erros = 0
    for bc_id, info in all_bc.items():
        if bc_id in manter_ids:
            log(f"  ✅ MANTER: {bc_id} [{info['lc']}] {info['title'][:40]}")
            continue
        lc = info["lc"]
        log(f"  🗑  Del {bc_id} [{lc}] {info['title'][:35]}")

        if lc in ["ready","created","testStarting","testing"]:
            try:
                req = urllib.request.Request(
                    f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bc_id}&part=id",
                    data=b"{}", method="POST"
                )
                req.add_header("Authorization", f"Bearer {token}")
                req.add_header("Content-Type", "application/json")
                urllib.request.urlopen(req, timeout=10)
                time.sleep(0.8)
            except: pass

        req = urllib.request.Request(
            f"https://www.googleapis.com/youtube/v3/liveBroadcasts?id={bc_id}",
            method="DELETE"
        )
        req.add_header("Authorization", f"Bearer {token}")
        try:
            urllib.request.urlopen(req, timeout=10)
            deletados += 1
        except Exception as e:
            log(f"    Err: {e}")
            erros += 1
        time.sleep(0.3)

    log(f"\n✅ Concluído: {deletados} deletados | {erros} erros | {len(manter_ids)} mantidos")

if __name__ == "__main__":
    main()
