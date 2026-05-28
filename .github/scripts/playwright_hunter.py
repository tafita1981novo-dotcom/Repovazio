#!/usr/bin/env python3
"""
PLAYWRIGHT JOB HUNTER v3 — Definitivo
Fluxo: absolute_url → click Apply → iframe GH → preencher → submit
Suporta: Greenhouse direto, iframe embed, custom pages (Stripe, Elastic...)
Rafael Rodrigues | +5522992418257
"""
import os, time, json, datetime, urllib.request, urllib.parse, hashlib, sys, re
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

PHONE    = "+5522992418257"
REPLY_TO = "Rafa_roberto2004@yahoo.com.br"
SUPA_URL = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SUPA_KEY = os.environ.get("SUPABASE_ANON_KEY","")
CV_PATH  = ".github/assets/rafael_cv.pdf"

PROFILE = {
    "first_name":"Rafael","last_name":"Rodrigues",
    "email":REPLY_TO,"phone":PHONE,
    "linkedin":"https://linkedin.com/in/rafael-r-a3946a15",
    "location":"Brazil","company":"Dataex","title":"Senior Data Analyst",
}
COVER = lambda role,co: f"""Dear {co} Hiring Team,

I am applying for the {role} position. Senior Data Analyst and Analytics Engineer with 15+ years of enterprise BI experience. Microsoft PL-300 Power BI Data Analyst and Tableau Desktop Specialist certified. Available immediately.

Key achievements:
• $9M+ operational savings — TIM/OI Telecommunications (500M+ records/month)
• 70% report latency reduction via DAX/SQL optimization — Keyrus consulting
• Enterprise analytics for 200+ business users across Financial Services, Retail, Telecom
• Multi-cloud: Power BI · BigQuery · Snowflake · Databricks SQL · Azure Synapse

Phone: {PHONE}
LinkedIn: linkedin.com/in/rafael-r-a3946a15

Available immediately for remote engagement.
Rafael Rodrigues | PL-300 | Tableau Specialist | {PHONE}"""

ANSWER_MAP = {
    r"authorized|legally authorized|work in the country|work authorization|eligible to work": "Yes",
    r"sponsorship|require.*sponsor|visa sponsor": "No",
    r"how did you hear|how did you find|referr|source": "LinkedIn",
    r"relocat|willing to relocat": "Yes",
    r"remote|work remotely": "Yes",
    r"salary|compensation|expected salary": "120000",
    r"start|available to start|when can you start": "Immediately",
    r"gender": "Prefer not to say",
    r"race|ethnicity": "I don't wish to answer",
    r"veteran": "I am not a protected veteran",
    r"disability": "I don't wish to answer",
    r"years of experience|years.*exp": "15",
    r"willing to work in.*office|hybrid|in.person": "Yes",
    r"us citizen|citizenship": "No",
}
def get_answer(label):
    lb = label.lower()
    for pat, ans in ANSWER_MAP.items():
        if re.search(pat, lb): return ans
    return ""

# Companies that don't use real Greenhouse (Workday, custom ATS, anti-bot)
BLOCKLIST = {
    "okta","datadog","brex","mongodb-commercial",
    "cloudflare","pagerduty","atlassian","snyk",
}

# ── Supabase ──────────────────────────────────────────────────────────────────
def supa_post(table, data):
    url  = f"{SUPA_URL}/rest/v1/{table}"
    hdrs = {"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
            "Content-Type":"application/json","Prefer":"return=minimal"}
    req  = urllib.request.Request(url, data=json.dumps(data).encode(), method="POST", headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=10) as r: return r.status
    except: return 0

def is_applied(eid):
    url  = f"{SUPA_URL}/rest/v1/job_leads?external_id=eq.{urllib.parse.quote(str(eid))}&applied=eq.true&select=id"
    hdrs = {"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}"}
    req  = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return len(json.loads(r.read())) > 0
    except: return False

def mark(eid, company, role, url, method, status):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    supa_post("job_leads", {"external_id":str(eid),"company":company,"role":role,
        "url":url,"platform":"Greenhouse","applied":True,"applied_at":now,"ats_type":method})
    supa_post("job_applications", {"company":company,"role":role,"url":url,
        "application_method":method,"platform":"Greenhouse","status":status})

