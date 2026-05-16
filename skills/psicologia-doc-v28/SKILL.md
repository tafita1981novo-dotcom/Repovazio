---
name: psicologia-doc-v28
description: Use esta SKILL sempre que o usuário mencionar: psicologia.doc, repovazio, Daniela Coelho, @psidanielacoelho, canal YouTube psicologia, narcisismo, apego ansioso, trauma, viral, cérebro autônomo, tokens sociais, Instagram, TikTok, WhatsApp grupos, monetização, 1000 subs, crescimento, setup tokens, espelhamento viral, render video, vídeo animado, gemini image, animação chibi, veo, voz george, render V8.
version: 28.1
date: 2026-05-15
---

# SKILL — psicologia.doc V28.1 (15/mai/2026)

## INFRA
- Supabase: `tpjvalzwkqwttvmszvie` | GitHub: `tafita81/Repovazio` | Vercel: `repovazio.vercel.app`
- Canal ATIVO: `UCyCkIpsVgME9yCj_oXJFheA` @psidanielacoelho
- Canal BLOQUEADO: `UCSH63tBfY6wEIdkC4u4zKdg` — NUNCA publicar

## RENDER V8 — PADRÃO DEFINITIVO ($0/MÊS)

### O que é
- **Imagens AI Chibi** via Gemini 2.5 Flash Image (PRIMARY) ou Gemini 3 Pro Image (PREMIUM)
- **21 cenas** sincronizadas frase a frase via ffconcat (12.77 chars/s)
- **Voz George** (Edge TTS pt-BR-AntonioNeural) — padrão absoluto
- **Lower third**: "Daniela Coelho | Saude Mental | @psidanielacoelho"
- **Caption badge** no topo de cada cena
- **Custo: $0**

### Por que NÃO é plágio do Psych2Go
1. Skin tone brasileiro (bege-acastanhado, não branco)
2. Lower third exclusivo + marca própria
3. Caption badges (elemento exclusivo)
4. Timing dinâmico por frase (vs blocos fixos)
5. Voz masculina (Psych2Go usa feminino)
6. 21 cenas narrativas estruturadas

## STYLE BIBLE V8

### Personagem RENATA (FEMININO — SEMPRE)
```
chibi anime girl, short brown hair bob cut, warm beige brazilian skin tone, pink blouse, 
large expressive brown eyes, rosy cheeks, kawaii flat design illustration, 
psychology animation style, vertical 9:16 portrait, clean line art, 
soft warm cream white background with pastel decorations, no text
```

### Personagem LUCAS (MASCULINO — antagonista)
```
chibi anime boy, slick dark hair, light skin, navy blue shirt, charming confident smile, 
large eyes, kawaii flat design, psychology animation style, 9:16 portrait, no text
```

### Paleta por cena
- Hook/Surpresa: creme quente #FFF8F0 + azul pastel
- Sinal/Perigo: vermelho vinho suave + dourado
- Científico: verde-teal + branco
- CTA/Celebração: dourado âmbar + arco-iris
- Amor/Cura: verde-esmeralda suave + rosa

## GEMINI API — IMAGENS GRÁTIS (CONFIRMADO)

### Modelos
| Modelo | Velocidade | Qualidade |
|--------|-----------|-----------|
| `gemini-2.5-flash-image` | 5.5s/img | ⭐⭐⭐⭐ PRIMARY |
| `gemini-3-pro-image-preview` | 15s/img | ⭐⭐⭐⭐⭐ PREMIUM |
| `gemini-3.1-flash-image-preview` | 13s/img | ⭐⭐⭐⭐⭐ PREMIUM |

### Chaves
- KEY1: `AIzaSyDzCea_65Al-vy342xslBSVmKPv0qzTuXY`
- KEY2: `AIzaSyCo-YEPjEw3KaOllUIpJKpVwdDZA-Mr5xg`

### Call
```python
import requests, base64

def gemini_image(prompt, model="gemini-2.5-flash-image"):
    KEY = "AIzaSyDzCea_65Al-vy342xslBSVmKPv0qzTuXY"
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={KEY}",
        json={"contents":[{"parts":[{"text":prompt}]}],
              "generationConfig":{"responseModalities":["IMAGE","TEXT"]}},
        timeout=60
    )
    for cand in r.json().get("candidates",[]):
        for part in cand.get("content",{}).get("parts",[]):
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])

# Paralelo 4 workers = 21 imgs em ~35s
from concurrent.futures import ThreadPoolExecutor, as_completed
with ThreadPoolExecutor(max_workers=4) as ex:
    futures = {ex.submit(gemini_image, prompt): i for i, prompt in enumerate(prompts)}
```

