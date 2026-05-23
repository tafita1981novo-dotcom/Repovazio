#!/usr/bin/env python3
"""
gumroad_publisher.py
Publica produtos digitais no Gumroad via API.

SETUP:
1. gumroad.com → Account → Advanced → Access Token
2. GitHub Secret: GUMROAD_ACCESS_TOKEN

Produtos prontos:
- 50 Prompts Power BI + IA ($19)
- Template Notion Saúde Mental ($9)
"""
import os, requests, pathlib

TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN", "")
BASE  = "https://api.gumroad.com/v2"

PRODUTOS = [
    {
        "name":         "50 Prompts Power BI + IA — Do DAX ao Dashboard",
        "price":        1900,  # centavos USD
        "description":  """15 anos de Power BI condensados em 50 prompts testados com GPT-4o, Claude e Copilot.

5 módulos: DAX Avançado | Design de Dashboards | Power Query + Modelagem | IA no Power BI | Governança.

Cada prompt inclui contexto de uso e resultado esperado.""",
        "file_key":     "50_prompts_powerbi",
        "tags":         ["power bi", "analytics", "dax", "ia", "dashboard"],
    },
    {
        "name":         "Template Notion — Sistema de Saúde Mental",
        "price":        900,
        "description":  """Sistema completo de saúde mental e produtividade no Notion.

Inclui: Diário CBT (Aaron Beck), Tracker de emoções, Sistema de hábitos, Plano de regulação emocional, Revisão semanal.

Baseado em Ainsworth, Gottman e Gross.""",
        "file_key":     "notion_template_saude_mental",
        "tags":         ["notion", "saúde mental", "cbt", "hábitos", "produtividade"],
    },
]

def verificar_token():
    if not TOKEN:
        print("GUMROAD_ACCESS_TOKEN ausente.")
        print()
        print("COMO CONFIGURAR (2 minutos):")
        print("1. gumroad.com → Login → Account → Advanced → Access Token")
        print("2. Copiar o token")
        print("3. GitHub: tafita81/Repovazio → Settings → Secrets → New")
        print("   Nome: GUMROAD_ACCESS_TOKEN")
        print("   Valor: [token copiado]")
        print()
        print("Depois, rodar: python3 scripts/gumroad_publisher.py")
        return False
    return True

def criar_produto(produto):
    r = requests.post(f"{BASE}/products",
        headers={"Authorization": f"Bearer {TOKEN}"},
        data={
            "name":         produto["name"],
            "price":        produto["price"],
            "description":  produto["description"],
            "published":    True,
            "tags":         ",".join(produto["tags"][:5]),
        }, timeout=30)
    if r.status_code in (200, 201):
        data = r.json().get("product", {})
        return data.get("short_url", "criado")
    return f"Erro {r.status_code}: {r.text[:200]}"

def run():
    if not verificar_token(): return
    
    print(f"=== GUMROAD PUBLISHER — {len(PRODUTOS)} produtos ===")
    for i, prod in enumerate(PRODUTOS):
        print(f"\n  [{i+1}] {prod['name'][:55]}")
        url = criar_produto(prod)
        ok = "gumroad.com" in url or "https://" in url
        print(f"  {'✅' if ok else '❌'} {url[:70]}")
    print("\n✅ Produtos publicados — compartilhar links nas redes sociais")

if __name__ == "__main__":
    run()
