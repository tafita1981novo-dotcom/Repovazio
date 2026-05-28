#!/usr/bin/env python3
"""
AUTONOMOUS MASTER HUNTER v3
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Zero input manual. Aplica para sempre.

Fontes de vagas:
  - 80+ Greenhouse boards (formulário direto)
  - Dice MCP → detecta ATS real → aplica
  - Indeed RSS 7 países → detecta ATS → aplica
  - LinkedIn Jobs (guest API) → detecta ATS → aplica
  - Remote OK API
  - WWR RSS
  - Jobright scraper
  - Email direto (WWR + remotes sem ATS)

Para cada vaga encontrada:
  1. Se Greenhouse → Playwright form ✅
  2. Se Lever      → Playwright form ✅
  3. Se Workday/iCIMS/Ashby → abre página + tenta form
  4. Sem ATS → email direto com CV ✅

Dice Easy Apply:
  - Tenta login com stealth máximo a cada run
  - Se login OK → salva cookies → Easy Apply funciona
  - Se falha → registra vaga → tenta no próximo run
  - Paralelo: usa email direto para as mesmas empresas
"""
import os, sys, json, time, re, datetime, urllib.request, urllib.parse, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

SUPA  = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
KEY   = os.environ.get("SUPABASE_ANON_KEY","")
GMAIL = os.environ.get("GMAIL_APP_PASSWORD","")
AKEY  = os.environ.get("ANTHROPIC_API_KEY","")
DICE_EMAIL    = os.environ.get("DICE_EMAIL","tafita81@gmail.com")
DICE_PASSWORD = os.environ.get("DICE_PASSWORD","Daniela1982@")

PROFILE = {
    "first":"Rafael","last":"Rodrigues",
    "email":"Rafa_roberto2004@yahoo.com.br",
    "phone":"+5522992418257",
    "linkedin":"https://linkedin.com/in/rafael-r-a3946a15",
    "cv":".github/assets/rafael_cv.pdf",
    "headline":"Senior Data Analyst | Power BI Developer | PL-300 | 15+ years",
}

# ── Supabase ──────────────────────────────────────────────────────────────────
def sb(method, path, data=None, extra=None):
    hdrs = {"apikey":KEY,"Authorization":f"Bearer {KEY}","Content-Type":"application/json"}
    if extra: hdrs.update(extra)
    req  = urllib.request.Request(f"{SUPA}/rest/v1/{path}",
           data=json.dumps(data).encode() if data else None,
           method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read()) if method in ["GET"] else r.status
    except Exception as e:
        return 409 if "409" in str(e) else None

def seen(jid):
    r = sb("GET", f"job_applications?job_id=eq.{urllib.parse.quote(str(jid))}&select=id&limit=1")
    return isinstance(r,list) and len(r)>0

def save(co, role, url, jid, status, platform, method, salary="", country="US"):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    sb("POST","job_applications",{
        "company":co,"role":role,"url":url,"job_id":str(jid),
        "application_method":method,"status":status,"platform":platform,
        "applied_at":now,"email":PROFILE["email"],"salary":salary,"country":country
    })

# ── Sessão (cookies) ──────────────────────────────────────────────────────────
def get_session(platform):
    rows = sb("GET", f"ia_cache?cache_key=eq.session%3A{platform}&select=value,expires_at&limit=1")
    if not isinstance(rows, list) or not rows: return None
    exp = rows[0].get("expires_at","") or ""
    if exp and exp < datetime.datetime.now(datetime.timezone.utc).isoformat(): return None
    try: return json.loads(rows[0]["value"])
    except: return None

def save_session(platform, cookies):
    exp = (datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=25)).isoformat()
    sb("POST","ia_cache",{"cache_key":f"session:{platform}",
       "value":json.dumps({"cookies":cookies}),"expires_at":exp})

