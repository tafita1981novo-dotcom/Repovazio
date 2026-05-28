#!/usr/bin/env python3
"""
AI-ADAPTIVE GLOBAL JOB HUNTER v7
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Indeed US + UK + NL + DE + CA + AU (RSS)
• Dice API (57+ remote BI/DA/PowerBI jobs/week)  
• Greenhouse API (60+ company boards)
• Remote OK + WWR
• IA adapta cover letter para cada vaga (Claude claude-sonnet-4-20250514)
• Nunca aplica na mesma vaga duas vezes (job_id único no Supabase)
• Rafael Rodrigues | 15+ anos | PL-300 | MBA
"""
import os, time, json, re, hashlib, datetime, smtplib, urllib.request, urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ─── PERFIL ──────────────────────────────────────────────────────────────────
P = {
  "name":     "Rafael Rodrigues",
  "email":    "Rafa_roberto2004@yahoo.com.br",
  "phone":    "+5522992418257",
  "linkedin": "https://linkedin.com/in/rafael-r-a3946a15",
  "cv":       ".github/assets/rafael_cv.pdf",
  "title":    "Senior Data Analyst | Power BI Developer | Analytics Engineer",
  "years":    "15+",
  "certs":    "Microsoft PL-300 | Tableau Desktop Specialist | MBA IBMEC | Six Sigma Green Belt",
  "wins": [
    "USD 9M+ operational savings at TIM/OI via BI automation",
    "70% report latency reduction at Keyrus via Power BI optimisation",
    "200+ business users served with self-service BI at Dataex",
    "500M+ records/month processed with near-realtime analytics",
    "83% automation efficiency gain at Coca-Cola via BigQuery pipelines",
  ],
  "exp": [
    "Dataex 2022–Present: Power BI+Tableau+Looker for 200+ users; BigQuery, Snowflake, Databricks",
    "Keyrus 2019–2022: Senior BI Consultant; Azure Synapse, SAP, Salesforce, 10+ enterprise clients",
    "Coca-Cola 2018–2019: 30+ KPIs, BigQuery, 83% automation efficiency",
    "TIM/OI 2007–2017: 500M+ subscriber records/month, USD 9M+ savings",
  ],
  "stack": "Power BI (DAX/PQuery/RLS/Tabular Editor) · Tableau · Looker (LookML) · SQL · T-SQL · Python (pandas/sklearn) · dbt · Airflow · Azure Synapse · BigQuery · Snowflake · Databricks",
}

SUPA  = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SKEY  = os.environ.get("SUPABASE_ANON_KEY","")
GMAIL = "tafita81@gmail.com"
GPASS = os.environ.get("GMAIL_APP_PASSWORD","")
AKEY  = os.environ.get("ANTHROPIC_API_KEY","")

# Keywords para filtrar vagas relevantes
KWORDS = ["data analyst","power bi","business intelligence","bi developer","bi analyst",
          "analytics engineer","reporting analyst","data visualization","tableau",
          "looker","senior analyst","bi engineer","analytics developer","visualization engineer"]

def is_relevant(t): return any(k in (t or "").lower() for k in KWORDS)

# ─── SUPABASE ────────────────────────────────────────────────────────────────
def sb(method, path, data=None):
    hdrs = {"apikey":SKEY,"Authorization":f"Bearer {SKEY}","Content-Type":"application/json",
            "Prefer":"return=minimal" if method!="GET" else ""}
    req  = urllib.request.Request(f"{SUPA}/rest/v1/{path}",
           data=json.dumps(data).encode() if data else None, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read()) if method=="GET" else r.status
    except Exception as e:
        return 409 if "409" in str(e) else None

def already(jid):
    r = sb("GET", f"job_applications?job_id=eq.{urllib.parse.quote(str(jid))}&status=not.eq.discovered&select=id&limit=1")
    return isinstance(r, list) and len(r) > 0

def save(co, role, url, jid, status, platform, method, cover="", salary="", country="US"):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    sb("POST","job_applications",{
        "company":co,"role":role,"url":url,"job_id":str(jid),
        "application_method":method,"status":status,"platform":platform,
        "applied_at":now,"email":P["email"],"salary":salary,"country":country,
        "cover_letter":cover[:800]
    })

