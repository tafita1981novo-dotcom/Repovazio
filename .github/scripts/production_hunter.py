#!/usr/bin/env python3
"""
EMAIL HUNTER v3 — Apenas emails verificados, sem bounces
Rafael Rodrigues | +5522992418257
"""
import os,time,json,smtplib,hashlib,datetime,urllib.request,urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email             import encoders

GMAIL_USER   = "tafita81@gmail.com"
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASSWORD","")
REPLY_TO     = "Rafa_roberto2004@yahoo.com.br"
PHONE        = "+5522992418257"
LINKEDIN_URL = "https://linkedin.com/in/rafael-r-a3946a15"
CV_PATH      = ".github/assets/rafael_cv.pdf"
SUPA_URL     = os.environ.get("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SUPA_KEY     = os.environ.get("SUPABASE_ANON_KEY","")

# ── BLACKLIST DE BOUNCES CONFIRMADOS ─────────────────────────────────────────
BOUNCE_BLACKLIST = {
    "careers@elfbeauty.com","jobs@trilogyfederal.com","recruiting@preply.com",
    "recruiting@lexipol.com","people@rockencantech.com.br","jobs@imagineworldwide.org",
    "talent@moniepoint.com","analytics.talent@gxo.com","careers@ciklum.com",
    "jobs@smartworking.io","hello@stemma.ai","careers@selectstar.com",
    "jobs@greatexpectations.io","jobs@soda.io","careers@acceldata.io",
    "jobs@montecarlodata.com","jobs@evidentlyai.com","jobs@polar-analytics.com",
    "hello@littledata.io","careers@nearsource.com","careers@precisioneffect.com",
    "careers@pachyderm.com","jobs@smartworking.io",
}

# ── LISTA LIMPA — apenas emails sem bounce ───────────────────────────────────
EMAIL_TARGETS = [
    {"c":"Edvantis",           "r":"Senior Analytics Engineer",        "to":"recruiting@edvantis.com"},
    {"c":"Wire IT",            "r":"Power BI Developer",               "to":"info@wireit.pt"},
    {"c":"Data Meaning",       "r":"Power BI / BI Consultant",         "to":"info@datameaning.com"},
    {"c":"Proxify",            "r":"Senior Power BI Developer",        "to":"talent@proxify.io"},
    {"c":"Sorcero",            "r":"Senior Data Analyst",              "to":"careers@sorcero.com"},
    {"c":"Loenbro",            "r":"BI Engineer",                      "to":"hr@loenbro.com"},
    {"c":"Corsearch",          "r":"Senior Data Analyst",              "to":"careers@corsearch.com"},
    {"c":"Airalo",             "r":"Senior Data Analyst, Growth",      "to":"people@airalo.com"},
    {"c":"Keyrus Global",      "r":"Senior Power BI Consultant",       "to":"talent@keyrus.com"},
    {"c":"Alpha Omega",        "r":"Azure Power BI Developer",         "to":"careers@alphaomega.com"},
    {"c":"Exsilio Solutions",  "r":"Power BI Developer",               "to":"hr@exsilio.com"},
    {"c":"Upvanta",            "r":"Data Visualization Expert PBI",    "to":"rekrutacja@upvanta.com"},
    {"c":"Toptal",             "r":"Senior Data Analyst / Power BI",   "to":"talent@toptal.com"},
    {"c":"Andela",             "r":"Senior Analytics Engineer",        "to":"work@andela.com"},
    {"c":"Turing",             "r":"Senior Data Analyst Remote",       "to":"hire@turing.com"},
    {"c":"Arc.dev",            "r":"Senior Power BI Developer",        "to":"talent@arc.dev"},
    {"c":"Crossover",          "r":"Senior Data Analyst",              "to":"apply@crossover.com"},
    {"c":"Lemon.io",           "r":"Senior Power BI Developer",        "to":"hey@lemon.io"},
    {"c":"Gun.io",             "r":"Senior Data Analyst",              "to":"work@gun.io"},
    {"c":"Toggl",              "r":"Senior Analytics Engineer",        "to":"careers@toggl.com"},
    {"c":"X-Team",             "r":"Senior Data Analyst",              "to":"join@x-team.com"},
    {"c":"Pangian",            "r":"Senior Data Analyst Remote",       "to":"hello@pangian.com"},
    {"c":"Improvado",          "r":"Senior Data Analyst",              "to":"jobs@improvado.io"},
    {"c":"Funnel.io",          "r":"Senior BI Developer",              "to":"careers@funnel.io"},
    {"c":"Supermetrics",       "r":"Senior Analytics Engineer",        "to":"jobs@supermetrics.com"},
    {"c":"Adjust",             "r":"Senior Data Analyst",              "to":"jobs@adjust.com"},
    {"c":"AppsFlyer",          "r":"Senior Data Analyst",              "to":"careers@appsflyer.com"},
    {"c":"Triple Whale",       "r":"Data Analyst",                     "to":"careers@triplewhale.com"},
    {"c":"Northbeam",          "r":"Senior Data Analyst",              "to":"jobs@northbeam.io"},
    {"c":"Atlan",              "r":"Senior Data Analyst",              "to":"careers@atlan.com"},
    {"c":"WhyLabs",            "r":"Data Analyst",                     "to":"careers@whylabs.ai"},
    {"c":"Arize AI",           "r":"Senior Analytics Engineer",        "to":"jobs@arize.com"},
]

def supa_post(table, data):
    url = f"{SUPA_URL}/rest/v1/{table}"
    req = urllib.request.Request(url,data=json.dumps(data).encode(),method="POST",headers={
        "apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
        "Content-Type":"application/json","Prefer":"return=minimal"})
    try:
        with urllib.request.urlopen(req,timeout=10) as r: return r.status
    except: return 0

def is_sent(email, company):
    eid = hashlib.md5(f"{email}_{company}".encode()).hexdigest()[:12]
    url = f"{SUPA_URL}/rest/v1/job_applications?email=eq.{urllib.parse.quote(email)}&company=eq.{urllib.parse.quote(company)}&status=eq.sent&select=id"
    req = urllib.request.Request(url,headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}"})
    try:
        with urllib.request.urlopen(req,timeout=8) as r: return len(json.loads(r.read()))>0
    except: return False

def build_email(company, role, to_email):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Application: {role} — 15+ Yrs | PL-300 | {PHONE} | Available Immediately"
    msg["From"]    = f"Rafael Rodrigues <{GMAIL_USER}>"
    msg["To"]      = to_email
    msg["Reply-To"]= REPLY_TO
    
    plain = f"""Dear {company} Hiring Team,

I am applying for the {role} position at {company}.

Senior Data Analyst and Power BI Developer with 15+ years delivering enterprise BI, cloud analytics, and self-service data platforms.

CERTIFICATIONS: Microsoft PL-300 Power BI Data Analyst | Tableau Desktop Specialist | MBA IBMEC

KEY IMPACT:
• Power BI dashboards for 200+ business users | USD 9M+ operational savings
• 70% report latency reduction | 500M+ records/month processed
• BigQuery · Snowflake · Databricks · Azure Synapse · ADF

CORE STACK: Power BI · DAX · Power Query · SQL · Python · Tableau · Looker · BigQuery

EXPERIENCE:
• Dataex (2022–Present): Enterprise BI, Power BI + Tableau + Looker for 200+ users
• Keyrus (2019–2022): Senior BI Consultant, 10+ enterprise clients, Azure Synapse
• Coca-Cola (2018–2019): Senior Data Analyst, 30+ KPIs, BigQuery
• TIM/OI Telecom (2007–2017): 500M+ records/month, USD 9M+ savings

Available immediately for remote positions. CV attached.

Best regards,
Rafael Rodrigues
{PHONE} | {REPLY_TO}
LinkedIn: {LINKEDIN_URL}
"""
    msg.attach(MIMEText(plain, "plain"))
    
    # Anexar CV
    if os.path.exists(CV_PATH):
        with open(CV_PATH,"rb") as f:
            att = MIMEBase("application","octet-stream"); att.set_payload(f.read())
        encoders.encode_base64(att)
        att.add_header("Content-Disposition","attachment",filename="Rafael_Rodrigues_CV.pdf")
        msg.attach(att)
    
    return msg

def main():
    today = datetime.date.today().strftime("%d/%m/%Y")
    print(f"\n{'═'*60}")
    print(f"  EMAIL HUNTER v3 — {today}")
    print(f"  {len(EMAIL_TARGETS)} alvos verificados | Blacklist: {len(BOUNCE_BLACKLIST)}")
    print(f"{'═'*60}\n")
    
    if not GMAIL_PASS:
        print("❌ GMAIL_APP_PASSWORD não configurado"); return
    
    sent = 0; skipped = 0; errors = 0
    
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        print("✅ SMTP conectado\n")
    except Exception as e:
        print(f"❌ SMTP falhou: {e}"); return
    
    for t in EMAIL_TARGETS:
        company, role, to_email = t["c"], t["r"], t["to"]
        
        # Verificação dupla: blacklist + histórico
        if to_email.lower() in BOUNCE_BLACKLIST:
            print(f"  🚫 BLACKLIST: {to_email}")
            skipped += 1; continue
        
        if is_sent(to_email, company):
            skipped += 1; continue
        
        print(f"  📧 {company:<22} → {to_email:<38}", end=" ", flush=True)
        
        try:
            msg = build_email(company, role, to_email)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            supa_post("job_applications",{
                "company":company,"role":role,"url":"","email":to_email,
                "application_method":"email","status":"sent","platform":"email",
                "applied_at":now
            })
            print("✅ enviado")
            sent += 1; time.sleep(3)
        except Exception as e:
            print(f"❌ {str(e)[:40]}")
            errors += 1; time.sleep(1)
    
    server.quit()
    print(f"\n{'═'*60}")
    print(f"  ✅ {sent} emails | ⏭️  {skipped} já enviados | ❌ {errors} erros")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    main()
