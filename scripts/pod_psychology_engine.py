#!/usr/bin/env python3
"""
pod_psychology_engine.py
Gera designs de print-on-demand (POD) para psicologia.

Modelo anônimo: zero rosto → produto + identidade = receita passiva.
Plataformas: Redbubble, Merch by Amazon, Printify (Shopify)

Tipos de produto:
  - Camisetas com frases de psicologia
  - Canecas com insights científicos
  - Posters motivacionais baseados em pesquisa
  - Notebooks/diários para autoconhecimento

Keywords de alta busca (Redbubble/Amazon):
  - "psychology gift", "mental health awareness"
  - "anxious attachment", "narcissism awareness"
  - "therapy humor", "introvert", "neuroscience"
"""
import os, requests, time, json, pathlib

GROQ = os.getenv("GROQ_API_KEY", "")
SB_URL = os.getenv("SUPABASE_URL", "")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
SBH = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
       "Content-Type": "application/json", "Prefer": "return=minimal"}
TMP = pathlib.Path("/tmp/pod"); TMP.mkdir(exist_ok=True)

# Frases de alta conversão para merch — baseadas em pesquisa
FRASES_BASE = {
    "apego_ansioso": [
        "My attachment style is: 'please don't leave'",
        "Anxiously attached but healing",
        "My love language is anxious attachment (I'm working on it)",
        "Childhood: complicated. Adult: in therapy.",
    ],
    "narcisismo": [
        "I survived a narcissist and all I got was this trauma",
        "Not your therapist. Not your punching bag. Not anymore.",
        "Empaths attract narcissists — until they don't",
        "Healing is realizing you weren't 'too sensitive'",
    ],
    "burnout": [
        "Burned out but make it aesthetic",
        "My body said 'rest' and my brain said 'anxiety'",
        "Cortisol is not a personality trait",
        "High functioning doesn't mean okay",
    ],
    "geral_psicologia": [
        "Neuroplasticity: your brain can change. And so can you.",
        "The nervous system knows what the mind won't admit",
        "Therapy taught me: other people's behavior is about them",
        "Dopamine, serotonin, oxytocin — the holy trinity",
        "My emotional regulation arc",
    ],
    "sono_frequencias": [
        "528Hz and chill",
        "Brain waves before business waves",
        "Delta waves are free therapy",
        "My sleep schedule has anxiety too",
    ],
}

# Prompts para gerar designs via Pollinations (sem texto na imagem!)
DESIGN_PROMPTS = {
    "minimalista": "minimal psychology concept art, clean lines, purple violet palette, white background, geometric brain motif, no text, modern design aesthetic",
    "dark_aesthetic": "dark psychology art, deep purple black, neon accent, neuroscience concept, aesthetic minimal, no text, high contrast",
    "pastel_healing": "soft pastel healing art, mint lavender pink, botanical elements, wellness concept, flat design, no text, gentle aesthetic",
    "scientific": "neuroscience diagram art, blue purple scientific illustration, synaptic connections, brain waves, minimal, no text",
}

def groq_frase(categoria, idioma="EN"):
    if not GROQ: return None
    prompt = (
        f"Generate 3 original t-shirt/mug design phrases about {categoria} psychology "
        f"in {idioma}. Rules: witty, relatable, NOT cliché, max 8 words each, "
        f"appeal to people in therapy/healing. Return ONLY the phrases, numbered 1-3."
    )
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile",
                  "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 100, "temperature": 0.90},
            timeout=20)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return None

def gerar_design_art(categoria, seed):
    """Gera arte de fundo para o design (SEM TEXTO no prompt)"""
    prompt = DESIGN_PROMPTS.get(
        {"apego_ansioso": "pastel_healing",
         "narcisismo": "dark_aesthetic",
         "burnout": "scientific",
         "sono_frequencias": "dark_aesthetic"}.get(categoria, "minimalista"))
    url = (f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt[:350])}"
           f"?model=flux&width=4500&height=5400&seed={seed}&nologo=true")
    try:
        r = requests.get(url, timeout=55)
        if r.status_code == 200 and len(r.content) > 20000:
            return r.content
    except: pass
    return None

def salvar_design(frase, categoria, arte=None):
    if not SB_KEY: return
    requests.post(f"{SB_URL}/rest/v1/pod_designs", headers=SBH,
        json={"frase": frase[:200], "categoria": categoria,
              "plataformas": ["Redbubble", "Merch Amazon", "Printify"],
              "status": "pending_upload", "has_art": arte is not None},
        timeout=8)

def run():
    print("=== PRINT-ON-DEMAND — Psicologia Anônima ===")
    print("Modelo: Redbubble + Merch Amazon — royalties passivos\n")
    total_frases = 0
    total_artes = 0

    for categoria, frases_base in FRASES_BASE.items():
        print(f"\n  📦 {categoria}:")

        # Salvar frases base
        for frase in frases_base:
            salvar_design(frase, categoria)
            total_frases += 1
            print(f"    ✅ '{frase[:50]}'")

        # Gerar frases novas com Groq
        novas = groq_frase(categoria)
        if novas:
            for linha in novas.split('\n')[:3]:
                frase_limpa = linha.lstrip('123. ').strip()
                if frase_limpa and len(frase_limpa) > 5:
                    salvar_design(frase_limpa, categoria)
                    total_frases += 1
                    print(f"    🆕 '{frase_limpa[:50]}'")

        time.sleep(2)

    print(f"\n{'='*45}")
    print(f"  ✅ {total_frases} frases/designs salvos no Supabase")
    print(f"  📤 Próximo: upload para Redbubble via API")
    print(f"  💰 Royalties: ~$2-8 por venda, sem estoque")

if __name__ == "__main__":
    run()
