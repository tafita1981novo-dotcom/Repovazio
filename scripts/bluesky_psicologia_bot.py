#!/usr/bin/env python3
"""
bluesky_psicologia_bot.py
Posts 10 insights psicologia/dia no Bluesky automaticamente.
APIs GRATUITAS: Groq (LLM) + Bluesky ATP (sem auth de API, só conta)
Roda via GitHub Actions — totalmente zero custo.
"""
import os, json, time, random, requests
from datetime import datetime

GROQ_KEY = os.getenv("GROQ_API_KEY", "")
BSKY_HANDLE = os.getenv("BLUESKY_HANDLE", "psidanielacoelho.bsky.social")
BSKY_PASS = os.getenv("BLUESKY_APP_PASSWORD", "")

TEMAS = [
    "narcisismo encoberto e sinais sutis que a maioria ignora",
    "apego ansioso e por que a gente sabota relacionamentos bons",
    "trauma do abandono na infância e como aparece em adultos",
    "sindrome do impostor e a ciência por trás da autodúvida",
    "vício em validação externa — neurociência da aprovação",
    "depressão sorridente: quando a dor fica invisível",
    "regulação emocional — técnicas que a ciência confirma",
    "gaslighting: reconhecer e sair da manipulação",
    "perfeccionismo como mecanismo de defesa",
    "fronteiras emocionais saudáveis vs isolamento",
    "luto disenfranchised — luto que ninguém valida",
    "hipervigilância após trauma — o corpo lembra",
    "amizades tóxicas e por que é difícil sair",
    "autocompaixão: pesquisa de Kristin Neff simplificada",
    "comportamentos de apego evitativo no dia a dia",
    "burnout vs cansaço normal — diferenças reais",
    "ansiedade social: o que acontece no cérebro",
    "autoestima contingente vs incondicional",
    "paralisia por análise — psicologia da procrastinação",
    "solidão emocional mesmo rodeado de pessoas",
]

FORMATOS = [
    "Revele um insight contra-intuitivo sobre {tema}. Máximo 280 caracteres, sem bullet points. Tom: Daniela Coelho, psicóloga empática e direta. Comece com fato surpreendente.",
    "Qual é o mecanismo neural por trás de {tema}? Explique em 1 frase científica + 1 implicação prática. Total: 280 chars. Cite 1 pesquisador (nome real).",
    "Complete: 'A maioria das pessoas não sabe que {tema}...' — continue em 250 chars. Ângulo: revelar algo que parece óbvio mas não é.",
    "3 sinais de {tema} que ninguém fala. Formato: sem numeração, fluido, 275 chars máx. Tom: revelação, não lista clínica.",
    "Se você reconhece {tema} em alguém próximo, o que fazer? 260 chars. Resposta prática, não genérica.",
]

def gerar_post(tema):
    if not GROQ_KEY:
        return f"Sobre {tema}: a ciência revela padrões que mudam como entendemos nossas relações. O que você percebe em si mesmo?"
    
    fmt = random.choice(FORMATOS).format(tema=tema)
    prompt = f"""Você é Daniela Coelho (@psidanielacoelho), psicóloga brasileira.
Escreva um post para o Bluesky (máximo 280 caracteres) sobre: {tema}
Instrução: {fmt}
REGRAS: sem hashtags, sem emojis excessivos (max 1), sem aspas, sem "Daniela:", sem bullets.
Retorne APENAS o texto do post, nada mais."""
    
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile",
                  "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 150, "temperature": 0.85},
            timeout=20)
        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"].strip()
            text = text.strip('"').strip("'").strip()
            return text[:280]
    except Exception as e:
        print(f"Groq erro: {e}")
    return f"Sobre {tema}: padrões que mudam como nos relacionamos conosco e com os outros."

def bsky_login():
    if not BSKY_PASS:
        print("BLUESKY_APP_PASSWORD não configurado — skip Bluesky")
        return None, None
    r = requests.post("https://bsky.social/xrpc/com.atproto.server.createSession",
        json={"identifier": BSKY_HANDLE, "password": BSKY_PASS}, timeout=15)
    if r.status_code == 200:
        d = r.json()
        return d["accessJwt"], d["did"]
    print(f"Bluesky login falhou: {r.status_code} {r.text[:100]}")
    return None, None

def bsky_post(token, did, text):
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    r = requests.post("https://bsky.social/xrpc/com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {token}"},
        json={"repo": did, "collection": "app.bsky.feed.post",
              "record": {"$type": "app.bsky.feed.post", "text": text, "createdAt": now}},
        timeout=15)
    return r.status_code in (200, 201)

def run():
    print(f"=== BLUESKY PSICOLOGIA BOT — {datetime.now():%Y-%m-%d %H:%M} ===")
    n_posts = int(os.getenv("N_POSTS", "3"))
    temas_hoje = random.sample(TEMAS, min(n_posts, len(TEMAS)))
    
    token, did = bsky_login()
    posted = 0
    
    for i, tema in enumerate(temas_hoje):
        print(f"\n[{i+1}/{len(temas_hoje)}] Gerando: {tema[:40]}...")
        texto = gerar_post(tema)
        print(f"  Post ({len(texto)} chars): {texto[:80]}...")
        
        if token and did:
            ok = bsky_post(token, did, texto)
            print(f"  Bluesky: {'✅ publicado' if ok else '❌ falhou'}")
            if ok:
                posted += 1
        else:
            print(f"  [DRY RUN] Post gerado (sem credenciais Bluesky)")
            posted += 1
        
        if i < len(temas_hoje) - 1:
            time.sleep(random.uniform(30, 90))
    
    print(f"\nTotal: {posted}/{len(temas_hoje)} posts publicados")

if __name__ == "__main__":
    run()
