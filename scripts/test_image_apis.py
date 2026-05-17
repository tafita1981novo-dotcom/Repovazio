#!/usr/bin/env python3
"""Testar todas as APIs de imagem disponíveis para chibi anime."""
import os, requests, base64, json, time
from PIL import Image
import io

NVIDIA_KEY  = os.environ.get("NVIDIA_API_KEY","")
HF_TOKEN    = os.environ.get("HF_TOKEN","")
GEMINI_KEY  = os.environ.get("GEMINI_API_KEY","")

CHIBI_PROMPT = "chibi anime girl, short dark bob hair, mint green blouse, psi symbol pin, big expressive eyes, kawaii style, white background, flat design, cute, masterpiece, absurdres, no text, original character"

print("="*60)
print("  TESTE DE APIs CHIBI ANIME — psicologia.doc")
print("="*60)

os.makedirs("/tmp/test_imgs", exist_ok=True)

# ─── 1. NVIDIA Flux.1 Schnell ─────────────────────────────────
print("\n1️⃣  NVIDIA API — Flux.1 Schnell")
if NVIDIA_KEY:
    # Endpoint NVIDIA NIM para imagens
    endpoints = [
        ("https://integrate.api.nvidia.com/v1/images/generations",
         {"model":"black-forest-labs/flux-schnell","prompt":CHIBI_PROMPT,
          "n":1,"height":1024,"width":576,"response_format":"b64_json"}),
        ("https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-xl-base-1.0",
         {"text_prompts":[{"text":CHIBI_PROMPT,"weight":1},
                          {"text":"realistic, photo, watermark, text, logo","weight":-1}],
          "seed":42,"sampler":"K_DPM_2_ANCESTRAL","steps":30,"cfg_scale":7,
          "height":1024,"width":576}),
    ]
    for url, payload in endpoints:
        try:
            r = requests.post(url, 
                headers={"Authorization":f"Bearer {NVIDIA_KEY}",
                         "Content-Type":"application/json",
                         "Accept":"application/json"},
                json=payload, timeout=60)
            if r.status_code == 200:
                data = r.json()
                # Extrair imagem
                img_data = None
                if "data" in data:
                    b64 = data["data"][0].get("b64_json","")
                    if b64: img_data = base64.b64decode(b64)
                elif "artifacts" in data:
                    b64 = data["artifacts"][0].get("base64","")
                    if b64: img_data = base64.b64decode(b64)
                if img_data:
                    img = Image.open(io.BytesIO(img_data))
                    sz = len(img_data)//1024
                    print(f"  ✅ NVIDIA Flux.1 FUNCIONOU! {img.size} | {sz}KB")
                    img.save("/tmp/test_imgs/nvidia_flux.jpg","JPEG",quality=95)
                    break
                else:
                    print(f"  ⚠️  {url.split('/')[4]}: sem imagem no response")
            elif r.status_code == 402:
                print(f"  💳 NVIDIA: rate limit / créditos esgotados")
            elif r.status_code == 404:
                print(f"  ❌ {url}: modelo não encontrado")
            else:
                print(f"  ❌ NVIDIA {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"  💥 NVIDIA erro: {str(e)[:80]}")
        time.sleep(2)
else:
    print("  ⚠️  NVIDIA_API_KEY não definida")

# ─── 2. HuggingFace Animagine XL 4.0 ─────────────────────────
print("\n2️⃣  HuggingFace — Animagine XL 4.0 (MELHOR chibi gratuito)")
if HF_TOKEN:
    models_hf = [
        "cagliostrolab/animagine-xl-4.0",
        "cagliostrolab/animagine-xl-3.1",
    ]
    prompt_hf = ("chibi, (chibi:1.4), 1girl, original character, "
                 "short dark hair, green blouse, psi symbol, "
                 "white background, simple background, kawaii, "
                 "flat style, big eyes, cute smile, pastel colors, "
                 "masterpiece, best quality, absurdres")
    neg_hf = ("nsfw, realistic, 3d, photo, worst quality, low quality, "
              "text, watermark, signature, extra fingers, bad anatomy")
    for model in models_hf:
        try:
            url = f"https://api-inference.huggingface.co/models/{model}"
            payload = {"inputs": prompt_hf,
                      "parameters":{"negative_prompt":neg_hf,
                                    "width":576,"height":1024,
                                    "guidance_scale":7,
                                    "num_inference_steps":25,
                                    "seed":42}}
            r = requests.post(url,
                headers={"Authorization":f"Bearer {HF_TOKEN}",
                         "Content-Type":"application/json"},
                json=payload, timeout=120)
            if r.status_code == 200 and 'image' in r.headers.get('content-type',''):
                img = Image.open(io.BytesIO(r.content))
                sz = len(r.content)//1024
                print(f"  ✅ HF {model.split('/')[1]} FUNCIONOU! {img.size} | {sz}KB")
                img.save(f"/tmp/test_imgs/hf_{model.split('/')[1]}.jpg","JPEG",quality=95)
                break
            elif r.status_code == 503:
                print(f"  ⏳ {model}: carregando modelo (cold start)...")
                time.sleep(30)
                r2 = requests.post(url, headers={"Authorization":f"Bearer {HF_TOKEN}"},
                                   json=payload, timeout=120)
                if r2.status_code == 200:
                    img = Image.open(io.BytesIO(r2.content))
                    sz = len(r2.content)//1024
                    print(f"  ✅ HF (após warmup) {sz}KB")
                    img.save(f"/tmp/test_imgs/hf_{model.split('/')[1]}.jpg","JPEG",quality=95)
                    break
            elif r.status_code == 401:
                print(f"  🔑 HF: token inválido ou não autorizado")
                break
            else:
                print(f"  ❌ HF {model}: {r.status_code} — {r.text[:80]}")
        except Exception as e:
            print(f"  💥 HF {model}: {str(e)[:80]}")
        time.sleep(3)
else:
    print("  ⚠️  HF_TOKEN não definido — CRIE EM huggingface.co/settings/tokens")
    print("       É GRATUITO e gera imagens chibi MUITO melhores que Gemini")

# ─── 3. Gemini 2025 (confirmação) ──────────────────────────────
print("\n3️⃣  Gemini (confirmação que modelo está certo)")
if GEMINI_KEY:
    for model in ["gemini-2.0-flash-preview-image-generation",
                  "gemini-2.0-flash-exp-image-generation"]:
        try:
            url = (f"https://generativelanguage.googleapis.com/v1beta"
                   f"/models/{model}:generateContent?key={GEMINI_KEY}")
            r = requests.post(url, json={
                "contents":[{"parts":[{"text":CHIBI_PROMPT}]}],
                "generationConfig":{"responseModalities":["IMAGE","TEXT"]}
            }, timeout=30)
            has_img = any("inlineData" in p
                for c in r.json().get("candidates",[])
                for p in c.get("content",{}).get("parts",[]))
            status = "✅ IMAGEM GERADA" if has_img else f"⚠️  sem imagem ({r.status_code})"
            print(f"  {status} — {model}")
        except Exception as e:
            print(f"  ❌ {model}: {str(e)[:60]}")

print("\n"+"="*60)
print("  RESUMO DOS RESULTADOS:")
import os as oss
for f in oss.listdir("/tmp/test_imgs"):
    sz = oss.path.getsize(f"/tmp/test_imgs/{f}")//1024
    print(f"  🖼️  {f}: {sz}KB")
print("="*60)
