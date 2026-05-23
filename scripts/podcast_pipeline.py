#!/usr/bin/env python3
"""
podcast_pipeline.py
Pipeline completo: Groq (roteiro) → Edge TTS (narração) → MP3 final
Tópicos: psicologia baseada em evidências, PT-BR, 8-12 minutos
Distribuição: Anchor FM → Spotify (gratuito, automático)
Custo: ZERO
"""
import os, asyncio, subprocess, json, time, random, requests
from pathlib import Path

GROQ_KEY = os.getenv("GROQ_API_KEY", "")
OUTPUT_DIR = Path(os.getenv("GITHUB_WORKSPACE", ".")) / "output" / "podcasts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EPISODIOS = [
    {"num": 1, "tema": "narcisismo encoberto", "subtitulo": "o tipo que ninguém vê"},
    {"num": 2, "tema": "apego ansioso", "subtitulo": "por que sabotamos relações boas"},
    {"num": 3, "tema": "trauma do abandono", "subtitulo": "como aparece em adultos"},
    {"num": 4, "tema": "síndrome do impostor", "subtitulo": "a ciência por trás da autodúvida"},
    {"num": 5, "tema": "depressão sorridente", "subtitulo": "quando a dor fica invisível"},
    {"num": 6, "tema": "burnout", "subtitulo": "diferenças reais do cansaço normal"},
    {"num": 7, "tema": "gaslighting", "subtitulo": "reconhecer e sair da manipulação"},
    {"num": 8, "tema": "fronteiras emocionais", "subtitulo": "saudáveis vs isolamento"},
]

VOZES_BOAS = [
    "pt-BR-AntonioNeural",      # voz masculina natural PT-BR
    "pt-BR-FranciscaNeural",    # voz feminina natural PT-BR
    "pt-BR-ThalitaMultilingualNeural",  # voz multilingual expressiva
]

def gerar_roteiro(tema, subtitulo, num):
    if not GROQ_KEY:
        return None
    
    prompt = f"""Você é Daniela Coelho, pesquisadora de comportamento humano brasileira especialista em relações.
Escreva roteiro de podcast Episódio {num}: "{tema.title()} — {subtitulo}"
8-10 minutos de fala natural (1100-1300 palavras).

ESTRUTURA:
[ABERTURA 30s] — frase gancho contra-intuitiva
[CASO REAL 90s] — história clínica fictícia mas realista  
[CIÊNCIA 2min] — pesquisadores reais: Malkin/Harvard, van der Kolk, Gottman, Siegel/UCLA
[5 SINAIS 3min] — não óbvios, específicos
[O QUE FAZER 90s] — 3 ações concretas
[ENCERRAMENTO 30s] — frase poderosa + próximo episódio

TOM: conversa entre amigas inteligentes. Direto, empático.
Use [pausa] para indicar pausas naturais.
Retorne APENAS o roteiro, sem comentários."""
    
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile",
                  "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 2000, "temperature": 0.8},
            timeout=60)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Groq erro: {e}")
    return None

async def narrar_edge_tts(texto, arquivo_saida, voz="pt-BR-FranciscaNeural"):
    """Narra texto usando Edge TTS (Microsoft, gratuito, ilimitado)"""
    try:
        import edge_tts
        # Remove marcadores de cena para leitura limpa
        texto_limpo = texto
        for tag in ["[ABERTURA", "[CASO", "[CIÊNCIA", "[SINAIS", "[FAZER", "[ENCERRAMENTO", "[pausa]", "[fim]"]:
            texto_limpo = texto_limpo.replace(tag, " ")
        
        communicate = edge_tts.Communicate(texto_limpo, voz, rate="+5%")
        await communicate.save(arquivo_saida)
        return True
    except ImportError:
        print("edge-tts não instalado. Instalar: pip install edge-tts")
        return False
    except Exception as e:
        print(f"Edge TTS erro: {e}")
        return False

def mixar_com_musica(narr_file, output_file, musica_volume=0.12):
    """Mixa narração com trilha ambiente via FFmpeg"""
    # Trilha silenciosa se não houver música
    cmd = [
        "ffmpeg", "-y",
        "-i", narr_file,
        "-af", f"volume=1.0,aecho=0.8:0.88:60:0.4",
        "-ar", "44100", "-ab", "128k",
        output_file
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    return result.returncode == 0

def run():
    print(f"=== PODCAST PIPELINE — {time.strftime('%Y-%m-%d %H:%M')} ===")
    ep_num = int(os.getenv("EPISODE_NUM", "1"))
    voz = os.getenv("TTS_VOICE", "pt-BR-FranciscaNeural")
    
    ep = next((e for e in EPISODIOS if e["num"] == ep_num), EPISODIOS[0])
    print(f"Episódio {ep['num']}: {ep['tema']} — {ep['subtitulo']}")
    
    # 1. Gerar roteiro
    print("1. Gerando roteiro via Groq...")
    roteiro = gerar_roteiro(ep["tema"], ep["subtitulo"], ep["num"])
    
    if not roteiro:
        print("   Groq indisponível — usando roteiro de template")
        roteiro = f"Olá, eu sou Daniela Coelho. Hoje vamos falar sobre {ep['tema']}. {ep['subtitulo'].capitalize()}. Este é um tema que aparece frequentemente no consultório e que merece uma conversa honesta e baseada em evidências."
    
    # Salvar roteiro
    roteiro_path = OUTPUT_DIR / f"ep{ep_num:02d}_roteiro.md"
    with open(roteiro_path, "w", encoding="utf-8") as f:
        f.write(f"# Episódio {ep['num']}: {ep['tema'].title()}\n")
        f.write(f"## {ep['subtitulo'].title()}\n\n")
        f.write(roteiro)
    print(f"   Roteiro salvo: {roteiro_path}")
    
    # 2. Narrar com Edge TTS
    narr_path = str(OUTPUT_DIR / f"ep{ep_num:02d}_narracao.mp3")
    print(f"2. Narrando com Edge TTS ({voz})...")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ok = loop.run_until_complete(narrar_edge_tts(roteiro, narr_path, voz))
    
    if ok:
        print(f"   Narração salva: {narr_path}")
        
        # 3. Mixar
        final_path = str(OUTPUT_DIR / f"podcast_ep{ep_num:02d}_{ep['tema'].replace(' ', '_')}.mp3")
        print("3. Finalizando áudio...")
        if mixar_com_musica(narr_path, final_path):
            print(f"   PRONTO: {final_path}")
            print(f"\n=== PUBLICAR NO ANCHOR FM ===")
            print(f"1. Acesse: https://anchor.fm/dashboard")
            print(f"2. New Episode → Upload Audio → selecione: {final_path}")
            print(f"3. Título: Ep.{ep_num}: {ep['tema'].title()} — {ep['subtitulo'].title()}")
            print(f"4. Publish → distribui Spotify automaticamente (48h)")
        else:
            print(f"   MP3 final (sem mix): {narr_path}")
    else:
        print("   Edge TTS falhou — verifique instalação")
        print(f"   Roteiro disponível em: {roteiro_path}")

if __name__ == "__main__":
    run()