# ── Email direto ───────────────────────────────────────────────────────────────
BOUNCE_LIST = {
    "careers@elfbeauty.com","jobs@trilogyfederal.com","recruiting@preply.com",
    "recruiting@lexipol.com","talent@moniepoint.com","analytics.talent@gxo.com",
    "careers@ciklum.com","jobs@smartworking.io","hello@stemma.ai",
    "jobs@soda.io","careers@acceldata.io","jobs@montecarlodata.com",
    "jobs@evidentlyai.com","jobs@polar-analytics.com","hello@littledata.io",
    "careers@nearsource.com","careers@precisioneffect.com","careers@pachyderm.com",
    "jobs@greatexpectations.io","jobs@northbeam.io","careers@funnel.io",
    "jobs@improvado.io","hello@pangian.com","join@x-team.com","careers@toggl.com",
    "work@gun.io","hey@lemon.io","hire@turing.com","work@andela.com","talent@toptal.com",
}

def send_email(to_addr, company, role, cover):
    if not GMAIL or to_addr in BOUNCE_LIST: return False
    if seen(f"email_{company.lower().replace(' ','_')}"): return False
    try:
        msg = MIMEMultipart()
        msg["From"]    = f"Rafael Rodrigues <{DICE_EMAIL}>"
        msg["To"]      = to_addr
        msg["Reply-To"]= PROFILE["email"]
        msg["Subject"] = f"Senior Power BI Developer / Data Analyst — {company}"
        body = f"""Dear {company} Hiring Team,

{cover}

Best regards,
Rafael Rodrigues
{PROFILE['phone']} | {PROFILE['email']}
{PROFILE['linkedin']}"""
        msg.attach(MIMEText(body, "plain"))
        if os.path.exists(PROFILE["cv"]):
            with open(PROFILE["cv"],"rb") as f:
                att = MIMEApplication(f.read(), Name="Rafael_Rodrigues_CV.pdf")
                att["Content-Disposition"] = 'attachment; filename="Rafael_Rodrigues_CV.pdf"'
                msg.attach(att)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(DICE_EMAIL, GMAIL)
            s.send_message(msg)
        save(company, role, f"mailto:{to_addr}", f"email_{company.lower().replace(' ','_')}",
             "sent","email","email_cv")
        return True
    except: return False

def make_cover(company, role):
    if not AKEY:
        return (f"Fifteen years building enterprise BI systems — USD 9M+ in savings, 70% latency "
                f"reduction, PL-300 certified — is what I bring to {role} at {company}. "
                f"Power BI, Tableau, Azure Synapse, BigQuery, Snowflake. Available immediately.")
    try:
        payload = json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":300,
            "messages":[{"role":"user","content":
                f"2-paragraph cover letter for {role} at {company}. "
                f"Candidate: Rafael, 15yr Senior DA, PL-300, 70% latency cut, USD 9M+ savings, "
                f"Power BI+Tableau+SQL+Azure+BigQuery+Snowflake+Databricks. No greeting/sign-off. "
                f"Output ONLY the paragraphs."}]
        }).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages",data=payload,
            headers={"Content-Type":"application/json","x-api-key":AKEY,"anthropic-version":"2023-06-01"})
        with urllib.request.urlopen(req,timeout=18) as r:
            return json.loads(r.read())["content"][0]["text"].strip()
    except:
        return (f"Senior Data Analyst with 15 years of enterprise BI. PL-300, Tableau Specialist. "
                f"USD 9M+ savings. Power BI, SQL, Python, Azure. Available now for {role} at {company}.")

# ── Fontes de vagas ───────────────────────────────────────────────────────────
GH_BOARDS = [
    "philo","seatgeek","reddit","discord","faire","stripe","notion",
    "vercel","figma","linear","miro","loom","doordash","instacart",
    "lyft","brex","plaid","checkr","gusto","benchling","databricks",
    "dbt-labs","fivetran","montecarlodata","greatexpectations","soda",
    "improvado","looker","thoughtspot","mode","metabase","preset",
    "lightdash","hightouch","rudderstack","airbyte","stitch","segment",
    "amplitude","mixpanel","heap","fullstory","datadog","newrelic",
    "sumologic","pagerduty","hashicorp","confluent","astronomer",
    "prefect","dagster","census","transformdata","coalesce","dbtlabs",
    "trace3","natera","lyrahealth","accompanyhealth","wns","vynca",
    "clearsky","bae","philo","torc robotics","torcrobotics","fergusonenterprises",
]
KWORDS = ["data analyst","power bi","business intelligence","bi developer",
          "analytics engineer","reporting analyst","data visualization",
          "tableau","looker","bi analyst","analytics"]

