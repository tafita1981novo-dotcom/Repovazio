"""
DISTRIBUIDOR — 1 vídeo → 6 plataformas em ~90 segundos
100% gratuito: Buffer API free tier
"""

import os, requests, json

BUFFER_TOKEN = os.environ.get("BUFFER_ACCESS_TOKEN2", "")

def get_profiles() -> dict:
    """Retorna IDs dos perfis conectados no Buffer."""
    r = requests.get(
        "https://api.bufferapp.com/1/profiles.json",
        params={"access_token": BUFFER_TOKEN}
    )
    if r.status_code != 200:
        return {}
    profiles = {}
    for p in r.json():
        service = p.get("service", "")
        profiles[service] = p.get("id", "")
    return profiles


def distribuir(texto: str, link_video: str = "", imagem_url: str = "") -> dict:
    """
    Publica em todas as plataformas conectadas via Buffer free.
    Buffer free: Instagram, Facebook, LinkedIn, X/Twitter, Pinterest, TikTok
    """
    if not BUFFER_TOKEN:
        print("❌ BUFFER_ACCESS_TOKEN não configurado")
        return {}

    profiles = get_profiles()
    resultados = {}

    for servico, profile_id in profiles.items():
        texto_plataforma = adaptar_texto(texto, servico, link_video)
        payload = {
            "access_token": BUFFER_TOKEN,
            "profile_ids[]": profile_id,
            "text": texto_plataforma,
            "shorten": True,
            "now": True  # publica imediatamente
        }
        if imagem_url:
            payload["media[photo]"] = imagem_url
        if link_video and servico == "youtube":
            payload["media[link]"] = link_video

        r = requests.post(
            "https://api.bufferapp.com/1/updates/create.json",
            data=payload,
            timeout=15
        )
        ok = r.status_code == 200
        resultados[servico] = ok
        print(f"{'✅' if ok else '❌'} {servico}: {'publicado' if ok else r.text[:80]}")

    return resultados


def adaptar_texto(base: str, plataforma: str, link: str = "") -> str:
    """Adapta o texto para cada plataforma."""
    hashtags_pt = "#psicologia #autoconhecimento #comportamento #mentalidade #desenvolvimentopessoal"

    if plataforma == "twitter":
        return f"{base[:200]}\n{link}"
    elif plataforma == "instagram":
        return f"{base}\n\n{hashtags_pt}\n\n🔗 Link na bio"
    elif plataforma == "linkedin":
        return f"{base}\n\nO que você pensa sobre isso? Comente abaixo 👇\n\n{link}"
    elif plataforma == "pinterest":
        return f"{base}\n\n{link}"
    else:
        return f"{base}\n\n{hashtags_pt}\n\n{link}"


if __name__ == "__main__":
    distribuir(
        "Novo vídeo: 7 sinais de ansiedade silenciosa que você ignora",
        "https://youtube.com/watch?v=EXEMPLO",
    )
