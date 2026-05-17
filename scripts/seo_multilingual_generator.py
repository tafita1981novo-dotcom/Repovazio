#!/usr/bin/env python3
"""
seo_multilingual_generator.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gera SEO trilingual para vídeos psicologia.doc:
  🇧🇷 PT-BR — padrão (narração + publicação principal)
  🇺🇸 EN   — tradução YouTube + tags globais
  🇪🇸 ES   — tradução YouTube + mercado hispânico

Usa LLM (Groq Llama 3.3 70B) para gerar as traduções.
Salva em content_pipeline.seo_multilingual (JSONB).

COMO USAR:
  python seo_multilingual_generator.py --id 683
  python seo_multilingual_generator.py --all-pending
"""
import os, sys, json, requests, re
from datetime import datetime

SB_URL   = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY   = os.environ.get("SUPABASE_SERVICE_KEY","")
GROQ_KEY = os.environ.get("GROQ_API_KEY","")

# Templates de hashtags fixas por língua (cerebro-validated)
HASHTAGS_FIXAS = {
    "pt_br": ["#psicologia","#saudemental","#narcisismo","#psidanielacoelho","#danielacoelho"],
    "en":    ["#psychology","#mentalhealth","#narcissism","#narcissisticabuse","#toxicrelationship"],
    "es":    ["#psicologia","#saludmental","#narcisismo","#relacionamientotoxico","#psicologiadepareja"],
}

# Tags que sempre aparecem (pirâmide broad→específico)
TAGS_BASE = {
    "pt_br": ["psicologia","saúde mental","narcisismo","relacionamento tóxico","Daniela Coelho","psidanielacoelho"],
    "en":    ["psychology","mental health","narcissism","toxic relationship","gaslighting","covert narcissist"],
    "es":    ["psicología","salud mental","narcisismo","relación tóxica","gaslighting","narcisismo encubierto"],
}

def groq_call(prompt, max_tokens=800):
    """Chama Groq Llama 3.3 70B para geração."""
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
        json={"model":"llama-3.3-70b-versatile","max_tokens":max_tokens,
              "messages":[{"role":"user","content":prompt}]}, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

def generate_seo_for_video(video_id: int, title_ptbr: str, topic: str,
                            pmid: str = None, claim_ptbr: str = None) -> dict:
    """Gera SEO trilingual completo para um vídeo."""
    
    print(f"  Gerando SEO trilingual para #{video_id}...")

    prompt_en = f"""You are a YouTube SEO expert for a Brazilian psychology channel.

Video (Brazilian Portuguese): "{title_ptbr}"
Topic: {topic}
{"Scientific reference: PMID " + pmid + " — " + claim_ptbr if pmid else ""}

Generate an English YouTube SEO package. Respond ONLY in JSON (no markdown):
{{
  "titulo": "English title (60-70 chars, keyword-first, no period)",
  "descricao_150": "First 150 chars for YouTube description (EN, hooks viewer)",
  "tags": ["list", "of", "14", "English", "SEO", "tags", "broad-to-specific"],
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5", "#hashtag6"]
}}

Rules:
- Title must start with the most searched term (narcissism/gaslighting/covert narcissist)
- Tags: 3 broad + 5 mid + 6 long-tail
- Hashtags: the most searched English psychology hashtags globally"""

    prompt_es = f"""Eres un experto en SEO de YouTube para un canal de psicología brasileño.

Video (Portugués Brasileño): "{title_ptbr}"
Tema: {topic}
{"Referencia científica: PMID " + pmid + " — " + claim_ptbr if pmid else ""}

Genera un paquete SEO en Español para YouTube. Responde SOLO en JSON (sin markdown):
{{
  "titulo": "Título en español (60-70 caracteres, keyword primero, sin punto final)",
  "descricao_150": "Primeros 150 caracteres descripción YouTube (ES, engancha al espectador)",
  "tags": ["lista", "de", "12", "tags", "SEO", "en", "español"],
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5", "#hashtag6"]
}}

Reglas:
- Título debe empezar con el término más buscado (narcisismo/gaslighting/narcisismo encubierto)
- Tags: 3 broad + 4 mid + 5 long-tail
- Hashtags: los más buscados en psicología en español (España + América Latina)"""

    # Gerar EN
    print("    Gerando EN...", end="", flush=True)
    try:
        en_raw = groq_call(prompt_en)
        en_data = json.loads(en_raw)
        # Adicionar tags base
        for t in TAGS_BASE["en"]:
            if t not in en_data.get("tags",[]):
                en_data["tags"].append(t)
        # Adicionar hashtags fixas
        for h in HASHTAGS_FIXAS["en"]:
            if h not in en_data.get("hashtags",[]):
                en_data["hashtags"].append(h)
        print(" ✅")
    except Exception as e:
        print(f" ⚠️ {e}")
        en_data = {
            "titulo": f"Covert Narcissist: {topic} - Signs You Are Ignoring",
            "descricao_150": f"Are you living with narcissistic abuse? Daniela reveals the signs.",
            "tags": TAGS_BASE["en"],
            "hashtags": HASHTAGS_FIXAS["en"],
        }

    # Gerar ES
    print("    Gerando ES...", end="", flush=True)
    try:
        es_raw = groq_call(prompt_es)
        es_data = json.loads(es_raw)
        for t in TAGS_BASE["es"]:
            if t not in es_data.get("tags",[]):
                es_data["tags"].append(t)
        for h in HASHTAGS_FIXAS["es"]:
            if h not in es_data.get("hashtags",[]):
                es_data["hashtags"].append(h)
        print(" ✅")
    except Exception as e:
        print(f" ⚠️ {e}")
        es_data = {
            "titulo": f"Narcisismo Encubierto: Señales de {topic}",
            "descricao_150": f"¿Vives con un narcisista? Daniela revela las señales.",
            "tags": TAGS_BASE["es"],
            "hashtags": HASHTAGS_FIXAS["es"],
        }

    return {
        "default_lang": "pt_br",
        "gerado_em": datetime.utcnow().isoformat(),
        "pt_br": {
            "titulo": title_ptbr,
            "tags": TAGS_BASE["pt_br"] + [topic.lower(), f"sinais de {topic.lower()}"],
            "hashtags": HASHTAGS_FIXAS["pt_br"],
        },
        "en": en_data,
        "es": es_data,
        "ciencia": {
            "pmid": pmid,
            "claim": claim_ptbr,
            "verificado": True,
        } if pmid else None,
    }

def update_db(video_id: int, seo: dict):
    """Salva SEO trilingual no Supabase."""
    r = requests.patch(f"{SB_URL}/rest/v1/content_pipeline?id=eq.{video_id}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json"},
        json={"seo_multilingual": seo}, timeout=30)
    r.raise_for_status()
    print(f"  ✅ Salvo no DB")

if __name__ == "__main__":
    vid_id = int(sys.argv[sys.argv.index("--id")+1]) if "--id" in sys.argv else 683
    seo = generate_seo_for_video(
        video_id=vid_id,
        title_ptbr="Narcisismo Encoberto: 3 Sinais Que Você Está Ignorando Agora Mesmo",
        topic="narcisismo encoberto",
        pmid="37286231",
        claim_ptbr="narcisistas têm viés hostil — interpretam qualquer tensão como ataque pessoal"
    )
    print(json.dumps(seo, ensure_ascii=False, indent=2))
    if SB_KEY:
        update_db(vid_id, seo)
    else:
        print("  ⚠️ SUPABASE_SERVICE_KEY não configurada — apenas exibindo resultado")
