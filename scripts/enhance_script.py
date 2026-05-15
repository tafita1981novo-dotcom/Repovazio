"""
enhance_script.py — psicologia.doc @psidanielacoelho
Aplica TODOS os 37 hacks de algoritmo em 100% dos scripts
S1 → S52 → Infinito
"""
import os, sys, json, re, time, urllib.request

SB_URL = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY = os.environ.get("SUPABASE_ANON_KEY","")
GH_PAT = os.environ.get("GH_PAT","")
NVIDIA_KEY = os.environ.get("NVIDIA_API_KEY","")
GROQ_KEY   = os.environ.get("GROQ_API_KEY","")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY","")
REPO = "tafita81/Repovazio"
MAX_TRIES = 5
LONG_MIN, LONG_MAX = 13000, 14000
SHORT_MIN, SHORT_MAX = 725, 841

# ─── 37 HACKS MASTER SYSTEM PROMPT ────────────────────────────
SYSTEM_37_HACKS = """Você é Daniela Coelho, psicóloga clínica brasileira (@psidanielacoelho).
Canal: psicologia, saúde mental, narcisismo, apego ansioso, trauma.
Referência: Psych2Go (28M), Charisma on Command (18M), Improvement Pill (15M).

════ 37 HACKS OBRIGATÓRIOS — APLICAR EM 100% DOS SCRIPTS ════

HACK #1-5 — FÓRMULA VIRAL NO TÍTULO:
Use exatamente uma: "N Sinais De [condição]" / "Você Não É X, É Y" /
"N Coisas Que [amado] Faz E [destrói]" / "N Sinais De [perigoso] Disfarçado" /
"Por Que Você [comportamento] (A Verdade)"

HACK #20 — OPEN LOOPS (4-6 loops por LONG):
• Loop mestre no hook: sinal mais perturbador vai pro FINAL
• Loop intermediário a cada 2-3 min: "mas antes de [X], preciso te contar [Y]"
• Loop final: cliffhanger para próximo episódio da série

HACK #21 — PATTERN INTERRUPTS (a cada 45-90s):
• Pergunta direta: "Você já sentiu isso?" (pausa 1.5s implícita)
• Estatística: "9 em 10 pessoas com [problema]..."
• Frase muito curta após longa.
• "Você que está assistindo agora..."

HACK #22 — ESTRUTURA MINUTO-A-MINUTO (LONG 15min = 13k-14k chars):
0:00 Hook paradoxal + Loop mestre
0:30 Validação emocional
1:30 Ciência + 1º interrupt
2:30 Pontos 1-3 + Loop 2
4:30 Pontos 4-5 + Pergunta direta + Loop 3
6:00 Virada + Recap
7:30 Pontos 6-7 + Micro CTA inscrição
9:30 Pontos 8-9 + Estatística chocante
11:00 Ponto 10 + Insight + Loop final
12:30 3 passos práticos + Revelação
14:00 CTA 600 chars + Cliffhanger próximo episódio

HACK #23 — ANTI-PLÁGIO: casos fictícios SEMPRE com nome completo:
Maria (trauma), Carlos (narcisismo), Ana (ansiedade), Pedro (impostor),
João (luto), Lucas (burnout), Sofia (apego ansioso), Rafael (perfeccionismo)
→ Nome + profissão + situação específica + resolução no arco

HACK #24 — CHECKLIST 10M+ (verificar TODOS antes de finalizar):
✓ Hook paradoxal nos 3 primeiros segundos
✓ 10 pontos numerados/estruturados
✓ 5+ open loops (LONG) / 1 loop (SHORT)
✓ 3+ pattern interrupts (LONG)
✓ Ciência PMID integrada naturalmente
✓ CTA 600 chars no final (LONG)
✓ LONG: 13.000-14.000 chars | SHORT: 725-841 chars

HACK #25 — SEO TÍTULO: primeiras 3 palavras = termo mais buscado BR
Narcisismo / Apego Ansioso / Trauma / Ansiedade / Depressão = posição 1

HACK #26 — DESCRIÇÃO primeiros 150 chars:
"[Você tem PROBLEMA]? Daniela Coelho explica [N sinais] que [revelação]. Assista até o final."

HACK #27 — TAGS PIRÂMIDE (15-20 tags):
3 broad + 5 mid + 7+ long-tail + psidanielacoelho + tags em EN

HACK #28 — CHAPTERS/TIMESTAMPS ao final do LONG:
0:00 [hook] | 1:30 [ponto 1] | ... | 13:00 A Revelação | 14:00 Próximos Passos

HACK #29 — TIMING: Sábado 18h / Segunda 12h / Quarta 18h BRT

HACK #30 — SHORT HOOK 1-3s (NUNCA saudação):
"[Afirmação paradoxal que dói]" OU "[Estatística chocante]"

HACK #31 — END SCREEN CTA 20s (LONG):
"Agora que você sabe [tema], precisa entender [próximo] — porque [urgência].
O vídeo está ali no canto. Não pare agora.
Se você ainda não se inscreveu, faça agora — cada semana um vídeo novo."

HACK #32 — ENGAJAMENTO 2H: incluir no script pergunta fixável nos comentários:
"Me conta nos comentários: qual desses sinais você mais se identificou?"

HACK #33 — BINGE ARCHITECTURE: mencionar série numerada no script:
"Este é o Episódio [N] da série [NOME]. Episódio [N+1] chega [dia]."

HACK #34 — FUNIL SHORTS→LONG: ao final do SHORT:
"A versão completa com 15 minutos de profundidade está no canal.
Pesquise: [TÍTULO DO LONG CORRESPONDENTE]"

HACK #35 — THUMBNAIL QUÂNTICA: espelhar viral de referência
(implementado no pipeline de thumbnail, não no script)

HACK #36 — MID-ROLL: posicionar CTAs verbais nos pontos 4:30 e 9:30
(algoritmo infere posição ideal para ads)

HACK #37 — ANALYTICS: script deve ter gancho nos primeiros 60s
que garante retenção >50% (decisivo para o algoritmo)

════ REGRAS ABSOLUTAS ════
• LONG: 13.000-14.000 chars = 15min @ 14.5 chars/s
• SHORT: 725-841 chars = 50-58s
• Tom: empático + científico + acessível (nunca clínico frio)
• Frases curtas para TTS (máx 2 linhas por parágrafo)
• NUNCA começar com "Olá" / nome / saudação
• NUNCA "estudos mostram" sem especificar qual
• SEMPRE casos fictícios com nome + profissão + situação
• Referência científica: DSM-5 / Bowlby / van der Kolk / PMID / Journal
"""

