#!/usr/bin/env python3
"""
youtube_comments_responder.py — Responde comentários automaticamente
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Como os maiores canais fazem:
  - Resposta rápida nas primeiras 2h após publicar (sinal de engajamento)
  - Linguagem natural, empática, com call-to-action suave
  - Groq gera resposta personalizada para cada comentário
  - TRANSPARENTE: é automação, não fraude. Canais como MrBeast usam equipes
    para responder — aqui é a IA da Daniela fazendo o mesmo trabalho.
  - YouTube PERMITE automação desde que não seja spam ou manipulação artificial.

REGRA: Sempre responder como Daniela Coelho, pesquisadora de comportamento humano.
PROIBIDO: psicóloga/psicólogo até jan/2027.
"""
import os, requests, time, json
import urllib3; urllib3.disable_warnings()

GROQ_KEY      = os.getenv("GROQ_API_KEY","")
YT_TOKEN      = os.getenv("YT_ACCESS_TOKEN","")
YT_REFRESH    = os.getenv("YT_REFRESH_TOKEN","")
YT_CLIENT_ID  = os.getenv("YT_CLIENT_ID","")
YT_CLIENT_SEC = os.getenv("YT_CLIENT_SECRET","")
CANAL_ID      = "UCyCkIpsVgME9yCj_oXJFheA"

# Templates de resposta por contexto detectado
TEMPLATES = {
    "identificacao": [
        "Que bom que você se identificou 💜 Isso que você descreveu é muito mais comum do que parece. A pesquisa de {pesquisador} mostra exatamente isso. Como você está lidando com isso hoje?",
        "Obrigada por compartilhar 🌙 O fato de você reconhecer esse padrão já é um passo enorme. Continue aqui — próxima semana trago mais sobre isso.",
        "Você não está sozinha nisso 💜 Isso que você descreveu tem um nome na ciência: {conceito}. Fica de olho no canal, vamos aprofundar!",
    ],
    "duvida": [
        "Ótima pergunta! De forma resumida: {resposta_curta}. Posso fazer um vídeo completo sobre isso — te aviso quando sair 🔔",
        "Essa dúvida merece um vídeo inteiro 😄 Por enquanto: {resposta_curta}. Já está na lista do canal!",
        "Boa pergunta! A pesquisa de {pesquisador} responde exatamente isso: {resposta_curta}. Salva esse comentário para quando o vídeo sair!",
    ],
    "agradecimento": [
        "Fico feliz que ajudou 💜 Isso me motiva a continuar pesquisando. Compartilha com alguém que precisa ver isso também!",
        "Isso me alegra muito 🌙 A Daniela continua aqui todo dia com mais pesquisas. Ativa o sininho para não perder!",
        "Obrigada de verdade 💜 Comentários como o seu são o que mantém esse canal vivo. Até o próximo!",
    ],
    "sono": [
        "Olá! Para quem quer ir mais fundo nesse tema do sono: tenho algo especial esperando por você 🌙 Comenta SONO aqui e te mando!",
        "Sono é um dos temas que mais pesquiso 💜 Se quiser um guia exclusivo baseado em ciência, comenta SONO que eu envio pra você!",
    ],
    "padrao": [
        "Obrigada pelo comentário 💜 Fico feliz que o conteúdo chegou até você. Continue acompanhando — tem muito mais por vir!",
        "Que bom ter você aqui 🌙 Se quiser mergulhar mais fundo, salva o vídeo e ativa as notificações para não perder nada!",
        "Muito obrigada 💜 Compartilha com alguém que precisa ver isso. Juntas chegamos mais longe!",
    ],
}

PESQUISADORES = ["Matthew Walker (Berkeley)","Craig Malkin (Harvard)","van der Kolk","Ainsworth","Gottman","Siegel (UCLA)"]
CONCEITOS     = ["apego ansioso","regulação do sistema nervoso","trauma bond","gaslighting","burnout crônico"]

def refresh_token():
    if not all([YT_REFRESH, YT_CLIENT_ID, YT_CLIENT_SEC]): return None
    try:
        r = requests.post("https://oauth2.googleapis.com/token",
            data={"client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SEC,
                  "refresh_token":YT_REFRESH,"grant_type":"refresh_token"},
            timeout=10)
        if r.status_code == 200: return r.json().get("access_token")
    except: pass
    return None

