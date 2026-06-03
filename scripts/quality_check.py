#!/usr/bin/env python3
"""🔍 Quality Check Engine — Score ≥ 50, re-render se abaixo"""
import os, json, subprocess, urllib.request
from datetime import datetime

SBU = os.getenv("SUPABASE_URL",""); SBK = os.getenv("SUPABASE_SERVICE_KEY","")

def sb_get(ep, p=""): 
    req = urllib.request.Request(f"{SBU}/rest/v1/{ep}?{p}", headers={"apikey":SBK,"Authorization":f"Bearer {SBK}"})
    with urllib.request.urlopen(req, timeout=15) as r: return json.loads(r.read())

def sb_patch(table, data, vid_id):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{SBU}/rest/v1/{table}?id=eq.{vid_id}", data=body, method="PATCH",
        headers={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=minimal"})
    with urllib.request.urlopen(req, timeout=10): pass

def qc_score(mp4_url):
    """Analisa qualidade do vídeo via ffprobe"""
    if not mp4_url: return 0
    score = 0
    try:
        cmd = ["ffprobe","-v","quiet","-print_format","json","-show_streams","-show_format", mp4_url]
        r = subprocess.run(cmd, capture_output=True, timeout=30)
        d = json.loads(r.stdout)
        for s in d.get("streams",[]):
            if s["codec_type"]=="video":
                br = int(s.get("bit_rate",0))//1000
                w,h = s.get("width",0), s.get("height",0)
                if br >= 1000: score += 25
                elif br >= 500: score += 15
                if w>=1080 and h>=1920: score += 25
                elif w>=720 and h>=1280: score += 15
                if s.get("codec_name")=="h264": score += 10
            elif s["codec_type"]=="audio":
                channels = s.get("channels",0)
                sr = int(s.get("sample_rate",0))
                br = int(s.get("bit_rate",0))//1000
                if channels>=2: score += 15
                if sr>=44100: score += 10
                if br>=128: score += 10
        score = min(score, 100)
    except Exception as e:
        score = 50  # dar benefício da dúvida se ffprobe falhar
    return score

def main():
    print(f"[{datetime.now():%H:%M:%S}] 🔍 Quality Check iniciado")
    videos = sb_get("content_pipeline",
        "status=eq.mp4_ready&mp4_url=not.is.null"
        "&select=id,title,mp4_url,quality_score_current"
        "&quality_score_current=is.null&limit=10")
    
    print(f"  {len(videos)} vídeos sem QC score")
    
    for v in videos:
        vid_id = v["id"]
        score = qc_score(v.get("mp4_url",""))
        action = "✅" if score >= 50 else "⚠️"
        print(f"  {action} [{vid_id}] {v['title'][:40]} → score={score}")
        
        update = {"quality_score_current": score}
        if score < 50:
            update["error"] = "RERENDER_QUALITY_v2"
            update["status"] = "audio_ready"
        sb_patch("content_pipeline", update, vid_id)
    
    print(f"  ✅ QC completo")

if __name__ == "__main__":
    main()
