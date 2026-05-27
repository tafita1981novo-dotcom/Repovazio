"""
gen_audio_samples_v2.py — Vozes FEMININAS + estilo top podcasts mundiais
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORREÇÕES vs v1:
  ❌ Voz masculina Antonio              → ✅ Francisca (PT) / Aria (EN) / Pilar (ES) / Nanami (JA)
  ❌ "Eu sou Daniela Coelho..."         → ✅ ZERO menção de nome (igual Sleep Magic/Pilar)
  ❌ Rate -12% (rápido demais p/ sono)  → ✅ Rate -25% + pitch -5% (igual Sleep Cove)
  ❌ Frases corridas                     → ✅ Reticências longas criando pausas hipnóticas
  ❌ "Eu sou Daniela e vou guiar..."     → ✅ Voz direta no corpo, igual top mundial

REFERÊNCIAS COPIADAS (estilo, não áudio — copyright):
  Sleep Magic (Jessica Porter) — voz feminina americana, pausas longas, body scan
  Medita con Pilar (ES)        — voz feminina espanhola, suavidade, segunda pessoa
  Persono (PT)                  — voz feminina brasileira, técnica escaneamento
  Nanami sleep ASMR (JA)        — sussurro suave japonês
"""
import os, asyncio, edge_tts, subprocess, pathlib, requests

OUT = pathlib.Path("/tmp/samples_v2"); OUT.mkdir(exist_ok=True)
SUPABASE_URL = "https://tpjvalzwkqwttvmszvie.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# ════════════════════════════════════════════════════════════════════════════
# VOZES FEMININAS — selecionadas para imitar top podcasts sono mundiais
# ════════════════════════════════════════════════════════════════════════════
VOICES = {
    "PT": "pt-BR-FranciscaNeural",       # estilo Persono — suave brasileira
    "EN": "en-US-AriaNeural",            # estilo Sleep Magic — feminina americana warm
    "ES": "es-ES-ElviraNeural",          # estilo Medita con Pilar — feminina espanhola
    "JA": "ja-JP-NanamiNeural",          # estilo ASMR japonês — sussurro suave
}

# ════════════════════════════════════════════════════════════════════════════
# TEXTOS REESCRITOS — estilo poético hipnótico, ZERO menção de nome
# Reticências = pausas naturais que Edge TTS respeita
# ════════════════════════════════════════════════════════════════════════════
SAMPLES = {
"PT": (
 # Indução hipnótica suave (igual abertura Persono/Projeto Meditar)
 "Feche os olhos suavemente... "
 "respire... "
 "deixe o ar entrar... "
 "e sair... "
 "naturalmente... "
 "cada respiração... te leva mais fundo... "
 "seus pés relaxam... "
 "suas pernas pesam... "
 "seu peito se solta... "
 "seus ombros descem... "
 "não há nada que precise ser feito agora... "
 "apenas estar... "
 "apenas respirar..."
),
"EN": (
 # Estilo Sleep Magic (Jessica Porter) — pausas longas, segunda pessoa direta
 "Close your eyes gently... "
 "breathe in... "
 "let the air enter... "
 "and leave... "
 "naturally... "
 "each breath... takes you deeper... "
 "your feet relax... "
 "your legs grow heavy... "
 "your chest softens... "
 "your shoulders drop... "
 "there is nothing you need to do now... "
 "only being... "
 "only breathing..."
),
"ES": (
 # Estilo Medita con Pilar — voz feminina suave espanhola
 "Cierra los ojos suavemente... "
 "respira... "
 "deja que el aire entre... "
 "y salga... "
 "naturalmente... "
 "cada respiración... te lleva más profundo... "
 "tus pies se relajan... "
 "tus piernas pesan... "
 "tu pecho se suelta... "
 "tus hombros bajan... "
 "no hay nada que necesites hacer ahora... "
 "solo ser... "
 "solo respirar..."
),
"JA": (
 # Estilo ASMR japonês — sussurro contemplativo
 "そっと目を閉じてください... "
 "息を吸って... "
 "空気が入ってくるのを... "
 "そして出ていくのを... "
 "自然に感じてください... "
 "一呼吸ごとに... もっと深くへ... "
 "足が緩み... "
 "脚が重くなり... "
 "胸が柔らかくなり... "
 "肩が下がります... "
 "今何かをする必要はありません... "
 "ただ在るだけ... "
 "ただ呼吸するだけ..."
),
}

async def gen_tts_warm(text, voice, out):
    """TTS com pitch -5% (mais grave/quente) + rate -25% (lento hipnótico)"""
    c = edge_tts.Communicate(text, voice, rate="-25%", pitch="-5Hz")
    await c.save(str(out))

# ════════════════════════════════════════════════════════════════════════════
# CAMA AMBIENTE — sons de chuva mais densos (igual canais top)
# ════════════════════════════════════════════════════════════════════════════
print("🎵 Cama ambiente: binaural 528Hz + chuva mais densa (estilo Sleep Cove)")
bed = OUT / "bed.aac"
subprocess.run(["ffmpeg","-y",
    "-f","lavfi","-i","sine=frequency=528:duration=90",
    "-f","lavfi","-i","sine=frequency=532:duration=90",
    "-f","lavfi","-i","anoisesrc=color=brown:duration=90",  # brown = chuva mais grave que pink
    "-filter_complex",
    "[0:a]volume=0.04[l];[1:a]volume=0.04[r];"
    "[l][r]amerge=inputs=2[bin];"
    # Chuva: filtros simulando água caindo em folhas
    "[2:a]highpass=f=150,lowpass=f=3500,volume=0.04[rain];"
    "[bin][rain]amix=inputs=2:duration=longest:normalize=0[out]",
    "-map","[out]","-c:a","aac","-b:a","160k","-ar","44100", str(bed)],
    capture_output=True, timeout=120)
print(f"   ✅ {bed.stat().st_size//1024} KB\n")

uploaded = []
for lang, text in SAMPLES.items():
    voice = VOICES[lang]
    print(f"🎙️  {lang} ({voice})")
    speech = OUT / f"speech_{lang.lower()}.mp3"
    asyncio.run(gen_tts_warm(text, voice, speech))
    
    # Mesclar com cama + fade in/out suave
    final = OUT / f"sample_{lang.lower()}.mp3"
    subprocess.run(["ffmpeg","-y",
        "-i", str(speech),
        "-stream_loop","-1","-i", str(bed),
        "-filter_complex",
        "[0:a]volume=1.0,afade=t=in:d=3,afade=t=out:st=999:d=3[s];"
        "[1:a]volume=0.30[a];"
        "[s][a]amix=inputs=2:duration=first[out]",
        "-map","[out]","-c:a","libmp3lame","-b:a","192k","-ar","44100", str(final)],
        capture_output=True, timeout=60)
    
    if final.exists():
        print(f"   ✅ {final.stat().st_size//1024} KB")
        if SUPABASE_KEY:
            with open(final, "rb") as f:
                r = requests.post(
                    f"{SUPABASE_URL}/storage/v1/object/samples/sample_{lang.lower()}_v2.mp3",
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "audio/mpeg",
                        "x-upsert": "true"
                    }, data=f.read()
                )
                if r.status_code in (200, 201):
                    url = f"{SUPABASE_URL}/storage/v1/object/public/samples/sample_{lang.lower()}_v2.mp3"
                    uploaded.append((lang, url))
                    print(f"   🌐 {url}")
                else:
                    print(f"   ⚠️  {r.status_code}: {r.text[:120]}")

print(f"\n✨ {len(uploaded)} amostras V2 prontas\n")
for lang, u in uploaded: print(f"   {lang}: {u}")