def detectar_contexto(texto):
    t = texto.lower()
    if any(w in t for w in ["me identifiquei","me vi","sou assim","passei","sofri","vivi"]): return "identificacao"
    if any(w in t for w in ["como","por que","qual","o que é","quando","dúvida","pergunta"]): return "duvida"
    if any(w in t for w in ["obrigada","obrigado","muito bom","incrível","excelente","ajudou","grata","gratidão"]): return "agradecimento"
    if any(w in t for w in ["sono","dormir","acordar","insônia","noite","cansada"]): return "sono"
    return "padrao"

def groq_resposta(comentario, contexto):
    if not GROQ_KEY:
        import random
        tpl = TEMPLATES[contexto][0]
        return tpl.replace("{pesquisador}", random.choice(PESQUISADORES)).replace("{conceito}", random.choice(CONCEITOS)).replace("{resposta_curta}", "isso é mais comum do que parece e tem solução baseada em ciência")
    prompt = (
        f"Você é Daniela Coelho, pesquisadora de comportamento humano.\n"
        f"Responda este comentário do YouTube de forma natural, empática e breve (max 2 frases + emoji).\n"
        f"CONTEXTO: {contexto}\n"
        f"COMENTÁRIO: {comentario}\n"
        f"REGRAS:\n"
        f"- Natural, como uma pessoa real responderia\n"
        f"- Empática mas objetiva\n"
        f"- Máx 50 palavras\n"
        f"- PROIBIDO: psicóloga/psicólogo. Usar: pesquisadora de comportamento humano\n"
        f"- Se for sono/dormem: CTA 'Comenta SONO que te envio algo especial'\n"
        f"Retorne APENAS a resposta, sem aspas."
    )
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":80,"temperature":0.82},
            timeout=12, verify=False)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except: pass
    import random
    return random.choice(TEMPLATES[contexto]).replace("{pesquisador}", random.choice(PESQUISADORES)).replace("{conceito}", random.choice(CONCEITOS)).replace("{resposta_curta}", "isso é muito mais comum do que parece")

def buscar_comentarios(token, video_id=None):
    if not token: return []
    params = {"part":"snippet","maxResults":50,"order":"time"}
    if video_id: params["videoId"] = video_id
    else:        params["allThreadsRelatedToChannelId"] = CANAL_ID
    try:
        r = requests.get("https://www.googleapis.com/youtube/v3/commentThreads",
            params=params,
            headers={"Authorization":f"Bearer {token}"},
            timeout=10)
        if r.status_code == 200:
            return r.json().get("items",[])
    except: pass
    return []

def responder_comentario(token, comment_id, resposta):
    if not token: return False
    try:
        r = requests.post("https://www.googleapis.com/youtube/v3/comments",
            params={"part":"snippet"},
            headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
            json={"snippet":{"parentId":comment_id,"textOriginal":resposta}},
            timeout=10)
        return r.status_code in (200, 201)
    except: return False

def run():
    print("=== YOUTUBE COMMENTS RESPONDER ===")
    print("  Como os grandes canais fazem: resposta automática + natural + rápida\n")
    token = refresh_token() or YT_TOKEN
    if not token:
        print("  Token YT não disponível — simulando respostas\n")
    comentarios = buscar_comentarios(token)
    respondidos = 0
    print(f"  Comentários encontrados: {len(comentarios)}")
    for item in comentarios[:20]:
        snippet   = item.get("snippet",{}).get("topLevelComment",{}).get("snippet",{})
        texto     = snippet.get("textDisplay","")
        author    = snippet.get("authorDisplayName","")
        comment_id= item.get("snippet",{}).get("topLevelComment",{}).get("id","")
        respondido= item.get("snippet",{}).get("totalReplyCount",0) > 0
        if respondido or not texto: continue
        contexto = detectar_contexto(texto)
        resposta = groq_resposta(texto[:200], contexto)
        print(f"  [{contexto}] @{author[:20]}: {texto[:40]}...")
        print(f"    → {resposta[:60]}...")
        if token and comment_id:
            ok = responder_comentario(token, comment_id, resposta)
            print(f"    {'✅ Respondido' if ok else '⚠️ Simulado'}")
        respondidos += 1
        time.sleep(2)
    print(f"\n  Total respondidos: {respondidos}")

if __name__=="__main__": run()
