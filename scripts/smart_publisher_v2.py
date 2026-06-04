#!/usr/bin/env python3
"""
smart_publisher_v2.py - Publicador inteligente YouTube
- Usa quota YouTube API (10.000 unidades/dia, reset 00h UTC)
- Cada upload = 1.600 unidades → máximo 6 uploads/dia
- Publica na ordem de pub_order
- Atualiza status no Supabase
- Thumbnails automáticas se possível
- Tags e SEO otimizados por idioma
"""
import os, sys, json, re, time, pathlib, urllib.request, urllib.parse
from datetime import datetime, timezone

SBU = os.environ.get("SUPABASE_URL","")
SBK = os.environ.get("SUPABASE_SERVICE_KEY","")
YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
MAX = int(os.environ.get("MAX_VIDEOS","6"))

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ❌ {m}", flush=True)

def get_token():
    data = urllib.parse.urlencode({
        "client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read()).get("access_token","")

def sb_get(ep, params):
    req = urllib.request.Request(f"{SBU}/rest/v1/{ep}?{params}")
    req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
    try:
        with urllib.request.urlopen(req,timeout=20) as r: return json.loads(r.read())
    except: return []

def sb_patch(id_, data):
    req = urllib.request.Request(f"{SBU}/rest/v1/content_pipeline?id=eq.{id_}",
        data=json.dumps(data).encode(), method="PATCH")
    req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
    req.add_header("Content-Type","application/json"); req.add_header("Prefer","return=minimal")
    try:
        with urllib.request.urlopen(req,timeout=15): pass
    except: pass

def gen_descricao(row):
    """Gera descrição SEO otimizada"""
    title = row.get("youtube_title") or row.get("title","")
    series = row.get("series_slug","psicologia")
    
    # Descrição estruturada para máximo SEO
    desc = f"""🔴 PESQUISA EM PSICOLOGIA | {title}

Daniela Coelho — Pesquisadora de Comportamento Humano

⚠️ Este conteúdo é baseado em pesquisa científica sobre comportamento humano e psicologia.

📌 SOBRE ESTE CANAL
Estudamos padrões de comportamento humano baseados em pesquisas de Harvard, UCLA, University of Texas e outras instituições.

🔔 ATIVE O SINO para não perder os próximos estudos!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 FONTES CIENTÍFICAS
• Dr. Craig Malkin (Harvard) — Narcisismo e Relacionamentos
• Bessel van der Kolk — Trauma e Comportamento
• Dr. Daniel Siegel (UCLA) — Neurociência Interpessoal
• Brené Brown (University of Texas) — Vulnerabilidade e Resiliência
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#psicologia #comportamentohumano #danielacoelho #psidanicoelho
#narcisismo #trauma #ansiedade #apego #autoconhecimento
#{series} #pesquisaempsicologia #saúdememtal
"""
    return desc[:4900]

def gen_tags(row):
    base = [
        "psicologia","comportamento humano","narcisismo","trauma",
        "ansiedade","apego ansioso","autoconhecimento","daniela coelho",
        "psidanicoelho","saude mental","pesquisa em psicologia",
        "harvard","neurociencia","relacionamentos","autoestima"
    ]
    extra = []
    title = (row.get("youtube_title") or row.get("title","")).lower()
    if "narcis" in title: extra += ["narcisismo encoberto","narcisista"]
    if "trauma" in title: extra += ["trauma de infancia","trauma psicologico"]
    if "ansied" in title: extra += ["ansiedade social","ataque de panico"]
    if "apego" in title:  extra += ["apego ansioso","teoria do apego","attachment"]
    if "depress" in title: extra += ["depressao silenciosa","sintomas depressao"]
    if "celul" in title:  extra += ["vicio em celular","tecnologia","redes sociais"]
    return (extra + base)[:30]

def baixar_mp4(url):
    """Baixa o vídeo do Supabase Storage"""
    tmp = pathlib.Path(f"/tmp/pub_{int(time.time())}.mp4")
    req = urllib.request.Request(url)
    req.add_header("apikey", SBK)
    req.add_header("Authorization", f"Bearer {SBK}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r, open(tmp,"wb") as f:
            while True:
                chunk = r.read(1024*1024)
                if not chunk: break
                f.write(chunk)
        sz = tmp.stat().st_size
        if sz > 500_000:
            log(f"  Baixado: {sz/1024/1024:.1f}MB → {tmp}")
            return str(tmp)
        else:
            log(f"  Arquivo muito pequeno ({sz}B), ignorando")
            tmp.unlink(missing_ok=True)
            return None
    except Exception as e:
        err(f"Erro ao baixar: {e}")
        return None

def upload_youtube(token, local_path, row):
    """Upload resumável para YouTube"""
    file_size = pathlib.Path(local_path).stat().st_size
    title = (row.get("youtube_title") or row.get("title",""))[:100]
    desc  = gen_descricao(row)
    tags  = gen_tags(row)

    body = json.dumps({
        "snippet": {
            "title": title, "description": desc,
            "tags": tags, "categoryId": "22",
            "defaultLanguage": "pt", "defaultAudioLanguage": "pt-BR"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids": False
        }
    }).encode()

    # 1. Iniciar upload resumável
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=body, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type","application/json")
    req.add_header("X-Upload-Content-Type","video/mp4")
    req.add_header("X-Upload-Content-Length", str(file_size))

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            upload_url = r.headers.get("Location","")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:300]
        if "uploadLimitExceeded" in err_body:
            err("Limite diário atingido! Reset às 00h UTC")
            return None, "quota_exceeded"
        if "quotaExceeded" in err_body:
            err("Quota API atingida! 10.000 unidades esgotadas")
            return None, "quota_exceeded"
        err(f"Init upload: {e.code} | {err_body}")
        return None, "error"

    if not upload_url: return None, "no_url"

    # 2. Enviar arquivo em chunks
    CHUNK = 8 * 1024 * 1024  # 8MB chunks
    uploaded = 0
    vid_id = None

    with open(local_path, "rb") as f:
        while uploaded < file_size:
            chunk_data = f.read(CHUNK)
            if not chunk_data: break
            chunk_end = uploaded + len(chunk_data) - 1

            req2 = urllib.request.Request(upload_url, data=chunk_data, method="PUT")
            req2.add_header("Content-Type","video/mp4")
            req2.add_header("Content-Range", f"bytes {uploaded}-{chunk_end}/{file_size}")
            req2.add_header("Content-Length", str(len(chunk_data)))

            try:
                with urllib.request.urlopen(req2, timeout=180) as r2:
                    if r2.status in (200, 201):
                        result = json.loads(r2.read())
                        vid_id = result.get("id","")
                        break
                    uploaded += len(chunk_data)
            except urllib.error.HTTPError as e2:
                if e2.code == 308:  # Resume Incomplete — continuar
                    range_hdr = e2.headers.get("Range","")
                    if range_hdr:
                        uploaded = int(range_hdr.split("-")[1]) + 1
                    else:
                        uploaded += len(chunk_data)
                else:
                    err(f"Chunk upload: {e2.code}")
                    return None, "error"

    return vid_id, "ok"

def main():
    log("="*65)
    log(f"SMART PUBLISHER V2 — {MAX} uploads | {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    log(f"Quota: 10.000 units/dia | Cada upload: 1.600 units → max 6/dia")
    log("="*65)

    # Buscar fila de publicação
    rows = sb_get("content_pipeline",
        "select=id,title,youtube_title,mp4_url,quality_score_current,pub_order,format,series_slug"
        "&status=eq.mp4_ready"
        "&quality_score_current=gte.95"
        "&mp4_url=not.is.null"
        "&order=pub_order.asc.nullslast,quality_score_current.desc,id.asc"
        f"&limit={MAX+5}")

    if not rows:
        log("Sem vídeos na fila! Aguardando renders...")
        return

    log(f"Fila: {len(rows)} vídeos | Publicando até {MAX}")

    token = get_token()
    if not token: err("Sem token!"); return

    publicados = 0
    for row in rows:
        if publicados >= MAX:
            log(f"Limite atingido ({MAX} uploads)")
            break

        vid_id = row["id"]
        title  = (row.get("youtube_title") or row.get("title",""))[:60]
        mp4url = row.get("mp4_url","")
        score  = row.get("quality_score_current",0)
        fmt    = row.get("format","short")

        log(f"\n[{publicados+1}/{MAX}] #{vid_id} score={score} | {title}")

        # Baixar vídeo
        local = baixar_mp4(mp4url)
        if not local:
            log(f"  Sem arquivo válido, pulando #{vid_id}")
            continue

        # Upload
        yt_id, status = upload_youtube(token, local, row)
        pathlib.Path(local).unlink(missing_ok=True)

        if status == "quota_exceeded":
            log("Quota esgotada! Parando.")
            break

        if yt_id:
            yt_url = f"https://youtube.com/watch?v={yt_id}"
            log(f"  ✅ PUBLICADO: {yt_url}")
            sb_patch(vid_id, {
                "status": "publicado",
                "yt_video_id": yt_id,
                "yt_url": yt_url,
                "published_at": datetime.now(timezone.utc).isoformat()
            })
            publicados += 1
            log(f"  💤 Aguardando 5s para evitar rate limit...")
            time.sleep(5)
        else:
            log(f"  Upload falhou: {status}")
            time.sleep(2)

    log(f"\n{'='*65}")
    log(f"RESULTADO: {publicados}/{MAX} vídeos publicados")
    if publicados == 0:
        log("⚠️  Zero uploads — verificar quota ou arquivos")
    else:
        log(f"✅ Canal atualizado com {publicados} vídeos novos!")

if __name__ == "__main__":
    main()
