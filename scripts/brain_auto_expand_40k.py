#!/usr/bin/env python3
# brain_auto_expand_40k.py
# Expande banco de APIs automaticamente para 40.000
# Estrategia: HuggingFace models (300K+) + RapidAPI + Government portals

import os, json, requests, time
from datetime import datetime

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY","")

def sbh():
    return {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json"}

def get_count():
    r = requests.get(f"{SB_URL}/rest/v1/api_brain?select=count","headers=sbh(),timeout=10)
    return int(r.headers.get("Content-Range","0/0").split("/")[-1]) if r.status_code==200 else 0

# Categorias HuggingFace para expandir
HF_PIPELINES = [
    "text-generation","text-to-speech","text-to-image","text-to-video",
    "automatic-speech-recognition","image-to-text","question-answering",
    "summarization","translation","text-classification","sentiment-analysis",
    "feature-extraction","token-classification","fill-mask","image-classification",
    "image-segmentation","object-detection","depth-estimation","image-to-image",
    "unconditional-image-generation","video-classification","audio-classification",
    "audio-to-audio","text-to-audio","document-question-answering",
    "visual-question-answering","zero-shot-classification","zero-shot-image-classification"
]

def fetch_hf_models(pipeline, limit=50, offset=0):
    url = f"https://huggingface.co/api/models"
    params = {"pipeline_tag":pipeline,"limit":limit,"skip":offset,"sort":"downloads","direction":-1}
    r = requests.get(url, params=params, timeout=30)
    return r.json() if r.status_code==200 else []

def insert_batch(apis):
    if not apis or not SB_KEY: return 0
    r = requests.post(f"{SB_URL}/rest/v1/api_brain",
        headers={**sbh(),"Prefer":"resolution=ignore-duplicates"},
        json=apis, timeout=30)
    return len(apis) if r.status_code in (200,201) else 0

def expand_hf(target=40000):
    total = get_count()
    print(f"Atual: {total} | Meta: {target}")
    added = 0
    
    for pipeline in HF_PIPELINES:
        if total + added >= target: break
        models = fetch_hf_models(pipeline, limit=100)
        batch = []
        for m in models[:50]:
            model_id = m.get("modelId","")
            if not model_id: continue
            downloads = m.get("downloads",0)
            if downloads < 100: continue
            batch.append({
                "name": model_id.split("/")[-1][:100],
                "category": "Machine Learning",
                "subcategory": pipeline.replace("-"," ").title(),
                "endpoint": f"https://api-inference.huggingface.co/models/{model_id}",
                "auth_type": "Bearer",
                "description": f"HF {pipeline} | {downloads:,} downloads | {model_id}",
                "relevance": 3 if downloads > 10000 else 2,
                "use_case": f"Pipeline {pipeline} automatizado gratis HuggingFace",
                "source": "huggingface",
                "tags": [pipeline, "huggingface", "free", model_id.split("/")[0] if "/" in model_id else "hf"]
            })
        n = insert_batch(batch)
        added += n
        print(f"  {pipeline}: +{n} ({total+added} total)")
        time.sleep(1)
    
    print(f"Expansao concluida. Total: {total+added}")

if __name__=="__main__":
    expand_hf(40000)
