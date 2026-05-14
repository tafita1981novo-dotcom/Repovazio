#!/usr/bin/env python3
"""daily_report.py — Status report do pipeline"""
import os, requests, json

SBU = os.environ.get("SUPABASE_URL","")
SBK = os.environ.get("SUPABASE_KEY","")
if not SBU or not SBK:
    print("Variaveis de ambiente nao configuradas")
    exit(0)

hdrs = {"Authorization": f"Bearer {SBK}", "apikey": SBK}

r = requests.get(f"{SBU}/rest/v1/content_pipeline?select=status,seo_score&limit=2000", headers=hdrs, timeout=15)
data = r.json()

cnt = {}
for x in data:
    cnt[x["status"]] = cnt.get(x["status"], 0) + 1

print("=" * 50)
print("PIPELINE STATUS")
print("=" * 50)
for k, v in sorted(cnt.items(), key=lambda x: -x[1]):
    print(f"  {k:<30}: {v}")

print(f"\n  Total: {len(data)}")
print(f"  MP4 prontos: {cnt.get('pending_credentials', 0)}")
print(f"  Publicados: {sum(1 for x in data if x.get('youtube_video_id'))}")
print("=" * 50)
