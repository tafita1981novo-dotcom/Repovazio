"""
piper_clone.py — Piper TTS, vozes masculinas pré-treinadas profissionais
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VANTAGEM vs Coqui XTTS:
  - 60MB por voz vs 1800MB do XTTS (30x mais leve)
  - 100ms latência vs 1-3min XTTS
  - MIT license total uso comercial
  - Sem dependência GPU
  - Qualidade comparável para vozes pré-treinadas

VOZES MASCULINAS GRAVES SELECIONADAS:
  EN: en_GB-alan-medium       — britânico calmo (estilo Sleep Cove)
  PT: pt_BR-faber-medium      — brasileiro grave (estilo Pedro Engler)  
  ES: es_ES-davefx-medium     — espanhol calmo (estilo Alan Disavia)

NOTA: Piper não suporta Japonês. JA fica para Coqui XTTS ou outro engine.
"""
import os, requests, subprocess, pathlib, time

OUT = pathlib.Path("/tmp/piper_out"); OUT.mkdir(exist_ok=True)
SUPABASE_URL = "https://tpjvalzwkqwttvmszvie.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

VOICES_HF = {
    # nome: (path_no_HF, descrição)
    "pt": "pt/pt_BR/faber/medium/pt_BR-faber-medium",
    "en": "en/en_GB/alan/medium/en_GB-alan-medium",
    "es": "es/es_ES/davefx/medium/es_ES-davefx-medium",
}

print("📥 Baixando 3 vozes Piper (~60MB cada)...")
voice_files = {}
for lang, path in VOICES_HF.items():
    onnx_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{path}.onnx"
    json_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{path}.onnx.json"
    
    onnx_file = OUT / f"{lang}.onnx"
    json_file = OUT / f"{lang}.onnx.json"
    
    if not onnx_file.exists():
        r = requests.get(onnx_url, stream=True, timeout=120)
        if r.status_code == 200:
            with open(onnx_file, "wb") as f:
                for chunk in r.iter_content(chunk_size=131072):
                    f.write(chunk)
            print(f"   ✅ {lang} ONNX: {onnx_file.stat().st_size//1024//1024} MB")
        else:
            print(f"   ❌ {lang} ONNX: {r.status_code}")
            continue
    
    if not json_file.exists():
        r2 = requests.get(json_url, timeout=30)
        json_file.write_bytes(r2.content)
    
    voice_files[lang] = (onnx_file, json_file)

# Importar Piper (instalado via pip)
print("\n🧠 Carregando Piper...")
from piper import PiperVoice
from piper.config import SynthesisConfig
import wave

# Textos para sleep induction
SAMPLES = {
    "pt": "Feche os olhos. Respire fundo. Deixe o ar entrar. E sair. Naturalmente. Cada respiração te leva mais fundo. Seus pés relaxam. Suas pernas pesam. Seu peito se solta. Não há nada que você precise fazer agora.",
    "en": "Close your eyes. Breathe deeply. Let the air enter. And leave. Naturally. Each breath takes you deeper. Your feet relax. Your legs grow heavy. Your chest softens. There is nothing you need to do now.",
    "es": "Cierra los ojos. Respira profundo. Deja entrar el aire. Y salir. Naturalmente. Cada respiración te lleva más profundo. Tus pies se relajan. Tus piernas pesan. Tu pecho se suelta. No hay nada que necesites hacer ahora.",
}

# Cama ambiente (binaural + brown noise rain)
print("🎵 Cama ambiente brown noise...")
bed = OUT / "bed.aac"
subprocess.run(["ffmpeg","-y",
    "-f","lavfi","-i","sine=frequency=528:duration=90",
    "-f","lavfi","-i","sine=frequency=532:duration=90",
    "-f","lavfi","-i","anoisesrc=color=brown:duration=90",
    "-filter_complex",
    "[0:a]volume=0.04[l];[1:a]volume=0.04[r];"
    "[l][r]amerge=inputs=2[bin];"
    "[2:a]highpass=f=150,lowpass=f=3500,volume=0.05[rain];"
    "[bin][rain]amix=inputs=2:duration=longest:normalize=0[out]",
    "-map","[out]","-c:a","aac","-b:a","160k","-ar","44100", str(bed)],
    capture_output=True, timeout=120)

uploaded = []
for lang, text in SAMPLES.items():
    if lang not in voice_files: continue
    onnx_file, _ = voice_files[lang]
    
    t0 = time.time()
    print(f"\n🎙️  {lang} — gerando com Piper...")
    
    voice = PiperVoice.load(str(onnx_file))
    
    # SynthesisConfig com slow-down para sleep (length_scale > 1 = mais lento)
    syn_config = SynthesisConfig(
        length_scale=1.4,       # 40% mais lento = hipnótico
        noise_scale=0.667,      # variação natural
        noise_w_scale=0.8       # variação cadência
    )
    
    # Gera WAV (synthesize_wav escreve direto no Wave_write object)
    raw_wav = OUT / f"raw_{lang}.wav"
    with wave.open(str(raw_wav), "wb") as wf:
        voice.synthesize_wav(text, wf, syn_config=syn_config)
    
    dt = time.time() - t0
    print(f"   ⏱️  Gerado em {dt:.1f}s | {raw_wav.stat().st_size//1024} KB")
    
    # Pós-processamento estúdio + mescla com cama
    final = OUT / f"sample_{lang}_piper.mp3"
    subprocess.run(["ffmpeg","-y",
        "-i", str(raw_wav),
        "-stream_loop","-1","-i", str(bed),
        "-filter_complex",
        # Voz: EQ + compressor + reverb
        "[0:a]asetrate=22050*0.97,aresample=44100,"
        "equalizer=f=180:width_type=h:width=80:g=2,"
        "lowpass=f=9000,"
        "acompressor=threshold=0.1:ratio=3:attack=10:release=200:makeup=2,"
        "aecho=0.6:0.5:60:0.25,"
        "loudnorm=I=-18:LRA=8:TP=-2,"
        "volume=1.0,afade=t=in:d=2,afade=t=out:st=999:d=3[s];"
        # Cama
        "[1:a]volume=0.28[a];"
        "[s][a]amix=inputs=2:duration=first[out]",
        "-map","[out]","-c:a","libmp3lame","-b:a","192k","-ar","44100", str(final)],
        capture_output=True, timeout=60)
    
    if final.exists() and SUPABASE_KEY:
        with open(final, "rb") as f:
            r = requests.post(
                f"{SUPABASE_URL}/storage/v1/object/samples/sample_{lang}_piper.mp3",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "audio/mpeg",
                    "x-upsert": "true"
                }, data=f.read()
            )
            if r.status_code in (200, 201):
                url = f"{SUPABASE_URL}/storage/v1/object/public/samples/sample_{lang}_piper.mp3"
                uploaded.append((lang, url))
                print(f"   🌐 {url}")

# Espaço usado
import shutil
total, used, free = shutil.disk_usage(OUT)
print(f"\n📊 Espaço usado em /tmp/piper_out: {sum(f.stat().st_size for f in OUT.iterdir())//1024//1024} MB")
print(f"📊 Disco GitHub Actions: {free//(1024**3)} GB livres de {total//(1024**3)} GB")

print(f"\n✨ {len(uploaded)} samples Piper prontas:")
for lang, u in uploaded: print(f"   {lang}: {u}")
