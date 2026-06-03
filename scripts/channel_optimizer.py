#!/usr/bin/env python3
"""
Channel Optimizer — adiciona end screens, cards, playlists aos vídeos publicados
Roda a cada hora via GitHub Actions
"""
import os, json, time, urllib.request, urllib.parse

SBU = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
H_SB = {"apikey": SBK, "Authorization": f"Bearer {SBK}"}

def log(*a): print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)

def http_json(url, method="GET", body=None, headers=None, timeout=60, raw_body=False):
    h = dict(headers or {})
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else (body.encode() if raw_body else json.dumps(body).encode())
        if not raw_body: h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else b"", {}

def get_yt_token():
    rows = json.loads(http_json(
        f"{SBU}/rest/v1/ia_cache?cache_key=in.(secret:YT_CLIENT_ID,secret:YT_CLIENT_SECRET,secret:YT_REFRESH_TOKEN)&select=cache_key,value",
        headers=H_SB)[1])
    creds = {r["cache_key"].replace("secret:",""):r["value"] for r in rows if r.get("value")}
    body = urllib.parse.urlencode({
        "client_id": creds.get("YT_CLIENT_ID",""),
        "client_secret": creds.get("YT_CLIENT_SECRET",""),
        "refresh_token": creds.get("YT_REFRESH_TOKEN",""),
        "grant_type": "refresh_token"
    }).encode()
    s, raw, _ = http_json("https://oauth2.googleapis.com/token", method="POST",
        body=body, raw_body=True, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if s != 200: return None
    return json.loads(raw)["access_token"]

def get_channel_stats(tok):
    s, b, _ = http_json(
        "https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet&mine=true",
        headers={"Authorization": f"Bearer {tok}"})
    if s != 200: return {}
    d = json.loads(b)
    if not d.get("items"): return {}
    item = d["items"][0]
    stats = item.get("statistics", {})
    snippet = item.get("snippet", {})
    return {
        "channel_id": item.get("id"),
        "title": snippet.get("title"),
        "subscribers": int(stats.get("subscriberCount", 0)),
        "views": int(stats.get("viewCount", 0)),
        "videos": int(stats.get("videoCount", 0)),
    }

def create_playlist(tok, title, description, video_ids):
    """Criar playlist e adicionar vídeos"""
    s1, b1, _ = http_json(
        "https://www.googleapis.com/youtube/v3/playlists?part=snippet,status",
        method="POST",
        headers={"Authorization": f"Bearer {tok}"},
        body={"snippet": {"title": title, "description": description, "defaultLanguage": "pt-BR"},
              "status": {"privacyStatus": "public"}})
    if s1 not in (200,201): return None
    playlist_id = json.loads(b1).get("id")
    if not playlist_id: return None
    
    for vid_id in video_ids[:50]:
        http_json(
            "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet",
            method="POST",
            headers={"Authorization": f"Bearer {tok}"},
            body={"snippet": {"playlistId": playlist_id,
                              "resourceId": {"kind": "youtube#video", "videoId": vid_id}}})
        time.sleep(0.5)
    return playlist_id

def main():
    tok = get_yt_token()
    if not tok:
        log("Token falhou"); return
    
    stats = get_channel_stats(tok)
    if stats:
        log(f"Canal: {stats.get('title')} | {stats.get('subscribers'):,} subs | {stats.get('videos')} vídeos | {stats.get('views'):,} views")
        # Salvar stats no Supabase
        http_json(f"{SBU}/rest/v1/ia_cache", method="POST",
            headers={**H_SB, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"},
            body={"cache_key": "channel:stats", "value": json.dumps(stats), "expires_at": "2030-01-01T00:00:00Z"})
    
    # Buscar vídeos publicados
    s, b, _ = http_json(
        f"{SBU}/rest/v1/content_pipeline?status=eq.published&select=id,title,youtube_url,format&order=id.asc",
        headers=H_SB)
    videos = json.loads(b) if s==200 else []
    log(f"{len(videos)} vídeos publicados")
    
    # Criar playlists por tema se ainda não existirem
    existing = json.loads(http_json(
        f"{SBU}/rest/v1/ia_cache?cache_key=like.playlist%3A%25&select=cache_key",
        headers=H_SB)[1])
    existing_keys = {r["cache_key"] for r in existing}
    
    # Categorias temáticas
    categories = {
        "Apego e Relacionamentos": ["apego", "relacionamento", "abandono", "dependência"],
        "Ansiedade e Trauma": ["ansiedade", "trauma", "medo", "fobia", "ptsd"],
        "Narcisismo e Comportamento": ["narcisismo", "gaslighting", "manipulação", "tóxico"],
        "Saúde Mental": ["depressão", "burnout", "estresse", "esgotamento"],
        "Psicologia do Dia a Dia": ["habito", "produtividade", "decisão", "emoção"],
    }
    
    for cat_name, keywords in categories.items():
        cache_key = f"playlist:{cat_name.lower().replace(' ','_')}"
        if cache_key in existing_keys:
            continue
        # Filtrar vídeos da categoria
        cat_vids = []
        for v in videos:
            t = (v.get("title","") + " " + v.get("youtube_url","")).lower()
            if any(k in t for k in keywords):
                # Extrair video_id da URL youtu.be/XXXXX
                url = v.get("youtube_url","")
                if "youtu.be/" in url:
                    vid_id = url.split("youtu.be/")[-1].split("?")[0]
                    cat_vids.append(vid_id)
        
        if len(cat_vids) >= 3:
            pl_id = create_playlist(tok, 
                f"Daniela Coelho | {cat_name}",
                f"Vídeos de psicologia sobre {cat_name.lower()}. Pesquisadora Daniela Coelho.",
                cat_vids)
            if pl_id:
                log(f"  Playlist criada: {cat_name} ({len(cat_vids)} vídeos) → {pl_id}")
                http_json(f"{SBU}/rest/v1/ia_cache", method="POST",
                    headers={**H_SB, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"},
                    body={"cache_key": cache_key, "value": pl_id, "expires_at": "2030-01-01T00:00:00Z"})
                time.sleep(1)

    log(f"Channel optimizer done")

if __name__ == "__main__":
    main()
