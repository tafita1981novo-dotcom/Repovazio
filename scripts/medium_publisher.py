#!/usr/bin/env python3
"""medium_publisher.py — publica 9 artigos PT no Medium"""
import os, requests, base64, time

MEDIUM_TOKEN = os.getenv("MEDIUM_TOKEN", "")
GH_PAT       = os.getenv("GH_PAT", os.getenv("GITHUB_TOKEN", ""))
REPO         = os.getenv("GITHUB_REPOSITORY", "tafita81/Repovazio")
BIO = "Daniela Coelho · Pesquisa e Conteúdo em Psicologia · @psidanielacoelho"

ARTIGOS = [
    {"file":"output/medium_article_narcisismo_encoberto.md",
     "titulo":"Narcisismo Encoberto: 5 Sinais Que Ninguém Percebe (e a Ciência Explica Por Quê)",
     "tags":["psicologia","saude-mental","narcisismo","relacoes","autoconhecimento"]},
    {"file":"output/medium_article_apego_ansioso.md",
     "titulo":"Apego Ansioso: Por Que Sabotamos os Relacionamentos Que Mais Queremos",
     "tags":["psicologia","apego","relacoes","saude-mental","comportamento"]},
    {"file":"output/medium_article_neurociencia_ansiedade.md",
     "titulo":"Neurociência da Ansiedade: O Que Acontece no Seu Cérebro (e Por Que Isso Muda Tudo)",
     "tags":["neurociencia","ansiedade","psicologia","cerebro","saude-mental"]},
    {"file":"output/medium_article_impostor.md",
     "titulo":"Síndrome do Impostor: Por Que Pessoas Competentes Se Sentem Fraudes",
     "tags":["psicologia","carreira","autoconhecimento","saude-mental","performance"]},
    {"file":"output/medium_article_trauma_desenvolvimento.md",
     "titulo":"Trauma de Desenvolvimento: Como a Infância Molda o Adulto Que Você É",
     "tags":["trauma","psicologia","infancia","saude-mental","relacoes"]},
    {"file":"output/medium_article_gaslighting.md",
     "titulo":"Gaslighting: Como Identificar e Sair Quando a Realidade Parece Escorregadia",
     "tags":["psicologia","gaslighting","relacoes","saude-mental","trauma"]},
    {"file":"output/medium_article_validacao.md",
     "titulo":"Vício em Validação: Por Que Precisamos de Aprovação o Tempo Todo",
     "tags":["psicologia","redes-sociais","autoestima","saude-mental","comportamento"]},
    {"file":"output/medium_article_critica.md",
     "titulo":"Por Que Críticas Doem Tanto (E O Que a Neurociência Diz Para Fazer Com Isso)",
     "tags":["psicologia","neurociencia","feedback","saude-mental","autoconhecimento"]},
    {"file":"output/medium_article_amigos.md",
     "titulo":"Por Que É Tão Difícil Fazer Amigos na Vida Adulta (E O Que Pesquisas Mostram)",
     "tags":["psicologia","amizade","solidao","relacoes","saude-mental"]},
]

def get_file(path):
    if not GH_PAT: return None
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}",
        headers={"Authorization": f"token {GH_PAT}"}, timeout=15)
    return base64.b64decode(r.json()["content"]).decode() if r.status_code == 200 else None

def uid():
    r = requests.get("https://api.medium.com/v1/me",
        headers={"Authorization": f"Bearer {MEDIUM_TOKEN}"}, timeout=10)
    return r.json()["data"]["id"] if r.status_code == 200 else None

def publicar(user_id, titulo, content, tags):
    r = requests.post(f"https://api.medium.com/v1/users/{user_id}/posts",
        headers={"Authorization": f"Bearer {MEDIUM_TOKEN}", "Content-Type": "application/json"},
        json={"title": titulo, "contentFormat": "markdown",
              "content": content + f"\n\n---\n*{BIO}*",
              "tags": tags[:5], "publishStatus": "public"}, timeout=30)
    return r.json().get("data", {}).get("url", f"Erro {r.status_code}") if r.status_code in (200,201) else f"Erro {r.status_code}"

def run():
    if not MEDIUM_TOKEN:
        print("MEDIUM_TOKEN ausente.")
        print("medium.com/me/settings → Integration Tokens → gerar token")
        print("GitHub: tafita81/Repovazio → Settings → Secrets → MEDIUM_TOKEN")
        return
    user_id = uid()
    if not user_id: return
    print(f"Publicando {len(ARTIGOS)} artigos PT no Medium...")
    for i, art in enumerate(ARTIGOS):
        content = get_file(art["file"])
        if not content: print(f"  [{i+1}] ❌ arquivo não encontrado"); continue
        url = publicar(user_id, art["titulo"], content, art["tags"])
        ok = "medium.com" in url
        print(f"  [{i+1}] {'✅' if ok else '❌'} {art['titulo'][:55]}")
        time.sleep(5)

if __name__ == "__main__":
    run()
