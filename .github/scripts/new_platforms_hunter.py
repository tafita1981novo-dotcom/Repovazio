#!/usr/bin/env python3
"""
NEW PLATFORMS HUNTER v1
40 plataformas remotas da lista:
- Remotive, WWR, Working Nomads, Jobspresso (API/RSS)
- JustRemote, DynamiteJobs, DailyRemote, HubstaffTalent (Playwright)
- FlexJobs, Turing, Arc.dev, Authentic Jobs, EuropeRemotely... (email direto)
- Upwork, Workana, Malt, Fiverr... (freelance → email)
"""
import os, json, time, re, datetime, urllib.request, urllib.parse, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

SUPA  = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
KEY   = os.environ.get("SUPABASE_ANON_KEY","")
AKEY  = os.environ.get("ANTHROPIC_API_KEY","")
GMAIL = os.environ.get("GMAIL_APP_PASSWORD","")
EM    = os.environ.get("DICE_EMAIL","tafita81@gmail.com")
CV    = ".github/assets/rafael_cv.pdf"
UA    = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0"
PROF  = {"first":"Rafael","last":"Rodrigues","email":"Rafa_roberto2004@yahoo.com.br",
         "phone":"+5522992418257","linkedin":"https://linkedin.com/in/rafael-r-a3946a15"}
KW    = ["data analyst","power bi","business intelligence","bi developer",
         "analytics engineer","reporting analyst","tableau","bi analyst",
         "data scientist","analytics","intelligence analyst"]
BOUNCE = {"hire@turing.com","work@andela.com","talent@toptal.com","hey@lemon.io",
          "work@gun.io","join@x-team.com","careers@toggl.com"}

