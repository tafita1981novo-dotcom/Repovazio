#!/usr/bin/env python3
"""
DICE AUTONOMOUS APPLY v2
━━━━━━━━━━━━━━━━━━━━━━━━
Estratégia 3 camadas (sem precisar de login Dice):

CAMADA 1 — Greenhouse/Lever via redirect
  → Visita URL da vaga no Dice
  → Detecta redirect para GH/Lever
  → Aplica via formulário direto (já funciona: 114+ confirmadas)

CAMADA 2 — Easy Apply via token salvo
  → Usa token da ia_cache (coluna 'value')
  → Faz POST na API interna do Dice
  → Aplica sem Playwright

CAMADA 3 — Playwright com credenciais
  → Tenta login email+senha
  → Se falhar → marca como 'needs_token'
"""
import os, json, time, re, datetime, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

SUPA = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
KEY  = os.environ.get("SUPABASE_ANON_KEY","")
DICE_EMAIL    = os.environ.get("DICE_EMAIL","tafita81@gmail.com")
DICE_PASSWORD = os.environ.get("DICE_PASSWORD","Daniela1982@")
AKEY = os.environ.get("ANTHROPIC_API_KEY","")

PROFILE = {
    "first":"Rafael","last":"Rodrigues",
    "email":"Rafa_roberto2004@yahoo.com.br",
    "phone":"+5522992418257",
    "linkedin":"https://linkedin.com/in/rafael-r-a3946a15",
    "cv":".github/assets/rafael_cv.pdf",
}

# ── Supabase helpers ──────────────────────────────────────────────────────────
def sb(method, path, data=None, headers_extra=None):
    hdrs = {"apikey":KEY,"Authorization":f"Bearer {KEY}","Content-Type":"application/json"}
    if headers_extra: hdrs.update(headers_extra)
    req  = urllib.request.Request(f"{SUPA}/rest/v1/{path}",
           data=json.dumps(data).encode() if data else None,
           method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read()) if method=="GET" else r.status
    except Exception as e:
        return 409 if "409" in str(e) else None

def get_dice_token():
    """Busca token salvo pelo usuário via página dice-setup"""
    rows = sb("GET","ia_cache?cache_key=eq.secret%3ADICE_SESSION_TOKEN&select=value&limit=1")
    if isinstance(rows, list) and rows:
        val = rows[0].get("value","")
        if len(val) > 20: return val
    return None

def already_applied(jid):
    r = sb("GET", f"job_applications?job_id=eq.{urllib.parse.quote(str(jid))}&select=id&limit=1")
    return isinstance(r,list) and len(r)>0

def save(co, role, url, jid, status, platform="Dice", salary=""):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    sb("POST","job_applications",{
        "company":co,"role":role,"url":url,"job_id":str(jid),
        "application_method":"dice_autonomous","status":status,
        "platform":platform,"applied_at":now,"email":PROFILE["email"],
        "salary":salary,"country":"US"
    })

def quick_cover(co, role):
    if not AKEY:
        return (f"Senior Data Analyst and Power BI Developer with 15+ years of enterprise BI experience. "
                f"USD 9M+ savings, 70% latency reduction, 200+ business users, PL-300 certified. "
                f"Available immediately for {role} at {co}. "
                f"Rafael Rodrigues | +5522992418257 | Rafa_roberto2004@yahoo.com.br")
    try:
        payload = json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":350,
            "messages":[{"role":"user","content":
                f"2 strong paragraphs, cover letter for {role} at {co}. "
                f"Candidate: 15yr Senior DA, Power BI PL-300, Tableau, SQL, Azure, BigQuery, Snowflake. "
                f"Wins: USD 9M+ savings, 70% latency cut, 200+ users. No greeting or sign-off. Output ONLY the 2 paragraphs."}]
        }).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages",data=payload,
            headers={"Content-Type":"application/json","x-api-key":AKEY,"anthropic-version":"2023-06-01"})
        with urllib.request.urlopen(req,timeout=20) as r:
            return json.loads(r.read())["content"][0]["text"].strip()
    except: return f"Senior Data Analyst, 15+ years, PL-300, USD 9M+ savings. Available for {role} at {co}."

