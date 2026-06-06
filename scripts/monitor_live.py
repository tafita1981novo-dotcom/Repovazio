#!/usr/bin/env python3
"""monitor_live.py — Coleta métricas da live a cada hora e salva no Supabase"""
import os, json, urllib.request, urllib.parse, requests
from datetime import datetime, timezone

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
SUPABASE_URL     = "https://tpjvalzwkqwttvmszvie.supabase.co"
SUPABASE_KEY     = os.environ.get("SUPABASE_KEY","")

def get_token():
    data=urllib.parse.urlencode({"client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
        "refresh_token":YT_REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    req=urllib.request.Request("https://oauth2.googleapis.com/token",data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read())["access_token"]

def yt_get(token,url):
    req=urllib.request.Request(url); req.add_header("Authorization",f"Bearer {token}")
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read())

def save_metric(data):
    if not SUPABASE_KEY: print("Sem SUPABASE_KEY, apenas printando"); return
    resp=requests.post(f"{SUPABASE_URL}/rest/v1/live_metrics",
        headers={"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"},
        json=data, timeout=15)
    return resp.status_code

def main():
    now = datetime.now(timezone.utc)
    print(f"[{now:%Y-%m-%d %H:%M}] Coletando métricas...")
    token = get_token()
    
    # Canal
    ch = yt_get(token,"https://www.googleapis.com/youtube/v3/channels?part=id,statistics,status&mine=true")
    ch_item = ch.get("items",[{}])[0]
    stats = ch_item.get("statistics",{})
    subs = int(stats.get("subscriberCount",0))
    views = int(stats.get("viewCount",0))
    videos = int(stats.get("videoCount",0))
    print(f"  Canal: {subs} subs | {views} views | {videos} vídeos")
    
    # Live broadcasts
    bc = yt_get(token,"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,statistics,status&broadcastType=all&mine=true&maxResults=5")
    live_viewers = 0
    live_id = ""
    for item in bc.get("items",[]):
        if item.get("status",{}).get("lifeCycleStatus") == "live":
            live_viewers = int(item.get("statistics",{}).get("concurrentViewers",0))
            live_id = item["id"]
            print(f"  Live {live_id}: {live_viewers} viewers concurrent")
    
    # Stream health
    st = yt_get(token,"https://www.googleapis.com/youtube/v3/liveStreams?part=id,status,cdn&mine=true&maxResults=3")
    stream_status = "unknown"
    for item in st.get("items",[]):
        if item.get("cdn",{}).get("ingestionInfo",{}).get("streamName","?").startswith("ewme"):
            stream_status = item.get("status",{}).get("streamStatus","?")
    print(f"  Stream: {stream_status}")
    
    # Calcular progresso para YPP
    ypp_subs_pct = min(100, (subs/1000)*100)
    ypp_note = "Fan Funding disponível!" if subs >= 500 else f"{500-subs} subs para fan funding"
    
    metric = {
        "timestamp": now.isoformat(),
        "subs": subs,
        "total_views": views,
        "total_videos": videos,
        "live_id": live_id,
        "concurrent_viewers": live_viewers,
        "stream_status": stream_status,
        "ypp_subs_pct": round(ypp_subs_pct,1),
        "note": ypp_note
    }
    
    code = save_metric(metric)
    
    print(f"""
  ━━━ PROGRESSO YPP ━━━━━━━━━━━━━━━━━━━━━
  Subs:  {subs}/1000  ({ypp_subs_pct:.0f}%) [{ypp_note}]
  Views: {views} (total acumulado)
  Stream: {stream_status}
  Saved: {code}
    """)

if __name__=="__main__": main()
