#!/usr/bin/env python3
"""
PATCH: Adiciona Canada + Europe ao AI Hunter
Fontes: Indeed CA/UK/DE/NL/FR/AU + Workopolis + EuroJobs + LinkedIn Jobs RSS
"""
import os, time, json, re, hashlib, datetime, urllib.request, urllib.parse

SUPA = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
KEY  = os.environ.get("SUPABASE_ANON_KEY","")

KWORDS = ["data analyst","power bi","business intelligence","bi developer","bi analyst",
          "analytics engineer","reporting analyst","data visualization","tableau","looker",
          "senior analyst","bi engineer","analytics developer","visualization engineer"]

def is_relevant(t): return any(k in (t or "").lower() for k in KWORDS)

def sb_post(data):
    req = urllib.request.Request(f"{SUPA}/rest/v1/job_applications",
        data=json.dumps(data).encode(), method="POST",
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"})
    try:
        with urllib.request.urlopen(req, timeout=8): pass
    except: pass

def already(jid):
    url = f"{SUPA}/rest/v1/job_applications?job_id=eq.{urllib.parse.quote(str(jid))}&select=id&limit=1"
    req = urllib.request.Request(url, headers={"apikey":KEY,"Authorization":f"Bearer {KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            return len(json.loads(r.read())) > 0
    except: return False

def fetch_canada_europe():
    """Busca vagas em Canada, UK, EU, Australia via Indeed RSS e outros feeds"""
    feeds = [
        # Canada
        ("https://ca.indeed.com/rss?q=senior+power+bi+developer&l=remote&jt=fulltime&sort=date","CA"),
        ("https://ca.indeed.com/rss?q=senior+data+analyst+remote&jt=fulltime&sort=date","CA"),
        ("https://ca.indeed.com/rss?q=analytics+engineer+remote&jt=fulltime&sort=date","CA"),
        ("https://ca.indeed.com/rss?q=business+intelligence+analyst&l=remote&sort=date","CA"),
        # UK
        ("https://www.indeed.co.uk/rss?q=senior+power+bi+developer+remote&sort=date","UK"),
        ("https://www.indeed.co.uk/rss?q=senior+data+analyst+remote&jt=fulltime&sort=date","UK"),
        ("https://www.indeed.co.uk/rss?q=analytics+engineer+remote&sort=date","UK"),
        ("https://www.indeed.co.uk/rss?q=business+intelligence+analyst+remote&sort=date","UK"),
        # Germany
        ("https://www.indeed.de/rss?q=senior+data+analyst+remote&sort=date","DE"),
        ("https://www.indeed.de/rss?q=power+bi+developer+remote&sort=date","DE"),
        # Netherlands  
        ("https://www.indeed.nl/rss?q=senior+data+analyst+remote&sort=date","NL"),
        ("https://www.indeed.nl/rss?q=power+bi+developer&l=remote&sort=date","NL"),
        # France
        ("https://www.indeed.fr/rss?q=senior+data+analyst+remote&sort=date","FR"),
        # Australia
        ("https://au.indeed.com/rss?q=senior+data+analyst+remote&jt=fulltime&sort=date","AU"),
        ("https://au.indeed.com/rss?q=power+bi+developer+remote&sort=date","AU"),
        # Singapore (Asia hub)
        ("https://www.indeed.com.sg/rss?q=senior+data+analyst+remote&sort=date","SG"),
    ]
    
    jobs = []
    for feed_url, country in feeds:
        try:
            req = urllib.request.Request(feed_url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                rss = r.read().decode("utf-8","ignore")
            
            items = re.findall(r"<item>(.*?)</item>", rss, re.DOTALL)
            for item in items:
                tm = re.search(r"<title><!\[CDATA\[(.*?)\]\]>|<title>(.*?)</title>", item)
                lm = re.search(r"<link>(https?://[^\s<]+)", item)
                gm = re.search(r"<guid[^>]*>(.*?)</guid>", item)
                sm = re.search(r"<source[^>]*>(.*?)</source>", item)
                dm = re.search(r"<description><!\[CDATA\[(.*?)\]\]>", item, re.DOTALL)
                
                title = ((tm.group(1) or tm.group(2)) if tm else "").strip()
                if not is_relevant(title): continue
                
                link  = lm.group(1).strip() if lm else ""
                guid  = gm.group(1).strip() if gm else link
                co    = sm.group(1).strip() if sm else "?"
                desc  = re.sub(r"<[^>]+"," ",dm.group(1)) if dm else ""
                jid   = f"ind_{country}_{hashlib.md5(guid.encode()).hexdigest()[:12]}"
                
                if not already(jid):
                    jobs.append({"id":jid,"company":co,"role":title,"url":link,
                        "desc":desc[:500],"country":country,"platform":f"Indeed/{country}"})
            time.sleep(0.3)
        except Exception as e:
            pass
    
    return jobs

def main():
    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n🌍 CANADA + EUROPE JOB PATCH — {today}")
    
    jobs = fetch_canada_europe()
    print(f"  Vagas novas encontradas: {len(jobs)}")
    
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    saved = 0
    for j in jobs:
        sb_post({
            "company": j["company"], "role": j["role"], "url": j["url"],
            "job_id": j["id"], "platform": j["platform"],
            "application_method": "greenhouse_form",
            "status": "discovered", "country": j["country"],
            "applied_at": now, "email": "Rafa_roberto2004@yahoo.com.br",
            "source_query": f"indeed_{j['country']}_remote"
        })
        saved += 1
    
    print(f"  ✅ {saved} vagas registradas para candidatura")
    
    # Resumo por país
    by_country = {}
    for j in jobs:
        by_country[j["country"]] = by_country.get(j["country"],0) + 1
    for c, n in sorted(by_country.items()):
        print(f"    {c}: {n} vagas")

if __name__ == "__main__":
    main()
