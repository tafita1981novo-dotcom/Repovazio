#!/usr/bin/env python3
import os,json,math,time,subprocess,requests
from PIL import Image,ImageDraw

SB_URL=os.environ.get("SUPABASE_URL","")
SB_KEY=os.environ.get("SUPABASE_KEY","")
W,H=1080,1920
os.makedirs("/tmp/v683",exist_ok=True)

VERM=(220,60,60);CORAL=(240,100,80);AM=(255,205,50);VERD=(60,180,100)
PR=(222,175,132);CR=(140,90,40);RR=(220,80,70)
PL=(182,135,90);CL=(55,32,12);RL=(60,80,200)
BR=(255,255,255);ES=(40,25,10)

def lerp(a,b,t): return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))

def fundo(draw,ct,cb):
    for y in range(H):
        t=y/H
        if y<H*0.72: c=lerp(ct,cb,y/(H*0.72))
        else: c=lerp(cb,(200,185,165),(y-H*0.72)/(H*0.28))
        draw.line([(0,y),(W,y)],fill=c)

def sol(draw):
    sx,sy,r=W-90,85,48
    for a in range(0,360,45):
        rad=math.radians(a)
        draw.line([int(sx+r*math.cos(rad)),int(sy+r*math.sin(rad)),int(sx+(r+28)*math.cos(rad)),int(sy+(r+28)*math.sin(rad))],fill=AM,width=7)
    draw.ellipse([sx-r,sy-r,sx+r,sy+r],fill=AM)

def nuvem(draw,x,y):
    for dx,dy,rx,ry in[(0,0,40,28),(-30,8,32,22),(30,8,32,22),(-15,-8,22,16),(15,-8,22,16)]:
        draw.ellipse([x+dx-rx,y+dy-ry,x+dx+rx,y+dy+ry],fill=BR)

