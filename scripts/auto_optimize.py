#!/usr/bin/env python3
"""🚀 Auto-Optimizer — Títulos A/B + Hashtags + YouTube updates"""
import os, json, urllib.request, urllib.parse
from datetime import datetime

SBU = os.getenv("SUPABASE_URL",""); SBK = os.getenv("SUPABASE_SERVICE_KEY","")
GROQ = os.getenv("GROQ_API_KEY","")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)

def groq_chat(messages, max_tokens=500):
    if not GROQ: return ""
    body = json.dumps({"model":"llama-3.3-70b-versatile","messages":messages,"max_tokens":max_tokens}).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",data=body)
    req.add_header("Authorization",f"Bearer {GROQ}"); req.add_header("Content-Type","application/json")
    with urllib.request.urlopen(req,timeout=20) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()

def sb_get(ep, p=""):
    req = urllib.request.Request(f"{SBU}/rest/v1/{ep}?{p}",headers={"apikey":SBK,"Authorization":f"Bearer {SBK}"})
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read())

def sb_patch(table, data, vid_id):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{SBU}/rest/v1/{table}?id=eq.{vid_id}",data=body,method="PATCH",
        headers={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=minimal"})
    with urllib.request.urlopen(req,timeout=10): pass

def get_token():
    rt = os.getenv("YT_REFRESH_TOKEN",""); ci = os.getenv("YT_CLIENT_ID",""); cs = os.getenv("YT_CLIENT_SECRET","")
    if not all([rt,ci,cs]): return ""
    body = urllib.parse.urlencode({"client_id":ci,"client_secret":cs,"refresh_token":rt,"grant_type":"refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token",data=body)
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read()).get("access_token","")

def optimize_title(title, topic):
    """Gera 3 variações de título via Groq"""
    msgs = [{"role":"user","content":f"""Crie 3 títulos YouTube VIRAIS para este vídeo de psicologia:
Tema: {topic}
Título atual: {title}

REGRAS ESTRITAS:
- Máx 70 chars (YouTube trunca)
- Hook emocional nos primeiros 5 palavras
- Uma revelação inesperada
- Sem clickbait vazio
- Baseado em neurociência real
- Formato: só os 3 títulos numerados, sem explicação

Exemplo de bom título:
"O Narcisista Mais Perigoso Não Grita. Ele Sorri | Neurociência"
"""}]
    resp = groq_chat(msgs, 200)
    titles = [l.strip().lstrip("123.-) ") for l in resp.split('\n') if len(l.strip()) > 20]
    return titles[:3]

def main():
    log("🚀 Auto-Optimizer iniciado")
    
    # 1. Otimizar títulos de vídeos prontos mas não publicados
    videos = sb_get("content_pipeline",
        "status=eq.mp4_ready&youtube_title_en=is.null"
        "&select=id,title,topic,youtube_title,series_slug&limit=5")
    
    log(f"  {len(videos)} vídeos para otimizar títulos")
    for v in videos:
        orig = v.get("youtube_title") or v.get("title","")
        topic = v.get("topic","") or v.get("series_slug","psicologia")
        
        # Gerar título em EN para canal internacional
        if GROQ:
            msgs_en = [{"role":"user","content":f"Translate to English (viral YouTube title, max 70 chars): {orig}"}]
            title_en = groq_chat(msgs_en, 100)
            msgs_es = [{"role":"user","content":f"Traduce al español (título YouTube viral, máx 70 chars): {orig}"}]
            title_es = groq_chat(msgs_es, 100)
            sb_patch("content_pipeline",{"youtube_title_en":title_en[:100],"youtube_title_es":title_es[:100]},v["id"])
            log(f"  ✅ [{v['id']}] EN+ES gerados")
    
    # 2. Gerar pinned_comment para vídeos sem
    videos_pc = sb_get("content_pipeline",
        "status=eq.mp4_ready&pinned_comment=is.null"
        "&select=id,title,topic,series_slug&limit=5")
    
    for v in videos_pc:
        if not GROQ: break
        msgs_pc = [{"role":"user","content":f"""Escreva um comentário pinado para o YouTube.
Deve:
- Agradecer o espectador
- Pedir para comentar a experiência deles
- Mencionar o próximo vídeo da série
- 2-3 linhas, empático e humano
Tema: {v.get('title','')}
Série: {v.get('series_slug','psicologia')}
"""}]
        pc = groq_chat(msgs_pc, 150)
        if pc: sb_patch("content_pipeline",{"pinned_comment":pc[:500]},v["id"])
    
    log(f"  ✅ Otimização concluída")

if __name__ == "__main__":
    main()
