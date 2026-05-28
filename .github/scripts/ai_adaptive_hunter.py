#!/usr/bin/env python3
"""
AI-ADAPTIVE APPLICATION ENGINE
Busca vagas em todos os sites, adapta o perfil com IA, candidata automaticamente
Rafael Rodrigues | Senior Data Analyst | Power BI | 15+ anos
"""
import os, time, json, datetime, hashlib, re, urllib.request, urllib.parse, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ── Perfil completo Rafael ────────────────────────────────────────────────────
PROFILE = {
    "name":     "Rafael Rodrigues",
    "email":    "Rafa_roberto2004@yahoo.com.br",
    "phone":    "+5522992418257",
    "linkedin": "https://linkedin.com/in/rafael-r-a3946a15",
    "location": "Brazil (Remote)",
    "title":    "Senior Data Analyst | Power BI Developer | Analytics Engineer",
    "years":    "15+",
    "summary": """Senior Data Analyst and Analytics Engineer with 15+ years delivering enterprise BI,
cloud analytics, and self-service data platforms across Retail, Financial Services,
Telecom, and Marketing sectors. Specialized in Power BI (DAX, Power Query, RLS,
Deployment Pipelines, Tabular Editor), SQL, Python, dimensional modeling.
Generated USD 9M+ operational savings, 70% report latency reduction, served 200+
business users, processed 500M+ records monthly.""",
    "certifications": [
        "Microsoft PL-300 Power BI Data Analyst Associate",
        "Tableau Desktop Specialist",
        "MBA IBMEC",
        "Six Sigma Green Belt"
    ],
    "stack": {
        "bi_tools":  "Power BI (expert), Tableau, Looker, ThoughtSpot, Qlik, SAP Analytics Cloud",
        "languages": "SQL, T-SQL, Python (pandas, scikit-learn), DAX, M (Power Query), LookML",
        "cloud":     "Azure (Synapse, ADF, Databricks, ML), GCP BigQuery, AWS (Redshift, Athena, QuickSight), Snowflake",
        "data_eng":  "dbt, Apache Airflow, Dimensional Modeling (Star/Snowflake, Kimball), ETL/ELT",
        "methods":   "Agile/Scrum, Data Governance, GDPR, SOX, KPI frameworks",
    },
    "experience": [
        {"co":"Dataex",    "role":"Senior Data Analyst",               "years":"2022–Present", "impact":"Power BI+Tableau+Looker for 200+ users; BigQuery, Snowflake, Databricks; 60% load time reduction"},
        {"co":"Keyrus",    "role":"Senior BI Consultant",              "years":"2019–2022",    "impact":"Azure Synapse, SAP, Salesforce, Oracle; 70% query optimization; 10+ enterprise clients"},
        {"co":"Coca-Cola", "role":"Senior Data Analyst",               "years":"2018–2019",    "impact":"30+ KPIs, BigQuery, 83% automation efficiency gain"},
        {"co":"TIM/OI",    "role":"Senior Data Analyst Strategic BI",  "years":"2007–2017",    "impact":"500M+ subscriber records/month; USD 9M+ savings; 500+ report consumers"},
    ],
    "achievements": [
        "USD 9M+ operational savings via BI automation at TIM/OI",
        "70% report latency reduction via Power BI optimization at Keyrus",
        "200+ business users served with self-service BI at Dataex",
        "500M+ records/month processed with near real-time analytics",
        "83% automation efficiency gain at Coca-Cola via BigQuery pipelines",
    ]
}

SUPA  = os.environ.get("SUPABASE_URL", "https://tpjvalzwkqwttvmszvie.supabase.co")
KEY   = os.environ.get("SUPABASE_ANON_KEY", "")
GMAIL = "tafita81@gmail.com"
GPASS = os.environ.get("GMAIL_APP_PASSWORD", "")
CV    = ".github/assets/rafael_cv.pdf"
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

KWORDS = ["data analyst","power bi","business intelligence","analytics engineer",
          "bi developer","bi analyst","reporting analyst","data visualization",
          "tableau","looker","senior analyst","analytics developer","bi engineer"]