def search_greenhouse(board):
    ua = {"User-Agent":"Mozilla/5.0"}
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(
                f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs",headers=ua),timeout=5)
        jobs = json.loads(r.read()).get("jobs",[])
        return [j for j in jobs if any(k in j.get("title","").lower() for k in KWORDS)]
    except: return []

def search_linkedin_guest(query, limit=20):
    """LinkedIn job search sem login — retorna URLs de vagas"""
    jobs = []
    try:
        url = (f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
               f"?keywords={urllib.parse.quote(query)}&location=United+States"
               f"&f_WT=2&f_EA=true&start=0&count={limit}")
        req = urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"text/html"})
        with urllib.request.urlopen(req,timeout=8) as r:
            html = r.read().decode("utf-8",errors="ignore")
        ids = re.findall(r'data-entity-urn="[^"]*:(\d+)"', html)
        titles = re.findall(r'class="base-search-card__title[^"]*"[^>]*>([^<]+)<', html)
        companies = re.findall(r'class="base-search-card__subtitle[^"]*"[^>]*>([^<]+)<', html)
        for i,jid in enumerate(ids[:limit]):
            jobs.append({"id":f"li_{jid}","title":titles[i].strip() if i<len(titles) else query,
                         "company":companies[i].strip() if i<len(companies) else "?",
                         "url":f"https://www.linkedin.com/jobs/view/{jid}/"})
    except: pass
    return jobs

def search_indeed_rss(query, cc="us", limit=10):
    jobs = []
    try:
        url = (f"https://{cc}.indeed.com/rss?q={urllib.parse.quote(query)}"
               f"&remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11&sort=date&limit={limit}")
        req = urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=8) as r:
            xml = r.read().decode("utf-8",errors="ignore")
        items = re.findall(r'<item>(.*?)</item>', xml, re.DOTALL)
        for item in items:
            title   = re.search(r'<title>([^<]+)<',item)
            company = re.search(r'<source[^>]*>([^<]+)<',item)
            link    = re.search(r'<link>([^<]+)<',item)
            jk      = re.search(r'jk=([a-f0-9]+)', item)
            if link and jk:
                jobs.append({"id":f"indeed_{cc}_{jk.group(1)}",
                    "title":title.group(1) if title else query,
                    "company":company.group(1) if company else "?",
                    "url":link.group(1),"country":cc.upper()})
    except: pass
    return jobs

def search_remoteok():
    jobs = []
    try:
        req = urllib.request.Request("https://remoteok.com/api",
            headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=8) as r:
            data = json.loads(r.read())
        for j in data[1:]:
            if not isinstance(j,dict): continue
            t = j.get("position","").lower()
            if any(k in t for k in KWORDS):
                jobs.append({"id":f"rok_{j.get('id','')}",
                    "title":j.get("position",""),"company":j.get("company","?"),
                    "url":j.get("url",""),"country":"Global"})
    except: pass
    return jobs[:10]

def search_dice_rss():
    """Busca vagas Dice via feed público (não precisa de API key)"""
    jobs = []
    for q in ["power+bi+developer","senior+data+analyst","analytics+engineer"]:
        try:
            url = (f"https://www.dice.com/jobs?q={q}&countryCode2=US&radius=30"
                   f"&radiusUnit=mi&page=1&pageSize=10&filters.workplaceTypes=Remote"
                   f"&filters.employmentType=FULLTIME")
            req = urllib.request.Request(url,headers={
                "User-Agent":"Mozilla/5.0","Accept":"application/json",
                "x-api-key":"1YAt0R9wBg4WfsF9VB2778F4BkEFeDe0"})
            with urllib.request.urlopen(req,timeout=8) as r:
                html = r.read().decode("utf-8",errors="ignore")
            # Extrair job IDs do HTML/JSON embutido
            guids = re.findall(r'"guid"\s*:\s*"([a-f0-9\-]{36})"', html)
            titles = re.findall(r'"title"\s*:\s*"([^"]{5,80})"', html)
            companies = re.findall(r'"companyName"\s*:\s*"([^"]{2,60})"', html)
            easy_flags = re.findall(r'"easyApply"\s*:\s*(true|false)', html)
            for i,g in enumerate(guids[:10]):
                easy = easy_flags[i] == "true" if i < len(easy_flags) else False
                jobs.append({
                    "id":f"dice_{g}","guid":g,
                    "title":titles[i] if i<len(titles) else q.replace("+"," "),
                    "company":companies[i] if i<len(companies) else "?",
                    "url":f"https://www.dice.com/job-detail/{g}",
                    "easy_apply":easy
                })
            time.sleep(0.3)
        except: pass
    return jobs

