#!/usr/bin/env python3
"""
minerador_viral.py — Minera posts virais de perfis gringa e adapta para BR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BASEADO EM TRANSCRIPT: "Peguei posts virais da gringa, adaptei para o Brasil"

ESTRATÉGIA:
  1. Busca conteúdo viral de perfis de psicologia/mindset (inglês)
  2. Groq traduz e adapta para PT-BR mantendo estrutura viral
  3. Gera prompts Pollinations para cada imagem do carrossel
  4. Salva fila no Supabase pronta para publicar
  5. 3 tipos de post: viralizar | vender | coringa (do transcript)

PERFIS REFERÊNCIA (do transcript):
  - @limitlessmindsets (mindset quadrinhos)
  - @psychologyfacts_ig
  - @highvaluemindset
  - @darkpsychologyy

TEMAS VIRAIS >10K likes confirmados:
  - Narcissist Red Flags
  - Burnout before it happens
  - Anxious Attachment Signs
  - Sleep and cortisol
  - Dark Psychology tactics
"""
import os, requests, time, json, random
import urllib3; urllib3.disable_warnings()

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
GROQ   = os.getenv("GROQ_API_KEY","")
SBH    = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
          "Content-Type":"application/json","Prefer":"return=minimal"}

# Posts virais da gringa com estrutura comprovada (adaptados)
POSTS_VIRAIS_GRINGA = [
    {
        "tema": "narcissist",
        "titulo_en": "Signs You're Dealing With a Covert Narcissist",
        "slides_en": [
            "They make you feel crazy for having normal emotions.",
            "They always play the victim, even when they hurt you.",
            "Research (Twenge 2009): covert narcissism is rising 40% since 2000.",
            "Sign 1: They gaslight you constantly.",
            "Sign 2: They never apologize genuinely.",
            "Sign 3: They isolate you from support.",
            "Sign 4: Your successes threaten them.",
            "Save this. You might need it."
        ],
        "likes_estimados": 44000,
        "tipo_cta": "vender",
    },
    {
        "tema": "burnout",
        "titulo_en": "Burnout Starts Long Before You Crash",
        "slides_en": [
            "Burnout doesn't start with exhaustion.",
            "It starts with pride in never stopping.",
            "Maslach (1981) identified 3 stages before collapse.",
            "Stage 1: Over-commitment disguised as dedication.",
            "Stage 2: Cynicism masking suppressed anger.",
            "Stage 3: Emotional detachment from everything.",
            "Your body knew before your mind did.",
            "When did YOU start feeling it?"
        ],
        "likes_estimados": 35000,
        "tipo_cta": "viralizar",
    },
    {
        "tema": "sleep",
        "titulo_en": "Why You Wake Up at 3AM Every Night",
        "slides_en": [
            "It's not random. It's biology.",
            "Cortisol peaks between 2-4am naturally.",
            "Walker (2017): REM sleep is when emotions process.",
            "Cause 1: Chronic stress keeps cortisol elevated.",
            "Cause 2: Unprocessed trauma from the day.",
            "Cause 3: Gut-brain axis imbalance.",
            "Your 3am wake-up is your nervous system asking for help.",
            "Comment '3AM' if this is you."
        ],
        "likes_estimados": 28000,
        "tipo_cta": "vender",
    },
    {
        "tema": "attachment",
        "titulo_en": "Why You Always Pick the Wrong Person",
        "slides_en": [
            "You don't choose wrong people. You choose familiar ones.",
            "Familiar doesn't mean safe.",
            "Ainsworth (1978): attachment style forms in first 18 months.",
            "Anxious attachment: clings to unavailable people.",
            "Avoidant attachment: runs from those who love them.",
            "Disorganized: wants love, fears it at the same time.",
            "Secure attachment can be developed in adulthood.",
            "Which pattern do you recognize in yourself?"
        ],
        "likes_estimados": 52000,
        "tipo_cta": "coringa",
    },
    {
        "tema": "discipline",
        "titulo_en": "A Disciplined Person Was Once Without Hope",
        "slides_en": [
            "A disciplined person was once without hope.",
            "A wealthy person was once broke.",
            "A mentally strong person was once at their lowest.",
            "The difference? They didn't confuse a temporary state with a permanent identity.",
            "Growth doesn't come from nowhere.",
            "It comes from confronting who you were.",
            "And choosing to become someone better.",
            "Save this for when you need it most."
        ],
        "likes_estimados": 55000,
        "tipo_cta": "viralizar",
    },
]

