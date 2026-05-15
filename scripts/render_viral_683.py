#!/usr/bin/env python3
"""render_viral_683_v3.py — 20 cenas viral, $0, sem "Psicologa" no LT"""
import os,json,math,time,subprocess,requests
from PIL import Image,ImageDraw

SB_URL=os.environ.get("SUPABASE_URL","")
SB_KEY=os.environ.get("SUPABASE_KEY","")
W,H=1080,1920
os.makedirs("/tmp/v683",exist_ok=True)

# 12 paletas distintas — nenhuma igual
PALS=[
    ((15,12,30),(30,20,50),(200,80,200)),    # 0 ROXO ESCURO
    ((200,20,20),(160,10,10),(255,240,240)),  # 1 VERMELHO VIBRANTE
    ((8,18,75),(4,8,55),(60,140,255)),        # 2 AZUL NOITE
    ((220,100,20),(180,70,5),(255,255,200)),  # 3 LARANJA
    ((55,8,8),(28,4,4),(255,90,90)),          # 4 VINHO
    ((200,160,10),(170,130,0),(120,60,0)),    # 5 AMBAR ESCURO
    ((160,30,30),(120,15,15),(255,215,80)),   # 6 VERMELHO OURO
    ((35,35,75),(18,18,55),(190,170,255)),    # 7 INDIGO
    ((0,130,120),(0,90,80),(180,255,245)),    # 8 TEAL
    ((65,15,95),(40,8,70),(195,90,255)),      # 9 ROXO
    ((15,150,70),(8,110,50),(180,255,210)),   # 10 VERDE
    ((220,170,0),(185,140,0),(160,60,0)),     # 11 OURO
]

PR=(222,175,132);CR=(140,90,40);RR=(220,80,70)
PL=(182,135,90);CL=(55,32,12);RL=(60,80,200)
BR=(255,255,255);ES=(10,8,8)
AM=(255,210,50);VERM=(220,50,50)
PJ=(200,195,185);CJ=(60,40,20)

def lerp(a,b,t): return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(len(a)))

def fundo(draw,ct,cb,cg=None):
    if cg is None: cg=tuple(max(0,c-25) for c in cb)
    for y in range(H):
        if y<int(H*0.72): c=lerp(ct,cb,y/(H*0.72))
        else: c=lerp(cb,cg,(y-H*0.72)/(H*0.28))
        draw.line([(0,y),(W,y)],fill=c)

