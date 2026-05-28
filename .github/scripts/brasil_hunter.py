#!/usr/bin/env python3
"""
BRASIL HUNTER — Gupy + Indeed BR + LinkedIn BR
Monitora vagas data analytics no Brasil
Rafael Rodrigues | +5522992418257
"""
import os, time, json, re, hashlib, datetime, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

PHONE    = "+5522992418257"
REPLY_TO = "Rafa_roberto2004@yahoo.com.br"
SUPA_URL = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SUPA_KEY = os.environ.get("SUPABASE_ANON_KEY","")
CV_PATH  = ".github/assets/rafael_cv.pdf"

KEYWORDS = ["data analyst","power bi","business intelligence","analista de dados",
            "analista bi","analytics","bi developer","engenheiro de dados",
            "analista de bi","power bi developer","especialista bi"]
def chk(t): return any(k in (t or "").lower() for k in KEYWORDS)

def supa_post(table, data):
    url = f"{SUPA_URL}/rest/v1/{table}"
    req = urllib.request.Request(url,data=json.dumps(data).encode(),method="POST",headers={
        "apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
        "Content-Type":"application/json","Prefer":"return=minimal"})
    try:
        with urllib.request.urlopen(req,timeout=10) as r: return r.status
    except: return 0

def is_applied(eid):
    url = f"{SUPA_URL}/rest/v1/job_leads?external_id=eq.{urllib.parse.quote(str(eid))}&applied=eq.true&select=id"
    req = urllib.request.Request(url,headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}"})
    try:
        with urllib.request.urlopen(req,timeout=8) as r: return len(json.loads(r.read()))>0
    except: return False

def mark(eid, co, role, url, platform, method, status):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    supa_post("job_leads",{"external_id":str(eid),"company":co,"role":role,"url":url,
        "platform":platform,"applied":True,"applied_at":now,"ats_type":method})
    supa_post("job_applications",{"company":co,"role":role,"url":url,
        "application_method":method,"platform":platform,"status":status})

# ── GUPY BRASIL ───────────────────────────────────────────────────────────────
def search_gupy(ctx):
    jobs = []; seen = set()
    searches = ["data+analyst","power+bi","analista+de+dados",
                "analytics+engineer","bi+developer","analista+bi"]
    page = ctx.new_page()
    for term in searches:
        try:
            page.goto(f"https://portal.gupy.io/job-search/term={term.replace('+','%20')}",timeout=20000)
            page.wait_for_load_state("domcontentloaded",timeout=12000); time.sleep(3)
            html = page.content()
            # Extrair job URLs do Gupy
            job_urls = re.findall(r'https://[a-z0-9\-]+\.gupy\.io/job/[A-Za-z0-9=+/\-_]+', html)
            for job_url in job_urls[:30]:
                jid = hashlib.md5(job_url.encode()).hexdigest()[:12]
                if jid in seen: continue
                # Pegar título da URL ou do contexto
                slug_match = re.search(rf'"{re.escape(job_url)}"[^{{}}]*?"name"\s*:\s*"([^"]+)"', html[:5000000])
                title = slug_match.group(1) if slug_match else "Data Analyst"
                company_match = re.search(rf'"{re.escape(job_url)}"[^{{}}]*?"company"\s*:\s*\{{"name"\s*:\s*"([^"]+)"', html)
                co = company_match.group(1) if company_match else "Empresa BR"
                seen.add(jid)
                jobs.append({"id":f"gupy_{jid}","company":co,"role":title,
                    "url":job_url,"platform":"Gupy BR","ats_type":"gupy_br"})
        except Exception as e:
            print(f"  Gupy {term}: {str(e)[:40]}")
    # Também tentar API direta
    try:
        api_url = "https://job-search.gupy.io/api/job?jobName=data+analyst&limit=50"
        req = urllib.request.Request(api_url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=10) as r:
            data = json.loads(r.read())
        items = data if isinstance(data,list) else data.get("data",data.get("jobs",[]))
        for j in (items if isinstance(items,list) else []):
            title = j.get("name","") or j.get("title","")
            if not chk(title): continue
            co  = j.get("company",{}).get("name","?") if isinstance(j.get("company"),dict) else str(j.get("company","?"))
            jid = str(j.get("id","")) or hashlib.md5(title.encode()).hexdigest()[:10]
            url = j.get("jobUrl","") or j.get("shareUrl","") or f"https://portal.gupy.io/job/{jid}"
            if jid not in seen:
                seen.add(jid)
                jobs.append({"id":f"gupy_{jid}","company":co,"role":title,
                    "url":url,"platform":"Gupy BR","ats_type":"gupy_br"})
    except: pass
    page.close()
    return jobs