def chk(t): return any(k in (t or "").lower() for k in KWORDS)

# ── Supabase helpers ──────────────────────────────────────────────────────────
def supa_req(method, path, data=None):
    url = f"{SUPA}/rest/v1/{path}"
    hdrs = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if method == "GET":    hdrs["Prefer"] = ""
    else:                   hdrs["Prefer"] = "return=minimal"
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
        method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read()) if method == "GET" else r.status
    except Exception as e:
        if "409" in str(e): return 409
        return None

def already_applied(job_id):
    res = supa_req("GET", f"job_applications?job_id=eq.{urllib.parse.quote(str(job_id))}&status=in.(success,sent,easy_apply_clicked)&select=id&limit=1")
    return bool(res)

def save_application(company, role, url, job_id, status, platform, method, cover_letter=""):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    supa_req("POST", "job_applications", {
        "company": company, "role": role, "url": url, "job_id": str(job_id),
        "application_method": method, "status": status, "platform": platform,
        "applied_at": now, "email": PROFILE["email"], "notes": cover_letter[:500] if cover_letter else ""
    })

# ── AI Cover Letter Generator ─────────────────────────────────────────────────
def generate_adaptive_cover(company, role, job_description):
    """Gera cover letter adaptada com IA para cada vaga específica"""
    if not ANTHROPIC_KEY:
        return _static_cover(company, role)
    
    # Extrair keywords da descrição da vaga
    desc_lower = job_description.lower()
    matched = []
    skill_map = {
        "power bi": f"Power BI expert (DAX, Power Query, RLS, Deployment Pipelines) — PL-300 certified",
        "tableau": f"Tableau Desktop Specialist — advanced LODs, Parameters, Cohort Analysis",
        "looker": f"Looker/LookML — custom explores, dashboards, data modeling",
        "sql": f"15+ years advanced SQL/T-SQL — performance tuning, complex analytics",
        "python": f"Python (pandas, scikit-learn) — automation, ML pipelines",
        "azure": f"Azure expertise: Synapse Analytics, ADF, Databricks, Azure ML",
        "bigquery": f"Google BigQuery — complex queries, cost optimization, 83% efficiency at Coca-Cola",
        "snowflake": f"Snowflake — data modeling, performance optimization",
        "databricks": f"Databricks SQL — large-scale analytics, 500M+ records/month",
        "dbt": f"dbt — data transformation, testing, documentation",
        "airflow": f"Apache Airflow — pipeline orchestration, scheduling",
        "healthcare": f"Healthcare analytics experience — regulatory compliance (HIPAA/ANS awareness)",
        "fintech": f"Financial services analytics — TIM/OI Telecom and Keyrus finance clients",
        "retail": f"Retail analytics — Coca-Cola and enterprise retail clients",
        "agile": f"Agile/Scrum practitioner — 15+ years enterprise delivery",
        "governance": f"Data Governance, SOX, GDPR compliance frameworks",
        "dashboard": f"Dashboard UX design — 200+ business users, executive-level storytelling",
        "kpi": f"KPI frameworks: CAC, LTV, ARPU, Churn, ROI, Retention, NPS",
        "machine learning": f"ML integration — scikit-learn, Azure ML, predictive/prescriptive models",
    }
    for kw, skill in skill_map.items():
        if kw in desc_lower: matched.append(skill)
    
    top_skills = matched[:5] if matched else [
        "Power BI (DAX, Power Query, RLS) — PL-300 certified",
        "15+ years SQL/T-SQL analytics engineering",
        "Azure Synapse + BigQuery + Snowflake + Databricks",
    ]
    
    # Detectar foco da vaga
    is_pbi   = "power bi" in desc_lower
    is_tab   = "tableau" in desc_lower
    is_cloud = any(k in desc_lower for k in ["azure","bigquery","snowflake","databricks"])
    is_eng   = any(k in desc_lower for k in ["engineer","pipeline","dbt","airflow"])
    
    tool_focus = "Power BI" if is_pbi else "Tableau" if is_tab else "BI toolstack"
    
    try:
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 600,
            "messages": [{
                "role": "user",
                "content": f"""Write a compelling 3-paragraph cover letter for this job:

Company: {company}
Role: {role}
Job Description (excerpt): {job_description[:1200]}

Candidate Profile:
- 15+ years Senior Data Analyst & {tool_focus} Developer
- PL-300 Microsoft Certified + Tableau Desktop Specialist + MBA
- Key achievements: USD 9M+ savings, 200+ business users, 70% latency reduction, 500M+ records/month
- Most relevant skills for THIS job: {'; '.join(top_skills)}
- Experience: Dataex (current), Keyrus BI consulting, Coca-Cola, TIM/OI Telecom

Rules:
- Start with a STRONG hook about the specific role at {company}
- Para 2: Match top 3 specific requirements from the job description to concrete achievements
- Para 3: Why {company} specifically + call to action
- Tone: confident, data-driven, professional
- Max 3 paragraphs, no fluff
- Do NOT include "Dear Hiring Team" or sign-off (will be added separately)
- Output ONLY the 3 paragraphs, nothing else"""
            }]
        }).encode()
        
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY,
                     "anthropic-version": "2023-06-01"}
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read())
            return resp["content"][0]["text"].strip()
    except Exception as e:
        return _static_cover(company, role, top_skills)

