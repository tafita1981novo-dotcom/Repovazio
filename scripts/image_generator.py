"""
🖼 Image Generator — Múltiplas fontes sem custo
Prioridade: HF FLUX.1-schnell > Sana > Pixabay > Pillow procedural
"""
import os, pathlib, urllib.request, urllib.parse, json, subprocess, struct, math, random

HF_TOKEN = os.getenv("HF_TOKEN", "")

def gen_hf_image(prompt, output_path, width=576, height=1024, seed=None):
    """Hugging Face FLUX.1-schnell — gratuito com HF_TOKEN"""
    if not HF_TOKEN:
        return False
    
    # FLUX.1-schnell é rápido e gratuito no HF
    models = [
        "black-forest-labs/FLUX.1-schnell",
        "stabilityai/stable-diffusion-xl-base-1.0",
        "stabilityai/stable-diffusion-2-1",
    ]
    
    payload = {
        "inputs": prompt[:400],
        "parameters": {
            "width": width,
            "height": height,
            "guidance_scale": 7.5,
            "num_inference_steps": 4 if "schnell" in models[0] else 20,
        }
    }
    if seed: payload["parameters"]["seed"] = seed
    
    for model in models:
        try:
            body = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"https://api-inference.huggingface.co/models/{model}",
                data=body
            )
            req.add_header("Authorization", f"Bearer {HF_TOKEN}")
            req.add_header("Content-Type", "application/json")
            
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
                if len(data) > 5000 and data[:3] in [b'\xff\xd8\xff', b'\x89PN']:
                    open(output_path, 'wb').write(data)
                    return True
        except Exception as e:
            # Model loading (503) = esperar e tentar novamente
            if "503" in str(e):
                import time; time.sleep(5)
    return False

def gen_pixabay_image(query, output_path, api_key=""):
    """Pixabay API — gratuita com key, muitas fotos HD"""
    if not api_key:
        api_key = os.getenv("PIXABAY_API_KEY", "")
    if not api_key:
        return False
    
    url = f"https://pixabay.com/api/?key={api_key}&q={urllib.parse.quote(query)}&image_type=photo&per_page=5&safesearch=true&category=feelings"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            hits = json.loads(r.read()).get("hits", [])
            if not hits: return False
            
            # Pegar imagem HD
            img_url = hits[0].get("largeImageURL", hits[0].get("webformatURL",""))
            if not img_url: return False
            
            with urllib.request.urlopen(img_url, timeout=30) as r2:
                data = r2.read()
                if len(data) > 5000:
                    open(output_path, 'wb').write(data)
                    return True
    except:
        pass
    return False

def gen_procedural_image(style, output_path, width=576, height=1024, seed=None):
    """Gera imagem procedural cinematográfica com FFmpeg (sempre funciona)"""
    if seed: random.seed(seed)
    
    styles = {
        "dark": {"bg":"0x06060F","fg":"0x7C3AED","fg2":"0xE11D48"},
        "warm": {"bg":"0x0F0A00","fg":"0xF59E0B","fg2":"0xEF4444"},
        "cool": {"bg":"0x060B10","fg":"0x0EA5E9","fg2":"0x8B5CF6"},
        "green":{"bg":"0x051005","fg":"0x10B981","fg2":"0x34D399"},
    }
    s = styles.get(style, styles["dark"])
    
    # Gerar gradient + partículas com FFmpeg (sem dependência Python)
    n_circles = random.randint(8, 20)
    
    # Usar Python/Pillow se disponível, senão FFmpeg
    try:
        from PIL import Image, ImageDraw, ImageFilter
        img = Image.new("RGB", (width, height), tuple(int(s["bg"].replace("0x",""),16).to_bytes(3,'big')))
        
        def hex2rgb(h): 
            h = h.replace("0x","")
            return tuple(int(h[i:i+2],16) for i in (0,2,4))
        
        draw = ImageDraw.Draw(img)
        fg_rgb = hex2rgb(s["fg"])
        fg2_rgb = hex2rgb(s["fg2"])
        bg_rgb = hex2rgb(s["bg"])
        
        # Background gradient
        for y in range(height):
            t = y/height
            c = tuple(int(bg_rgb[i] + (fg_rgb[i]-bg_rgb[i])*t*0.3) for i in range(3))
            draw.line([(0,y),(width,y)], fill=c)
        
        # Círculos decorativos (neurônios)
        for _ in range(n_circles):
            x = random.randint(0, width)
            y = random.randint(0, height)
            r = random.randint(2, 30)
            alpha = random.randint(30, 120)
            color = fg_rgb if random.random() > 0.5 else fg2_rgb
            draw.ellipse([(x-r,y-r),(x+r,y+r)], fill=(*color, alpha))
        
        # Linhas de conexão (rede neural)
        centers = [(random.randint(50, width-50), random.randint(50, height-50)) for _ in range(8)]
        for i, (x1,y1) in enumerate(centers):
            for x2,y2 in centers[i+1:]:
                dist = ((x2-x1)**2 + (y2-y1)**2)**0.5
                if dist < 250:
                    draw.line([(x1,y1),(x2,y2)], fill=(*fg_rgb, 40), width=1)
        
        # Blur para suavizar
        img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
        img.save(output_path, "JPEG", quality=90)
        return True
        
    except ImportError:
        # Fallback FFmpeg puro
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c={s['bg']}:size={width}x{height}:r=1",
            "-vf", f"drawbox=x={width//4}:y={height//4}:w={width//2}:h={height//2}:color={s['fg']}@0.2:t=fill",
            "-frames:v", "1", output_path
        ]
        r = subprocess.run(cmd, capture_output=True, timeout=15)
        return r.returncode == 0

def generate_image(prompt, output_path, width=576, height=1024, seed=None, style="dark"):
    """Tenta todas as fontes em ordem"""
    # 1. HF FLUX.1-schnell (melhor qualidade)
    if HF_TOKEN and gen_hf_image(prompt, output_path, width, height, seed):
        return "hf"
    
    # 2. Pixabay
    if gen_pixabay_image(prompt[:30], output_path):
        return "pixabay"
    
    # 3. Procedural (sempre funciona)
    if gen_procedural_image(style, output_path, width, height, seed):
        return "procedural"
    
    return None

if __name__ == "__main__":
    print("Testando gerador de imagens...")
    
    # Testar HF
    if os.getenv("HF_TOKEN"):
        ok = gen_hf_image("peaceful woman meditating, no text, cinematic", "/tmp/test_hf.jpg")
        print(f"HF: {'✅' if ok else '❌'}")
    
    # Testar procedural
    ok = gen_procedural_image("dark", "/tmp/test_proc.jpg")
    print(f"Procedural: {'✅' if ok else '❌'}")
    import pathlib
    if pathlib.Path('/tmp/test_proc.jpg').exists():
        print(f"  Tamanho: {pathlib.Path('/tmp/test_proc.jpg').stat().st_size//1024}KB")
