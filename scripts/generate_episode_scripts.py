#!/usr/bin/env python3
"""
generate_episode_scripts.py — GERADOR DE SCRIPTS COMPLETOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Para cada episódio sem script:
1. Carrega personagens do universo + estratégia do arco
2. Groq gera script COMPLETO com:
   - Personagens interagindo (Sara, Lucas, Daniela, etc.)
   - Mecanismos de hipnose embutidos
   - Segmentos de ~41 chars (cada um = 1 imagem diferente)
   - Captions específicas por segmento
   - Cliffhanger no final
3. Salva em content_pipeline (status=script_ready)
4. Vincula ao series_episodes

MECANISMOS DE HIPNOSE EMBUTIDOS EM CADA SCRIPT:
  H1 LOOP ABERTO    — pergunta sem resposta no início
  H2 RECONHECIMENTO — "você já fez isso?" direto ao espectador
  H3 MICRO-TENSÃO   — pequena revelação a cada 30s
  H4 PARASOCIAL     — chamar espectador de "você" constantemente
  H5 CLIFF INTERNO  — mini-cliffhanger antes de cada pausa natural
  H6 PROVA SOCIAL   — "pesquisas mostram que 8 em 10 pessoas..."
  H7 URGÊNCIA       — "você precisa saber isso AGORA"
  H8 IDENTIDADE     — "se você se identificou com X, então..."
"""
import os, sys, json, re, time, requests

SB_URL  = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY  = os.environ.get("SUPABASE_SERVICE_KEY","")
GROQ_KEY= os.environ.get("GROQ_API_KEY","")

# Quantos episódios gerar por execução
BATCH_SIZE = int(os.environ.get("BATCH_SIZE","5"))

def sb_get(table, qs):
    r = requests.get(f"{SB_URL}/rest/v1/{table}?{qs}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=30)
    r.raise_for_status(); return r.json()

def sb_post(table, data):
    r = requests.post(f"{SB_URL}/rest/v1/{table}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"},
        json=data, timeout=30)
    r.raise_for_status(); return r.json()

def sb_patch(table, where, data):
    r = requests.patch(f"{SB_URL}/rest/v1/{table}?{where}",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                 "Content-Type":"application/json","Prefer":"return=minimal"},
        json=data, timeout=30)
    r.raise_for_status()

# Carregar personagens do universo
chars = sb_get("character_universe",
    "select=slug,name,role,visual_desc,personality&order=id.asc")
CHARS = {c["slug"]: c for c in chars}

# Carregar memória do universo
mem_rows = sb_get("universe_memory",
    "select=character_slug,current_stage,cumulative_arc,visual_evolution")
MEM = {m["character_slug"]: m for m in mem_rows}

# Carregar episódios sem vídeo
pending = sb_get("series_episodes",
    "select=id,series_id,episode,season,episode_title,arc_phase,arc_role,script_strategy"
    f"&video_id=is.null&arc_position=not.is.null&order=series_id.asc,episode.asc"
    f"&limit={BATCH_SIZE}")

# Carregar séries
series_rows = sb_get("series",
    "select=id,title,theme,slug,icon,color_hex&publish_order=gt.0&order=publish_order.asc")
SERIES = {s["id"]: s for s in series_rows}

print(f"{'═'*60}")
print(f"  ψ GERADOR DE SCRIPTS — psicologia.doc")
print(f"  {len(pending)} episódios para gerar")
print(f"{'═'*60}\n")

def get_char_context(series_theme):
    """Selecionar personagens relevantes para o tema."""
    # Mapeamento tema → personagens principais
    theme_chars = {
        "narcisismo": ["daniela","sara","marcos","ana","julia"],
        "apego": ["daniela","sara","gui","ana","julia"],
        "gaslighting": ["daniela","sara","marcos","julia","ana"],
        "ansiedade": ["daniela","bia","ana","pedro"],
        "trauma": ["daniela","sara","clara","maya","ana"],
        "relacionamento": ["daniela","sara","rafa","julia","gui"],
        "depressao": ["daniela","lucas","maya","ana"],
        "luto": ["daniela","maya","pedro","ana"],
        "burnout": ["daniela","bia","renata","ana"],
        "dependencia": ["daniela","lucas","gui","julia"],
        "autossabotagem": ["daniela","pedro","bia","ana"],
        "ie": ["daniela","pedro","ana"],
        "autoestima": ["daniela","pedro","julia","maya"],
        "ansiedade-social": ["daniela","pedro","sara","julia"],
        "impostor": ["daniela","bia","pedro","ana"],
        "trabalho-toxico": ["daniela","bia","renata","pedro"],
        "borderline": ["daniela","sara","ana","julia"],
        "tdah": ["daniela","theo","pedro","ana"],
        "pas": ["daniela","sara","julia","maya"],
        "autoconhecimento": ["daniela","pedro","maya","ana"],
        "love-bombing": ["daniela","sara","rafa","julia"],
        "feridas": ["daniela","clara","sara","maya"],
        "manipulacao": ["daniela","sara","marcos","julia"],
        "reparentalizacao": ["daniela","clara","maya","sara"],
        "regulacao": ["daniela","bia","ana","pedro"],
    }
    slugs = theme_chars.get(series_theme, ["daniela","sara","lucas","ana"])
    result = []
    for slug in slugs[:5]:
        c = CHARS.get(slug)
        if c:
            m = MEM.get(slug, {})
            result.append({
                "name": c["name"],
                "visual": m.get("visual_evolution", c["visual_desc"]),
                "personality": c["personality"],
                "stage": m.get("current_stage", 1),
                "arc": m.get("cumulative_arc", ""),
            })
    return result