# ── Email targets — plataformas sem API pública ──────────────────────────────
PLATFORM_EMAIL_TARGETS = [
    # FlexJobs companies (top employers)
    ("jobs@flexjobs.com",          "FlexJobs",        "Senior Data Analyst Remote"),
    ("hello@arc.dev",              "Arc.dev",         "Senior Data Analyst Power BI"),
    ("jobs@authenticjobs.com",     "Authentic Jobs",  "Business Intelligence Analyst"),
    ("talent@hubstaff.com",        "Hubstaff Talent", "Senior Data Analyst"),
    ("jobs@dynamitejobs.com",      "Dynamite Jobs",   "Business Intelligence Developer"),
    ("hello@remotive.com",         "Remotive",        "Senior Data Analyst"),
    ("jobs@justremote.co",         "JustRemote",      "Business Intelligence Analyst"),
    ("jobs@workingnomads.com",     "Working Nomads",  "Senior Data Analyst"),
    ("hello@jobspresso.co",        "Jobspresso",      "Power BI Developer"),
    # Scale.jobs
    ("hello@scale.jobs",           "Scale.jobs",      "Senior Data Analyst Power BI"),
    # Tech companies via Wellfound/AngelList that use email
    ("jobs@notion.so",             "Notion",          "Data Analyst Power BI"),
    ("careers@figma.com",          "Figma",           "Business Intelligence Analyst"),
    ("analytics@linear.app",       "Linear",          "Senior Data Analyst"),
    ("talent@vercel.com",          "Vercel",          "Data Analyst"),
    ("jobs@railway.app",           "Railway",         "Analytics Engineer"),
    # EuropeRemotely targets
    ("careers@remote.com",         "Remote.com",      "Senior Data Analyst"),
    ("jobs@deel.com",              "Deel",            "Business Intelligence Analyst"),
    ("talent@rippling.com",        "Rippling",        "Data Analyst Power BI"),
    ("careers@lattice.com",        "Lattice",         "Analytics Engineer"),
    ("jobs@culture-amp.com",       "Culture Amp",     "Data Analyst"),
    # Workana / Latin America
    ("hello@workana.com",          "Workana",         "Senior Data Analyst Power BI"),
    ("jobs@malt.com",              "Malt",            "Business Intelligence Consultant"),
    ("careers@outsourcely.com",    "Outsourcely",     "Senior Data Analyst"),
    # TechMeAbroad targets
    ("jobs@techmeabroad.com",      "TechMeAbroad",    "Data Analyst Power BI"),
    ("careers@workinstartups.com", "WorkInStartups",  "Business Intelligence Analyst"),
    # SkipTheDrive aggregator companies
    ("careers@automattic.com",     "Automattic",      "Senior Data Analyst"),
    ("jobs@invisionapp.com",       "InVision",        "Business Intelligence Analyst"),
    ("analytics@basecamp.com",     "Basecamp",        "Data Analyst"),
    ("jobs@zapier.com",            "Zapier",          "Analytics Engineer"),
    ("talent@buffer.com",          "Buffer",          "Senior Data Analyst"),
    # Real remote-first companies
    ("careers@gitlab.com",         "GitLab",          "Senior Data Analyst"),
    ("talent@github.com",          "GitHub",          "Business Intelligence Analyst"),
    ("analytics@shopify.com",      "Shopify",         "Senior Data Analyst"),
    ("careers@squarespace.com",    "Squarespace",     "Data Analyst Power BI"),
    ("jobs@hubspot.com",           "HubSpot",         "Business Intelligence Analyst"),
    ("analytics@mailchimp.com",    "Mailchimp",       "Senior Data Analyst"),
    ("careers@zendesk.com",        "Zendesk",         "Analytics Engineer"),
    ("jobs@intercom.com",          "Intercom",        "Business Intelligence Analyst"),
    ("analytics@twilio.com",       "Twilio",          "Senior Data Analyst"),
    ("careers@segment.com",        "Segment",         "Analytics Engineer"),
    ("jobs@amplitude.com",         "Amplitude",       "Senior Data Analyst"),
    ("analytics@mixpanel.com",     "Mixpanel",        "Business Intelligence Analyst"),
    ("jobs@datadog.com",           "Datadog",         "Senior Data Analyst"),
    ("careers@elastic.co",         "Elastic",         "Business Intelligence Developer"),
    ("talent@confluent.io",        "Confluent",       "Data Analyst Power BI"),
    ("analytics@dbt-labs.com",     "dbt Labs",        "Analytics Engineer"),
    ("jobs@fivetran.com",          "Fivetran",        "Senior Data Analyst"),
    ("careers@airbyte.com",        "Airbyte",         "Data Analyst"),
    ("analytics@hightouch.com",    "Hightouch",       "Senior Data Analyst"),
    ("jobs@monte-carlo.io",        "Monte Carlo",     "Analytics Engineer"),
]

def get(url, hdrs=None, timeout=8):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if hdrs: h.update(hdrs)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except: return ""

def sb(m, p, d=None):
    h = {"apikey":KEY,"Authorization":"Bearer "+KEY,"Content-Type":"application/json"}
    rq = urllib.request.Request(SUPA+"/rest/v1/"+p,
         data=json.dumps(d).encode() if d else None, method=m, headers=h)
    try:
        with urllib.request.urlopen(rq, timeout=8) as r:
            return json.loads(r.read()) if m=="GET" else r.status
    except Exception as e: return 409 if "409" in str(e) else None

def seen(jid):
    r = sb("GET","job_applications?job_id=eq."+urllib.parse.quote(str(jid))+"&select=id&limit=1")
    return isinstance(r, list) and len(r) > 0

def save(co, role, url, jid, status, platform, method):
    sb("POST","job_applications",{
        "company":co,"role":role,"url":url,"job_id":str(jid),
        "application_method":method,"status":status,"platform":platform,
        "applied_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "email":PROF["email"],"country":"US"})

def cover(co, role):
    if not AKEY:
        return f"15yr Senior DA PL-300 USD 9M+ savings Power BI Tableau SQL available for {role} at {co}."
    try:
        p = json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":200,
            "messages":[{"role":"user","content":
                f"2 tight paragraphs for {role} at {co}. Rafael 15yr DA PL-300 USD 9M savings "
                f"Power BI Tableau SQL Azure BigQuery. No greeting no sign-off."}]}).encode()
        rq = urllib.request.Request("https://api.anthropic.com/v1/messages",data=p,
            headers={"Content-Type":"application/json","x-api-key":AKEY,"anthropic-version":"2023-06-01"})
        with urllib.request.urlopen(rq,timeout=18) as r:
            return json.loads(r.read())["content"][0]["text"].strip()
    except: return f"15yr DA PL-300 available for {role} at {co}."

