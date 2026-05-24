#!/usr/bin/env python3
"""
PLAYWRIGHT JOB HUNTER v2 — Corrigido
Suporta: Greenhouse direto + iframes embedded + React SPAs
Rafael Rodrigues | +5522992418257
"""
import os, time, json, datetime, urllib.request, urllib.parse, hashlib, sys
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

PHONE     = "+5522992418257"
REPLY_TO  = "Rafa_roberto2004@yahoo.com.br"
SUPA_URL  = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SUPA_KEY  = os.environ.get("SUPABASE_ANON_KEY","")
CV_PATH   = ".github/assets/rafael_cv.pdf"

PROFILE = {
    "first_name":"Rafael","last_name":"Rodrigues",
    "email":REPLY_TO,"phone":PHONE,
    "linkedin":"https://linkedin.com/in/rafael-r-a3946a15",
}
COVER = lambda role,co: f"""Dear {co} Hiring Team,
I am applying for the {role} position. Senior Data Analyst and Analytics Engineer with 15+ years of enterprise BI experience. Microsoft PL-300 Power BI Data Analyst certified. Available immediately.
Key: $9M+ operational savings · 70% latency reduction · 200+ users · 500M+ records/month
Phone: {PHONE} | LinkedIn: linkedin.com/in/rafael-r-a3946a15"""

ANSWER_MAP = {
    "authorized":True,"legally authorized":True,"work in the country":True,
    "sponsorship":False,"require.*sponsor":False,"visa sponsor":False,
    "how did you hear":"LinkedIn","how did you find":"LinkedIn",
    "referr":"LinkedIn","source":"LinkedIn","refer":"LinkedIn",
    "relocat":True,"remote":True,"work remotely":True,
    "salary":"120000","compensation":"120000","expected salary":"120000",
    "start":"Immediately","available to start":"Immediately",
    "gender":"Prefer not to say","race":"I don't wish to answer",
    "ethnicity":"I don't wish to answer","veteran":"I am not a protected veteran",
    "disability":"I don't wish to answer","years of experience":"15",
}
import re as _re
def get_answer(label):
    lb = label.lower()
    for pat, ans in ANSWER_MAP.items():
        if _re.search(str(pat), lb):
            if isinstance(ans, bool): return "Yes" if ans else "No"
            return str(ans)
    return ""

# ── Supabase ──────────────────────────────────────────────────────────────────
def supa(method, table, data=None, params=""):
    url = f"{SUPA_URL}/rest/v1/{table}?{params}"
    hdrs = {"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
            "Content-Type":"application/json","Prefer":"return=minimal"}
    body = json.dumps(data).encode() if data else None
    req  = urllib.request.Request(url,data=body,method=method,headers=hdrs)
    try:
        with urllib.request.urlopen(req,timeout=10) as r:
            try: return json.loads(r.read()), r.status
            except: return {}, r.status
    except urllib.error.HTTPError as e:
        return {}, e.code
    except: return {}, 0

def is_applied(eid):
    rows,_ = supa("GET","job_leads",params=f"external_id=eq.{urllib.parse.quote(str(eid))}&applied=eq.true&select=id")
    return isinstance(rows,list) and len(rows)>0

def mark_applied(eid,company,role,url,platform,method,status):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    supa("POST","job_leads",{"external_id":str(eid),"company":company,"role":role,
        "url":url,"platform":platform,"applied":True,"applied_at":now,"ats_type":method})
    supa("POST","job_applications",{"company":company,"role":role,"url":url,
        "application_method":method,"platform":platform,"status":status})

# ── Job Discovery ─────────────────────────────────────────────────────────────
GH_COMPANIES = [
    "braze","twilio","adyen","stripe","elastic","clickhouse","databricks",
    "datadog","honeycombio","grafana-labs","amplitude","mixpanel","segment",
    "fullstory","heap","pendo","thoughtspot","sigmacomputing","mode-analytics",
    "hex","metabase","dbt-labs","fivetran","airbyte","hightouch","census",
    "monte-carlo-data","brex","ramp","mercury","affirm","gusto","rippling",
    "lattice","cultureamp","asana","notion","webflow","figma","miro","loom",
    "zendesk","intercom","gong","outreach","salesloft","hubspot","coinbase",
    "kraken","robinhood","plaid","marqeta","payoneer","openai","cohere",
    "scale-ai","labelbox","weights-biases","arize-ai","shopify","narvar",
    "airbnb","expedia","hopper","tripadvisor","sorcero","corsearch","lexipol",
    "preply","airalo","moniepoint","nubank","vtex","rdstation","gitlab",
    "hashicorp","cloudflare","fastly","pagerduty","linear","zapier","sentry",
    "freshworks","docusign","twilio","okta","hashicorp","snyk","atlassian",
    "mongodb","cockroachdb","planetscale","neon","algolia","elastic",
    "contentful","typeform","hotjar","mixpanel","segment","heap","fullstory",
]
KEYWORDS = ["data analyst","power bi","business intelligence","bi developer",
            "analytics engineer","bi analyst","reporting analyst","data visualization"]

