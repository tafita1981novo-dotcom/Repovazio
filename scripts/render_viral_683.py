#!/usr/bin/env python3
"""render_viral_683_v7.py
MELHORIAS V7:
  - Renata = boneca FEMININA (saia, cabelo longo, cilios)
  - Lucas = boneco MASCULINO (ombros largos, cabelo curto)
  - ffconcat: cada cena dura EXATAMENTE o tempo da frase falada
  - 21 cenas mapeadas frase por frase do script (12.77 chars/s)
  - Props por frase: celular, megafone, trofeu, coracao, espiral, sino...
  - SEM Psicologa no lower third
  - $0 custo
"""
import os,json,math,time,subprocess,requests
from PIL import Image,ImageDraw

SB_URL=os.environ.get("SUPABASE_URL","")
SB_KEY=os.environ.get("SUPABASE_KEY","")
W,H=1080,1920
os.makedirs("/tmp/v7",exist_ok=True)

# Paletas distintas por cena
PALS=[
    ((15,12,30),(30,20,50),(200,80,220)),    # 0 ROXO
    ((200,20,20),(160,10,10),(255,240,240)),  # 1 VERMELHO
    ((8,18,75),(4,8,55),(60,140,255)),        # 2 AZUL
    ((220,100,20),(180,70,5),(255,255,200)),  # 3 LARANJA
    ((55,8,8),(28,4,4),(255,90,90)),          # 4 VINHO
    ((200,160,10),(170,130,0),(120,60,0)),    # 5 AMBAR
    ((160,30,30),(120,15,15),(255,215,80)),   # 6 VERM+OURO
    ((35,35,75),(18,18,55),(190,170,255)),    # 7 INDIGO
    ((0,130,120),(0,90,80),(180,255,245)),    # 8 TEAL
    ((65,15,95),(40,8,70),(195,90,255)),      # 9 ROXO2
    ((15,150,70),(8,110,50),(180,255,210)),   # 10 VERDE
    ((220,170,0),(185,140,0),(160,60,0)),     # 11 OURO
]

# Personagens
PR_F=(222,175,132);CR_F=(160,100,45);RR_F=(220,80,100)  # Renata fem
PR_M=(182,135,90); CR_M=(55,32,12);  RL_M=(60,80,200)   # Lucas masc
PR_J=(222,175,132);CR_J=(90,55,20);  RJ=(255,255,255)    # Jaleco

BR=(255,255,255);ES=(10,8,8)
AM=(255,210,50);VERM=(220,50,50)

def lerp(a,b,t): return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(len(a)))

def fundo(draw,ct,cb):
    for y in range(H):
        c=lerp(ct,cb,y/(H*0.75)) if y<int(H*0.75) else lerp(cb,tuple(max(0,x-25) for x in cb),(y-H*0.75)/(H*0.25))
        draw.line([(0,y),(W,y)],fill=c)