def send_email(to, co, role, jid):
    if not GMAIL or to in BOUNCE: return False
    if seen(jid): return False
    try:
        msg = MIMEMultipart()
        msg["From"]     = f"Rafael Rodrigues <{EM}>"
        msg["To"]       = to
        msg["Reply-To"] = PROF["email"]
        msg["Subject"]  = f"Senior Data Analyst / Power BI — {co}"
        body = (f"Dear {co} Hiring Team,\n\n{cover(co,role)}\n\n"
                f"Best regards,\nRafael Rodrigues\n{PROF['phone']} | {PROF['email']}")
        msg.attach(MIMEText(body, "plain"))
        if os.path.exists(CV):
            with open(CV,"rb") as f:
                att = MIMEApplication(f.read(), Name="Rafael_Rodrigues_CV.pdf")
                att["Content-Disposition"] = 'attachment; filename="Rafael_Rodrigues_CV.pdf"'
                msg.attach(att)
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
            s.login(EM,GMAIL); s.send_message(msg)
        save(co,role,f"mailto:{to}",jid,"sent","email","email_cv")
        return True
    except: return False

def fill_gh(ctx, co, role, url, jid):
    pg = ctx.new_page()
    try:
        pg.goto(url,timeout=18000); pg.wait_for_load_state("domcontentloaded",timeout=8000); time.sleep(1.5)
        if "greenhouse" not in pg.url: pg.close(); return "no_gh"
        cv_txt = cover(co,role); filled = 0
        for sel,val in [("#first_name",PROF["first"]),("input[name='first_name']",PROF["first"]),
                        ("#last_name",PROF["last"]),("input[name='last_name']",PROF["last"]),
                        ("#email",PROF["email"]),("input[name='email']",PROF["email"]),
                        ("#phone",PROF["phone"]),("input[name='phone']",PROF["phone"])]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=400): el.clear(); el.fill(val); filled+=1
            except: pass
        for sel in ["input[name*='linkedin']","input[id*='linkedin']"]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=300): el.fill(PROF["linkedin"])
            except: pass
        if os.path.exists(CV):
            for sel in ["input[type='file'][name*='resume']","input[type='file']"]:
                try:
                    el=pg.locator(sel).first
                    if el.count(): el.set_input_files(CV); time.sleep(2); break
                except: pass
        for sel in ["textarea[name*='cover']","#cover_letter_text"]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=300):
                    el.fill(f"Dear {co} Hiring Team,\n\n{cv_txt}\n\nBest,\nRafael\n{PROF['phone']}")
            except: pass
        if filled >= 2:
            for sel in ["input[type='submit']","button[type='submit']","#submit_app"]:
                try:
                    el=pg.locator(sel).first
                    if el.is_visible(timeout=1200):
                        el.click(force=True); time.sleep(5)
                        body=pg.inner_text("body")[:300].lower(); pg.close()
                        return "success" if any(w in body for w in ["thank","received","submitted"]) else "submitted"
                except: pass
        pg.close(); return f"fields_{filled}"
    except Exception as e:
        try: pg.close()
        except: pass
        return f"err:{str(e)[:20]}"

