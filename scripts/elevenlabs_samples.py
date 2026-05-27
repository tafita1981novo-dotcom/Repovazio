"""
elevenlabs_samples.py — ElevenLabs Multilingual v2 + voz MASCULINA Daniel/George
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ESTRATÉGIA:
  1. Voz Daniel (British male) — IDÊNTICA ao estilo Sleep Cove (Chris)
  2. Modelo eleven_multilingual_v2 — UMA voz, 29 idiomas
  3. Settings hipnose: stability 0.85 + similarity 0.95 + style 0.20
  4. Texto com pontuação que cria pausas naturais (sem reticências artificiais)
  5. Mescla com binaural 528Hz + chuva brown noise

CONSUMO: ~150 chars × 4 idiomas = 600 chars do mensal (32K disponíveis)
"""
import os, requests, subprocess, pathlib

OUT = pathlib.Path("/tmp/elevenlabs_samples"); OUT.mkdir(exist_ok=True)
ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY")
SUPABASE_URL = "https://tpjvalzwkqwttvmszvie.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Voz Daniel — britânico grave, estilo Sleep Cove (#1 global sleep podcast)
VOICE_ID = "onwK4e9ZLuTAKqWW03F9"  # Daniel — British male, deep, calm

# Texto curto, pontuação natural cria pausas (ElevenLabs respeita pontuação melhor que Edge)
SAMPLES = {
"PT": "Feche os olhos. Respire fundo. Deixe o ar entrar. E sair. Cada respiração te leva mais fundo. Seus pés relaxam. Suas pernas pesam. Seu peito se solta. Não há nada que você precise fazer agora.",
"EN": "Close your eyes. Breathe deeply. Let the air enter. And leave. Each breath takes you deeper. Your feet relax. Your legs grow heavy. Your chest softens. There is nothing you need to do now.",
"ES": "Cierra los ojos. Respira profundo. Deja entrar el aire. Y salir. Cada respiración te lleva más profundo. Tus pies se relajan. Tus piernas pesan. Tu pecho se suelta. No hay nada que necesites hacer ahora.",
"JA": "目を閉じてください。深く息を吸ってください。空気を入れて。そして出して。一呼吸ごとに、もっと深くへ。足が緩み。脚が重くなり。胸が柔らかくなります。今、何もする必要はありません。",
}

print("🔑 Testando ElevenLabs API key...")
r = requests.get("https://api.elevenlabs.io/v1/user", 
                 headers={"xi-api-key": ELEVEN_KEY}, timeout=10)
if r.status_code != 200:
    print(f"❌ Key inválida ou bloqueada: {r.status_code} — {r.text[:200]}")
    exit(1)
user = r.json()
remaining = user.get("subscription",{}).get("character_count", 0)
limit = user.get("subscription",{}).get("character_limit", 0)
print(f"✅ Conectado. Usados: {remaining}/{limit} chars este mês")
print(f"   Tier: {user.get('subscription',{}).get('tier','?')}\n")

# Gerar cama (binaural + chuva brown)
print("🎵 Cama ambiente brown noise...")
bed = OUT / "bed.aac"
subprocess.run(["ffmpeg","-y",
    "-f","lavfi","-i","sine=frequency=528:duration=60",
    "-f","lavfi","-i","sine=frequency=532:duration=60",
    "-f","lavfi","-i","anoisesrc=color=brown:duration=60",
    "-filter_complex",
    "[0:a]volume=0.04[l];[1:a]volume=0.04[r];"
    "[l][r]amerge=inputs=2[bin];"
    "[2:a]highpass=f=150,lowpass=f=3500,volume=0.05[rain];"
    "[bin][rain]amix=inputs=2:duration=longest:normalize=0[out]",
    "-map","[out]","-c:a","aac","-b:a","160k","-ar","44100", str(bed)],
    capture_output=True, timeout=120)

uploaded = []
for lang, text in SAMPLES.items():
    print(f"🎙️  {lang} ({len(text)} chars) — gerando com Daniel...")
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
        headers={
            "xi-api-key": ELEVEN_KEY,
            "Content-Type": "application/json"
        },
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.85,           # alta = consistente, calmo
                "similarity_boost": 0.95,    # mantém voz Daniel
                "style": 0.20,               # baixo = sem dramatização
                "use_speaker_boost": True
            }
        },
        timeout=60
    )
    
    if r.status_code != 200:
        print(f"   ❌ {r.status_code}: {r.text[:200]}")
        continue
    
    speech_mp3 = OUT / f"speech_{lang.lower()}.mp3"
    speech_mp3.write_bytes(r.content)
    print(f"   ✅ Speech: {speech_mp3.stat().st_size//1024} KB")
    
    # Mesclar com cama
    final = OUT / f"sample_{lang.lower()}_eleven.mp3"
    subprocess.run(["ffmpeg","-y",
        "-i", str(speech_mp3),
        "-stream_loop","-1","-i", str(bed),
        "-filter_complex",
        "[0:a]volume=1.0,afade=t=in:d=2,afade=t=out:st=999:d=3[s];"
        "[1:a]volume=0.28[a];"
        "[s][a]amix=inputs=2:duration=first[out]",
        "-map","[out]","-c:a","libmp3lame","-b:a","192k","-ar","44100", str(final)],
        capture_output=True, timeout=60)
    
    if final.exists() and SUPABASE_KEY:
        with open(final, "rb") as f:
            up = requests.post(
                f"{SUPABASE_URL}/storage/v1/object/samples/sample_{lang.lower()}_eleven.mp3",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "audio/mpeg",
                    "x-upsert": "true"
                }, data=f.read()
            )
            if up.status_code in (200, 201):
                url = f"{SUPABASE_URL}/storage/v1/object/public/samples/sample_{lang.lower()}_eleven.mp3"
                uploaded.append((lang, url))
                print(f"   🌐 {url}")
            else:
                print(f"   ⚠️ Upload: {up.status_code}")

# Verificar quanto consumiu
r2 = requests.get("https://api.elevenlabs.io/v1/user", headers={"xi-api-key": ELEVEN_KEY})
if r2.status_code == 200:
    after = r2.json().get("subscription",{}).get("character_count", 0)
    print(f"\n📊 Chars consumidos nesta sessão: {after - remaining}")
    print(f"📊 Restante este mês: {limit - after} chars")

print(f"\n✨ {len(uploaded)} amostras ElevenLabs prontas:")
for lang, u in uploaded: print(f"   {lang}: {u}")
