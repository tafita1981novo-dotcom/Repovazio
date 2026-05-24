#!/usr/bin/env python3
"""
quadrinhos_dark.py — Carrosséis dark de psicologia (Quadrinhos 2.0)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BASEADO EM: Transcript "R$31K em 10 dias com Claude e página dark"

ESTRATÉGIA:
  1. Posts virais gringa (psicologia/mindset) → adapta pro BR
  2. ChatGPT/Pollinations recria imagens no estilo Daniela (chibi kawaii)
  3. Canva (templates dark) finaliza carrossel
  4. 3 posts/dia: 9h (viralizar), 12h (vender), 18h (coringa)
  5. CTA: "Comenta SONO" → DM → produto

PRODUTOS:
  - Low ticket: R$29,90 (app-psicologia.html) → Kirvano/Hotmart
  - Premium: R$216/ano (Psicologia Para Dormir WhatsApp)

MATH do transcript adaptado:
  5 vendas/dia × R$29 = R$145/dia = R$4.350/mês (conservador)
  20 vendas/dia × R$29 = R$580/dia = R$17.400/mês (viral)
"""
import os, requests, time, json, random
import urllib3; urllib3.disable_warnings()

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
GROQ   = os.getenv("GROQ_API_KEY","")
SBH    = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
          "Content-Type":"application/json","Prefer":"return=minimal"}

# Horários de pico para postar (do transcript)
HORARIOS = ["09:00","12:00","18:00"]

# Perfis gringa para minerar (psicologia/mindset)
PERFIS_VIRAIS = [
    "limitlessmindsets",   # Mindset quadrinhos
    "psychologyfacts_ig",  # Psicologia facts
    "highvalue_mindset",   # Mentalidade
    "darkpsychologyy",     # Dark psychology
    "neuroscience.mind",   # Neurociência
]