# ── Discovery ─────────────────────────────────────────────────────────────────
GH_COMPANIES = [
    # BI/Analytics platforms
    "amplitude","mixpanel","segment","fullstory","heap","pendo","thoughtspot",
    "sigmacomputing","mode-analytics","hex","metabase","dbt-labs","fivetran",
    "airbyte","hightouch","census","monte-carlo-data","datafold","acceldata",
    # Tech unicorns using standard GH
    "braze","twilio","adyen","stripe","elastic","clickhouse","databricks",
    "honeycombio","grafana-labs","affirm","gusto","rippling","lattice",
    "cultureamp","asana","notion","webflow","figma","miro","loom","zendesk",
    "intercom","gong","outreach","salesloft","hubspot","coinbase","kraken",
    "robinhood","plaid","marqeta","payoneer","openai","cohere","scale-ai",
    "labelbox","weights-biases","arize-ai","shopify","narvar","airbnb",
    "expedia","hopper","tripadvisor","sorcero","corsearch","lexipol","preply",
    "airalo","moniepoint","elfbeauty","preply","ciklum","lexipol","trilogyfederal",
    "nubank","vtex","rdstation","gitlab","hashicorp",
    "fastly","linear","zapier","sentry","freshworks","docusign","okta",
    "mongodb","algolia","elastic","contentful","typeform","hotjar",
    # Additional companies
    "benchling","lattice","rippling","deel","remote","oyster",
    "lumentum","verkada","vanta","ironclad","watershed","watershed-climates",
    "glean-systems","retool","replit","cursor","vercel-jobs","supabase",
    "planetscale","neon","render","railway","fly-io","turso",
    "dagster-io","prefect","astronomer","mage-ai",
    "highspot","seismic","showpad","klue","crayon-io",
    "brainware","hinge-health","livongo","sword-health","calm",
    "headspace","noom","weight-watchers","beachbody",
    "coda","airtable","clickup","linear","shortcut","basecamp",
    "notion-so","craft-docs","obsidian","roamresearch",
    "figma-design","invision-app","zeplin","abstract","avocode",
    "miro-so","mural","conceptboard","stormboard",
    "amplitude-dp","mixpanel-js","segment-io","heap-io","pendo-io",
    "fullstory-io","smartlook","hotjar-io","clarity-ms",
    "posthog","june-so","koala","june-analytics",
    # Financial services
    "brex-fintech","ramp-financial","mercury-bank","novo-bank","found",
    "relay-fi","lili-bank","bluevine","kabbage","fundbox",
    "affirm-loan","afterpay","klarna-us","zip-co","sezzle",
    "stripe-payments","adyen-global","checkout-com","rapyd","payoneer-global",
    # More startups
    "clio","litera","ironclad-legal","docusign-agreements","pandadoc",
    "contractpodai","lexcheck","evisort","superdraft",
    "clearbit-data","lusha-tech","zoominfo-inc","apollo-io","hunter-io",
    "seamless-ai","cognism","demandbase","6sense","intent","leadgenius",
]

KEYWORDS = ["data analyst","power bi","business intelligence","bi developer",
            "analytics engineer","bi analyst","reporting analyst","data visualization",
            "bi engineer","analytics engineer","insight analyst"]

def discover_jobs():
    jobs = []; seen = set()
    for co in GH_COMPANIES:
        if co in BLOCKLIST: continue
        try:
            url = f"https://boards-api.greenhouse.io/v1/boards/{co}/jobs"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
                for j in data.get("jobs",[]):
                    jid = j["id"]; key = f"{co}_{jid}"
                    if key in seen: continue; seen.add(key)
                    if any(k in j.get("title","").lower() for k in KEYWORDS):
                        jobs.append({
                            "id": f"gh_{co}_{jid}",
                            "company": co.replace("-"," ").title(),
                            "role": j["title"],
                            "abs_url": j.get("absolute_url",""),
                            "co": co, "jid": jid
                        })
        except: pass
        time.sleep(0.15)
    return jobs

