#!/usr/bin/env python3
"""
whatsapp_produto.py — Psicologia Diária via WhatsApp (modelo do transcript)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BASEADO EM: Transcript "App de histórias que faturou R$1M"

ADAPTAÇÃO PARA PSICOLOGIA.DOC:
  Original: histórias infantis diárias via WhatsApp → R$216/ano
  Nossa versão: psicologia diária para ansiedade/sono → R$216/ano

PRODUTO:
  Nome: "Psicologia Para Dormir com Daniela Coelho"
  Entrega: 1 áudio guiado de 3-5 min por dia no WhatsApp
  Tema: ansiedade, sono, narcisismo, apego, mindfulness
  Formato: narração Daniela + música ambiente (Edge TTS + binaural)
  Hotmart: assinatura anual recorrente (cobrança automática)

FUNIL (do transcript):
  Instagram reels (sem aparecer, com IA) → comententa "sono" →
  DM com link da página de vendas →
  Checkout Hotmart R$216/ano →
  Grupo WhatsApp exclusivo →
  Áudio diário 19h30

TRABALHO DIÁRIO: 5-7 min (gerar áudio → enviar no grupo)
  → nosso pipeline JÁ FAZ automaticamente via GitHub Actions

PROJEÇÃO (modelo do transcript 1% de 500k downloads):
  1.000 assinantes × R$216 = R$216.000/ano = R$18.000/mês
  10.000 assinantes × R$216 = R$2.160.000/ano = R$180.000/mês
"""
import os, subprocess, requests, pathlib, time
import urllib3; urllib3.disable_warnings()

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
GROQ   = os.getenv("GROQ_API_KEY","")
SBH    = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
          "Content-Type":"application/json","Prefer":"return=minimal"}
TMP    = pathlib.Path("/tmp/whatsapp_prod"); TMP.mkdir(exist_ok=True)

PRODUTO = {
    "nome": "Psicologia Para Dormir",
    "descricao": "Daniela Coelho entrega todo dia um áudio de psicologia para você dormir melhor, reduzir a ansiedade e entender sua mente.",
    "preco_anual": 216.00,
    "preco_mensal": 19.90,
    "plataforma": "Hotmart",
    "publico": "adultos 25-50, ansiedade, insônia, desenvolvimento pessoal",
    "cta_instagram": "Comenta SONO que eu te envio o link 👇",
    "horario_entrega": "19:30",
    "formato_audio_segundos": 240,  # 4 min
}

# Temas para 30 dias de conteúdo
TEMAS_30_DIAS = [
    {"dia":1,  "tema":"ansiedade", "titulo":"Por Que Sua Mente Acelera Antes de Dormir",        "tecnica":"respiração 4-7-8"},
    {"dia":2,  "tema":"sono",      "titulo":"O Ritual que Harvard Usa para Dormir em 10 min",    "tecnica":"relaxamento progressivo"},
    {"dia":3,  "tema":"narcis",    "titulo":"Como Detectar se Você Está com um Narcisista",      "tecnica":"journaling protegido"},
    {"dia":4,  "tema":"burnout",   "titulo":"Seu Sistema Nervoso Está em Modo de Emergência",    "tecnica":"grounding 5-4-3-2-1"},
    {"dia":5,  "tema":"apego",     "titulo":"Por Que Você Escolhe Quem Te Faz Sofrer",           "tecnica":"meditação de compaixão"},
    {"dia":6,  "tema":"sono",      "titulo":"528Hz Reduz Cortisol em 65% — Ouça Esta Noite",    "tecnica":"binaural 528hz"},
    {"dia":7,  "tema":"ansiedade", "titulo":"A Técnica da Caixa que Militares Usam para Dormir", "tecnica":"box breathing"},
    {"dia":8,  "tema":"trauma",    "titulo":"Por Que Traumas Aparecem à Noite",                  "tecnica":"EMDR simplificado"},
    {"dia":9,  "tema":"sono",      "titulo":"O Hormônio que Você Destrói Toda Noite",            "tecnica":"higiene do sono"},
    {"dia":10, "tema":"mindful",   "titulo":"Meditação de 4 Minutos Para Limpar o Dia",          "tecnica":"body scan"},
    {"dia":11, "tema":"narcis",    "titulo":"Gaslighting Deixa Rastros no Seu Sono",             "tecnica":"validação emocional"},
    {"dia":12, "tema":"apego",     "titulo":"O Que o Seu Estilo de Apego Diz Sobre Seu Sono",   "tecnica":"autocuidado noturno"},
    {"dia":13, "tema":"ansiedade", "titulo":"Por Que Sua Ansiedade Piora à Noite",               "tecnica":"externalização de preocupações"},
    {"dia":14, "tema":"sono",      "titulo":"O Que Acontece no Seu Cérebro Durante a Fase REM",  "tecnica":"intenção de sonhos"},
    {"dia":15, "tema":"burnout",   "titulo":"O Dia em Que Seu Corpo Disse Não Antes de Você",    "tecnica":"recuperação parasimpática"},
]