# Temas virais + estrutura de carrossel (adaptado para BR psicologia)
TEMPLATES_CARROSSEL = [
    {
        "tema":"narcisismo",
        "titulo":"O Narcisista Que Parece Vítima",
        "slides":[
            {"tipo":"hook",      "texto":"Um narcisista raramente parece mal."},
            {"tipo":"reveal_1",  "texto":"Ele parece a VÍTIMA da história."},
            {"tipo":"reveal_2",  "texto":"E isso é exatamente o que o torna perigoso."},
            {"tipo":"ciencia",   "texto":"Kernberg (1975) chamou isso de 'grandiosidade frágil'."},
            {"tipo":"sinal_1",   "texto":"Sinal 1: Sempre é culpa de alguém."},
            {"tipo":"sinal_2",   "texto":"Sinal 2: Precisam de admiração constante."},
            {"tipo":"sinal_3",   "texto":"Sinal 3: Empatia só quando convém."},
            {"tipo":"cta",       "texto":"Salva este post. Pode ser útil um dia."},
        ],
        "cta_legenda":"Comenta SONO que te mando algo que vai te ajudar 👇",
        "publico_alvo":"relacionamento_toxicos",
    },
    {
        "tema":"burnout",
        "titulo":"Burnout Não Começa Com Cansaço",
        "slides":[
            {"tipo":"hook",      "texto":"Burnout não começa com cansaço."},
            {"tipo":"reveal_1",  "texto":"Começa com o orgulho de nunca parar."},
            {"tipo":"reveal_2",  "texto":"Com o 'eu aguento mais um pouco'."},
            {"tipo":"ciencia",   "texto":"Maslach (1981) identificou 3 fases antes do colapso."},
            {"tipo":"sinal_1",   "texto":"Fase 1: Excesso de comprometimento."},
            {"tipo":"sinal_2",   "texto":"Fase 2: Irritabilidade sem causa clara."},
            {"tipo":"sinal_3",   "texto":"Fase 3: Distanciamento emocional."},
            {"tipo":"cta",       "texto":"Você está em qual fase?"},
        ],
        "cta_legenda":"Comenta SONO se isso te tocou 👇",
        "publico_alvo":"burnout_ansiedade",
    },
    {
        "tema":"sono",
        "titulo":"Por Que Você Acorda às 3h da Manhã",
        "slides":[
            {"tipo":"hook",      "texto":"Você acorda exatamente às 3h da manhã?"},
            {"tipo":"reveal_1",  "texto":"Não é coincidência."},
            {"tipo":"reveal_2",  "texto":"É cortisol. É grelina. É o seu sistema nervoso pedindo socorro."},
            {"tipo":"ciencia",   "texto":"Walker (2017): REM é quando processamos emoções do dia."},
            {"tipo":"sinal_1",   "texto":"Causa 1: Estresse crônico elevado."},
            {"tipo":"sinal_2",   "texto":"Causa 2: Pico natural de cortisol às 2-4h."},
            {"tipo":"sinal_3",   "texto":"Causa 3: Trauma não processado."},
            {"tipo":"cta",       "texto":"Comenta 3H se você se identifica."},
        ],
        "cta_legenda":"Comenta SONO para receber o protocolo completo 👇",
        "publico_alvo":"insonia_ansiedade",
    },
    {
        "tema":"apego",
        "titulo":"Por Que Você Escolhe Quem Te Machuca",
        "slides":[
            {"tipo":"hook",      "texto":"Você não escolhe quem te machuca por acidente."},
            {"tipo":"reveal_1",  "texto":"Você escolhe o que parece familiar."},
            {"tipo":"reveal_2",  "texto":"E familiar nem sempre significa seguro."},
            {"tipo":"ciencia",   "texto":"Ainsworth (1978): apego é formado nos primeiros 18 meses de vida."},
            {"tipo":"sinal_1",   "texto":"Apego ansioso: clínica com quem afasta."},
            {"tipo":"sinal_2",   "texto":"Apego evitante: foge de quem ama."},
            {"tipo":"sinal_3",   "texto":"Apego seguro: pode ser desenvolvido na vida adulta."},
            {"tipo":"cta",       "texto":"Qual é o seu estilo de apego?"},
        ],
        "cta_legenda":"Comenta SONO que te mando algo especial 👇",
        "publico_alvo":"relacionamentos_autoconhecimento",
    },
    {
        "tema":"mindset",
        "titulo":"Uma Pessoa Disciplinada Já Foi Sem Esperança",
        "slides":[
            {"tipo":"hook",      "texto":"Uma pessoa disciplinada já foi sem esperança."},
            {"tipo":"reveal_1",  "texto":"Um rico já foi pobre."},
            {"tipo":"reveal_2",  "texto":"Um mentalmente forte já esteve no chão."},
            {"tipo":"ciencia",   "texto":"A diferença? Eles não confundiram estado temporário com identidade permanente."},
            {"tipo":"sinal_1",   "texto":"Crescimento não vem do nada."},
            {"tipo":"sinal_2",   "texto":"Vem de confrontar quem você era."},
            {"tipo":"sinal_3",   "texto":"E escolher ser alguém melhor."},
            {"tipo":"cta",       "texto":"Salva se isso ressoou com você."},
        ],
        "cta_legenda":"Comenta SONO para receber algo que vai mudar sua noite 👇",
        "publico_alvo":"desenvolvimento_pessoal",
    },
]

def groq_adaptar_slide(slide_texto, tema):
    """Adapta texto do slide para PT-BR mais impactante"""
    if not GROQ: return slide_texto
    prompt = (
        f"Reescreva em PT-BR para Instagram post dark de psicologia.\n"
        f"Tema: {tema}\nTexto original: '{slide_texto}'\n"
        f"Regras: max 12 palavras, impactante, sem hashtag, sem emoji\n"
        f"Retorne APENAS a frase reescrita, nada mais."
    )
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":50,"temperature":0.85},
            timeout=10, verify=False)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip().strip('"')
    except: pass
    return slide_texto