def gerar_script(ep, serie):
    """Gerar script completo para um episódio via Groq."""
    if not GROQ_KEY:
        return None, None
    
    theme = serie.get("theme","psicologia")
    ep_chars = get_char_context(theme)
    
    # Determinar duração baseado no tipo (pilot = mais curto para hook, finale = mais longo)
    arc_role = ep.get("arc_role","")
    is_long = arc_role in ("A CIÊNCIA", "O CUSTO OCULTO", "COMO PRATICAR", "TRANSFORMAÇÃO", "FINAL FELIZ")
    target_chars = 12000 if is_long else 8000  # ~14min vs ~9min com AntonioNeural
    
    # Char guide
    char_lines = []
    for c in ep_chars:
        stage_label = ["🔴iniciando","🟠percebendo","🟡lutando","🟢crescendo","✅transformado"][
            min(c["stage"]-1, 4)]
        char_lines.append(f"• {c['name']} ({stage_label}): {c["visual_desc"]}")
    char_guide = "\n".join(char_lines)
    
    system = f"""Você é o roteirista chefe de @psidanielacoelho, canal de psicologia no YouTube.
Escreva um roteiro COMPLETO para narração em voz (pt-BR, AntonioNeural).

PERSONAGENS NESTE EPISÓDIO:
{char_guide}

REGRAS DE ESCRITA (SAGRADAS):
1. Cada parágrafo = ~40 chars = 1 cena visual diferente
2. USE "você" constantemente (hipnose parasocial)
3. ABRA LOOPS no início, feche só no final (loop aberto)
4. A cada 3 parágrafos: mini-revelação ou mini-cliffhanger
5. PROVA SOCIAL: cite pesquisas a cada 60 segundos
6. URGÊNCIA: "você precisa saber AGORA", "isso é urgente"
7. IDENTIDADE: "se você se identificou, você provavelmente..."
8. Personagens AGEM e FALAM (não apenas Daniela narrando)
9. Último parágrafo: SEMPRE cliffhanger para próximo ep
10. Tom: íntimo, urgente, empático — como amiga que sabe mais

MECANISMOS DE HIPNOSE (embutir naturalmente):
H1-LOOP: "Antes de te contar o mais importante, deixa eu te mostrar algo..."
H2-RECONHECIMENTO: "Você já sentiu que [situação específica]?"
H3-PROVA: "Um estudo de Harvard mostrou que..."
H4-URGÊNCIA: "E olha só o que acontece quando você ignora isso..."
H5-IDENTIDADE: "Quem tem [padrão] geralmente..."
H6-PARASOCIAL: Daniela/personagem falam DIRETAMENTE com o espectador

FORMATO RIGOROSO:
- APENAS texto corrido para narração
- SEM marcadores, SEM títulos, SEM listas
- SEM [narrador], SEM [cena], SEM qualquer tag
- Parágrafos curtos de ~40 chars SEPARADOS por linha em branco
- Total: {target_chars} chars (importante para timing)

ESTRATÉGIA DESTE EPISÓDIO: {ep.get('script_strategy','')}"""

    user_msg = f"""Série: {serie.get('title','')}
Episódio {ep.get('episode',1)} de 10 — Fase: {ep.get('arc_phase','')} | {ep.get('arc_role','')}
Título: {ep.get('episode_title','')}

Escreva o roteiro completo de {target_chars} chars.
Inicie com um GANCHO PODEROSO nos primeiros 2 parágrafos.
Use os personagens naturalmente ao longo do episódio.
Termine com cliffhanger para o episódio {ep.get('episode',1)+1}."""

    for attempt in range(3):
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
                json={"model":"llama-3.3-70b-versatile",
                      "messages":[{"role":"system","content":system},
                                   {"role":"user","content":user_msg}],
                      "temperature":0.85,"max_tokens":8000},
                timeout=120)
            if r.status_code == 200:
                script = r.json()["choices"][0]["message"]["content"].strip()
                # Limpar tags indesejadas
                script = re.sub(r'\[.*?\]', '', script)
                script = re.sub(r'\*\*.*?\*\*:', '', script)
                script = script.strip()
                
                # Gerar captions (uma por ~41 chars)
                paras = [p.strip() for p in script.split('\n\n') if p.strip()]
                captions = []
                for para in paras:
                    # Caption = primeiras 25 chars da frase
                    cap = para[:25].split('.')[0].split(',')[0].strip()
                    if len(cap) < 5: cap = para[:20].strip()
                    captions.append(cap[:25])
                if captions: captions[-1] = "INSCREVA-SE AGORA 🔔"
                
                print(f"   ✅ Script: {len(script)} chars | {len(paras)} cenas | {len(captions)} captions")
                return script, captions
        except Exception as e:
            print(f"   Tentativa {attempt+1}: {e}")
            time.sleep(8)
    return None, None

