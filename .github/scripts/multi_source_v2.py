#!/usr/bin/env python3
"""
MULTI-SOURCE HUNTER v2 — 10 novas plataformas 2025
Glassdoor · Jobright.ai · Simplify · Wellfound · myjobb.ai
+ Indeed (MCP) · Dice · Remote OK · WWR · Landing.Jobs
Rafael Rodrigues | +5522992418257
"""
import os, time, json, re, hashlib, datetime, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

PHONE    = "+5522992418257"
REPLY_TO = "Rafa_roberto2004@yahoo.com.br"
SUPA_URL = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SUPA_KEY = os.environ.get("SUPABASE_ANON_KEY","")

KEYWORDS = ["data analyst","power bi","business intelligence","analytics engineer",
            "bi developer","bi analyst","reporting analyst","data visualization"]
def chk(t): return any(k in (t or "").lower() for k in KEYWORDS)

def supa_post(table, data):
    url  = f"{SUPA_URL}/rest/v1/{table}"
    body = json.dumps(data).encode()
    req  = urllib.request.Request(url,data=body,method="POST",headers={
        "apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
        "Content-Type":"application/json","Prefer":"return=minimal"})
    try:
        with urllib.request.urlopen(req,timeout=10) as r: return r.status
    except: return 0

def is_applied(eid):
    url = f"{SUPA_URL}/rest/v1/job_leads?external_id=eq.{urllib.parse.quote(str(eid))}&applied=eq.true&select=id"
    req = urllib.request.Request(url,headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}"})
    try:
        with urllib.request.urlopen(req,timeout=8) as r:
            return len(json.loads(r.read())) > 0
    except: return False

def mark(eid, company, role, url, platform, method, status):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    supa_post("job_leads",{"external_id":str(eid),"company":company,"role":role,
        "url":url,"platform":platform,"applied":True,"applied_at":now,"ats_type":method})
    supa_post("job_applications",{"company":company,"role":role,"url":url,
        "application_method":method,"platform":platform,"status":status})

# ── GLASSDOOR — via GraphQL ───────────────────────────────────────────────────
def search_glassdoor(ctx):
    jobs = []
    try:
        page = ctx.new_page()
        gd_data = []
        def on_resp(resp):
            if "glassdoor.com/graph" in resp.url:
                try: gd_data.append(resp.json())
                except: pass
        page.on("response", on_resp)
        page.goto("https://www.glassdoor.com/Job/remote-power-bi-analyst-jobs-SRCH_IL.0,6_IS11047_KO7,23.htm", timeout=25000)
        page.wait_for_load_state("networkidle",timeout=15000); time.sleep(4)
        for resp in gd_data:
            resp_str = json.dumps(resp)
            matches = re.findall(r'"jobViewUrl":"([^"]+)"[^}]*"jobTitleText":"([^"]+)"[^}]*"employerName":"([^"]+)"', resp_str)
            for url_path, title, co in matches:
                if not chk(title): continue
                full_url = f"https://www.glassdoor.com{url_path}" if not url_path.startswith("http") else url_path
                jid = re.search(r'jobListingId=(\d+)', url_path)
                jid = jid.group(1) if jid else hashlib.md5(title.encode()).hexdigest()[:10]
                jobs.append({"id":f"gd_{jid}","company":co,"role":title,"url":full_url,
                    "platform":"Glassdoor","ats_type":"glassdoor"})
        page.close()
    except Exception as e:
        print(f"  Glassdoor: {str(e)[:50]}")
        try: page.close()
        except: pass
    return jobs

# ── JOBRIGHT.AI — via Next.js data ────────────────────────────────────────────
def search_jobright(ctx):
    jobs = []
    try:
        page = ctx.new_page()
        for search in ["Data-Analyst","Power-BI-Developer","Analytics-Engineer"]:
            page.goto(f"https://jobright.ai/jobs/{search}?remote=true&sortBy=date", timeout=25000)
            page.wait_for_load_state("domcontentloaded",timeout=15000); time.sleep(5)
            html = page.content()
            nd_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if nd_match:
                try:
                    nd = json.loads(nd_match.group(1))
                    job_list = nd.get("props",{}).get("pageProps",{}).get("jobList",[])
                    for item in job_list:
                        jr = item.get("jobResult",{})
                        title = jr.get("title","") or jr.get("jobTitle","")
                        co = jr.get("company","?")
                        if isinstance(co,dict): co = co.get("name","?")
                        jid = jr.get("jobId","") or jr.get("id","")
                        apply_url = jr.get("applyUrl","") or f"https://jobright.ai/jobs/{jid}"
                        if chk(title) and jid:
                            jobs.append({"id":f"jr_{jid}","company":str(co),"role":title,
                                "url":apply_url,"platform":"Jobright.ai","ats_type":"jobright"})
                except: pass
        page.close()
    except Exception as e:
        print(f"  Jobright: {str(e)[:50]}")
        try: page.close()
        except: pass
    # Dedup
    seen = set(); unique = []
    for j in jobs:
        if j["id"] not in seen: seen.add(j["id"]); unique.append(j)
    return unique