def find_ats(co, role=""):
    clean = re.sub(r'\b(inc|llc|corp|ltd|co|the|group|global|technologies|solutions)\b','',co.lower())
    slug_base = re.sub(r'[^a-z0-9]','',clean.strip())
    slug_dash  = re.sub(r'[^a-z0-9]','-',clean.strip()).strip('-')
    words = clean.split()
    slugs = list(dict.fromkeys([slug_base,slug_dash,slug_base[:10],
        words[0] if words else slug_base,
        ''.join(w for w in words if len(w)>2)]))[:6]
    for slug in slugs:
        if len(slug)<2: continue
        try:
            rq=urllib.request.Request(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
                headers={"User-Agent":UA})
            with urllib.request.urlopen(rq,timeout=4) as r:
                jobs=json.loads(r.read()).get("jobs",[])
            rel=[j for j in jobs if any(k in j.get("title","").lower() for k in KW)]
            if rel: return "gh",rel[0].get("absolute_url","")
            if jobs: return "gh",jobs[0].get("absolute_url","")
        except: pass
        try:
            rq2=urllib.request.Request(f"https://api.lever.co/v0/postings/{slug}?mode=json",
                headers={"User-Agent":UA})
            with urllib.request.urlopen(rq2,timeout=4) as r:
                jobs2=json.loads(r.read())
            if isinstance(jobs2,list) and jobs2:
                rel2=[j for j in jobs2 if any(k in j.get("text","").lower() for k in KW)]
                t=(rel2[0] if rel2 else jobs2[0])
                return "lever",t.get("hostedUrl","")
        except: pass
    return None,""

def process(ctx, co, role, source_url, jid, platform):
    print(f"    {co[:22]:<22} {role[:35]}", end=" ", flush=True)
    ats,apply_url = find_ats(co, role)
    if ats=="gh" and apply_url:
        res=fill_gh(ctx,co,role,apply_url,jid)
        icon="✅" if "success" in res or "submit" in res else "📋"
        print(f"→ {icon} GH:{res}")
        save(co,role,apply_url,jid,res,platform,"gh_form")
        return res
    elif ats=="lever":
        print(f"→ 📋 lever:{apply_url[:30]}")
        save(co,role,apply_url,jid,"ats_lever",platform,"lever")
        return "lever"
    else:
        domain=re.sub(r'[^a-z0-9]','',co.lower())[:20]
        for addr in [f"careers@{domain}.com",f"jobs@{domain}.com"]:
            if send_email(addr,co,role,jid+"_em"):
                print(f"→ 📧 {addr}"); return "email_sent"
        print(f"→ ⚠️  no_channel"); save(co,role,source_url,jid,"no_channel",platform,"miss")
        return "no_channel"

# ── Scrapers ─────────────────────────────────────────────────────────────────

def run_remotive(ctx):
    print("\n  ── REMOTIVE ──────────────────────────────────")
    ok=processed=0
    for q in ["data analyst","power bi","business intelligence","analytics engineer","tableau","reporting analyst"]:
        try:
            raw=get(f"https://remotive.com/api/remote-jobs?search={urllib.parse.quote(q)}&limit=30")
            jobs=json.loads(raw).get("jobs",[])
            for j in jobs:
                if not any(k in j.get("title","").lower() for k in KW): continue
                jid=f"remotive_{j.get('id','')}"
                if seen(jid): continue
                co=j.get("company_name","?"); role=j.get("title","?")
                res=process(ctx,co,role,j.get("url",""),jid,"Remotive")
                if "success" in res or "submit" in res or "email_sent" in res: ok+=1
                processed+=1; time.sleep(0.8)
        except: pass
    print(f"  Remotive: {processed} processadas, {ok} aplicadas")

def run_wwr(ctx):
    print("\n  ── WE WORK REMOTELY ──────────────────────────")
    ok=processed=0
    for feed_url in [
        "https://weworkremotely.com/remote-jobs.rss",
        "https://weworkremotely.com/categories/remote-data-science-jobs.rss",
    ]:
        raw=get(feed_url)
        if not raw: continue
        items=re.findall(r"<item>(.*?)</item>",raw,re.DOTALL)
        for item in items:
            t=re.search(r"<title>(?:<!\[CDATA\[)?([^\]<\n]{3,120})",item)
            l=re.search(r"<link>([^\s<]+)",item)
            if not t: continue
            title=t.group(1).strip()
            if not any(k in title.lower() for k in KW): continue
            # Formato: "Company: Role"
            co = title.split(":")[0].strip() if ":" in title else "?"
            role = title.split(":",1)[-1].strip() if ":" in title else title
            url = l.group(1).strip() if l else ""
            jid = f"wwr_{re.sub(r'[^a-z0-9]','',title.lower())[:20]}"
            if seen(jid): continue
            res=process(ctx,co,role,url,jid,"WWR")
            if "success" in res or "submit" in res or "email_sent" in res: ok+=1
            processed+=1; time.sleep(0.8)
    print(f"  WWR: {processed} processadas, {ok} aplicadas")