# ── Fill helpers ──────────────────────────────────────────────────────────────
def fill_standard_fields(ctx, profile, cv_path, cover):
    """Preenche campos padrão do Greenhouse em qualquer contexto"""
    # Campos de texto padrão
    field_map = {
        "input[name='first_name']":        profile["first_name"],
        "input[name='last_name']":         profile["last_name"],
        "input[name='email']":             profile["email"],
        "input[name='phone']":             profile["phone"],
        "input[name='candidate-location']":"Brazil",
        "input[id='candidate-location']":  "Brazil",
    }
    for sel, val in field_map.items():
        try:
            el = ctx.locator(sel).first
            if el.is_visible(timeout=1000): el.fill(val)
        except: pass

    # LinkedIn
    for sel in ["input[name*='linkedin']","input[placeholder*='LinkedIn']",
                "input[id*='linkedin']","input[name*='Link']"]:
        try:
            el = ctx.locator(sel).first
            if el.is_visible(timeout=600): el.fill(profile["linkedin"]); break
        except: pass

    # CV upload
    if cv_path and os.path.exists(cv_path):
        for sel in ["input[type='file'][name='resume']",
                    "input[type='file'][name*='resume']",
                    "input[type='file'][id*='resume']",
                    "input[type='file']"]:
            try:
                el = ctx.locator(sel).first
                if el.count() > 0:
                    el.set_input_files(cv_path)
                    time.sleep(2); break
            except: pass

    # Cover letter
    for sel in ["textarea[name='cover_letter']","textarea[id*='cover']",
                "textarea[placeholder*='cover']","textarea[name*='cover']"]:
        try:
            el = ctx.locator(sel).first
            if el.is_visible(timeout=600): el.fill(cover[:3000]); break
        except: pass

    # Selects (dropdowns)
    for sel_el in ctx.locator("select").all():
        try:
            sel_id  = sel_el.get_attribute("id") or ""
            lbl_txt = ""
            if sel_id:
                lbl = ctx.locator(f"label[for='{sel_id}']").first
                if lbl.count(): lbl_txt = lbl.inner_text()
            ans = get_answer(lbl_txt)
            if not ans: continue
            for opt in sel_el.locator("option").all():
                otxt = opt.inner_text().strip().lower()
                if ans.lower() in otxt or otxt.startswith(ans.lower()[:3]):
                    sel_el.select_option(label=opt.inner_text()); break
        except: pass

    # Radio buttons
    done = set()
    for radio in ctx.locator("input[type='radio']").all():
        try:
            name = radio.get_attribute("name") or ""
            if name in done: continue
            rid  = radio.get_attribute("id") or ""
            lbl  = ctx.locator(f"label[for='{rid}']").first
            lbl_txt = lbl.inner_text() if lbl.count() else name
            ans  = get_answer(lbl_txt)
            val  = radio.get_attribute("value") or ""
            if ans == "Yes" and val.lower() in ["yes","1","true"]:
                radio.check(); done.add(name)
            elif ans == "No" and val.lower() in ["no","0","false"]:
                radio.check(); done.add(name)
        except: pass

    # Custom text questions (question_XXXXXX)
    for inp in ctx.locator("input[name^='question_'],textarea[name^='question_']").all():
        try:
            iid  = inp.get_attribute("id") or ""
            lbl  = ctx.locator(f"label[for='{iid}']").first
            lbl_txt = lbl.inner_text() if lbl.count() else ""
            ans  = get_answer(lbl_txt) or "LinkedIn"
            inp.fill(ans)
        except: pass

def find_and_submit(ctx, timeout=8000):
    """Encontra e clica no botão de submit. Retorna True se clicou."""
    SUBMIT_SELECTORS = [
        "input[type='submit']",
        "button[type='submit']",
        "#submit_app",
        "[id*='submit_app']",
        "button:has-text('Submit application')",
        "button:has-text('Submit Application')",
        "button:has-text('Submit')",
        "button:has-text('Apply for this Job')",
        "button:has-text('Apply for This Job')",
        "button:has-text('Send Application')",
        "button:has-text('Complete Application')",
        "button:has-text('Send my Application')",
        "[value='Submit Application']",
        "[value='Submit application']",
        "[data-qa='btn-submit']",
        "[data-testid*='submit']",
        "[data-testid*='apply']",
        "button.s-btn[type='submit']",
        "button[class*='submit']",
        "button[class*='apply-btn']",
        "form button:last-of-type",
    ]
    for sel in SUBMIT_SELECTORS:
        try:
            el = ctx.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=800):
                el.scroll_into_view_if_needed()
                el.click(force=True, timeout=timeout)
                time.sleep(3)
                return True
        except: pass
    return False

def find_gh_iframe(page, wait_extra=0):
    """Procura iframe do Greenhouse na página"""
    if wait_extra > 0: time.sleep(wait_extra)
    for frame in page.frames:
        if "greenhouse.io" in frame.url:
            return frame
    return None

def prepare_iframe(frame):
    """Clica 'Enter manually' se necessário e aguarda formulário carregar"""
    for sel in ["button:has-text('Enter manually')",
                "a:has-text('Enter manually')",
                "button:has-text('manually')",
                "[class*='manual']"]:
        try:
            el = frame.locator(sel).first
            if el.is_visible(timeout=2000):
                el.click(); time.sleep(2); break
        except: pass

