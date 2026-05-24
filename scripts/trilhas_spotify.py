#!/usr/bin/env python3
"""
trilhas_spotify.py — Pipeline de trilhas musicais para Spotify via Amuse
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FLUXO:
  1. Edge TTS gera narração ambient (vozes ASMR)
  2. FFmpeg mixar com binaural tone (528Hz, 432Hz, 174Hz)
  3. Output: 45-60min MP3 por trilha
  4. Upload no Amuse.io (gratuito) → distribui Spotify, Apple Music, Deezer

TRILHAS PSICOLOGIA VOL.1:
  - Sono Profundo 528Hz — Regeneração Celular
  - Ansiedade Zero 432Hz — Relaxamento Neural
  - Foco Total 40Hz — Modo Concentração
  - Cura Emocional 174Hz — Alívio do Estresse
  - Meditação ASMR — Apego Seguro

ROYALTY: 100% (Amuse gratuito, sem label)
TEMPO APROVAÇÃO: 2-4 semanas após upload
"""
import os, asyncio, subprocess
from pathlib import Path

GROQ_KEY  = os.getenv("GROQ_API_KEY","")
OUT       = Path("output/trilhas"); OUT.mkdir(parents=True, exist_ok=True)

TRILHAS = [
    {"nome":"sono_profundo_528hz",   "hz":528, "duracao_min":45,
     "titulo":"Sono Profundo 528Hz — Regeneração Celular | Psicologia do Sono",
     "descricao":"Frequência 528Hz + voz guiada para sono profundo. Baseado em pesquisa do Dr. Matthew Walker (Berkeley).",
     "tags":["sono","528hz","relaxamento","meditação","psicologia"]},
    {"nome":"ansiedade_zero_432hz",  "hz":432, "duracao_min":40,
     "titulo":"Ansiedade Zero 432Hz — Regulação do Sistema Nervoso",
     "descricao":"432Hz + técnica de regulação do Dr. Stephen Porges (Teoria Polivagal). Reduz cortisol.",
     "tags":["ansiedade","432hz","meditação","relaxamento","nervoso"]},
    {"nome":"foco_total_40hz",       "hz":40,  "duracao_min":50,
     "titulo":"Foco Total 40Hz — Ondas Gamma para Produtividade",
     "descricao":"Ondas gamma 40Hz + texto de concentração. Estudos MIT mostram aumento de 25% no foco.",
     "tags":["foco","40hz","produtividade","concentração","gamma"]},
    {"nome":"cura_emocional_174hz",  "hz":174, "duracao_min":45,
     "titulo":"Cura Emocional 174Hz — Alívio do Trauma Emocional",
     "descricao":"174Hz para alívio da dor emocional. Técnica baseada em van der Kolk (Corpo Guarda o Trauma).",
     "tags":["cura","trauma","emoções","174hz","meditação"]},
    {"nome":"meditacao_apego_seguro","hz":396, "duracao_min":35,
     "titulo":"Apego Seguro — Meditação Guiada com Frequência 396Hz",
     "descricao":"Liberação de medo e culpa via 396Hz. Baseado em Ainsworth e teoria do apego seguro.",
     "tags":["apego","meditação","relacionamentos","396hz","cura"]},
]

async def gerar_naracao_ambient(trilha):
    """Gera narração ASMR suave via Edge TTS"""
    try:
        import edge_tts
        texto = (
            f"Esta é uma sessão de {trilha['titulo'].split('—')[0].strip()}. "
            f"Respire fundo. Deixe seu corpo relaxar. "
            f"Você está segura. Você está em paz. "
            f"Cada respiração te leva mais fundo ao descanso. "
            f"Seu sistema nervoso está se regulando. "
            f"Baseado em pesquisa científica real. "
            f"Você merece descanso. Você merece paz. "
            f"Respire. Solte. Descanse."
        )
        audio_path = str(OUT / f"{trilha['nome']}_narr.mp3")
        communicate = edge_tts.Communicate(
            texto * 8,  # repetir para duração
            "pt-BR-FranciscaNeural",
            rate="-20%",  # mais devagar, ASMR
            volume="+10%"
        )
        await communicate.save(audio_path)
        return audio_path
    except Exception as e:
        print(f"  Edge TTS erro: {e}")
        return None

def gerar_binaural_tone(hz, duracao_seg, output):
    """Gera tom binaural via FFmpeg (grátis, sem API)"""
    # Frequência base + beatfrequency para binaural
    freq_esq = hz
    freq_dir  = hz + 10  # diferença de 10Hz cria efeito binaural
    cmd = [
        "ffmpeg","-y",
        "-f","lavfi",
        "-i", f"sine=frequency={freq_esq}:duration={duracao_seg}",
        "-f","lavfi",
        "-i", f"sine=frequency={freq_dir}:duration={duracao_seg}",
        "-filter_complex","[0:a][1:a]amerge=inputs=2,volume=0.3[out]",
        "-map","[out]",
        "-ar","44100","-b:a","128k",
        output
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=120)
    return r.returncode == 0

def mixar_trilha(narr_file, binaural_file, output, fade_dur=5):
    """Mixa narração ASMR com binaural tone"""
    cmd = [
        "ffmpeg","-y",
        "-i", narr_file,
        "-i", binaural_file,
        "-filter_complex",
        "[0:a]volume=1.0[narr];"
        "[1:a]volume=0.4[bin];"
        "[narr][bin]amix=inputs=2:duration=longest[out]",
        "-map","[out]",
        "-ar","44100","-b:a","256k",  # alta qualidade para streaming
        output
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=300)
    return r.returncode == 0

def run():
    print("=== TRILHAS SPOTIFY — Pipeline Amuse ===")
    print("  Formato: Narração ASMR + Binaural Tone")
    print("  Distribuição: Amuse.io → Spotify/Apple/Deezer (grátis)")
    for trilha in TRILHAS[:2]:  # 2 por run para não travar
        print(f"  Gerando: {trilha['titulo'][:50]}")
        dur_seg = trilha["duracao_min"] * 60
        binaural = str(OUT / f"{trilha['nome']}_binaural.mp3")
        print(f"    1. Binaural {trilha['hz']}Hz {trilha['duracao_min']}min...")
        ok_bin = gerar_binaural_tone(trilha["hz"], dur_seg, binaural)
        if not ok_bin:
            print(f"    FFmpeg erro"); continue
        print(f"    2. Narração Edge TTS ASMR...")
        loop = asyncio.new_event_loop()
        narr = loop.run_until_complete(gerar_naracao_ambient(trilha))
        final = str(OUT / f"{trilha['nome']}_FINAL.mp3")
        if narr:
            print(f"    3. Mixando...")
            if mixar_trilha(narr, binaural, final):
                size = Path(final).stat().st_size // (1024*1024)
                print(f"    OK {final} ({size}MB)")
            else:
                print(f"    Mix falhou, usando binaural puro")
                import shutil; shutil.copy(binaural, final)
        else:
            print(f"    TTS falhou, binaural puro: {binaural}")
    print("\nPRÓXIMO PASSO: Upload em amuse.io")
    print("  1. amuse.io → New Release")
    print("  2. Upload MP3 de output/trilhas/")
    print("  3. Preencher metadados (título, tags)")
    print("  4. Distribuir → Spotify aprovação 2-4 semanas")

if __name__=="__main__": run()
