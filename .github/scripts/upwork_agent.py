#!/usr/bin/env python3
"""
UPWORK AUTONOMOUS AGENT — Rafael Rodrigues
Busca jobs, gera propostas com IA, submete automaticamente
Profile: https://www.upwork.com/freelancers/~01024e421f4dda8440
"""
import os, time, json, datetime, hashlib, re, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

PHONE        = "+5522992418257"
REPLY_TO     = "Rafa_roberto2004@yahoo.com.br"
GMAIL        = "tafita81@gmail.com"
APP_PASS     = os.environ.get("GMAIL_APP_PASSWORD","")
UPWORK_USER  = os.environ.get("UPWORK_EMAIL","")
UPWORK_PASS  = os.environ.get("UPWORK_PASSWORD","")
SUPA_URL     = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SUPA_KEY     = os.environ.get("SUPABASE_ANON_KEY","")
PROFILE_URL  = "https://www.upwork.com/freelancers/~01024e421f4dda8440"
COOKIES_FILE  = ".github/upwork_cookies.json"
UPWORK_COOKIES_B64 = os.environ.get("UPWORK_COOKIES","")  # cookies base64 como secret

# ─── Perfil completo para geração de propostas ───────────────────────────────
RAFAEL_BIO = """
Name: Rafael Rodrigues
Title: Senior Data Analyst & Power BI Developer
Experience: 15+ years enterprise BI and analytics
Phone: +5522992418257
Email: Rafa_roberto2004@yahoo.com.br
LinkedIn: linkedin.com/in/rafael-r-a3946a15

Core expertise:
- Power BI (DAX, Power Query, RLS, Dataflows, Incremental Refresh)
- Tableau, Looker, SQL (advanced), Python
- BigQuery, Snowflake, Databricks SQL, Azure Synapse, Amazon Athena
- Dimensional Modeling, Star Schema, ETL/ELT, Data Governance
- Certifications: Microsoft PL-300, Tableau Desktop Specialist, MBA IBMEC

Career highlights:
- $9M+ operational savings at TIM/OI Telecommunications (500M+ records/month)
- 70% report latency reduction via DAX/SQL optimization at Keyrus
- Analytics platforms for 200+ business users
- Delivered enterprise BI for Financial Services, Retail, Telecom, Insurance
- Keyrus (global BI consultancy), Coca-Cola (BigQuery), TIM/OI, Dataex

Availability: Immediately | Remote only | US/EU timezone compatible
Rate: $55-80/hour (negotiable based on project)
"""

KEYWORDS = ["power bi","data analyst","business intelligence","bi developer",
            "analytics engineer","bi analyst","reporting analyst","tableau",
            "data visualization","sql analyst","looker","dax","power query"]

