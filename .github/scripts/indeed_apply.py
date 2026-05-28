#!/usr/bin/env python3
"""Indeed Apply — busca vagas + aplica via Playwright com cookies"""
import os, sys, json, time, datetime, urllib.request, urllib.parse, re

sys.path.insert(0, os.path.dirname(__file__))
from session_manager import load_session, save_session, stealth_context, sb_upsert, sb_get, human_type

SUPA = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
KEY  = os.environ.get("SUPABASE_ANON_KEY","")

PROFILE = {
    "first":"Rafael","last":"Rodrigues",
    "email":"Rafa_roberto2004@yahoo.com.br",
    "phone":"+5522992418257","cv":".github/assets/rafael_cv.pdf",
}

QUERIES = ["power bi developer","senior data analyst","business intelligence analyst","analytics engineer"]
COUNTRIES = [
    ("us","United+States"),("ca","Canada"),("gb","United+Kingdom"),
    ("de","Germany"),("au","Australia"),
]

def already_applied(jid):
    r = sb_get(f"job_applications?job_id=eq.{urllib.parse.quote(str(jid))}&select=id&limit=1")
    return isinstance(r,list) and len(r)>0

def save(co, role, url, jid, status, country="US"):
    sb_upsert("job_applications",{
        "company":co,"role":role,"url":url,"job_id":str(jid),
        "application_method":"indeed_apply","status":status,
        "platform":"Indeed","applied_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "email":PROFILE["email"],"country":country
    })

def search_rss(query, country_code, limit=10):
    """Busca vagas via RSS do Indeed"""
    jobs = []
    try:
        url = (f"https://{country_code}.indeed.com/jobs?q={urllib.parse.quote(query)}"
               f"&remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11&sort=date&limit={limit}")
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode("utf-8", errors="ignore")
        # Extrair job IDs
        jks = re.findall(r'"jobkey"\s*:\s*"([^"]+)"', html)
        titles = re.findall(r'"title"\s*:\s*"([^"]+)"', html)
        companies = re.findall(r'"company"\s*:\s*"([^"]+)"', html)
        for i, jk in enumerate(jks[:limit]):
            jobs.append({
                "id": f"indeed_{country_code}_{jk}",
                "title": titles[i] if i < len(titles) else query,
                "company": companies[i] if i < len(companies) else "?",
                "url": f"https://{country_code}.indeed.com/viewjob?jk={jk}",
                "country": country_code.upper()
            })
    except: pass
    return jobs

def apply_indeed(ctx, job, session=None):
    """Tenta aplicar via Indeed — detecta ATS ou Indeed Apply"""
    pg = ctx.new_page()
    try:
        if session:
            for c in session.get("cookies",[]): 
                try: ctx.add_cookies([c])
                except: pass
        pg.goto(job["url"], timeout=20000)
        pg.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(2)
        # Clicar Apply
        for sel in ["button:has-text('Apply now')","a:has-text('Apply now')","#indeedApplyButton",
                    "button:has-text('Apply on company site')"]:
            try:
                el = pg.locator(sel).first
                if el.is_visible(timeout=1500):
                    # Checar se vai para ATS externo
                    with pg.expect_navigation(timeout=6000) as nav:
                        el.click()
                    new_url = pg.url
                    # Se for Greenhouse/Lever — aplicar via formulário
                    if "greenhouse.io" in new_url: pg.close(); return "external_gh", new_url
                    if "lever.co" in new_url: pg.close(); return "external_lever", new_url
                    if "workday" in new_url: pg.close(); return "external_workday", new_url
                    # Indeed Apply direto
                    for fsel, fval in [
                        ("input[name='name.first']", PROFILE["first"]),
                        ("input[name='name.last']", PROFILE["last"]),
                        ("input[type='email']", PROFILE["email"]),
                        ("input[name='phoneNumber']", PROFILE["phone"]),
                    ]:
                        try:
                            el2=pg.locator(fsel).first
                            if el2.is_visible(timeout=400): el2.fill(fval)
                        except: pass
                    for ss in ["button:has-text('Submit')","button:has-text('Apply')","button[type='submit']"]:
                        try:
                            el3 = pg.locator(ss).first
                            if el3.is_visible(timeout=1000):
                                el3.click(); time.sleep(4)
                                pg.close(); return "success", ""
                        except: pass
                    pg.close(); return "partial", ""
            except: pass
        pg.close(); return "no_apply_btn", ""
    except Exception as e:
        try: pg.close()
        except: pass
        return "err", str(e)[:30]

def main():
    from playwright.sync_api import sync_playwright
    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n{'━'*58}")
    print(f"  🔍 INDEED APPLY — {today}")
    print(f"{'━'*58}\n")
    session = load_session("indeed")
    if not session:
        print("  Tentando login Indeed automático...")
        with sync_playwright() as p:
            br, ctx = stealth_context(p)
            from session_manager import try_login_indeed
            cookies = try_login_indeed(ctx)
            if cookies:
                save_session("indeed", cookies)
                session = {"cookies": cookies}
                print(f"  ✅ Login Indeed OK")
            br.close()
    ok = skip = err = 0
    all_jobs = []
    for q in QUERIES:
        for cc, _ in COUNTRIES[:3]:
            jobs = search_rss(q, cc, 8)
            all_jobs.extend(jobs)
            time.sleep(0.3)
    seen = set()
    unique = [j for j in all_jobs if j["id"] not in seen and not seen.add(j["id"])]
    new_jobs = [j for j in unique if not already_applied(j["id"])]
    print(f"  Vagas Indeed: {len(unique)} | Novas: {len(new_jobs)}\n")
    with sync_playwright() as p:
        br, ctx = stealth_context(p)
        for job in new_jobs[:15]:
            co = job.get("company","?")[:22]
            role = job.get("title","?")[:38]
            co_flag = job.get("country","US")
            print(f"  [{co_flag}] {co:<22} {role:<38}", end=" ", flush=True)
            status, detail = apply_indeed(ctx, job, session)
            icon = "✅" if "success" in status else "🔗" if "external" in status else "⚠️"
            print(f"{icon} {status}")
            save(job.get("company","?"), job.get("title","?"), job["url"], job["id"], status, co_flag)
            if "success" in status: ok += 1
            elif "external" in status: ok += 1
            else: err += 1
            time.sleep(2)
        br.close()
    print(f"\n  ✅ {ok} aplicados | ⚠️ {err} outros")

if __name__ == "__main__":
    main()