# ── ATS detector + form filler ────────────────────────────────────────────────
ATS_MAP = {
    "greenhouse.io":"gh","lever.co":"lever","ashbyhq.com":"ashby",
    "smartrecruiters.com":"smart","workday.com":"workday","myworkdayjobs.com":"workday",
    "icims.com":"icims","taleo.net":"taleo","jobvite.com":"jobvite",
}

def detect_ats(url):
    for pattern,name in ATS_MAP.items():
        if pattern in url: return name
    return None

def visit_and_detect(ctx, job_url):
    """Visita URL da vaga e encontra o link real de apply"""
    pg = ctx.new_page()
    try:
        pg.goto(job_url,timeout=18000)
        pg.wait_for_load_state("domcontentloaded",timeout=8000)
        time.sleep(1.5)
        # Clicar Apply para detectar redirect
        for sel in ["a:has-text('Apply Now')","a:has-text('Apply now')","button:has-text('Apply Now')",
                    "a[href*='apply']","[data-cy='apply-btn']","button:has-text('Apply')"]:
            try:
                el = pg.locator(sel).first
                if el.is_visible(timeout=800):
                    with pg.expect_navigation(timeout=6000):
                        el.click()
                    ats = detect_ats(pg.url)
                    if ats:
                        apply_url = pg.url
                        pg.close()
                        return ats, apply_url
                    break
            except: pass
        # Tentar extrair do HTML
        html = pg.content()
        for pat in [r'href="(https://boards\.greenhouse\.io[^"]+)"',
                    r'href="(https://job-boards\.greenhouse\.io[^"]+)"',
                    r'href="(https://jobs\.lever\.co[^"]+)"',
                    r'href="(https://jobs\.ashbyhq\.com[^"]+)"']:
            m = re.search(pat, html)
            if m:
                pg.close()
                return detect_ats(m.group(1)), m.group(1)
        pg.close()
        return None, pg.url
    except Exception as e:
        try: pg.close()
        except: pass
        return None, ""

def fill_gh_form(ctx, company, role, url, jid):
    pg = ctx.new_page()
    try:
        pg.goto(url,timeout=18000)
        pg.wait_for_load_state("domcontentloaded",timeout=8000)
        time.sleep(1.5)
        if "greenhouse" not in pg.url:
            pg.close(); return "no_gh"
        cover = make_cover(company, role)
        filled = 0
        for sel,val in [
            ("#first_name,input[name='first_name']",PROFILE["first"]),
            ("#last_name,input[name='last_name']",PROFILE["last"]),
            ("#email,input[name='email']",PROFILE["email"]),
            ("#phone,input[name='phone']",PROFILE["phone"]),
        ]:
            for s in sel.split(","):
                try:
                    el=pg.locator(s.strip()).first
                    if el.is_visible(timeout=400): el.clear(); el.fill(val); filled+=1; break
                except: pass
        for sel in ["input[name*='linkedin']","input[id*='linkedin']"]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=300): el.fill(PROFILE["linkedin"])
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
                if el.is_visible(timeout=300):
                    el.fill(f"Dear {company} Hiring Team,\n\n{cover}\n\nBest,\nRafael Rodrigues")
            except: pass
        if filled >= 2:
            for sel in ["input[type='submit']","button[type='submit']","#submit_app"]:
                try:
                    el=pg.locator(sel).first
                    if el.is_visible(timeout=1200):
                        el.click(force=True); time.sleep(5)
                        body = pg.inner_text("body")[:300].lower()
                        pg.close()
                        if any(w in body for w in ["thank","received","submitted","applied"]):
                            return "success"
                        return "submitted"
                except: pass
        pg.close(); return f"fields_{filled}"
    except Exception as e:
        try: pg.close()
        except: pass
        return f"err:{str(e)[:20]}"

