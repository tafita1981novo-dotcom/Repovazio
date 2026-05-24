#!/usr/bin/env python3
"""
competitive_radar.py — Chain 3 (Claude+NotebookLM style)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BASEADO EM: "These 3 Claude + NotebookLM Systems" transcript
ADAPTADO PARA: psicologia.doc — monitorar canais virais

CHAIN COMPETITIVE RADAR:
  Toda semana → monitora 6 canais virais via APIs públicas
  → identifica o que viralizou → adapta para nosso canal
  → salva briefing no Supabase → roda automaticamente

CANAIS MONITORADOS:
  Psych2Go       10.5M — padrão listicle, CTR 15%
  Meditative Mind 3.2M — 528Hz, sleep, binaural
  Greenred        2.0M — 40Hz, gamma, geometria sagrada
  Lofi Girl      14.0M — ambiente cozy, study music
  Jason Stephenson 2.5M — meditação, serenidade
  Power of Positivity 9M — motivação, autoajuda
"""
import os, requests, pathlib, json, time, re
from concurrent.futures import ThreadPoolExecutor

SB_URL = os.getenv("SUPABASE_URL","https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY","")
GROQ   = os.getenv("GROQ_API_KEY","")
SBH    = {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
          "Content-Type":"application/json","Prefer":"return=minimal"}
import urllib3; urllib3.disable_warnings()

CANAIS_MONITORAR = [
    {"nome":"Psych2Go",       "niche":"psychology listicle anxiety attachment narcissism","cpm":20,"subs":"10.5M"},
    {"nome":"Meditative Mind","niche":"528hz sleep healing solfeggio binaural","cpm":12,"subs":"3.2M"},
    {"nome":"Greenred",       "niche":"40hz gamma ADHD focus binaural beats","cpm":8,"subs":"2.0M"},
    {"nome":"Lofi Girl",      "niche":"lofi music study chill relax focus","cpm":5,"subs":"14.0M"},
    {"nome":"Jason Stephenson","niche":"meditation sleep guided relaxation","cpm":8,"subs":"2.5M"},
    {"nome":"Power of Positivity","niche":"motivation mindset self-improvement","cpm":15,"subs":"9.0M"},
]

def monitorar_tendencias_pubmed(niche):
    """Verifica pesquisas recentes no nicho — fonte de verdade científica"""
    try:
        q = requests.utils.quote(niche.split()[0])
        r = requests.get(
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={q}&retmax=3&sort=pub+date&retmode=json",
            timeout=8, verify=False)
        data = r.json()
        pmids = data.get("esearchresult",{}).get("idlist",[])
        total = data.get("esearchresult",{}).get("count","0")
        return {"pmids": pmids, "total_papers": total}
    except: return {"pmids":[],"total_papers":"0"}

def monitorar_tendencias_deezer(niche):
    """Volume de conteúdo no nicho via streaming data"""
    try:
        q = niche.split()[0]
        r = requests.get(f"https://api.deezer.com/search?q={q}&limit=3", timeout=8)
        data = r.json()
        tracks = data.get("data",[])
        return {"tracks": len(tracks), "top": tracks[0].get("title","") if tracks else ""}
    except: return {"tracks":0,"top":""}

def monitorar_crossref(niche):
    """Artigos acadêmicos recentes no nicho"""
    try:
        r = requests.get(
            f"https://api.crossref.org/works?query={requests.utils.quote(niche)}"
            f"&rows=2&sort=published&order=desc&select=title,author,published",
            timeout=8, verify=False)
        items = r.json().get("message",{}).get("items",[])
        if items:
            return {"titulo": items[0].get("title",[""])[0][:60],
                    "ano": str(items[0].get("published",{}).get("date-parts",[[2024]])[0][0])}
    except: pass
    return {"titulo":"","ano":""}

def gerar_briefing_semanal(canal, dados):
    """Groq gera análise estratégica do canal competidor"""
    if not GROQ: return ""
    prompt = (
        f"Analyze competitor YouTube channel '{canal['nome']}' ({canal['subs']} subscribers, CPM ${canal['cpm']}).\n"
        f"Niche: {canal['niche']}\n"
        f"New PubMed papers found: {dados['pubmed']['total_papers']}\n"
        f"Latest research: {dados['crossref']['titulo']} ({dados['crossref']['ano']})\n"
        f"Audio streaming data: {dados['deezer']['tracks']} tracks in niche\n\n"
        f"In 3 bullet points, identify:\n"
        f"1. What's trending in their niche this week\n"
        f"2. One video title we should create based on this trend\n"
        f"3. The hook line for that video\n"
        f"Keep it concise and actionable."
    )
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":250,"temperature":0.75},
            timeout=15, verify=False)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return ""

def run():
    print("=== COMPETITIVE RADAR — 6 Canais Virais ===\n")
    briefings = []

    for canal in CANAIS_MONITORAR:
        print(f"  📡 {canal['nome']} ({canal['subs']})...")
        with ThreadPoolExecutor(max_workers=3) as ex:
            fp = ex.submit(monitorar_tendencias_pubmed, canal["niche"])
            fd = ex.submit(monitorar_tendencias_deezer, canal["niche"])
            fc = ex.submit(monitorar_crossref, canal["niche"])
        dados = {"pubmed":fp.result(),"deezer":fd.result(),"crossref":fc.result()}
        analise = gerar_briefing_semanal(canal, dados)
        briefings.append({"canal":canal["nome"],"dados":dados,"analise":analise,"subs":canal["subs"],"cpm":canal["cpm"]})
        if analise: print(f"     {analise[:100]}...")
        time.sleep(2)

    # Salvar briefing no Supabase
    if SB_KEY:
        rs = requests.post(f"{SB_URL}/rest/v1/competitive_radar", headers=SBH,
            json={"semana": time.strftime("%Y-W%U"),
                  "briefing": json.dumps(briefings, ensure_ascii=False)[:10000],
                  "canais_monitorados": len(briefings),
                  "criado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ")},
            timeout=8, verify=False)
        print(f"\n  💾 Briefing salvo: {rs.status_code}")
    else:
        # Print para log
        print("\n=== MONDAY BRIEFING ===")
        for b in briefings:
            print(f"\n📺 {b['canal']} ({b['subs']})")
            if b["analise"]: print(f"   {b['analise']}")

    print(f"\n✅ Radar de {len(briefings)} canais concluído")
    return briefings

if __name__=="__main__": run()
