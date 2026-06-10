"""
AFFILIATE TRACKER — Descobre e monitora oportunidades de afiliados
100% gratuito: APIs públicas + LLM gratuito
"""

import os, requests, json, datetime

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY2", "")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY2", "")
SUPABASE_URL   = os.environ.get("SUPABASE_URL2", "")
SUPABASE_KEY   = os.environ.get("SUPABASE_KEY2", "")

# Programas de afiliado 100% gratuitos para cadastrar
PROGRAMAS = [
    {
        "nome": "ClickBank",
        "url_cadastro": "https://clickbank.com",
        "comissao": "50-75% por venda",
        "nichos": ["psicologia", "autoajuda", "finanças", "IA"],
        "pagamento": "Wise / cheque",
        "minimo_saque": 100
    },
    {
        "nome": "Impact.com",
        "url_cadastro": "https://impact.com",
        "comissao": "$50-500 por referral",
        "nichos": ["SaaS", "ferramentas IA", "produtividade"],
        "pagamento": "Wise / PayPal",
        "minimo_saque": 50
    },
    {
        "nome": "PartnerStack",
        "url_cadastro": "https://partnerstack.com",
        "comissao": "% recorrente mensal",
        "nichos": ["SaaS", "tecnologia", "automação"],
        "pagamento": "PayPal",
        "minimo_saque": 25
    },
    {
        "nome": "Hotmart Afiliados",
        "url_cadastro": "https://hotmart.com",
        "comissao": "30-80% por venda",
        "nichos": ["cursos", "infoprodutos", "coaching"],
        "pagamento": "PIX instantâneo",
        "minimo_saque": 0
    },
    {
        "nome": "Amazon Associates",
        "url_cadastro": "https://associados.amazon.com.br",
        "comissao": "1-10%",
        "nichos": ["livros", "tecnologia", "produtos físicos"],
        "pagamento": "Depósito direto",
        "minimo_saque": 30
    }
]


def descobrir_produtos_afiliado(nicho: str) -> list[dict]:
    """Usa LLM para descobrir os melhores produtos de afiliado no nicho."""
    from quantum_brain import call_llm

    prompt = f"""
Você é especialista em marketing de afiliados em português brasileiro.
Nicho: {nicho}

Liste os 5 MELHORES produtos para promover como afiliado agora em 2026.
Critérios: alta comissão, alta conversão, produto legítimo.

Responda APENAS em JSON:
{{
  "produtos": [
    {{
      "nome": "...",
      "plataforma": "ClickBank/Hotmart/Impact",
      "comissao_pct": 60,
      "preco_medio": 97,
      "publico": "...",
      "argumento_venda": "..."
    }}
  ]
}}
"""
    resposta = call_llm(prompt)
    try:
        clean = resposta.strip().replace("```json","").replace("```","").strip()
        return json.loads(clean).get("produtos", [])
    except:
        return []


def gerar_link_afiliado_conteudo(titulo_video: str, produtos: list[dict]) -> str:
    """Gera texto de descrição com links de afiliado integrados naturalmente."""
    from quantum_brain import call_llm

    produtos_txt = "\n".join([
        f"- {p['nome']} ({p['plataforma']}): {p['argumento_venda']}"
        for p in produtos[:3]
    ])

    prompt = f"""
Crie uma descrição para YouTube que integra naturalmente recomendações de produtos.
Vídeo: "{titulo_video}"

Produtos para recomendar:
{produtos_txt}

A descrição deve:
- Ter 300-500 palavras
- Mencionar os produtos de forma NATURAL, não forçada
- Cada produto com o placeholder [LINK_AFILIADO_X] onde X é o número
- Tom: pesquisadora de comportamento humano, empática, especialista
- Terminar com CTA para inscrição

Responda apenas com o texto da descrição.
"""
    return call_llm(prompt)


def salvar_programa(programa: dict):
    """Salva programa de afiliado no Supabase."""
    if not SUPABASE_URL:
        return
    requests.post(
        f"{SUPABASE_URL}/rest/v1/affiliate_programs",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        },
        json={**programa, "created_at": datetime.datetime.now().isoformat()}
    )


def executar():
    print("💰 Affiliate Tracker iniciando...")

    for prog in PROGRAMAS:
        print(f"\n📌 {prog['nome']}")
        print(f"   Comissão: {prog['comissao']}")
        print(f"   Pagamento: {prog['pagamento']}")
        print(f"   Cadastro: {prog['url_cadastro']}")
        salvar_programa(prog)

    print("\n🔍 Descobrindo produtos para nicho psicologia...")
    produtos = descobrir_produtos_afiliado("psicologia e autoconhecimento")
    for p in produtos:
        print(f"  ✅ {p.get('nome')} — {p.get('comissao_pct')}% — R${p.get('preco_medio')}")

    print("\n✅ Affiliate Tracker concluído")
    return produtos


if __name__ == "__main__":
    executar()