# ── Main apply function ───────────────────────────────────────────────────────
def apply_job(page, job, cv_path):
    co      = job["co"]
    jid     = job["jid"]
    role    = job["role"]
    company = job["company"]
    abs_url = job["abs_url"]
    cover   = COVER(role, company)

    # ── ESTRATÉGIA 1: Ir para absolute_url (pode já ter iframe GH) ────────────
    try:
        nav_url = abs_url if abs_url else f"https://boards.greenhouse.io/{co}/jobs/{jid}"
        page.goto(nav_url, timeout=20000)
        page.wait_for_load_state("networkidle", timeout=12000)
        time.sleep(2)
    except PWTimeout:
        return "timeout"

    # Verificar se estamos direto no Greenhouse
    if "greenhouse.io" in page.url:
        fill_standard_fields(page, PROFILE, cv_path, cover)
        if find_and_submit(page):
            return "success_direct"

    # Procurar iframe do Greenhouse (aguardar JS carregar)
    frame = find_gh_iframe(page, wait_extra=1)

    # ── ESTRATÉGIA 2: Clicar botão "Apply" na página ──────────────────────────
    if not frame:
        for sel in ["a:has-text('Apply for this role')",
                    "a:has-text('Apply for this Job')",
                    "a:has-text('Apply Now')",
                    "button:has-text('Apply')",
                    "a[href*='/apply']",
                    "[class*='apply-button']",
                    "[data-testid*='apply']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1500):
                    href = el.get_attribute("href") or ""
                    if href and href.startswith("/"):
                        base = "/".join(page.url.split("/")[:3])
                        page.goto(base + href, timeout=15000)
                    elif href:
                        page.goto(href, timeout=15000)
                    else:
                        el.click(timeout=5000)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    time.sleep(2)
                    frame = find_gh_iframe(page, wait_extra=1)
                    break
            except: pass

    # ── ESTRATÉGIA 3: Ir direto para boards.greenhouse.io ────────────────────
    if not frame:
        try:
            direct = f"https://boards.greenhouse.io/{co}/jobs/{jid}"
            page.goto(direct, timeout=15000)
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(2)
            if "greenhouse.io" in page.url:
                fill_standard_fields(page, PROFILE, cv_path, cover)
                if find_and_submit(page):
                    return "success_direct_fallback"
            frame = find_gh_iframe(page, wait_extra=1)
        except: pass

    # ── PREENCHER VIA IFRAME ──────────────────────────────────────────────────
    if frame:
        try:
            prepare_iframe(frame)
            fill_standard_fields(frame, PROFILE, cv_path, cover)
            time.sleep(1)
            if find_and_submit(frame):
                return "success_iframe"
            # Tentar force-click em qualquer botão parecido com submit
            for btn in frame.locator("button").all():
                try:
                    txt = btn.inner_text().strip().lower()
                    if any(k in txt for k in ["submit","apply","send","complete","continue"]):
                        btn.scroll_into_view_if_needed()
                        btn.click(force=True, timeout=4000)
                        time.sleep(2)
                        return "success_iframe_forced"
                except: pass
            return "iframe_no_submit"
        except Exception as e:
            return f"iframe_error:{str(e)[:30]}"

    return "no_form_found"

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    print(f"\n{'='*65}")
    print(f"  PLAYWRIGHT HUNTER v3 — {today}")
    print(f"  Tel: {PHONE}")
    print(f"{'='*65}\n")

    if not os.path.exists(CV_PATH):
        print(f"❌ CV não encontrado: {CV_PATH}"); return
    print(f"✅ CV: {os.path.getsize(CV_PATH):,} bytes\n")

    print("Descobrindo vagas Greenhouse...")
    all_jobs = discover_jobs()
    new_jobs = [j for j in all_jobs if not is_applied(j["id"])]
    print(f"Total: {len(all_jobs)} | Novas: {len(new_jobs)}\n")

    if not new_jobs:
        print("✅ Nenhuma vaga nova."); return

    ok = fail = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage",
                  "--disable-gpu","--window-size=1280,800"]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width":1280,"height":800},
            locale="en-US",
        )

        print("── PREENCHENDO FORMULÁRIOS ─────────────────────────────────────")
        for i, job in enumerate(new_jobs[:50], 1):
            page = ctx.new_page()
            co_label = job["company"][:22]
            role_label = job["role"][:38]
            print(f"  [{i:2}/{min(len(new_jobs),50)}] {co_label:<24} {role_label}", end=" ", flush=True)

            try:
                result = apply_job(page, job, CV_PATH)
            except Exception as e:
                result = f"exc:{str(e)[:30]}"
            finally:
                try: page.close()
                except: pass

            success = "success" in result
            icon = "✅" if success else "📨" if "forced" in result else "⚠️"
            print(f"{icon} {result}")

            mark(job["id"], job["company"], job["role"],
                 job["abs_url"], "greenhouse_pw",
                 "success" if success else result)

            if success: ok += 1
            else: fail += 1
            time.sleep(2)

        browser.close()

    print(f"\n{'='*65}")
    print(f"  ✅ Aplicados com sucesso: {ok}")
    print(f"  ⚠️  Não aplicados:        {fail}")
    print(f"  TOTAL:                   {ok+fail}/{min(len(new_jobs),50)}")
    print(f"{'='*65}\n")

if __name__ == "__main__":
    main()