def discover_jobs():
    jobs = []; seen = set()
    for co in GH_COMPANIES:
        try:
            url = f"https://boards-api.greenhouse.io/v1/boards/{co}/jobs"
            req = urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=6) as r:
                data = json.loads(r.read())
                for j in data.get("jobs",[]):
                    jid = j["id"]; key = f"{co}_{jid}"
                    if key in seen: continue
                    seen.add(key)
                    if any(k in j.get("title","").lower() for k in KEYWORDS):
                        jobs.append({"id":f"gh_{co}_{jid}","company":co.replace("-"," ").title(),
                            "role":j["title"],"abs_url":j.get("absolute_url",""),
                            "platform":"Greenhouse","ats_type":"greenhouse_pw",
                            "co":co,"jid":jid})
        except: pass
        time.sleep(0.15)
    return jobs

# ── Form Fill Core ────────────────────────────────────────────────────────────
def fill_fields(ctx, profile, cv_path, cover):
    """Preenche campos padrão em qualquer contexto (page ou frame)"""
    # Nome
    for sel,val in [("input[name='first_name']",profile["first_name"]),
                    ("input[name='last_name']",profile["last_name"]),
                    ("input[name='email']",profile["email"]),
                    ("input[name='phone']",profile["phone"]),
                    ("input[name='candidate-location']","Brazil"),]:
        try:
            el = ctx.locator(sel).first
            if el.is_visible(timeout=1500): el.fill(val)
        except: pass
    # LinkedIn
    for sel in ["input[name*='linkedin']","input[placeholder*='LinkedIn']","input[id*='linkedin']"]:
        try:
            el = ctx.locator(sel).first
            if el.is_visible(timeout=800): el.fill(profile["linkedin"]); break
        except: pass
    # CV
    if cv_path and os.path.exists(cv_path):
        for sel in ["input[type='file'][name='resume']","input[type='file'][name*='resume']","input[type='file']"]:
            try:
                el = ctx.locator(sel).first
                if el.count() > 0: el.set_input_files(cv_path); time.sleep(1.5); break
            except: pass
    # Cover letter
    for sel in ["textarea[name='cover_letter']","textarea[id*='cover']","textarea[placeholder*='cover']"]:
        try:
            el = ctx.locator(sel).first
            if el.is_visible(timeout=800): el.fill(cover[:3000]); break
        except: pass
    # Selects
    for sel_el in ctx.locator("select").all():
        try:
            sel_id = sel_el.get_attribute("id") or ""
            label_txt = ""
            if sel_id:
                lbl = ctx.locator(f"label[for='{sel_id}']").first
                if lbl.count(): label_txt = lbl.inner_text()
            answer = get_answer(label_txt)
            if answer:
                for opt in sel_el.locator("option").all():
                    otxt = opt.inner_text().strip().lower()
                    if answer.lower() in otxt or otxt.startswith(answer.lower()[0]):
                        sel_el.select_option(label=opt.inner_text()); break
        except: pass
    # Radios
    done_names = set()
    for radio in ctx.locator("input[type='radio']").all():
        try:
            name = radio.get_attribute("name") or ""
            if name in done_names: continue
            rid = radio.get_attribute("id") or ""
            label_txt = ""
            if rid:
                lbl = ctx.locator(f"label[for='{rid}']").first
                if lbl.count(): label_txt = lbl.inner_text()
            answer = get_answer(label_txt) or get_answer(name.lower())
            if answer:
                val = radio.get_attribute("value") or ""
                if answer.lower() in val.lower() or val.lower() in ["yes","1","true"] and answer=="Yes":
                    radio.check(); done_names.add(name)
                elif val.lower() in ["no","0","false"] and answer=="No":
                    radio.check(); done_names.add(name)
        except: pass
    # Custom text questions
    for inp in ctx.locator("input[name^='question_'],textarea[name^='question_']").all():
        try:
            iid = inp.get_attribute("id") or ""
            label_txt = ""
            if iid:
                lbl = ctx.locator(f"label[for='{iid}']").first
                if lbl.count(): label_txt = lbl.inner_text()
            answer = get_answer(label_txt) or "LinkedIn"
            tag = inp.evaluate("el=>el.tagName")
            inp.fill(answer)
        except: pass

def try_submit(ctx, timeout=6000):
    """Tenta clicar no botão de submit. Retorna True se clicou."""
    SELECTORS = [
        "input[type='submit']",
        "button[type='submit']",
        "#submit_app",
        "button:has-text('Submit application')",
        "button:has-text('Submit Application')",
        "button:has-text('Submit')",
        "button:has-text('Apply for this Job')",
        "button:has-text('Send Application')",
        "button:has-text('Complete Application')",
        "[value='Submit Application']",
        "[data-qa='btn-submit']",
        "button.s-btn",
        "button.btn-apply",
    ]
    for sel in SELECTORS:
        try:
            el = ctx.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=1000):
                el.scroll_into_view_if_needed()
                el.click(force=True, timeout=timeout)
                time.sleep(3)
                return True
        except: pass
    return False

