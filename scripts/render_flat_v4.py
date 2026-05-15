#!/usr/bin/env python3
"""
render_flat_v4.py V2 — CONTEXTUAL SCENE ENGINE
Imagens refletem EXATAMENTE o que é falado no script.
Personagens do elenco fixo com tons de pele, props e poses por cena.
"""
import os, re, time, random, math, base64, json, io, requests
from PIL import Image, ImageDraw, ImageFilter
from supabase import create_client

SB_URL  = os.environ.get("SUPABASE_URL","")
SB_KEY  = os.environ.get("SUPABASE_KEY","")
NVIDIA  = os.environ.get("NVIDIA_API_KEY","")
sb = create_client(SB_URL, SB_KEY)

W, H = 1080, 1920

# ── ELENCO FIXO (8 personagens, tons de pele, roupas) ──────────────────────
ELENCO = {
    "renata":  {"pele":(218,175,130),"cabelo":(90,55,20),"roupa":(220,70,70),  "saias":True},
    "marina":  {"pele":(230,188,148),"cabelo":(160,110,55),"roupa":(180,80,160),"saias":True},
    "sofia":   {"pele":(235,192,152),"cabelo":(145,95,45),"roupa":(200,160,40), "saias":True},
    "lara":    {"pele":(205,158,112),"cabelo":(100,65,28),"roupa":(80,160,180), "saias":True},
    "ana":     {"pele":(242,200,160),"cabelo":(190,140,75),"roupa":(180,60,160),"saias":True},
    "lucas":   {"pele":(182,135,90), "cabelo":(55,32,12),"roupa":(55,80,200),   "saias":False},
    "carlos":  {"pele":(165,118,78), "cabelo":(40,24,8), "roupa":(40,140,80),   "saias":False},
    "rafael":  {"pele":(188,142,98), "cabelo":(62,38,15),"roupa":(70,100,210),  "saias":False},
    "default": {"pele":(210,168,120),"cabelo":(90,55,20),"roupa":(220,80,60),   "saias":True},
}

# ── PALETAS DE FUNDO POR EMOÇÃO ────────────────────────────────────────────
PALETAS = {
    "narcis":   {"top":(255,180,160),"bot":(255,220,200),"geo":(220,80,60)},
    "ansied":   {"top":(180,220,255),"bot":(210,235,255),"geo":(70,130,200)},
    "burnout":  {"top":(255,210,170),"bot":(255,235,210),"geo":(200,120,40)},
    "depress":  {"top":(190,200,220),"bot":(220,225,240),"geo":(100,110,160)},
    "trauma":   {"top":(220,190,255),"bot":(240,220,255),"geo":(140,70,200)},
    "cura":     {"top":(180,240,200),"bot":(210,255,220),"geo":(60,180,100)},
    "impostor": {"top":(255,220,170),"bot":(255,240,210),"geo":(200,150,40)},
    "padrao":   {"top":(255,245,180),"bot":(255,250,220),"geo":(180,140,40)},
}

# ── MAPA PALAVRA→CENA ──────────────────────────────────────────────────────
CENA_MAP = [
    (["cama","acordar","dormir","levantar"],       "cama"),
    (["celular","telefone","mensagem","tela"],      "celular"),
    (["trabalho","computador","reunião","startup"], "escritorio"),
    (["laudo","médic","hospital","jaleco"],         "medico"),
    (["casal","namorad","casad","juntos"],          "casal"),
    (["criança","infância","menin"],                "crianca"),
    (["chorar","lágrima","desabar","dor"],          "emocao_triste"),
    (["sorrir","sorriso","alegre","celebr"],        "emocao_feliz"),
    (["ansiedade","coração","disparar","tremer"],   "ansiedade"),
    (["respirar","calma","paz","transformar"],      "cura"),
    (["cérebro","neurô","ciência","pesquisa"],      "ciencia"),
    (["espelh","reflexo","descobrir","verdade"],    "revelacao"),
]

def detectar_tema(title, script):
    t = (title + " " + script[:200]).lower()
    if any(w in t for w in ["narcis","manipul","gaslight"]): return "narcis"
    if any(w in t for w in ["celular","apego","ansioso","trauma"]): return "ansied"
    if any(w in t for w in ["burnout","cama","neurológ","córtex"]): return "burnout"
    if any(w in t for w in ["depress","silencio","sorri","chora"]): return "depress"
    if any(w in t for w in ["impostor","perfeccion","fraude","laudo"]): return "impostor"
    if any(w in t for w in ["trauma","infância","criança"]): return "trauma"
    return "padrao"