# ── APLICAR NO GUPY ───────────────────────────────────────────────────────────
def apply_gupy(page, job):
    try:
        page.goto(job["url"],timeout=20000)
        page.wait_for_load_state("domcontentloaded",timeout=12000); time.sleep(3)
        final = page.url

        # Procurar botão de candidatura
        for sel in ["button:has-text('Candidatar')","a:has-text('Candidatar')",
                    "button:has-text('Quero me candidatar')","[data-testid='apply-button']",
                    "button:has-text('Aplicar')","button[type='submit']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click(); time.sleep(3)
                    # Se redirecionar para login, pular
                    if "login" in page.url or "entrar" in page.url: return "requires_login"
                    return "clicked_apply_gupy"
            except: pass

        # Verificar se tem formulário de dados
        for sel in ["input[name='name']","input[placeholder*='nome']","input[type='email']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1000): return "form_visible"
            except: pass

        return "no_btn_gupy"
    except PWTimeout: return "timeout"
    except Exception as e: return f"error:{str(e)[:30]}"

# ── CATHO BRASIL ──────────────────────────────────────────────────────────────
def search_catho(ctx):
    jobs = []; seen = set()
    page = ctx.new_page()
    try:
        page.goto("https://www.catho.com.br/vagas/data-analyst/?remote=true",timeout=20000)
        page.wait_for_load_state("networkidle",timeout=15000); time.sleep(3)
        html = page.content()
        # Extrair vagas do JSON embutido
        matches = re.findall(r'"title"\s*:\s*"([^"]{5,80})".*?"company"\s*:\s*"([^"]+)".*?"id"\s*:\s*"?(\d+)"?', html[:500000], re.DOTALL)
        for title, co, jid in matches:
            if not chk(title) or jid in seen: continue
            seen.add(jid)
            jobs.append({"id":f"catho_{jid}","company":co,"role":title,
                "url":f"https://www.catho.com.br/vagas/{jid}/","platform":"Catho BR","ats_type":"catho_br"})
        # DOM fallback
        if not jobs:
            for el in page.locator("a[href*='/vagas/'], [class*='vacancy']").all()[:30]:
                try:
                    txt  = el.inner_text().strip()[:60]
                    href = el.get_attribute("href") or ""
                    if chk(txt) and href:
                        jid = hashlib.md5(txt.encode()).hexdigest()[:10]
                        jobs.append({"id":f"catho_{jid}","company":"?","role":txt,
                            "url":href if href.startswith("http") else f"https://www.catho.com.br{href}",
                            "platform":"Catho BR","ats_type":"catho_br"})
                except: pass
    except Exception as e:
        print(f"  Catho: {str(e)[:50]}")
    page.close()
    return jobs

# ── INFOJOBS BRASIL ───────────────────────────────────────────────────────────
def search_infojobs(ctx):
    jobs = []; seen = set()
    page = ctx.new_page()
    try:
        page.goto("https://www.infojobs.com.br/empregos-de-data-analyst.aspx?modalidadeTrab=home_office",timeout=20000)
        page.wait_for_load_state("domcontentloaded",timeout=12000); time.sleep(2)
        for sel in ["[class*='vacancy']","a[href*='/vaga/']","h2 a","h3 a"]:
            els = page.locator(sel).all()
            for el in els[:25]:
                try:
                    txt  = el.inner_text().strip()[:60]
                    href = el.get_attribute("href") or ""
                    if chk(txt) and href:
                        jid = hashlib.md5(txt.encode()).hexdigest()[:10]
                        if jid not in seen:
                            seen.add(jid)
                            jobs.append({"id":f"ij_{jid}","company":"?","role":txt,
                                "url":href if href.startswith("http") else f"https://www.infojobs.com.br{href}",
                                "platform":"InfoJobs BR","ats_type":"infojobs_br"})
                except: pass
            if jobs: break
    except Exception as e:
        print(f"  InfoJobs: {str(e)[:50]}")
    page.close()
    return jobs

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n{'='*60}")
    print(f"  BRASIL HUNTER — {today}")
    print(f"  Gupy · Catho · InfoJobs · Trampos")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
                  "--disable-blink-features=AutomationControlled"]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width":1280,"height":800}, locale="pt-BR"
        )
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        print("── DESCOBERTA ─────────────────────────────────────────────")
        print("  Gupy...",end=" ",flush=True)
        gupy = search_gupy(ctx); print(f"{len(gupy)} vagas")

        print("  Catho...",end=" ",flush=True)
        catho = search_catho(ctx); print(f"{len(catho)} vagas")

        print("  InfoJobs...",end=" ",flush=True)
        ij = search_infojobs(ctx); print(f"{len(ij)} vagas")

        all_jobs = gupy + catho + ij
        new_jobs = [j for j in all_jobs if not is_applied(j["id"])]
        print(f"\n  TOTAL: {len(all_jobs)} | Novas: {len(new_jobs)}\n")

        print("── CANDIDATANDO ───────────────────────────────────────────")
        applied = 0
        for i, job in enumerate(new_jobs[:30], 1):
            page = ctx.new_page()
            print(f"  [{i:2}/{min(len(new_jobs),30)}] [{job['platform'][:10]:10}] {job['company'][:20]:<22} {job['role'][:35]}", end=" ", flush=True)
            result = apply_gupy(page, job) if "gupy" in job["ats_type"] else "opened_page"
            ok = any(k in result for k in ["success","clicked","redirect","form"])
            print(f"{'✅' if ok else '⚠️'} {result}")
            mark(job["id"],job["company"],job["role"],job["url"],
                 job["platform"],job["ats_type"],"success" if ok else result)
            if ok: applied += 1
            try: page.close()
            except: pass
            time.sleep(2)

        browser.close()

    print(f"\n{'='*60}")
    print(f"  ✅ {applied} candidaturas Brasil | {today}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