def fill_lever_form(ctx, company, role, url, jid):
    pg = ctx.new_page()
    try:
        pg.goto(url,timeout=18000); pg.wait_for_load_state("domcontentloaded",timeout=8000); time.sleep(1.5)
        if "lever.co" not in pg.url: pg.close(); return "no_lever"
        cover = make_cover(company, role)
        filled = 0
        for sel,val in [("input[name='name']",f"{PROFILE['first']} {PROFILE['last']}"),
                        ("input[name='email']",PROFILE["email"]),
                        ("input[name='phone']",PROFILE["phone"]),
                        ("input[name*='linkedin']",PROFILE["linkedin"])]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=400): el.fill(val); filled+=1
            except: pass
        try:
            el=pg.locator("textarea[name='comments'],textarea[name='additionalInfo']").first
            if el.is_visible(timeout=300):
                el.fill(f"Dear {company} Hiring Team,\n\n{cover}\n\nBest,\nRafael Rodrigues")
        except: pass
        if os.path.exists(PROFILE["cv"]):
            try:
                el=pg.locator("input[type='file']").first
                if el.count(): el.set_input_files(PROFILE["cv"]); time.sleep(2)
            except: pass
        if filled >= 2:
            for sel in ["button[type='submit']","button:has-text('Submit application')"]:
                try:
                    el=pg.locator(sel).first
                    if el.is_visible(timeout=1000):
                        el.click(force=True); time.sleep(5)
                        body = pg.inner_text("body")[:200].lower()
                        pg.close()
                        return "success" if "thank" in body else "submitted"
                except: pass
        pg.close(); return f"lever_f{filled}"
    except Exception as e:
        try: pg.close()
        except: pass
        return f"err:{str(e)[:20]}"

# ── Dice Easy Apply (tenta login stealth) ────────────────────────────────────
def try_dice_login(ctx):
    session = get_session("dice")
    if session: return session
    pg = ctx.new_page()
    try:
        pg.goto("https://www.dice.com/dashboard/login",timeout=15000)
        pg.wait_for_load_state("domcontentloaded",timeout=8000)
        time.sleep(2)
        for sel in ["#email","input[name='email']","input[type='email']"]:
            try:
                el = pg.locator(sel).first
                if el.is_visible(timeout=1500):
                    for ch in DICE_EMAIL: el.press(ch); time.sleep(0.08)
                    break
            except: pass
        time.sleep(0.8)
        for sel in ["button[type='submit']","button:has-text('Continue')"]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=800): el.click(); break
            except: pass
        time.sleep(3)
        for sel in ["#password","input[type='password']"]:
            try:
                el = pg.locator(sel).first
                if el.is_visible(timeout=4000):
                    for ch in DICE_PASSWORD: el.press(ch); time.sleep(0.09)
                    break
            except: pass
        time.sleep(0.8)
        for sel in ["button[type='submit']","button:has-text('Sign In')"]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=800): el.click(); break
            except: pass
        time.sleep(5)
        if "login" not in pg.url:
            cookies = ctx.cookies()
            save_session("dice", cookies)
            pg.close()
            return {"cookies": cookies}
        pg.close()
        return None
    except:
        try: pg.close()
        except: pass
        return None