def create_video_record(ep, serie, script, captions):
    """Criar registro no content_pipeline e vincular ao episódio."""
    topic_map = {
        "narcisismo": "Narcisismo e Manipulação",
        "apego": "Apego Ansioso",
        "gaslighting": "Gaslighting",
        "ansiedade": "Ansiedade",
        "trauma": "Trauma de Infância",
        "relacionamento": "Relacionamentos Tóxicos",
        "depressao": "Depressão",
        "luto": "Luto e Perda",
        "burnout": "Burnout",
        "dependencia": "Dependência Emocional",
        "autossabotagem": "Autossabotagem",
        "ie": "Inteligência Emocional",
        "autoestima": "Autoestima",
        "ansiedade-social": "Ansiedade Social",
        "impostor": "Síndrome do Impostor",
        "trabalho-toxico": "Trabalho Tóxico",
        "borderline": "Borderline",
        "tdah": "TDAH Adulto",
        "pas": "Pessoa Altamente Sensível",
        "autoconhecimento": "Autoconhecimento",
        "love-bombing": "Love Bombing",
        "feridas": "Feridas da Infância",
        "manipulacao": "Manipulação e Controle",
        "reparentalizacao": "Reparentalização",
        "regulacao": "Regulação Emocional",
    }
    
    theme = serie.get("theme","psicologia")
    topic = topic_map.get(theme, "Saúde Mental")
    
    # Determinar plataforma baseado no tamanho do script
    is_long_ep = len(script) > 8000
    platform = "youtube_long" if is_long_ep else "youtube"
    
    video_data = {
        "title": ep.get("episode_title",""),
        "script": script,
        "topic": topic,
        "platform": platform,
        "status": "script_ready",
        "metadata": json.dumps({
            "series_id": ep.get("series_id"),
            "episode": ep.get("episode"),
            "arc_phase": ep.get("arc_phase"),
            "arc_role": ep.get("arc_role"),
            "captions_count": len(captions),
            "chars": len(script),
            "hypnosis_mechanisms": ["H1-LOOP","H2-RECONHECIMENTO","H3-PROVA","H4-URGENCIA","H5-IDENTIDADE","H6-PARASOCIAL"],
            "chars_per_segment": 41,
            "images_needed": max(20, len(script)//41//5),
        })
    }
    
    try:
        result = sb_post("content_pipeline", video_data)
        if result and isinstance(result, list) and result[0].get("id"):
            video_id = result[0]["id"]
            # Vincular ao series_episodes
            sb_patch("series_episodes",
                f"id=eq.{ep['id']}",
                {"video_id": video_id})
            return video_id
    except Exception as e:
        print(f"   ERRO ao salvar: {e}")
    return None

# PROCESSAR EPISÓDIOS
generated = 0
for ep in pending:
    serie = SERIES.get(ep.get("series_id"))
    if not serie:
        continue
    
    print(f"\n{'─'*50}")
    print(f"  S{serie.get('publish_order',0)}/E{ep.get('episode',0)} — {ep.get('episode_title','')[:50]}")
    print(f"  Fase: {ep.get('arc_phase','')} | {ep.get('arc_role','')}")
    
    script, captions = gerar_script(ep, serie)
    
    if script and len(script) > 500:
        video_id = create_video_record(ep, serie, script, captions)
        if video_id:
            print(f"  ✅ Video #{video_id} criado | {len(script)} chars")
            generated += 1
        else:
            print(f"  ❌ Falha ao salvar no DB")
    else:
        print(f"  ⚠️ Script não gerado")
    
    time.sleep(3)  # Rate limit

print(f"\n{'═'*60}")
print(f"  ✅ {generated}/{len(pending)} episódios gerados com sucesso")
print(f"{'═'*60}\n")