def groq_gerar_audio_guiado(tema_info):
    """Gera script de áudio guiado para WhatsApp (3-4 min, narração Daniela)"""
    if not GROQ: return None
    prompt = (
        f"Write a 240-second guided audio script in Brazilian Portuguese.\n"
        f"Speaker: Daniela Coelho, pesquisadora de comportamento humano\n"
        f"Title: {tema_info['titulo']}\n"
        f"Topic: {tema_info['tema']}\n"
        f"Technique: {tema_info['tecnica']}\n\n"
        f"FORMAT (áudio guiado para dormir melhor):\n"
        f"- Abertura: apresentação calorosa (15s)\n"
        f"- Contexto científico: PubMed + pesquisador real (45s)\n"
        f"- Técnica guiada passo a passo (120s)\n"
        f"- Reflexão de fechamento (45s)\n"
        f"- Encerramento: 'Boa noite. Nos vemos amanhã.' (15s)\n\n"
        f"REGRAS:\n"
        f"- Tom: quente, calmo, confiante\n"
        f"- Inclui pauses [PAUSA 3s] para técnicas de respiração\n"
        f"- PROIBIDO: 'psicóloga/psicólogo'. Use: 'pesquisadora de comportamento humano'\n"
        f"- Total: ~300 palavras em PT-BR"
    )
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":600,"temperature":0.78},
            timeout=20, verify=False)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return None

def gerar_audio_tts(script, dia):
    """Converte script em áudio MP3 via Edge TTS (voz FranciscaNeural)"""
    # Remove marcadores de pausa para TTS (insere silêncio artificialmente)
    s = script.replace("[PAUSA 3s]"," ... ").replace("[PAUSA]"," ... ")
    s = ". ".join(x.strip() for x in s.replace("\n"," ").split(".") if x.strip())
    out = TMP/f"audio_dia{dia:02d}.mp3"
    subprocess.run(["edge-tts","--voice=pt-BR-FranciscaNeural","--rate=-18%",
                    f"--text={s}",f"--write-media={str(out)}"],
                   capture_output=True, timeout=90)
    return out if out.exists() and out.stat().st_size > 50000 else None

def mix_binaural(audio_p, hz=528):
    """Adiciona binaural 528Hz de fundo no áudio (relaxamento profundo)"""
    out = TMP/f"mix_528hz_{audio_p.stem}.mp3"
    bi = TMP/f"bi_{hz}.aac"
    if not bi.exists():
        hr = hz + 4
        subprocess.run(["ffmpeg","-y","-f","lavfi","-i",f"sine=frequency={hz}:duration=300",
                        "-f","lavfi","-i",f"sine=frequency={hr}:duration=300",
                        "-filter_complex","[0:a]volume=0.06[l];[1:a]volume=0.06[r];[l][r]amerge=inputs=2[out]",
                        "-map","[out]","-c:a","aac","-b:a","128k",str(bi)],
                       capture_output=True, timeout=60)
    if not bi.exists(): return audio_p
    subprocess.run(["ffmpeg","-y","-i",str(audio_p),"-i",str(bi),
                    "-filter_complex","[0:a]volume=1[v];[1:a]volume=0.10[f];[v][f]amix=inputs=2:duration=first[out]",
                    "-map","[out]","-c:a","libmp3lame","-b:a","128k","-shortest",str(out)],
                   capture_output=True, timeout=120)
    return out if out.exists() and out.stat().st_size > 50000 else audio_p

def salvar_supabase(tema, script, audio_path=""):
    if not SB_KEY: return
    requests.post(f"{SB_URL}/rest/v1/whatsapp_psicologia_queue", headers=SBH,
        json={"dia": tema["dia"], "titulo": tema["titulo"],
              "tema": tema["tema"], "tecnica": tema["tecnica"],
              "script": script[:800] if script else "",
              "audio_path": audio_path,
              "status": "ready" if audio_path else "pending",
              "horario_envio": "19:30"},
        timeout=8, verify=False)

def run():
    print("=== WHATSAPP PRODUTO — Psicologia Para Dormir ===\n")
    print(f"  Produto: {PRODUTO['nome']}")
    print(f"  Preço: R${PRODUTO['preco_anual']}/ano | R${PRODUTO['preco_mensal']}/mês")
    print(f"  Entrega: {PRODUTO['horario_entrega']} via WhatsApp\n")

    total = 0
    for tema in TEMAS_30_DIAS[:5]:  # 5 dias de conteúdo
        print(f"  📅 Dia {tema['dia']:02d}: {tema['titulo'][:45]}")
        script = groq_gerar_audio_guiado(tema)
        if not script:
            print(f"     ⚠️  sem script"); continue
        print(f"     📝 {len(script.split())} palavras geradas")

        audio = gerar_audio_tts(script, tema["dia"])
        if audio:
            audio_mix = mix_binaural(audio)
            size_kb = audio_mix.stat().st_size//1024
            print(f"     🎵 {audio_mix.name} ({size_kb}KB) com 528Hz")
            salvar_supabase(tema, script, str(audio_mix))
            total += 1
        else:
            salvar_supabase(tema, script)
        time.sleep(3)

    print(f"\n  ✅ {total} áudios gerados para WhatsApp")
    print(f"\n  FUNIL COMPLETO:")
    print(f"  Instagram Reels (IA) → '{PRODUTO['cta_instagram']}'")
    print(f"  → DM link → Hotmart R${PRODUTO['preco_anual']}/ano → Grupo WhatsApp → Áudio diário")
    print(f"\n  PROJEÇÃO:")
    print(f"  1.000 assinantes → R$216.000/ano = R$18.000/mês")
    print(f"  10.000 assinantes → R$2.160.000/ano = R$180.000/mês")

if __name__=="__main__": run()