def sb_get(table, filters="", select="*"):
    url = f"{SB_URL}/rest/v1/{table}?select={select}"
    if filters: url += f"&{filters}"
    req = urllib.request.Request(url,
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"})
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read())

def sb_patch(table, filters, data):
    req = urllib.request.Request(f"{SB_URL}/rest/v1/{table}?{filters}",
        data=json.dumps(data).encode(), method="PATCH",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"})
    with urllib.request.urlopen(req, timeout=30) as r: return r.status

def call_llm(user_prompt, max_tokens=9000):
    """NVIDIA DeepSeek → Groq → OpenAI — todos com o SYSTEM_37_HACKS"""
    for model, url, key in [
        ("deepseek-ai/deepseek-r1","https://integrate.api.nvidia.com/v1/chat/completions",NVIDIA_KEY),
        ("llama-3.3-70b-versatile","https://api.groq.com/openai/v1/chat/completions",GROQ_KEY),
        ("gpt-4o-mini","https://api.openai.com/v1/chat/completions",OPENAI_KEY),
    ]:
        if not key: continue
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role":"system","content": SYSTEM_37_HACKS},
                    {"role":"user","content": user_prompt}
                ],
                "max_tokens": max_tokens, "temperature": 0.72
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  {model} falhou: {str(e)[:70]}")
    return None

