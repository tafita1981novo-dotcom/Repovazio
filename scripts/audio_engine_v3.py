"""
audio_engine_v3.py — Piper TTS + presets emocionais por frase
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ESTRATÉGIA POR FRASE (anti-robotização):
  Cada frase é sintetizada SEPARADAMENTE com SynthesisConfig próprio
  Detecta tipo emocional → escolhe length_scale + noise + pausa
  Concatena com silêncios contextuais variáveis (não fixos)

3 PRESETS:
  live_sleep  → length 1.6-1.95 | pausas 2-4s | tom contemplativo grave
  shorts_hook → length 1.0-1.3  | pausas 0.3-1s | tom revelação chocante
  long_video  → length 1.2-1.5  | pausas 1-2s   | tom professor calmo

CLASSIFICAÇÃO EMOCIONAL POR FRASE:
  Comando        ("Feche os olhos") → mais lento, grave
  Estado         ("Seus pés relaxam") → médio
  Revelação      ("Não há nada que precise...") → lentíssimo
  Citação        ("Van der Kolk descobriu...") → médio, autoritário
  Encerramento   ("...apenas respirar") → silêncio longo após
"""
import os, requests, subprocess, pathlib, time, wave, re

OUT = pathlib.Path("/tmp/v3_out"); OUT.mkdir(exist_ok=True)
SUPABASE_URL = "https://tpjvalzwkqwttvmszvie.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
PRESET = os.getenv("PRESET", "live_sleep")

VOICES_HF = {
    "pt": "pt/pt_BR/faber/medium/pt_BR-faber-medium",
    "en": "en/en_GB/alan/medium/en_GB-alan-medium",
    "es": "es/es_ES/davefx/medium/es_ES-davefx-medium",
}

# ════════════════════════════════════════════════════════════════════════════
# CLASSIFICADOR EMOCIONAL POR FRASE (heurístico, multi-idioma)
# ════════════════════════════════════════════════════════════════════════════
COMMANDS = {  # verbos no imperativo = comandos suaves
    "pt": ["feche", "respire", "deixe", "permita", "sinta", "observe", "perceba"],
    "en": ["close", "breathe", "let", "allow", "feel", "observe", "notice"],
    "es": ["cierra", "respira", "deja", "permite", "siente", "observa", "percibe"],
}
STATES = {  # verbos descritivos = estados corporais
    "pt": ["relaxam", "pesam", "descem", "se solta", "afunda", "amolece"],
    "en": ["relax", "grow heavy", "drop", "soften", "sink", "deepen"],
    "es": ["se relajan", "pesan", "bajan", "se suelta", "se hunde", "ablanda"],
}
REVELATIONS = {  # frases de profundidade existencial
    "pt": ["não há nada", "você não precisa", "apenas", "naturalmente", "só ser"],
    "en": ["there is nothing", "you don't need", "only", "naturally", "just being"],
    "es": ["no hay nada", "no necesitas", "solo", "naturalmente", "solo ser"],
}

def classify_phrase(text, lang):
    """Retorna tipo emocional: command|state|revelation|citation|neutral"""
    t = text.lower().strip(". !?")
    # Citação científica
    if any(name in t.lower() for name in ["van der kolk","ainsworth","malkin","sapolsky","busemeyer","pothos","raichle","chartrand","skinner","stern","williams","freedman","bowen"]):
        return "citation"
    # Revelação existencial (procura padrões em qualquer idioma)
    for pattern in REVELATIONS.get(lang, []):
        if pattern in t: return "revelation"
    # Comando
    first_word = t.split()[0] if t.split() else ""
    if first_word in COMMANDS.get(lang, []): return "command"
    # Estado corporal
    for pattern in STATES.get(lang, []):
        if pattern in t: return "state"
    return "neutral"