# ── CAMADA 1: Detectar ATS real via Playwright ────────────────────────────────
ATS_PATTERNS = {
    "greenhouse.io": "greenhouse","lever.co": "lever",
    "ashbyhq.com": "ashby","smartrecruiters.com": "smartrecruiters",
    "workday.com": "workday","myworkdayjobs.com": "workday",
    "icims.com": "icims","taleo.net": "taleo","jobvite.com": "jobvite",
}

def detect_and_apply_ats(ctx, job):
    """Visita job page → detecta ATS → aplica diretamente"""
    pg = ctx.new_page()
    result = "unknown"
    apply_url = ""
    try:
        pg.goto(job["url"], timeout=20000)
        pg.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(2)

        # Clicar em Apply Now para detectar redirect
        for sel in ["a:has-text('Apply Now')","a:has-text('Apply now')",
                    "button:has-text('Apply Now')","a[href*='apply']",
                    "[data-cy='apply-btn']","a.apply-btn"]:
            try:
                el = pg.locator(sel).first
                if el.is_visible(timeout=1000):
                    # Capturar URL antes de clicar
                    with pg.expect_navigation(timeout=8000) as nav:
                        el.click()
                    apply_url = pg.url
                    break
            except: pass

        if not apply_url: apply_url = pg.url

        # Detectar qual ATS
        ats_type = next((v for k,v in ATS_PATTERNS.items() if k in apply_url), None)

        if ats_type == "greenhouse":
            pg.close()
            return apply_gh(ctx, job["company"], job["role"], apply_url, job["id"])
        elif ats_type == "lever":
            pg.close()
            return apply_lever(ctx, job["company"], job["role"], apply_url, job["id"])
        elif ats_type:
            pg.close()
            return f"ats_{ats_type}"
        else:
            # Tentar extrair link de apply do HTML
            html = pg.content()
            for pat in [r'href="(https://boards\.greenhouse\.io[^"]+)"',
                       r'href="(https://jobs\.lever\.co[^"]+)"',
                       r'href="(https://[^"]*greenhouse[^"]*)"']:
                m = re.search(pat, html)
                if m:
                    apply_url = m.group(1)
                    pg.close()
                    if "greenhouse" in apply_url:
                        return apply_gh(ctx, job["company"], job["role"], apply_url, job["id"])
                    return apply_lever(ctx, job["company"], job["role"], apply_url, job["id"])
            pg.close()
            return "no_ats_detected"
    except Exception as e:
        try: pg.close()
        except: pass
        return f"err:{str(e)[:30]}"

# ── CAMADA 2: Easy Apply via token ────────────────────────────────────────────
def easy_apply_with_token(token, job_id, company, role):
    """POST direto na API de apply do Dice usando token de sessão"""
    endpoints = [
        f"https://www.dice.com/api/apply/easy/{job_id}",
        f"https://platform.dice.com/apply/{job_id}",
    ]
    hdrs = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        "Origin": "https://www.dice.com",
        "Referer": f"https://www.dice.com/job-detail/{job_id}",
    }
    for ep in endpoints:
        try:
            req = urllib.request.Request(ep,
                data=json.dumps({"jobId":job_id,"company":company,"title":role}).encode(),
                method="POST", headers=hdrs)
            with urllib.request.urlopen(req, timeout=8) as r:
                resp = json.loads(r.read())
                if resp.get("success") or resp.get("applicationId") or resp.get("status")=="applied":
                    return "success_token"
        except urllib.error.HTTPError as e:
            if e.code in [401,403]: return "token_expired"
        except: pass
    return "token_apply_failed"