# ── SIMPLIFY.JOBS — via Playwright ────────────────────────────────────────────
def search_simplify(ctx):
    jobs = []
    try:
        page = ctx.new_page()
        sj_data = []
        def on_resp(resp):
            if "simplify.jobs" in resp.url and "json" in resp.headers.get("content-type",""):
                try:
                    data = resp.json()
                    sj_data.append({"url":resp.url,"data":data})
                except: pass
        page.on("response", on_resp)
        page.goto("https://simplify.jobs/jobs?search=power+bi+data+analyst&remote=true", timeout=25000)
        page.wait_for_load_state("networkidle",timeout=15000); time.sleep(5)
        
        # Tentar extrair dos dados capturados
        for r in sj_data:
            data = r["data"]
            if isinstance(data,list):
                for j in data:
                    title = j.get("title","") or j.get("name","")
                    if chk(title):
                        co = j.get("company","?")
                        if isinstance(co,dict): co = co.get("name","?")
                        jid = j.get("id","") or hashlib.md5(title.encode()).hexdigest()[:10]
                        jobs.append({"id":f"sj_{jid}","company":str(co),"role":title,
                            "url":f"https://simplify.jobs/jobs/{jid}","platform":"Simplify","ats_type":"simplify"})
        
        # Se não achou via API, tentar DOM
        if not jobs:
            html = page.content()
            job_blocks = re.findall(r'"title":"([^"]+)","company":\{"name":"([^"]+)"[^}]*\},"id":"([^"]+)"', html)
            for title, co, jid in job_blocks:
                if chk(title):
                    jobs.append({"id":f"sj_{jid}","company":co,"role":title,
                        "url":f"https://simplify.jobs/jobs/{jid}","platform":"Simplify","ats_type":"simplify"})
        page.close()
    except Exception as e:
        print(f"  Simplify: {str(e)[:50]}")
        try: page.close()
        except: pass
    return jobs

# ── WELLFOUND — startups ──────────────────────────────────────────────────────
def search_wellfound(ctx):
    jobs = []
    try:
        page = ctx.new_page()
        wf_data = []
        def on_resp(resp):
            if "wellfound.com" in resp.url:
                ct = resp.headers.get("content-type","")
                if "json" in ct:
                    try: wf_data.append(resp.json())
                    except: pass
        page.on("response", on_resp)
        for url in ["https://wellfound.com/jobs?roles[]=analyst&remote=true",
                    "https://wellfound.com/jobs?q=data+analyst&remote=true"]:
            page.goto(url, timeout=25000)
            page.wait_for_load_state("networkidle",timeout=15000); time.sleep(4)
        
        # Extrair vagas dos dados capturados
        for resp_data in wf_data:
            s = json.dumps(resp_data)
            if "jobListings" in s or "jobListing" in s:
                matches = re.findall(r'"title":"([^"]+)".*?"name":"([^"]+)".*?"jobUrl":"([^"]+)"', s)
                for title, co, url_path in matches:
                    if chk(title):
                        full_url = f"https://wellfound.com{url_path}" if not url_path.startswith("http") else url_path
                        jid = hashlib.md5(url_path.encode()).hexdigest()[:10]
                        jobs.append({"id":f"wf_{jid}","company":co,"role":title,
                            "url":full_url,"platform":"Wellfound","ats_type":"wellfound"})
        
        # Fallback: DOM
        if not jobs:
            html = page.content()
            for pat in [r'"title":"([^"]+)","startup":\{"name":"([^"]+)".*?"jobUrl":"([^"]+)"']:
                matches = re.findall(pat, html[:300000], re.DOTALL)
                for title, co, url_path in matches:
                    if chk(title):
                        full_url = url_path if url_path.startswith("http") else f"https://wellfound.com{url_path}"
                        jid = hashlib.md5(title.encode()).hexdigest()[:10]
                        jobs.append({"id":f"wf_{jid}","company":co,"role":title,
                            "url":full_url,"platform":"Wellfound","ats_type":"wellfound"})
        page.close()
    except Exception as e:
        print(f"  Wellfound: {str(e)[:50]}")
        try: page.close()
        except: pass
    seen = set(); unique=[]
    for j in jobs:
        if j["id"] not in seen: seen.add(j["id"]); unique.append(j)
    return unique

# ── MYJOBB.AI ─────────────────────────────────────────────────────────────────
def search_myjobb():
    jobs = []
    for q in ["power+bi+analyst","data+analyst+remote","analytics+engineer"]:
        try:
            url = f"https://myjobb.ai/api/jobs?q={q}&remote=true"
            req = urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=10) as r:
                data = json.loads(r.read())
            items = data if isinstance(data,list) else data.get("jobs",data.get("results",[]))
            for j in (items if isinstance(items,list) else []):
                title = j.get("title","") or j.get("position","")
                if not chk(title): continue
                co = j.get("company","?") or j.get("employer","?")
                if isinstance(co,dict): co = co.get("name","?")
                jid = j.get("id","") or hashlib.md5(title.encode()).hexdigest()[:10]
                jobs.append({"id":f"mj_{jid}","company":str(co),"role":title,
                    "url":j.get("url","https://myjobb.ai"),"platform":"MyJobb.ai","ats_type":"myjobb"})
            time.sleep(0.5)
        except: pass
    return jobs

