#!/usr/bin/env python3
"""
youtube_description_gen.py — Descrição YouTube SEO-otimizada com CTAs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRATÉGIA SEO (YouTube):
  - Primeiras 2 linhas: hook + keyword principal (aparece na preview)
  - Corpo: timestamp + conteúdo + pesquisadores citados
  - Links: app R$29,90 → WhatsApp R$216 → Instagram
  - Hashtags: 3 máximo (YouTube penaliza excesso)
  - Keywords: 10-15 palavras-chave no texto naturalmente

CANAL: @psidanielacoelho
REGRA: NUNCA mencionar psicóloga/psicólogo até jan/2027
"""
import os, requests, json, time
import urllib3; urllib3.disable_warnings()

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
GROQ   = os.getenv("GROQ_API_KEY","")
SBH    = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
          "Content-Type":"application/json","Prefer":"return=minimal"}

LINK_APP   = "https://repovazio.vercel.app/app-vendas"
LINK_WA    = "https://repovazio.vercel.app/psicologia-para-dormir"
LINK_INSTA = "https://instagram.com/psidanielacoelho"
LINK_YT    = "https://youtube.com/@psidanielacoelho"

TEMPLATE_DESCRICAO = """⚠️ {HOOK_LINHA_1}

{HOOK_LINHA_2}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 O QUE VOCÊ VAI APRENDER:
{TOPICOS}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ TIMESTAMPS:
00:00 — Introdução
{TIMESTAMPS}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔬 PESQUISAS CITADAS:
{PESQUISADORES}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 RECURSOS GRATUITOS E PAGOS:

🧠 App Modo Psicologia (R$29,90 único):
Rituais noturnos + missões + insights científicos
→ {LINK_APP}

🌙 Psicologia Para Dormir (R$216/ano):
Áudio diário 4min com Daniela — todo dia 19h30
→ {LINK_WA}

📸 Instagram: @psidanielacoelho
→ {LINK_INSTA}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{KEYWORDS_NATURAIS}

{HASHTAGS}
"""

VIDEOS_PIPELINE = [
    {
        "video_id": "narcis1",
        "titulo": "O Narcisista Encoberto Que Você Não Viu Chegar",
        "tema": "narcissism",
        "hook": "Você já sentiu que estava enlouquecendo em um relacionamento?",
        "topicos": ["Como identificar o narcisismo encoberto", "Os 5 sinais que ninguém fala", "Por que você ficou", "Como sair e curar"],
        "pesquisadores": ["Dr. Craig Malkin (Harvard)", "Dr. Ramani Durvasula (UCLA)", "Bessel van der Kolk (trauma)"],
        "keywords": ["narcisismo encoberto", "gaslighting", "abuso emocional", "relacionamento tóxico", "como sair de relacionamento abusivo"],
        "hashtags": ["#narcisismo", "#psicologia", "#relacionamentos"],
    },
    {
        "video_id": "sono1",
        "titulo": "Por Que Você Acorda Às 3h da Manhã (A Ciência Explica)",
        "tema": "sleep",
        "hook": "Acordar às 3h da manhã não é aleatório. É biologia.",
        "topicos": ["Cortisol e o ciclo do sono", "REM e processamento emocional", "O que o 3h diz sobre você", "Como resolver em 21 dias"],
        "pesquisadores": ["Matthew Walker (Berkeley)", "Russell Foster (Oxford)", "Robert Sapolsky (Stanford)"],
        "keywords": ["acordar às 3h", "insônia", "cortisol e sono", "ansiedade noturna", "como dormir melhor"],
        "hashtags": ["#sono", "#insônia", "#psicologia"],
    },
    {
        "video_id": "burnout1",
        "titulo": "Burnout Começa Antes Do Cansaço (3 Fases Que Ninguém Te Conta)",
        "tema": "burnout",
        "hook": "Burnout não começa com exaustão. Começa com orgulho de nunca parar.",
        "topicos": ["Fase 1: Supercompromisso", "Fase 2: Cinismo mascarado", "Fase 3: Desapego emocional", "Como reverter cada fase"],
        "pesquisadores": ["Christina Maslach (Berkeley)", "Herbert Freudenberger (pioneiro)", "Michael Leiter (burnout research)"],
        "keywords": ["burnout", "esgotamento mental", "burnout como evitar", "síndrome de burnout", "burnout fases"],
        "hashtags": ["#burnout", "#saúdemental", "#psicologia"],
    },
]

