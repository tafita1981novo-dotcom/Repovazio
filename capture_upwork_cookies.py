#!/usr/bin/env python3
"""
UPWORK COOKIE CAPTURE
Roda UMA VEZ no seu PC. Browser real, voce faz login, cookies vao pro GitHub.
"""
import json, base64, subprocess, sys

for pkg in ["playwright","requests","PyNaCl"]:
    try: __import__(pkg.lower())
    except: subprocess.check_call([sys.executable,"-m","pip","install",pkg,"-q"])
subprocess.run([sys.executable,"-m","playwright","install","chromium"], capture_output=True)

from playwright.sync_api import sync_playwright
import requests
from nacl import public

print()
print("="*50)
print("  UPWORK - Captura de Cookies")
print("="*50)

REPO  = "tafita81/Repovazio"
TOKEN = input("  Cole seu GitHub Token (ghp_...): ").strip()
HEADS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}

print()
print("  Passos:")
print("  1. Browser abre em instantes")
print("  2. Faca login com Google + 2FA no celular")
print("  3. Quando ver a pagina do Upwork, volte aqui")
input()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        viewport={"width":1280,"height":900}
    )
    page = ctx.new_page()
    page.goto("https://www.upwork.com/ab/account-security/login")
    print("  Browser aberto! Faca o login agora.")
    input("  Logado? Pressione ENTER: ")
    cookies = ctx.cookies()
    browser.close()

upwork = [c for c in cookies if "upwork" in c.get("domain","").lower()]
if not upwork:
    print("  Erro: nao achei cookies. Tente novamente."); sys.exit(1)
print(f"  {len(upwork)} cookies capturados!")

cookies_b64 = base64.b64encode(json.dumps(cookies).encode()).decode()
with open("upwork_cookies_b64.txt","w") as f: f.write(cookies_b64)

print("  Enviando para GitHub...")
try:
    pk  = requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key", headers=HEADS).json()
    box = public.SealedBox(public.PublicKey(base64.b64decode(pk["key"])))
    enc = base64.b64encode(box.encrypt(cookies_b64.encode())).decode()
    r   = requests.put(
        f"https://api.github.com/repos/{REPO}/actions/secrets/UPWORK_COOKIES",
        headers=HEADS, json={"encrypted_value":enc,"key_id":pk["key_id"]}
    )
    if r.status_code in [201,204]:
        requests.post(
            f"https://api.github.com/repos/{REPO}/actions/workflows/upwork-agent.yml/dispatches",
            headers=HEADS, json={"ref":"main"}
        )
        print()
        print("="*50)
        print("  PRONTO! Upwork conectado!")
        print("  Agente roda sozinho a cada 3 horas.")
        print("="*50)
    else:
        print(f"  Erro {r.status_code} - adicione manualmente:")
        print(f"  Secret: UPWORK_COOKIES = conteudo de upwork_cookies_b64.txt")
except Exception as e:
    print(f"  {e}")
    print(f"  Salvo em upwork_cookies_b64.txt")
