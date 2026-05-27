#!/usr/bin/env python3
"""
MULTI-SOURCE JOB HUNTER — Remote OK, WWR, Landing.Jobs, Upwork, Jobatus
Rafael Rodrigues | +5522992418257
"""
import os, time, json, datetime, urllib.request, urllib.parse, hashlib, sys, re
import xml.etree.ElementTree as ET
from urllib.error import HTTPError
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

PHONE    = "+5522992418257"
REPLY_TO = "Rafa_roberto2004@yahoo.com.br"
GMAIL    = "tafita81@gmail.com"
APP_PASS = os.environ.get("GMAIL_APP_PASSWORD","")
SUPA_URL = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SUPA_KEY = os.environ.get("SUPABASE_ANON_KEY","")
CV_PATH  = ".github/assets/rafael_cv.pdf"

PROFILE = {
    "first_name":"Rafael","last_name":"Rodrigues",
    "email":REPLY_TO,"phone":PHONE,
    "linkedin":"https://linkedin.com/in/rafael-r-a3946a15",
    "current_company":"Dataex","current_title":"Senior Data Analyst",
    "years_experience":"15","location":"Brazil",
}

COVER = lambda role, co: f"""Dear {co} Hiring Team,

I am applying for the {role} position. I'm a Senior Data Analyst and Analytics Engineer with 15+ years of enterprise BI experience. Microsoft PL-300 Power BI Data Analyst certified. Available immediately for remote work.

Selected highlights:
• $9M+ operational savings — TIM/OI Telecommunications
• 70% report latency reduction via DAX/SQL — Keyrus consulting  
• Analytics platforms for 200+ business users (Financial Services, Retail, Telecom)
• 500M+ subscriber records/month environments
• Power BI · BigQuery · Snowflake · Databricks SQL · Azure Synapse · Python · SQL

Phone: {PHONE}
LinkedIn: https://linkedin.com/in/rafael-r-a3946a15
Available immediately for remote engagement.

Best regards,
Rafael Rodrigues — Senior Data Analyst | PL-300 Certified | {PHONE}
{REPLY_TO}"""

UPWORK_PROPOSAL = lambda role, co: f"""Hi,

I'm applying for your {role} opportunity. Senior Data Analyst & BI Engineer with 15+ years delivering enterprise analytics that generate measurable business impact.

**Why I'm the right fit:**
✅ $9M+ operational savings via analytics-driven optimization (TIM/OI Telecom, 500M+ records/month)
✅ 70% report latency reduction through DAX/SQL optimization at Keyrus (enterprise BI consultancy)
✅ End-to-end Power BI delivery: DAX · Power Query · RLS · Dataflows · Incremental Refresh
✅ Multi-cloud: BigQuery · Snowflake · Databricks SQL · Azure Synapse · Amazon Athena
✅ 200+ business users served | 12+ data sources integrated | Microsoft PL-300 certified

**Relevant experience for this project:**
- Enterprise Power BI dashboards for C-level stakeholders
- Complex DAX calculations, dimensional modeling (Star Schema, SCD 1/2)
- Python + SQL ETL automation
- Cloud DW (BigQuery at Coca-Cola, Snowflake/Databricks at Dataex)

I deliver clean, well-documented, scalable BI solutions — not just dashboards. My work creates lasting value.

Portfolio: linkedin.com/in/rafael-r-a3946a15
Phone/WhatsApp: {PHONE}

Available to start immediately. Happy to do a quick call to discuss your needs.

Best,
Rafael Rodrigues"""

KEYWORDS = ["data analyst","power bi","business intelligence","bi analyst",
            "analytics engineer","bi developer","reporting analyst","data visualization"]
def chk(t): return any(k in (t or "").lower() for k in KEYWORDS)

# ─── Supabase ─────────────────────────────────────────────────────────────────
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
    except: return {}, 0