def detectar_personagem(titulo, script):
    nomes = ["renata","marina","sofia","lara","ana","lucas","carlos","rafael"]
    ts = (titulo + " " + script[:300]).lower()
    for n in nomes:
        if n in ts:
            return n
    return "default"

def detectar_tipo_cena(trecho):
    t = trecho.lower()
    for kws, tipo in CENA_MAP:
        if any(k in t for k in kws):
            return tipo
    return "personagem"

def dividir_script_cenas(script, n_cenas=6):
    """Divide o script em N segmentos proporcionais."""
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', script) if len(s.strip()) > 15]
    if not sentences: return [""] * n_cenas
    per = max(1, len(sentences) // n_cenas)
    cenas = []
    for i in range(n_cenas):
        start = i * per
        end = start + per if i < n_cenas - 1 else len(sentences)
        cenas.append(" ".join(sentences[start:end]))
    return cenas

# ── PILLOW DRAW UTILS ──────────────────────────────────────────────────────
def ellipse(draw, cx, cy, rw, rh, fill, outline=None, lw=0):
    draw.ellipse([cx-rw, cy-rh, cx+rw, cy+rh], fill=fill,
                 outline=outline, width=lw)

def rect(draw, x, y, w, h, fill, r=8):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill)

def lerp_c(c1, c2, t):
    return tuple(int(c1[i]*(1-t)+c2[i]*t) for i in range(3))

