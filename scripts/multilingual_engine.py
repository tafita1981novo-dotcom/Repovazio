#!/usr/bin/env python3
"""
🌍 Multi-Language Engine — EN, ES, FR, DE, JA, KO, ZH
Monetiza nos países com RPM mais alto do mundo
RPM por país/idioma:
- EN (EUA/CA/AU/UK): $8-25 🔥🔥🔥
- DE (Alemanha): $12-30 🔥🔥🔥🔥
- FR (França): $8-20 🔥🔥🔥
- JA (Japão): $6-15 🔥🔥
- KO (Coreia): $5-12 🔥
- ES (Espanha/México): $3-8 🔥
- PT-BR: $3-6
"""
import os, json, subprocess, pathlib, urllib.request, urllib.parse
from datetime import datetime

SBU = os.getenv("SUPABASE_URL","")
SBK = os.getenv("SUPABASE_SERVICE_KEY","")
GROQ = os.getenv("GROQ_API_KEY","")
TARGET_LANG = os.getenv("TARGET_LANG","en-US")

LANG_CONFIGS = {
    "en-US": {
        "voice": "en-US-AvaMultilingualNeural",
        "rate": "+8%",
        "rpm_estimate": 15,
        "channel_note": "en_channel_queue (2470 vídeos esperando!)"
    },
    "es-ES": {
        "voice": "es-ES-ElviraNeural",
        "rate": "+10%",
        "rpm_estimate": 6,
        "channel_note": "Hispânico: 500M+ falantes"
    },
    "fr-FR": {
        "voice": "fr-FR-DeniseNeural",
        "rate": "+8%",
        "rpm_estimate": 12,
        "channel_note": "Francófono: alto RPM"
    },
    "de-DE": {
        "voice": "de-DE-SeraphinaMultilingualNeural",
        "rate": "+10%",
        "rpm_estimate": 20,
        "channel_note": "Alemão: RPM mais alto da Europa"
    },
    "ja-JP": {
        "voice": "ja-JP-NanamiNeural",
        "rate": "+5%",
        "rpm_estimate": 10,
        "channel_note": "Japonês: audiência premium"
    },
    "ko-KR": {
        "voice": "ko-KR-SunHiNeural",
        "rate": "+8%",
        "rpm_estimate": 8,
        "channel_note": "Coreano: crescimento 2024-2026"
    },
    "zh-CN": {
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "+5%",
        "rpm_estimate": 5,
        "channel_note": "Mandarim: maior audiência do mundo"
    },
}

def groq_translate(text, target_lang, title):
    if not GROQ: return text
    lang_name = {"en-US":"English","es-ES":"Spanish","fr-FR":"French","de-DE":"German",
                 "ja-JP":"Japanese","ko-KR":"Korean","zh-CN":"Mandarin Chinese"}.get(target_lang,"English")
    body = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role":"user","content":f"""Translate this psychology script to {lang_name}.
Keep it emotional, scientific, and viral. Preserve all citations (Harvard, Gottman, etc.).
Don't translate researcher names or brand names.

Title: {title}
Script: {text[:2000]}

Return ONLY the translated text, nothing else."""}],
        "max_tokens": 2000
    }).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body)
    req.add_header("Authorization", f"Bearer {GROQ}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()

def sb_get(ep, p=""):
    req = urllib.request.Request(f"{SBU}/rest/v1/{ep}?{p}",
        headers={"apikey":SBK,"Authorization":f"Bearer {SBK}"})
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read())

def sb_insert(table, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{SBU}/rest/v1/{table}", data=body, method="POST",
        headers={"apikey":SBK,"Authorization":f"Bearer {SBK}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read())

def main():
    print(f"🌍 Multi-Language Engine — {TARGET_LANG}")
    config = LANG_CONFIGS.get(TARGET_LANG, LANG_CONFIGS["en-US"])
    print(f"   Voice: {config['voice']}")
    print(f"   Estimated RPM: ${config['rpm_estimate']}")
    print(f"   Note: {config['channel_note']}")
    
    # Para EN: usar en_channel_queue (já tem 2470 vídeos!)
    if TARGET_LANG == "en-US":
        queue = sb_get("en_channel_queue",
            "status=eq.ready&select=id,title_en,script_en,series_slug,pub_order&order=pub_order.asc&limit=5")
        
        if queue:
            print(f"\n✅ {len(queue)} vídeos na en_channel_queue!")
            for v in queue[:3]:
                print(f"   - {v.get('title_en','?')[:50]}")
            return
    
    # Para outros idiomas: pegar vídeos PT-BR com mp4_ready e traduzir
    videos = sb_get("content_pipeline",
        "status=eq.mp4_ready&format=eq.short"
        "&select=id,title,script,youtube_title,youtube_description,series_slug"
        f"&youtube_title_{TARGET_LANG[:2].lower()}=is.null&limit=5")
    
    print(f"\n{len(videos)} vídeos para traduzir para {TARGET_LANG}")
    
    for v in videos[:3]:
        print(f"\nTraduzindo [{v['id']}]: {v['title'][:50]}")
        
        if not GROQ:
            print("  ⚠️  GROQ_API_KEY necessário para tradução")
            break
        
        script_pt = v.get("script","") or v.get("youtube_description","")
        title_pt  = v.get("youtube_title","") or v.get("title","")
        lang_code = TARGET_LANG[:2].lower()
        
        title_trans  = groq_translate(title_pt, TARGET_LANG, title_pt)[:100]
        script_trans = groq_translate(script_pt[:1500], TARGET_LANG, title_pt)
        
        print(f"  ✅ Título: {title_trans[:60]}")
        
        # Salvar no content_pipeline
        import urllib.request as ur
        body = json.dumps({f"youtube_title_{lang_code}": title_trans,
                           f"youtube_desc_{lang_code}": script_trans[:2000]}).encode()
        req = ur.Request(f"{SBU}/rest/v1/content_pipeline?id=eq.{v['id']}", data=body, method="PATCH",
            headers={"apikey":SBK,"Authorization":f"Bearer {SBK}",
                     "Content-Type":"application/json","Prefer":"return=minimal"})
        with ur.urlopen(req,timeout=10): pass
        print(f"  ✅ Tradução salva!")
    
    # Resumo monetização potencial
    total_videos = len(sb_get("content_pipeline","status=eq.mp4_ready&select=id"))
    rpm = config["rpm_estimate"]
    views_est = total_videos * 10000  # 10K views médias por vídeo
    revenue_est = views_est / 1000 * rpm
    print(f"\n💰 Potencial de receita ({TARGET_LANG}):")
    print(f"   {total_videos} vídeos × 10K views × RPM ${rpm}")
    print(f"   = ${revenue_est:,.0f} estimado")

if __name__ == "__main__":
    main()
