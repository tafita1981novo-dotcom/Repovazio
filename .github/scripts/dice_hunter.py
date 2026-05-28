#!/usr/bin/env python3
"""
DICE HUNTER — Login + Easy Apply
Rafael Rodrigues | tafita81@gmail.com
"""
import os, time, json, datetime, urllib.request, urllib.parse, re
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

EMAIL  = os.environ.get("DICE_EMAIL", "tafita81@gmail.com")
PASSW  = os.environ.get("DICE_PASSWORD", "")
PHONE  = "+5522992418257"
CV     = ".github/assets/rafael_cv.pdf"
SUPA   = os.environ.get("SUPABASE_URL", "https://tpjvalzwkqwttvmszvie.supabase.co")
KEY    = os.environ.get("SUPABASE_ANON_KEY", "")

SEARCHES = [
    "Power BI Developer remote",
    "Senior Data Analyst remote",
    "Analytics Engineer remote",
    "Business Intelligence Analyst remote",
]

def supa_post(table, data):
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}",
        data=json.dumps(data).encode(), method="POST",
        headers={"apikey": KEY, "Authorization": f"Bearer {KEY}",
                 "Content-Type": "application/json", "Prefer": "return=minimal"})
    try:
        with urllib.request.urlopen(req, timeout=8): pass
    except: pass

def is_applied(job_id):
    url = f"{SUPA}/rest/v1/job_applications?job_id=eq.{urllib.parse.quote(str(job_id))}&status=eq.success&select=id&limit=1"
    req = urllib.request.Request(url, headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            return len(json.loads(r.read())) > 0
    except: return False

def save(company, role, url, job_id, status):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    supa_post("job_applications", {
        "company": company, "role": role, "url": url, "job_id": str(job_id),
        "application_method": "dice_easy_apply", "status": status,
        "platform": "Dice", "applied_at": now, "email": EMAIL
    })

def login_dice(page):
    """Faz login na conta Dice"""
    try:
        page.goto("https://www.dice.com/dashboard/login", timeout=20000)
        page.wait_for_load_state("domcontentloaded", timeout=12000)
        time.sleep(2)

        # Preencher email
        for sel in ["#email", "input[name='email']", "input[type='email']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.fill(EMAIL); break
            except: pass

        # Clicar Continue / Next
        for sel in ["button:has-text('Sign In')", "button:has-text('Continue')",
                    "button[type='submit']", "#loginButton"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1000): el.click(); time.sleep(2); break
            except: pass

        # Preencher senha
        for sel in ["#password", "input[name='password']", "input[type='password']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.fill(PASSW); break
            except: pass

        # Submit
        for sel in ["button:has-text('Sign In')", "button[type='submit']", "#loginButton"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1000): el.click(); time.sleep(4); break
            except: pass

        # Verificar login
        time.sleep(3)
        url = page.url
        logged = any(k in url for k in ["dashboard", "find-jobs", "profile", "home"])
        print(f"  Login Dice: {'✅' if logged else '⚠️'} ({url[:60]})")
        return logged
    except Exception as e:
        print(f"  Login Dice erro: {str(e)[:50]}")
        return False

def search_and_apply(ctx, search_query, logged_page):
    """Busca vagas e aplica via Easy Apply"""
    jobs_applied = 0
    try:
        q = urllib.parse.quote(search_query)
        url = f"https://www.dice.com/jobs?q={q}&countryCode=US&radius=30&radiusUnit=mi&page=1&pageSize=20&filters.workplaceTypes=Remote&filters.employmentType=FULLTIME&language=en"

        page = ctx.new_page()
        page.goto(url, timeout=20000)
        page.wait_for_load_state("domcontentloaded", timeout=12000)
        time.sleep(3)

        html = page.content()

        # Extrair job IDs da página
        job_ids = re.findall(r'"id"\s*:\s*"([a-f0-9]{32})"', html)
        titles  = re.findall(r'"title"\s*:\s*"([^"]{5,80})"', html)
        cos     = re.findall(r'"companyName"\s*:\s*"([^"]{2,50})"', html)

        print(f"  [{search_query[:30]}] {len(job_ids)} vagas encontradas")

        for i, job_id in enumerate(job_ids[:10]):
            if is_applied(f"dice_{job_id}"): continue

            title  = titles[i] if i < len(titles) else "Data Analyst"
            co     = cos[i]    if i < len(cos)    else "?"
            job_url = f"https://www.dice.com/job-detail/{job_id}"

            print(f"    [{i+1}] {co[:20]:<22} {title[:40]}", end=" ", flush=True)

            # Navegar para a vaga
            jpage = ctx.new_page()
            try:
                jpage.goto(job_url, timeout=20000)
                jpage.wait_for_load_state("domcontentloaded", timeout=12000)
                time.sleep(2)

                # Clicar em Easy Apply
                applied = False
                for sel in [
                    "button:has-text('Easy Apply')",
                    "[data-cy='easy-apply-btn']",
                    "button.btn-apply",
                    "button:has-text('Apply Now')",
                ]:
                    try:
                        el = jpage.locator(sel).first
                        if el.is_visible(timeout=2000):
                            el.click()
                            time.sleep(3)

                            # Modal de aplicação — preencher se necessário
                            for fsel, fval in [
                                ("input[name='phone']", PHONE),
                                ("input[placeholder*='phone']", PHONE),
                                ("input[placeholder*='Phone']", PHONE),
                            ]:
                                try:
                                    fel = jpage.locator(fsel).first
                                    if fel.is_visible(timeout=800):
                                        fel.fill(fval)
                                except: pass

                            # Submit da modal
                            for ssel in ["button:has-text('Submit')", "button:has-text('Apply')",
                                         "button[type='submit']"]:
                                try:
                                    sel_el = jpage.locator(ssel).first
                                    if sel_el.is_visible(timeout=1500):
                                        sel_el.click()
                                        time.sleep(3)
                                        applied = True
                                        break
                                except: pass

                            if applied: break
                    except: pass

                status = "success" if applied else "easy_apply_clicked"
                icon   = "✅" if applied else "📋"
                print(f"{icon} {'aplicado' if applied else 'clicado'}")
                save(co, title, job_url, f"dice_{job_id}", status)
                if applied: jobs_applied += 1
            except Exception as e:
                print(f"❌ {str(e)[:30]}")
            finally:
                try: jpage.close()
                except: pass
            time.sleep(2)

        page.close()
    except Exception as e:
        print(f"  Erro busca: {str(e)[:50]}")

    return jobs_applied

def main():
    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n{'='*60}")
    print(f"  DICE HUNTER — {today}")
    print(f"  {EMAIL}")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled",
                  "--disable-dev-shm-usage"]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        # Login
        login_page = ctx.new_page()
        logged = login_dice(login_page)
        login_page.close()

        if not logged:
            print("⚠️  Login falhou — tentando sem login (vagas públicas)")

        # Buscar e aplicar
        total = 0
        for q in SEARCHES:
            total += search_and_apply(ctx, q, logged)
            time.sleep(2)

        browser.close()

    print(f"\n  ✅ {total} candidaturas Dice | {today}")

if __name__ == "__main__":
    main()