## TIMING FFCONCAT

```python
CHARS_PER_SEC = 12.77  # George calibrado no #683

def dur_frase(frase):
    return max(0.8, len(frase) / CHARS_PER_SEC)

# Criar concat.txt
with open("concat.txt", "w") as f:
    for img_path, frase in zip(imgs, frases):
        f.write(f"file '{img_path}
duration {dur_frase(frase):.3f}
")
    f.write(f"file '{imgs[-1]}'
")  # último sem dur

# Render
subprocess.run(["ffmpeg","-y",
    "-f","concat","-safe","0","-i","concat.txt",
    "-i","audio.mp3",
    "-c:v","libx264","-pix_fmt","yuv420p",
    "-c:a","aac","-b:a","128k",
    "-t","58","-r","25","-crf","18",
    "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1",
    "-movflags","+faststart","output.mp4"
])
```

## OVERLAY LOWER THIRD + BADGE

```python
def overlay_lt(img_path, caption=None):
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    H, W = 1920, 1080
    # Lower third
    draw.rectangle([0,H-95,W,H], fill=(8,6,18))
    draw.rectangle([0,H-95,5,H], fill=(220,50,50))
    draw.text((22,H-83),"psi",fill=(255,210,50))
    draw.text((62,H-80),"Daniela Coelho",fill=(255,255,255))
    draw.text((62,H-50),"Saude Mental  |  @psidanielacoelho",fill=(185,170,225))
    draw.rectangle([0,H-4,W,H],fill=(220,50,50))
    # Badge topo
    if caption:
        cw = min(len(caption)*14+44, W-60)
        cx = W//2
        draw.rounded_rectangle([cx-cw//2,32,cx+cw//2,80],radius=15,fill=(245,245,255))
        draw.text((cx-cw//2+22,42),caption,fill=(20,15,45))
    img.save(img_path,"JPEG",quality=95)
```

## SISTEMA DE ANIMAÇÃO

### ATUAL V8: imagens estáticas com troca por frase (funciona)

### V8.1 PRÓXIMO: 3 frames por cena (personagens se movem)
```python
# 3 variações de pose por cena-chave
poses = [
    "listening pose, arms at rest",          # frame A
    "raising hand, arm gesture",             # frame B
    "leaning forward, engaged expression"   # frame C
]
# Ciclo no ffconcat: A(0.08s) B(0.08s) C(0.08s) = 12.5fps sub-animação
n_ciclos = int(dur / 0.24)
for _ in range(n_ciclos):
    for frame in [A, B, C]:
        concat.write(f"file '{frame}'
duration 0.08
")
```

### V8.3 EXPERIMENTAL: VEO image-to-video
```python
# VEO 2.0 (image-to-video — mais estável)
r = requests.post(
    f"https://generativelanguage.googleapis.com/v1beta/models/veo-2.0-generate-001:predictLongRunning?key={KEY}",
    json={"instances":[{"prompt":"character blinks, kawaii 2D animation",
                         "image":{"bytesBase64Encoded":img_b64,"mimeType":"image/jpeg"}}],
          "parameters":{"aspectRatio":"9:16","durationSeconds":6,"sampleCount":1}},
    timeout=20
)
op = r.json()["name"]
# Poll a cada 20s → uri do vídeo quando done=True
```

## SISTEMA DE VOZ

### Padrão: Edge TTS George (SEMPRE)
```python
import edge_tts, asyncio
async def gerar_audio(script):
    comm = edge_tts.Communicate(script, "pt-BR-AntonioNeural")
    await comm.save("audio.mp3")
asyncio.run(gerar_audio(script))
```

### Pós-processamento (qualidade máxima)
```python
subprocess.run(["ffmpeg","-y","-i","audio.mp3",
    "-af","equalizer=f=200:width_type=o:width=2:g=3,"
          "equalizer=f=3000:width_type=o:width=2:g=2,"
          "compand=attacks=0.01:decays=0.2:points=-70/-70|-30/-20|-10/-10|0/-6,"
          "volume=1.3,aresample=44100",
    "-c:a","libmp3lame","-b:a","192k","audio_pro.mp3"])
```