def run_working_nomads(ctx):
    print("\n  ── WORKING NOMADS ────────────────────────────")
    ok=processed=0
    raw=get("https://www.workingnomads.com/api/exposed_jobs/?category=development&limit=50")
    if not raw: return
    try: jobs=json.loads(raw)
    except: return
    if not isinstance(jobs,list): return
    for j in jobs:
        if not any(k in j.get("title","").lower() for k in KW): continue
        co=j.get("company_name","?") or "?"
        if co=="?":
            # Extrair do title se for "Company - Role"
            title=j.get("title","")
            if " - " in title: co=title.split(" - ")[0].strip()
            elif " | " in title: co=title.split(" | ")[0].strip()
        role=j.get("title","?")
        jid=f"wn_{re.sub(r'[^a-z0-9]','',role.lower())[:20]}"
        if seen(jid): continue
        url=j.get("url","")
        res=process(ctx,co,role,url,jid,"WorkingNomads")
        if "success" in res or "submit" in res or "email_sent" in res: ok+=1
        processed+=1; time.sleep(0.8)
    print(f"  WorkingNomads: {processed} processadas, {ok} aplicadas")

def run_jobspresso(ctx):
    print("\n  ── JOBSPRESSO ────────────────────────────────")
    ok=processed=0
    raw=get("https://jobspresso.co/feed/?post_type=job_listing")
    if not raw: return
    items=re.findall(r"<item>(.*?)</item>",raw,re.DOTALL)
    for item in items:
        t=re.search(r"<title>(?:<!\[CDATA\[)?([^\]<\n]{5,100})",item)
        l=re.search(r"<link>([^\s<]+)",item)
        if not t: continue
        role=t.group(1).strip()
        if not any(k in role.lower() for k in KW): continue
        url=l.group(1).strip() if l else ""
        jid=f"jsp_{re.sub(r'[^a-z0-9]','',role.lower())[:20]}"
        if seen(jid): continue
        # Visitar página para extrair empresa e apply URL
        pg=ctx.new_page()
        try:
            pg.goto(url,timeout=12000); pg.wait_for_load_state("domcontentloaded",timeout=6000); time.sleep(1.5)
            # Extrair empresa
            co="?"
            for sel in [".company-name","h2.company","span[class*='company']","[class*='employer']"]:
                try:
                    el=pg.locator(sel).first
                    if el.is_visible(timeout=500): co=el.inner_text().strip()[:40]; break
                except: pass
            # Extrair apply URL externo
            apply_url=""
            for sel in ["a.apply-button-link","a:has-text('Apply')","a[href*='greenhouse']","a[href*='lever.co']"]:
                try:
                    el=pg.locator(sel).first
                    if el.is_visible(timeout=500):
                        href=el.get_attribute("href") or ""
                        if href and len(href)>10: apply_url=href; break
                except: pass
            pg.close()
        except:
            try: pg.close()
            except: pass
        res=process(ctx,co,role,apply_url or url,jid,"Jobspresso")
        if "success" in res or "submit" in res or "email_sent" in res: ok+=1
        processed+=1; time.sleep(1)
    print(f"  Jobspresso: {processed} processadas, {ok} aplicadas")