def is_applied(eid):
    rows,_ = supa("GET","job_leads",
        params=f"external_id=eq.{urllib.parse.quote(str(eid))}&applied=eq.true&select=id")
    return isinstance(rows,list) and len(rows)>0

def mark_applied(eid, company, role, url, platform, method, status):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    supa("POST","job_leads",{"external_id":str(eid),"company":company,"role":role,
        "url":url,"platform":platform,"applied":True,"applied_at":now,"ats_type":method})
    supa("POST","job_applications",{"company":company,"role":role,"url":url,
        "application_method":method,"platform":platform,"status":status})

# ─── FONTE 1: Remote OK ───────────────────────────────────────────────────────
def search_remoteok():
    jobs = []; seen = set()
    for tag in ["analyst","analytics","sql","python","data","bi","intelligence"]:
        try:
            url = f"https://remoteok.com/api?tag={tag}"
            req = urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible)","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=10) as r:
                data = json.loads(r.read())
            for j in data:
                if not isinstance(j,dict): continue
                jid = str(j.get("id",j.get("slug",hash(str(j)))))
                if jid in seen: continue
                if not chk(j.get("position","")): continue
                seen.add(jid)
                jobs.append({
                    "id":f"rk_{jid}",
                    "company":j.get("company","Remote OK"),
                    "role":j.get("position","?"),
                    "url":j.get("url","https://remoteok.com"),
                    "apply_url":j.get("apply_url") or j.get("url",""),
                    "platform":"Remote OK",
                    "salary":j.get("salary",""),
                    "tags":j.get("tags",[]),
                    "ats_type":"remoteok",
                })
            time.sleep(0.4)
        except: pass
    return jobs

# ─── FONTE 2: WWR ─────────────────────────────────────────────────────────────
def search_wwr():
    jobs = []
    FEEDS = [
        "https://weworkremotely.com/categories/remote-data-jobs.rss",
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/remote-jobs.rss",
    ]
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
    for feed_url in FEEDS:
        try:
            req = urllib.request.Request(feed_url, headers={"User-Agent":"Mozilla/5.0"})
            with opener.open(req, timeout=12) as r:
                data = r.read()
            root = ET.fromstring(data)
            for i in root.findall('.//item'):
                title = i.findtext('title','')
                link  = i.findtext('link','') or i.findtext('guid','')
                desc  = i.findtext('description','')
                if not chk(title) and not chk(desc): continue
                # Extrair empresa do título (formato: "Empresa: Cargo")
                parts = title.split(':',1) if ':' in title else ["WWR", title]
                co    = parts[0].strip() if len(parts)>1 else "WWR Job"
                role  = parts[1].strip() if len(parts)>1 else title
                jid   = hashlib.md5(title.encode()).hexdigest()[:12]
                jobs.append({
                    "id":f"wwr_{jid}","company":co,"role":role,
                    "url":link,"apply_url":link,
                    "platform":"WWR","salary":"","ats_type":"wwr",
                })
        except: pass
    return jobs

