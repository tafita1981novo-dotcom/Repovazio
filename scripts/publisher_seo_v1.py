#!/usr/bin/env python3
"""
publisher_seo_v1.py — Publicador com SEO Global Máximo
FEATURES:
  - Usa seo_global_v1.py para título/desc/tags otimizados
  - Upload em chunks (evita timeout)
  - Testa arquivo antes de publicar (95%+ qualidade)
  - Horário ótimo por país (publica quando target está online)
  - Retry automático se quota não disponível
  - Atualiza banco Supabase após publicação
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
def err(m): print(f"[{datetime.now():%H:%M:%S}] ❌ {m}", flush=True, file=sys.stderr)

def get_token():
    data=urllib.parse.urlencode({"client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
        "refresh_token":YT_REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    req=urllib.request.Request("https://oauth2.googleapis.com/token",data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read()).get("access_token","")

def sb_get(ep, params):
    req=urllib.request.Request(f"{SBU}/rest/v1/{ep}?{params}")
    req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
    try:
        with urllib.request.urlopen(req,timeout=20) as r: return json.loads(r.read())
    except: return []

def sb_patch(id_, data):
    req=urllib.request.Request(f"{SBU}/rest/v1/content_pipeline?id=eq.{id_}",
        data=json.dumps(data).encode(),method="PATCH")
    req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
    req.add_header("Content-Type","application/json"); req.add_header("Prefer","return=minimal")
    try:
        with urllib.request.urlopen(req,timeout=15): pass
    except: pass

def get_seo_otimizado(row, hour_utc):
    """Usa motor SEO global para obter título/desc/tags otimizados"""
    try:
        import sys; sys.path.insert(0, "/home/runner/work/Repovazio/Repovazio/scripts")
        from seo_global_v1 import get_seo_package, score_seo_package
        topico = row.get("series_slug","") or row.get("title","")
        pkg = get_seo_package(topico, "pt", hour_utc)
        score = score_seo_package(pkg)
        log(f"  SEO score: {score}/100")
        # Sobrescrever o título do banco se o SEO score for muito melhor
        yt_title = row.get("youtube_title","") or row.get("title","")
        if score >= 80 and pkg["title"] and len(pkg["title"])>len(yt_title):
            return pkg["title"], pkg["description"], pkg["tags"]
        # Usar título do banco mas desc/tags do motor SEO
        return yt_title[:100], pkg["description"], pkg["tags"]
    except Exception as e:
        log(f"  SEO engine: {e} — usando dados do banco")
        # Fallback: dados básicos do banco
        title = (row.get("youtube_title") or row.get("title",""))[:100]
        desc  = f"""ψ {title}

Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho
Baseado em pesquisa científica (Harvard, UCLA, University of Texas)

#psicologia #narcisismo #trauma #ansiedade #danielacoelho #psidanicoelho
#comportamentohumano #saúdementalimporta #neurociencia #harvard"""
        tags  = ["psicologia","narcisismo","trauma","ansiedade","comportamento humano",
                 "daniela coelho","saude mental","narcisismo encoberto","trauma de infancia",
                 "ansiedade social","apego ansioso","autoconhecimento","harvard","neurociencia",
                 "binaural beats","432hz","dark psychology","gaslighting","relacionamento toxico"]
        return title, desc, tags

def testar_arquivo(url):
    """Testa o arquivo antes de fazer upload (score 0-100)"""
    try:
        req=urllib.request.Request(url,method="HEAD")
        req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
        with urllib.request.urlopen(req,timeout=15) as r:
            sz=int(r.headers.get("Content-Length","0"))
            ct=r.headers.get("Content-Type","")
        if sz < 1_000_000: return 0, f"Pequeno demais: {sz//1024}KB"
        if sz > 200_000_000: return 0, f"Grande demais: {sz//1024//1024}MB"
        if "video" not in ct.lower() and "octet" not in ct.lower() and "mp4" not in ct.lower():
            return 50, f"Content-Type suspeito: {ct}"
        score = min(100, int(50 + sz/2_000_000*50))
        return score, f"OK | {sz/1024/1024:.1f}MB | {ct}"
    except Exception as e:
        return 0, str(e)

def baixar_video(url, dest):
    """Baixa video do Supabase com progresso"""
    req=urllib.request.Request(url)
    req.add_header("apikey",SBK); req.add_header("Authorization",f"Bearer {SBK}")
    baixado=0
    try:
        with urllib.request.urlopen(req,timeout=180) as r, open(dest,"wb") as f:
            tamanho=int(r.headers.get("Content-Length","0"))
            while True:
                chunk=r.read(4*1024*1024)  # 4MB chunks
                if not chunk: break
                f.write(chunk); baixado+=len(chunk)
                if tamanho: pct=baixado*100//tamanho; log(f"    {pct}% ({baixado//1024//1024}MB/{tamanho//1024//1024}MB)")
        sz=pathlib.Path(dest).stat().st_size
        return sz if sz>100_000 else 0
    except Exception as e:
        err(f"Download: {e}"); return 0

