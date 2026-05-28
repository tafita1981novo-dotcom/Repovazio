#!/usr/bin/env python3
"""
APPLY NOW — Candidatura imediata nas vagas Dice/Indeed verificadas
Philo (GH) · TORC Robotics (GH) · Ferguson (Workday)
+ Dice Easy Apply com login Daniela1982@
"""
import os, time, json, datetime, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

SUPA  = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
KEY   = os.environ.get("SUPABASE_ANON_KEY","")
DICE_EMAIL    = os.environ.get("DICE_EMAIL","tafita81@gmail.com")
DICE_PASSWORD = os.environ.get("DICE_PASSWORD","Daniela1982@")
AKEY  = os.environ.get("ANTHROPIC_API_KEY","")

PROFILE = {
    "first": "Rafael", "last": "Rodrigues",
    "email": "Rafa_roberto2004@yahoo.com.br",
    "phone": "+5522992418257",
    "linkedin": "https://linkedin.com/in/rafael-r-a3946a15",
    "location": "Brazil",
    "cv": ".github/assets/rafael_cv.pdf",
}

def save_app(company, role, url, jid, status, platform):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    req = urllib.request.Request(f"{SUPA}/rest/v1/job_applications",
        data=json.dumps({"company":company,"role":role,"url":url,"job_id":str(jid),
            "application_method":platform.lower().replace(" ","_"),"status":status,
            "platform":platform,"applied_at":now,"email":PROFILE["email"]}).encode(),
        method="POST",
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"})
    try:
        with urllib.request.urlopen(req, timeout=8): pass
    except: pass

def ai_cover(company, role, desc):
    if not AKEY: return f"""I am applying for the {role} position at {company}.

Senior Data Analyst and Power BI Developer with 15+ years of enterprise BI experience across Telecom, Retail, Financial Services, and Consulting. Currently at Dataex building Power BI + Tableau + Looker solutions for 200+ business users on BigQuery, Snowflake, and Databricks. Certified Microsoft PL-300 and Tableau Desktop Specialist.

Key achievements: USD 9M+ operational savings, 70% report latency reduction, 500M+ records/month processed. Available immediately for remote work.

Rafael Rodrigues | +5522992418257 | Rafa_roberto2004@yahoo.com.br"""
    
    try:
        payload = json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":400,
            "messages":[{"role":"user","content":f"""2 short paragraphs cover letter for {role} at {company}.
Candidate: 15+ yr Senior Data Analyst, Power BI PL-300, Tableau, SQL, Azure Synapse, BigQuery, Snowflake, Databricks, dbt.
Achievements: USD 9M+ savings, 70% latency reduction, 200+ users. Available immediately remote.
Job context: {desc[:400]}
Output ONLY the 2 paragraphs, no greeting, no sign-off."""}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages",data=payload,
            headers={"Content-Type":"application/json","x-api-key":AKEY,"anthropic-version":"2023-06-01"})
        with urllib.request.urlopen(req,timeout=20) as r:
            return json.loads(r.read())["content"][0]["text"].strip()
    except:
        return f"I am applying for the {role} position at {company}. 15+ years Senior Data Analyst, Power BI PL-300, Tableau, Azure Synapse, BigQuery, Snowflake. USD 9M+ savings, 200+ users. Available immediately remote."

# ─── Greenhouse Form ──────────────────────────────────────────────────────────
def apply_gh_form(ctx, company, role, url, job_id):
    pg = ctx.new_page()
    try:
        pg.goto(url, timeout=25000)
        pg.wait_for_load_state("domcontentloaded", timeout=12000)
        time.sleep(3)
        if "greenhouse" not in pg.url: pg.close(); return "redirect"
        
        cover = ai_cover(company, role, "")
        filled = 0
        
        for sel, val in [
            ("#first_name,input[name='first_name']", PROFILE["first"]),
            ("#last_name,input[name='last_name']", PROFILE["last"]),
            ("#email,input[name='email']", PROFILE["email"]),
            ("#phone,input[name='phone']", PROFILE["phone"]),
        ]:
            for s in sel.split(","):
                try:
                    el=pg.locator(s.strip()).first
                    if el.is_visible(timeout=600): el.clear(); el.fill(val); filled+=1; break
                except: pass
        
        for sel in ["input[name*='linkedin']","input[id*='linkedin']"]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=400): el.clear(); el.fill(PROFILE["linkedin"]); break
            except: pass
        
        if os.path.exists(PROFILE["cv"]):
            for sel in ["input[type='file'][name*='resume']","input[type='file']"]:
                try:
                    el=pg.locator(sel).first
                    if el.count(): el.set_input_files(PROFILE["cv"]); time.sleep(2); break
                except: pass
        
        for sel in ["textarea[name*='cover']","#cover_letter_text","textarea[id*='cover']"]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=400):
                    el.clear()
                    el.fill(f"Dear {company} Hiring Team,\n\n{cover}\n\nBest,\nRafael Rodrigues\n{PROFILE['phone']}")
                    break
            except: pass
        
        if filled >= 2:
            for sel in ["input[type='submit']","button[type='submit']","#submit_app","button#submit_app"]:
                try:
                    el=pg.locator(sel).first
                    if el.is_visible(timeout=1500):
                        el.click(force=True); time.sleep(6)
                        body=pg.inner_text("body")[:400].lower()
                        pg.close()
                        if any(w in body for w in ["thank","received","submitted","applied"]):
                            return "success"
                        return "submitted"
                except: pass
        
        pg.close()
        return f"fields_{filled}"
    except PWTimeout: pg.close(); return "timeout"
    except Exception as e: pg.close(); return f"err:{str(e)[:30]}"