# ─── FONTE 3: Landing.Jobs ────────────────────────────────────────────────────
def search_landing_jobs():
    jobs = []; seen = set()
    for page in range(1, 6):
        try:
            url = f"https://landing.jobs/api/v1/jobs?remote=true&q=data+analyst&page={page}"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            items = data if isinstance(data,list) else data.get("jobs",data.get("data",[]))
            if not items: break
            for j in (items if isinstance(items,list) else []):
                jid = str(j.get("id",""))
                if jid in seen: continue
                title = str(j.get("title","") or j.get("role","") or j.get("position",""))
                if not chk(title): continue
                seen.add(jid)
                co = ""
                if isinstance(j.get("company"),dict):
                    co = j["company"].get("name","?")
                elif j.get("company_name"):
                    co = j["company_name"]
                else:
                    co = str(j.get("company","Landing.Jobs"))
                jobs.append({
                    "id":f"lj_{jid}","company":co,"role":title,
                    "url":f"https://landing.jobs/jobs/{jid}",
                    "apply_url":f"https://landing.jobs/jobs/{jid}/apply",
                    "platform":"Landing.Jobs","salary":str(j.get("salary","") or ""),
                    "ats_type":"landing_jobs",
                })
            time.sleep(0.5)
        except: break
    
    # Também buscar power bi
    for q in ["power+bi","business+intelligence","analytics+engineer"]:
        try:
            url = f"https://landing.jobs/api/v1/jobs?remote=true&q={q}&page=1"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            items = data if isinstance(data,list) else data.get("jobs",data.get("data",[]))
            for j in (items if isinstance(items,list) else []):
                jid = str(j.get("id",""))
                if jid in seen: continue
                title = str(j.get("title","") or j.get("role","") or "")
                if not chk(title): continue
                seen.add(jid)
                co = str(j.get("company","?")) if not isinstance(j.get("company"),dict) else j["company"].get("name","?")
                jobs.append({"id":f"lj_{jid}","company":co,"role":title,
                    "url":f"https://landing.jobs/jobs/{jid}","apply_url":f"https://landing.jobs/jobs/{jid}",
                    "platform":"Landing.Jobs","salary":"","ats_type":"landing_jobs"})
        except: pass
    return jobs

# ─── FONTE 4: Upwork ─────────────────────────────────────────────────────────
def search_upwork_playwright(ctx):
    jobs = []
    try:
        page = ctx.new_page()
        page.goto("https://www.upwork.com/nx/search/jobs/?q=power+bi+data+analyst&remote_job_filter=ONLY_REMOTE&sort=recency", timeout=25000)
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(3)
        
        # Tentar extrair vagas do DOM
        job_tiles = page.locator("[data-test='job-tile-list'] article, .job-tile, [class*='JobTile']").all()
        if not job_tiles:
            job_tiles = page.locator("article, section[class*='job']").all()
        
        for tile in job_tiles[:20]:
            try:
                title_el = tile.locator("h2, h3, [class*='title']").first
                title = title_el.inner_text().strip() if title_el.count() else ""
                if not chk(title): continue
                
                link_el = tile.locator("a").first
                href = link_el.get_attribute("href") if link_el.count() else ""
                if href and not href.startswith("http"):
                    href = f"https://www.upwork.com{href}"
                
                jid = hashlib.md5(title.encode()).hexdigest()[:10]
                jobs.append({
                    "id":f"uw_{jid}","company":"Upwork Client","role":title,
                    "url":href or "https://www.upwork.com","apply_url":href or "",
                    "platform":"Upwork","salary":"","ats_type":"upwork",
                })
            except: pass
        page.close()
    except Exception as e:
        print(f"  Upwork search erro: {str(e)[:50]}")
    return jobs

# ─── FONTE 5: Jobatus via Playwright ─────────────────────────────────────────
def search_jobatus_playwright(ctx):
    jobs = []
    for url in ["https://www.jobatus.com.br/trabalhos-q-data-analyst+remote",
                "https://www.jobatus.es/ofertas-de-trabajo/data-analyst-remoto"]:
        try:
            page = ctx.new_page()
            page.goto(url, timeout=15000)
            page.wait_for_load_state("domcontentloaded", timeout=8000)
            
            # Procurar listagem de vagas
            job_links = page.locator("a[href*='/emprego/'], a[href*='/oferta/'], a[href*='/job/']").all()
            for link in job_links[:15]:
                try:
                    title = link.inner_text().strip()
                    href  = link.get_attribute("href") or ""
                    if chk(title) and href:
                        jid = hashlib.md5(title.encode()).hexdigest()[:10]
                        jobs.append({
                            "id":f"jb_{jid}","company":"Jobatus","role":title,
                            "url":href if href.startswith("http") else f"https://www.jobatus.com.br{href}",
                            "apply_url":href,"platform":"Jobatus","salary":"","ats_type":"jobatus",
                        })
                except: pass
            page.close()
            if jobs: break
        except: 
            try: page.close()
            except: pass
    return jobs

