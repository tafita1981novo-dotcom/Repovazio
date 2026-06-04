#!/usr/bin/env python3
"""
thumbnail_seo_v1.py — Thumbnails virais com CTR máximo por país/idioma
ESTRATÉGIA:
  - Fundo escuro (#06060F) — premium look
  - Texto grande e impactante (hook em 3 palavras)
  - Ícone ψ para branding
  - Paleta: violeta #7C3AED + crimson #E11D48 + gold #F59E0B
  - Upscale para 1280x720px (padrão YouTube)
  - Salva no Supabase Storage
"""
import os, pathlib, math, random, json, urllib.request
from datetime import datetime

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)

def criar_thumbnail(titulo, lang="pt", topico="narcisismo", output=None):
    """Cria thumbnail viral 1280x720px com PIL"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        log("Pillow não disponível"); return None

    W, H = 1280, 720
    # Cores da marca ψ
    BG      = (6,   6,  15)   # #06060F
    VIOLET  = (124, 58,237)   # #7C3AED
    CRIMSON = (225, 29, 72)   # #E11D48
    GOLD    = (245,158, 11)   # #F59E0B
    WHITE   = (255,255,255)
    GRAY    = (180,180,200)

    img = Image.new("RGB", (W,H), BG)
    draw = ImageDraw.Draw(img)

    # ── GRADIENTE LATERAL ───────────────────────────────────────────────
    for x in range(W//3):
        t = x / (W//3)
        r = int(BG[0] + (VIOLET[0]-BG[0]) * t * 0.3)
        g = int(BG[1] + (VIOLET[1]-BG[1]) * t * 0.3)
        b = int(BG[2] + (VIOLET[2]-BG[2]) * t * 0.3)
        draw.line([(x,0),(x,H)], fill=(r,g,b))

    # ── CÍRCULO DECORATIVO (direita) ────────────────────────────────────
    cx, cy, r = int(W*0.78), H//2, int(H*0.42)
    for i in range(8, 0, -1):
        alpha = i/8
        c = tuple(int(v*alpha*0.6) for v in VIOLET)
        draw.ellipse([(cx-r-i*15, cy-r-i*15),(cx+r+i*15, cy+r+i*15)], fill=c)
    draw.ellipse([(cx-r,cy-r),(cx+r,cy+r)], fill=tuple(int(v*0.8) for v in VIOLET))

    # ── SÍMBOLO ψ (grande, direita) ─────────────────────────────────────
    try:
        fnt_psi = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 180)
    except:
        fnt_psi = ImageFont.load_default()
    draw.text((cx-55, cy-95), "ψ", font=fnt_psi, fill=WHITE)

    # ── BARRA DE ACENTO (esquerda) ──────────────────────────────────────
    draw.rectangle([(0,0),(8,H)], fill=VIOLET)

    # ── TEXTO PRINCIPAL ─────────────────────────────────────────────────
    # Extrair hook do título (até 3 linhas)
    palavras = titulo.split()
    lines = []
    current = ""
    for w in palavras:
        test = f"{current} {w}".strip()
        if len(test) <= 22:
            current = test
        else:
            if current: lines.append(current)
            current = w
    if current: lines.append(current)
    lines = lines[:3]  # máximo 3 linhas

    try:
        fnt_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        fnt_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        fnt_badge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except:
        fnt_big = fnt_sub = fnt_badge = ImageFont.load_default()

    # Texto principal (esquerda)
    y_start = int(H*0.20)
    for i, line in enumerate(lines):
        y = y_start + i * 85
        # Sombra
        draw.text((35+3, y+3), line, font=fnt_big, fill=(0,0,0))
        # Texto principal
        color = CRIMSON if i == 0 else WHITE  # primeira linha em crimson = impacto
        draw.text((35, y), line, font=fnt_big, fill=color)

    # Subtítulo (pesquisadora)
    sub_y = y_start + len(lines)*85 + 20
    sub_text = {
        "pt": "Daniela Coelho • Pesquisadora de Psicologia",
        "en": "Daniela Coelho • Psychology Researcher",
        "de": "Daniela Coelho • Psychologieforscherin",
        "es": "Daniela Coelho • Investigadora de Psicología",
        "fr": "Daniela Coelho • Chercheuse en Psychologie",
    }.get(lang, "Daniela Coelho • Psychology Researcher")
    draw.text((35, sub_y), sub_text, font=fnt_sub, fill=GRAY)

    # Badge "ψ PSICOLOGIA" no topo
    badge_text = "ψ PSICOLOGIA • @psidanicoelho"
    draw.rectangle([(30, 20),(30+len(badge_text)*12, 55)], fill=VIOLET)
    draw.text((38, 25), badge_text, font=fnt_badge, fill=WHITE)

    # Linha gold na base
    draw.rectangle([(0, H-8),(W, H)], fill=GOLD)

    # Save
    if not output:
        output = pathlib.Path("/tmp") / f"thumb_{lang}_{int(datetime.now().timestamp())}.jpg"
    img.save(str(output), "JPEG", quality=95, optimize=True)
    sz = pathlib.Path(output).stat().st_size
    log(f"Thumbnail: {output} ({sz//1024}KB)")
    return str(output)

def upload_thumbnail_yt(token, video_id, thumb_path):
    """Faz upload da thumbnail para o YouTube"""
    file_size = pathlib.Path(thumb_path).stat().st_size
    url = f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}&uploadType=media"
    req = urllib.request.Request(url, data=open(thumb_path,"rb").read(), method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "image/jpeg")
    req.add_header("Content-Length", str(file_size))
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            log(f"Thumbnail upada: {video_id} ✅")
            return True
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:200]
        log(f"Thumbnail error: {e.code} | {err_body}")
        return False

if __name__ == "__main__":
    log("=== THUMBNAIL SEO TEST ===")
    for lang in ["pt","en","de"]:
        t = criar_thumbnail("Narcisista Encoberto: 7 Sinais Que Você Está Sendo Manipulado", lang, "narcisismo")
        if t: log(f"  ✅ {lang}: {t}")
    log("Thumbnails geradas com sucesso!")