# ─── Dice Login + Easy Apply ──────────────────────────────────────────────────
def dice_login(ctx):
    pg = ctx.new_page()
    try:
        # Tentar login direto com email+password
        pg.goto("https://www.dice.com/dashboard/login", timeout=20000)
        pg.wait_for_load_state("domcontentloaded", timeout=12000)
        time.sleep(2)
        
        # Email
        for sel in ["#email","input[name='email']","input[type='email']"]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=2000): el.fill(DICE_EMAIL); break
            except: pass
        
        # Continue
        for sel in ["button[type='submit']","#loginButton","button:has-text('Sign In')","button:has-text('Continue')"]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=1000): el.click(); time.sleep(3); break
            except: pass
        
        # Verificar se pediu senha
        passwd_visible = False
        for sel in ["#password","input[name='password']","input[type='password']"]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.fill(DICE_PASSWORD)
                    passwd_visible = True
                    break
            except: pass
        
        if passwd_visible:
            for sel in ["button[type='submit']","#loginButton","button:has-text('Sign In')"]:
                try:
                    el=pg.locator(sel).first
                    if el.is_visible(timeout=1000): el.click(); time.sleep(5); break
                except: pass
        
        time.sleep(3)
        url = pg.url
        logged = any(k in url for k in ["dashboard","find-jobs","jobs","home","profile"]) and "login" not in url
        print(f"    Dice login: {'✅' if logged else '⚠️'} → {url[:55]}")
        pg.close()
        return logged
    except Exception as e:
        try: pg.close()
        except: pass
        print(f"    Dice login erro: {str(e)[:40]}")
        return False

