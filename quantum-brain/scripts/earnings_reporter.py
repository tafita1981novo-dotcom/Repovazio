"""
EARNINGS REPORTER — Relatório diário de ganhos às 8h
100% gratuito: Supabase + LLM gratuito
"""

import os, requests, json, datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL2", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY2", "")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY2", "")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY2", "")


def buscar_ganhos(dias: int = 7) -> list[dict]:
    """Busca ganhos dos últimos N dias no Supabase."""
    if not SUPABASE_URL:
        return []
    desde = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/earnings_log",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        },
        params={"date": f"gte.{desde}", "order": "date.desc"}
    )
    return r.json() if r.status_code == 200 else []


def calcular_totais(ganhos: list[dict]) -> dict:
    hoje = datetime.date.today().isoformat()
    ontem = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    total_hoje    = sum(g["revenue"] for g in ganhos if g.get("date") == hoje)
    total_ontem   = sum(g["revenue"] for g in ganhos if g.get("date") == ontem)
    total_semana  = sum(g["revenue"] for g in ganhos)
    total_mes     = sum(
        g["revenue"] for g in ganhos
        if g.get("date", "")[:7] == hoje[:7]
    )

    por_fonte = {}
    for g in ganhos:
        fonte = g.get("source", "outro")
        por_fonte[fonte] = por_fonte.get(fonte, 0) + g.get("revenue", 0)

    return {
        "hoje": round(total_hoje, 2),
        "ontem": round(total_ontem, 2),
        "semana": round(total_semana, 2),
        "mes": round(total_mes, 2),
        "por_fonte": {k: round(v, 2) for k, v in por_fonte.items()},
        "variacao_pct": round(
            ((total_hoje - total_ontem) / max(total_ontem, 0.01)) * 100, 1
        )
    }


def gerar_relatorio_texto(totais: dict) -> str:
    """Gera texto do relatório diário."""
    linhas = [
        "═══════════════════════════════════",
        "🧠 QUANTUM BRAIN — RELATÓRIO DIÁRIO",
        f"📅 {datetime.date.today().strftime('%d/%m/%Y')}",
        "═══════════════════════════════════",
        "",
        f"💰 HOJE:        ${totais['hoje']:.2f}",
        f"📊 ONTEM:       ${totais['ontem']:.2f} "
        f"({'↑' if totais['variacao_pct'] >= 0 else '↓'}"
        f"{abs(totais['variacao_pct'])}%)",
        f"📈 ESTA SEMANA: ${totais['semana']:.2f}",
        f"🗓️ ESTE MÊS:   ${totais['mes']:.2f}",
        "",
        "📌 POR FONTE:",
    ]
    for fonte, valor in totais["por_fonte"].items():
        linhas.append(f"   {fonte:20s} ${valor:.2f}")

    linhas += [
        "",
        "═══════════════════════════════════",
        "✅ Sistema rodando. Próxima execução: amanhã 3h UTC",
        "═══════════════════════════════════"
    ]
    return "\n".join(linhas)


def registrar_ganho(source: str, platform: str, revenue: float,
                    currency: str = "USD", payment_via: str = "wise",
                    notes: str = ""):
    """Registra um ganho no Supabase."""
    if not SUPABASE_URL:
        return False
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/earnings_log",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        json={
            "date":        datetime.date.today().isoformat(),
            "source":      source,
            "platform":    platform,
            "revenue":     revenue,
            "currency":    currency,
            "payment_via": payment_via,
            "notes":       notes
        }
    )
    return r.status_code in (200, 201)


def executar():
    print("📊 Earnings Reporter iniciando...")
    ganhos  = buscar_ganhos(dias=30)
    totais  = calcular_totais(ganhos)
    relatorio = gerar_relatorio_texto(totais)
    print(relatorio)

    # Salvar relatório como arquivo
    path = f"/tmp/relatorio_{datetime.date.today().isoformat()}.txt"
    with open(path, "w") as f:
        f.write(relatorio)

    return totais


if __name__ == "__main__":
    executar()