def _static_cover(company, role, skills=None):
    skills = skills or ["Power BI (PL-300)", "15+ years analytics engineering", "Azure/BigQuery/Snowflake"]
    return f"""I am applying for the {role} position at {company}. As a Senior Data Analyst and Analytics Engineer with 15+ years of enterprise BI experience, I bring a proven track record of delivering measurable impact: USD 9M+ in operational savings, 70% report latency reduction, and self-service analytics for 200+ business users.

My expertise aligns precisely with this role: {'; '.join(skills[:3])}. At Dataex, I currently architect Power BI solutions on BigQuery, Snowflake, and Databricks. Previously at Keyrus (global BI consultancy), I optimized 70% of query performance across Azure Synapse environments. I hold Microsoft PL-300 (Power BI Data Analyst), Tableau Desktop Specialist, and MBA certifications.

I am immediately available for remote positions and eager to bring this depth of experience to {company}. I would welcome the opportunity to discuss how my analytics engineering background aligns with your team's goals."""

# ── Job Sources ───────────────────────────────────────────────────────────────
def fetch_greenhouse_jobs():
    """API pública Greenhouse — vagas abertas verificadas"""
    BOARDS = [
        "stripe","chime","adyen","intercom","okta","nubank","braze","elastic",
        "clickhouse","datadog","affirm","launchdarkly","waymo","twilio",
        "databricks","salesloft","vtex","fastly","contentful","showpad",
        "mongodb","attentive","sigmoid","robinhood","amplitude","mixpanel",
        "fullstory","heap","pendo","thoughtspot","hex","metabase","dbt-labs",
        "fivetran","airbyte","hightouch","gusto","rippling","lattice","gong",
        "klaviyo","pagerduty","linear","sentry","algolia","coinbase","plaid",
        "zendesk","hubspot","shopify","gitlab","cloudflare","zapier",
        "benchling","natera","flatiron","veeva","blend","chime",
        "brex","ramp","mercury","faire","duolingo","coursera",
        "seatgeek","betterment","wealthfront","squarespace",
    ]
    jobs = []
    for co in BOARDS:
        try:
            url = f"https://boards-api.greenhouse.io/v1/boards/{co}/jobs"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
            for j in data.get("jobs", []):
                if chk(j.get("title", "")):
                    jobs.append({
                        "id":       f"gh_{j['id']}",
                        "company":  co.replace("-", " ").title(),
                        "role":     j["title"],
                        "url":      j.get("absolute_url", ""),
                        "desc":     j.get("content", "")[:2000],
                        "location": j.get("location", {}).get("name", "Remote"),
                        "platform": "Greenhouse",
                        "method":   "greenhouse_form",
                    })
            time.sleep(0.1)
        except: pass
    return jobs