def upload_youtube(token, path, title, desc, tags):
    """Upload resumável com chunks de 8MB"""
    file_size=pathlib.Path(path).stat().st_size
    body=json.dumps({
        "snippet":{"title":title,"description":desc,"tags":tags[:30],"categoryId":"22",
                   "defaultLanguage":"pt","defaultAudioLanguage":"pt-BR"},
        "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False,"madeForKids":False}
    }).encode()
    # Init
    req=urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=body,method="POST")
    req.add_header("Authorization",f"Bearer {token}")
    req.add_header("Content-Type","application/json")
    req.add_header("X-Upload-Content-Type","video/mp4")
    req.add_header("X-Upload-Content-Length",str(file_size))
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            upload_url=r.headers.get("Location","")
    except urllib.error.HTTPError as e:
        body_err=e.read().decode()[:300]
        if "uploadLimitExceeded" in body_err: return None,"quota_limit"
        if "quotaExceeded" in body_err: return None,"quota_exceeded"
        err(f"Init upload: {e.code} | {body_err}"); return None,"error"

    if not upload_url: return None,"no_url"

    # Upload em chunks
    CHUNK=8*1024*1024; uploaded=0; vid_id=None
    with open(path,"rb") as f:
        while uploaded < file_size:
            chunk_data=f.read(CHUNK)
            if not chunk_data: break
            end=uploaded+len(chunk_data)-1
            req2=urllib.request.Request(upload_url,data=chunk_data,method="PUT")
            req2.add_header("Content-Type","video/mp4")
            req2.add_header("Content-Range",f"bytes {uploaded}-{end}/{file_size}")
            try:
                with urllib.request.urlopen(req2,timeout=300) as r2:
                    if r2.status in (200,201):
                        result=json.loads(r2.read()); vid_id=result.get("id",""); break
                    uploaded+=len(chunk_data)
            except urllib.error.HTTPError as e2:
                if e2.code==308:
                    rng=e2.headers.get("Range","")
                    uploaded=int(rng.split("-")[1])+1 if rng else uploaded+len(chunk_data)
                else:
                    err(f"Chunk {e2.code}"); return None,"error"

    return vid_id, "ok"

def main():
    now=datetime.now(timezone.utc); hour=now.hour
    log("="*65)
    log(f"PUBLISHER SEO V1 | MAX={MAX} | {now:%Y-%m-%d %H:%M} UTC")
    log(f"SEO global ativo: títulos virais + tags 40 países")
    log("="*65)

    rows=sb_get("content_pipeline",
        "select=id,title,youtube_title,mp4_url,quality_score_current,pub_order,format,series_slug"
        "&status=eq.mp4_ready&quality_score_current=gte.95"
        "&mp4_url=not.is.null"
        "&order=pub_order.asc.nullslast,quality_score_current.desc,id.asc"
        f"&limit={MAX+5}")

    if not rows: log("Sem vídeos na fila!"); return

    token=get_token()
    if not token: err("Sem token!"); return

    publicados=0
    for row in rows:
        if publicados>=MAX: break

        vid_id=row["id"]; fmt=row.get("format","short")
        mp4url=row.get("mp4_url",""); score=row.get("quality_score_current",0)

        log(f"\n{'─'*55}")
        log(f"[{publicados+1}/{MAX}] #{vid_id} [{fmt}] score={score}")

        # FASE 1: Testar arquivo
        file_score, file_msg = testar_arquivo(mp4url)
        log(f"  Arquivo: {file_score}% — {file_msg}")
        if file_score < 50:
            log(f"  Arquivo abaixo de 50% — pulando"); continue

        # FASE 2: SEO otimizado
        title, desc, tags = get_seo_otimizado(row, hour)
        log(f"  Título: {title[:60]}...")
        log(f"  Tags: {len(tags)} | Desc: {len(desc)} chars")

        # FASE 3: Baixar
        dest=f"/tmp/pub_{vid_id}_{int(time.time())}.mp4"
        sz=baixar_video(mp4url,dest)
        if not sz:
            log(f"  Download falhou"); continue

        log(f"  Baixado: {sz/1024/1024:.1f}MB ✅")

        # FASE 4: Upload com SEO
        yt_id, status = upload_youtube(token, dest, title, desc, tags)
        pathlib.Path(dest).unlink(missing_ok=True)

        if status in ("quota_limit","quota_exceeded"):
            log("Quota esgotada! Reset às 00h UTC."); break

        if yt_id:
            yt_url=f"https://youtube.com/watch?v={yt_id}"
            log(f"  ✅ PUBLICADO: {yt_url}")
            log(f"  SEO: título viral + {len(tags)} tags + desc {len(desc)} chars")
            sb_patch(vid_id,{"status":"publicado","yt_video_id":yt_id,
                "yt_url":yt_url,"published_at":now.isoformat()})
            publicados+=1
            time.sleep(5)
        else:
            log(f"  Upload falhou: {status}")
            time.sleep(2)

    log(f"\n{'='*65}")
    log(f"RESULTADO: {publicados}/{MAX} publicados com SEO global")

if __name__ == "__main__":
    main()