def groq_gerar_conteudo(video):
    if not GROQ:
        return {
            "hook_l1": video["hook"],
            "hook_l2": f"Neste vídeo, você vai entender {video['titulo'].lower()}.",
            "timestamps": "01:23 — Os primeiros sinais\n03:45 — A ciência por trás\n07:12 — Como resolver",
            "keywords_naturais": " ".join(video["keywords"]),
        }
    prompt = (
        f"Gere conteúdo para descrição YouTube para:\n"
        f"Título: {video['titulo']}\n"
        f"Hook: {video['hook']}\n\n"
        f"Retorne JSON com:\n"
        f"  hook_l1: string (hook linha 1, max 100 chars)\n"
        f"  hook_l2: string (complemento, max 100 chars)\n"
        f"  timestamps: string (5 timestamps formato mm:ss — Assunto)\n"
        f"  keywords_naturais: string (parágrafo de 50 palavras usando keywords naturalmente)\n"
        f"PROIBIDO: psicóloga/psicólogo. Retorne APENAS o JSON."
    )
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":300,"temperature":0.7},
            timeout=15, verify=False)
        if r.status_code == 200:
            txt = r.json()["choices"][0]["message"]["content"].strip()
            txt = txt.replace("```json","").replace("```","").strip()
            return json.loads(txt)
    except: pass
    return {"hook_l1":video["hook"],"hook_l2":"","timestamps":"","keywords_naturais":""}

def montar_descricao(video, conteudo):
    topicos = "\n".join([f"  ✓ {t}" for t in video["topicos"]])
    pesquisadores = "\n".join([f"  • {p}" for p in video["pesquisadores"]])
    return (TEMPLATE_DESCRICAO
        .replace("{HOOK_LINHA_1}", conteudo.get("hook_l1", video["hook"]))
        .replace("{HOOK_LINHA_2}", conteudo.get("hook_l2", ""))
        .replace("{TOPICOS}", topicos)
        .replace("{TIMESTAMPS}", conteudo.get("timestamps",""))
        .replace("{PESQUISADORES}", pesquisadores)
        .replace("{LINK_APP}", LINK_APP)
        .replace("{LINK_WA}", LINK_WA)
        .replace("{LINK_INSTA}", LINK_INSTA)
        .replace("{KEYWORDS_NATURAIS}", conteudo.get("keywords_naturais",""))
        .replace("{HASHTAGS}", " ".join(video["hashtags"]))
    )

def salvar_seo(video, descricao):
    if not SB_KEY: return
    requests.post(f"{SB_URL}/rest/v1/video_seo",
        headers={**SBH,"Prefer":"return=minimal"},
        json={"video_id":video["video_id"],
              "titulo_principal":video["titulo"],
              "descricao":descricao[:2000],
              "tags":json.dumps(video["keywords"]),
              "status":"ready"},
        timeout=8, verify=False)

def run():
    print("=== YOUTUBE DESCRIPTION GEN — SEO + CTAs ===\n")
    for video in VIDEOS_PIPELINE:
        print(f"  🎬 {video['titulo'][:45]}")
        conteudo = groq_gerar_conteudo(video)
        descricao = montar_descricao(video, conteudo)
        salvar_seo(video, descricao)
        print(f"     ✅ Descrição: {len(descricao)} chars | {len(video['keywords'])} keywords | {len(video['hashtags'])} hashtags")
        time.sleep(1)
    print(f"\n  ✅ {len(VIDEOS_PIPELINE)} descrições geradas e salvas no Supabase")
    print(f"  💰 Cada vídeo inclui CTA para R$29,90 app + R$216/ano WA")

if __name__=="__main__": run()
