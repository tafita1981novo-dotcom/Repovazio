#!/usr/bin/env python3
"""render_quantum_v2.py Cerebro V15 — NVIDIA 3 endpoints + Pillow multi-cena Psych2Go"""
import os, json, time, requests, base64, random, math
from PIL import Image, ImageDraw
from supabase import create_client

SB_URL = os.environ["SUPABASE_URL"]
SB_KEY = os.environ["SUPABASE_KEY"]
sb = create_client(SB_URL, SB_KEY)
SB_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwanZhbHp3a3F3dHR2bXN6dmllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwMzUyOTMsImV4cCI6MjA5MTYxMTI5M30.UEgUo0Mw15ihQZykLAY5QApRzgTXkfIewZFzIgwao3Q"
NVIDIA_KEY = os.environ.get("NVIDIA_API_KEY","")

PALETAS = {
    "ansioso":[(255,243,163),(200,175,90),(225,185,40)],
    "melancolico":[(176,196,222),(100,125,168),(70,90,140)],
    "tenso":[(255,195,175),(210,95,75),(185,50,30)],
    "urgente":[(255,218,145),(200,135,35),(175,90,0)],
    "esperanca":[(178,220,178),(75,158,75),(35,118,35)],
    "empatia":[(255,215,195),(198,125,88),(158,75,45)],
    "contemplativo":[(230,190,230),(158,88,158),(118,45,118)],
    "calmo":[(165,213,232),(55,138,178),(25,98,138)],
    "alivio":[(195,238,195),(55,178,55),(15,118,15)],
}
EMOCAO_KEYS = list(PALETAS.keys())
TONS_PELE = [
    (245,210,185),(225,180,145),(200,155,115),
    (175,125,90),(150,100,70),(130,85,60),(110,70,50),(90,55,40),
]
TONS_CABELO = [(90,55,30),(40,25,10),(180,130,60),(60,40,20),(200,60,30),(30,30,30),(160,100,40)]

def detectar_emocao(titulo, script):
    t = (titulo + " " + script[:400]).lower()
    if any(x in t for x in ["ansio","panico","medo","abandono","apego"]): return "ansioso"
    if any(x in t for x in ["trauma","dor","ferida","abuso"]): return "melancolico"
    if any(x in t for x in ["narcis","manipu","toxico","gaslight"]): return "tenso"
    if any(x in t for x in ["burnout","esgota","depressao"]): return "urgente"
    if any(x in t for x in ["cura","supera","esperanca"]): return "esperanca"
    if any(x in t for x in ["limites","autoestima","amor"]): return "empatia"
    return "contemplativo"

