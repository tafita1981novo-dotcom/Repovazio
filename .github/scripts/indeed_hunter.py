#!/usr/bin/env python3
"""
INDEED HUNTER — Login + Easy Apply
Rafael Rodrigues | tafita81@gmail.com
"""
import os, time, json, datetime, urllib.request, urllib.parse, re
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

EMAIL  = os.environ.get("INDEED_EMAIL", "tafita81@gmail.com")
PASSW  = os.environ.get("INDEED_PASSWORD", "")
PHONE  = "+5522992418257"
CV     = ".github/assets/rafael_cv.pdf"
SUPA   = os.environ.get("SUPABASE_URL", "https://tpjvalzwkqwttvmszvie.supabase.co")
KEY    = os.environ.get("SUPABASE_ANON_KEY", "")

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
        "application_method": "indeed_easy_apply", "status": status,
        "platform": "Indeed", "applied_at": now, "email": EMAIL
    })

def login_indeed(page):
    """Login no Indeed"""
    try:
        page.goto("https://secure.indeed.com/auth?hl=en&co=US", timeout=20000)
        page.wait_for_load_state("domcontentloaded", timeout=12000)
        time.sleep(2)

        # Email
        for sel in ["input[name='__email']", "#ifl-InputFormField-3", "input[type='email']",
                    "input[autocomplete='username']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000): el.fill(EMAIL); break
            except: pass

        for sel in ["button:has-text('Continue with email')", "button[type='submit']",
                    "#login-submit-component"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1500): el.click(); time.sleep(3); break
            except: pass

        # Senha
        for sel in ["input[name='__password']", "input[type='password']",
                    "#ifl-InputFormField-7"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=4000): el.fill(PASSW); break
            except: pass

        for sel in ["button:has-text('Sign in')", "button[type='submit']",
                    "#login-submit-component"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1500): el.click(); time.sleep(5); break
            except: pass

        time.sleep(3)
        url = page.url
        logged = any(k in url for k in ["dashboard", "jobs", "profile", "myjobs", "account"])
        print(f"  Login Indeed: {'✅' if logged else '⚠️'} ({url[:60]})")
        return logged
    except Exception as e:
        print(f"  Login Indeed erro: {str(e)[:50]}")
        return False

def search_and_apply_indeed(ctx):
    """Busca vagas e aplica via Easy Apply no Indeed"""
    total = 0
    searches = [
        ("Power BI Developer", "remote"),
        ("Senior Data Analyst", "remote"),
        ("Analytics Engineer", "remote"),
        ("Business Intelligence Analyst", "remote"),
    ]

    for query, loc in searches:
        try:
            q   = urllib.parse.quote(query)
            l   = urllib.parse.quote(loc)
            url = f"https://www.indeed.com/jobs?q={q}&l={l}&jt=fulltime&sort=date&remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11"

            page = ctx.new_page()
            page.goto(url, timeout=20000)
            page.wait_for_load_state("domcontentloaded", timeout=12000)
            time.sleep(3)

            # Extrair job keys
            html    = page.content()
            job_keys = re.findall(r'"jobKey"\s*:\s*"([^"]{8,20})"', html)
            job_keys += re.findall(r'data-jk="([^"]{8,20})"', html)
            job_keys = list(dict.fromkeys(job_keys))  # dedup

            print(f"  [{query[:25]}] {len(job_keys)} vagas")

            for jk in job_keys[:8]:
                if is_applied(f"indeed_{jk}"): continue

                job_url = f"https://www.indeed.com/viewjob?jk={jk}"
                jpage   = ctx.new_page()
                try:
                    jpage.goto(job_url, timeout=20000)
                    jpage.wait_for_load_state("domcontentloaded", timeout=12000)
                    time.sleep(2)

                    title = "Data Analyst"
                    co    = "?"
                    try:
                        title = jpage.locator("h1.jobsearch-JobInfoHeader-title").first.inner_text()[:60]
                    except: pass
                    try:
                        co = jpage.locator("[data-testid='inlineHeader-companyName']").first.inner_text()[:30]
                    except: pass

                    print(f"    {co[:20]:<22} {title[:38]}", end=" ", flush=True)

                    # Clicar Apply / Easy Apply
                    applied = False
                    for sel in [
                        "#indeedApplyButton",
                        "button:has-text('Apply now')",
                        "button:has-text('Easy Apply')",
                        "[data-testid='apply-button']",
                        "a:has-text('Apply now')",
                    ]:
                        try:
                            el = jpage.locator(sel).first
                            if el.is_visible(timeout=2000):
                                el.click()
                                time.sleep(4)
                                new_url = jpage.url

                                # Se abriu formulário Indeed
                                if "smartapply" in new_url or "apply" in new_url:
                                    # Preencher campos
                                    for fsel, fval in [
                                        ("input[name='applicant.phoneNumber']", PHONE),
                                        ("input[placeholder*='Phone']", PHONE),
                                        ("input[name='applicant.name.first']", "Rafael"),
                                        ("input[name='applicant.name.last']", "Rodrigues"),
                                    ]:
                                        try:
                                            fel = jpage.locator(fsel).first
                                            if fel.is_visible(timeout=800): fel.fill(fval)
                                        except: pass

                                    # Continuar e submeter
                                    for nsel in ["button:has-text('Continue')", "button:has-text('Submit')",
                                                 "button[type='submit']"]:
                                        try:
                                            nel = jpage.locator(nsel).first
                                            if nel.is_visible(timeout=1500):
                                                nel.click()
                                                time.sleep(3)
                                                applied = True
                                                break
                                        except: pass
                                break
                        except: pass

                    status = "success" if applied else "easy_apply_clicked"
                    icon   = "✅" if applied else "📋"
                    print(f"{icon}")
                    save(co, title, job_url, f"indeed_{jk}", status)
                    if applied: total += 1
                except Exception as e:
                    print(f"❌ {str(e)[:30]}")
                finally:
                    try: jpage.close()
                    except: pass
                time.sleep(2)

            page.close()
        except Exception as e:
            print(f"  Erro: {str(e)[:50]}")

    return total

def main():
    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n{'='*60}")
    print(f"  INDEED HUNTER — {today}")
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

        login_page = ctx.new_page()
        logged = login_indeed(login_page)
        login_page.close()

        if not logged:
            print("⚠️  Login falhou — tentando sem login")

        total = search_and_apply_indeed(ctx)
        browser.close()

    print(f"\n  ✅ {total} candidaturas Indeed | {today}")

if __name__ == "__main__":
    main()