# ── CAMADA 3: Playwright Easy Apply ──────────────────────────────────────────
def easy_apply_playwright(ctx, job_id, company, role, url):
    pg = ctx.new_page()
    try:
        pg.goto(url, timeout=20000)
        pg.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(2)

        # Já deve estar logado (se camada 3 executou login antes)
        for sel in ["button:has-text('Easy Apply')","[data-cy='easy-apply-btn']",
                    "button.btn-apply","button:has-text('Apply Now')"]:
            try:
                el = pg.locator(sel).first
                if el.is_visible(timeout=1500):
                    el.click(); time.sleep(3)

                    # Preencher modal se aparecer
                    for fsel, fval in [
                        ("input[name='phone']", PROFILE["phone"]),
                        ("input[placeholder*='hone']", PROFILE["phone"]),
                        ("input[name*='name']", f"{PROFILE['first']} {PROFILE['last']}"),
                    ]:
                        try:
                            el2 = pg.locator(fsel).first
                            if el2.is_visible(timeout=500): el2.fill(fval)
                        except: pass

                    # Submit
                    for ss in ["button:has-text('Submit')","button[type='submit']"]:
                        try:
                            el3 = pg.locator(ss).first
                            if el3.is_visible(timeout=1000):
                                el3.click(); time.sleep(3)
                                pg.close(); return "easy_apply_success"
                        except: pass
                    pg.close(); return "easy_apply_clicked"
            except: pass
        pg.close(); return "no_easy_apply_btn"
    except Exception as e:
        try: pg.close()
        except: pass
        return f"err:{str(e)[:25]}"

# ── Greenhouse form ───────────────────────────────────────────────────────────
def apply_gh(ctx, co, role, url, jid):
    pg = ctx.new_page()
    try:
        pg.goto(url, timeout=20000)
        pg.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(2)
        if "greenhouse" not in pg.url: pg.close(); return "no_gh"

        cover = quick_cover(co, role)
        filled = 0
        for sel, val in [
            ("#first_name,input[name='first_name']", PROFILE["first"]),
            ("#last_name,input[name='last_name']", PROFILE["last"]),
            ("#email,input[name='email']", PROFILE["email"]),
            ("#phone,input[name='phone']", PROFILE["phone"]),
        ]:
            for s in sel.split(","):
                try:
                    el=pg.locator(s.strip()).first
                    if el.is_visible(timeout=500): el.clear(); el.fill(val); filled+=1; break
                except: pass

        for sel in ["input[name*='linkedin']","input[id*='linkedin']"]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=400): el.fill(PROFILE["linkedin"]); break
            except: pass

        if os.path.exists(PROFILE["cv"]):
            for sel in ["input[type='file'][name*='resume']","input[type='file']"]:
                try:
                    el=pg.locator(sel).first
                    if el.count(): el.set_input_files(PROFILE["cv"]); time.sleep(2); break
                except: pass

        for sel in ["textarea[name*='cover']","#cover_letter_text"]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=400):
                    el.fill(f"Dear {co} Hiring Team,\n\n{cover}\n\nBest,\nRafael Rodrigues\n{PROFILE['phone']}")
                    break
            except: pass

        if filled >= 2:
            for sel in ["input[type='submit']","button[type='submit']","#submit_app"]:
                try:
                    el=pg.locator(sel).first
                    if el.is_visible(timeout=1500):
                        el.click(force=True); time.sleep(5)
                        body = pg.inner_text("body")[:300].lower()
                        pg.close()
                        if any(w in body for w in ["thank","received","submitted","applied","success"]):
                            return "gh_success"
                        return "gh_submitted"
                except: pass
        pg.close(); return f"gh_fields_{filled}"
    except Exception as e: pg.close(); return f"gh_err:{str(e)[:25]}"

