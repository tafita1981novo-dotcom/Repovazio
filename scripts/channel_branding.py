#!/usr/bin/env python3
"""
Channel Branding Generator — psicologia.doc
Gera: Banner (2560x1440), Profile pic (800x800), Thumbnail template
Estilo: Dark, purple/neon, kawaii chibi anime, ψ symbol
Baseado em: MrBeast (high contrast), Kurzgesagt (clean dark), Dr. Mike (authority)
"""
import urllib.request, urllib.parse, pathlib, json, os, subprocess

GROQ_KEY = os.getenv("GROQ_API_KEY", "")
TMP = pathlib.Path("/tmp/branding"); TMP.mkdir(exist_ok=True)

def pollinations_img(prompt, w, h, seed, path):
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width={w}&height={h}&seed={seed}&nologo=true&model=flux"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "psidoc/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if len(data) > 5000:
            pathlib.Path(path).write_bytes(data)
            print(f"  ✅ {pathlib.Path(path).name}: {len(data)//1024}KB")
            return True
    except Exception as e:
        print(f"  ❌ {pathlib.Path(path).name}: {e}")
    return False

# ── 1. BANNER DO CANAL (2560x1440) ─────────────────────────
print("1. Gerando banner do canal...")
banner_prompt = """
YouTube channel art banner, ultra dark cinematic, "psicologia.doc" text logo large center,
psychology brain neural network purple neon glowing, kawaii chibi anime Daniela character 
researcher pose, ψ psi symbol prominent, dark deep purple #06060F background, electric violet 
neon accents, floating psychology icons (brain, heart, molecules), professional broadcast quality,
horizontal widescreen 16:9, text reads "Daniela Coelho | Pesquisadora de Comportamento Humano",
subscribe button indication, high quality YouTube art style
### nsfw, watermark, bad text, blurry, low quality
"""
pollinations_img(banner_prompt, 2560, 1440, 8888, TMP / "channel_banner.jpg")

# ── 2. FOTO DE PERFIL (800x800) ────────────────────────────
print("2. Gerando foto de perfil...")
profile_prompt = """
Perfect YouTube profile picture, kawaii chibi anime character Daniela, 
female researcher psychologist, dark purple background with neon glow,
ψ psi symbol, confident pose, round circular crop friendly, high contrast,
purple hair, lab coat, neon purple eyes, professional but cute,
dark gradient background #06060F to #7C3AED, perfect face detail
### nsfw, watermark, realistic, real person, blurry
"""
pollinations_img(profile_prompt, 800, 800, 9999, TMP / "profile_picture.jpg")

# ── 3. TEMPLATE DE THUMBNAIL ────────────────────────────────
print("3. Gerando template de thumbnail...")
thumb_prompt = """
YouTube thumbnail template, dark background #06060F, high contrast text area,
kawaii chibi Daniela shocked/surprised expression, neon yellow text outline space,
large bold text overlay space left side, psychological concept visualization right side,
viral YouTube thumbnail style like MrBeast, 3D text, glowing effects,
fear/curiosity emotion trigger, arrow or circle highlight space
### watermark, nsfw, blurry, generic
"""
pollinations_img(thumb_prompt, 1280, 720, 7777, TMP / "thumbnail_template.jpg")

# ── 4. GERAR DESCRIÇÃO VIRAL VIA GROQ ─────────────────────
print("4. Gerando descrição do canal via IA...")
if GROQ_KEY:
    desc_prompt = """Você é especialista em crescimento de canais YouTube virais (MrBeast, Kurzgesagt, NÃO PSICÓLOGA).

Crie a DESCRIÇÃO PERFEITA para o canal @psidanicoelho de Daniela Coelho, pesquisadora de comportamento humano.

Regras:
- NUNCA use "psicóloga" ou "terapeuta" (proibido até 2027)
- Use: pesquisadora, comportamento humano, ciência, neurociência
- Inclua: keywords virais (narcisismo, ansiedade, trauma, manipulação, autoconhecimento)
- Emojis estratégicos para SEO e engagement
- Máx 500 chars para a description principal (YouTube limita busca)
- Adicione seção de links
- Tom: autoritativo mas acessível
- Idioma: Português BR
- Inclua: ψ símbolo como marca

Formato:
[LINHA1: Hook de 1 linha com o que o canal oferece]
[LINHAS 2-4: Proposta de valor com emojis]
[SEÇÃO de temas abordados]
[CTA para inscrição]
[Links formatados]"""
    
    try:
        body = json.dumps({
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": desc_prompt}],
            "max_tokens": 600, "temperature": 0.8
        }).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=body, method="POST",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            desc = json.loads(r.read())["choices"][0]["message"]["content"]
        
        (TMP / "channel_description.txt").write_text(desc)
        print(f"  ✅ Descrição gerada ({len(desc)} chars)")
        print("\n--- PRÉVIA ---")
        print(desc[:400])
        print("---")
    except Exception as e:
        print(f"  Groq: {e}")

print("\n✅ Todos os assets de branding gerados em /tmp/branding/")
print("Arquivos: channel_banner.jpg, profile_picture.jpg, thumbnail_template.jpg, channel_description.txt")