# ════════════════════════════════════════════════════════════════════════════
# CONFIGS DE SÍNTESE POR PRESET + TIPO EMOCIONAL
# (length_scale, noise_scale, noise_w_scale, pause_after_seconds)
# ════════════════════════════════════════════════════════════════════════════
PRESETS = {
"live_sleep": {  # LIVE BLACK SCREEN — máximo hipnótico
    "command":    (1.95, 0.50, 0.55, 2.5),   # mais lento ainda
    "state":      (1.75, 0.55, 0.65, 1.8),
    "revelation": (1.90, 0.45, 0.55, 3.5),   # silêncio longo após
    "citation":   (1.60, 0.60, 0.70, 1.5),
    "neutral":    (1.70, 0.55, 0.65, 1.8),
    "closing":    (1.95, 0.45, 0.50, 4.0),   # última frase do bloco
},
"shorts_hook": {  # SHORTS VIRAIS — impactante
    "command":    (1.20, 0.70, 0.80, 0.4),
    "state":      (1.15, 0.70, 0.80, 0.5),
    "revelation": (1.30, 0.65, 0.75, 1.2),   # punchline = pausa
    "citation":   (1.05, 0.75, 0.85, 0.4),
    "neutral":    (1.10, 0.70, 0.80, 0.5),
    "closing":    (1.35, 0.65, 0.75, 1.5),
},
"long_video": {  # LONG FORM — professor calmo
    "command":    (1.45, 0.60, 0.70, 1.2),
    "state":      (1.30, 0.62, 0.72, 1.0),
    "revelation": (1.50, 0.55, 0.65, 2.0),
    "citation":   (1.25, 0.65, 0.75, 1.2),
    "neutral":    (1.35, 0.62, 0.72, 1.0),
    "closing":    (1.50, 0.55, 0.65, 2.5),
},
}

# ════════════════════════════════════════════════════════════════════════════
# TEXTOS DE EXEMPLO (mesma indução, 3 idiomas)
# ════════════════════════════════════════════════════════════════════════════
SAMPLES = {
"pt": [
    "Feche os olhos.",
    "Respire fundo.",
    "Deixe o ar entrar.",
    "E sair.",
    "Naturalmente.",
    "Cada respiração te leva mais fundo.",
    "Seus pés relaxam.",
    "Suas pernas pesam.",
    "Seu peito se solta.",
    "Seus ombros descem.",
    "Não há nada que você precise fazer agora.",
    "Apenas respirar.",
],
"en": [
    "Close your eyes.",
    "Breathe deeply.",
    "Let the air enter.",
    "And leave.",
    "Naturally.",
    "Each breath takes you deeper.",
    "Your feet relax.",
    "Your legs grow heavy.",
    "Your chest softens.",
    "Your shoulders drop.",
    "There is nothing you need to do now.",
    "Only breathing.",
],
"es": [
    "Cierra los ojos.",
    "Respira profundo.",
    "Deja entrar el aire.",
    "Y salir.",
    "Naturalmente.",
    "Cada respiración te lleva más profundo.",
    "Tus pies se relajan.",
    "Tus piernas pesan.",
    "Tu pecho se suelta.",
    "Tus hombros bajan.",
    "No hay nada que necesites hacer ahora.",
    "Solo respirar.",
],
}

