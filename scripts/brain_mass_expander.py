#!/usr/bin/env python3
# brain_mass_expander.py
# Usa Groq + Nvidia + Gemini para descobrir 100 novas APIs por rodada
# Objetivo: 40.000 APIs. Roda todo hora via GitHub Action.

import os, json, requests, time, random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

GK = os.getenv("GROQ_API_KEY","")
NK = os.getenv("NVIDIA_API_KEY","")
GEM = os.getenv("GEMINI_API_KEY","")
SB  = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SK  = os.getenv("SUPABASE_SERVICE_KEY","")

def sbh():
    return {"apikey":SK,"Authorization":f"Bearer {SK}","Content-Type":"application/json"}

# 40 categorias para explorar — rotacao aleatoria
CATS_40K = [
    "Neuroscience Research","Cognitive Psychology","Clinical Psychology",
    "Educational Psychology","Positive Psychology","Sports Psychology",
    "Organizational Psychology","Forensic Psychology","Child Psychology",
    "Geriatric Psychology","Neuroimaging Tools","Brain Computer Interface",
    "Mental Health Apps","Therapy Platforms","Mindfulness Tools",
    "Meditation Apps","Sleep Science","Chronobiology",
    "Psychopharmacology Data","Psychiatric Research","Behavioral Economics",
    "Decision Making Research","Emotion Recognition AI","Facial Expression API",
    "Voice Emotion Analysis","Sentiment Analysis NLP","Text Classification Mental Health",
    "Crisis Intervention Tools","Suicide Prevention Data","Addiction Research",
    "Trauma Research PTSD","Eating Disorder Research","Anxiety Disorder Data",
    "Depression Research","ADHD Research Tools","Autism Spectrum Data",
    "Personality Assessment","Intelligence Testing","Neuropsychology Assessment",
    "Rehabilitation Psychology","Music Therapy","Art Therapy",
    "Drama Therapy","Animal Assisted Therapy","Virtual Reality Therapy",
    "Biofeedback Neurofeedback","Heart Rate Variability","Cortisol Stress Markers",
    "Sleep Tracking APIs","Meditation Biometrics"
]

def discover_apis_groq(categoria):
    if not GK: return []
    prompt = (f"List 5 real, publicly accessible APIs in the category: {categoria} "
              f"that are useful for psychology content creation. "
              f"For each: name, base endpoint URL, auth_type (none/apiKey/OAuth/Bearer). "
              f"JSON only, array: "
              f"[{{"name":"X","endpoint":"https://","auth_type":"apiKey"}}]")
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GK}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":prompt}],
                  "max_tokens":600,"response_format":{"type":"json_object"}},
            timeout=30)
        if r.status_code == 200:
            data = json.loads(r.json()["choices"][0]["message"]["content"])
            if isinstance(data, list): return data
            for v in data.values():
                if isinstance(v, list): return v
    except: pass
    return []

def discover_apis_gemini(categoria):
    if not GEM: return []
    prompt = (f"List 5 real APIs for: {categoria} psychology content. "
              f"JSON array: [{{"name":"X","endpoint":"https://","auth_type":"none"}}]")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEM}"
        r = requests.post(url,
            json={"contents":[{"parts":[{"text":prompt}]}],
                  "generationConfig":{"responseMimeType":"application/json"}},
            timeout=30)
        if r.status_code == 200:
            txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(txt)
            if isinstance(data, list): return data
            for v in data.values():
                if isinstance(v, list): return v
    except: pass
    return []

def save_apis(apis, categoria):
    if not SK: return 0
    ok = 0
    for a in apis[:5]:
        name = str(a.get("name","?"))[:100]
        endpoint = str(a.get("endpoint",""))[:500]
        auth = str(a.get("auth_type","apiKey"))[:50]
        if not endpoint.startswith("http"): continue
        r = requests.post(f"{SB}/rest/v1/api_brain",
            headers={**sbh(),"Prefer":"resolution=ignore-duplicates"},
            json={"name":name,"category":categoria,"subcategory":name[:50],
                  "endpoint":endpoint,"auth_type":auth,
                  "description":f"{categoria} API discovered by Quantum Brain",
                  "relevance":2,"use_case":categoria,"source":"groq-discovery",
                  "tags":[categoria.lower().replace(" ","-"),"auto-discovered"]},
            timeout=10)
        if r.status_code in (200,201,409): ok+=1
    return ok

def get_current_count():
    r = requests.get(f"{SB}/rest/v1/api_brain?select=count",
                    headers={**sbh(),"Prefer":"count=exact"},timeout=5)
    return int(r.headers.get("Content-Range","0/0").split("/")[-1])

def run():
    current = get_current_count()
    target  = 40000
    remaining = target - current
    print(f"BRAIN MASS EXPANDER — {datetime.now():%Y-%m-%d %H:%M}")
    print(f"Atual: {current:,} | Meta: {target:,} | Faltam: {remaining:,}")
    if remaining <= 0:
        print("META ATINGIDA!")
        return

    cats = random.sample(CATS_40K, min(10, len(CATS_40K)))
    print(f"Explorando {len(cats)} categorias em paralelo...")
    total_new = 0

    with ThreadPoolExecutor(max_workers=5) as ex:
        fgroq = {ex.submit(discover_apis_groq, c): c for c in cats[:5]}
        fgem  = {ex.submit(discover_apis_gemini, c): c for c in cats[5:]}
        for f in as_completed({**fgroq, **fgem}):
            cat = {**fgroq, **fgem}[f]
            apis = f.result()
            if apis:
                saved = save_apis(apis, cat)
                total_new += saved
                if saved: print(f"  +{saved} [{cat[:30]}]")
            time.sleep(0.5)

    new_total = get_current_count()
    print(f"Nova contagem: {new_total:,} (+{new_total - current} esta rodada)")
    print(f"Progresso: {new_total/target*100:.1f}% da meta 40K")

if __name__ == "__main__":
    run()