def fetch_indeed_jobs():
    """Indeed RSS feeds para US + EU + Global"""
    jobs = []
    feeds = [
        # US remote
        "https://www.indeed.com/rss?q=senior+power+bi+developer&l=remote&jt=fulltime&sort=date",
        "https://www.indeed.com/rss?q=senior+data+analyst+remote&jt=fulltime&sort=date",
        "https://www.indeed.com/rss?q=analytics+engineer+remote&jt=fulltime&sort=date",
        "https://www.indeed.com/rss?q=business+intelligence+analyst+remote&jt=fulltime&sort=date",
        # UK
        "https://www.indeed.co.uk/rss?q=senior+power+bi+developer&l=remote&jt=fulltime&sort=date",
        "https://www.indeed.co.uk/rss?q=senior+data+analyst+remote&jt=fulltime&sort=date",
        # Netherlands / Europe
        "https://www.indeed.nl/rss?q=senior+data+analyst&l=remote&jt=fulltime&sort=date",
        "https://www.indeed.de/rss?q=senior+data+analyst&l=remote&jt=fulltime&sort=date",
        # Canada / Australia
        "https://ca.indeed.com/rss?q=senior+power+bi+developer&l=remote&jt=fulltime&sort=date",
        "https://au.indeed.com/rss?q=senior+data+analyst&l=remote&jt=fulltime&sort=date",
    ]
    for feed_url in feeds:
        try:
            req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                rss = r.read().decode("utf-8", "ignore")
            items = re.findall(r"<item>(.*?)</item>", rss, re.DOTALL)
            for item in items:
                title_m   = re.search(r"<title><!\[CDATA\[(.*?)\]\]>|<title>(.*?)</title>", item)
                link_m    = re.search(r"<link>(.*?)</link>", item)
                guid_m    = re.search(r"<guid[^>]*>(.*?)</guid>", item)
                source_m  = re.search(r"<source[^>]*>(.*?)</source>", item)
                desc_m    = re.search(r"<description><!\[CDATA\[(.*?)\]\]>", item, re.DOTALL)
                title = (title_m.group(1) or title_m.group(2)).strip() if title_m else ""
                if not chk(title): continue
                link  = link_m.group(1).strip()  if link_m  else ""
                guid  = guid_m.group(1).strip()  if guid_m  else link
                co    = source_m.group(1).strip() if source_m else "?"
                desc  = re.sub(r"<[^>]+>", "", desc_m.group(1)) if desc_m else ""
                jid   = hashlib.md5(guid.encode()).hexdigest()[:14]
                # Detectar país
                country = "US"
                if "indeed.co.uk" in feed_url: country = "UK"
                elif "indeed.nl"   in feed_url: country = "NL"
                elif "indeed.de"   in feed_url: country = "DE"
                elif "ca.indeed"   in feed_url: country = "CA"
                elif "au.indeed"   in feed_url: country = "AU"
                jobs.append({
                    "id":       f"indeed_{jid}",
                    "company":  co,
                    "role":     title,
                    "url":      link,
                    "desc":     desc[:2000],
                    "location": f"Remote ({country})",
                    "platform": f"Indeed ({country})",
                    "method":   "indeed_email",
                    "country":  country,
                })
            time.sleep(0.3)
        except: pass
    # Dedup
    seen = set(); unique = []
    for j in jobs:
        if j["id"] not in seen: seen.add(j["id"]); unique.append(j)
    return unique

def fetch_dice_jobs():
    """Dice remote jobs US"""
    jobs = []
    searches = [
        "power+bi+developer", "senior+data+analyst", "analytics+engineer",
        "business+intelligence+analyst", "bi+developer", "tableau+developer"
    ]
    for q in searches:
        try:
            url = (f"https://job-search-api.svc.dhigroupinc.com/v1/dice/jobs/search"
                   f"?q={q}&countryCode2=US&radius=30&radiusUnit=mi&page=1&pageSize=20"
                   f"&filters.workplaceTypes=Remote&filters.employmentType=FULLTIME"
                   f"&fields=id,title,companyName,salary,detailsPageUrl,postedDate,employerType")
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "x-api-key": "1YAt0R9wBg4WfsF9VB2778F4BkEFeDe0"
            })
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            for j in data.get("data", []):
                title = j.get("title", "")
                if not chk(title): continue
                jid = j.get("id") or j.get("guid", hashlib.md5(title.encode()).hexdigest()[:10])
                jobs.append({
                    "id":       f"dice_{jid}",
                    "company":  j.get("companyName", "?"),
                    "role":     title,
                    "url":      j.get("detailsPageUrl", ""),
                    "desc":     "",
                    "location": "Remote (US)",
                    "platform": "Dice",
                    "method":   "dice_easy_apply",
                    "salary":   j.get("salary", ""),
                })
            time.sleep(0.5)
        except: pass
    seen = set(); unique = []
    for j in jobs:
        if j["id"] not in seen: seen.add(j["id"]); unique.append(j)
    return unique