# ─── AI COVER LETTER ─────────────────────────────────────────────────────────
def make_cover(co, role, desc):
    """Gera cover letter personalizada com IA para esta vaga específica"""
    desc_l = (desc or "").lower()

    # Mapear skills da vaga → conquistas do Rafael
    skill_map = {
        "power bi":      "Power BI expert (PL-300 certified) — DAX, Power Query, RLS, Tabular Editor, Deployment Pipelines",
        "tableau":       "Tableau Desktop Specialist — advanced LODs, Parameters, Cohort/Funnel Analysis",
        "looker":        "Looker/LookML — custom explores, dashboards, semantic models",
        "sql":           "15+ years advanced SQL/T-SQL — complex joins, window functions, performance tuning",
        "python":        "Python (pandas, scikit-learn) — ETL automation, ML pipelines",
        "azure":         "Azure expertise: Synapse Analytics, ADF, Databricks, Azure ML",
        "bigquery":      "Google BigQuery — 83% efficiency gain at Coca-Cola",
        "snowflake":     "Snowflake — data modeling, cost optimisation, performance tuning",
        "databricks":    "Databricks SQL — 500M+ records/month at enterprise scale",
        "dbt":           "dbt — data transformation pipelines, testing, documentation",
        "healthcare":    "Healthcare analytics awareness — regulatory, population health reporting",
        "fintech":       "Financial analytics — TIM/OI Telecom (USD 9M+ savings), Keyrus finance clients",
        "retail":        "Retail analytics — Coca-Cola, Crate & Barrel-type growth insights",
        "governance":    "Data Governance, SOX, GDPR compliance — enterprise-grade standards",
        "dashboard":     "Dashboard UX & executive storytelling — 200+ business users served",
        "kpi":           "KPI frameworks: CAC, LTV, ARPU, Churn, ROI, NPS",
        "machine learning":"ML integration — scikit-learn, Azure ML, predictive models",
        "agile":         "Agile/Scrum practitioner — 15+ years enterprise delivery",
        "snowflake":     "Snowflake DWH — data modelling, query optimisation",
    }
    matched = [v for k,v in skill_map.items() if k in desc_l][:4]
    if not matched:
        matched = ["Power BI (PL-300)", "15+ years SQL/T-SQL analytics", "Azure Synapse + BigQuery + Snowflake"]

    if not AKEY:
        return _static(co, role, matched)

    try:
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 500,
            "messages":[{"role":"user","content":f"""Write a persuasive 3-paragraph cover letter for:

Company: {co}
Role: {role}
Job excerpt: {desc[:1000]}

Candidate profile:
- 15+ years Senior Data Analyst & BI Developer, Brazil (remote-ready)
- Certifications: {P['certs']}
- Top achievements: {'; '.join(P['wins'][:3])}
- Most relevant skills for THIS job: {'; '.join(matched)}
- Current: Dataex — Power BI+Tableau+Looker for 200+ users
- Prior: Keyrus (global BI consulting), Coca-Cola, TIM/OI Telecom

Instructions:
- Hook: specific hook about THIS role at {co} (not generic)
- Para 2: match 3 specific job requirements to concrete measurable achievements
- Para 3: why {co} specifically + strong CTA
- Tone: confident, precise, data-driven
- Max 3 paragraphs — no "Dear Hiring Team" or sign-off (added separately)
- Output ONLY the body paragraphs"""}]
        }).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload,
            headers={"Content-Type":"application/json","x-api-key":AKEY,"anthropic-version":"2023-06-01"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())["content"][0]["text"].strip()
    except:
        return _static(co, role, matched)

def _static(co, role, skills):
    return f"""I am applying for the {role} position at {co}. As a Senior Data Analyst and Analytics Engineer with 15+ years of enterprise BI experience across Retail, Telecom, Financial Services, and Marketing, I bring a proven record of impact: USD 9M+ in operational savings, 70% report latency reduction, and self-service analytics platforms serving 200+ business users globally.

My technical depth directly matches this role: {'; '.join(skills[:3])}. At Dataex (current), I architect Power BI and Tableau solutions on BigQuery, Snowflake and Databricks. At Keyrus (global BI consultancy), I optimised Azure Synapse environments achieving 70% query performance gains for 10+ enterprise clients. I hold Microsoft PL-300, Tableau Desktop Specialist, and MBA certifications — all directly applicable here.

Available immediately for remote engagement. I would welcome the opportunity to discuss how my 15+ years of analytics engineering experience can accelerate {co}'s data-driven objectives."""