# ─── APLICAR VIA EMAIL ────────────────────────────────────────────────────────
SIG = f"""<br><br><table style="font-family:Arial;border-top:2px solid #1F3864;padding-top:12px;"><tr><td>
<div style="font-size:15px;font-weight:800;color:#1F3864;">Rafael Rodrigues</div>
<div style="font-size:12px;color:#5B21B6;">Senior Data Analyst · Analytics Engineer · Cloud BI Specialist</div>
<div style="font-size:11px;color:#555;line-height:1.9;margin-top:4px;">
📱 <strong>{PHONE}</strong><br>✉️ {REPLY_TO}<br>
🔗 linkedin.com/in/rafael-r-a3946a15<br>
🌎 Open to US/EU Remote · Available Immediately
</div></td></tr></table>"""

def send_email_app(server, company, role, to_email, platform, cv_bytes):
    cover = COVER(role, company)
    html = f"""<html><body style="font-family:Arial;max-width:680px;margin:0 auto;">
<div style="background:linear-gradient(135deg,#1F3864,#5B21B6);padding:20px 26px;border-radius:8px 8px 0 0;">
<div style="color:rgba(255,255,255,.7);font-size:10px;letter-spacing:3px;text-transform:uppercase;">Application via {platform}</div>
<div style="color:#fff;font-size:20px;font-weight:800;margin:6px 0 2px;">{role}</div>
<div style="color:rgba(255,255,255,.75);font-size:12px;">{company} · Rafael Rodrigues · PL-300 · {PHONE}</div>
</div>
<div style="background:#fff;padding:24px;border:1px solid #E5E7EB;border-top:none;border-radius:0 0 8px 8px;">
{"".join(f"<p style='font-size:13px;line-height:1.9;color:#374151;'>{p}</p>" for p in cover.split('\n\n') if p.strip())}
{SIG}</div></body></html>"""
    msg = MIMEMultipart("mixed")
    msg["From"]    = f"Rafael Rodrigues <{GMAIL}>"
    msg["To"]      = to_email
    msg["Subject"] = f"Application: {role} — 15+ Yrs Enterprise BI | PL-300 | {PHONE} | Available Now"
    msg["Reply-To"]= REPLY_TO
    msg.attach(MIMEText(html,"html"))
    if cv_bytes:
        att = MIMEBase("application","pdf"); att.set_payload(cv_bytes)
        encoders.encode_base64(att)
        att.add_header("Content-Disposition","attachment",filename="Rafael_Rodrigues_Senior_DA_CV.pdf")
        msg.attach(att)
    server.sendmail(GMAIL,[to_email],msg.as_string())