### Upgrade: Gemini TTS Charon (voz masculina premium)
```python
r = requests.post(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={KEY}",
    json={"contents":[{"parts":[{"text":texto}]}],
          "generationConfig":{"responseModalities":["AUDIO"],
                               "speechConfig":{"voiceConfig":{"prebuiltVoiceConfig":{"voiceName":"Charon"}}}}},
    timeout=30
)
# Retorna audio/l16; rate=24000 → converter: ffmpeg -f s16le -ar 24000 -ac 1 -i raw.pcm audio.mp3
```

## ESTRUTURA 21 CENAS (PADRÃO TODOS OS VÍDEOS)

| # | Tipo | Personagem | Prop |
|---|------|-----------|------|
| 1 | Hook pergunta | RENATA surpresa | ? gigante |
| 2 | Estatística | 3 chars, 1 destacado | círculo vermelho |
| 3 | Contradição | Objeto rasurado | X vermelho |
| 4 | Revelação breve | LUCAS | balão sussurro |
| 5 | Contexto/casal | RENATA + LUCAS | aliança |
| 6 | Aparência externa | LUCAS perfeito | estrelas |
| 7 | Realidade interna | RENATA sofrendo | espiral |
| 8 | Amplificação | 3+ chars + STOP | mão STOP |
| 9 | SINAL 1 intro | RENATA + badge | badge S1 |
| 10 | SINAL 1 detalhe | RENATA + LUCAS | seta culpa |
| 11 | SINAL 2 | LUCAS + troféu | badge S2 |
| 12 | SINAL 3 | RENATA exausta | badge S3 + pesos |
| 13 | Autoridade científica | Jaleco + cérebro | dreno |
| 14 | Validação | RENATA | ✅ check verde |
| 15 | Definição negativa | Objeto | coração rasurado |
| 16 | Manipulação | LUCAS máscara | máscara teatro |
| 17 | CTA compartilhar | Celular | seta envio |
| 18 | CTA inscrever | Sino dourado | sino + notas |
| 19 | Empoderamento | RENATA feliz | corações |
| 20 | Amor real | Ícones | olho + ouvido |
| 21 | CTA final | RENATA + sino | próximo episódio |

## REGRAS ABSOLUTAS
1. Lower third: "Daniela Coelho | Saude Mental | @psidanielacoelho"
2. NUNCA "Psicóloga" (só jan/2027+)
3. Voz: pt-BR-AntonioNeural (George, masculino)
4. Duração: 55–58s (≤60s Shorts)
5. Resolução: 1080×1920, 25fps, CRF 18
6. NUNCA canal `UCSH63tBfY6wEIdkC4u4zKdg`
7. Mínimo: 21/21 cenas AI Gemini

## COMO CRIAR VÍDEO NOVO (ex: ID=700)
```
1. SELECT script,audio_url FROM content_pipeline WHERE id=700;
2. cp scripts/render_viral_683_v8.py scripts/render_viral_700_v8.py
3. Trocar id=eq.683→id=eq.700 (3x) e /tmp/v8/→/tmp/v700/
4. Atualizar CENAS[] com frases do script (dur=len(frase)/12.77)
5. Atualizar prompts Gemini para o tema do vídeo
6. Criar .github/workflows/render-viral-700-v8.yml
7. Disparar workflow_dispatch
```

## CHAVES
- Gemini: `AIzaSyDzCea_65Al-vy342xslBSVmKPv0qzTuXY`
- Gemini backup: `AIzaSyCo-YEPjEw3KaOllUIpJKpVwdDZA-Mr5xg`
- NVIDIA: `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`
- ElevenLabs: Sarah `EXAVITQu4vr4xnSDxMaL` multilingual_v2 (~32k chars)
- GitHub Secrets: SUPABASE_SERVICE_KEY + GEMINI_API_KEY

## ESTADO (15/mai/2026)
- #683 V8: 21/21 cenas Gemini AI em 35s | 55.9s | 6.6MB
- URL referência: /mp4s/v683_viral_v8_1778891025.mp4
- Dashboard: https://repovazio.vercel.app/admin.html