def dice_easy_apply(ctx, company, role, url, job_id):
    pg = ctx.new_page()
    try:
        pg.goto(url, timeout=20000)
        pg.wait_for_load_state("domcontentloaded", timeout=12000)
        time.sleep(3)
        
        applied = False
        for sel in ["button:has-text('Easy Apply')","[data-cy='easy-apply-btn']",
                    "button.btn-apply","button:has-text('Apply Now')"]:
            try:
                el=pg.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click(); time.sleep(4)
                    
                    # Preencher modal se aparecer
                    for fsel, fval in [
                        ("input[name='phone']", PROFILE["phone"]),
                        ("input[placeholder*='phone']", PROFILE["phone"]),
                        ("input[placeholder*='Phone']", PROFILE["phone"]),
                        ("input[name*='name']", "Rafael Rodrigues"),
                    ]:
                        try:
                            fel=pg.locator(fsel).first
                            if fel.is_visible(timeout=600): fel.fill(fval)
                        except: pass
                    
                    # Submit
                    for ssel in ["button:has-text('Submit')","button:has-text('Apply')",
                                 "button[type='submit']"]:
                        try:
                            sel_el=pg.locator(ssel).first
                            if sel_el.is_visible(timeout=1200):
                                sel_el.click(); time.sleep(3)
                                applied = True; break
                        except: pass
                    break
            except: pass
        
        pg.close()
        return "success" if applied else "clicked"
    except Exception as e:
        try: pg.close()
        except: pass
        return f"err:{str(e)[:25]}"

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n{'━'*60}")
    print(f"  🎯 APPLY NOW — Dice/Indeed Jobs — {today}")
    print(f"{'━'*60}\n")
    
    # Vagas confirmadas com ATS verificado
    GREENHOUSE_JOBS = [
        ("Philo",         "Senior Business Intelligence Analyst",
         "https://job-boards.greenhouse.io/philo/jobs/7958304",       "gh_philo_sbia"),
        ("TORC Robotics", "Senior BI Analyst",
         "https://job-boards.greenhouse.io/torcrobotics/jobs/8543",   "gh_torc_sbia"),
    ]
    
    DICE_EASY_APPLY = [
        ("Intersect Group",              "Lead Data Modeler",
         "https://www.dice.com/job-detail/f6493b90-5dc9-48db-a8e0-2f20600ff20d", "dice_f6493b90"),
        ("Innovative IT Technologies",   "Power BI Architect $69/h",
         "https://www.dice.com/job-detail/b3273a76-077f-4cfd-924f-f0d262fff6f7", "dice_b3273a76"),
        ("Drunix Solution",              "Senior Analytics Developer Power BI+Snowflake",
         "https://www.dice.com/job-detail/830dd703-b618-4a9c-868e-f142b8d38f43", "dice_830dd703"),
        ("Central Point Partners",       "Power BI Data Analyst $75-85K",
         "https://www.dice.com/job-detail/04cc1460-bede-4ced-adfd-428774213fad", "dice_04cc1460"),
        ("HMG America",                  "Power BI Developer Canada",
         "https://www.dice.com/job-detail/7daa4b44-f459-411e-bee3-1a23127329c5", "dice_7daa4b44"),
    ]
    
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage",
                  "--disable-blink-features=AutomationControlled"])
        ctx = br.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width":1280,"height":800},locale="en-US")
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        
        # 1. Greenhouse (Philo + TORC)
        print("── GREENHOUSE (via formulário) ─────────────────────────────")
        for co, role, url, jid in GREENHOUSE_JOBS:
            print(f"  {co:<25} {role[:35]}", end=" ", flush=True)
            res = apply_gh_form(ctx, co, role, url, jid)
            icon = "✅" if "success" in res or "submitted" in res else "⚠️ "
            print(f"{icon} {res}")
            save_app(co, role, url, jid, res, "Greenhouse")
            time.sleep(3)
        
        # 2. Dice Easy Apply
        print("\n── DICE EASY APPLY (com login) ─────────────────────────────")
        print(f"  Fazendo login: {DICE_EMAIL}")
        logged = dice_login(ctx)
        
        for co, role, url, jid in DICE_EASY_APPLY:
            print(f"  {co:<30} {role[:35]}", end=" ", flush=True)
            res = dice_easy_apply(ctx, co, role, url, jid)
            icon = "✅" if "success" in res else "📋" if "clicked" in res else "⚠️ "
            print(f"{icon} {res}")
            save_app(co, role, url, jid, res, "Dice")
            time.sleep(2)
        
        br.close()
    
    print(f"\n{'━'*60}")
    print(f"  Greenhouse: 2 | Dice Easy Apply: 5 | {today}")
    print(f"{'━'*60}\n")

if __name__ == "__main__":
    main()