def dividir_cenas(script, duracao_min):
    paras = [p.strip() for p in script.split("\n") if p.strip()]
    if not paras: paras = [script]
    n = 5 if duracao_min < 3 else min(18, max(8, len(paras)))
    chunk = max(1, len(paras)//n)
    cenas = []
    for i in range(0, len(paras), chunk):
        cenas.append(" ".join(paras[i:i+chunk]))
        if len(cenas) >= n: break
    return cenas or [script]

def desenhar_personagem(draw, cx, cy, tom_pele, cor_char, cor_acc, seed):
    pele = tom_pele
    pele_esc = tuple(max(0,c-30) for c in pele)
    cabelo = TONS_CABELO[seed % len(TONS_CABELO)]
    # Sombra
    draw.ellipse([cx-82,cy+188,cx+82,cy+215], fill=tuple(max(0,c-35) for c in (220,215,210)))
    # Pernas
    draw.rounded_rectangle([cx-50,cy+120,cx-14,cy+208], radius=15, fill=pele_esc, outline=cor_acc, width=3)
    draw.rounded_rectangle([cx+14,cy+120,cx+50,cy+208], radius=15, fill=pele_esc, outline=cor_acc, width=3)
    # Torso
    draw.rounded_rectangle([cx-62,cy-12,cx+62,cy+135], radius=20, fill=cor_char, outline=cor_acc, width=4)
    # Bracos por pose
    pose = seed % 5
    if pose == 0:
        draw.rounded_rectangle([cx-122,cy+18,cx-62,cy+92], radius=14, fill=pele, outline=cor_acc, width=3)
        draw.rounded_rectangle([cx+62,cy+18,cx+122,cy+92], radius=14, fill=pele, outline=cor_acc, width=3)
    elif pose == 1:
        draw.rounded_rectangle([cx-95,cy+22,cx-10,cy+78], radius=13, fill=pele, outline=cor_acc, width=3)
        draw.rounded_rectangle([cx+10,cy+32,cx+95,cy+88], radius=13, fill=pele, outline=cor_acc, width=3)
    elif pose == 2:
        draw.rounded_rectangle([cx-122,cy-48,cx-62,cy+38], radius=14, fill=pele, outline=cor_acc, width=3)
        draw.rounded_rectangle([cx+62,cy+22,cx+122,cy+88], radius=14, fill=pele, outline=cor_acc, width=3)
    elif pose == 3:
        draw.rounded_rectangle([cx-148,cy+10,cx-62,cy+68], radius=14, fill=pele, outline=cor_acc, width=3)
        draw.rounded_rectangle([cx+62,cy+10,cx+148,cy+68], radius=14, fill=pele, outline=cor_acc, width=3)
    else:
        draw.rounded_rectangle([cx-118,cy+20,cx-62,cy+68], radius=13, fill=pele, outline=cor_acc, width=3)
        draw.rounded_rectangle([cx+62,cy+30,cx+118,cy+78], radius=13, fill=pele, outline=cor_acc, width=3)
    # Pescoco
    draw.rounded_rectangle([cx-19,cy-30,cx+19,cy+8], radius=9, fill=pele)
    # Cabeca SEM ROSTO
    hr = 73
    hy = cy - hr - 36
    draw.ellipse([cx-hr-8,hy-hr-14,cx+hr+8,hy+26], fill=cabelo)
    draw.ellipse([cx-hr,hy-hr,cx+hr,hy+hr], fill=pele, outline=cor_acc, width=4)

def expressao_abstrata(draw, cx, hy, hr, emocao, cor_acc, seed):
    if emocao == "tenso":
        for ang in range(0,360,40):
            rad = math.radians(ang)
            x1=cx+int(hr*1.15*math.cos(rad)); y1=hy+int(hr*1.15*math.sin(rad))
            x2=cx+int(hr*1.48*math.cos(rad)); y2=hy+int(hr*1.48*math.sin(rad))
            draw.line([x1,y1,x2,y2], fill=cor_acc, width=4)
    elif emocao == "ansioso":
        for i in range(0,300,18):
            rad=math.radians(i); r=hr*1.12+i*0.18
            x=cx+int(r*math.cos(rad)); y=hy+int(r*math.sin(rad))
            draw.ellipse([x-4,y-4,x+4,y+4], fill=cor_acc)
    elif emocao in ["esperanca","alivio","empatia","calmo"]:
        for dx,dy in [(-hr*1.6,-hr*1.3),(hr*1.6,-hr*1.3),(0,-hr*1.9)]:
            sx,sy=int(cx+dx),int(hy+dy)
            draw.ellipse([sx-14,sy-14,sx+14,sy+14], fill=cor_acc)
            draw.line([sx-22,sy,sx+22,sy], fill=cor_acc, width=3)
            draw.line([sx,sy-22,sx,sy+22], fill=cor_acc, width=3)
    elif emocao == "melancolico":
        for i in range(6):
            rx=cx-60+i*24; draw.line([rx,hy+hr+4,rx-6,hy+hr+30], fill=cor_acc, width=3)
    else:
        draw.arc([cx-hr*1.3,hy-hr*1.3,cx+hr*1.3,hy+hr*1.3], 0, 180, fill=cor_acc, width=3)

def gerar_cena_pillow(emocao, cena_idx, total_cenas, video_id):
    """Gera cena 2D Psych2Go com personagem sem rosto — rica variacao"""
    random.seed(cena_idx*17 + video_id*3)
    # Rotacionar paleta para variedade entre cenas
    em_idx = (EMOCAO_KEYS.index(emocao) + cena_idx) % len(EMOCAO_KEYS)
    em_cena = EMOCAO_KEYS[em_idx]
    bg_c, char_c, acc_c = PALETAS[em_cena]

    W, H = 1344, 768
    img = Image.new("RGB", (W,H), bg_c)
    draw = ImageDraw.Draw(img)
    # Gradiente
    for y in range(H):
        f = 1.0-(y/H)*0.18
        draw.line([(0,y),(W,y)], fill=tuple(int(c*f) for c in bg_c))
    # Circulos decorativos
    for _ in range(20):
        cx2=random.randint(-60,W+60); cy2=random.randint(-60,H+60)
        r2=random.randint(20,115)
        soft=tuple(max(0,int(c*0.80)) for c in bg_c)
        draw.ellipse([cx2-r2,cy2-r2,cx2+r2,cy2+r2], fill=soft)

    comp = cena_idx % 7
    pele = TONS_PELE[cena_idx % len(TONS_PELE)]

    if comp == 5 and total_cenas > 3:
        # Dois personagens (relacionamento)
        desenhar_personagem(draw, W//3, H//2+10, pele, char_c, acc_c, cena_idx)
        pele2 = TONS_PELE[(cena_idx+3) % len(TONS_PELE)]
        char2 = tuple(min(255,c+50) for c in char_c)
        acc2  = tuple(max(0,c-25) for c in acc_c)
        desenhar_personagem(draw, W*2//3, H//2+10, pele2, char2, acc2, cena_idx+4)
        draw.line([W//3+85, H//2, W*2//3-85, H//2], fill=acc_c, width=3)
    elif comp == 6:
        # Personagem pequeno em canto (solidao/reflexao)
        desenhar_personagem(draw, W//4, H//2+20, pele, char_c, acc_c, cena_idx)
    else:
        posicoes_x = [W//2, W//3, W*2//3, W//4+80, W*3//4-80, W//2, W//2]
        cx = posicoes_x[comp]
        cy = H//2 + (comp%3-1)*15
        desenhar_personagem(draw, cx, cy, pele, char_c, acc_c, cena_idx)
        # Expressao abstrata
        hr = 73; hy = cy - hr - 36
        expressao_abstrata(draw, cx, hy, hr, em_cena, acc_c, cena_idx)

    path = f"/tmp/cena_{video_id}_{cena_idx}.jpg"
    img.save(path, "JPEG", quality=93)
    return path

def tentar_nvidia(prompt, video_id, cena_idx):
    if not NVIDIA_KEY: return None
    endpoints = [
        ("https://integrate.api.nvidia.com/v1/images/generations",
         {"model":"black-forest-labs/flux-schnell","prompt":prompt,
          "n":1,"size":"1344x768","response_format":"b64_json"}),
        ("https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux-schnell",
         {"prompt":prompt,"width":1344,"height":768,"num_inference_steps":4,
          "guidance_scale":3.5,"num_images":1,"seed":random.randint(1,999999)}),
        ("https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-xl",
         {"prompt":prompt,"width":1344,"height":768,"num_inference_steps":20,
          "guidance_scale":7.0,"seed":random.randint(1,999999)}),
    ]
    for ep, payload in endpoints:
        try:
            r = requests.post(ep,
                headers={"Authorization":f"Bearer {NVIDIA_KEY}","Content-Type":"application/json"},
                json=payload, timeout=90)
            print(f"    NVIDIA {ep.split('/')[-1]}: {r.status_code}")
            if r.status_code != 200:
                try: print(f"      {r.json().get('detail',r.text[:120])}")
                except: print(f"      {r.text[:120]}")
                continue
            data = r.json()
            b64 = (data.get("artifacts",[{}])[0].get("base64","") or
                   data.get("data",[{}])[0].get("b64_json",""))
            if b64:
                p = f"/tmp/nv_{video_id}_{cena_idx}.jpg"
                with open(p,"wb") as f: f.write(base64.b64decode(b64))
                print(f"    NVIDIA OK: {len(b64)//1024}KB")
                return p
        except Exception as e:
            print(f"    NVIDIA exc: {e}")
    return None

def gerar_prompt(titulo, trecho, emocao, cena_idx):
    personagens = [
        "Brazilian woman 25-30 medium brown skin dark wavy hair emotional",
        "Brazilian man 28-35 olive skin short dark hair tense posture",
        "Brazilian woman 35-45 Black skin natural afro hair thoughtful",
        "Brazilian young man 22-28 tan skin casual worried expression",
        "Brazilian woman 40-50 mixed race shoulder hair reflective",
    ]
    paletas_desc = {
        "tenso":"warm coral red pastel background",
        "ansioso":"pale yellow #FFF3A3 background",
        "melancolico":"dusty blue #B0C4DE background",
        "esperanca":"soft mint green background",
        "empatia":"warm peach background",
        "contemplativo":"soft lavender background",
    }
    expressoes = {
        "tenso":"tense suspicious expression narrowed eyes",
        "ansioso":"wide anxious eyes worried trembling",
        "melancolico":"sad downcast eyes contemplative",
        "esperanca":"hopeful warm smile gentle eyes",
        "empatia":"compassionate smile kind understanding",
        "contemplativo":"thoughtful pensive tilted head",
    }
    p = personagens[cena_idx % len(personagens)]
    pal = paletas_desc.get(emocao,"soft pastel background")
    expr = expressoes.get(emocao,"expressive emotional face")
    return (f"flat 2D vector art illustration educational animation style, "
            f"medium shot, {p}, {expr}, {pal}, bold clean outlines, "
            f"Psych2Go cartoon style, single character, NO TEXT NO WORDS NO LETTERS "
            f"NO NUMBERS NO LOGOS NO WATERMARKS ZERO TEXT IN IMAGE")

def upload_img(path, video_id, cena_idx):
    fname = f"v2/img_{video_id}_{cena_idx}_{int(time.time())}.jpg"
    with open(path,"rb") as f: data = f.read()
    try:
        sb.storage.from_("videos").upload(fname, data,
            file_options={"content-type":"image/jpeg","x-upsert":"true"})
        return f"{SB_URL}/storage/v1/object/public/videos/{fname}"
    except:
        r = requests.post(f"{SB_URL}/storage/v1/object/videos/{fname}",
            headers={"apikey":SB_ANON,"Authorization":f"Bearer {SB_ANON}",
                     "Content-Type":"image/jpeg","x-upsert":"true"}, data=data)
        if r.status_code in [200,201]:
            return f"{SB_URL}/storage/v1/object/public/videos/{fname}"
    return None

def get_pendentes():
    r = sb.table("content_pipeline").select(
        "id,title,script,audio_url,metadata,duracao_min,pub_order"
    ).eq("status","mp4_ready").is_("mp4_url",None).order("pub_order").limit(5).execute()
    return r.data or []

def processar(v):
    vid_id = v["id"]
    title  = v.get("title","")
    script = v.get("script","") or ""
    audio  = v.get("audio_url","")
    dur    = float(v.get("duracao_min") or 0.9)
    print(f"\n  #{vid_id} {title[:55]}")
    if not audio:
        print("    sem audio — pulando"); return False
    emocao = detectar_emocao(title, script)
    cenas  = dividir_cenas(script, dur)
    print(f"    emocao={emocao} | {len(cenas)} cenas")
    urls = []
    for i, trecho in enumerate(cenas):
        print(f"    cena {i+1}/{len(cenas)}...")
        prompt = gerar_prompt(title, trecho, emocao, i)
        img = tentar_nvidia(prompt, vid_id, i)
        fonte = "nvidia"
        if not img:
            img = gerar_cena_pillow(emocao, i, len(cenas), vid_id)
            fonte = "pillow"
        url = upload_img(img, vid_id, i)
        if url:
            urls.append(url)
            print(f"      cena {i+1} ({fonte}) OK")
        time.sleep(0.3)
    if not urls:
        print("    sem imagens"); return False
    sb.table("content_pipeline").update({
        "status":"video_ready","mp4_url":None,
        "metadata":(v.get("metadata") or {}) | {
            "quantum_images":urls,"quantum_image":urls[0],
            "n_cenas":len(urls),"emocao":emocao,
            "render_method":"multi_scene_psych2go_v15",
            "processado_em":int(time.time()),
        }
    }).eq("id",vid_id).execute()
    print(f"    video_ready com {len(urls)} cenas")
    return True

def main():
    print("=== RENDER QUANTUM V15 multi-cena Psych2Go ===")
    print(f"NVIDIA: {'OK' if NVIDIA_KEY else 'ausente pillow fallback'}")
    videos = get_pendentes()
    print(f"Videos: {len(videos)}")
    ok = 0
    for v in videos:
        try:
            if processar(v): ok += 1
            time.sleep(1)
        except:
            import traceback; traceback.print_exc()
    print(f"Concluido: {ok}/{len(videos)}")

if __name__ == "__main__":
    main()
