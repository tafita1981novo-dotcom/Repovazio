#!/usr/bin/env python3
"""Wellfound (AngelList) — busca startups + aplica com cookies"""
import os, sys, json, time, datetime, urllib.request, urllib.parse, re

sys.path.insert(0, os.path.dirname(__file__))
from session_manager import load_session, save_session, stealth_context, sb_upsert, sb_get

SUPA = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
KEY  = os.environ.get("SUPABASE_ANON_KEY","")

PROFILE = {
    "first":"Rafael","last":"Rodrigues",
    "email":"Rafa_roberto2004@yahoo.com.br",
    "phone":"+5522992418257",
    "cv":".github/assets/rafael_cv.pdf",
    "bio":"Senior Data Analyst with 15+ years. PL-300, Tableau. USD 9M+ savings. Power BI, SQL, Python, Azure, BigQuery."
}

def already_applied(jid):
    r = sb_get(f"job_applications?job_id=eq.{urllib.parse.quote(str(jid))}&select=id&limit=1")
    return isinstance(r,list) and len(r)>0

def save(co, role, url, jid, status):
    sb_upsert("job_applications",{
        "company":co,"role":role,"url":url,"job_id":f"wf_{jid}",
        "application_method":"wellfound_apply","status":status,
        "platform":"Wellfound","applied_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "email":PROFILE["email"],"country":"US"
    })

def search_wellfound_api(session_data, role_slug="data-analyst", limit=20):
    """Busca vagas via API GraphQL do Wellfound"""
    if not session_data: return []
    cookies_str = "; ".join([f"{c['name']}={c['value']}" for c in session_data.get("cookies",[])])
    query = """
    query JobSearchResults($query:String,$remote:Boolean,$jobTypes:[String],$page:Int){
      startupSearchResults(query:$query,jobTypes:$jobTypes,remote:$remote,page:$page){
        startups{id name slug jobs(jobTypes:$jobTypes){id title url easyApply}}
      }
    }"""
    try:
        payload = json.dumps({"query":query,"variables":{
            "query":"data analyst power bi","remote":True,
            "jobTypes":["full_time"],"page":1
        }}).encode()
        req = urllib.request.Request(
            "https://wellfound.com/graphql",
            data=payload, method="POST",
            headers={"Content-Type":"application/json","Cookie":cookies_str,
                     "User-Agent":"Mozilla/5.0","Referer":"https://wellfound.com/jobs"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        jobs = []
        for startup in data.get("data",{}).get("startupSearchResults",{}).get("startups",[]):
            for j in startup.get("jobs",[]):
                if j.get("easyApply"):
                    jobs.append({"id":j["id"],"title":j["title"],"company":startup["name"],"url":j.get("url","")})
        return jobs[:limit]
    except: return []

def apply_wellfound(ctx, job):
    pg = ctx.new_page()
    try:
        url = job["url"] or f"https://wellfound.com/jobs/{job['id']}"
        pg.goto(url, timeout=20000)
        pg.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(2)
        for sel in ["button:has-text('Apply')","a:has-text('Apply')",".apply-button","[class*='apply']"]:
            try:
                el = pg.locator(sel).first
                if el.is_visible(timeout=1000): el.click(); time.sleep(2); break
            except: pass
        filled = 0
        for sel, val in [
            ("textarea[name*='cover']","Senior DA 15yr, PL-300, 9M+ savings. Would love to join."),
            ("input[name='phone']", PROFILE["phone"]),
        ]:
            try:
                el = pg.locator(sel).first
                if el.is_visible(timeout=400): el.fill(val); filled += 1
            except: pass
        if os.path.exists(PROFILE["cv"]):
            try:
                el = pg.locator("input[type='file']").first
                if el.count(): el.set_input_files(PROFILE["cv"]); time.sleep(2); filled += 1
            except: pass
        for sel in ["button:has-text('Submit')","button[type='submit']"]:
            try:
                el = pg.locator(sel).first
                if el.is_visible(timeout=1000):
                    el.click(); time.sleep(4)
                    pg.close(); return "success"
            except: pass
        pg.close(); return f"partial_{filled}"
    except Exception as e:
        try: pg.close()
        except: pass
        return f"err:{str(e)[:25]}"

def main():
    from playwright.sync_api import sync_playwright
    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n{'━'*58}")
    print(f"  🚀 WELLFOUND APPLY — {today}")
    print(f"{'━'*58}\n")
    session = load_session("wellfound")
    if not session:
        print("  Tentando login Wellfound automático...")
        with sync_playwright() as p:
            br, ctx = stealth_context(p)
            from session_manager import try_login_wellfound
            cookies = try_login_wellfound(ctx)
            if cookies:
                save_session("wellfound", cookies)
                session = {"cookies": cookies}
                print(f"  ✅ Login OK — {len(cookies)} cookies")
            br.close()
    if not session:
        print("  ⚠️  Wellfound sem sessão")
        return
    jobs = search_wellfound_api(session, limit=20)
    new_jobs = [j for j in jobs if not already_applied(j["id"])]
    print(f"  Vagas: {len(jobs)} | Novas: {len(new_jobs)}\n")
    ok = err = 0
    with sync_playwright() as p:
        br, ctx = stealth_context(p)
        for c in session.get("cookies",[]): 
            try: ctx.add_cookies([c])
            except: pass
        for job in new_jobs[:10]:
            co = job["company"][:22]
            role = job["title"][:38]
            print(f"  {co:<24} {role:<38}", end=" ", flush=True)
            res = apply_wellfound(ctx, job)
            icon = "✅" if "success" in res else "⚠️"
            print(f"{icon} {res}")
            save(job["company"], job["title"], job["url"], job["id"], res)
            if "success" in res: ok += 1
            else: err += 1
            time.sleep(2)
        br.close()
    print(f"\n  ✅ {ok} | ⚠️ {err}")

if __name__ == "__main__":
    main()