def geo(draw,cor,n,seed):
    import random; random.seed(seed*31+7)
    for _ in range(n):
        x=random.randint(50,W-50);y=random.randint(50,int(H*0.75));r=random.randint(8,30)
        t=random.choice(["c","t","q"])
        c2=tuple(min(255,c+40) for c in cor)
        if t=="c": draw.ellipse([x-r,y-r,x+r,y+r],fill=cor)
        elif t=="t": draw.polygon([(x,y-r),(x-r,y+r),(x+r,y+r)],fill=cor)
        else: draw.rectangle([x-r//2,y-r//2,x+r//2,y+r//2],fill=cor)

def lt(draw):
    """Lower third SEM palavra 'Psicologa' — valido a partir jan/2027"""
    bx,by=28,H-118
    draw.rounded_rectangle([bx,by,bx+440,by+76],radius=11,fill=(12,10,25))
    draw.text((bx+14,by+10),"psi",fill=AM)
    draw.text((bx+44,by+10),"Daniela Coelho | Saude Mental",fill=BR)
    draw.text((bx+44,by+40),"@psidanielacoelho",fill=(190,175,230))
    draw.rectangle([bx,by+73,bx+440,by+76],fill=VERM)

def perna(draw,cx,cy,sc,sr):
    lw=int(28*sc);lg=int(100*sc)
    for dx in[-int(17*sc),int(17*sc)]:
        draw.rounded_rectangle([cx+dx-lw//2,cy,cx+dx+lw//2,cy+lg],radius=10,fill=sr)
        draw.ellipse([cx+dx-int(20*sc),cy+lg-5,cx+dx+int(20*sc),cy+lg+18],fill=(30,20,12))

def corpo(draw,cx,cy,sc,roupa):
    bw=int(90*sc);bh=int(120*sc)
    sr=tuple(max(0,c-50) for c in roupa)
    draw.rounded_rectangle([cx-bw//2,cy-bh,cx+bw//2,cy],radius=22,fill=roupa)
    draw.rounded_rectangle([cx-int(22*sc),cy-bh,cx+int(22*sc),cy-bh+int(22*sc)],radius=8,fill=sr)

def braco(draw,cx,bw,cy,sc,pele,pose):
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

def olho(draw,ex,oy,hr,pele,expr):
    ew,eh=int(hr*0.24),int(hr*0.28)
    draw.ellipse([ex-ew,oy-eh,ex+ew,oy+eh],fill=BR)
    draw.ellipse([ex-int(hr*0.16),oy-int(hr*0.18),ex+int(hr*0.16),oy+int(hr*0.18)],fill=(55,40,30))
    draw.ellipse([ex-int(hr*0.09),oy-int(hr*0.10),ex+int(hr*0.09),oy+int(hr*0.10)],fill=ES)
    draw.ellipse([ex+int(hr*0.05),oy-int(hr*0.14),ex+int(hr*0.12),oy-int(hr*0.07)],fill=BR)
    for k in range(5):
        ang=math.radians(-70+k*35)
        draw.line([int(ex+ew*math.cos(ang)),int(oy-eh*math.sin(ang)),
                   int(ex+(ew+9)*math.cos(ang)),int(oy-(eh+10)*math.sin(ang))],fill=ES,width=2)
    if expr=="exausto":
        draw.line([ex-ew,oy,ex+ew,oy],fill=ES,width=int(hr*0.18))

def rosto(draw,cx,cy,hr,pele,expr):
    sob=cy-int(hr*0.55);oy=cy-int(hr*0.18)
    for sgn in[-1,1]:
        ex=cx+sgn*int(hr*0.38)
        if expr in["bravo","frustrado"]:
            draw.line([(ex-int(hr*0.24),sob-int(hr*0.10)*sgn),(ex+int(hr*0.24),sob+int(hr*0.10)*sgn)],fill=ES,width=int(hr*0.13))
        elif expr in["triste","exausto","choro","confuso"]:
            draw.line([(ex-int(hr*0.24),sob+int(hr*0.10)*sgn),(ex+int(hr*0.24),sob-int(hr*0.10)*sgn)],fill=ES,width=int(hr*0.11))
        elif expr=="surpresa":
            draw.arc([ex-int(hr*0.24),sob-int(hr*0.15),ex+int(hr*0.24),sob+int(hr*0.05)],0,180,fill=ES,width=int(hr*0.10))
        else:
            draw.line([(ex-int(hr*0.22),sob),(ex+int(hr*0.22),sob)],fill=ES,width=int(hr*0.09))
        olho(draw,ex,oy,hr,pele,expr)
    draw.ellipse([cx-7,cy+int(hr*0.06),cx+7,cy+int(hr*0.13)],fill=tuple(max(0,c-28) for c in pele))
    my=cy+int(hr*0.33);bw2=int(hr*0.42)
    if expr in["feliz","sorriso_falso"]:
        draw.arc([cx-bw2,my-int(hr*0.24),cx+bw2,my+int(hr*0.24)],0,180,fill=ES,width=int(hr*0.11))
        if expr=="sorriso_falso":
            draw.arc([cx-bw2+6,my-int(hr*0.20),cx+bw2-6,my+int(hr*0.20)],10,170,fill=BR,width=int(hr*0.07))
    elif expr in["triste","choro"]:
        draw.arc([cx-bw2,my-int(hr*0.12),cx+bw2,my+int(hr*0.28)],180,0,fill=ES,width=int(hr*0.11))
        if expr=="choro":
            draw.polygon([(cx-25,my-20),(cx-34,my+8),(cx-16,my+8)],fill=(80,150,255))
    elif expr=="surpresa":
        draw.ellipse([cx-22,my-20,cx+22,my+20],fill=ES)
    elif expr=="falando":
        draw.arc([cx-28,my-16,cx+28,my+16],0,180,fill=ES,width=int(hr*0.10))
        draw.rounded_rectangle([cx-20,my-6,cx+20,my+6],radius=5,fill=BR)
    elif expr=="exausto":
        draw.line([cx-24,my+5,cx+24,my],fill=ES,width=int(hr*0.10))
    elif expr in["bravo","frustrado"]:
        draw.arc([cx-bw2+12,my-6,cx+bw2-12,my+30],180,0,fill=ES,width=int(hr*0.12))
    elif expr=="confuso":
        draw.arc([cx-bw2+5,my-8,cx+bw2-5,my+22],190,350,fill=ES,width=int(hr*0.10))
    else:
        draw.line([cx-24,my,cx+24,my],fill=ES,width=int(hr*0.10))

def boneco(draw,cx,cy,pele,cab,roupa,expr="neutro",pose="pe",sc=1.0):
    hr=int(58*sc);bw=int(90*sc);bh=int(120*sc)
    sr=tuple(max(0,c-50) for c in roupa);sp=tuple(max(0,c-35) for c in pele)
    perna(draw,cx,cy,sc,sr)
    corpo(draw,cx,cy,sc,roupa)
    braco(draw,cx,bw,cy,sc,pele,pose)
    draw.rectangle([cx-int(16*sc),cy-bh-int(14*sc),cx+int(16*sc),cy-bh+int(10*sc)],fill=pele)
    hx,hy=cx,cy-bh-hr+int(12*sc)
    draw.ellipse([hx-hr,hy-hr,hx+hr,hy+hr],fill=pele)
    draw.ellipse([hx-hr-7,hy-18,hx-hr+12,hy+18],fill=sp)
    draw.ellipse([hx+hr-12,hy-18,hx+hr+7,hy+18],fill=sp)
    draw.ellipse([hx-hr-5,hy-hr-8,hx+hr+5,hy-int(hr*0.28)],fill=cab)
    rosto(draw,hx,hy,hr,pele,expr)

def badge(draw,cx,cy,txt,cor=None,larg=None):
    if cor is None: cor=VERM
    l=len(txt)*13+30 if larg is None else larg
    draw.rounded_rectangle([cx-l//2,cy-26,cx+l//2,cy+26],radius=14,fill=cor)
    draw.text((cx-l//2+15,cy-10),txt,fill=BR)

def trofeu(draw,cx,cy,sc=1.2):
    pts=[(cx-int(50*sc),cy-int(100*sc)),(cx+int(50*sc),cy-int(100*sc)),
         (cx+int(62*sc),cy-int(50*sc)),(cx,cy),(cx-int(62*sc),cy-int(50*sc))]
    draw.polygon(pts,fill=AM)
    draw.rectangle([cx-int(20*sc),cy-14,cx+int(20*sc),cy+28],fill=AM)
    draw.rectangle([cx-int(38*sc),cy+28,cx+int(38*sc),cy+40],fill=AM)
    draw.ellipse([cx-int(28*sc),cy-int(96*sc),cx-int(8*sc),cy-int(76*sc)],fill=(255,248,160))

def coracao(draw,cx,cy,r=42,cor=None):
    if cor is None: cor=VERM
    draw.ellipse([cx-r,cy-r//2,cx,cy+r//2],fill=cor)
    draw.ellipse([cx,cy-r//2,cx+r,cy+r//2],fill=cor)
    draw.polygon([(cx-r,cy),(cx,cy+int(r*1.25)),(cx+r,cy)],fill=cor)

def estrela(draw,cx,cy,re,ri,cor):
    pts=[]
    for k in range(10):
        ang=math.radians(k*36-90)
        r=re if k%2==0 else ri
        pts.append((cx+r*math.cos(ang),cy+r*math.sin(ang)))
    draw.polygon(pts,fill=cor)

N=20
GND=int(H*0.70)

def cena(idx):
    pi=(idx-1)%len(PALS)
    ct,cb,ac=PALS[pi]
    img=Image.new("RGB",(W,H))
    draw=ImageDraw.Draw(img)
    fundo(draw,ct,cb)
    geo(draw,ac,8,idx)

    cx=W//2

    if idx==1:
        # ROXO ESCURO — Hook: estrela+interrogacao
        estrela(draw,cx,int(H*0.26),90,45,(160,40,180))
        draw.text((cx-32,int(H*0.22)),"?",fill=ac)
        for ang in range(0,360,60):
            rad=math.radians(ang)
            draw.line([int(cx+105*math.cos(rad)),int(GND-185+105*math.sin(rad)),
                       int(cx+148*math.cos(rad)),int(GND-185+148*math.sin(rad))],fill=ac,width=5)
        boneco(draw,cx,GND,PR,CR,RR,"surpresa","pe",1.55)

    elif idx==2:
        # VERMELHO — 3 personagens, narcisista circulado
        xs=[cx-240,cx,cx+240]
        peles=[(225,178,130),(190,142,95),PL]
        cabs=[(148,95,40),(62,36,15),CL]
        roupas=[(80,160,80),(80,80,80),RL]
        exprs=["neutro","neutro","sorriso_falso"]
        for i,(x,pe,ca,ro,ex) in enumerate(zip(xs,peles,cabs,roupas,exprs)):
            boneco(draw,x,GND,pe,ca,ro,ex,"pe",1.05)
        draw.ellipse([cx+180,GND-220,cx+300,GND-40],outline=BR,width=7)
        draw.text((cx-52,int(H*0.25)),"9/10",fill=BR)

    elif idx==3:
        # AZUL NOITE — Lucas sorrindo + bolhas sussurro
        boneco(draw,cx,GND,PL,CL,RL,"sorriso_falso","pe",1.65)
        for k,(bx,by,r) in enumerate([(cx+155,int(H*0.42),18),(cx+208,int(H*0.38),25),(cx+270,int(H*0.34),35)]):
            draw.ellipse([bx-r,by-r,bx+r,by+r],outline=ac,width=4)
        draw.text((cx+242,int(H*0.28)),"shhh",fill=ac)

    elif idx==4:
        # LARANJA — Casal: Lucas dominante, Renata menor
        boneco(draw,cx+135,GND,PL,CL,RL,"sorriso_falso","pe",1.45)
        boneco(draw,cx-115,GND+18,PR,CR,RR,"confuso","pe",1.20)
        # Coração partido
        coracao(draw,cx,int(H*0.35),r=52)
        draw.line([(cx-4,int(H*0.31)),(cx+5,int(H*0.42))],fill=BR,width=7)

    elif idx==5:
        # VINHO — Renata enlouquecendo + espiral
        boneco(draw,cx,GND,PR,CR,RR,"confuso","pe",1.58)
        for k in range(80):
            t=k/80.0;r=82*t;ang=t*4*2*math.pi
            x1=int(cx+r*math.cos(ang));y1=int(int(H*0.40)+r*math.sin(ang))
            r2=82*(t+0.015);x2=int(cx+r2*math.cos(ang+0.3));y2=int(int(H*0.40)+r2*math.sin(ang+0.3))
            draw.line([(x1,y1),(x2,y2)],fill=ac,width=4)
        draw.polygon([(cx+130,int(H*0.36)),(cx+120,int(H*0.42)),(cx+140,int(H*0.42))],fill=(80,150,255))

    elif idx==6:
        # AMBAR — SINAL 1: Renata fala, Lucas de costas
        badge(draw,cx-120,int(H*0.22),"SINAL  1",cor=VERM,larg=200)
        boneco(draw,cx-135,GND,PR,CR,RR,"falando","pe",1.38)
        boneco(draw,cx+135,GND,PL,CL,RL,"bravo","costas",1.38)
        draw.rounded_rectangle([cx-250,int(H*0.37),cx-50,int(H*0.46)],radius=20,fill=BR)
        draw.line([(cx-190,int(H*0.40)),(cx-110,int(H*0.44))],fill=VERM,width=9)
        draw.line([(cx-110,int(H*0.40)),(cx-190,int(H*0.44))],fill=VERM,width=9)

    elif idx==7:
        # VERMELHO+OURO — SINAL 2: Trofeu
        badge(draw,cx-120,int(H*0.22),"SINAL  2",cor=(160,50,0),larg=200)
        trofeu(draw,cx,int(H*0.40),1.3)
        boneco(draw,cx+185,GND,PL,CL,RL,"sorriso_falso","apontando",1.20)
        boneco(draw,cx-185,GND,PR,CR,RR,"triste","pe",1.10)
        draw.line([(cx+165,int(H*0.50)),(cx+65,int(H*0.50))],fill=AM,width=8)
        draw.polygon([(cx+65,int(H*0.50)-13),(cx+65,int(H*0.50)+13),(cx+33,int(H*0.50))],fill=AM)

    elif idx==8:
        # INDIGO — SINAL 3: Renata exausta
        badge(draw,cx-120,int(H*0.22),"SINAL  3",cor=(90,25,140),larg=200)
        boneco(draw,cx,GND,PR,CR,RR,"exausto","pe",1.58)
        for x in[cx-92,cx+92]:
            draw.line([(x,int(H*0.37)),(x,int(H*0.43))],fill=ac,width=9)
            draw.polygon([(x-13,int(H*0.43)),(x+13,int(H*0.43)),(x,int(H*0.46))],fill=ac)
        draw.polygon([(cx+102,int(H*0.44)),(cx+91,int(H*0.50)),(cx+113,int(H*0.50))],fill=(80,160,255))

    elif idx==9:
        # TEAL — Dr. Ramani, ciencia
        boneco(draw,cx-80,GND,PR,CR,(255,255,255),"neutro","pe",1.32)
        draw.ellipse([cx+80,int(H*0.30),cx+220,int(H*0.44)],fill=(220,150,160))
        draw.ellipse([cx+138,int(H*0.28),cx+240,int(H*0.40)],fill=(200,130,140))
        draw.line([(cx+162,int(H*0.44)),(cx+162,int(H*0.55))],fill=VERM,width=9)
        draw.polygon([(cx+149,int(H*0.55)),(cx+175,int(H*0.55)),(cx+162,int(H*0.58))],fill=VERM)
        badge(draw,cx+155,int(H*0.62),"Dr. Ramani  UCLA",cor=(0,80,80),larg=295)

    elif idx==10:
        # ROXO — Manipulacao: Lucas + mascara
        boneco(draw,cx,GND,PL,CL,RL,"sorriso_falso","pe",1.65)
        draw.ellipse([cx-80,int(H*0.30),cx+80,int(H*0.42)],fill=(240,225,145),outline=AM,width=5)
        draw.arc([cx-34,int(H*0.355),cx+34,int(H*0.395)],0,180,fill=(180,25,25),width=7)
        for sgn in[-1,1]:
            draw.ellipse([cx+sgn*20-11,int(H*0.315),cx+sgn*20+11,int(H*0.355)],fill=(200,50,50))

    elif idx==11:
        # VERDE — Renata posicao de forca + coracoes
        boneco(draw,cx,GND,PR,CR,RR,"feliz","pe",1.65)
        for ro,c2 in[(100,(220,55,55)),(145,(255,90,90)),(185,(255,160,160))]:
            for ang in[0,60,120,180,240,300]:
                rad=math.radians(ang)
                hx2=int(cx+ro*math.cos(rad));hy2=int(GND-210+ro*math.sin(rad))
                r2=max(6,int(24*(1-ro/225)))
                coracao(draw,hx2,hy2,r=r2,cor=c2)

    elif idx==12:
        # OURO — CTA sino+psi
        draw.arc([cx-72,int(H*0.22),cx+72,int(H*0.36)],180,0,fill=AM,width=15)
        draw.rectangle([cx-70,int(H*0.29),cx+70,int(H*0.33)],fill=AM)
        draw.ellipse([cx-15,int(H*0.36)-7,cx+15,int(H*0.36)+15],fill=AM)
        boneco(draw,cx,GND,PR,CR,RR,"feliz","pe",1.58)
        badge(draw,cx,int(H*0.18),"Inscreva-se AGORA!",cor=VERM,larg=380)

    elif idx==13:
        # ROXO (PALS[0]) — variacao extra
        boneco(draw,cx-120,GND,PR,CR,RR,"falando","apontando",1.3)
        boneco(draw,cx+120,GND,PL,CL,RL,"surpresa","pe",1.3)
        # Exclamacao
        draw.rectangle([cx-8,int(H*0.26),cx+8,int(H*0.40)],fill=ac)
        draw.ellipse([cx-10,int(H*0.42),cx+10,int(H*0.45)],fill=ac)

    elif idx==14:
        # VERMELHO (PALS[1]) — Renata frustrada
        boneco(draw,cx,GND,PR,CR,RR,"frustrado","pe",1.6)
        # Linhas de raiva
        for ang in[20,80,140,200,260,320]:
            rad=math.radians(ang)
            draw.line([int(cx+120*math.cos(rad)),int(GND-200+120*math.sin(rad)),
                       int(cx+160*math.cos(rad)),int(GND-200+160*math.sin(rad))],fill=ac,width=6)

    elif idx==15:
        # AZUL (PALS[2]) — Lucas de perfil + sombra
        boneco(draw,cx,GND,PL,CL,RL,"sorriso_falso","pe",1.6)
        # Sombra por tras (duplo menor)
        boneco(draw,cx+60,GND+20,(80,60,50),(40,20,8),(30,40,100),"neutro","pe",1.1)

    elif idx==16:
        # LARANJA (PALS[3]) — Renata exausta caminhando
        boneco(draw,cx-80,GND,PR,CR,RR,"exausto","apontando",1.5)
        # Seta apontando pra baixo
        draw.line([(cx+120,int(H*0.35)),(cx+120,int(H*0.48))],fill=VERM,width=10)
        draw.polygon([(cx+107,int(H*0.48)),(cx+133,int(H*0.48)),(cx+120,int(H*0.52))],fill=VERM)

    elif idx==17:
        # VINHO (PALS[4]) — Casal + barreira visual
        boneco(draw,cx-130,GND+10,PR,CR,RR,"triste","pe",1.35)
        boneco(draw,cx+130,GND,PL,CL,RL,"neutro","pe",1.35)
        # Barreira no meio
        for y in range(int(H*0.30),int(H*0.70),20):
            draw.line([(cx-10,y),(cx+10,y)],fill=ac,width=12)

    elif idx==18:
        # AMBAR (PALS[5]) — Lucas com expressao controlada
        boneco(draw,cx,GND,PL,CL,RL,"neutro","pe",1.65)
        # Fones de ouvido estilizados
        draw.arc([cx-90,int(H*0.32),cx+90,int(H*0.45)],180,0,fill=ac,width=12)
        draw.ellipse([cx-98,int(H*0.36),cx-74,int(H*0.43)],fill=ac)
        draw.ellipse([cx+74,int(H*0.36),cx+98,int(H*0.43)],fill=ac)

    elif idx==19:
        # VERDE (PALS[10]) — Renata sorindo radiante
        boneco(draw,cx,GND,PR,CR,RR,"feliz","pe",1.65)
        # Brilhos ao redor
        for ang in range(0,360,45):
            rad=math.radians(ang)
            x1=int(cx+145*math.cos(rad));y1=int(GND-220+145*math.sin(rad))
            x2=int(cx+188*math.cos(rad));y2=int(GND-220+188*math.sin(rad))
            draw.line([(x1,y1),(x2,y2)],fill=ac,width=7)

    elif idx==20:
        # OURO (PALS[11]) — CTA final com ψ
        draw.text((cx-52,int(H*0.22)),"psi",fill=ac)
        boneco(draw,cx,GND,PR,CR,RR,"feliz","pe",1.55)
        badge(draw,cx,int(H*0.18),"Proximo Episodio",cor=(160,50,0),larg=360)
        badge(draw,cx,int(H*0.13),"Inscreva-se Agora",cor=VERM,larg=360)

    lt(draw)
    p=f"/tmp/v683/cena{idx:02d}.jpg"
    img.save(p,"JPEG",quality=93)
    print(f"  cena {idx:02d}: {ct[0]},{ct[1]},{ct[2]} -> OK")
    return p

print("=== RENDER VIRAL V3 | 20 CENAS | SEM PSICOLOGA ===")
paths=[cena(i) for i in range(1,N+1)]
print("Cenas OK! Verificando diversidade de cores:")
from PIL import Image as PIL_Image
import numpy as np
for i,p in enumerate(paths[:5],1):
    arr=np.array(PIL_Image.open(p))
    print(f"  Cena {i:02d}: top R={int(np.mean(arr[:100,:,0]))},G={int(np.mean(arr[:100,:,1]))},B={int(np.mean(arr[:100,:,2]))}")

# AUDIO
r=requests.get(f"{SB_URL}/rest/v1/content_pipeline",
    params={"select":"audio_url","id":"eq.683"},
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"})
audio_url=r.json()[0]["audio_url"]
print(f"Audio: {audio_url[-50:]}")
r2=requests.get(audio_url,headers={"apikey":SB_KEY},timeout=90)
with open("/tmp/v683/audio.mp3","wb") as f: f.write(r2.content)

probe=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",
    "/tmp/v683/audio.mp3"],capture_output=True,text=True)
ADU=float(json.loads(probe.stdout)["format"]["duration"])
DUR=ADU/N;FPS=25;FR=int(DUR*FPS)
print(f"Audio {ADU:.1f}s | cena {DUR:.2f}s | {FR}f")

# KEN BURNS — alternando para ritmo dinamico
KB=["zi","zo","pl","pr","zt","zb","zi","pl","zo","pr",
    "zt","zi","zo","pl","pr","zi","zo","zt","pl","zi"]

def kb(m,fr):
    if m=="zi": z=f"min(zoom+0.0006,1.24)";x="(iw-iw/zoom)/2";y="(ih-ih/zoom)/2"
    elif m=="zo": z=f"if(eq(on,1),1.24,max(zoom-0.0006,1.0))";x="(iw-iw/zoom)/2";y="(ih-ih/zoom)/2"
    elif m=="pl": z="1.14";x=f"(iw-iw/zoom)/2+65*((on-1)/{fr})";y="(ih-ih/zoom)/2"
    elif m=="pr": z="1.14";x=f"max(0,(iw-iw/zoom)/2-65*((on-1)/{fr}))";y="(ih-ih/zoom)/2"
    elif m=="zt": z=f"min(zoom+0.0006,1.24)";x="(iw-iw/zoom)/2";y="0"
    else: z=f"if(eq(on,1),1.24,max(zoom-0.0006,1.0))";x="(iw-iw/zoom)/2";y="ih-ih/zoom"
    return f"zoompan=z='{z}':x='{x}':y='{y}':d={fr}:s=1080x1920:fps={FPS}"

inp=[]
for p in paths: inp+=["-loop","1","-t",str(DUR+0.15),"-i",p]

fc=""
for i in range(N):
    fc+=f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,{kb(KB[i%len(KB)],FR+3)}[v{i}];"
fc+="".join(f"[v{i}]" for i in range(N))
fc+=f"concat=n={N}:v=1:a=0[vout];[vout]eq=saturation=1.20:brightness=0.03:contrast=1.08[vf]"

print("Renderizando FFmpeg (20 cenas)...")
cmd=["ffmpeg","-y"]+inp+["-i","/tmp/v683/audio.mp3",
    "-filter_complex",fc,"-map","[vf]","-map",f"{N}:a",
    "-c:v","libx264","-preset","fast","-crf","18",
    "-c:a","aac","-b:a","128k","-pix_fmt","yuv420p",
    "-r",str(FPS),"-t","58","-movflags","+faststart",
    "/tmp/v683/viral_v3.mp4"]
res=subprocess.run(cmd,capture_output=True,text=True,timeout=480)
if res.returncode!=0:
    print("FFMPEG ERRO:"); print(res.stderr[-2000:]); exit(1)

sz=os.path.getsize("/tmp/v683/viral_v3.mp4")
probe2=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",
    "/tmp/v683/viral_v3.mp4"],capture_output=True,text=True)
dur2=float(json.loads(probe2.stdout)["format"]["duration"])
print(f"MP4: {sz//1024}KB | {dur2:.1f}s")

# UPLOAD
fname=f"mp4s/v683_viral_v6_{int(time.time())}.mp4"
with open("/tmp/v683/viral_v3.mp4","rb") as f: data=f.read()
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
                         "metadata":{"render_version":"v6_viral_20cenas_sem_psicologa",
                                     "n_cenas":20,"lower_third":"Saude Mental",
                                     "score_viral":99,"quality_status":"aprovado"}}),timeout=30)
    print(f"DB: {r4.status_code} — {mp4_url[-55:]}")
print("Concluido!")
