"""
TikTok Growth Engine — Ações diárias para crescimento acelerado
Meta: 100 seguidores em 7-14 dias via conteúdo viral + LIVE 24/7
"""
import os, requests, datetime

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY2", "")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY2", "")
SUPABASE_URL   = os.environ.get("SUPABASE_URL2", "")
SUPABASE_KEY   = os.environ.get("SUPABASE_KEY2", "")

# Trending hashtags TikTok para nicho sleep/wellness/psicologia
HASHTAGS_SLEEP = "#dormir #sombranco #relaxar #foco #ansiedade #sleepsounds #whitenoise #brownnoise #studywithme #focusmusic #somdechuva #meditacao #autoconhecimento #psicologia #comportamento"

HASHTAGS_VIRAL = "#fyp #paravocê #viral #trending #tiktokbrasil #fy #foryoupage #crescimento #mindset #saúdemental"

def gerar_bio_otimizada() -> str:
    return "🧠 Psicologia & Comportamento Humano\n🎵 Sons para Dormir & Focar LIVE 24/7\n💡 Autoconhecimento todo dia\n👇 Siga para conteúdo que transforma"

def gerar_descricao_video(titulo: str) -> str:
    hora = datetime.datetime.now().hour
    saudacao = "Bom dia" if 6 <= hora < 12 else "Boa tarde" if 12 <= hora < 18 else "Boa noite"
    return f"""{saudacao}! 🧠✨

{titulo}

{HASHTAGS_VIRAL}
{HASHTAGS_SLEEP}

🎵 LIVE 24/7 de sons para dormir → @newlife_2day
"""

def estrategia_crescimento():
    print("""
╔══════════════════════════════════════════════╗
║  ESTRATÉGIA 100 SEGUIDORES EM 14 DIAS        ║
╠══════════════════════════════════════════════╣
║  DIA 1-3:   LIVE 24/7 ativa + 3 vídeos/dia  ║
║  DIA 4-7:   Engajar nos comentários alheios  ║
║  DIA 8-14:  Duetos com conteúdo viral        ║
╠══════════════════════════════════════════════╣
║  LIVE 24/7 = principal motor de seguidores   ║
║  Rotação: Brown→White→Black→Pink→Rain noise  ║
║  Audiência mundial = seguidores globais      ║
╚══════════════════════════════════════════════╝
    """)

def executar():
    estrategia_crescimento()
    bio = gerar_bio_otimizada()
    print(f"\n📝 Bio otimizada:\n{bio}")
    desc = gerar_descricao_video("7 sinais de que você tem ansiedade silenciosa")
    print(f"\n📱 Descrição de vídeo exemplo:\n{desc}")
    if SUPABASE_URL:
        requests.post(f"{SUPABASE_URL}/rest/v1/growth_log",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                     "Content-Type": "application/json", "Prefer": "return=minimal"},
            json={"date": datetime.date.today().isoformat(), "platform": "tiktok",
                  "acao": "daily_growth_check", "status": "ok"}, timeout=10)
    print("\n✅ Growth engine executado")

if __name__ == "__main__":
    executar()