# Baixar vozes Piper
print(f"📥 Vozes Piper + preset: {PRESET}")
voice_files = {}
for lang, path in VOICES_HF.items():
    onnx_file = OUT / f"{lang}.onnx"
    json_file = OUT / f"{lang}.onnx.json"
    if not onnx_file.exists():
        r = requests.get(f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{path}.onnx", stream=True, timeout=120)
        if r.status_code == 200:
            with open(onnx_file, "wb") as f:
                for chunk in r.iter_content(chunk_size=131072): f.write(chunk)
        r2 = requests.get(f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{path}.onnx.json", timeout=30)
        json_file.write_bytes(r2.content)
    voice_files[lang] = onnx_file
    print(f"   ✅ {lang}")

# Cama ambiente brown noise
print("🎵 Cama brown noise...")
bed = OUT / "bed.aac"
subprocess.run(["ffmpeg","-y",
    "-f","lavfi","-i","sine=frequency=528:duration=120",
    "-f","lavfi","-i","sine=frequency=532:duration=120",
    "-f","lavfi","-i","anoisesrc=color=brown:duration=120",
    "-filter_complex",
    "[0:a]volume=0.04[l];[1:a]volume=0.04[r];"
    "[l][r]amerge=inputs=2[bin];"
    "[2:a]highpass=f=150,lowpass=f=3500,volume=0.05[rain];"
    "[bin][rain]amix=inputs=2:duration=longest:normalize=0[out]",
    "-map","[out]","-c:a","aac","-b:a","160k","-ar","44100", str(bed)],
    capture_output=True, timeout=120)

# Importar Piper
from piper import PiperVoice
from piper.config import SynthesisConfig

def make_silence(seconds, out_wav):
    """Silêncio mono 22050Hz (formato Piper)"""
    subprocess.run(["ffmpeg","-y",
        "-f","lavfi","-i","anullsrc=r=22050:cl=mono",
        "-t", str(seconds),
        "-c:a","pcm_s16le", str(out_wav)],
        capture_output=True, timeout=15)

uploaded = []
preset = PRESETS[PRESET]

for lang, phrases in SAMPLES.items():
    if lang not in voice_files: continue
    print(f"\n🎙️  {lang} — sintetizando {len(phrases)} frases (preset={PRESET})")
    
    voice = PiperVoice.load(str(voice_files[lang]))
    parts = []
    
    for i, phrase in enumerate(phrases):
        # Classificar emoção
        is_last = (i == len(phrases) - 1)
        emotion = "closing" if is_last else classify_phrase(phrase, lang)
        length, noise, noise_w, pause = preset[emotion]
        
        # Sintetizar com config específico desta frase
        cfg = SynthesisConfig(
            length_scale=length,
            noise_scale=noise,
            noise_w_scale=noise_w
        )
        phrase_wav = OUT / f"{lang}_{i:02d}.wav"
        with wave.open(str(phrase_wav), "wb") as wf:
            voice.synthesize_wav(phrase, wf, syn_config=cfg)
        parts.append(phrase_wav)
        
        # Silêncio depois (variável por contexto)
        silence_wav = OUT / f"{lang}_{i:02d}_sil.wav"
        make_silence(pause, silence_wav)
        parts.append(silence_wav)
        
        print(f"   {i+1:2d}. [{emotion:10}] len={length} pausa={pause}s  \"{phrase[:40]}\"")
    
    # Concatenar todas as frases + silêncios
    concat_list = OUT / f"{lang}_list.txt"
    with open(concat_list, "w") as f:
        for p in parts:
            if p.exists():
                f.write(f"file '{p.resolve()}'\n")
    
    concat_wav = OUT / f"{lang}_full.wav"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat_list),
                    "-c:a","pcm_s16le", str(concat_wav)],
                   capture_output=True, timeout=60)
    
    # Pós-processamento estúdio + mescla com cama
    final = OUT / f"sample_{lang}_{PRESET}.mp3"
    subprocess.run(["ffmpeg","-y",
        "-i", str(concat_wav),
        "-stream_loop","-1","-i", str(bed),
        "-filter_complex",
        # Pitch -3%, EQ corpo, compressor, reverb sutil
        "[0:a]aresample=44100,"
        "asetrate=44100*0.97,aresample=44100,"
        "equalizer=f=180:width_type=h:width=80:g=2,"
        "lowpass=f=9000,"
        "acompressor=threshold=0.1:ratio=3:attack=10:release=200:makeup=2,"
        "aecho=0.6:0.5:60:0.20,"
        "loudnorm=I=-18:LRA=8:TP=-2,"
        "volume=1.0,afade=t=in:d=3,afade=t=out:st=999:d=4[s];"
        "[1:a]volume=0.28[a];"
        "[s][a]amix=inputs=2:duration=first[out]",
        "-map","[out]","-c:a","libmp3lame","-b:a","192k","-ar","44100", str(final)],
        capture_output=True, timeout=90)
    
    if final.exists():
        total_dur = sum(preset[classify_phrase(p, lang)][0]*2 + preset[classify_phrase(p, lang)][3] for p in phrases)
        print(f"   ✅ {final.stat().st_size//1024} KB | ~{int(total_dur)}s")
        
        if SUPABASE_KEY:
            with open(final, "rb") as f:
                r = requests.post(
                    f"{SUPABASE_URL}/storage/v1/object/samples/sample_{lang}_{PRESET}.mp3",
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "audio/mpeg",
                        "x-upsert": "true"
                    }, data=f.read()
                )
                if r.status_code in (200, 201):
                    url = f"{SUPABASE_URL}/storage/v1/object/public/samples/sample_{lang}_{PRESET}.mp3"
                    uploaded.append((lang, url))
                    print(f"   🌐 {url}")

print(f"\n✨ {len(uploaded)} samples preset={PRESET} prontas:")
for lang, u in uploaded: print(f"   {lang}: {u}")