def gerar_prompt_pollinations(slide):
    """Gera prompt para Pollinations criar imagem do slide"""
    tipo = slide["tipo"]
    mapa = {
        "hook":     "kawaii chibi anime character looking shocked, dark background, minimalist",
        "reveal_1": "kawaii chibi anime character pointing at viewer, serious expression, dark",
        "reveal_2": "kawaii chibi anime character with magnifying glass, discovering something, dark",
        "ciencia":  "kawaii chibi anime character reading scientific book, glasses, dark background",
        "sinal_1":  "kawaii chibi anime character with WARNING sign, alert expression, dark",
        "sinal_2":  "kawaii chibi anime character holding number 2, thinking, dark background",
        "sinal_3":  "kawaii chibi anime character with red flag, observing, dark background",
        "cta":      "kawaii chibi anime character waving, friendly smile, purple glow, dark bg",
    }
    base = mapa.get(tipo, "kawaii chibi anime character, dark background, minimal")
    neg = "### text, watermark, nsfw, blurry, lowres, bad anatomy"
    return f"masterpiece, best quality, {base} {neg}"

def url_pollinations(prompt, idx):
    seed = 9001 + idx * 77
    p = requests.utils.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{p}?seed={seed}&width=576&height=576&nologo=true"

def gerar_scripts_legenda(template, groq=True):
    """Gera legenda completa do post com CTA"""
    if not GROQ: return f"{template['titulo']}\n\n{template['cta_legenda']}"
    prompt = (
        f"Escreva legenda para post dark de psicologia no Instagram em PT-BR.\n"
        f"Tema: {template['tema']}\nTítulo: {template['titulo']}\n"
        f"CTA obrigatório no final: '{template['cta_legenda']}'\n"
        f"Regras: 50-80 palavras, tom reflexivo/impactante, 1 emoji apenas no CTA\n"
        f"Retorne APENAS a legenda, sem explicação."
    )
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":120,"temperature":0.82},
            timeout=15, verify=False)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return f"{template['titulo']}\n\n{template['cta_legenda']}"

def salvar_supabase(template, legenda, slides_dados):
    if not SB_KEY: return
    requests.post(f"{SB_URL}/rest/v1/social_posts", headers=SBH,
        json={"plataforma":"instagram","tema":template["tema"],
              "hook":template["slides"][0]["texto"][:200],
              "legenda":legenda[:500],
              "cta":template["cta_legenda"],
              "status":"pending",
              "link_produto":"repovazio.vercel.app/app-psicologia"},
        timeout=8, verify=False)

def run():
    print("=== QUADRINHOS DARK — Carrosséis Psicologia ===\n")
    print(f"  Estratégia: 3 posts/dia | 9h 12h 18h | CTA: 'Comenta SONO'\n")
    print(f"  Produtos: R$29,90 app + R$216/ano WhatsApp\n")

    for i, tmpl in enumerate(TEMPLATES_CARROSSEL):
        print(f"  🎨 {tmpl['tema'].upper()}: '{tmpl['titulo'][:40]}'")

        # Gera slides adaptados
        slides_out = []
        for j, slide in enumerate(tmpl["slides"]):
            txt = groq_adaptar_slide(slide["texto"], tmpl["tema"])
            prompt_img = gerar_prompt_pollinations({"tipo":slide["tipo"]})
            img_url = url_pollinations(prompt_img, i*10+j)
            slides_out.append({"tipo":slide["tipo"],"texto":txt,"imagem":img_url})

        # Gera legenda
        leg = gerar_scripts_legenda(tmpl)
        salvar_supabase(tmpl, leg, slides_out)

        print(f"     ✅ {len(slides_out)} slides | legenda gerada")
        print(f"     🔗 img_0: {slides_out[0]['imagem'][:60]}...")
        time.sleep(2)

    print(f"\n  MATH (modelo do transcript):")
    print(f"   5 vendas/dia R$29 = R$145/dia = R$4.350/mês (conservador)")
    print(f"  20 vendas/dia R$29 = R$580/dia = R$17.400/mês (viral)")
    print(f"  + R$216/ano WhatsApp = receita recorrente")

if __name__=="__main__": run()