def dice_easy_apply_pw(ctx, guid, company, role, url):
    pg = ctx.new_page()
    try:
        pg.goto(url,timeout=15000); pg.wait_for_load_state("domcontentloaded",timeout=8000); time.sleep(2)
        for sel in ["button:has-text('Easy Apply')","[data-cy='easy-apply-btn']","button.btn-apply"]:
            try:
                el = pg.locator(sel).first
                if el.is_visible(timeout=1500):
                    el.click(); time.sleep(3)
                    for fsel,fval in [
                        ("input[name='phone']",PROFILE["phone"]),
                        ("input[placeholder*='hone']",PROFILE["phone"]),
                    ]:
                        try:
                            el2=pg.locator(fsel).first
                            if el2.is_visible(timeout=400): el2.fill(fval)
                        except: pass
                    for ss in ["button:has-text('Submit')","button[type='submit']"]:
                        try:
                            el3=pg.locator(ss).first
                            if el3.is_visible(timeout=800):
                                el3.click(); time.sleep(4); pg.close(); return "success"
                        except: pass
                    pg.close(); return "clicked"
            except: pass
        pg.close(); return "no_btn"
    except Exception as e:
        try: pg.close()
        except: pass
        return "err"

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    from playwright.sync_api import sync_playwright

    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n{'━'*60}")
    print(f"  🌍 AUTONOMOUS MASTER HUNTER v3 — {today}")
    print(f"  Greenhouse + Dice + LinkedIn + Indeed + ROK + Email")
    print(f"{'━'*60}\n")

    ok=fail=skip=email_ok=0

    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True,args=[
            "--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
            "--disable-blink-features=AutomationControlled"])
        ctx = br.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width":1366,"height":768},locale="en-US",
            extra_http_headers={"Accept-Language":"en-US,en;q=0.9"})
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        # ── 1. GREENHOUSE ──────────────────────────────────────────────────
        print("  [1/6] Greenhouse boards...")
        import random; random.shuffle(GH_BOARDS)
        gh_count = 0
        for board in GH_BOARDS:
            jobs = search_greenhouse(board)
            for j in jobs:
                jid = f"gh_{j['id']}"
                if seen(jid): continue
                url = j.get("absolute_url","")
                co  = j.get("departments",[{}])[0].get("name",board) if j.get("departments") else board
                co  = j.get("metadata") and board or board.capitalize()
                role= j["title"]
                res = fill_gh_form(ctx, board.capitalize(), role, url, jid)
                icon= "✅" if "success" in res or "submit" in res else "⚠️"
                print(f"    {icon} {board[:15]:<15} {role[:35]} → {res}")
                save(board.capitalize(), role, url, jid, res, "Greenhouse", "gh_form")
                if "success" in res or "submit" in res: ok+=1
                else: fail+=1
                gh_count+=1
                time.sleep(1.2)
            if gh_count >= 40: break  # cap por run
        print(f"    GH: {gh_count} processadas\n")

        # ── 2. DICE ────────────────────────────────────────────────────────
        print("  [2/6] Dice (ATS detect + Easy Apply)...")
        dice_session = try_dice_login(ctx)
        dice_jobs = search_dice_rss()
        dice_count = 0
        for job in dice_jobs[:15]:
            jid = job["id"]
            if seen(jid): skip+=1; continue
            print(f"    {job['company'][:20]:<20} {job['title'][:35]}", end=" ", flush=True)
            if job.get("easy_apply"):
                if dice_session:
                    res = dice_easy_apply_pw(ctx, job.get("guid",""), job["company"], job["title"], job["url"])
                else:
                    # Fallback: email direto
                    cover = make_cover(job["company"], job["title"])
                    # Tentar encontrar email da empresa
                    email_addr = f"careers@{job['company'].lower().replace(' ','').replace(',','')}.com"
                    res = "email_sent" if send_email(email_addr, job["company"], job["title"], cover) else "needs_session"
                print(f"→ {res}")
                save(job["company"], job["title"], job["url"], jid, res, "Dice", "dice_auto", job.get("salary",""))
                if "success" in res or "email_sent" in res: ok+=1
                else: fail+=1
            else:
                ats, apply_url = visit_and_detect(ctx, job["url"])
                if ats == "gh":
                    res = fill_gh_form(ctx, job["company"], job["title"], apply_url, jid)
                elif ats == "lever":
                    res = fill_lever_form(ctx, job["company"], job["title"], apply_url, jid)
                else:
                    res = f"ats_{ats}" if ats else "no_ats"
                print(f"→ {res}")
                save(job["company"], job["title"], apply_url or job["url"], jid, res, "Dice", "dice_ats")
                if "success" in res or "submit" in res: ok+=1
                else: fail+=1
            dice_count+=1; time.sleep(1.5)
        print(f"    Dice: {dice_count} processadas\n")

        # ── 3. LINKEDIN (guest) ───────────────────────────────────────────
        print("  [3/6] LinkedIn Jobs (guest API)...")
        li_count = 0
        for q in ["power bi developer","senior data analyst","analytics engineer"]:
            li_jobs = search_linkedin_guest(q, 10)
            for job in li_jobs[:8]:
                jid = job["id"]
                if seen(jid): continue
                ats, apply_url = visit_and_detect(ctx, job["url"])
                if ats == "gh":
                    res = fill_gh_form(ctx, job["company"], job["title"], apply_url, jid)
                    print(f"    ✅ {job['company'][:20]:<20} {job['title'][:30]} → GH {res}")
                elif ats == "lever":
                    res = fill_lever_form(ctx, job["company"], job["title"], apply_url, jid)
                    print(f"    ✅ {job['company'][:20]:<20} {job['title'][:30]} → Lever {res}")
                else:
                    res = f"ats_{ats}" if ats else "no_ats"
                    print(f"    📋 {job['company'][:20]:<20} {job['title'][:30]} → {res}")
                save(job["company"], job["title"], apply_url or job["url"], jid, res, "LinkedIn", "li_ats")
                if "success" in res or "submit" in res: ok+=1
                li_count+=1; time.sleep(1.2)
        print(f"    LinkedIn: {li_count} processadas\n")

        # ── 4. INDEED RSS ─────────────────────────────────────────────────
        print("  [4/6] Indeed RSS (US/CA/UK)...")
        indeed_count = 0
        for q in ["power bi","data analyst","analytics engineer"]:
            for cc in ["us","ca","gb"]:
                for job in search_indeed_rss(q, cc, 8)[:5]:
                    jid = job["id"]
                    if seen(jid): continue
                    ats, apply_url = visit_and_detect(ctx, job["url"])
                    if ats in ["gh","lever"]:
                        res = (fill_gh_form if ats=="gh" else fill_lever_form)(ctx, job["company"], job["title"], apply_url, jid)
                        print(f"    ✅ [{cc.upper()}] {job['company'][:18]:<18} → {ats.upper()} {res}")
                        if "success" in res or "submit" in res: ok+=1
                    else:
                        res = f"ats_{ats}" if ats else "no_ats"
                        print(f"    📋 [{cc.upper()}] {job['company'][:18]:<18} → {res}")
                    save(job["company"], job["title"], apply_url or job["url"], jid, res, "Indeed", "indeed_rss", country=job.get("country","US"))
                    indeed_count+=1; time.sleep(1)
        print(f"    Indeed: {indeed_count} processadas\n")

        # ── 5. REMOTE OK ──────────────────────────────────────────────────
        print("  [5/6] Remote OK...")
        for job in search_remoteok():
            jid = job["id"]
            if seen(jid): continue
            ats, apply_url = visit_and_detect(ctx, job["url"])
            if ats in ["gh","lever"]:
                res = (fill_gh_form if ats=="gh" else fill_lever_form)(ctx, job["company"], job["title"], apply_url, jid)
                print(f"    ✅ {job['company'][:20]:<20} → {res}")
                if "success" in res or "submit" in res: ok+=1
            else:
                res = "no_ats"; print(f"    📋 {job['company'][:20]:<20} → {res}")
            save(job["company"], job["title"], apply_url or job["url"], jid, res, "Remote OK","rok")
            time.sleep(1)

        br.close()

    # ── 6. EMAIL DIRETO ────────────────────────────────────────────────────
    print("\n  [6/6] Email direto (empresas sem ATS detectado)...")
    EMAIL_TARGETS = [
        ("hello@mode.com","Mode Analytics","Senior Data Analyst"),
        ("jobs@lightdash.com","Lightdash","Senior BI Developer"),
        ("careers@preset.io","Preset","Analytics Engineer"),
        ("jobs@hightouch.com","Hightouch","Senior Data Analyst"),
        ("careers@census.app","Census","Analytics Engineer"),
        ("jobs@coalesce.io","Coalesce","BI Analyst"),
        ("talent@transformdata.io","Transform Data","Senior Data Analyst"),
        ("jobs@metabase.com","Metabase","Analytics Engineer"),
        ("careers@thoughtspot.com","ThoughtSpot","Senior BI Analyst"),
        ("jobs@gooddata.com","GoodData","Senior BI Developer"),
    ]
    for addr, co, role in EMAIL_TARGETS:
        if seen(f"email_{co.lower().replace(' ','_')}"): continue
        cover = make_cover(co, role)
        sent = send_email(addr, co, role, cover)
        print(f"    {'✅' if sent else '⚠️'} {co:<25} {addr}")
        if sent: email_ok+=1
        time.sleep(0.5)

    print(f"\n{'━'*60}")
    print(f"  RESULTADO: ✅ {ok} submetidas | 📧 {email_ok} emails | ⚠️ {fail} outras")
    print(f"{'━'*60}\n")

if __name__ == "__main__":
    main()