def apply_lever(ctx, co, role, url, jid):
    """Lever.co form — structure similar to Greenhouse"""
    pg = ctx.new_page()
    try:
        pg.goto(url, timeout=20000)
        pg.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(2)
        if "lever.co" not in pg.url: pg.close(); return "no_lever"

        cover = quick_cover(co, role)
        filled = 0
        for sel, val in [
            ("input[name='name']",  f"{PROFILE['first']} {PROFILE['last']}"),
            ("input[name='email']", PROFILE["email"]),
            ("input[name='phone']", PROFILE["phone"]),
            ("input[name*='linkedin']", PROFILE["linkedin"]),
        ]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=500): el.fill(val); filled+=1
            except: pass

        try:
            el=pg.locator("textarea[name='comments'],textarea[name='additionalInfo']").first
            if el.is_visible(timeout=400):
                el.fill(f"Dear {co} Hiring Team,\n\n{cover}\n\nBest,\nRafael Rodrigues")
        except: pass

        if os.path.exists(PROFILE["cv"]):
            try:
                el=pg.locator("input[type='file']").first
                if el.count(): el.set_input_files(PROFILE["cv"]); time.sleep(2)
            except: pass

        if filled >= 2:
            for sel in ["button[type='submit']","button:has-text('Submit application')",
                        "button:has-text('Submit')"]:
                try:
                    el=pg.locator(sel).first
                    if el.is_visible(timeout=1500):
                        el.click(force=True); time.sleep(5)
                        body = pg.inner_text("body")[:200].lower()
                        pg.close()
                        return "lever_success" if "thank" in body or "received" in body else "lever_submitted"
                except: pass
        pg.close(); return f"lever_fields_{filled}"
    except Exception as e: pg.close(); return f"lever_err:{str(e)[:25]}"

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n{'━'*58}")
    print(f"  🎲 DICE AUTONOMOUS APPLY v2 — {today}")
    print(f"  Camada 1: ATS Detection | 2: Token API | 3: Playwright")
    print(f"{'━'*58}\n")

    # Vagas do Dice MCP (coletadas via Claude MCP — chave diferente da API direta)
    DICE_JOBS = [
        # Easy Apply
        {"id":"dice_ea_04cc1460","company":"Central Point Partners",
         "role":"Power BI Data Analyst","url":"https://www.dice.com/job-detail/04cc1460-bede-4ced-adfd-428774213fad",
         "salary":"$75-85K","easy_apply":True},
        {"id":"dice_ea_b3273a76","company":"Innovative IT Technologies",
         "role":"Power BI Architect","url":"https://www.dice.com/job-detail/b3273a76-077f-4cfd-924f-f0d262fff6f7",
         "salary":"$69/h","easy_apply":True},
        # Non-Easy Apply (detectar ATS)
        {"id":"dice_na_31064754","company":"Experian",
         "role":"Solution Engineer Data Analytics","url":"https://www.dice.com/job-detail/31064754-835c-446a-a681-187d52d2edd7",
         "salary":"$100-174K","easy_apply":False},
        {"id":"dice_na_8afb7f9b","company":"Lumen",
         "role":"Senior Lead Data Architect","url":"https://www.dice.com/job-detail/8afb7f9b-4db7-4f42-aeef-1bdb987c1a95",
         "salary":"$132-176K","easy_apply":False},
        {"id":"dice_na_35f063c0","company":"Reed Elsevier / LexisNexis",
         "role":"Data Scientist","url":"https://www.dice.com/job-detail/35f063c0-4f5b-41ce-975d-b563bfef5ffc",
         "salary":"$115-192K","easy_apply":False},
    ]

    # Verificar token disponível
    token = get_dice_token()
    print(f"  Token Dice: {'✅ disponível' if token else '⚠️  não encontrado (capturar via dice-setup)'}")
    print(f"  Vagas para processar: {len([j for j in DICE_JOBS if not already_applied(j['id'])])}\n")

    ok = skip = err = 0

    with sync_playwright() as p:
        br = p.chromium.launch(headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
                  "--disable-blink-features=AutomationControlled"])
        ctx = br.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width":1280,"height":800}, locale="en-US")
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        # Tentar login Playwright (uma vez para Easy Apply)
        dice_logged = False
        if any(j["easy_apply"] for j in DICE_JOBS):
            print("  Tentando login Dice...")
            lp = ctx.new_page()
            try:
                lp.goto("https://www.dice.com/dashboard/login", timeout=15000)
                lp.wait_for_load_state("domcontentloaded", timeout=8000)
                time.sleep(2)
                for sel in ["#email","input[name='email']","input[type='email']"]:
                    try:
                        el=lp.locator(sel).first
                        if el.is_visible(timeout=1500): el.fill(DICE_EMAIL); break
                    except: pass
                for sel in ["button[type='submit']","button:has-text('Sign In')","button:has-text('Continue')"]:
                    try:
                        el=lp.locator(sel).first
                        if el.is_visible(timeout=800): el.click(); time.sleep(3); break
                    except: pass
                for sel in ["#password","input[type='password']"]:
                    try:
                        el=lp.locator(sel).first
                        if el.is_visible(timeout=3000): el.fill(DICE_PASSWORD); break
                    except: pass
                for sel in ["button[type='submit']","button:has-text('Sign In')"]:
                    try:
                        el=lp.locator(sel).first
                        if el.is_visible(timeout=800): el.click(); time.sleep(5); break
                    except: pass
                dice_logged = "dashboard" in lp.url or "jobs" in lp.url
                print(f"  Login: {'✅' if dice_logged else '⚠️  falhou'} → {lp.url[:50]}")
            except Exception as e:
                print(f"  Login erro: {str(e)[:40]}")
            lp.close()

        # Processar cada vaga
        print(f"\n{'─'*58}")
        for job in DICE_JOBS:
            if already_applied(job["id"]):
                print(f"  ⏭️  {job['company'][:25]} já aplicado"); skip+=1; continue

            co   = job["company"][:24]
            role = job["role"][:38]
            sal  = job.get("salary","")[:14]
            print(f"  [{('Easy' if job['easy_apply'] else ' ATS'):4}] {co:<24} {role:<38} {sal}", end=" ", flush=True)

            if job["easy_apply"]:
                # Camada 2: Token API
                if token:
                    jid_raw = job["id"].replace("dice_ea_","")
                    res = easy_apply_with_token(token, jid_raw, job["company"], job["role"])
                    if "success" in res: print(f"✅ {res}"); save(job["company"],job["role"],job["url"],job["id"],"success"); ok+=1; continue
                    elif "expired" in res: print(f"⚠️  token expirado")
                # Camada 3: Playwright
                if dice_logged:
                    res = easy_apply_playwright(ctx, job["id"].replace("dice_ea_",""), job["company"], job["role"], job["url"])
                    icon = "✅" if "success" in res else "📋"
                    print(f"{icon} {res}")
                    save(job["company"],job["role"],job["url"],job["id"],res)
                    if "success" in res: ok+=1
                    else: err+=1
                else:
                    print("⏸️  needs_token")
                    save(job["company"],job["role"],job["url"],job["id"],"needs_token")
            else:
                # Camada 1: Detectar ATS
                res = detect_and_apply_ats(ctx, job)
                icon = "✅" if any(k in res for k in ["success","submitted"]) else "🔗" if "ats_" in res else "⚠️ "
                print(f"{icon} {res}")
                save(job["company"],job["role"],job["url"],job["id"],res,salary=job.get("salary",""))
                if any(k in res for k in ["success","submitted"]): ok+=1
                else: err+=1
            time.sleep(2)

        br.close()

    print(f"\n{'━'*58}")
    print(f"  ✅ {ok} aplicados | ⏭️ {skip} já feitos | ⚠️  {err} outros")
    print(f"  {'Token pronto: camada 2 ativa' if token else 'Para ativar Easy Apply: tafita81.github.io/Repovazio/dice-setup.html'}")
    print(f"{'━'*58}\n")

if __name__ == "__main__":
    main()
