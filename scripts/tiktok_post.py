#!/usr/bin/env python3
"""
tiktok_post.py — Posta vídeo no TikTok usando session cookies
Sem necessidade de API Developer aprovada
Requer: TT_SESSION_ID (cookie sessionid do TikTok)
"""
import os, sys, json, subprocess, pathlib, urllib.request, urllib.parse
from datetime import datetime

TT_SESSION = os.environ.get("TT_SESSION_ID","")
SB_URL     = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY     = os.environ.get("SUPABASE_SERVICE_KEY","")
VIDEO_PATH = os.environ.get("VIDEO_PATH","")
CAPTION    = os.environ.get("CAPTION","🔴 BLACK SCREEN | BINAURAL 432Hz | #blackscreen #432hz #darkpsychology #psidanicoelho")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)

def get_latest_short():
    """Pega o short mais recente do Supabase"""
    if not SB_KEY: return None
    req=urllib.request.Request(f"{SB_URL}/rest/v1/video_jobs?select=video_path,title,script_id&status=eq.published&format=eq.short&order=created_at.desc&limit=1",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"})
    try:
        with urllib.request.urlopen(req,timeout=10) as r:
            jobs=json.loads(r.read())
        return jobs[0].get("video_path") if jobs else None
    except: return None

def post_tiktok_playwright(video_path, caption):
    """Posta no TikTok usando Playwright + session cookie"""
    if not TT_SESSION:
        log("⚠️  Sem TT_SESSION_ID — precisa configurar no GitHub Secrets")
        log("   Como obter:")
        log("   1. Abra tiktok.com no Chrome, faça login")
        log("   2. F12 → Application → Cookies → tiktok.com")
        log("   3. Copie o valor de 'sessionid'")
        log("   4. GitHub Secrets → TT_SESSION_ID = [valor]")
        return False
    
    script=f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const ctx = await browser.newContext();
  
  // Injetar session cookie
  await ctx.addCookies([{{
    name: 'sessionid',
    value: '{TT_SESSION}',
    domain: '.tiktok.com',
    path: '/'
  }}]);
  
  const page = await ctx.newPage();
  await page.goto('https://www.tiktok.com/upload', {{ timeout: 30000 }});
  await page.waitForLoadState('networkidle');
  
  // Upload do vídeo
  const fileInput = await page.$('input[type="file"]');
  if (!fileInput) {{ console.error('Sem input de arquivo'); process.exit(1); }}
  await fileInput.setInputFiles('{video_path}');
  await page.waitForTimeout(5000);
  
  // Preencher caption
  const captionInput = await page.$('[data-contents]');
  if (captionInput) {{
    await captionInput.click();
    await captionInput.fill('{caption[:150]}');
  }}
  
  await page.waitForTimeout(2000);
  
  // Postar
  const postBtn = await page.$('button[data-e2e="post_video_button"]');
  if (postBtn) {{
    await postBtn.click();
    await page.waitForTimeout(3000);
    console.log('TikTok postado!');
  }} else {{
    console.error('Botão de post não encontrado');
    process.exit(1);
  }}
  
  await browser.close();
}})().catch(e => {{ console.error(e); process.exit(1); }});
"""
    try:
        node_script = "/tmp/tt_post.js"
        with open(node_script,"w") as f: f.write(script)
        result = subprocess.run(["node", node_script], capture_output=True, timeout=120)
        if result.returncode == 0:
            log(f"TikTok ✅: {result.stdout.decode().strip()}")
            return True
        else:
            log(f"TikTok ❌: {result.stderr.decode()[-200:]}")
            return False
    except Exception as e:
        log(f"TikTok erro: {e}")
        return False

def main():
    log("=== TikTok Post ===")
    video = VIDEO_PATH or get_latest_short()
    if not video:
        log("Sem vídeo disponível"); return
    log(f"Vídeo: {video}")
    post_tiktok_playwright(video, CAPTION)

if __name__ == "__main__":
    main()