def fetch_remoteok_jobs():
    """Remote OK API"""
    jobs = []
    for tag in ["data-analyst", "bi-developer", "analytics"]:
        try:
            req = urllib.request.Request(
                f"https://remoteok.com/api?tags={tag}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            for j in data:
                if not isinstance(j, dict): continue
                pos = j.get("position", "")
                if not chk(pos): continue
                jid = str(j.get("id", hashlib.md5(pos.encode()).hexdigest()[:10]))
                jobs.append({
                    "id":       f"rok_{jid}",
                    "company":  j.get("company", "?"),
                    "role":     pos,
                    "url":      j.get("url", ""),
                    "desc":     j.get("description", "")[:2000],
                    "location": "Remote (Global)",
                    "platform": "Remote OK",
                    "method":   "remoteok_email",
                    "tags":     " ".join(j.get("tags", [])),
                })
            time.sleep(0.5)
        except: pass
    seen = set(); unique = []
    for j in jobs:
        if j["id"] not in seen: seen.add(j["id"]); unique.append(j)
    return unique

def fetch_wwr_jobs():
    """We Work Remotely RSS"""
    jobs = []
    try:
        req = urllib.request.Request(
            "https://weworkremotely.com/categories/remote-data-analysis-jobs.rss",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            rss = r.read().decode("utf-8", "ignore")
        items = re.findall(r"<item>(.*?)</item>", rss, re.DOTALL)
        for item in items:
            title_m = re.search(r"<title><!\[CDATA\[(.*?)\]\]>", item)
            link_m  = re.search(r"<link>(https?://[^\s<]+)", item)
            guid_m  = re.search(r"<guid[^>]*>(.*?)</guid>", item)
            title = title_m.group(1).strip() if title_m else ""
            if not chk(title): continue
            link = link_m.group(1).strip() if link_m else ""
            guid = guid_m.group(1).strip() if guid_m else link
            jid  = hashlib.md5(guid.encode()).hexdigest()[:12]
            # title format: "Company: Role"
            parts = title.split(":", 1)
            co   = parts[0].strip() if len(parts) > 1 else "?"
            role = parts[1].strip() if len(parts) > 1 else title
            jobs.append({
                "id":       f"wwr_{jid}",
                "company":  co,
                "role":     role,
                "url":      link,
                "desc":     "",
                "location": "Remote (Global)",
                "platform": "WWR",
                "method":   "wwr_apply",
            })
    except: pass
    return jobs

# ── Apply via Greenhouse form ─────────────────────────────────────────────────
def apply_greenhouse_form(ctx, job, cover_letter):
    """Preenche formulário Greenhouse com cover letter adaptada"""
    board_id  = re.search(r"greenhouse\.io/(?:embed/job_app\?for=)?([^&/?]+)", job["url"])
    job_token = re.search(r"token=(\d+)", job["url"])
    
    urls_to_try = [job["url"]]
    if board_id and job_token:
        urls_to_try.append(f"https://boards.greenhouse.io/embed/job_app?for={board_id.group(1)}&token={job_token.group(1)}")
    
    for url in urls_to_try:
        page = ctx.new_page()
        try:
            page.goto(url, timeout=25000)
            page.wait_for_load_state("domcontentloaded", timeout=12000)
            time.sleep(3)
            if "greenhouse.io" not in page.url: page.close(); continue
            
            # Preencher campos
            fields_filled = 0
            form_fields = [
                ("input[name='first_name'], #first_name", "Rafael"),
                ("input[name='last_name'], #last_name", "Rodrigues"),
                ("input[name='email'], #email", PROFILE["email"]),
                ("input[name='phone'], #phone", PROFILE["phone"]),
            ]
            for sel, val in form_fields:
                for s in sel.split(","):
                    try:
                        el = page.locator(s.strip()).first
                        if el.is_visible(timeout=800): el.clear(); el.fill(val); fields_filled += 1; break
                    except: pass
            
            # LinkedIn
            for sel in ["input[name*='linkedin']", "input[id*='linkedin']", "input[placeholder*='LinkedIn']"]:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=800): el.clear(); el.fill(PROFILE["linkedin"]); break
                except: pass
            
            # Location
            for sel in ["input[name*='location']", "input[placeholder*='City']", "#job_application_location"]:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=800): el.clear(); el.fill("Brazil"); break
                except: pass
            
            # Upload CV
            if os.path.exists(CV):
                for sel in ["input[type='file'][name='resume']", "input[type='file'][id*='resume']", "input[type='file']"]:
                    try:
                        el = page.locator(sel).first
                        if el.count(): el.set_input_files(CV); time.sleep(2); break
                    except: pass
            
            # Cover letter adaptada pela IA
            for sel in ["textarea[name*='cover']", "textarea[id*='cover']", "#cover_letter_text",
                        "textarea[name*='resume']"]:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=800):
                        el.clear()
                        el.fill(f"Dear Hiring Team at {job['company']},\n\n{cover_letter}\n\nBest regards,\nRafael Rodrigues\n{PROFILE['phone']}\n{PROFILE['email']}\n{PROFILE['linkedin']}")
                        break
                except: pass
            
            # Campos dropdown — autorização de trabalho
            for sel in ["select[name*='authorized']", "select[name*='sponsor']", "select[name*='work_auth']"]:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=800):
                        # Tentar encontrar opção "Yes" ou "Authorized"
                        for opt in ["Yes", "Authorized", "1", "true"]:
                            try: el.select_option(label=opt); break
                            except: pass
                except: pass
            
            # Submit
            if fields_filled >= 2:
                for sel in ["input[type='submit']", "button[type='submit']:has-text('Submit')",
                            "button[type='submit']:has-text('Apply')", "#submit_app",
                            "button#submit_app", "input[value*='Submit']"]:
                    try:
                        el = page.locator(sel).first
                        if el.is_visible(timeout=2000):
                            el.click(force=True); time.sleep(5)
                            body = page.inner_text("body")[:400]
                            if any(w in body.lower() for w in ["thank you","application received","submitted","applied","success"]):
                                page.close(); return "success"
                            elif any(w in body.lower() for w in ["error","required","invalid"]):
                                page.close(); return "form_error"
                            page.close(); return "submitted"
                    except: pass
            page.close(); return f"fields_{fields_filled}"
        except PWTimeout:
            try: page.close()
            except: pass
            return "timeout"
        except Exception as e:
            try: page.close()
            except: pass
            return f"err:{str(e)[:30]}"
    return "no_valid_url"