# ── APPLY VIA JOBRIGHT/GLASSDOOR (extrair empresa → aplicar via GH/LV) ────────
def apply_extracted_job(page, job, cv_path):
    """Para vagas de Jobright/Glassdoor, navega para o apply_url e tenta aplicar"""
    apply_url = job.get("url","")
    if not apply_url: return "no_url"
    try:
        page.goto(apply_url, timeout=20000)
        page.wait_for_load_state("domcontentloaded",timeout=12000); time.sleep(3)
        final = page.url
        
        # Se redirecionou para Greenhouse
        if "greenhouse.io" in final or "boards.greenhouse.io" in final:
            for sel,val in [("input[name='first_name']","Rafael"),("input[name='last_name']","Rodrigues"),
                            ("input[name='email']",REPLY_TO),("input[name='phone']",PHONE)]:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=1000): el.fill(val)
                except: pass
            if cv_path and os.path.exists(cv_path):
                try:
                    fi = page.locator("input[type='file'][name='resume']").first
                    if fi.count(): fi.set_input_files(cv_path); time.sleep(1)
                except: pass
            for sel in ["input[type='submit']","button[type='submit']","button:has-text('Submit')"]:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=1000): el.click(force=True); time.sleep(3); return "success_gh"
                except: pass
        
        # Se ficou no site (Glassdoor/Jobright) — clicar Apply
        for sel in ["a:has-text('Apply Now')", "button:has-text('Apply')", "a:has-text('Apply')",
                    "[class*='apply']","[data-test='apply']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1500):
                    href = el.get_attribute("href") or ""
                    el.click(); time.sleep(3)
                    if "greenhouse.io" in page.url or "lever.co" in page.url:
                        return f"redirected_to_ats"
                    return "clicked_apply"
            except: pass
        
        return "opened_page"
    except PWTimeout: return "timeout"
    except Exception as e: return f"error:{str(e)[:30]}"

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n{'='*65}")
    print(f"  MULTI-SOURCE HUNTER v2 — {today}")
    print(f"  Glassdoor · Jobright · Simplify · Wellfound · MyJobb")
    print(f"{'='*65}\n")
    
    CV_PATH = ".github/assets/rafael_cv.pdf"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage",
                  "--disable-blink-features=AutomationControlled","--disable-gpu"]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width":1280,"height":800},locale="en-US"
        )
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        
        # Descoberta
        print("── DESCOBERTA ──────────────────────────────────────────────────")
        all_jobs = []
        
        print("  Glassdoor...",end=" ",flush=True)
        gd = search_glassdoor(ctx)
        print(f"{len(gd)} vagas")
        all_jobs.extend(gd)
        
        print("  Jobright.ai...",end=" ",flush=True)
        jr = search_jobright(ctx)
        print(f"{len(jr)} vagas")
        all_jobs.extend(jr)
        
        print("  Simplify.jobs...",end=" ",flush=True)
        sj = search_simplify(ctx)
        print(f"{len(sj)} vagas")
        all_jobs.extend(sj)
        
        print("  Wellfound...",end=" ",flush=True)
        wf = search_wellfound(ctx)
        print(f"{len(wf)} vagas")
        all_jobs.extend(wf)
        
        print("  MyJobb.ai...",end=" ",flush=True)
        mj = search_myjobb()
        print(f"{len(mj)} vagas")
        all_jobs.extend(mj)
        
        total = len(all_jobs)
        new_jobs = [j for j in all_jobs if not is_applied(j["id"])]
        print(f"\n  TOTAL: {total} | Novas: {len(new_jobs)}\n")
        
        # Aplicar
        print("── APLICANDO ───────────────────────────────────────────────────")
        applied = 0
        for i, job in enumerate(new_jobs[:40], 1):
            page = ctx.new_page()
            print(f"  [{i:2}/{min(len(new_jobs),40)}] [{job['platform'][:10]:10}] {job['company'][:20]:<22} {job['role'][:35]}", end=" ", flush=True)
            result = apply_extracted_job(page, job, CV_PATH)
            ok = any(k in result for k in ["success","clicked","redirect"])
            print(f"{'✅' if ok else '📨' if result=='opened_page' else '⚠️'} {result}")
            mark(job["id"],job["company"],job["role"],job["url"],job["platform"],
                 job["ats_type"],"success" if ok else result)
            if ok: applied += 1
            try: page.close()
            except: pass
            time.sleep(2)
        
        browser.close()
    
    print(f"\n{'='*65}")
    print(f"  ✅ {applied}/{len(new_jobs[:40])} candidaturas | {today}")
    print(f"{'='*65}\n")

if __name__ == "__main__":
    main()