def full_cover(co, role, body):
    return f"Dear Hiring Team at {co},\n\n{body}\n\nBest regards,\nRafael Rodrigues\n{P['phone']} | {P['email']}\nLinkedIn: {P['linkedin']}"

# ─── JOB SOURCES ─────────────────────────────────────────────────────────────
def jobs_greenhouse():
    boards = [
        "stripe","chime","adyen","intercom","okta","nubank","braze","elastic","clickhouse",
        "datadog","affirm","launchdarkly","waymo","twilio","databricks","salesloft","vtex",
        "fastly","contentful","mongodb","attentive","robinhood","amplitude","mixpanel",
        "fullstory","heap","pendo","thoughtspot","hex","metabase","dbt-labs","fivetran",
        "airbyte","hightouch","gusto","rippling","lattice","gong","klaviyo","pagerduty",
        "linear","sentry","algolia","coinbase","plaid","zendesk","hubspot","shopify",
        "gitlab","cloudflare","zapier","benchling","brex","ramp","mercury","faire",
        "duolingo","coursera","seatgeek","betterment","squarespace","experian","epam",
        "unitedhealth","humana","uhg","optum","anthem","cigna","aetna",
        "palantir","snowflake","databricks","dbt","fivetran","airbyte",
        "pinterest","lyft","doordash","airbnb","twitch","reddit","discord",
    ]
    out = []
    for co in boards:
        try:
            req = urllib.request.Request(f"https://boards-api.greenhouse.io/v1/boards/{co}/jobs",
                headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
            for j in data.get("jobs",[]):
                if is_relevant(j.get("title","")):
                    out.append({"id":f"gh_{j['id']}","company":co.replace("-"," ").title(),
                        "role":j["title"],"url":j.get("absolute_url",""),
                        "desc":j.get("content","")[:2000],"location":j.get("location",{}).get("name","Remote"),
                        "platform":"Greenhouse","method":"greenhouse_form","country":"US","salary":""})
            time.sleep(0.08)
        except: pass
    return out

def jobs_indeed():
    feeds = [
        ("https://www.indeed.com/rss?q=senior+power+bi+developer&l=remote&jt=fulltime&sort=date","US"),
        ("https://www.indeed.com/rss?q=senior+data+analyst+remote&l=remote&jt=fulltime&sort=date","US"),
        ("https://www.indeed.com/rss?q=analytics+engineer+remote&l=remote&jt=fulltime&sort=date","US"),
        ("https://www.indeed.com/rss?q=business+intelligence+analyst+remote&jt=fulltime&sort=date","US"),
        ("https://www.indeed.com/rss?q=power+bi+developer+remote&l=remote&sort=date","US"),
        ("https://www.indeed.co.uk/rss?q=senior+power+bi+developer&l=remote&sort=date","UK"),
        ("https://www.indeed.co.uk/rss?q=senior+data+analyst+remote&sort=date","UK"),
        ("https://www.indeed.nl/rss?q=senior+data+analyst&l=remote&sort=date","NL"),
        ("https://www.indeed.de/rss?q=senior+data+analyst+remote&sort=date","DE"),
        ("https://ca.indeed.com/rss?q=senior+power+bi+developer&l=remote&sort=date","CA"),
        ("https://au.indeed.com/rss?q=senior+data+analyst+remote&sort=date","AU"),
    ]
    out = []
    for url, country in feeds:
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                rss = r.read().decode("utf-8","ignore")
            for item in re.findall(r"<item>(.*?)</item>", rss, re.DOTALL):
                tm = re.search(r"<title><!\[CDATA\[(.*?)\]\]>|<title>(.*?)</title>",item)
                lm = re.search(r"<link>(https?://[^\s<]+)",item)
                gm = re.search(r"<guid[^>]*>(.*?)</guid>",item)
                sm = re.search(r"<source[^>]*>(.*?)</source>",item)
                dm = re.search(r"<description><!\[CDATA\[(.*?)\]\]>",item,re.DOTALL)
                title = ((tm.group(1) or tm.group(2)) if tm else "").strip()
                if not is_relevant(title): continue
                link  = lm.group(1).strip() if lm else ""
                guid  = gm.group(1).strip() if gm else link
                co    = sm.group(1).strip() if sm else "?"
                desc  = re.sub(r"<[^>]+"," ",dm.group(1)) if dm else ""
                jid   = f"ind_{hashlib.md5(guid.encode()).hexdigest()[:14]}_{country}"
                out.append({"id":jid,"company":co,"role":title,"url":link,
                    "desc":desc[:2000],"location":f"Remote ({country})","platform":f"Indeed/{country}",
                    "method":"greenhouse_form","country":country,"salary":""})
            time.sleep(0.3)
        except: pass
    seen=set(); return [j for j in out if not (j["id"] in seen or seen.add(j["id"]))]

def jobs_dice():
    queries = ["power+bi+developer","senior+data+analyst","analytics+engineer",
               "business+intelligence+analyst","bi+developer","tableau+developer",
               "data+visualization+engineer","reporting+analyst"]
    out = []
    for q in queries:
        try:
            url = (f"https://job-search-api.svc.dhigroupinc.com/v1/dice/jobs/search"
                   f"?q={q}&countryCode2=US&radius=30&radiusUnit=mi&page=1&pageSize=25"
                   f"&filters.workplaceTypes=Remote&filters.employmentType=FULLTIME"
                   f"&fields=id,title,companyName,salary,detailsPageUrl,postedDate,easyApply,summary")
            req = urllib.request.Request(url, headers={
                "User-Agent":"Mozilla/5.0",
                "x-api-key":"1YAt0R9wBg4WfsF9VB2778F4BkEFeDe0"
            })
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            for j in data.get("data",[]):
                title = j.get("title","")
                if not is_relevant(title): continue
                jid   = j.get("id") or j.get("guid","")
                out.append({"id":f"dice_{jid}","company":j.get("companyName","?"),
                    "role":title,"url":j.get("detailsPageUrl",""),
                    "desc":j.get("summary","")[:1500],"location":"Remote (US)",
                    "platform":"Dice","method":"dice_apply","country":"US",
                    "salary":j.get("salary",""),"easy_apply":j.get("easyApply",False)})
            time.sleep(0.4)
        except: pass
    seen=set(); return [j for j in out if not (j["id"] in seen or seen.add(j["id"]))]

def jobs_remoteok():
    out = []
    for tag in ["data-analyst","bi-developer","analytics","power-bi"]:
        try:
            req = urllib.request.Request(f"https://remoteok.com/api?tags={tag}",
                headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            for j in data:
                if not isinstance(j,dict): continue
                pos = j.get("position","")
                if not is_relevant(pos): continue
                out.append({"id":f"rok_{j.get('id','')}","company":j.get("company","?"),
                    "role":pos,"url":j.get("url",""),"desc":j.get("description","")[:1500],
                    "location":"Remote (Global)","platform":"RemoteOK",
                    "method":"remoteok_apply","country":"Global","salary":""})
            time.sleep(0.5)
        except: pass
    seen=set(); return [j for j in out if not (j["id"] in seen or seen.add(j["id"]))]

def jobs_wwr():
    out = []
    try:
        req = urllib.request.Request(
            "https://weworkremotely.com/categories/remote-data-analysis-jobs.rss",
            headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            rss = r.read().decode("utf-8","ignore")
        for item in re.findall(r"<item>(.*?)</item>",rss,re.DOTALL):
            tm = re.search(r"<title><!\[CDATA\[(.*?)\]\]>",item)
            lm = re.search(r"<link>(https?://[^\s<]+)",item)
            title = tm.group(1).strip() if tm else ""
            if not is_relevant(title): continue
            link = lm.group(1).strip() if lm else ""
            jid  = f"wwr_{hashlib.md5(link.encode()).hexdigest()[:12]}"
            parts= title.split(":",1)
            out.append({"id":jid,"company":parts[0].strip() if len(parts)>1 else "?",
                "role":parts[1].strip() if len(parts)>1 else title,
                "url":link,"desc":"","location":"Remote (Global)",
                "platform":"WWR","method":"wwr_apply","country":"Global","salary":""})
    except: pass
    return out

# ─── APPLY VIA GREENHOUSE FORM ───────────────────────────────────────────────
def apply_gh(ctx, job, cover):
    urls = [job["url"]]
    bid  = re.search(r"greenhouse\.io/(?:embed/job_app\?for=)?([^&/?#]+)",job["url"])
    tok  = re.search(r"token=(\d+)",job["url"])
    if bid and tok:
        urls.append(f"https://boards.greenhouse.io/embed/job_app?for={bid.group(1)}&token={tok.group(1)}")

    for url in urls:
        pg = ctx.new_page()
        try:
            pg.goto(url, timeout=25000)
            pg.wait_for_load_state("domcontentloaded", timeout=12000)
            time.sleep(2)
            if "greenhouse.io" not in pg.url: pg.close(); continue

            filled = 0
            for sel, val in [
                ("#first_name,input[name='first_name']","Rafael"),
                ("#last_name,input[name='last_name']","Rodrigues"),
                ("#email,input[name='email']",P["email"]),
                ("#phone,input[name='phone']",P["phone"]),
            ]:
                for s in sel.split(","):
                    try:
                        el=pg.locator(s.strip()).first
                        if el.is_visible(timeout=600): el.clear(); el.fill(val); filled+=1; break
                    except: pass

            for sel in ["input[name*='linkedin']","input[id*='linkedin']","input[placeholder*='LinkedIn']"]:
                try:
                    el=pg.locator(sel).first
                    if el.is_visible(timeout=500): el.clear(); el.fill(P["linkedin"]); break
                except: pass

            for sel in ["input[name*='location']","input[placeholder*='City']"]:
                try:
                    el=pg.locator(sel).first
                    if el.is_visible(timeout=500): el.clear(); el.fill("Brazil"); break
                except: pass

            if os.path.exists(P["cv"]):
                for sel in ["input[type='file'][name*='resume']","input[type='file']"]:
                    try:
                        el=pg.locator(sel).first
                        if el.count(): el.set_input_files(P["cv"]); time.sleep(2); break
                    except: pass

            for sel in ["textarea[name*='cover']","textarea[id*='cover']","#cover_letter_text"]:
                try:
                    el=pg.locator(sel).first
                    if el.is_visible(timeout=500): el.clear(); el.fill(full_cover(job["company"],job["role"],cover)); break
                except: pass

            # Campos de autorização de trabalho
            for sel in ["select[name*='authorized']","select[id*='authorized']",
                        "select[name*='sponsor']","select[id*='sponsor']"]:
                try:
                    el=pg.locator(sel).first
                    if el.is_visible(timeout=500):
                        for opt in ["No","no","0","false"]:
                            try: el.select_option(label=opt); break
                            except: pass
                except: pass

            if filled >= 2:
                for sel in ["input[type='submit']","button[type='submit']","#submit_app"]:
                    try:
                        el=pg.locator(sel).first
                        if el.is_visible(timeout=1500):
                            el.click(force=True); time.sleep(5)
                            body=pg.inner_text("body")[:400].lower()
                            if any(w in body for w in ["thank","received","submitted","applied","success"]):
                                pg.close(); return "success"
                            elif any(w in body for w in ["error","required","invalid"]):
                                pg.close(); return "form_error"
                            pg.close(); return "submitted"
                    except: pass
            pg.close(); return f"fields_{filled}"
        except PWTimeout: pg.close(); return "timeout"
        except Exception as e: pg.close(); return f"err:{str(e)[:25]}"
    return "no_url"

# ─── APPLY VIA EMAIL ─────────────────────────────────────────────────────────
def apply_email(job, cover, srv):
    to = job.get("email","")
    if not to or not srv: return "no_smtp"
    msg = MIMEMultipart()
    msg["Subject"] = f"Application: {job['role']} — 15+ Yrs BI | PL-300 | {P['phone']} | Remote"
    msg["From"]    = f"Rafael Rodrigues <{GMAIL}>"
    msg["To"]      = to
    msg["Reply-To"]= P["email"]
    msg.attach(MIMEText(full_cover(job["company"],job["role"],cover),"plain"))
    if os.path.exists(P["cv"]):
        with open(P["cv"],"rb") as f:
            att=MIMEBase("application","octet-stream"); att.set_payload(f.read())
        encoders.encode_base64(att)
        att.add_header("Content-Disposition","attachment",filename="Rafael_Rodrigues_CV.pdf")
        msg.attach(att)
    try: srv.sendmail(GMAIL,to,msg.as_string()); return "sent"
    except Exception as e: return f"smtp:{str(e)[:25]}"

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n{'━'*65}")
    print(f"  🤖 AI-ADAPTIVE GLOBAL JOB HUNTER v7 — {today}")
    print(f"  Greenhouse · Indeed (6 países) · Dice · RemoteOK · WWR")
    print(f"  Cover letter personalizada com IA para cada vaga")
    print(f"{'━'*65}\n")

    # ── Coletar vagas de todas as fontes ──────────────────────────────
    print("── DESCOBERTA ──────────────────────────────────")
    print("  Greenhouse... ", end="",flush=True); gh=jobs_greenhouse();  print(len(gh))
    print("  Indeed (6)...  ", end="",flush=True); ind=jobs_indeed();    print(len(ind))
    print("  Dice...        ", end="",flush=True); di=jobs_dice();        print(len(di))
    print("  RemoteOK...    ", end="",flush=True); ro=jobs_remoteok();   print(len(ro))
    print("  WWR...         ", end="",flush=True); ww=jobs_wwr();         print(len(ww))

    all_jobs = gh + ind + di + ro + ww
    new_jobs = [j for j in all_jobs if not already(j["id"])]

    print(f"\n  Total: {len(all_jobs)} | ✨ Novas: {len(new_jobs)}\n")
    if not new_jobs: print("✅ Nenhuma vaga nova — banco atualizado."); return

    # ── SMTP ──────────────────────────────────────────────────────────
    smtp=None
    if GPASS:
        try: smtp=smtplib.SMTP_SSL("smtp.gmail.com",465); smtp.login(GMAIL,GPASS)
        except: smtp=None

    # ── Aplicar ───────────────────────────────────────────────────────
    print("── CANDIDATURAS (IA adapta cada cover letter) ──────────────────")
    ok=skip=err=0

    with sync_playwright() as pl:
        br = pl.chromium.launch(headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
                  "--disable-blink-features=AutomationControlled"])
        ctx= br.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width":1280,"height":800},locale="en-US")
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        for i,job in enumerate(new_jobs[:70],1):
            co   = job["company"][:20]
            role = job["role"][:38]
            plat = job["platform"][:12]
            print(f"  [{i:2}] [{plat:12}] {co:<22} {role:<38}",end=" ",flush=True)

            cover = make_cover(job["company"], job["role"], job.get("desc",""))

            if job["method"] in ("greenhouse_form","gh_form"):
                res = apply_gh(ctx, job, cover)
            elif job["method"] in ("email_apply","indeed_email") and smtp:
                res = apply_email(job, cover, smtp)
            else:
                # Registrar como descoberta para candidatura manual/próximo ciclo
                res = "tracked"

            icon = "✅" if any(k in res for k in ["success","submitted","sent"]) else \
                   "📋" if res=="tracked" else "⚠️ "
            print(f"{icon} {res}")

            save(job["company"],job["role"],job["url"],job["id"],
                 res,job["platform"],job["method"],cover,
                 job.get("salary",""),job.get("country","US"))

            if any(k in res for k in ["success","submitted","sent"]): ok+=1
            elif res=="tracked": skip+=1
            else: err+=1
            time.sleep(1.5)

        br.close()

    if smtp: smtp.quit()

    print(f"\n{'━'*65}")
    print(f"  ✅ {ok} candidaturas enviadas/confirmadas")
    print(f"  📋 {skip} registradas (canal sem automação)")
    print(f"  ⚠️  {err} com erro")
    print(f"  🤖 Cover letters geradas por IA para CADA vaga")
    print(f"  📅 {today} | Próxima rodada: amanhã 9h UTC")
    print(f"{'━'*65}\n")

if __name__=="__main__":
    main()