def run_justremote(ctx):
    print("\n  ── JUSTREMOTE (Playwright) ───────────────────")
    ok=processed=0
    for q in ["data-analyst","business-intelligence","power-bi"]:
        pg=ctx.new_page()
        try:
            pg.goto(f"https://justremote.co/remote-{q}-jobs",timeout=20000)
            pg.wait_for_load_state("domcontentloaded",timeout=10000); time.sleep(2)
            html=pg.content(); pg.close()
            cos=re.findall(r'"company"\s*:\s*"([^"]+)"',html)
            roles=re.findall(r'"title"\s*:\s*"([^"]+)"',html)
            ids=re.findall(r'"id"\s*:\s*"?(\d+)"?',html)
            for i,co in enumerate(cos[:12]):
                role=roles[i] if i<len(roles) else q.replace("-"," ")
                if not any(k in role.lower() for k in KW): continue
                jid=f"jr3_{ids[i] if i<len(ids) else i}"
                if seen(jid): continue
                res=process(ctx,co,role,f"https://justremote.co",jid,"JustRemote")
                if "success" in res or "submit" in res or "email_sent" in res: ok+=1
                processed+=1; time.sleep(0.8)
        except:
            try: pg.close()
            except: pass
    print(f"  JustRemote: {processed} processadas, {ok} aplicadas")

def run_dynamitejobs(ctx):
    print("\n  ── DYNAMITE JOBS (Playwright) ────────────────")
    ok=processed=0
    pg=ctx.new_page()
    try:
        pg.goto("https://dynamitejobs.com/remote-jobs?q=data+analyst",timeout=20000)
        pg.wait_for_load_state("domcontentloaded",timeout=10000); time.sleep(2)
        html=pg.content(); pg.close()
        cos=re.findall(r'class="company[^"]*"[^>]*>([^<]+)<',html)
        roles=re.findall(r'class="position[^"]*"[^>]*>([^<]+)<',html)
        links=re.findall(r'href="(/remote-job/[^"]+)"',html)
        for i,(co,role) in enumerate(zip(cos[:12],roles)):
            if not any(k in role.lower() for k in KW): continue
            jid=f"dj_{re.sub(r'[^a-z0-9]','',role.lower())[:20]}"
            if seen(jid): continue
            url=f"https://dynamitejobs.com{links[i]}" if i<len(links) else ""
            res=process(ctx,co,role,url,jid,"DynamiteJobs")
            if "success" in res or "submit" in res or "email_sent" in res: ok+=1
            processed+=1; time.sleep(0.8)
    except:
        try: pg.close()
        except: pass
    print(f"  DynamiteJobs: {processed} processadas, {ok} aplicadas")

def run_platform_emails():
    print("\n  ── PLATFORM EMAIL TARGETS ────────────────────")
    ok=0
    for addr,co,role in PLATFORM_EMAIL_TARGETS:
        jid=f"pem_{re.sub(r'[^a-z0-9]','',co.lower())[:16]}"
        if seen(jid): continue
        print(f"    {co[:28]:<28}", end=" ", flush=True)
        sent=send_email(addr,co,role,jid)
        print("→ 📧 sent" if sent else "→ ⚠️  skip")
        if sent: ok+=1
        time.sleep(0.4)
    print(f"  Platform emails: {ok} enviados")

def main():
    from playwright.sync_api import sync_playwright
    today=datetime.date.today().strftime("%d/%m/%Y")
    print("\n"+"━"*58)
    print(f"  🌐 NEW PLATFORMS HUNTER v1 — {today}")
    print(f"  Remotive · WWR · WorkingNomads · Jobspresso · JustRemote")
    print(f"  DynamiteJobs · 50 platform email targets")
    print("━"*58)
    with sync_playwright() as pw:
        br=pw.chromium.launch(headless=True,args=[
            "--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
            "--disable-blink-features=AutomationControlled"])
        ctx=br.new_context(user_agent=UA,viewport={"width":1366,"height":768},locale="en-US",
            extra_http_headers={"Accept-Language":"en-US,en;q=0.9"})
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        run_remotive(ctx)
        run_wwr(ctx)
        run_working_nomads(ctx)
        run_jobspresso(ctx)
        run_justremote(ctx)
        run_dynamitejobs(ctx)
        br.close()
    run_platform_emails()
    print("\n"+"━"*58)
    print("  ✅ New Platforms Hunter concluído")
    print("━"*58+"\n")

if __name__=="__main__":
    main()
