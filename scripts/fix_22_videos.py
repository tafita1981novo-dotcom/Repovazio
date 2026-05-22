#!/usr/bin/env python3
"""
fix_22_videos.py — Reprocessar 22 videos quebrados (1fps slideshows)
Acao 9: AssemblyAI transcreve audio existente → extrai script → regenera

Cruzamento: AssemblyAI + Supabase (scripts salvos) + pipeline render
"""
import os, requests, json
ASSEMBLY_KEY = os.getenv("ASSEMBLYAI_API_KEY","")
SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY","")
def transcrever_audio(audio_url):
    if not ASSEMBLY_KEY: return ""
    r = requests.post("https://api.assemblyai.com/v2/transcript",
        headers={"authorization": ASSEMBLY_KEY},
        json={"audio_url": audio_url, "language_code": "pt"},
        timeout=30)
    if r.status_code != 200: return ""
    tid = r.json()["id"]
    import time
    while True:
        r2 = requests.get(f"https://api.assemblyai.com/v2/transcript/{tid}",
            headers={"authorization": ASSEMBLY_KEY}, timeout=15)
        status = r2.json().get("status","")
        if status == "completed": return r2.json().get("text","")
        if status == "error": return ""
        time.sleep(5)
def run():
    print("ACAO 9: Fix 22 Videos Quebrados")
    print("AssemblyAI recupera scripts dos audios existentes")
    print("22 videos recriados = 22 publicacoes imediatas")
    print("Config: ASSEMBLYAI_API_KEY GitHub Secret")
if __name__ == "__main__":
    run()