def geo(draw,cor,n,seed):
    import random; random.seed(seed)
    for _ in range(n):
        x=random.randint(40,W-40);y=random.randint(80,int(H*0.82));r=random.randint(8,22)
        t=random.choice(["c","t","q"])
        if t=="c": draw.ellipse([x-r,y-r,x+r,y+r],fill=cor)
        elif t=="t": draw.polygon([(x,y-r),(x-r,y+r),(x+r,y+r)],fill=cor)
        else: draw.rectangle([x-r//2,y-r//2,x+r//2,y+r//2],fill=cor)

def lt(draw):
    bx,by=28,H-118
    draw.rounded_rectangle([bx,by,bx+430,by+76],radius=11,fill=(22,20,40))
    draw.text((bx+14,by+10),"psi",fill=(140,80,220))
    draw.text((bx+42,by+10),"Daniela Coelho | Psicóloga Clínica",fill=(240,238,255))
    draw.text((bx+42,by+40),"@psidanielacoelho",fill=(160,130,210))
    draw.rectangle([bx,by+73,bx+430,by+76],fill=VERM)

def perna(draw,cx,cy,sc,cor):
    lw=int(26*sc);leg=int(95*sc)
    for dx in[-int(16*sc),int(16*sc)]:
        draw.rounded_rectangle([cx+dx-lw//2,cy,cx+dx+lw//2,cy+leg],radius=9,fill=cor)
        draw.ellipse([cx+dx-int(18*sc),cy+leg-5,cx+dx+int(18*sc),cy+leg+14],fill=(45,35,25))

def corpo(draw,cx,cy,sc,cor):
    bw=int(88*sc);bh=int(118*sc)
    sr=tuple(max(0,c-50) for c in cor)
    draw.rounded_rectangle([cx-bw//2,cy-bh,cx+bw//2,cy],radius=20,fill=cor)
    draw.rounded_rectangle([cx-int(22*sc),cy-bh,cx+int(22*sc),cy-bh+int(20*sc)],radius=8,fill=sr)

def braco(draw,cx,cy,bw,sc,pele,pose):
    bh=int(118*sc);ay=cy-int(72*sc)
    for sgn,dx in[(-1,-bw//2-int(6*sc)),(1,bw//2+int(6*sc))]:
        if pose=="apontando" and sgn==1:
            draw.line([cx+dx,ay,cx+dx+sgn*int(50*sc),ay-int(60*sc)],fill=pele,width=int(20*sc))
            draw.ellipse([cx+dx+sgn*int(38*sc)-14,ay-74,cx+dx+sgn*int(38*sc)+14,ay-46],fill=pele)
        elif pose=="costas":
            draw.line([cx+dx,ay,cx,ay+int(20*sc)],fill=pele,width=int(20*sc))
        else:
            draw.line([cx+dx,ay,cx+dx+sgn*int(25*sc),ay+40],fill=pele,width=int(20*sc))
            draw.ellipse([cx+dx+sgn*14-14,ay+26,cx+dx+sgn*14+14,ay+54],fill=pele)

def cabeca(draw,cx,cy,bh,sc,pele,cab,expr):
    hr=int(56*sc);sp=tuple(max(0,c-35) for c in pele)
    hy=cy-bh-hr+int(10*sc)
    draw.rectangle([cx-int(14*sc),cy-bh-int(12*sc),cx+int(14*sc),cy-bh+int(8*sc)],fill=pele)
    draw.ellipse([cx-hr,hy-hr,cx+hr,hy+hr],fill=pele)
    draw.ellipse([cx-hr-6,hy-16,cx-hr+10,hy+16],fill=sp)
    draw.ellipse([cx+hr-10,hy-16,cx+hr+6,hy+16],fill=sp)
    draw.ellipse([cx-hr-4,hy-hr-6,cx+hr+4,hy-int(hr*0.3)],fill=cab)
    rosto(draw,cx,hy,hr,pele,expr)

def rosto(draw,cx,cy,hr,pele,expr):
    sob=cy-int(hr*0.55);oy=cy-int(hr*0.18)
    for sgn in[-1,1]:
        ex=cx+sgn*int(hr*0.38)
        if expr in["bravo"]:
            draw.line([(ex-int(hr*0.22),sob-int(hr*0.08)*sgn),(ex+int(hr*0.22),sob+int(hr*0.08)*sgn)],fill=ES,width=int(hr*0.12))
        elif expr in["triste","exausto","choro"]:
            draw.line([(ex-int(hr*0.22),sob+int(hr*0.08)*sgn),(ex+int(hr*0.22),sob-int(hr*0.08)*sgn)],fill=ES,width=int(hr*0.10))
        else:
            draw.line([(ex-int(hr*0.20),sob),(ex+int(hr*0.20),sob)],fill=ES,width=int(hr*0.09))
        ew,eh=int(hr*0.22),int(hr*0.26)
        draw.ellipse([ex-ew,oy-eh,ex+ew,oy+eh],fill=BR)
        draw.ellipse([ex-int(hr*0.14),oy-int(hr*0.16),ex+int(hr*0.14),oy+int(hr*0.16)],fill=(55,40,30))
        draw.ellipse([ex-int(hr*0.08),oy-int(hr*0.09),ex+int(hr*0.08),oy+int(hr*0.09)],fill=ES)
        draw.ellipse([ex+5,oy-13,ex+11,oy-7],fill=BR)
        if expr=="exausto":
            draw.line([ex-ew,oy,ex+ew,oy],fill=ES,width=int(hr*0.16))
    draw.ellipse([cx-6,cy+5,cx+6,cy+12],fill=tuple(max(0,c-25) for c in pele))
    my=cy+int(hr*0.32);bw=int(hr*0.40)
    if expr in["feliz","sorriso_falso"]:
        draw.arc([cx-bw,my-int(hr*0.22),cx+bw,my+int(hr*0.22)],0,180,fill=ES,width=int(hr*0.10))
        if expr=="sorriso_falso":
            draw.arc([cx-bw+5,my-int(hr*0.18),cx+bw-5,my+int(hr*0.18)],10,170,fill=BR,width=int(hr*0.06))
    elif expr in["triste","choro"]:
        draw.arc([cx-bw,my-int(hr*0.10),cx+bw,my+int(hr*0.25)],180,0,fill=ES,width=int(hr*0.10))
        if expr=="choro":
            draw.polygon([(cx-22,my-17),(cx-30,my+5),(cx-14,my+5)],fill=(100,160,255))
    elif expr in["surpresa"]:
        draw.ellipse([cx-20,my-18,cx+20,my+18],fill=ES)
    elif expr=="falando":
        draw.arc([cx-25,my-15,cx+25,my+15],0,180,fill=ES,width=int(hr*0.09))
        draw.rounded_rectangle([cx-18,my-5,cx+18,my+5],radius=4,fill=BR)
    elif expr=="exausto":
        draw.line([cx-22,my+4,cx+22,my],fill=ES,width=int(hr*0.09))
    elif expr=="bravo":
        draw.arc([cx-bw+10,my-5,cx+bw-10,my+28],180,0,fill=ES,width=int(hr*0.11))
    else:
        draw.line([cx-22,my,cx+22,my],fill=ES,width=int(hr*0.09))

def boneco(draw,cx,cy,pele,cab,roupa,expr="neutro",pose="pe",sc=1.0):
    bw=int(88*sc);bh=int(118*sc)
    perna(draw,cx,cy,sc,tuple(max(0,c-50) for c in roupa))
    corpo(draw,cx,cy,sc,roupa)
    braco(draw,cx,cy,bw,sc,pele,pose)
    cabeca(draw,cx,cy,bh,sc,pele,cab,expr)

def coracao_fn(draw,cx,cy,r=40,cor=None,partido=False):
    if cor is None: cor=VERM
    draw.ellipse([cx-r,cy-r//2,cx,cy+r//2],fill=cor)
    draw.ellipse([cx,cy-r//2,cx+r,cy+r//2],fill=cor)
    draw.polygon([(cx-r,cy),(cx,cy+int(r*1.2)),(cx+r,cy)],fill=cor)
    if partido:
        draw.line([(cx,cy-r//2),(cx-5,cy+r//2)],fill=BR,width=4)
        draw.line([(cx,cy-r//2),(cx+5,cy+r//2)],fill=BR,width=4)

def trofeu_fn(draw,cx,cy):
    draw.polygon([(cx-48,cy-96),(cx+48,cy-96),(cx+60,cy-48),(cx,cy),(cx-60,cy-48)],fill=AM)
    draw.rectangle([cx-18,cy-12,cx+18,cy+24],fill=AM)
    draw.rectangle([cx-36,cy+24,cx+36,cy+36],fill=AM)
    draw.ellipse([cx-24,cy-90,cx-6,cy-72],fill=(255,245,150))

def badge(draw,x,y,texto,cor=None):
    if cor is None: cor=VERM
    w=len(texto)*14+30
    draw.rounded_rectangle([x,y,x+w,y+46],radius=12,fill=cor)
    draw.text((x+15,y+10),texto,fill=BR)

print("=== Gerando 12 cenas virais para #683 ===")

def cena(idx):
    img=Image.new("RGB",(W,H))
    draw=ImageDraw.Draw(img)
    gnd=int(H*0.74)

    if idx==1:
        fundo(draw,(255,210,180),(255,185,160))
        sol(draw);nuvem(draw,160,190);nuvem(draw,700,140)
        geo(draw,CORAL,10,1)
        boneco(draw,W//2-60,gnd,PR,CR,RR,"surpresa","pe",1.35)
        draw.text((W//2+100,int(H*0.30)),"?",fill=VERM)

    elif idx==2:
        fundo(draw,(255,200,170),(255,175,155))
        nuvem(draw,300,160);nuvem(draw,750,200)
        geo(draw,CORAL,8,2)
        boneco(draw,W//2-250,gnd,(225,175,130),(145,95,40),(80,160,80),"neutro","pe",1.0)
        boneco(draw,W//2,gnd,(190,140,95),(60,35,15),(80,80,80),"neutro","pe",1.0)
        boneco(draw,W//2+250,gnd,PL,CL,RL,"sorriso_falso","pe",1.0)
        draw.ellipse([W//2+190,int(H*0.44),W//2+310,int(H*0.56)],outline=VERM,width=6)
        draw.text((W//2-55,int(H*0.22)),"9 em 10",fill=VERM)

    elif idx==3:
        fundo(draw,(255,195,165),(250,160,145))
        geo(draw,CORAL,12,3)
        boneco(draw,W//2,gnd,PL,CL,RL,"sorriso_falso","pe",1.4)
        for i,r in enumerate([14,20,28]):
            bx=W//2+120+i*45;by=int(H*0.46)-i*10
            draw.ellipse([bx-r,by-r,bx+r,by+r],outline=VERM,width=3)

    elif idx==4:
        fundo(draw,(255,205,175),(255,180,160))
        sol(draw);nuvem(draw,200,160);nuvem(draw,700,130)
        geo(draw,CORAL,9,4)
        boneco(draw,W//2+120,gnd,PL,CL,RL,"sorriso_falso","pe",1.3)
        boneco(draw,W//2-100,gnd+20,PR,CR,RR,"triste","pe",1.05)
        coracao_fn(draw,W//2,int(H*0.42),r=45,partido=True)

    elif idx==5:
        fundo(draw,(240,160,140),(220,130,110))
        geo(draw,(180,60,60),15,5)
        boneco(draw,W//2,gnd,PR,CR,RR,"confuso","pe",1.35)
        # Espiral simples
        import math as m
        for i in range(80):
            t=i/80.0;r=75*t;ang=t*4*2*m.pi
            x1=int(W//2+r*m.cos(ang));y1=int(int(H*0.41)+r*m.sin(ang))
            r2=75*(t+0.015);x2=int(W//2+r2*m.cos(ang+0.3));y2=int(int(H*0.41)+r2*m.sin(ang+0.3))
            draw.line([(x1,y1),(x2,y2)],fill=VERM,width=3)

    elif idx==6:
        fundo(draw,(255,205,175),(250,175,155))
        geo(draw,CORAL,9,6)
        boneco(draw,W//2-140,gnd,PR,CR,RR,"falando","apontando",1.15)
        boneco(draw,W//2+140,gnd,PL,CL,RL,"bravo","costas",1.15)
        draw.rounded_rectangle([W//2-240,int(H*0.38),W//2-40,int(H*0.48)],radius=18,fill=BR)
        draw.line([(W//2-180,int(H*0.41)),(W//2-100,int(H*0.45))],fill=VERM,width=7)
        draw.line([(W//2-100,int(H*0.41)),(W//2-180,int(H*0.45))],fill=VERM,width=7)
        badge(draw,W//2-250,int(H*0.21),"SINAL 1")

    elif idx==7:
        fundo(draw,(255,210,180),(255,185,165))
        geo(draw,CORAL,9,7)
        trofeu_fn(draw,W//2,int(H*0.42))
        boneco(draw,W//2+170,gnd,PL,CL,RL,"sorriso_falso","apontando",1.1)
        boneco(draw,W//2-170,gnd,PR,CR,RR,"triste","pe",1.0)
        badge(draw,W//2-250,int(H*0.21),"SINAL 2")

    elif idx==8:
        fundo(draw,(240,180,155),(220,155,130))
        geo(draw,CORAL,8,8)
        boneco(draw,W//2,gnd,PR,CR,RR,"exausto","pe",1.3)
        for x in[W//2-80,W//2+80]:
            draw.line([(x,int(H*0.38)),(x,int(H*0.44))],fill=VERM,width=6)
            draw.polygon([(x-10,int(H*0.44)),(x+10,int(H*0.44)),(x,int(H*0.46))],fill=VERM)
        draw.polygon([(W//2+75,int(H*0.47)),(W//2+68,int(H*0.52)),(W//2+82,int(H*0.52))],fill=(100,160,255))
        badge(draw,W//2-250,int(H*0.21),"SINAL 3")

    elif idx==9:
        fundo(draw,(200,230,255),(175,210,255))
        geo(draw,(70,120,200),9,9)
        boneco(draw,W//2-80,gnd,PR,CR,(255,255,255),"neutro","pe",1.1)
        draw.ellipse([W//2+80,int(H*0.32),W//2+200,int(H*0.44)],fill=(220,150,160))
        draw.ellipse([W//2+130,int(H*0.30),W//2+220,int(H*0.40)],fill=(200,130,140))
        badge(draw,W//2+40,int(H*0.56),"Dr. Ramani  UCLA",(70,120,200))

    elif idx==10:
        fundo(draw,(255,195,160),(240,165,140))
        geo(draw,CORAL,10,10)
        boneco(draw,W//2,gnd,PL,CL,RL,"sorriso_falso","pe",1.4)
        # Mascara oval
        draw.ellipse([W//2-70,int(H*0.32),W//2+70,int(H*0.42)],fill=(240,220,160),outline=AM,width=4)
        draw.arc([W//2-30,int(H*0.365),W//2+30,int(H*0.395)],0,180,fill=VERM,width=5)

    elif idx==11:
        fundo(draw,(180,240,200),(160,220,180),(140,200,160))
        sol(draw,W-100,80);nuvem(draw,180,180);nuvem(draw,680,150)
        geo(draw,VERD,10,11)
        boneco(draw,W//2,gnd,PR,CR,RR,"feliz","pe",1.4)
        import math as m
        for ro,cor2 in[(90,VERM),(120,(255,100,100)),(150,(255,160,160))]:
            for ang in[30,90,150,210,270,330]:
                rad=m.radians(ang)
                hx=int(W//2+ro*m.cos(rad));hy=int(H*0.42+ro*m.sin(rad))
                r2=max(5,int(20*(1-ro/200)))
                coracao_fn(draw,hx,hy,r=r2,cor=cor2)

    elif idx==12:
        fundo(draw,(255,215,185),(255,190,170))
        sol(draw);nuvem(draw,200,170);nuvem(draw,760,140)
        geo(draw,CORAL,8,12)
        draw.text((W//2-40,int(H*0.28)),"psi",fill=VERM)
        boneco(draw,W//2,gnd,PR,CR,RR,"feliz","pe",1.3)
        badge(draw,W//2-210,int(H*0.17),"Inscreva-se agora!")

    lt(draw)
    draw.text((W-55,28),"psi",fill=(190,190,200))
    p=f"/tmp/v683/cena{idx:02d}.jpg"
    img.save(p,"JPEG",quality=93)
    print(f"  cena {idx:02d} OK")
    return p

paths=[cena(i) for i in range(1,13)]
print("Todas as cenas geradas!")

# Buscar audio
r=requests.get(f"{SB_URL}/rest/v1/content_pipeline",
    params={"select":"audio_url","id":"eq.683"},
    headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"})
audio_url=r.json()[0]["audio_url"]
r2=requests.get(audio_url,headers={"apikey":SB_KEY},timeout=90)
with open("/tmp/v683/audio.mp3","wb") as f: f.write(r2.content)

probe=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format","/tmp/v683/audio.mp3"],capture_output=True,text=True)
audio_dur=float(json.loads(probe.stdout)["format"]["duration"])
DUR=audio_dur/12;FPS=25;FR=int(DUR*FPS)
print(f"Audio {audio_dur:.1f}s | cena {DUR:.2f}s | {FR} frames")

KB=["zoom_in_center","zoom_out_center","pan_left","pan_right","zoom_in_top","zoom_out_bot","zoom_in_center","pan_right","zoom_out_center","pan_left","zoom_in_top","zoom_in_center"]

def kb(m,fr):
    if m=="zoom_in_center": z=f"min(zoom+0.0004,1.18)";x="(iw-iw/zoom)/2";y="(ih-ih/zoom)/2"
    elif m=="zoom_out_center": z=f"if(eq(on,1),1.18,max(zoom-0.0004,1.0))";x="(iw-iw/zoom)/2";y="(ih-ih/zoom)/2"
    elif m=="pan_left": z="1.10";x=f"(iw-iw/zoom)/2+50*((on-1)/{fr})";y="(ih-ih/zoom)/2"
    elif m=="pan_right": z="1.10";x=f"(iw-iw/zoom)/2-50*((on-1)/{fr})";y="(ih-ih/zoom)/2"
    elif m=="zoom_in_top": z=f"min(zoom+0.0004,1.18)";x="(iw-iw/zoom)/2";y="0"
    else: z=f"if(eq(on,1),1.18,max(zoom-0.0004,1.0))";x="(iw-iw/zoom)/2";y="ih-ih/zoom"
    return f"zoompan=z='{z}':x='{x}':y='{y}':d={fr}:s={W}x{H}:fps={FPS}"

inp=[]
for p in paths: inp+=["-loop","1","-t",str(DUR+0.3),"-i",p]

fc=""
for i in range(12):
    fi=f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,{kb(KB[i],FR+5)}"
    if i>0: fi+=f",fade=t=in:st=0:d=0.25"
    if i<11: fi+=f",fade=t=out:st={DUR-0.25:.3f}:d=0.25"
    fi+=f"[v{i}];"
    fc+=fi
fc+="".join(f"[v{i}]" for i in range(12))
fc+=f"concat=n=12:v=1:a=0[vout];[vout]eq=saturation=1.15:brightness=0.02:contrast=1.05[vf]"

cmd=["ffmpeg","-y"]+inp+["-i","/tmp/v683/audio.mp3","-filter_complex",fc,"-map","[vf]","-map","12:a","-c:v","libx264","-preset","fast","-crf","20","-c:a","aac","-b:a","128k","-pix_fmt","yuv420p","-r",str(FPS),"-t","58","-movflags","+faststart","/tmp/v683/viral.mp4"]

print("Renderizando FFmpeg...")
res=subprocess.run(cmd,capture_output=True,text=True,timeout=360)
if res.returncode!=0: print("FFMPEG ERRO:"); print(res.stderr[-2000:]); exit(1)

sz=os.path.getsize("/tmp/v683/viral.mp4")
print(f"MP4: {sz//1024}KB")

probe2=subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format","/tmp/v683/viral.mp4"],capture_output=True,text=True)
dur2=float(json.loads(probe2.stdout)["format"]["duration"])
print(f"Duracao: {dur2:.1f}s")

fname=f"mp4s/v683_viral_v5_{int(time.time())}.mp4"
with open("/tmp/v683/viral.mp4","rb") as f: mp4b=f.read()

mp4_url=None
for t in range(5):
    r3=requests.post(f"{SB_URL}/storage/v1/object/videos/{fname}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"video/mp4","x-upsert":"true"},
        data=mp4b,timeout=300)
    if r3.status_code in[200,201]:
        mp4_url=f"{SB_URL}/storage/v1/object/public/videos/{fname}"
        print(f"Upload OK")
        break
    print(f"  upload {t+1}: {r3.status_code}")
    time.sleep(5)

if mp4_url:
    r4=requests.patch(f"{SB_URL}/rest/v1/content_pipeline?id=eq.683",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=minimal"},
        data=json.dumps({"mp4_url":mp4_url,"status":"pending_credentials"}),timeout=30)
    print(f"DB: {r4.status_code}")
print("Concluido!")