# ─── APPLY VIA PLAYWRIGHT (para links de apply) ───────────────────────────────
def apply_via_playwright(page, job, cv_path):
    apply_url = job.get("apply_url","") or job.get("url","")
    if not apply_url: return "no_url"
    
    # Se for Upwork — submeter proposta
    if "upwork.com" in apply_url:
        return apply_upwork(page, job, cv_path)
    
    # Se for Landing.Jobs — aplicar na plataforma
    if "landing.jobs" in apply_url:
        return apply_landing_jobs(page, job, cv_path)
    
    # Para outros (Remote OK, WWR, Jobatus): navegar para o apply_url
    # muitas vezes redireciona para Greenhouse/Lever do empregador
    try:
        page.goto(apply_url, timeout=20000)
        page.wait_for_load_state("domcontentloaded", timeout=12000)
        time.sleep(2)
        
        final_url = page.url
        co  = job["company"]
        role= job["role"]
        cover = COVER(role, co)
        
        # Verificar se está em Greenhouse
        if "greenhouse.io" in final_url or "boards.greenhouse.io" in final_url:
            # Tentar extrair company e job_id
            m = re.search(r'boards\.greenhouse\.io/(\w+)/jobs/(\d+)', final_url)
            if m:
                from playwright_hunter_v2_funcs import fill_fields, try_submit
                fill_fields(page, PROFILE, cv_path, cover)
                if try_submit(page): return "success_gh"
        
        # Verificar se está em Lever
        if "lever.co" in final_url or "jobs.lever.co" in final_url:
            for sel, val in [("input[name='name']", f"{PROFILE['first_name']} {PROFILE['last_name']}"),
                              ("input[name='email']", PROFILE["email"]),
                              ("input[name='phone']", PROFILE["phone"])]:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=1000): el.fill(val)
                except: pass
            if cv_path and os.path.exists(cv_path):
                try:
                    fi = page.locator("input[type='file']").first
                    if fi.count(): fi.set_input_files(cv_path)
                except: pass
            for sel in ["button[type='submit']","button:has-text('Submit')"]:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=1000):
                        el.click(force=True); time.sleep(3); return "success_lever"
                except: pass
        
        # Se chegou em página de vagas genérica — procurar botão Apply
        for sel in ["a:has-text('Apply')", "button:has-text('Apply')", 
                    "[class*='apply']", "a[href*='apply']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1000):
                    href = el.get_attribute("href") or ""
                    el.click(); time.sleep(2)
                    return "clicked_apply"
            except: pass
        
        return "opened_page"
    except PWTimeout:
        return "timeout"
    except Exception as e:
        return f"error:{str(e)[:40]}"

def apply_upwork(page, job, cv_path):
    """Tentar submeter proposta no Upwork"""
    try:
        url = job.get("url","")
        if not url: return "no_url"
        page.goto(url, timeout=20000)
        page.wait_for_load_state("domcontentloaded", timeout=12000)
        time.sleep(3)
        
        # Procurar botão "Apply Now" / "Submit Proposal"
        for sel in ["a:has-text('Apply Now')", "button:has-text('Apply Now')",
                    "button:has-text('Submit Proposal')", "a:has-text('Submit a Proposal')"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click(); time.sleep(3)
                    # Preencher cover letter
                    proposal = UPWORK_PROPOSAL(job["role"], job["company"])
                    for csel in ["textarea[placeholder*='cover']","textarea[name*='cover']",
                                 "textarea[class*='proposal']","textarea"]:
                        try:
                            ta = page.locator(csel).first
                            if ta.is_visible(timeout=1000):
                                ta.fill(proposal[:2000]); break
                        except: pass
                    # Submit
                    for bsel in ["button:has-text('Submit')", "button[type='submit']"]:
                        try:
                            btn = page.locator(bsel).first
                            if btn.is_visible(timeout=1000):
                                btn.click(force=True); time.sleep(2)
                                return "success_upwork"
                        except: pass
                    return "proposal_filled"
            except: pass
        return "no_apply_btn"
    except: return "upwork_error"

def apply_landing_jobs(page, job, cv_path):
    """Aplicar no Landing.Jobs"""
    try:
        page.goto(job["url"], timeout=15000)
        page.wait_for_load_state("networkidle", timeout=10000)
        # Procurar botão apply
        for sel in ["a:has-text('Apply')", "button:has-text('Apply')",
                    "a:has-text('Candidatar')", ".apply-btn"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1000):
                    href = el.get_attribute("href") or ""
                    el.click(); time.sleep(2)
                    # Se redireciona para Greenhouse/Lever
                    if "greenhouse.io" in page.url or "lever.co" in page.url:
                        return f"redirected_to_{page.url.split('/')[2]}"
                    return "clicked_apply_lj"
            except: pass
        return "no_btn_lj"
    except: return "lj_error"

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n{'='*65}")
    print(f"  MULTI-SOURCE HUNTER — {today}")
    print(f"  Tel: {PHONE}")
    print(f"{'='*65}\n")

    cv_bytes = b""
    if os.path.exists(CV_PATH):
        with open(CV_PATH,"rb") as f: cv_bytes = f.read()
        print(f"✅ CV: {len(cv_bytes):,} bytes\n")

    # Gmail
    server = None
    if APP_PASS:
        try:
            server = smtplib.SMTP("smtp.gmail.com",587)
            server.ehlo(); server.starttls()
            server.login(GMAIL,APP_PASS)
            print("✅ Gmail OK\n")
        except Exception as e:
            print(f"⚠️ Gmail: {e}\n")

    results = []

    # ── Fase 1: Descoberta de vagas ──────────────────────────────────────────
    print("── DESCOBERTA ──────────────────────────────────────────────────")
    rk_jobs  = search_remoteok()
    wwr_jobs = search_wwr()
    lj_jobs  = search_landing_jobs()
    
    print(f"  Remote OK:    {len(rk_jobs)} vagas")
    print(f"  WWR:          {len(wwr_jobs)} vagas")
    print(f"  Landing.Jobs: {len(lj_jobs)} vagas")

    all_jobs = rk_jobs + wwr_jobs + lj_jobs
    new_jobs = [j for j in all_jobs if not is_applied(j["id"])]
    print(f"  NOVAS (não aplicadas): {len(new_jobs)}\n")

    if not new_jobs:
        print("✅ Tudo já aplicado!\n")
        return

    # ── Fase 2: Aplicar ───────────────────────────────────────────────────────
    print("── APLICANDO ───────────────────────────────────────────────────")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu"]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            locale="en-US"
        )
        
        # Descobrir jobs Upwork + Jobatus via Playwright
        print("  Buscando Upwork...")
        uw_jobs = search_upwork_playwright(ctx)
        print(f"  Upwork: {len(uw_jobs)} vagas")
        
        print("  Buscando Jobatus...")
        jb_jobs = search_jobatus_playwright(ctx)
        print(f"  Jobatus: {len(jb_jobs)} vagas")
        
        extra = [j for j in uw_jobs+jb_jobs if not is_applied(j["id"])]
        new_jobs.extend(extra)
        print(f"  TOTAL NOVAS (com Upwork+Jobatus): {len(new_jobs)}\n")
        
        for i, job in enumerate(new_jobs[:50], 1):
            page = ctx.new_page()
            co   = job["company"]
            role = job["role"]
            plat = job["platform"]
            
            print(f"  [{i:2}/{min(len(new_jobs),50)}] [{plat:12}] {co[:20]:<22} {role[:38]}", end=" ", flush=True)
            
            # Tentar aplicar via Playwright
            result = apply_via_playwright(page, job, CV_PATH)
            
            # Se não conseguiu via Playwright e tem email, tenta email
            if result in ["no_url","opened_page","no_apply_btn"] and server:
                # Usar email de contato da empresa se disponível
                to = job.get("email","")
                if to:
                    try:
                        send_email_app(server, co, role, to, plat, cv_bytes)
                        result = "email_sent"
                    except: pass
            
            ok = any(k in result for k in ["success","email_sent","clicked","redirected","proposal"])
            icon = "✅" if "success" in result else "📨" if ok else "⚠️"
            print(f"{icon} {result}")
            
            mark_applied(job["id"],co,role,job["url"],plat,plat.lower().replace(" ","_"),
                        "success" if ok else result)
            results.append({"company":co,"role":role,"platform":plat,"result":result})
            
            try: page.close()
            except: pass
            time.sleep(2)
        
        browser.close()

    ok = sum(1 for r in results if any(k in r["result"] for k in ["success","email_sent","clicked","redirected","proposal"]))
    print(f"\n{'='*65}")
    print(f"  ✅ {ok}/{len(results)} candidaturas enviadas")
    print(f"  Plataformas: Remote OK + WWR + Landing.Jobs + Upwork + Jobatus")
    print(f"{'='*65}\n")

if __name__ == "__main__":
    main()