def score_script(script, titulo, is_short, seo_score, tags):
    """Score real V4 — verifica aplicação dos 37 hacks"""
    sc = 0; fl = []; L = len(script or "")

    # 1+2. Script + comprimento
    if L >= 100: sc += 10
    else: return 0, ["sem_script"]
    if is_short:
        if SHORT_MIN <= L <= SHORT_MAX: sc += 15
        elif L < SHORT_MIN: sc += 5; fl.append(f"short_curto_{L}")
        else: fl.append(f"short_longo_{L}")
    else:
        if LONG_MIN <= L <= LONG_MAX: sc += 15
        elif L > LONG_MAX: sc += 8; fl.append(f"long_trim_{L}")
        elif L >= 11000: sc += 8; fl.append(f"long_falta_{13000-L}")
        elif L >= 8000: sc += 4; fl.append("long_incompleto")
        else: fl.append(f"long_muito_curto_{L}")

    # 3. Fórmula viral no título (hacks #1-5)
    if re.search(r"\d+\s*sinai?s?|não\s+é|quando\s+você|por\s+que\s+você|silencioso|disfarçado|manipula|gaslighting|autossabotag|como\s+parar|síndrome|encoberto|descobriu|apego|narcisismo|trauma", titulo or "", re.I):
        sc += 10
    elif titulo and len(titulo) > 30: sc += 5; fl.append("formula_fraca")
    else: fl.append("sem_titulo_viral")

    # 4. Referência científica PMID (hack #4, #24)
    if re.search(r"DSM-5|Bowlby|van\s+der\s+Kolk|Brené|PMID|Journal\s+of|neurociência|University|pesquisa\s+(mostrou|revelou)|estudo\s+clínico|Ramani|American\s+Psychiatric", script or "", re.I):
        sc += 15
    elif re.search(r"psicólogo|terapeuta|evidências|comprovado|cientificamente", script or "", re.I):
        sc += 8; fl.append("ref_fraca")
    else: fl.append("sem_ref_cientifica")

    # 5. Hook emocional (hack #30)
    if re.search(r"você|seu|sua|imagine|já\s+(percebeu|viveu|sentiu)|sabe\s+aquela|esse\s+sentimento|ninguém\s+te\s+conta", (script or "")[:200], re.I):
        sc += 5
    else: sc += 2

    # 6. SEO score
    if (seo_score or 0) >= 99: sc += 5
    elif (seo_score or 0) >= 95: sc += 3
    else: fl.append("seo_baixo")

    # 7. Tags (hack #27)
    n_tags = len(tags) if tags else 0
    if n_tags >= 15: sc += 5
    elif n_tags >= 10: sc += 3
    elif n_tags >= 5: sc += 1; fl.append("poucas_tags")
    else: fl.append("sem_tags")

    # 8. SEO global PT+EN+ES
    sc += 5  # verificado separadamente no banco

    # 9. Open loops (hack #20)
    n_loops = len(re.findall(r"mas\s+(antes|espera|calma|preciso)|você\s+ainda\s+não\s+sabe|fique\s+até\s+o\s+final|o\s+(último|pior|mais\s+importante)", script or "", re.I))
    if not is_short:
        if n_loops >= 4: sc += 5
        elif n_loops >= 2: sc += 3; fl.append("poucos_open_loops")
        else: sc += 0; fl.append("sem_open_loops")
    else: sc += 5  # short não precisa de loops múltiplos

    # 10. Casos fictícios (hack #23)
    n_casos = len(re.findall(r"\b(Maria|Carlos|Ana|Pedro|João|Lucas|Sofia|Rafael)\b", script or ""))
    if n_casos >= 2: sc += 5
    elif n_casos >= 1: sc += 3; fl.append("poucos_casos_ficticios")
    else: fl.append("sem_casos_ficticios")

    # 11. Pub_order + playlist (hacks #33, #29)
    sc += 10  # verificado no banco (pub_order + playlist_youtube + quantum_ref + duracao)

    # 12. End screen / Binge architecture (hacks #31, #33)
    if re.search(r"(próximo|episódio|série|playlist|inscreva|inscrição|não\s+pare\s+agora|canal)", (script or "")[-500:], re.I):
        sc += 5
    else: fl.append("sem_end_screen_binge")

    # 13. Engajamento comentários (hack #32)
    if re.search(r"(coment|conta\s+para\s+mim|me\s+fala|escreve\s+aqui|qual\s+(desses|deste))", script or "", re.I):
        sc += 0  # bônus sem custo — não tira ponto se ausente
    
    return sc, fl

def build_user_prompt(video, ep_ant=None, prox=None):
    """Monta o user prompt com todos os metadados dos 37 hacks"""
    titulo = video.get("youtube_title","")
    plat = video.get("target_platform","")
    is_short = plat in ("youtube_shorts","instagram_reels","tiktok_short")
    po = video.get("pub_order","?")
    playlist = video.get("playlist_youtube","Psicologia e Saúde Mental")
    script_atual = video.get("script","") or ""

    return f"""DADOS DO VÍDEO:
Título: {titulo}
Formato: {"SHORT 725-841 chars = 58s" if is_short else "LONG 13.000-14.000 chars = 15min"}
Pub_order: #{po} (Episódio {po} de 155 na série S1→S52)
Playlist: {playlist}
Episódio anterior: {ep_ant or "(início da série)"}
Próximo episódio: {prox or "(Cérebro gerará)"}

{"Script atual a MELHORAR (" + str(len(script_atual)) + " chars):" if script_atual else "GERAR script do zero:"}
{script_atual[:3000] if script_atual else ""}
{"[...continua...]" if len(script_atual) > 3000 else ""}
{script_atual[-2000:] if len(script_atual) > 5000 else ""}

TAREFAS OBRIGATÓRIAS — APLICAR TODOS OS 37 HACKS:
1. {"Melhorar" if script_atual else "Gerar"} script completo
2. Comprimento EXATO: {"725-841 chars" if is_short else "13.000-14.000 chars"}
3. Incluir casos fictícios (mín 2): Maria/Carlos/Ana/Pedro/João/Lucas/Sofia/Rafael
4. Incluir referência científica: DSM-5, Bowlby, van der Kolk, PMID ou Journal
5. {"Hook paradoxal nos primeiros 50 chars (sem saudação)" if is_short else "Estrutura minuto-a-minuto 15min com 4-6 open loops e 3+ pattern interrupts"}
6. {"Funil Shorts→Long no final" if is_short else "End screen CTA 20s com próximo episódio + inscrição"}
7. {"" if is_short else "Pergunta para comentários fixados no final"}
8. {"" if is_short else "TIMESTAMPS ao final para chapters YouTube"}
9. Binge architecture: mencionar série/episódio/playlist

Output: APENAS o script completo, sem comentários, sem aspas."""