# ── Main form filler ──────────────────────────────────────────────────────────
def apply_to_job(page, job, cv_path):
    co   = job["co"]
    jid  = job["jid"]
    role = job["role"]
    company = job["company"]
    cover = COVER(role, company)

    # Estratégia 1: boards.greenhouse.io direto
    direct_url = f"https://boards.greenhouse.io/{co}/jobs/{jid}"
    try:
        page.goto(direct_url, timeout=20000)
        page.wait_for_load_state("networkidle", timeout=12000)
    except PWTimeout:
        return "timeout_loading"

    final_url = page.url
    on_greenhouse = "greenhouse.io" in final_url

    if on_greenhouse:
        # Preenchimento direto na página
        fill_fields(page, PROFILE, cv_path, cover)
        if try_submit(page):
            return "success_direct"
        return "no_submit_direct"

    # Estratégia 2: Empresa tem careers page própria com iframe Greenhouse
    time.sleep(2)  # aguardar JS carregar iframes
    page.wait_for_load_state("networkidle", timeout=8000)

    # Procurar iframe do Greenhouse
    gh_frame = None
    for frame in page.frames:
        if "greenhouse.io" in frame.url:
            gh_frame = frame
            break

    if not gh_frame:
        # Estratégia 3: Tentar absolute_url da empresa
        try:
            abs_url = job.get("abs_url","")
            if abs_url and abs_url != direct_url:
                page.goto(abs_url, timeout=15000)
                page.wait_for_load_state("networkidle", timeout=10000)
                time.sleep(2)
                for frame in page.frames:
                    if "greenhouse.io" in frame.url:
                        gh_frame = frame
                        break
        except: pass

    if not gh_frame:
        return "no_gh_iframe"

    # Preenchimento via iframe
    try:
        # Clicar "Enter manually" se existir (para formulários com upload first)
        for sel in ["button:has-text('Enter manually')","a:has-text('Enter manually')",
                    "button:has-text('manually')","[class*='manual-entry']"]:
            try:
                el = gh_frame.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click()
                    time.sleep(1.5)
                    break
            except: pass

        fill_fields(gh_frame, PROFILE, cv_path, cover)
        time.sleep(1)

        if try_submit(gh_frame):
            return "success_iframe"

        # Última tentativa: force-click em qualquer botão que pareça submit
        for btn in gh_frame.locator("button").all():
            try:
                txt = btn.inner_text().strip().lower()
                if any(k in txt for k in ["submit","apply","send","complete"]):
                    btn.scroll_into_view_if_needed()
                    btn.click(force=True, timeout=3000)
                    time.sleep(2)
                    return "success_iframe_force"
            except: pass

        return "no_submit_iframe"
    except Exception as e:
        return f"iframe_error:{str(e)[:40]}"

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    today = datetime.date.today().strftime("%d/%m/%Y %H:%M UTC")
    print(f"\n{'='*60}")
    print(f"  PLAYWRIGHT HUNTER v2 — {today}")
    print(f"  Tel: {PHONE}")
    print(f"{'='*60}\n")

    if not os.path.exists(CV_PATH):
        print(f"❌ CV não encontrado: {CV_PATH}"); return
    print(f"✅ CV: {os.path.getsize(CV_PATH):,} bytes\n")

    print("Descobrindo vagas Greenhouse...")
    all_jobs  = discover_jobs()
    new_jobs  = [j for j in all_jobs if not is_applied(j["id"])]
    print(f"Total: {len(all_jobs)} | Novas (não aplicadas): {len(new_jobs)}\n")

    if not new_jobs:
        print("✅ Nenhuma vaga nova — sistema atualizado!"); return

    results = {"success":0,"submitted":0,"failed":0,"skipped":0}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage",
                  "--disable-gpu","--disable-web-security",
                  "--allow-running-insecure-content"]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width":1280,"height":800},
            locale="en-US",
            java_script_enabled=True,
        )
        ctx.set_default_timeout(15000)

        print("── PREENCHENDO FORMULÁRIOS ─────────────────────────────────")
        for i, job in enumerate(new_jobs[:40], 1):
            page = ctx.new_page()
            print(f"  [{i:2}/{min(len(new_jobs),40)}] {job['company']:<25} {job['role'][:38]}", end=" ", flush=True)

            try:
                result = apply_to_job(page, job, CV_PATH)
            except Exception as e:
                result = f"exception:{str(e)[:30]}"
            finally:
                try: page.close()
                except: pass

            ok = "success" in result
            icon = "✅" if "success" in result else "📨" if "submitted" in result else "⚠️"
            print(f"{icon} {result}")

            status = "success" if ok else result
            mark_applied(job["id"],job["company"],job["role"],
                        job["abs_url"],job["platform"],"greenhouse_pw",status)

            if ok: results["success"] += 1
            elif "submitted" in result: results["submitted"] += 1
            else: results["failed"] += 1
            time.sleep(2)

        browser.close()

    total_ok = results["success"] + results["submitted"]
    print(f"\n{'='*60}")
    print(f"  ✅ Sucesso confirmado: {results['success']}")
    print(f"  📨 Submetidos:         {results['submitted']}")
    print(f"  ❌ Falhou:             {results['failed']}")
    print(f"  TOTAL APLICADO:       {total_ok}/{len(new_jobs[:40])}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