def geo(draw,cor,n,seed):
    import random; random.seed(seed*37+13)
    for _ in range(n):
        x=random.randint(50,W-50);y=random.randint(50,int(H*0.72));r=random.randint(8,28)
        t=random.choice(["c","t","q"])
        if t=="c": draw.ellipse([x-r,y-r,x+r,y+r],fill=cor)
        elif t=="t": draw.polygon([(x,y-r),(x-r,y+r),(x+r,y+r)],fill=cor)
        else: draw.rectangle([x-r//2,y-r//2,x+r//2,y+r//2],fill=cor)

def lt(draw):
    bx,by=28,H-118
    draw.rounded_rectangle([bx,by,bx+440,by+76],radius=11,fill=(12,10,25))
    draw.text((bx+14,by+10),"psi",fill=AM)
    draw.text((bx+44,by+10),"Daniela Coelho | Saude Mental",fill=BR)
    draw.text((bx+44,by+40),"@psidanielacoelho",fill=(190,175,230))
    draw.rectangle([bx,by+73,bx+440,by+76],fill=VERM)

# ────────────────── PERSONAGEM FEMININO ──────────────────
def boneca(draw,cx,cy,pele,cab,roupa,expr="neutro",pose="pe",sc=1.0):
    """Personagem FEMININO: saia, cabelo comprido, cilios longos"""
    hr=int(55*sc);bw=int(82*sc);bh=int(100*sc);leg=int(80*sc);lw=int(24*sc)
    sr=tuple(max(0,c-45) for c in roupa);sp=tuple(max(0,c-30) for c in pele)
    # Pernas (slim)
    for dx in[-int(14*sc),int(14*sc)]:
        draw.rounded_rectangle([cx+dx-lw//2,cy,cx+dx+lw//2,cy+leg],radius=8,fill=sr)
        draw.ellipse([cx+dx-int(14*sc),cy+leg-4,cx+dx+int(14*sc),cy+leg+12],fill=(30,20,12))
    # SAIA (trapézio)
    sw=int(75*sc)
    draw.polygon([(cx-int(38*sc),cy-int(20*sc)),(cx+int(38*sc),cy-int(20*sc)),
                   (cx+sw,cy+int(5*sc)),(cx-sw,cy+int(5*sc))],fill=sr)
    # Corpo
    draw.rounded_rectangle([cx-bw//2,cy-bh,cx+bw//2,cy-int(22*sc)],radius=18,fill=roupa)
    # Cintura
    draw.rounded_rectangle([cx-int(35*sc),cy-int(28*sc),cx+int(35*sc),cy-int(12*sc)],radius=6,fill=sr)
    # Braços (finos)
    ay=cy-int(65*sc)
    for sgn,dx in[(-1,-bw//2-int(5*sc)),(1,bw//2+int(5*sc))]:
        if pose=="apontando" and sgn==1:
            draw.line([cx+dx,ay,cx+dx+sgn*int(45*sc),ay-int(55*sc)],fill=pele,width=int(16*sc))
            draw.ellipse([cx+dx+sgn*int(33*sc)-12,ay-68,cx+dx+sgn*int(33*sc)+12,ay-44],fill=pele)
        elif pose=="costas":
            draw.line([cx+dx,ay,cx,ay+int(18*sc)],fill=pele,width=int(16*sc))
        else:
            draw.line([cx+dx,ay,cx+dx+sgn*int(22*sc),ay+int(35*sc)],fill=pele,width=int(16*sc))
            draw.ellipse([cx+dx+sgn*12-12,ay+23,cx+dx+sgn*12+12,ay+47],fill=pele)
    draw.rectangle([cx-int(12*sc),cy-bh-int(10*sc),cx+int(12*sc),cy-bh+int(8*sc)],fill=pele)
    # Cabeça
    hx,hy=cx,cy-bh-hr+int(10*sc)
    draw.ellipse([hx-hr,hy-hr,hx+hr,hy+hr],fill=pele)
    draw.ellipse([hx-hr-5,hy-14,hx-hr+9,hy+14],fill=sp)
    draw.ellipse([hx+hr-9,hy-14,hx+hr+5,hy+14],fill=sp)
    # CABELO COMPRIDO (bun no topo + fios laterais)
    draw.ellipse([hx-hr-3,hy-hr-5,hx+hr+3,hy-int(hr*0.22)],fill=cab)
    # Fios laterais (feminino)
    for sgn in[-1,1]:
        x_a=min(hx+sgn*(hr-8),hx+sgn*(hr+8));x_b=max(hx+sgn*(hr-8),hx+sgn*(hr+8))
        draw.rounded_rectangle([x_a,hy-int(hr*0.3),x_b,hy+int(hr*0.6)],radius=8,fill=cab)
    # Coque no topo
    draw.ellipse([hx-int(hr*0.4),hy-hr-int(hr*0.45),hx+int(hr*0.4),hy-hr+int(hr*0.1)],fill=cab)
    rosto_fem(draw,hx,hy,hr,pele,expr)

def rosto_fem(draw,cx,cy,hr,pele,expr):
    """Rosto feminino com cilios mais expressivos"""
    sob=cy-int(hr*0.55);oy=cy-int(hr*0.18)
    ew,eh=int(hr*0.24),int(hr*0.28)
    for sgn in[-1,1]:
        ex=cx+sgn*int(hr*0.37)
        # Sobrancelha fina
        if expr in["bravo","frustrado"]:
            draw.line([(ex-int(hr*0.22),sob-int(hr*0.08)*sgn),(ex+int(hr*0.22),sob+int(hr*0.08)*sgn)],fill=ES,width=int(hr*0.07))
        elif expr in["triste","exausto","choro"]:
            draw.line([(ex-int(hr*0.22),sob+int(hr*0.08)*sgn),(ex+int(hr*0.22),sob-int(hr*0.08)*sgn)],fill=ES,width=int(hr*0.07))
        elif expr=="surpresa":
            draw.arc([ex-int(hr*0.22),sob-int(hr*0.14),ex+int(hr*0.22),sob+int(hr*0.04)],0,180,fill=ES,width=int(hr*0.07))
        else:
            draw.line([(ex-int(hr*0.20),sob),(ex+int(hr*0.20),sob)],fill=ES,width=int(hr*0.06))
        # Olho com esclera
        draw.ellipse([ex-ew,oy-eh,ex+ew,oy+eh],fill=BR)
        draw.ellipse([ex-int(hr*0.15),oy-int(hr*0.17),ex+int(hr*0.15),oy+int(hr*0.17)],fill=(80,50,35))
        draw.ellipse([ex-int(hr*0.09),oy-int(hr*0.10),ex+int(hr*0.09),oy+int(hr*0.10)],fill=ES)
        draw.ellipse([ex+int(hr*0.05),oy-int(hr*0.13),ex+int(hr*0.11),oy-int(hr*0.07)],fill=BR)
        # CILIOS LONGOS (feminino)
        for k in range(7):
            ang=math.radians(-80+k*27)
            draw.line([int(ex+ew*math.cos(ang)),int(oy-eh*math.sin(ang)),
                       int(ex+(ew+12)*math.cos(ang)),int(oy-(eh+13)*math.sin(ang))],fill=ES,width=2)
        if expr=="exausto":
            draw.line([ex-ew,oy,ex+ew,oy],fill=ES,width=int(hr*0.17))
    draw.ellipse([cx-6,cy+int(hr*0.06),cx+6,cy+int(hr*0.12)],fill=tuple(max(0,c-25) for c in pele))
    # Batom/boca feminina
    my=cy+int(hr*0.32);bw2=int(hr*0.38)
    boca_cor=(200,70,90) if expr in["feliz","sorriso_falso"] else ES
    if expr in["feliz","sorriso_falso"]:
        draw.arc([cx-bw2,my-int(hr*0.22),cx+bw2,my+int(hr*0.22)],0,180,fill=boca_cor,width=int(hr*0.12))
        # Dentes brancos
        draw.arc([cx-bw2+6,my-int(hr*0.18),cx+bw2-6,my+int(hr*0.18)],10,170,fill=BR,width=int(hr*0.06))
    elif expr in["triste","choro"]:
        draw.arc([cx-bw2,my-int(hr*0.10),cx+bw2,my+int(hr*0.25)],180,0,fill=boca_cor,width=int(hr*0.11))
        if expr=="choro":
            draw.polygon([(cx-22,my-18),(cx-31,my+6),(cx-13,my+6)],fill=(80,150,255))
    elif expr=="surpresa":
        draw.ellipse([cx-20,my-18,cx+20,my+18],fill=ES)
    elif expr=="falando":
        draw.arc([cx-25,my-14,cx+25,my+14],0,180,fill=boca_cor,width=int(hr*0.10))
        draw.rounded_rectangle([cx-18,my-5,cx+18,my+5],radius=4,fill=BR)
    elif expr=="exausto":
        draw.line([cx-22,my+4,cx+22,my],fill=ES,width=int(hr*0.10))
    else:
        draw.line([cx-22,my,cx+22,my],fill=ES,width=int(hr*0.09))

# ────────────────── PERSONAGEM MASCULINO ──────────────────
def boneco(draw,cx,cy,pele,cab,roupa,expr="neutro",pose="pe",sc=1.0):
    """Personagem MASCULINO: ombros mais largos, calca, cabelo curto"""
    hr=int(57*sc);bw=int(95*sc);bh=int(120*sc);leg=int(98*sc);lw=int(28*sc)
    sr=tuple(max(0,c-50) for c in roupa);sp=tuple(max(0,c-35) for c in pele)
    for dx in[-int(17*sc),int(17*sc)]:
        draw.rounded_rectangle([cx+dx-lw//2,cy,cx+dx+lw//2,cy+leg],radius=10,fill=sr)
        draw.ellipse([cx+dx-int(20*sc),cy+leg-5,cx+dx+int(20*sc),cy+leg+16],fill=(30,20,12))
    draw.rounded_rectangle([cx-bw//2,cy-bh,cx+bw//2,cy],radius=22,fill=roupa)
    draw.rounded_rectangle([cx-int(22*sc),cy-bh,cx+int(22*sc),cy-bh+int(22*sc)],radius=8,fill=sr)
    ay=cy-int(74*sc)
    for sgn,dx in[(-1,-bw//2-int(8*sc)),(1,bw//2+int(8*sc))]:
        if pose=="apontando" and sgn==1:
            draw.line([cx+dx,ay,cx+dx+sgn*int(55*sc),ay-int(65*sc)],fill=pele,width=int(22*sc))
            draw.ellipse([cx+dx+sgn*int(42*sc)-16,ay-82,cx+dx+sgn*int(42*sc)+16,ay-50],fill=pele)
        elif pose=="costas":
            draw.line([cx+dx,ay,cx,ay+int(22*sc)],fill=pele,width=int(22*sc))
        else:
            draw.line([cx+dx,ay,cx+dx+sgn*int(28*sc),ay+int(42*sc)],fill=pele,width=int(22*sc))
            draw.ellipse([cx+dx+sgn*16-16,ay+28,cx+dx+sgn*16+16,ay+56],fill=pele)
    draw.rectangle([cx-int(16*sc),cy-bh-int(14*sc),cx+int(16*sc),cy-bh+int(10*sc)],fill=pele)
    hx,hy=cx,cy-bh-hr+int(12*sc)
    draw.ellipse([hx-hr,hy-hr,hx+hr,hy+hr],fill=pele)
    draw.ellipse([hx-hr-7,hy-18,hx-hr+12,hy+18],fill=sp)
    draw.ellipse([hx+hr-12,hy-18,hx+hr+7,hy+18],fill=sp)
    # Cabelo CURTO masculino
    draw.ellipse([hx-hr-4,hy-hr-5,hx+hr+4,hy-int(hr*0.28)],fill=cab)
    rosto_masc(draw,hx,hy,hr,pele,expr)

def rosto_masc(draw,cx,cy,hr,pele,expr):
    sob=cy-int(hr*0.55);oy=cy-int(hr*0.18)
    ew,eh=int(hr*0.23),int(hr*0.26)
    for sgn in[-1,1]:
        ex=cx+sgn*int(hr*0.38)
        if expr in["bravo","frustrado"]:
            draw.line([(ex-int(hr*0.23),sob-int(hr*0.10)*sgn),(ex+int(hr*0.23),sob+int(hr*0.10)*sgn)],fill=ES,width=int(hr*0.13))
        elif expr in["triste","exausto","choro"]:
            draw.line([(ex-int(hr*0.23),sob+int(hr*0.10)*sgn),(ex+int(hr*0.23),sob-int(hr*0.10)*sgn)],fill=ES,width=int(hr*0.11))
        elif expr=="surpresa":
            draw.arc([ex-int(hr*0.23),sob-int(hr*0.15),ex+int(hr*0.23),sob+int(hr*0.05)],0,180,fill=ES,width=int(hr*0.10))
        else:
            draw.line([(ex-int(hr*0.21),sob),(ex+int(hr*0.21),sob)],fill=ES,width=int(hr*0.09))
        draw.ellipse([ex-ew,oy-eh,ex+ew,oy+eh],fill=BR)
        draw.ellipse([ex-int(hr*0.14),oy-int(hr*0.16),ex+int(hr*0.14),oy+int(hr*0.16)],fill=(55,40,30))
        draw.ellipse([ex-int(hr*0.08),oy-int(hr*0.09),ex+int(hr*0.08),oy+int(hr*0.09)],fill=ES)
        draw.ellipse([ex+int(hr*0.05),oy-int(hr*0.13),ex+int(hr*0.11),oy-int(hr*0.07)],fill=BR)
        # Cílios mais curtos (masculino)
        for k in range(4):
            ang=math.radians(-65+k*43)
            draw.line([int(ex+ew*math.cos(ang)),int(oy-eh*math.sin(ang)),
                       int(ex+(ew+7)*math.cos(ang)),int(oy-(eh+8)*math.sin(ang))],fill=ES,width=2)
        if expr=="exausto":
            draw.line([ex-ew,oy,ex+ew,oy],fill=ES,width=int(hr*0.17))
    draw.ellipse([cx-7,cy+int(hr*0.06),cx+7,cy+int(hr*0.13)],fill=tuple(max(0,c-28) for c in pele))
    my=cy+int(hr*0.32);bw2=int(hr*0.40)
    if expr in["feliz","sorriso_falso"]:
        draw.arc([cx-bw2,my-int(hr*0.22),cx+bw2,my+int(hr*0.22)],0,180,fill=ES,width=int(hr*0.10))
        if expr=="sorriso_falso":
            draw.arc([cx-bw2+6,my-int(hr*0.18),cx+bw2-6,my+int(hr*0.18)],10,170,fill=BR,width=int(hr*0.06))
    elif expr in["triste","choro"]:
        draw.arc([cx-bw2,my-int(hr*0.10),cx+bw2,my+int(hr*0.25)],180,0,fill=ES,width=int(hr*0.10))
        if expr=="choro":
            draw.polygon([(cx-24,my-19),(cx-33,my+7),(cx-15,my+7)],fill=(80,150,255))
    elif expr=="surpresa":
        draw.ellipse([cx-22,my-19,cx+22,my+19],fill=ES)
    elif expr=="falando":
        draw.arc([cx-27,my-15,cx+27,my+15],0,180,fill=ES,width=int(hr*0.09))
        draw.rounded_rectangle([cx-19,my-5,cx+19,my+5],radius=4,fill=BR)
    elif expr=="exausto":
        draw.line([cx-23,my+5,cx+23,my],fill=ES,width=int(hr*0.09))
    elif expr in["bravo","frustrado"]:
        draw.arc([cx-bw2+12,my-6,cx+bw2-12,my+30],180,0,fill=ES,width=int(hr*0.11))
    else:
        draw.line([cx-23,my,cx+23,my],fill=ES,width=int(hr*0.09))

# ────────────── PROPS ──────────────
def prop_interrogacao(draw,cx,cy,cor,sc=1.2):
    draw.text((cx-int(28*sc),cy-int(40*sc)),"?",fill=cor)

def prop_celular(draw,cx,cy,sc=1.0):
    # Celular flat design
    pw,ph=int(50*sc),int(90*sc)
    draw.rounded_rectangle([cx-pw//2,cy-ph//2,cx+pw//2,cy+ph//2],radius=12,fill=(40,40,55))
    draw.rounded_rectangle([cx-pw//2+4,cy-ph//2+10,cx+pw//2-4,cy+ph//2-8],radius=6,fill=(80,170,255))
    # Tela com sinal de "ouvindo"
    draw.ellipse([cx-14,cy-8,cx+14,cy+12],fill=(255,100,100))
    draw.text((cx-6,cy-3),"♪",fill=BR)
    draw.ellipse([cx-5,cy+ph//2-6,cx+5,cy+ph//2-2],fill=(120,120,140))

def prop_megafone_X(draw,cx,cy,sc=1.0):
    # Megafone
    bx,by=int(45*sc),int(30*sc)
    draw.polygon([(cx-bx,cy-by//2),(cx,cy-by),(cx,cy+by),(cx-bx,cy+by//2)],fill=AM)
    draw.arc([cx,cy-int(40*sc),cx+int(50*sc),cy+int(40*sc)],270,90,fill=AM,width=int(12*sc))
    # X vermelho em cima
    draw.line([(cx+int(15*sc),cy-int(40*sc)),(cx+int(45*sc),cy-int(10*sc))],fill=VERM,width=int(8*sc))
    draw.line([(cx+int(45*sc),cy-int(40*sc)),(cx+int(15*sc),cy-int(10*sc))],fill=VERM,width=int(8*sc))

def prop_alianca(draw,cx,cy,sc=1.0):
    r=int(28*sc)
    draw.ellipse([cx-r,cy-r,cx+r,cy+r],outline=AM,width=int(10*sc))
    draw.ellipse([cx-int(r*0.5),cy-int(r*0.5),cx+int(r*0.5),cy+int(r*0.5)],fill=AM)

def prop_espiral(draw,cx,cy,sc=1.0):
    for k in range(80):
        t=k/80.0;r=int(80*sc)*t;ang=t*4*2*math.pi
        x1=int(cx+r*math.cos(ang));y1=int(cy+r*math.sin(ang))
        r2=int(80*sc)*(t+0.015);x2=int(cx+r2*math.cos(ang+0.3));y2=int(cy+r2*math.sin(ang+0.3))
        draw.line([(x1,y1),(x2,y2)],fill=VERM,width=4)

def prop_trofeu(draw,cx,cy,sc=1.0):
    pts=[(cx-int(50*sc),cy-int(100*sc)),(cx+int(50*sc),cy-int(100*sc)),
         (cx+int(62*sc),cy-int(50*sc)),(cx,cy),(cx-int(62*sc),cy-int(50*sc))]
    draw.polygon(pts,fill=AM)
    draw.rectangle([cx-int(20*sc),cy-14,cx+int(20*sc),cy+28],fill=AM)
    draw.rectangle([cx-int(38*sc),cy+28,cx+int(38*sc),cy+42],fill=AM)
    draw.ellipse([cx-int(28*sc),cy-int(96*sc),cx-int(8*sc),cy-int(76*sc)],fill=(255,248,160))

def prop_coracao(draw,cx,cy,r=45,cor=None,partido=False):
    if cor is None: cor=VERM
    draw.ellipse([cx-r,cy-r//2,cx,cy+r//2],fill=cor)
    draw.ellipse([cx,cy-r//2,cx+r,cy+r//2],fill=cor)
    draw.polygon([(cx-r,cy),(cx,cy+int(r*1.25)),(cx+r,cy)],fill=cor)
    if partido:
        draw.line([(cx-4,cy-r//2),(cx+5,cy+int(r*1.1))],fill=BR,width=7)

def prop_badge(draw,cx,cy,txt,cor=None,larg=None):
    if cor is None: cor=VERM
    l=len(txt)*13+30 if larg is None else larg
    draw.rounded_rectangle([cx-l//2,cy-26,cx+l//2,cy+26],radius=14,fill=cor)
    draw.text((cx-l//2+15,cy-10),txt,fill=BR)

def prop_sino(draw,cx,cy,sc=1.0):
    draw.arc([cx-int(70*sc),cy-int(70*sc),cx+int(70*sc),cy+int(20*sc)],180,0,fill=AM,width=int(14*sc))
    draw.rectangle([cx-int(68*sc),cy-int(5*sc),cx+int(68*sc),cy+int(10*sc)],fill=AM)
    draw.ellipse([cx-int(14*sc),cy+int(10*sc)-6,cx+int(14*sc),cy+int(10*sc)+14],fill=AM)

def prop_cerebro(draw,cx,cy,sc=1.0):
    draw.ellipse([cx-int(60*sc),cy-int(50*sc),cx+int(40*sc),cy+int(30*sc)],fill=(220,150,160))
    draw.ellipse([cx-int(10*sc),cy-int(55*sc),cx+int(55*sc),cy+int(20*sc)],fill=(200,130,140))
    draw.arc([cx-int(30*sc),cy-int(20*sc),cx+int(20*sc),cy+int(20*sc)],180,0,fill=(180,100,120),width=int(7*sc))

def prop_peso(draw,cx,cy,sc=1.0):
    """Setas de peso caindo"""
    for x in[cx-90,cx+90]:
        draw.line([(x,cy-30),(x,cy+20)],fill=VERM,width=8)
        draw.polygon([(x-12,cy+20),(x+12,cy+20),(x,cy+38)],fill=VERM)

def prop_mascara(draw,cx,cy,sc=1.0):
    draw.ellipse([cx-int(80*sc),cy-int(40*sc),cx+int(80*sc),cy+int(40*sc)],fill=(240,225,145),outline=AM,width=5)
    draw.arc([cx-int(34*sc),cy-int(8*sc),cx+int(34*sc),cy+int(28*sc)],0,180,fill=(180,30,30),width=7)
    for sgn in[-1,1]:
        draw.ellipse([cx+sgn*int(30*sc)-12,cy-int(18*sc),cx+sgn*int(30*sc)+12,cy+int(5*sc)],fill=(30,20,10))

def prop_coracao_X(draw,cx,cy):
    prop_coracao(draw,cx,cy,r=50,cor=(80,80,120))
    draw.line([(cx-35,cy-35),(cx+35,cy+35)],fill=VERM,width=10)

def prop_olho_ouvido(draw,cx,cy):
    # Olho
    draw.ellipse([cx-130,cy-35,cx-30,cy+35],fill=BR,outline=ES,width=5)
    draw.ellipse([cx-100,cy-22,cx-60,cy+22],fill=(55,40,30))
    draw.ellipse([cx-90,cy-12,cx-70,cy+12],fill=ES)
    # Ouvido
    draw.arc([cx+30,cy-35,cx+130,cy+35],270,90,fill=(222,175,132),width=16)
    draw.arc([cx+50,cy-20,cx+110,cy+20],270,90,fill=(222,175,132),width=10)

def prop_check(draw,cx,cy,cor,sc=1.0):
    r=int(55*sc)
    draw.ellipse([cx-r,cy-r,cx+r,cy+r],fill=cor)
    # Check mark
    pts=[(cx-int(30*sc),cy),(cx-int(10*sc),cy+int(22*sc)),(cx+int(30*sc),cy-int(22*sc))]
    for i in range(len(pts)-1):
        draw.line([pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1]],fill=BR,width=int(9*sc))

def prop_celular_envio(draw,cx,cy):
    prop_celular(draw,cx-60,cy)
    draw.line([(cx-10,cy),(cx+80,cy)],fill=AM,width=7)
    draw.polygon([(cx+80,cy-12),(cx+80,cy+12),(cx+105,cy)],fill=AM)

GND=int(H*0.70)
CX=W//2

# ──────────────── 21 CENAS ────────────────
# (frase, dur_s, palette_idx)
# Timing: 12.77 chars/s (829 chars / 64.9s audio)
CENAS_DEF = [
    # idx, frase, dur, pal, fn_cena
    (1,  "Voce acha que reconheceria um narcisista?", 3.29, 0),
    (2,  "9 em 10 pessoas nao reconhecem.",           2.51, 1),
    (3,  "O narcisismo encoberto nao grita.",         2.59, 2),
    (4,  "Ele sussurra.",                             1.02, 2),
    (5,  "Renata, 34, designer, casada com Lucas.",   3.13, 3),
    (6,  "Por fora perfeito.",                        1.41, 3),
    (7,  "Por dentro ela enlouquecia.",               2.11, 4),
    (8,  "Aguarda. Isso e mais comum do que parece.", 3.21, 5),
    (9,  "Sinal 1: Ele esquece tudo que voce fala",  3.13, 5),
    (10, "mas lembra quando precisa te culpar.",      2.82, 1),
    (11, "Sinal 2: Suas conquistas viram historia dele.", 3.60, 6),
    (12, "Sinal 3: Voce sai exausta e sempre sentindo que errou.", 4.31, 7),
    (13, "Dr. Ramani - UCLA: dreno emocional sistematico.", 3.76, 8),
    (14, "E real. Nao e exagero.",                   1.80, 8),
    (15, "Isso nao e amor dificil.",                  1.88, 9),
    (16, "E manipulacao com rosto gentil.",            2.43, 9),
    (17, "Manda esse video pra quem precisa.",        2.66, 2),
    (18, "Inscreva-se.",                              0.94, 11),
    (19, "Voce merece um amor que nao esgota.",       2.82, 10),
    (20, "Que nao confunde. Um amor que te ve e te ouve.", 3.68, 10),
    (21, "CTA final — proximo episodio",              5.39, 11),  # resto
]

def draw_cena(idx, pal_idx):
    ct,cb,ac=PALS[pal_idx]
    img=Image.new("RGB",(W,H))
    draw=ImageDraw.Draw(img)
    fundo(draw,ct,cb)
    geo(draw,ac,7,idx*11)

    if idx==1:
        # Renata com ? gigante — "reconheceria um narcisista?"
        boneca(draw,CX-80,GND,PR_F,CR_F,RR_F,"surpresa","pe",1.55)
        prop_interrogacao(draw,CX+130,int(H*0.28),ac,1.8)
        # Espelho simplificado
        draw.rounded_rectangle([CX+170,int(H*0.32),CX+260,int(H*0.48)],radius=15,fill=(120,120,150))
        draw.rounded_rectangle([CX+175,int(H*0.325),CX+255,int(H*0.475)],radius=12,fill=(180,200,220))

    elif idx==2:
        # 3 bonecos em fila — 1 narcisista circulado
        boneca(draw,CX-240,GND,(225,178,130),(148,95,40),(80,160,80),"neutro","pe",1.1)
        boneco(draw,CX,GND,(190,142,95),(62,36,15),(80,80,80),"neutro","pe",1.1)
        boneco(draw,CX+240,GND,PR_M,CR_M,RL_M,"sorriso_falso","pe",1.1)
        draw.ellipse([CX+180,GND-225,CX+305,GND-35],outline=BR,width=8)
        draw.text((CX-55,int(H*0.24)),"9/10",fill=BR)

    elif idx==3:
        # Megafone rasurado — "nao grita"
        prop_megafone_X(draw,CX,int(H*0.40),sc=1.4)
        boneco(draw,CX-50,GND,PR_M,CR_M,RL_M,"neutro","pe",1.0)

    elif idx==4:
        # Lucas com dedo nos labios + bolhas sussurro — "ele sussurra"
        boneco(draw,CX,GND,PR_M,CR_M,RL_M,"sorriso_falso","pe",1.6)
        for k,(bx,by,r) in enumerate([(CX+150,int(H*0.42),18),(CX+202,int(H*0.38),24),(CX+262,int(H*0.34),33)]):
            draw.ellipse([bx-r,by-r,bx+r,by+r],outline=ac,width=4)
        draw.text((CX+228,int(H*0.28)),"shhh",fill=ac)

    elif idx==5:
        # Renata+Lucas juntos com alianca/coracao — "casada com Lucas"
        boneca(draw,CX-120,GND,PR_F,CR_F,RR_F,"feliz","pe",1.3)
        boneco(draw,CX+130,GND,PR_M,CR_M,RL_M,"sorriso_falso","pe",1.3)
        prop_alianca(draw,CX,int(H*0.36),1.0)
        prop_coracao(draw,CX,int(H*0.22),r=35)

    elif idx==6:
        # Lucas sorrindo com estrela dourada — "por fora perfeito"
        boneco(draw,CX,GND,PR_M,CR_M,RL_M,"sorriso_falso","pe",1.65)
        for ang in[0,60,120,180,240,300]:
            rad=math.radians(ang);r=130
            draw.line([int(CX+r*math.cos(rad)),int(GND-250+r*math.sin(rad)),
                       int(CX+(r+40)*math.cos(rad)),int(GND-250+(r+40)*math.sin(rad))],fill=AM,width=7)
        draw.ellipse([CX-35,GND-285,CX+35,GND-215],fill=AM)
        draw.ellipse([CX-20,GND-270,CX+20,GND-230],fill=(255,248,160))

    elif idx==7:
        # Renata enlouquecendo com espiral — "por dentro ela enlouquecia"
        boneca(draw,CX,GND,PR_F,CR_F,RR_F,"confuso","pe",1.55)
        prop_espiral(draw,CX,int(H*0.40))
        draw.polygon([(CX+130,int(H*0.36)),(CX+120,int(H*0.42)),(CX+140,int(H*0.42))],fill=(80,150,255))

    elif idx==8:
        # Mao STOP + 3 silhuetas — "mais comum do que parece"
        boneca(draw,CX-220,GND,PR_F,CR_F,RR_F,"surpresa","pe",1.0)
        boneco(draw,CX-80,GND,PR_M,CR_M,(120,120,120),"neutro","pe",0.9)
        boneco(draw,CX+60,GND,(200,150,100),(80,50,20),(120,80,50),"neutro","pe",0.9)
        # Mao STOP grande
        draw.rounded_rectangle([CX+160,int(H*0.30),CX+280,int(H*0.48)],radius=25,fill=(255,220,180))
        draw.text((CX+172,int(H*0.35)),"STOP",fill=VERM)
        draw.rectangle([CX+184,int(H*0.36),CX+256,int(H*0.46)],fill=(255,230,200))

    elif idx==9:
        # SINAL 1 + Renata falando com balao vazio
        prop_badge(draw,CX-100,int(H*0.22),"SINAL  1",cor=VERM,larg=200)
        boneca(draw,CX-130,GND,PR_F,CR_F,RR_F,"falando","pe",1.3)
        draw.rounded_rectangle([CX-260,int(H*0.37),CX-60,int(H*0.47)],radius=20,fill=BR)

    elif idx==10:
        # Lucas de costas com seta de culpa
        boneca(draw,CX-130,GND,PR_F,CR_F,RR_F,"triste","pe",1.2)
        boneco(draw,CX+130,GND,PR_M,CR_M,RL_M,"bravo","costas",1.2)
        # Balao de Renata com X
        draw.rounded_rectangle([CX-260,int(H*0.37),CX-60,int(H*0.47)],radius=20,fill=BR)
        draw.line([(CX-195,int(H*0.40)),(CX-125,int(H*0.44))],fill=VERM,width=9)
        draw.line([(CX-125,int(H*0.40)),(CX-195,int(H*0.44))],fill=VERM,width=9)
        # Seta de culpa apontando para Renata
        draw.line([(CX+80,int(H*0.35)),(CX-80,int(H*0.35))],fill=VERM,width=6)
        draw.polygon([(CX-80,int(H*0.35)-10),(CX-80,int(H*0.35)+10),(CX-105,int(H*0.35))],fill=VERM)

    elif idx==11:
        # SINAL 2 + Trofeu + Lucas apontando
        prop_badge(draw,CX-100,int(H*0.22),"SINAL  2",cor=(160,50,0),larg=200)
        prop_trofeu(draw,CX,int(H*0.40),1.3)
        boneco(draw,CX+185,GND,PR_M,CR_M,RL_M,"sorriso_falso","apontando",1.15)
        boneca(draw,CX-185,GND,PR_F,CR_F,RR_F,"triste","pe",1.05)

    elif idx==12:
        # SINAL 3 + Renata exausta com peso visual
        prop_badge(draw,CX-100,int(H*0.22),"SINAL  3",cor=(90,25,140),larg=200)
        boneca(draw,CX,GND,PR_F,CR_F,RR_F,"exausto","pe",1.55)
        prop_peso(draw,CX,int(H*0.40))
        draw.polygon([(CX+100,int(H*0.44)),(CX+89,int(H*0.50)),(CX+111,int(H*0.50))],fill=(80,160,255))

    elif idx==13:
        # Dr. Ramani jaleco + cerebro drenando
        boneco(draw,CX-90,GND,PR_J,CR_J,RJ,"neutro","pe",1.28)
        prop_cerebro(draw,CX+110,int(H*0.33))
        draw.line([(CX+150,int(H*0.44)),(CX+150,int(H*0.55))],fill=VERM,width=9)
        draw.polygon([(CX+138,int(H*0.55)),(CX+162,int(H*0.55)),(CX+150,int(H*0.59))],fill=VERM)
        prop_badge(draw,CX+145,int(H*0.62),"Dr. Ramani UCLA",cor=(0,80,80),larg=290)

    elif idx==14:
        # Check verde — "E real"
        prop_check(draw,CX,int(H*0.38),(20,160,80))
        boneca(draw,CX-30,GND,PR_F,CR_F,RR_F,"surpresa","pe",1.2)

    elif idx==15:
        # Coracao partido — "nao e amor dificil"
        prop_coracao_X(draw,CX,int(H*0.38))
        draw.text((CX-38,int(H*0.50)),"amor?",fill=ac)

    elif idx==16:
        # Lucas com mascara + face mal — "manipulacao rosto gentil"
        boneco(draw,CX,GND,PR_M,CR_M,RL_M,"sorriso_falso","pe",1.65)
        prop_mascara(draw,CX,int(H*0.31))

    elif idx==17:
        # Celular enviando — "manda esse video"
        prop_celular_envio(draw,CX,int(H*0.38))
        boneca(draw,CX-140,GND,PR_F,CR_F,RR_F,"feliz","apontando",1.2)

    elif idx==18:
        # Sino grande + ψ — "inscreva-se"
        prop_sino(draw,CX,int(H*0.32))
        boneca(draw,CX+20,GND,PR_F,CR_F,RR_F,"feliz","pe",1.45)
        prop_badge(draw,CX,int(H*0.18),"Inscreva-se AGORA!",cor=VERM,larg=380)

    elif idx==19:
        # Renata feliz com corações — "amor que nao esgota"
        boneca(draw,CX,GND,PR_F,CR_F,RR_F,"feliz","pe",1.65)
        for ro,cor2 in[(95,(220,55,55)),(140,(255,90,90)),(180,(255,160,160))]:
            for ang in[0,60,120,180,240,300]:
                rad=math.radians(ang)
                hx2=int(CX+ro*math.cos(rad));hy2=int(GND-215+ro*math.sin(rad))
                r2=max(6,int(22*(1-ro/220)))
                prop_coracao(draw,hx2,hy2,r=r2,cor=cor2)

    elif idx==20:
        # Olho + Ouvido — "te ve e te ouve"
        prop_olho_ouvido(draw,CX,int(H*0.38))
        boneca(draw,CX,GND,PR_F,CR_F,RR_F,"surpresa","pe",1.3)

    elif idx==21:
        # CTA final — psi + PROXIMO EPISODIO + sino
        prop_sino(draw,CX+130,int(H*0.24),1.2)
        draw.text((CX-52,int(H*0.22)),"psi",fill=ac)
        boneca(draw,CX,GND,PR_F,CR_F,RR_F,"feliz","pe",1.55)
        prop_badge(draw,CX,int(H*0.18),"Proximo Episodio",cor=(160,50,0),larg=360)
        prop_badge(draw,CX,int(H*0.13),"Inscreva-se Agora",cor=VERM,larg=360)

    lt(draw)
    p=f"/tmp/v7/cena{idx:02d}.jpg"
    img.save(p,"JPEG",quality=93)
    print(f"  [{idx:02d}] {CENAS_DEF[idx-1][1][:40]}")
    return p

print("=== RENDER V7: 21 CENAS PRECISAS | FEMININO | SEM DELAY ===")
imgs=[]
for idx,frase,dur,pal in CENAS_DEF:
    imgs.append((draw_cena(idx,pal), dur))
print("Cenas geradas!")

# AUDIO
r=requests.get(f"{SB_URL}/rest/v1/content_pipeline",params={"select":"audio_url","id":"eq.683"},
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"})
audio_url=r.json()[0]["audio_url"]
r2=requests.get(audio_url,headers={"apikey":SB_KEY},timeout=90)
with open("/tmp/v7/audio.mp3","wb") as f: f.write(r2.content)
probe=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",
    "/tmp/v7/audio.mp3"],capture_output=True,text=True)
ADU=float(json.loads(probe.stdout)["format"]["duration"])
print(f"Audio: {ADU:.1f}s")

# FFCONCAT — cada cena com duracao exata da frase
with open("/tmp/v7/concat.txt","w") as f:
    for img_path,dur in imgs:
        f.write(f"file '{img_path}'\n")
        f.write(f"duration {dur:.3f}\n")
    # Ultimo frame
    f.write(f"file '{imgs[-1][0]}'\n")
print("ffconcat pronto")

# RENDER
print("Renderizando...")
cmd=["ffmpeg","-y",
     "-f","concat","-safe","0","-i","/tmp/v7/concat.txt",
     "-i","/tmp/v7/audio.mp3",
     "-c:v","libx264","-pix_fmt","yuv420p",
     "-c:a","aac","-b:a","128k",
     "-shortest","-r","25","-crf","18",
     "-vf","eq=saturation=1.18:brightness=0.02:contrast=1.06",
     "-movflags","+faststart",
     "/tmp/v7/viral_v7.mp4"]
res=subprocess.run(cmd,capture_output=True,text=True,timeout=480)
if res.returncode!=0: print("ERRO:"); print(res.stderr[-2000:]); exit(1)

sz=os.path.getsize("/tmp/v7/viral_v7.mp4")
probe2=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",
    "/tmp/v7/viral_v7.mp4"],capture_output=True,text=True)
dur2=float(json.loads(probe2.stdout)["format"]["duration"])
print(f"MP4: {sz//1024}KB | {dur2:.1f}s")

fname=f"mp4s/v683_viral_v7_{int(time.time())}.mp4"
with open("/tmp/v7/viral_v7.mp4","rb") as f: data=f.read()
mp4_url=None
for t in range(6):
    r3=requests.post(f"{SB_URL}/storage/v1/object/videos/{fname}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"video/mp4","x-upsert":"true"},
        data=data,timeout=420)
    if r3.status_code in[200,201]:
        mp4_url=f"{SB_URL}/storage/v1/object/public/videos/{fname}"
        print(f"Upload OK"); break
    print(f"  upload {t+1}: {r3.status_code}"); time.sleep(6)

if mp4_url:
    r4=requests.patch(f"{SB_URL}/rest/v1/content_pipeline?id=eq.683",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"},
        data=json.dumps({"mp4_url":mp4_url,"status":"pending_credentials",
                         "metadata":{"render_version":"v7_feminino_timing_preciso",
                                     "n_cenas":21,"ffconcat":True,
                                     "personagem_feminino":True,"sem_delay":True}}),timeout=30)
    print(f"DB: {r4.status_code} — {mp4_url[-55:]}")
print("Concluido!")