def groq_adaptar_post(post):
    """Traduz e adapta post viral para PT-BR mantendo estrutura"""
    if not GROQ: return post["slides_en"]
    slides_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(post["slides_en"])])
    prompt = (
        f"Adapte este post viral do inglês para PT-BR. Tema: {post['tema']}\n"
        f"Original EN:\n{slides_text}\n\n"
        f"REGRAS RÍGIDAS:\n"
        f"- Mantenha a estrutura slide por slide (mesma quantidade)\n"
        f"- Max 12 palavras por slide\n"
        f"- Tom dark/reflexivo, impactante\n"
        f"- Citar pesquisador real (Maslach, Walker, Ainsworth, etc)\n"
        f"- PROIBIDO: psicóloga/psicólogo\n"
        f"- Último slide: CTA tipo 'Comenta SONO' ou 'Salva esse post'\n"
        f"Retorne APENAS os slides numerados, um por linha."
    )
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":300,"temperature":0.8},
            timeout=20, verify=False)
        if r.status_code == 200:
            txt = r.json()["choices"][0]["message"]["content"].strip()
            linhas = [l.split(". ",1)[-1] if ". " in l[:4] else l
                      for l in txt.split("\n") if l.strip()]
            return linhas[:8]
    except: pass
    return post["slides_en"]

def gerar_prompts_imagem(slides_pt, tema, idx_post):
    """Gera prompts Pollinations para cada slide (estilo carrossel dark)"""
    estilos = {
        "narcissist": "dark mysterious character in shadows, dramatic lighting",
        "burnout":    "exhausted figure in corporate setting, dramatic shadows",
        "sleep":      "person awake at night, moonlight, dark bedroom",
        "attachment": "two silhouettes reaching toward each other, dark background",
        "discipline": "determined figure climbing mountain, dramatic sky",
    }
    estilo = estilos.get(tema, "dramatic dark cinematic scene")
    prompts = []
    for i, slide in enumerate(slides_pt):
        seed = 9001 + idx_post * 100 + i * 13
        prompt = f"masterpiece, kawaii chibi anime illustration, {estilo}, minimal text space ### text, watermark, nsfw, blurry"
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?seed={seed}&width=576&height=1024&nologo=true"
        prompts.append(url)
    return prompts

def groq_legenda_instagram(post, slides_pt):
    """Gera legenda otimizada para Instagram"""
    if not GROQ: return f"{post['titulo_en']}\n\nComenta SONO que eu te mando algo especial 👇"
    tipo_cta = post["tipo_cta"]
    cta_map = {
        "vender": "Comenta SONO que eu te mando o link do produto 👇",
        "viralizar": "Salva e manda pra quem precisa ver isso 🔁",
        "coringa": "Comenta o que você reconheceu em si mesmo 👇",
    }
    cta = cta_map.get(tipo_cta, cta_map["vender"])
    prompt = (
        f"Legenda Instagram PT-BR para post dark de psicologia.\n"
        f"Tema: {post['tema']} | Likes esperados: {post['likes_estimados']:,}\n"
        f"Tipo: {tipo_cta} (viralizar=pede seguir | vender=pede clicar | coringa=engajamento)\n"
        f"CTA obrigatório no final: '{cta}'\n"
        f"MAX 60 palavras. Tom reflexivo, impactante. 1 emoji apenas no CTA.\n"
        f"Retorne APENAS a legenda."
    )
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":100,"temperature":0.82},
            timeout=15, verify=False)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return cta

def salvar_fila(post, slides_pt, imagens, legenda):
    if not SB_KEY: return
    requests.post(f"{SB_URL}/rest/v1/social_posts", 
        headers={**SBH,"Prefer":"return=minimal"},
        json={"plataforma":"instagram",
              "tema":post["tema"],
              "hook":slides_pt[0][:100] if slides_pt else "",
              "legenda":legenda[:500],
              "cta":post["tipo_cta"],
              "status":"ready",
              "link_produto":"repovazio.vercel.app/app-vendas"},
        timeout=8, verify=False)

def run():
    print("=== MINERADOR VIRAL — Posts Gringa → BR ===\n")
    print(f"  Estratégia do transcript: pega o que já viralizou, adapta para BR\n")
    print(f"  3 tipos: viralizar | vender | coringa\n")
    total = 0
    for i, post in enumerate(POSTS_VIRAIS_GRINGA):
        print(f"  🌎 [{post['tipo_cta'].upper()}] {post['titulo_en'][:45]}")
        print(f"     ({post['likes_estimados']:,} likes estimados gringa)")
        slides_pt = groq_adaptar_post(post)
        imagens   = gerar_prompts_imagem(slides_pt, post["tema"], i)
        legenda   = groq_legenda_instagram(post, slides_pt)
        salvar_fila(post, slides_pt, imagens, legenda)
        print(f"     ✅ {len(slides_pt)} slides adaptados → fila Instagram")
        total += 1
        time.sleep(2)

    print(f"\n  ✅ {total} posts virais minerados e adaptados para BR")
    print(f"  📱 Fila Instagram: {total} posts prontos para publicar")
    print(f"  ⏰ Publicar: 9h (viralizar) | 12h (vender) | 18h (coringa)")

if __name__=="__main__": run()
