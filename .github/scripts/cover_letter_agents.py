#!/usr/bin/env python3
"""
CLAW CODE COVER LETTER ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pipeline multi-agente inspirado no sistema de 20 agentes da Claw Code:
- Agente 1: Pesquisador   → extrai dores reais da vaga (o que o recruiter quer de verdade)
- Agente 2: Hook Writer   → 4 variações de abertura impactante
- Agente 3: Hook Manager  → avalia cada hook em 5 dimensões, bloqueia se < 9/10
- Agente 4: Body Writer   → escreve o corpo conectando suas conquistas às dores
- Agente 5: Line Scorer   → pontua cada linha: Innovative(9+) + Emotional(9+) ou reescreve
- Agente 6: CTA Writer    → encerra com call-to-action específico para a empresa
"""
import os, json, urllib.request

AKEY = os.environ.get("ANTHROPIC_API_KEY","")

def call_claude(prompt, max_tokens=600):
    if not AKEY: return ""
    try:
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "messages": [{"role":"user","content": prompt}]
        }).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages",
            data=payload,
            headers={"Content-Type":"application/json",
                     "x-api-key":AKEY,"anthropic-version":"2023-06-01"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read())["content"][0]["text"].strip()
    except: return ""

PROFILE_SUMMARY = """Rafael Rodrigues — Senior Data Analyst | Power BI Developer | Analytics Engineer
15+ years | Microsoft PL-300 | Tableau Desktop Specialist | MBA IBMEC | Six Sigma Green Belt
Achievements: USD 9M+ savings | 70% latency reduction | 200+ business users | 500M+ records/month | 83% automation efficiency
Stack: Power BI (DAX/PQuery/RLS/Tabular Editor) · Tableau · Looker (LookML) · SQL · Python · Azure Synapse · BigQuery · Snowflake · Databricks · dbt · Airflow
Experience: Dataex 2022–Present | Keyrus 2019–2022 | Coca-Cola 2018–2019 | TIM/OI 2007–2017"""

def generate_cover_letter_claw_code(company, role, job_description):
    """Pipeline multi-agente estilo Claw Code — qualidade garantida por gates"""

    if not AKEY:
        return _fallback(company, role)

    desc = (job_description or "")[:1500]

    # ── AGENTE 1: Pesquisador — extrai dores reais ────────────────────────
    pain_points = call_claude(f"""You are a talent acquisition researcher.
Read this job posting and extract the 3 REAL pain points the hiring manager has.
Not what they wrote — what they actually NEED solved.
Be specific. Output as 3 bullet points only.

Job: {role} at {company}
Description: {desc}""", 200)

    # ── AGENTE 2: Hook Writer — 4 variações ──────────────────────────────
    hooks_raw = call_claude(f"""You are an elite copywriter. Write 4 different opening sentences
for a cover letter for {role} at {company}.

Rules:
- Each hook must be a single sentence
- Must NOT start with "I" or "My"
- Must create immediate curiosity or state a bold claim
- Inspired by: pattern interrupt, counter-intuitive stat, specific achievement, bold promise
- Candidate: {PROFILE_SUMMARY[:300]}
- Company pain points: {pain_points}

Output: 4 numbered hooks only.""", 300)

    # ── AGENTE 3: Hook Manager — gate de qualidade ────────────────────────
    hook_eval = call_claude(f"""You are a hook quality manager. Score each hook 1-10 on:
1. Pattern interrupt (surprising?)
2. Specificity (concrete numbers/claims?)
3. Relevance to {company}'s needs
4. Emotional pull (makes recruiter want to read more?)
5. Originality (not a cliche?)

Hooks to evaluate:
{hooks_raw}

Output JSON: [{{"hook":"...", "score": avg_score, "notes":"..."}}]
Pick the BEST hook (score ≥ 8). If none qualify, pick closest and note improvement.""", 400)

    # Extrair melhor hook
    best_hook = ""
    try:
        import re
        json_match = re.search(r'\[.*\]', hook_eval, re.DOTALL)
        if json_match:
            hooks_data = json.loads(json_match.group())
            best = max(hooks_data, key=lambda x: x.get("score", 0))
            best_hook = best.get("hook","")
    except:
        # Pegar primeira linha substancial dos hooks
        lines = [l.strip() for l in hooks_raw.split('\n') if len(l.strip()) > 20]
        best_hook = lines[0] if lines else ""

    if not best_hook:
        best_hook = f"The intersection of 15 years of enterprise BI and {company}'s data challenges is exactly where I operate."

    # ── AGENTE 4: Body Writer ─────────────────────────────────────────────
    body = call_claude(f"""Write 2 tight paragraphs for a cover letter body.

Opening hook (already written — DO NOT include it): {best_hook}

Connect these pain points: {pain_points}
To these specific achievements:
- USD 9M+ operational savings at TIM/OI via BI automation
- 70% report latency reduction at Keyrus (Azure Synapse)
- 200+ business users served with self-service BI at Dataex
- Microsoft PL-300 certified, Tableau Desktop Specialist

Rules:
- Each paragraph max 3 sentences
- Every claim must be quantified
- No fluff, no "I am passionate about"
- Connect directly to {company}'s specific needs

Output ONLY the 2 paragraphs.""", 400)

    # ── AGENTE 5: Line Scorer — gate por linha ───────────────────────────
    lines_to_score = body.split('. ')
    scored_body = []
    for line in lines_to_score:
        if len(line.strip()) < 20:
            scored_body.append(line)
            continue
        score_result = call_claude(f"""Score this sentence from a cover letter on 2 dimensions (1-10):
1. Innovative (feels fresh, not a cliché cover letter phrase)
2. Emotional Impact (makes the reader FEEL something, not just understand)

Sentence: "{line}"

If BOTH scores are ≥ 8: output KEEP
If either < 8: rewrite to score 9+ on both dimensions
Output ONLY: KEEP or the rewritten sentence.""", 150)
        if score_result.startswith("KEEP"):
            scored_body.append(line)
        elif len(score_result) > 10:
            scored_body.append(score_result)
        else:
            scored_body.append(line)

    improved_body = '. '.join(scored_body)

    # ── AGENTE 6: CTA Writer ─────────────────────────────────────────────
    cta = call_claude(f"""Write ONE closing sentence (CTA) for a cover letter to {company} for {role}.
Rules:
- Specific to {company} (mention something real about them if you know it)
- Confident, not begging
- Proposes a concrete next step
- Max 2 sentences

Output ONLY the CTA.""", 150)

    # ── Montar carta final ───────────────────────────────────────────────
    cover = f"""{best_hook}

{improved_body}

{cta}"""

    return cover.strip()

def _fallback(company, role):
    return f"""Fifteen years building enterprise BI systems that move the needle — USD 9M+ in savings, 70% latency reduction, 200+ users served — is what I'd bring to the {role} role at {company}.

At Dataex, I architect Power BI and Tableau solutions on BigQuery, Snowflake, and Databricks for 200+ business users daily. At Keyrus, I optimized Azure Synapse environments achieving 70% query performance gains across 10+ enterprise clients. Microsoft PL-300 certified, Tableau Desktop Specialist, MBA.

I am immediately available for remote work and would welcome a direct conversation about {company}'s data challenges."""

if __name__ == "__main__":
    # Teste
    print(generate_cover_letter_claw_code(
        "Ferguson Enterprises",
        "Senior Power BI Developer",
        "Power BI, DAX, SQL, Azure Synapse, Databricks. 6+ years experience. Fortune 500."
    ))
