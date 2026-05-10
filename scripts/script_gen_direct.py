#!/usr/bin/env python3
"""Gera scripts cinematograficos direto via Groq sem Edge Functions.
UA-aware: Supabase usa python-client, Groq usa openai-python.
"""
import os, json, urllib.request, urllib.error

SBU = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
GROQ = os.environ["GROQ_API_KEY"]

UA_SUPABASE = "supabase-py/2.0 (script-gen-direct)"
UA_GROQ = "openai-python/1.51.0"

def http(url, method="GET", body=None, headers=None, timeout=180, ua=None):
    h = dict(headers or {})
    h["User-Agent"] = ua or "python-urllib/3.11"
    h.setdefault("Accept", "application/json")
    data = None
    if body:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode() if e.fp else str(e))
    except Exception as e:
        return 0, str(e)

def sb(url, method="GET", body=None):
    return http(url, method, body,
                headers={"apikey": SBK, "Authorization": f"Bearer {SBK}"},
                ua=UA_SUPABASE)

def groq_generate(system, user, max_tokens=8000):
    s, body = http("https://api.groq.com/openai/v1/chat/completions", "POST",
        body={"model":"llama-3.3-70b-versatile",
              "messages":[{"role":"system","content":system},{"role":"user","content":user}],
              "max_tokens": max_tokens, "temperature": 0.7},
        headers={"Authorization": f"Bearer {GROQ}"},
        ua=UA_GROQ)
    if s == 200:
        return json.loads(body)["choices"][0]["message"]["content"]
    print(f"[groq] err {s}: {body[:300]}")
    return None

def main():
    s, raw = sb(f"{SBU}/rest/v1/content_pipeline?status=eq.pending_generation&metadata->>eternal_brain_decision=eq.CINEMATIC_RESET_2026-05-10&order=id.desc&limit=3&select=id,title,target_platform,metadata")
    if s != 200:
        print(f"[err] supabase {s}: {raw[:300]}"); return
    pipes = json.loads(raw)
    print(f"[gen] {len(pipes)} cinematograficos pending")

    ok = 0
    import time
    for idx, p in enumerate(pipes):
        if idx > 0:
            print(f"[gen] aguardando 35s pra evitar rate limit Groq...")
            time.sleep(35)
        pid, title, plat, meta = p["id"], p["title"], p["target_platform"], p.get("metadata",{}) or {}
        voz = meta.get("voice_profile_required","feminina_calma_lenta")
        serie_nome = meta.get("serie_nome","Decifre a Mente")
        mirror_canal = meta.get("mirror_canal_origem","Psych2Go")
        mirror_hook = meta.get("mirror_hook_3s","")
        topico = meta.get("topic_seed","psicologia")

        is_short = plat in ("youtube_shorts","instagram_reels","tiktok_short","pinterest_pin")
        target_min = 1 if is_short else 20
        target_chars = 800 if is_short else 14000

        system = f"""Roteirista psicologia/saude mental canal Daniela Coelho.
Estilo CINEMATOGRAFICO LENTO PROFUNDO CALMO (estilo Psych2Go narrado por Amanda Silvera).
Voz alvo: {voz} - tom hipnotico que prende atencao sem dropoff.
Serie: {serie_nome}. Inspiracao: {mirror_canal} (NAO mencionar nome).
Hook 3s ouro: {mirror_hook}.

REGRAS:
- Ritmo lento, pausas dramaticas.
- Frases curtas (max 18 palavras).
- "voce ja se sentiu...", "imagine que...", "talvez voce reconheca...".
- ZERO mencao a marcas concorrentes.
- ZERO diagnostico medico, apenas educativo.
- Hook 3s = pergunta paradoxal ou afirmacao perturbadora.
- Estrutura: HOOK 5s + DOR + N PONTOS + RESOLUCAO + CTA.
- Saida: APENAS o roteiro corrido em portugues BR, sem cabecalhos."""

        user_prompt = f"""Topico: {topico}
Titulo: {title}
Duracao alvo: {target_min} minutos ({target_chars} caracteres aprox).
Plataforma: {plat}.

Gere o roteiro completo agora em portugues BR cinematografico, narrado em primeira pessoa."""

        print(f"\n[gen] #{pid} '{title[:60]}' (voz={voz}, alvo={target_chars}c)")
        script = groq_generate(system, user_prompt, max_tokens=8000)
        if not script:
            print(f"[gen] #{pid} falhou"); continue
        script = script.strip()
        if len(script) < 500:
            print(f"[gen] #{pid} muito curto"); continue

        s_up, b_up = sb(f"{SBU}/rest/v1/content_pipeline?id=eq.{pid}", "PATCH",
            body={"status":"script_ready", "script": script,
                  "metadata": {**meta,
                               "script_generated_chars": len(script),
                               "script_generated_via": "groq_direct_cinematic"}})
        print(f"[gen] #{pid} -> script_ready ({len(script)}c) sb={s_up}")
        if s_up < 300: ok += 1
    print(f"\n[gen] total ok: {ok}/{len(pipes)}")

if __name__ == "__main__":
    main()