# ─── Supabase ─────────────────────────────────────────────────────────────────
def supa_get(table, params=""):
    url = f"{SUPA_URL}/rest/v1/{table}?{params}"
    req = urllib.request.Request(url, headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except: return []

def supa_post(table, data):
    url  = f"{SUPA_URL}/rest/v1/{table}"
    body = json.dumps(data).encode()
    req  = urllib.request.Request(url, data=body, method="POST",headers={
        "apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
        "Content-Type":"application/json","Prefer":"return=minimal"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r: return r.status
    except: return 0

def is_proposed(job_id):
    rows = supa_get("job_leads", f"external_id=eq.{urllib.parse.quote(f'uw_{job_id}')}&applied=eq.true&select=id")
    return isinstance(rows,list) and len(rows)>0

def mark_proposed(job_id, title, client, url, status, proposal_preview):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    supa_post("job_leads", {
        "external_id": f"uw_{job_id}",
        "company": client, "role": title,
        "url": url, "platform": "Upwork",
        "applied": True, "applied_at": now, "ats_type": "upwork"
    })
    supa_post("job_applications", {
        "company": client, "role": title, "url": url,
        "application_method": "upwork_proposal", "platform": "Upwork",
        "status": status, "notes": proposal_preview[:200]
    })

# ─── Geração de proposta com IA (Anthropic API) ───────────────────────────────
def generate_proposal(job_title, job_description, client_name, budget):
    """Gera proposta personalizada usando Claude"""
    try:
        import urllib.request, json
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 800,
            "messages": [{
                "role": "user",
                "content": f"""You are Rafael Rodrigues, a Senior Data Analyst with 15+ years of experience.
Write a concise, compelling Upwork proposal for this job. Be specific, professional, and results-oriented.
Start with a hook that shows you read the job description. Mention 1-2 specific relevant achievements.
End with a clear call to action. Maximum 250 words. Write in first person.

Freelancer profile:
{RAFAEL_BIO}

Job Title: {job_title}
Client: {client_name}
Budget: {budget}
Job Description:
{job_description[:800]}

Write ONLY the proposal text, no headers or labels."""
            }]
        }
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
            return resp["content"][0]["text"]
    except Exception as e:
        # Fallback: proposta template
        return f"""Hi,

I noticed you need help with {job_title} — this is exactly where I specialize.

With 15+ years in enterprise BI (Power BI, SQL, BigQuery, Snowflake), I've delivered measurable results: $9M+ in operational savings, 70% report latency reduction, and analytics platforms for 200+ users at companies like Coca-Cola, Keyrus, and TIM/OI Telecommunications.

For your project, I'd bring:
✅ Deep Power BI expertise (DAX, Power Query, RLS, Dataflows) — Microsoft PL-300 certified
✅ End-to-end delivery: from data modeling to executive dashboard
✅ Clear communication and timely delivery

I'm available to start immediately and would love to discuss your specific needs.

Best,
Rafael Rodrigues | Senior Data Analyst | PL-300 Certified
Phone/WhatsApp: {PHONE}"""

# ─── Login e navegação no Upwork ─────────────────────────────────────────────
def login_upwork(ctx, email, password):
    """Faz login no Upwork e retorna cookies"""
    page = ctx.new_page()
    try:
        print("  Abrindo página de login...")
        page.goto("https://www.upwork.com/ab/account-security/login", timeout=25000)
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(3)

        # Verificar se está logado
        if "feed" in page.url or "find-work" in page.url:
            print("  ✅ Já logado!")
            cookies = ctx.cookies()
            page.close()
            return cookies, True

        # Preencher email
        for sel in ["input[name='login[username]']","input[type='email']","#login_username","input[name='username']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.fill(email); print(f"  Email preenchido ({sel})")
                    break
            except: pass

        # Clicar Continue
        for sel in ["button[type='submit']","#login_password_continue","button:has-text('Continue')"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click(); time.sleep(2); break
            except: pass

        # Preencher password
        for sel in ["input[name='login[password]']","input[type='password']","#login_password"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.fill(password); print("  Senha preenchida")
                    break
            except: pass

        # Submit
        for sel in ["button[type='submit']","#login_control_continue","button:has-text('Log In')"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click(); time.sleep(5); break
            except: pass

        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(3)

        current = page.url
        print(f"  URL após login: {current[:60]}")
        success = "feed" in current or "find-work" in current or "my-jobs" in current
        cookies = ctx.cookies()
        page.close()
        return cookies, success
    except Exception as e:
        print(f"  Login erro: {e}")
        try: page.close()
        except: pass
        return [], False

def search_jobs_upwork(page):
    """Busca jobs relevantes no Upwork"""
    jobs = []
    search_terms = [
        "power bi data analyst",
        "business intelligence developer",
        "analytics engineer power bi",
        "sql data analyst remote",
        "tableau power bi developer",
    ]
    for term in search_terms[:3]:
        try:
            encoded = urllib.parse.quote(term)
            url = f"https://www.upwork.com/nx/search/jobs/?q={encoded}&remote_job_filter=ONLY_REMOTE&sort=recency&hourly_rate=30-"
            page.goto(url, timeout=20000)
            page.wait_for_load_state("domcontentloaded", timeout=12000)
            time.sleep(3)

            # Extrair jobs do DOM
            job_tiles = page.locator("article[data-test='job-tile']").all()
            if not job_tiles:
                job_tiles = page.locator("[class*='job-tile'], [data-ev-sublocation='job_title']").all()

            for tile in job_tiles[:10]:
                try:
                    # Título
                    title_el = tile.locator("h2, h3, [class*='title'], [data-test='job-title']").first
                    title = title_el.inner_text().strip() if title_el.count() else ""
                    if not title or not any(k in title.lower() for k in KEYWORDS): continue

                    # Link
                    link_el = tile.locator("a[href*='/jobs/']").first
                    href = link_el.get_attribute("href") if link_el.count() else ""
                    if href and not href.startswith("http"):
                        href = f"https://www.upwork.com{href}"

                    # Job ID
                    jid = re.search(r'~(\w+)', href or "")
                    jid = jid.group(1) if jid else hashlib.md5(title.encode()).hexdigest()[:12]

                    # Budget/rate
                    budget = ""
                    for bsel in ["[data-test='budget']","[class*='budget']","[class*='price']"]:
                        try:
                            b = tile.locator(bsel).first
                            if b.count(): budget = b.inner_text().strip()[:30]; break
                        except: pass

                    # Cliente
                    client = "Upwork Client"
                    for csel in ["[data-test='client-name']","[class*='client']"]:
                        try:
                            c = tile.locator(csel).first
                            if c.count(): client = c.inner_text().strip()[:30]; break
                        except: pass

                    jobs.append({
                        "id": jid, "title": title, "url": href,
                        "budget": budget, "client": client,
                        "description": ""  # será carregada depois
                    })
                except: pass
            time.sleep(2)
        except Exception as e:
            print(f"  Busca '{term}': {str(e)[:40]}")

    # Deduplicar
    seen = set()
    unique = [j for j in jobs if j["id"] not in seen and not seen.add(j["id"])]
    return unique

def get_job_description(page, job_url):
    """Carrega a descrição completa do job"""
    try:
        page.goto(job_url, timeout=20000)
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(2)
        for sel in ["[data-test='Description']","[class*='description']","#job-description","section.description"]:
            try:
                el = page.locator(sel).first
                if el.count():
                    return el.inner_text().strip()[:1500]
            except: pass
        # Fallback: pegar texto da página
        return page.inner_text("main")[:800] if page.locator("main").count() else ""
    except:
        return ""

def submit_proposal(page, job, proposal_text, hourly_rate="65"):
    """Submete proposta no Upwork"""
    try:
        # Navegar para o job
        page.goto(job["url"], timeout=20000)
        page.wait_for_load_state("domcontentloaded", timeout=12000)
        time.sleep(2)

        # Encontrar botão Apply
        clicked = False
        for sel in [
            "button:has-text('Apply Now')",
            "a:has-text('Apply Now')",
            "button:has-text('Submit a Proposal')",
            "[data-qa='btn-apply']",
            "button.up-btn:has-text('Apply')",
        ]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click(); time.sleep(3)
                    clicked = True; break
            except: pass

        if not clicked: return "no_apply_btn"

        # Preencher cover letter / proposal
        for sel in [
            "textarea[placeholder*='proposal']",
            "textarea[placeholder*='cover']",
            "textarea[name*='proposal']",
            "[data-test='cover-letter']",
            "textarea",
        ]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.fill(proposal_text[:3000])
                    print(f"    Proposta preenchida ({len(proposal_text)} chars)")
                    break
            except: pass

        # Preencher rate (se houver campo)
        for sel in ["input[name*='rate']","input[placeholder*='rate']","input[placeholder*'$/hr']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1000):
                    el.fill(hourly_rate); break
            except: pass

        # Submit
        time.sleep(1)
        for sel in [
            "button:has-text('Submit Proposal')",
            "button:has-text('Submit')",
            "button[type='submit']",
            "[data-qa='btn-submit-proposal']",
        ]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click(force=True); time.sleep(4)
                    print(f"    ✅ Proposta submetida!")
                    return "success"
            except: pass

        return "submit_btn_not_found"
    except Exception as e:
        return f"error:{str(e)[:50]}"

# ─── Relatório por email ──────────────────────────────────────────────────────
def send_report(proposals):
    if not APP_PASS: return
    rows = ""
    for p in proposals:
        icon = "✅" if p["status"]=="success" else "⚠️"
        rows += f"<tr style='border-bottom:1px solid #E5E7EB;'><td style='padding:8px;'>{icon}</td><td style='padding:8px;font-weight:600;color:#1F3864;'>{p['client'][:25]}</td><td style='padding:8px;font-size:12px;color:#374151;'>{p['title'][:45]}</td><td style='padding:8px;font-size:11px;color:#059669;'>{p['budget'][:20]}</td><td style='padding:8px;font-size:11px;'>{p['status']}</td></tr>"

    ok = sum(1 for p in proposals if p["status"]=="success")
    html = f"""<html><body style="font-family:Arial;max-width:720px;margin:0 auto;">
<div style="background:linear-gradient(135deg,#1F3864,#14a800);padding:22px;border-radius:8px 8px 0 0;">
<div style="color:rgba(255,255,255,.8);font-size:10px;letter-spacing:3px;text-transform:uppercase;">Upwork Autonomous Agent</div>
<div style="color:#fff;font-size:22px;font-weight:800;margin-top:6px;">🎯 {ok}/{len(proposals)} Propostas Submetidas</div>
<div style="color:rgba(255,255,255,.7);">Rafael Rodrigues · {PHONE} · {datetime.date.today().strftime('%d/%m/%Y')}</div>
</div>
<div style="background:#fff;padding:20px;border:1px solid #E5E7EB;border-top:none;border-radius:0 0 8px 8px;">
<table style="width:100%;border-collapse:collapse;">
<tr style="background:#F8FAFC;border-bottom:2px solid #E5E7EB;">
<th style="padding:8px;font-size:11px;color:#6B7280;text-align:left;text-transform:uppercase;"></th>
<th style="padding:8px;font-size:11px;color:#6B7280;text-align:left;text-transform:uppercase;">Cliente</th>
<th style="padding:8px;font-size:11px;color:#6B7280;text-align:left;text-transform:uppercase;">Vaga</th>
<th style="padding:8px;font-size:11px;color:#6B7280;text-align:left;text-transform:uppercase;">Budget</th>
<th style="padding:8px;font-size:11px;color:#6B7280;text-align:left;text-transform:uppercase;">Status</th>
</tr>{rows}
</table>
<div style="margin-top:16px;padding:12px;background:#F0FDF4;border-radius:8px;font-size:12px;color:#065F46;">
✅ Agente 24/7 ativo · Roda a cada 3h · Propostas geradas por IA Claude<br>
📞 {PHONE} · 🔗 upwork.com/freelancers/~01024e421f4dda8440
</div></div></body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = f"Upwork Agent <{GMAIL}>"
        msg["To"]      = GMAIL
        msg["Subject"] = f"🎯 Upwork [{datetime.date.today().strftime('%d/%m')}] — {ok}/{len(proposals)} propostas"
        msg.attach(MIMEText(html,"html"))
        s = smtplib.SMTP("smtp.gmail.com",587); s.ehlo(); s.starttls()
        s.login(GMAIL,APP_PASS); s.sendmail(GMAIL,[GMAIL],msg.as_string()); s.quit()
        print(f"\n✅ Relatório enviado para {GMAIL}")
    except Exception as e:
        print(f"Relatório: {e}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    today = datetime.date.today().strftime("%d/%m/%Y %H:%M")
    print(f"\n{'='*65}")
    print(f"  UPWORK AUTONOMOUS AGENT — {today}")
    print(f"  Profile: ~01024e421f4dda8440")
    print(f"{'='*65}\n")

    if not UPWORK_USER or not UPWORK_PASS:
        print("❌ UPWORK_EMAIL e UPWORK_PASSWORD não configurados.")
        print("   Adicione como GitHub Secrets: UPWORK_EMAIL e UPWORK_PASSWORD")
        return

    print(f"  Email: {UPWORK_USER}")
    proposals = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
                "--disable-blink-features=AutomationControlled",
                "--window-size=1280,800",
            ]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width":1280,"height":800},
            locale="en-US",
            timezone_id="America/Sao_Paulo",
        )
        ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en','pt-BR']});
            window.chrome = {runtime: {}};
        """)

        # Carregar cookies do GitHub Secret (prioridade)
        if UPWORK_COOKIES_B64 and not cookies_loaded:
            try:
                import base64 as _b64
                cookies_data = json.loads(_b64.b64decode(UPWORK_COOKIES_B64).decode())
                ctx.add_cookies(cookies_data)
                cookies_loaded = True
                print("✅ Cookies carregados do GitHub Secret\n")
            except Exception as e:
                print(f"⚠️ Cookies do secret: {e}")

        # Carregar cookies salvos (se existir)
        cookies_loaded = False
        if os.path.exists(COOKIES_FILE):
            try:
                with open(COOKIES_FILE) as f:
                    ctx.add_cookies(json.load(f))
                cookies_loaded = True
                print("✅ Cookies carregados\n")
            except: pass

        # Login
        print("── LOGIN ────────────────────────────────────────────────────")
        cookies, login_ok = login_upwork(ctx, UPWORK_USER, UPWORK_PASS)
        if not login_ok and not cookies_loaded:
            print("❌ Login falhou. Verifique credenciais.")
            browser.close(); return
        
        # Salvar cookies
        if cookies:
            try:
                os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
                with open(COOKIES_FILE,"w") as f:
                    json.dump(cookies, f)
                print("✅ Cookies salvos\n")
            except: pass

        # Buscar vagas
        print("── BUSCANDO VAGAS ────────────────────────────────────────────")
        search_page = ctx.new_page()
        jobs = search_jobs_upwork(search_page)
        new_jobs = [j for j in jobs if not is_proposed(j["id"])]
        print(f"  Total encontradas: {len(jobs)} | Novas: {len(new_jobs)}\n")
        search_page.close()

        if not new_jobs:
            print("✅ Nenhuma vaga nova — tudo já proposto!")
            browser.close(); return

        # Processar cada vaga
        print("── GERANDO E SUBMETENDO PROPOSTAS ───────────────────────────")
        for i, job in enumerate(new_jobs[:15], 1):
            work_page = ctx.new_page()
            print(f"\n  [{i:2}/{min(len(new_jobs),15)}] {job['client'][:20]:<22} {job['title'][:40]}")

            # Carregar descrição
            desc = ""
            if job.get("url"):
                desc = get_job_description(work_page, job["url"])
                if desc: print(f"    Descrição: {len(desc)} chars")

            # Gerar proposta com IA
            print("    Gerando proposta com IA...", end=" ", flush=True)
            proposal = generate_proposal(
                job["title"], desc or "Data Analyst / Power BI Developer role",
                job["client"], job.get("budget","")
            )
            print(f"✅ {len(proposal)} chars")

            # Submeter
            print(f"    Submetendo proposta...", end=" ", flush=True)
            result = submit_proposal(work_page, job, proposal)
            print(f"{'✅' if result=='success' else '⚠️'} {result}")

            # Registrar
            mark_proposed(
                job["id"], job["title"], job["client"],
                job.get("url",""), result, proposal[:200]
            )
            proposals.append({
                "client":  job["client"],
                "title":   job["title"],
                "budget":  job.get("budget",""),
                "status":  result,
                "proposal": proposal[:100]
            })
            work_page.close()
            time.sleep(3)  # Evitar rate limit

        browser.close()

    # Relatório
    ok = sum(1 for p in proposals if p["status"]=="success")
    print(f"\n{'='*65}")
    print(f"  ✅ {ok}/{len(proposals)} propostas submetidas")
    print(f"{'='*65}")
    if proposals: send_report(proposals)

if __name__ == "__main__":
    main()