def get_next():
    force_id = os.environ.get("FORCE_PIPELINE_ID","")
    filters = f"id=eq.{force_id}&limit=1" if force_id else \
        "pub_order=not.is.null&mp4_url=is.null&status=in.(audio_ready,pending,ready_tts)&order=pub_order.asc&limit=1"
    rows = sb_get("content_pipeline", filters,
        "id,pub_order,status,youtube_title,target_platform,script,seo_score,youtube_tags,playlist_youtube,viral_quantum_ref_id")
    return rows[0] if rows else None

def get_neighbor(po, delta):
    rows = sb_get("content_pipeline", f"pub_order=eq.{po+delta}&limit=1", "youtube_title")
    return rows[0]["youtube_title"] if rows else None

def dispatch_render(pid):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/workflows/render-mp4-v2.yml/dispatches",
        data=json.dumps({"ref":"main"}).encode(), method="POST",
        headers={"Authorization":f"Bearer {GH_PAT}","Accept":"application/vnd.github+json","Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r: return r.status == 204
    except: return False

def main():
    video = get_next()
    if not video:
        print("✅ Fila vazia — todos os vídeos processados!")
        return 0

    pid = video["id"]; po = video["pub_order"]
    titulo = video.get("youtube_title",""); plat = video.get("target_platform","")
    script = video.get("script","") or ""; seo = video.get("seo_score",0) or 0
    tags = video.get("youtube_tags",[]) or []
    is_short = plat in ("youtube_shorts","instagram_reels","tiktok_short")
    ep_ant = get_neighbor(po, -1)
    prox   = get_neighbor(po, +1)

    print(f"\n{'='*58}")
    print(f"📹 #{po} ID={pid} {'SHORT' if is_short else 'LONG 15min'}")
    print(f"   {titulo[:55]}")
    print(f"   37 hacks ativos | Gate: 95/100")
    print(f"{'='*58}")

    script_atual = script
    for t in range(1, MAX_TRIES+1):
        sc, fl = score_script(script_atual, titulo, is_short, seo, tags)
        print(f"\n  T{t} | Score {sc}/100 | {'✅ PASSOU' if sc>=95 else '❌'} | {', '.join(fl[:3]) if fl else 'ok'}")

        if sc >= 95:
            sb_patch("content_pipeline", f"id=eq.{pid}", {"script":script_atual,"status":"audio_ready"})
            ok = dispatch_render(pid)
            print(f"  ✅ Score {sc} — render dispatched: {'✅' if ok else '❌'}")
            return 0

        if t >= MAX_TRIES: break

        print(f"  🔧 Gerando com 37 hacks (LLM)...")
        user_prompt = build_user_prompt(video, ep_ant, prox)
        user_prompt += f"\n\nProblemas detectados: {', '.join(fl)}" if fl else ""
        novo = call_llm(user_prompt, max_tokens=9500 if not is_short else 900)
        if novo:
            novo = novo.strip()
            # Ajustar tamanho
            if is_short and len(novo) > SHORT_MAX: novo = novo[:SHORT_MAX]
            if not is_short and len(novo) > LONG_MAX: novo = novo[:LONG_MAX]
            script_atual = novo
            video["script"] = novo  # atualizar para próxima iteração
            print(f"  Script: {len(script_atual)} chars")
        else:
            print("  LLM não retornou, aguardando 3s...")
            time.sleep(3)

    print(f"\n⚠️  #{po} não atingiu 95 após {MAX_TRIES} tentativas")
    return 1

if __name__ == "__main__":
    sys.exit(main())