# ── Apply via Email ───────────────────────────────────────────────────────────
def apply_via_email(job, cover_letter, server):
    """Envia email com cover letter adaptada e CV em anexo"""
    to_email = job.get("email", "")
    if not to_email: return "no_email"
    
    msg = MIMEMultipart()
    msg["Subject"] = f"Application: {job['role']} — 15+ Yrs | PL-300 | {PROFILE['phone']} | Available Immediately"
    msg["From"]    = f"Rafael Rodrigues <{GMAIL}>"
    msg["To"]      = to_email
    msg["Reply-To"]= PROFILE["email"]
    
    body = f"""Dear Hiring Team at {job['company']},

{cover_letter}

Best regards,
Rafael Rodrigues
{PROFILE['phone']} | {PROFILE['email']}
LinkedIn: {PROFILE['linkedin']}
"""
    msg.attach(MIMEText(body, "plain"))
    if os.path.exists(CV):
        with open(CV, "rb") as f:
            att = MIMEBase("application","octet-stream"); att.set_payload(f.read())
        encoders.encode_base64(att)
        att.add_header("Content-Disposition","attachment",filename="Rafael_Rodrigues_CV.pdf")
        msg.attach(att)
    try:
        server.sendmail(GMAIL, to_email, msg.as_string())
        return "sent"
    except Exception as e:
        return f"smtp_err:{str(e)[:30]}"

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n{'='*70}")
    print(f"  AI-ADAPTIVE JOB HUNTER — {today}")
    print(f"  Greenhouse · Indeed (US/UK/EU/CA/AU) · Dice · Remote OK · WWR")
    print(f"  IA: Cover letter personalizada para cada vaga")
    print(f"{'='*70}\n")
    
    # ── Descoberta de vagas ──────────────────────────────────────────────
    print("── DESCOBERTA ──────────────────────────────────────────────────────")
    print("  Greenhouse...  ", end="", flush=True); gh   = fetch_greenhouse_jobs();  print(f"{len(gh)}")
    print("  Indeed...      ", end="", flush=True); ind  = fetch_indeed_jobs();       print(f"{len(ind)}")
    print("  Dice...        ", end="", flush=True); dice = fetch_dice_jobs();          print(f"{len(dice)}")
    print("  Remote OK...   ", end="", flush=True); rok  = fetch_remoteok_jobs();     print(f"{len(rok)}")
    print("  WWR...         ", end="", flush=True); wwr  = fetch_wwr_jobs();           print(f"{len(wwr)}")
    
    all_jobs = gh + ind + dice + rok + wwr
    new_jobs = [j for j in all_jobs if not already_applied(j["id"])]
    print(f"\n  Total encontradas: {len(all_jobs)} | Novas (não aplicadas): {len(new_jobs)}\n")
    
    if not new_jobs:
        print("✅ Nenhuma vaga nova hoje. Sistema saudável."); return
    
    # ── SMTP para emails ──────────────────────────────────────────────────
    smtp_server = None
    if GPASS:
        try:
            smtp_server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            smtp_server.login(GMAIL, GPASS)
        except: smtp_server = None
    
    # ── Playwright para formulários ───────────────────────────────────────
    print("── CANDIDATANDO (com IA adaptativa) ────────────────────────────────")
    success = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
                  "--disable-blink-features=AutomationControlled"]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width":1280,"height":800}, locale="en-US"
        )
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        
        for i, job in enumerate(new_jobs[:60], 1):
            co   = job["company"][:20]
            role = job["role"][:40]
            plat = job["platform"][:10]
            print(f"  [{i:2}/{min(len(new_jobs),60)}] [{plat:10}] {co:<22} {role:<40}", end=" ", flush=True)
            
            # Gerar cover letter adaptada com IA
            cover = generate_adaptive_cover(job["company"], job["role"], job.get("desc",""))
            
            # Aplicar conforme método
            if job["method"] == "greenhouse_form":
                result = apply_greenhouse_form(ctx, job, cover)
            elif job["method"] in ("indeed_email","remoteok_email","wwr_apply") and smtp_server:
                job["email"] = job.get("email","")
                result = "navigated"  # Email direto requer email do recrutador
            else:
                result = "tracked"  # Registrar para acompanhamento manual
            
            ok   = any(k in result for k in ["success","submitted","sent"])
            icon = "✅" if ok else "📋" if result in ("tracked","navigated") else "⚠️ "
            print(f"{icon} {result}")
            
            save_application(job["company"], job["role"], job["url"], job["id"],
                           result, job["platform"], job["method"], cover[:300])
            if ok: success += 1
            time.sleep(2)
        
        browser.close()
    
    if smtp_server: smtp_server.quit()
    
    print(f"\n{'='*70}")
    print(f"  ✅ {success} candidaturas confirmadas")
    print(f"  📋 {len(new_jobs[:60])-success} registradas para acompanhamento")
    print(f"  🤖 Cover letters geradas por IA para cada vaga")
    print(f"  {today}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