# ── DESENHO DE PERSONAGEM ─────────────────────────────────────────────────
def desenhar_personagem(draw, cx, cy, p, expressao="neutro", pose="pe", tamanho=1.0):
    sc = tamanho
    pele = p["pele"]; roupa = p["roupa"]; cab = p["cabelo"]
    escuro = tuple(max(0,c-40) for c in pele)
    sombra_roupa = tuple(max(0,c-50) for c in roupa)

    head_r = int(52*sc)
    body_h  = int(120*sc)
    body_w  = int(84*sc)
    leg_h   = int(90*sc)
    arm_l   = int(80*sc)

    if pose == "deitado":
        # Horizontal na cama
        bx, by = cx - int(200*sc), cy
        # Corpo
        draw.rounded_rectangle([bx, by-int(30*sc), bx+int(200*sc), by+int(30*sc)], radius=20, fill=roupa)
        # Cabeça
        ellipse(draw, bx-head_r+10, by, head_r, head_r, pele)
        # Rosto
        _face(draw, bx-head_r+10, by, head_r, pele, expressao, escuro)
        # Lençol
        draw.rounded_rectangle([bx-int(30*sc), by, bx+int(230*sc), by+int(60*sc)], radius=15, fill=(240,240,255))
        return

    if pose == "sentado":
        cy += int(40*sc)

    # Pernas
    leg_w = int(24*sc)
    for dx in [-int(18*sc), int(18*sc)]:
        draw.rounded_rectangle([cx+dx-leg_w//2, cy, cx+dx+leg_w//2, cy+leg_h], radius=8, fill=sombra_roupa)
        # Sapato
        ellipse(draw, cx+dx, cy+leg_h, int(18*sc), int(10*sc), (50,40,30))

    # Corpo
    draw.rounded_rectangle([cx-body_w//2, cy-body_h, cx+body_w//2, cy], radius=18, fill=roupa)

    # Braços
    for dx in [-body_w//2-int(5*sc), body_w//2+int(5*sc)]:
        sign = -1 if dx < 0 else 1
        ax, ay = cx+dx, cy-int(70*sc)
        draw.line([ax, ay, ax+sign*int(30*sc), ay+int(arm_l//2)], fill=pele, width=int(18*sc))
        ellipse(draw, ax+sign*int(32*sc), ay+int(arm_l//2), int(12*sc), int(12*sc), pele)

    # Cabeça
    ellipse(draw, cx, cy-body_h-head_r+int(15*sc), head_r, head_r, pele)
    # Cabelo
    ellipse(draw, cx, cy-body_h-head_r*2+int(20*sc), head_r+int(4*sc), int(head_r*0.55), cab)

    # Rosto
    _face(draw, cx, cy-body_h-head_r+int(15*sc), head_r, pele, expressao, escuro)

def _face(draw, cx, cy, hr, pele, expressao, escuro):
    # Olhos
    for dx in [-int(hr*0.35), int(hr*0.35)]:
        ellipse(draw, cx+dx, cy-int(hr*0.15), int(hr*0.14), int(hr*0.16), (255,255,255))
        ellipse(draw, cx+dx, cy-int(hr*0.15), int(hr*0.08), int(hr*0.09), (40,30,20))
        # Brilho
        ellipse(draw, cx+dx+int(hr*0.04), cy-int(hr*0.20), int(hr*0.04), int(hr*0.04), (255,255,255))

    if expressao == "feliz":
        # Sorriso
        draw.arc([cx-int(hr*0.4), cy+int(hr*0.05), cx+int(hr*0.4), cy+int(hr*0.45)],
                  0, 180, fill=escuro, width=int(hr*0.1))
    elif expressao == "triste":
        draw.arc([cx-int(hr*0.4), cy+int(hr*0.2), cx+int(hr*0.4), cy+int(hr*0.55)],
                  180, 0, fill=escuro, width=int(hr*0.1))
        # Lágrima
        draw.polygon([
            (cx-int(hr*0.35), cy+int(hr*0.05)),
            (cx-int(hr*0.42), cy+int(hr*0.25)),
            (cx-int(hr*0.28), cy+int(hr*0.25)),
        ], fill=(100,160,255))
    elif expressao == "ansioso":
        draw.arc([cx-int(hr*0.3), cy+int(hr*0.15), cx+int(hr*0.3), cy+int(hr*0.45)],
                  0, 180, fill=escuro, width=int(hr*0.08))
        # Suor
        draw.polygon([(cx+int(hr*0.45), cy-int(hr*0.2)),
                      (cx+int(hr*0.5), cy-int(hr*0.05)),
                      (cx+int(hr*0.38), cy-int(hr*0.05))], fill=(100,200,255))
    elif expressao == "exausto":
        # Olhos meio fechados
        for dx in [-int(hr*0.35), int(hr*0.35)]:
            draw.rectangle([cx+dx-int(hr*0.14), cy-int(hr*0.23),
                             cx+dx+int(hr*0.14), cy-int(hr*0.12)], fill=pele)
        draw.line([cx-int(hr*0.25), cy+int(hr*0.3), cx+int(hr*0.25), cy+int(hr*0.28)],
                   fill=escuro, width=int(hr*0.07))
    else:  # neutro
        draw.line([cx-int(hr*0.25), cy+int(hr*0.28), cx+int(hr*0.25), cy+int(hr*0.28)],
                   fill=escuro, width=int(hr*0.07))

# ── PROPS / ELEMENTOS DE CENA ──────────────────────────────────────────────
def desenhar_celular(draw, x, y, s=1.0):
    cw, ch = int(50*s), int(90*s)
    draw.rounded_rectangle([x-cw//2, y-ch//2, x+cw//2, y+ch//2], radius=10, fill=(30,30,40))
    draw.rounded_rectangle([x-cw//2+6, y-ch//2+10, x+cw//2-6, y+ch//2-12], radius=4, fill=(100,180,255))
    # Notificação
    ellipse(draw, x+cw//2-8, y-ch//2+8, 10, 10, (220,50,50))
    draw.text((x+cw//2-12, y-ch//2+2), "!", fill=(255,255,255))

def desenhar_cama(draw, cx, cy, s=1.0):
    bw, bh = int(380*s), int(160*s)
    # Estrutura
    draw.rounded_rectangle([cx-bw//2, cy-bh//2, cx+bw//2, cy+bh//2], radius=20, fill=(160,120,80))
    # Colchão
    draw.rounded_rectangle([cx-bw//2+15, cy-bh//2+20, cx+bw//2-15, cy+bh//2-15], radius=12, fill=(240,235,255))
    # Travesseiro
    draw.rounded_rectangle([cx-bw//2+25, cy-bh//2+25, cx-bw//2+120, cy-bh//2+70], radius=8, fill=(255,255,255))
    # Cabeceira
    draw.rounded_rectangle([cx-bw//2, cy-bh//2-40, cx+bw//2, cy-bh//2+10], radius=15, fill=(130,90,50))

def desenhar_coracao(draw, cx, cy, r, cor=(220,60,80), batendo=False):
    # Coração simples com círculos
    ellipse(draw, cx-r//2, cy-r//4, r//2, r//2, cor)
    ellipse(draw, cx+r//2, cy-r//4, r//2, r//2, cor)
    draw.polygon([(cx-r, cy),(cx, cy+r),(cx+r, cy)], fill=cor)

def desenhar_estrelas(draw, n=6):
    for _ in range(n):
        x, y = random.randint(50, W-50), random.randint(80, int(H*0.4))
        r = random.randint(8, 18)
        c = random.randint(200, 255)
        ellipse(draw, x, y, r, r//2, (c, c, int(c*0.7)))

def desenhar_nuvens(draw, pal):
    nuvens = [(150,180,3), (450,120,2.5), (680,200,2), (900,150,2.2), (280,250,1.8)]
    for nx, ny, s in nuvens:
        for dx, dy in [(0,0),(-30,10),(30,10),(-15,-8),(15,-8)]:
            ellipse(draw, nx+dx, ny+dy, int(38*s), int(28*s), (255,255,255))

def desenhar_sol(draw, pal):
    sx, sy = W-90, 85
    # Raios
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        r1, r2 = 55, 80
        draw.line([int(sx+r1*math.cos(rad)), int(sy+r1*math.sin(rad)),
                   int(sx+r2*math.cos(rad)), int(sy+r2*math.sin(rad))],
                   fill=(255,200,50), width=6)
    ellipse(draw, sx, sy, 48, 48, (255,210,50))

def desenhar_elementos_geo(draw, pal, seed=0):
    random.seed(seed)
    geo_c = pal["geo"]
    formas = []
    for _ in range(8):
        x, y = random.randint(30, W-30), random.randint(80, int(H*0.85))
        tipo = random.choice(["circ","tri","quad"])
        r = random.randint(10, 28)
        alpha = random.randint(80, 160)
        formas.append((x, y, tipo, r, geo_c, alpha))
    for x, y, tipo, r, c, a in formas:
        c_a = c + (a,) if len(c)==3 else c
        if tipo == "circ":
            ellipse(draw, x, y, r, r, c)
        elif tipo == "tri":
            draw.polygon([(x,y-r),(x-r,y+r),(x+r,y+r)], fill=c)
        else:
            draw.rectangle([x-r//2, y-r//2, x+r//2, y+r//2], fill=c)

def desenhar_lower_third(draw):
    bx, by = 28, H-120
    bw, bh = 420, 72
    # Fundo
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=10,
                             fill=(26, 26, 42))
    # ψ icon
    draw.text((bx+14, by+12), "ψ", fill=(124,58,237))
    draw.text((bx+40, by+12), "Daniela Coelho | Psicóloga Clínica",
               fill=(240,240,255))
    draw.text((bx+40, by+40), "@psidanielacoelho", fill=(160,130,210))

def desenhar_watermark_psi(draw):
    draw.text((W-60, 30), "ψ", fill=(200,200,200))

# ── GERADOR DE CENA CONTEXTUAL ────────────────────────────────────────────
def gerar_cena_contextual(titulo, trecho, cena_idx, n_cenas, video_id, tema, personagem_nome):
    img = Image.new("RGB", (W, H), (255,255,255))
    draw = ImageDraw.Draw(img)

    pal = PALETAS.get(tema, PALETAS["padrao"])
    p   = ELENCO.get(personagem_nome, ELENCO["default"])
    tipo_cena = detectar_tipo_cena(trecho)

    # ── Fundo gradiente ──
    for y in range(H):
        t = y / H
        # 3 zonas: céu quente → meio quente → chão
        if y < H*0.65:
            t2 = y / (H*0.65)
            c = lerp_c(pal["top"], pal["bot"], t2)
        else:
            t2 = (y - H*0.65) / (H*0.35)
            c = lerp_c(pal["bot"], (200,185,160), t2)
        draw.line([(0,y),(W,y)], fill=c)

    # Chão
    gy = int(H * 0.72)
    draw.rectangle([0, gy, W, H], fill=(210,195,170))

    # Decorativos
    desenhar_sol(draw, pal)
    desenhar_nuvens(draw, pal)
    desenhar_elementos_geo(draw, pal, seed=cena_idx + video_id * 10)

    # ── CENAS CONTEXTUAIS ──────────────────────────────────────────────
    cx_p = int(W * 0.42)  # posição X do personagem

    if tipo_cena == "cama":
        # Quarto: cama + personagem deitado
        desenhar_cama(draw, W//2, gy - 60, s=1.1)
        desenhar_personagem(draw, W//2, gy-90, p, "exausto", "deitado", tamanho=0.9)
        # Relógio
        ellipse(draw, W-120, 300, 45, 45, (240,240,240))
        draw.text((W-140, 275), "2:00", fill=(50,50,50))

    elif tipo_cena == "celular":
        # Pessoa em pé com celular na mão
        desenhar_personagem(draw, cx_p, gy, p, "ansioso", "pe", tamanho=1.0)
        desenhar_celular(draw, cx_p+80, gy-220, s=1.2)
        # Ondas de ansiedade
        for r in [30, 55, 80]:
            draw.arc([cx_p+60-r, gy-240-r, cx_p+100+r, gy-200+r],
                      0, 180, fill=(*pal["geo"][:3], 100), width=3)

    elif tipo_cena == "escritorio":
        # Personagem sentado + mesa + computador
        desenhar_personagem(draw, cx_p, gy, p, "exausto", "sentado", tamanho=0.95)
        # Mesa
        draw.rectangle([cx_p-160, gy-40, cx_p+160, gy+20], fill=(170,130,90))
        # Computador
        draw.rounded_rectangle([cx_p-60, gy-180, cx_p+60, gy-60], radius=8, fill=(40,40,60))
        draw.rounded_rectangle([cx_p-52, gy-172, cx_p+52, gy-68], radius=4, fill=(80,180,255))
        # Papéis
        for dx in [-100, -130, -70]:
            draw.rounded_rectangle([cx_p+dx, gy-55, cx_p+dx+50, gy-30], radius=3, fill=(255,255,240))

    elif tipo_cena == "medico":
        # Personagem com jaleco + laudos
        p_med = dict(p); p_med["roupa"] = (255,255,255)
        desenhar_personagem(draw, cx_p, gy, p_med, "neutro", "pe", tamanho=1.0)
        # Prancheta
        draw.rounded_rectangle([cx_p+60, gy-200, cx_p+130, gy-120], radius=5, fill=(255,255,240))
        for i in range(5):
            draw.line([cx_p+68, gy-190+i*14, cx_p+122, gy-190+i*14], fill=(180,180,180), width=2)
        # Cruz médica
        draw.rectangle([W-100, 200, W-70, 260], fill=(220,50,50))
        draw.rectangle([W-115, 215, W-55, 245], fill=(220,50,50))

    elif tipo_cena == "casal":
        # Dois personagens
        p2 = ELENCO.get("carlos", ELENCO["default"])
        desenhar_personagem(draw, W//2-110, gy, p, "feliz", "pe", tamanho=0.9)
        desenhar_personagem(draw, W//2+110, gy, p2, "feliz", "pe", tamanho=0.9)
        # Coração entre eles
        desenhar_coracao(draw, W//2, gy-280, 40)

    elif tipo_cena == "crianca":
        # Criança pequena aguardando
        p_cri = dict(p); 
        desenhar_personagem(draw, cx_p, gy, p, "triste", "pe", tamanho=0.65)
        # Brinquedo no chão
        ellipse(draw, cx_p+60, gy+10, 20, 20, (220,80,80))

    elif tipo_cena == "emocao_triste":
        desenhar_personagem(draw, cx_p, gy, p, "triste", "pe", tamanho=1.0)
        # Chuva
        for _ in range(12):
            rx, ry = random.randint(50, W-50), random.randint(80, gy-50)
            draw.line([(rx, ry), (rx-5, ry+25)], fill=(100,160,220), width=3)

    elif tipo_cena == "emocao_feliz":
        desenhar_personagem(draw, cx_p, gy, p, "feliz", "pe", tamanho=1.05)
        # Confetes
        for _ in range(15):
            rx, ry = random.randint(50, W-50), random.randint(80, gy-50)
            c = random.choice([(220,80,60),(80,160,220),(60,180,80),(220,180,40)])
            draw.rectangle([rx, ry, rx+12, ry+6], fill=c)

    elif tipo_cena == "ansiedade":
        desenhar_personagem(draw, cx_p, gy, p, "ansioso", "pe", tamanho=1.0)
        # Coração batendo
        desenhar_coracao(draw, W//2+160, gy-350, 50, (220,50,50))
        # Linhas de estresse
        for i in range(3):
            draw.arc([cx_p+80+i*15, gy-260+i*10, cx_p+140+i*15, gy-200+i*10],
                      -30, 30, fill=(220,80,80), width=4)

    elif tipo_cena == "cura":
        desenhar_personagem(draw, cx_p, gy, p, "feliz", "pe", tamanho=1.05)
        # Círculos de paz
        for r in [60, 100, 145]:
            draw.arc([cx_p-r, gy-380-r, cx_p+r, gy-380+r+100],
                      0, 360, fill=(*pal["geo"][:3],), width=3)
        draw.text((cx_p-30, gy-470), "♥", fill=(80,200,120))

    elif tipo_cena == "ciencia":
        desenhar_personagem(draw, cx_p, gy, p, "neutro", "pe", tamanho=0.95)
        # Cérebro simplificado
        ellipse(draw, W//2+200, gy-450, 70, 55, (220,150,160))
        ellipse(draw, W//2+240, gy-440, 45, 35, (200,130,140))
        # Ondas cerebrais
        pontos = []
        for i in range(60):
            x2 = W//2+140+i*2
            y2 = gy-390+int(20*math.sin(i*0.5))
            pontos.append((x2, y2))
        if len(pontos) > 1: draw.line(pontos, fill=(180,60,80), width=3)

    elif tipo_cena == "revelacao":
        desenhar_personagem(draw, cx_p, gy, p, "neutro", "pe", tamanho=1.0)
        # Espelho / moldura
        draw.rounded_rectangle([W//2+80, gy-450, W//2+220, gy-250], radius=12, fill=(200,190,180))
        draw.rounded_rectangle([W//2+90, gy-440, W//2+210, gy-260], radius=8, fill=(210,230,240))
        # Reflexo
        desenhar_personagem(draw, W//2+150, gy-310, p, "neutro", "pe", tamanho=0.4)

    else:  # personagem genérico
        desenhar_personagem(draw, cx_p, gy, p, "neutro", "pe", tamanho=1.0)

    # ── LOWER THIRD + WATERMARK ─────────────────────────────────────────
    desenhar_lower_third(draw)
    desenhar_watermark_psi(draw)

    path = f"/tmp/cena_v4ctx_{video_id}_{cena_idx}.jpg"
    img.save(path, "JPEG", quality=92)
    return path

# ── NVIDIA PROMPT CONTEXTUAL ───────────────────────────────────────────────
def gerar_prompt_nvidia(titulo, trecho, cena_idx, tema, personagem, tipo_cena):
    pal = PALETAS.get(tema, PALETAS["padrao"])
    r, g, b = pal["top"]
    cor_desc = f"warm background rgb({r},{g},{b})"

    descricoes_cena = {
        "cama":         "person lying in bed looking exhausted, bedroom scene",
        "celular":      "person holding smartphone looking anxious, checking messages compulsively",
        "escritorio":   "person sitting at desk with laptop looking stressed and tired",
        "medico":       "person in white coat holding medical clipboard, professional scene",
        "casal":        "two people standing together, relationship scene",
        "crianca":      "small child waiting alone, emotional scene",
        "emocao_triste":"person looking sad with tears, emotional vulnerable scene",
        "emocao_feliz": "person smiling joyfully, celebrating, happy scene",
        "ansiedade":    "person with hands on chest looking anxious and overwhelmed",
        "cura":         "person breathing peacefully with eyes closed, healing scene",
        "ciencia":      "person with thought bubble showing brain activity, neuroscience",
        "revelacao":    "person looking at mirror with realization expression",
        "personagem":   "person standing thoughtfully, educational psychology scene",
    }
    cena_desc = descricoes_cena.get(tipo_cena, "person in a colorful scene")

    return (
        f"flat 2D vector illustration, {cena_desc}, {cor_desc}, "
        f"simple geometric cartoon character with expressive face and visible eyes, "
        f"bright warm colorful palette, clean bold outlines, "
        f"School of Life or Kurzgesagt animation style, "
        f"cheerful educational scene, no text no words no letters no logos"
    )

def tentar_nvidia(prompt, video_id, cena_idx):
    if not NVIDIA: return None
    endpoints = [
        ("https://integrate.api.nvidia.com/v1/images/generations",
         {"model":"black-forest-labs/flux-schnell","prompt":prompt,
          "n":1,"size":"1344x768","response_format":"b64_json"}),
    ]
    for ep, payload in endpoints:
        try:
            r = requests.post(ep,
                headers={"Authorization":"Bearer "+NVIDIA,"Content-Type":"application/json"},
                json=payload, timeout=90)
            print(f"    NVIDIA {r.status_code}")
            if r.status_code != 200: continue
            data = r.json()
            b64 = data.get("data",[{}])[0].get("b64_json","") or \
                  data.get("artifacts",[{}])[0].get("base64","")
            if b64:
                p = f"/tmp/nv_{video_id}_{cena_idx}.jpg"
                with open(p,"wb") as f: f.write(base64.b64decode(b64))
                # Converter para portrait 1080x1920
                img = Image.open(p)
                # Crop central landscape → portrait
                img_r = img.resize((1080, int(img.height*1080/img.width)))
                portrait = Image.new("RGB",(1080,1920),(255,250,230))
                portrait.paste(img_r, (0, (1920-img_r.height)//2))
                portrait.save(p, "JPEG", quality=90)
                return p
        except Exception as e:
            print(f"    NVIDIA exc: {e}")
    return None

def upload_retry(path, video_id, cena_idx, tentativas=3):
    fname = f"v4ctx/flat_{video_id}_{cena_idx}_{int(time.time())}.jpg"
    with open(path,"rb") as f: data = f.read()
    for i in range(tentativas):
        try:
            r = requests.post(SB_URL+"/storage/v1/object/videos/"+fname,
                headers={"apikey":SB_KEY,"Authorization":"Bearer "+SB_KEY,
                         "Content-Type":"image/jpeg","x-upsert":"true"},
                data=data, timeout=120)
            if r.status_code in [200,201]:
                return SB_URL+"/storage/v1/object/public/videos/"+fname
        except Exception as e:
            print(f"    upload exc: {e}")
        time.sleep(2)
    return None

def get_pendentes():
    r = sb.table("content_pipeline").select(
        "id,title,script,audio_url,metadata,duracao_min,pub_order"
    ).eq("status","mp4_ready").is_("mp4_url",None).order("pub_order").limit(5).execute()
    return r.data or []

def processar(v):
    vid_id = v["id"]; title = v.get("title",""); script = v.get("script","") or ""
    dur = float(v.get("duracao_min") or 0.9)
    print(f"\n  #{vid_id} {title[:55]}")
    tema = detectar_tema(title, script)
    personagem = detectar_personagem(title, script)
    n_cenas = 6
    cenas_texto = dividir_script_cenas(script, n_cenas)
    print(f"    tema={tema} | personagem={personagem} | {n_cenas} cenas contextuais")

    urls = []
    for i, trecho in enumerate(cenas_texto):
        tipo = detectar_tipo_cena(trecho)
        print(f"    cena {i+1}/{n_cenas} tipo={tipo}...")
        # Tentar NVIDIA primeiro com prompt contextual
        prompt = gerar_prompt_nvidia(title, trecho, i, tema, personagem, tipo)
        img = tentar_nvidia(prompt, vid_id, i)
        fonte = "nvidia"
        if not img:
            # Fallback: Pillow contextual
            img = gerar_cena_contextual(title, trecho, i, n_cenas, vid_id, tema, personagem)
            fonte = "pillow_ctx"
        url = upload_retry(img, vid_id, i)
        if url:
            urls.append(url)
            print(f"      cena {i+1} ({fonte}) OK")
        time.sleep(0.4)

    if not urls: print("    sem imagens"); return False
    sb.table("content_pipeline").update({
        "status":"video_ready","mp4_url":None,
        "metadata": (v.get("metadata") or {}) | {
            "quantum_images":urls,"quantum_image":urls[0],
            "n_cenas":len(urls),"tema":tema,"personagem":personagem,
            "render_method":"flat_2d_contextual_v4_2",
            "processado_em":int(time.time()),
        }
    }).eq("id",vid_id).execute()
    print(f"    video_ready {len(urls)} cenas contextuais")
    return True

def main():
    print("=== RENDER FLAT V4.2 — CONTEXTUAL SCENE ENGINE ===")
    print(f"NVIDIA: {'OK' if NVIDIA else 'ausente → Pillow contextual'}")
    videos = get_pendentes()
    print(f"Videos: {len(videos)}")
    ok = 0
    for v in videos:
        try:
            if processar(v): ok += 1
        except Exception as e:
            import traceback; traceback.print_exc()
        time.sleep(1)
    print(f"Concluido: {ok}/{len(videos)}")

if __name__ == "__main__":
    main()
