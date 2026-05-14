"""
Script de melhoria sequencial do ranking psicologia.doc
Processa UMA video por vez em ordem de pub_order
Garante score >= 95 antes de renderizar
"""
import os, sys, json, re, time, urllib.request

# Config
SB_URL = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY = os.environ.get("SUPABASE_ANON_KEY","")
GH_PAT = os.environ.get("GH_PAT","")
NVIDIA_KEY = os.environ.get("NVIDIA_API_KEY","")
GROQ_KEY = os.environ.get("GROQ_API_KEY","")
REPO = "tafita81/Repovazio"
MAX_TENTATIVAS = 5

LONG_MIN, LONG_MAX = 17000, 17800
SHORT_MIN, SHORT_MAX = 725, 841

def sb_sql(query):
    req = urllib.request.Request(
        f"{SB_URL}/rest/v1/rpc/exec_sql",
        data=json.dumps({"query": query}).encode(),
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                 "Content-Type": "application/json", "Prefer": "return=representation"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except:
        pass

def sb_get(table, filters="", select="*"):
    url = f"{SB_URL}/rest/v1/{table}?select={select}"
    if filters: url += f"&{filters}"
    req = urllib.request.Request(url,
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def sb_patch(table, filters, data):
    url = f"{SB_URL}/rest/v1/{table}?{filters}"
    req = urllib.request.Request(url,
        data=json.dumps(data).encode(), method="PATCH",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                 "Content-Type": "application/json", "Prefer": "return=representation"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def call_llm(system_prompt, user_prompt, max_tokens=4000):
    """Tenta NVIDIA DeepSeek → Groq Llama como fallback"""
    # Tentar NVIDIA
    if NVIDIA_KEY:
        try:
            payload = {
                "model": "deepseek-ai/deepseek-r1",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens, "temperature": 0.7
            }
            req = urllib.request.Request(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Authorization": f"Bearer {NVIDIA_KEY}",
                         "Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=90) as r:
                result = json.loads(r.read())
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  NVIDIA falhou: {e}")

    # Fallback Groq
    if GROQ_KEY:
        try:
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens, "temperature": 0.7
            }
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Authorization": f"Bearer {GROQ_KEY}",
                         "Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=90) as r:
                result = json.loads(r.read())
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  Groq falhou: {e}")
    return None

def score_script(script, titulo, is_short, seo_score, tags):
    """Score real baseado nos critérios da memória eterna"""
    score = 0
    falhas = []
    script_len = len(script or "")

    # 1. Script existe
    if script and script_len >= 100:
        score += 20
    else:
        falhas.append("sem_script")
        return score, falhas

    # 2. Comprimento
    if is_short:
        if SHORT_MIN <= script_len <= SHORT_MAX: score += 20
        elif script_len < SHORT_MIN: score += 8; falhas.append("curto_demais")
        else: falhas.append("longo_demais")
    else:
        if LONG_MIN <= script_len <= LONG_MAX: score += 20
        elif script_len >= 13000: score += 12; falhas.append("abaixo_17000")
        elif script_len >= 8000: score += 6; falhas.append("script_incompleto")
        else: falhas.append("muito_curto")

    # 3. Título viral
    if titulo and re.search(r'\d+\s*sinais?|não\s+é\s+\w+.*é|quando\s+você|como\s+identificar|por\s+que\s+você|o\s+que\s+\w+\s+faz|você\s+(sabota|tem|está)', titulo or "", re.I):
        score += 15
    elif titulo and len(titulo) > 20:
        score += 7; falhas.append("titulo_formula_fraca")

    # 4. Referência científica
    if re.search(r'DSM-5|Bowlby|van der Kolk|Brené Brown|Kübler-Ross|Ramani|PMID|neurociência|American Psychiatric|Journal|pesquisa|estudo científico', script or "", re.I):
        score += 15
    else:
        score += 0; falhas.append("sem_ref_cientifica")

    # 5. Hook inicial
    if re.search(r'você|seu|sua|imagine|já percebeu|existe algo|esse sentimento', (script or "")[:200], re.I):
        score += 10
    else:
        score += 3

    # 6. SEO Score
    if seo_score >= 99: score += 10
    elif seo_score >= 95: score += 8
    else: falhas.append("seo_baixo")

    # 7. Tags
    if tags and len(tags) >= 10: score += 5
    elif tags and len(tags) >= 5: score += 3
    else: falhas.append("poucas_tags")

    # 8. Pub_order (garantido)
    score += 5

    return score, falhas

def expandir_long_script(script, titulo, falhas):
    """Expande script LONG para 17000-17800 chars com referências científicas"""
    script_len = len(script)
    chars_faltam = LONG_MIN - script_len
    precisa_refs = "sem_ref_cientifica" in falhas

    system = """Você é Daniela Coelho, psicóloga clínica brasileira especialista em psicologia viral.
Escreva EXCLUSIVAMENTE em português brasileiro. Tom: empático, científico, acessível.
REGRAS ABSOLUTAS:
- Sempre inclua referências científicas: DSM-5, Bowlby, van der Kolk, Brené Brown, ou pesquisas com PMID
- Use frases curtas para TTS (max 2 linhas por parágrafo)
- Hook emocional forte no início
- Exemplos reais anonimizados (João, Maria, Ana...)
- Sempre termine com cliffhanger para o próximo episódio"""

    user = f"""Título: {titulo}
Script atual ({script_len} chars):
{script[:3000]}
[...continua...]
{script[-2000:]}

TAREFA:
1. EXPANDA este script para exatamente {LONG_MIN}-{LONG_MAX} caracteres
2. {'ADICIONE referências científicas (DSM-5, Bowlby, van der Kolk, PMID) integradas naturalmente' if precisa_refs else ''}
3. Mantenha o tom e estilo atual
4. Adicione mais exemplos, profundidade científica, e insights práticos
5. Output: APENAS o script expandido completo, sem comentários

Script atual termina em:
{script[-500:]}

Continue e expanda a partir daqui mantendo coerência narrativa:"""

    llm_response = call_llm(system, user, max_tokens=8000)
    if llm_response:
        # Se o LLM retornou um script completo
        if len(llm_response) > 2000:
            # Combinar script original com expansão
            novo_script = script + "\n\n" + llm_response
            novo_script = novo_script[:LONG_MAX]
            return novo_script
    return None

def melhorar_short_script(script, titulo, falhas):
    """Melhora script SHORT: adiciona refs, ajusta tamanho"""
    script_len = len(script)
    precisa_refs = "sem_ref_cientifica" in falhas
    precisa_expandir = "curto_demais" in falhas
    precisa_reduzir = "longo_demais" in falhas

    system = """Você é Daniela Coelho, psicóloga clínica brasileira.
Escreva scripts para YouTube Shorts em português brasileiro.
REGRAS:
- Exatamente 725-841 caracteres (contados sem espaços extras)
- Inclua referência científica (DSM-5, Bowlby, pesquisa) integrada naturalmente
- Hook impactante nos primeiros 2 segundos
- Fórmula viral: N Sinais, Não é X é Y, ou Por Que Você...
- Cada frase em linha separada para Edge TTS"""

    user = f"""Título: {titulo}
Script atual ({script_len} chars):
{script}

PROBLEMAS:
{', '.join(falhas)}

TAREFA: Reescreva este script SHORT para:
1. Ter exatamente entre 725-841 caracteres
2. {'Incluir referência científica (DSM-5, Bowlby, neurociência) naturalmente' if precisa_refs else ''}
3. Manter o gancho do título
4. Output: APENAS o script reescrito, sem comentários ou aspas"""

    llm_response = call_llm(system, user, max_tokens=800)
    if llm_response:
        # Limpar e verificar tamanho
        novo = llm_response.strip()
        if SHORT_MIN <= len(novo) <= SHORT_MAX:
            return novo
        # Tentar ajustar
        if len(novo) > SHORT_MAX:
            novo = novo[:SHORT_MAX]
        return novo
    return None

def get_next_video():
    """Busca próximo vídeo a processar em ordem"""
    rows = sb_get("content_pipeline",
        "pub_order=not.is.null&mp4_url=is.null&status=in.(audio_ready,pending,ready_tts)&order=pub_order.asc&limit=1",
        "id,pub_order,status,youtube_title,target_platform,script,seo_score,youtube_tags,youtube_description")
    return rows[0] if rows else None

def get_storage_mb():
    """Retorna uso atual de storage em MB"""
    rows = sb_get("storage/objects", "bucket_id=eq.videos",
                  "(metadata->>'size')::numeric")
    # Usar API de storage diferente
    try:
        req = urllib.request.Request(
            f"{SB_URL}/storage/v1/object/list/videos",
            data=json.dumps({"prefix":"","limit":500}).encode(), method="POST",
            headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            files = json.loads(r.read())
            total = sum((f.get("metadata") or {}).get("size", 0) for f in files if f.get("name"))
            return total / 1024 / 1024
    except:
        return 0

def dispatch_render(pipeline_id):
    """Dispara o render-mp4-v2 workflow"""
    payload = {
        "ref": "main",
        "inputs": {"pipeline_id": str(pipeline_id)}
    }
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/workflows/render-mp4-v2.yml/dispatches",
        data=json.dumps(payload).encode(), method="POST",
        headers={"Authorization": f"Bearer {GH_PAT}",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 204
    except Exception as e:
        print(f"  Dispatch falhou: {e}")
        return False

def main():
    video = get_next_video()
    if not video:
        print("✅ Nenhum vídeo pendente. Pipeline completo!")
        return 0

    pid = video["id"]
    pub_order = video["pub_order"]
    titulo = video.get("youtube_title", "")
    plataforma = video.get("target_platform", "")
    script = video.get("script", "") or ""
    seo_score = video.get("seo_score", 0) or 0
    tags = video.get("youtube_tags", []) or []
    is_short = plataforma in ("youtube_shorts", "instagram_reels", "tiktok_short")

    print(f"\n{'='*60}")
    print(f"📹 Processando #{pub_order} — ID {pid}")
    print(f"   Tipo: {'SHORT' if is_short else 'LONG'} | {titulo[:50]}")
    print(f"{'='*60}")

    storage_mb = get_storage_mb()
    print(f"💾 Storage atual: {storage_mb:.1f} MB / 900 MB")
    if storage_mb > 850:
        print(f"⚠️  Storage crítico! Interrompendo para limpeza manual.")
        return 2

    # Loop de melhoria
    script_atual = script
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        score, falhas = score_script(script_atual, titulo, is_short, seo_score, tags)
        print(f"\n  Tentativa {tentativa} | Score: {score}/100 | {'✅ PASSOU' if score >= 95 else '❌ FALHOU'}")
        if falhas:
            print(f"  Falhas: {', '.join(falhas)}")

        if score >= 95:
            print(f"\n  ✅ Score {score} — atualizando banco e disparando render...")
            # Atualizar script no banco
            sb_patch("content_pipeline", f"id=eq.{pid}",
                     {"script": script_atual, "status": "audio_ready"})
            # Disparar render
            ok = dispatch_render(pid)
            print(f"  Render dispatched: {'✅' if ok else '❌'}")
            print(f"\n🎬 Vídeo #{pub_order} enfileirado com score {score}")
            return 0

        if tentativa >= MAX_TENTATIVAS:
            print(f"\n  ❌ Máximo de tentativas atingido. Score final: {score}")
            break

        # Melhorar script
        print(f"  🔧 Melhorando script... (falhas: {', '.join(falhas)})")
        if is_short:
            novo_script = melhorar_short_script(script_atual, titulo, falhas)
        else:
            novo_script = expandir_long_script(script_atual, titulo, falhas)

        if novo_script:
            script_atual = novo_script
            print(f"  Script atualizado: {len(script_atual)} chars")
        else:
            print(f"  LLM não retornou melhoria, tentando novamente...")
            time.sleep(2)

    print(f"\n⚠️  Vídeo #{pub_order} não atingiu score 95 após {MAX_TENTATIVAS} tentativas")
    return 1

if __name__ == "__main__":
    sys.exit(main())
