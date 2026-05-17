#!/usr/bin/env python3
"""
test_voices.py — Testar e comparar qualidade de vozes TTS
George (ElevenLabs) vs AntonioNeural (edge_tts)
"""
import os, subprocess, json, asyncio, requests

SB_URL = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY = os.environ.get("SUPABASE_SERVICE_KEY","")
XI_KEY = os.environ.get("ELEVENLABS_API_KEY","")

WORKDIR = "/tmp/voice_test"
os.makedirs(WORKDIR, exist_ok=True)

def log(m): print(m, flush=True)

# Texto de teste — trecho típico do canal
TEST_TEXT = (
    "Você já ficou olhando pro celular esperando uma mensagem que não veio? "
    "E quando ela chegou, foi só uma desculpa vazia. "
    "Daniela pergunta: isso acontece com você? "
    "Narcisismo encoberto. Os sinais são sutis e quase impossíveis de ver de dentro. "
    "Sinal 1: ele nunca assume os erros. Nunca. Nem os absolutamente óbvios. "
    "Pesquisas de Harvard mostram que narcisistas culpam outros em 94% dos conflitos. "
    "Dra. Ana explica: sob manipulação crônica, o cérebro começa a duvidar da própria memória. "
    "Seus sentimentos são válidos. Sua dor é completamente real."
)

log(f"{'='*55}")
log(f"  🎤 TESTE DE VOZES — psicologia.doc")
log(f"  {len(TEST_TEXT)} chars de texto de teste")
log(f"{'='*55}\n")

# ── VOICE 1: ElevenLabs George ────────────────────────────
def test_george():
    if not XI_KEY:
        log("❌ ELEVENLABS_API_KEY não configurado")
        return None
    
    # Verificar vozes disponíveis e encontrar George
    r = requests.get("https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": XI_KEY}, timeout=15)
    
    if r.status_code != 200:
        log(f"❌ ElevenLabs API erro {r.status_code}")
        return None
    
    voices = r.json().get("voices",[])
    log(f"✅ ElevenLabs API OK | {len(voices)} vozes")
    
    # Buscar George
    george = next((v for v in voices if "george" in v.get("name","").lower()), None)
    
    if not george:
        # Tentar com ID fixo
        george = {"voice_id": "JBFqnCBsd6RMkjVDRZzb", "name": "George"}
        log(f"  George não encontrado nas vozes — usando ID fixo")
    
    log(f"  Usando voz: {george['name']} ({george['voice_id']})")
    
    # Verificar conta
    sub_r = requests.get("https://api.elevenlabs.io/v1/user/subscription",
        headers={"xi-api-key": XI_KEY}, timeout=10)
    if sub_r.status_code == 200:
        sub = sub_r.json()
        used = sub.get("character_count",0)
        limit = sub.get("character_limit",0)
        log(f"  Conta: {used}/{limit} chars ({limit-used} restantes)")
    
    # Gerar áudio
    log(f"\n  Gerando áudio George ({len(TEST_TEXT)} chars)...")
    r2 = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{george['voice_id']}",
        headers={"xi-api-key": XI_KEY, "Content-Type": "application/json"},
        json={
            "text": TEST_TEXT,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.50,
                "similarity_boost": 0.85,
                "style": 0.35,
                "use_speaker_boost": True,
                "speed": 1.0
            }
        },
        timeout=120
    )
    
    if r2.status_code == 200:
        path = f"{WORKDIR}/george_test.mp3"
        with open(path,'wb') as f: f.write(r2.content)
        # Medir duração
        probe = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",path],
            capture_output=True,text=True)
        dur = float(json.loads(probe.stdout)["format"]["duration"])
        sz = len(r2.content)//1024
        log(f"  ✅ George: {dur:.1f}s | {sz}KB")
        return path, dur, sz
    else:
        log(f"  ❌ Erro {r2.status_code}: {r2.text[:200]}")
        return None

# ── VOICE 2: AntonioNeural (correto — sem ponto duplo) ───
async def test_antonio():
    import edge_tts
    path = f"{WORKDIR}/antonio_test.mp3"
    # FIX: sem ". " para evitar pausa dupla
    c = edge_tts.Communicate(TEST_TEXT, voice="pt-BR-AntonioNeural", rate="+37%")
    await c.save(path)
    probe = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",path],
        capture_output=True,text=True)
    dur = float(json.loads(probe.stdout)["format"]["duration"])
    sz = os.path.getsize(path)//1024
    log(f"  ✅ AntonioNeural: {dur:.1f}s | {sz}KB")
    return path, dur, sz

# ── VOICE 3: ThalitaMultilingual (melhor voz MS PT-BR) ──
async def test_thalita():
    import edge_tts
    path = f"{WORKDIR}/thalita_test.mp3"
    c = edge_tts.Communicate(TEST_TEXT, voice="pt-BR-ThalitaMultilingualNeural", rate="+37%")
    await c.save(path)
    probe = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",path],
        capture_output=True,text=True)
    dur = float(json.loads(probe.stdout)["format"]["duration"])
    sz = os.path.getsize(path)//1024
    log(f"  ✅ ThalitaMultilingual: {dur:.1f}s | {sz}KB")
    return path, dur, sz

# Executar testes
log("🎤 VOICE 1: ElevenLabs George")
george_result = test_george()

log("\n🎤 VOICE 2: AntonioNeural (edge_tts, corrigido)")
antonio_result = asyncio.run(test_antonio())

log("\n🎤 VOICE 3: ThalitaMultilingual (edge_tts)")
thalita_result = asyncio.run(test_thalita())

# Resultado
log(f"\n{'='*55}")
log("  COMPARATIVO FINAL")
log(f"{'='*55}")

results = [
    ("George (ElevenLabs)", george_result),
    ("AntonioNeural", antonio_result),
    ("ThalitaMultilingual", thalita_result),
]

for name, res in results:
    if res:
        path, dur, sz = res if len(res)==3 else (res,0,0)
        log(f"  {name:25}: {dur:.1f}s | {sz}KB | {path}")
    else:
        log(f"  {name:25}: FALHOU")

# Upload dos áudios para Supabase
log("\n☁️  Upload dos áudios de teste...")
for name, res in results:
    if res and len(res)==3:
        path, dur, sz = res
        fname = os.path.basename(path)
        with open(path,'rb') as f: data=f.read()
        r = requests.post(f"{SB_URL}/storage/v1/object/videos/voice_tests/{fname}",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                     "Content-Type":"audio/mpeg","x-upsert":"true"},
            data=data, timeout=60)
        if r.status_code in (200,201):
            url = f"{SB_URL}/storage/v1/object/public/videos/voice_tests/{fname}"
            log(f"  ✅ {name}: {url}")
        else:
            log(f"  ❌ Upload {name}: {r.status_code}")
