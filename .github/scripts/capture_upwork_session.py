#!/usr/bin/env python3
"""
Capturador de sessão Upwork — rode UMA VEZ no seu computador
Abre browser real, você faz login com Google, cookies são salvos automaticamente
"""
from playwright.sync_api import sync_playwright
import json, base64, os, time

print("\n" + "="*55)
print("  UPWORK SESSION CAPTURE")
print("  Vou abrir o browser. Faça login com Google.")
print("="*55 + "\n")

with sync_playwright() as p:
    # Browser VISÍVEL (não headless) para você fazer login
    browser = p.chromium.launch(
        headless=False,
        args=["--start-maximized"]
    )
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        viewport=None
    )
    page = ctx.new_page()
    
    # Abrir Upwork login
    print("Abrindo Upwork...")
    page.goto("https://www.upwork.com/ab/account-security/login", timeout=30000)
    
    print("\n>>> Clique em 'Continue with Google'")
    print(">>> Faça login com tafita81@gmail.com")
    print(">>> Após entrar no Upwork, aguarde...")
    
    # Aguardar até estar logado (max 3 minutos)
    for i in range(36):
        time.sleep(5)
        current = page.url
        if any(k in current for k in ["feed","find-work","my-jobs","freelancer"]):
            print(f"\n✅ Login detectado! URL: {current[:60]}")
            break
        if i % 6 == 0:
            print(f"  [{i*5}s] Aguardando login... URL: {current[:50]}")
    
    # Salvar cookies
    cookies = ctx.cookies()
    cookies_json = json.dumps(cookies)
    cookies_b64  = base64.b64encode(cookies_json.encode()).decode()
    
    # Salvar arquivo local
    with open("upwork_cookies.txt", "w") as f:
        f.write(cookies_b64)
    
    print(f"\n✅ {len(cookies)} cookies salvos!")
    print(f"\nCOPIE o conteúdo abaixo e envie para o Claude:")
    print("="*55)
    print(cookies_b64[:200] + "...")
    print("="*55)
    print(f"\nArquivo salvo: upwork_cookies.txt")
    print("Copie o conteúdo completo do arquivo e envie para o Claude")
    
    input("\nPressione Enter para fechar o browser...")
    browser.close()
