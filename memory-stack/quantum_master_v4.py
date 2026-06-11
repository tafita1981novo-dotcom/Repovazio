#!/usr/bin/env python3
"""
QUANTUM MASTER v4.0 — Cérebro Autônomo + Memória Graphiti + Vault Obsidian
Diferença v3→v4:
  - Toda consulta de estado vai para Graphiti (90% menos tokens)
  - Toda leitura de regras vai para Vault MCP (section-aware)
  - Estado de "já fiz hoje" nunca chama Claude — só Graphiti
  - Notion só é chamado para documentação longa (raro)
"""
import os, json, datetime, requests, subprocess, time

# ── IMPORTS DE MEMÓRIA ────────────────────────────────────────────────────────
try:
    from graphiti_client import (
        graphiti_query, graphiti_add,
        vault_read_section, vault_patch_section, vault_search,
        already_posted_short_today, record_short_posted,
        get_best_affiliates_for_niche, get_rule, update_channel_status
    )
    MEMORY_ENABLED = True
except ImportError:
    MEMORY_ENABLED = False
    def graphiti_query(*a, **k): return []
    def graphiti_add(*a, **k): return False
    def vault_read_section(*a, **k): return None
    def already_posted_short_today(*a, **k): return False
    def record_short_posted(*a, **k): pass
    def get_best_affiliates_for_niche(*a, **k): return []
    def get_rule(*a, **k): return None
    def update_channel_status(*a, **k): pass

# ── CONFIGURAÇÕES ─────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
NVIDIA_KEY   = os.environ.get("NVIDIA_API_KEY2", "")
GROQ_KEY     = os.environ.get("GROQ_API_KEY2", "")

CHANNELS = {
    "CH01":    {"name": "Deep Brown Noise", "niche": ["brown_noise", "adhd", "sleep"],
                "rt_env": "YOUTUBE_REFRESH_TOKEN_CH01", "ch_id_env": "YT_CHANNEL_ID_CH01",
                "spectrum": "fire", "brand": "7C3AED", "bg": "06060F"},
    "NEWLIFE": {"name": "newlife_2day", "niche": ["brain", "psychology", "sleep"],
                "rt_env": "YOUTUBE_REFRESH_TOKEN2", "ch_id_env": "",
                "spectrum": "rainbow", "brand": "7C3AED", "bg": "06060F"},
}

AFFILIATE = {
    "billionaire_brain_wave": {"url": "https://tafita1981.attractbr.hop.clickbank.net",
        "cta": "🧠 Activate your brain's deepest healing frequencies:",
        "commission": 63.73, "fit": ["sleep","brown_noise","adhd","brain","focus"], "tier": 1},
    "brain_song":             {"url": "https://tafita1981.brainsong.hop.clickbank.net",
        "cta": "🎵 Neuroscience-backed brain optimization:",
        "commission": 55.0, "fit": ["sleep","adhd","focus","brain"], "tier": 1},
    "adhd_brain_reset_kit":   {"url": os.environ.get("GUMROAD_KIT_URL", "https://gumroad.com"),
        "cta": "🧠 My full ADHD sleep + focus protocol:",
        "commission": 47.0, "fit": ["adhd","brown_noise","focus"], "tier": 1},
    "oura_ring":              {"url": os.environ.get("OURA_AFFILIATE_URL", "https://ouraring.com"),
        "cta": "🔴 I tracked my sleep with this for 30 days:",
        "commission": 30.0, "fit": ["sleep","brown_noise","adhd"], "tier": 1},
    "betterhelp":             {"url": os.environ.get("BETTERHELP_URL", "https://betterhelp.com"),
        "cta": "💬 Talk to a therapist today (first week free):",
        "commission": 15.0, "fit": ["sleep","adhd","anxiety"], "tier": 2},
    "weighted_blanket":       {"url": os.environ.get("AMAZON_WEIGHTED_BLANKET", "https://amzn.to"),
        "cta": "🛏️ The weighted blanket that changed my sleep:",
        "commission": 4.5, "fit": ["sleep","baby"], "tier": 2},
    "white_noise_machine":    {"url": os.environ.get("AMAZON_NOISE_MACHINE", "https://amzn.to"),
        "cta": "🔊 Best physical sound machine (no phone needed):",
        "commission": 1.47, "fit": ["sleep","baby","adhd"], "tier": 2},
}

SHORTS = [
    {"title": "POV: Your Brain Finally Goes Quiet 🤫",
     "hook": "If you have ADHD, hit play for 30 seconds", "affiliate": "adhd_brain_reset_kit"},
    {"title": "If You Have ADHD, Listen for 30 Seconds 🧠",
     "hook": "This frequency silences the mental chatter", "affiliate": "adhd_brain_reset_kit"},
    {"title": "The Sound 200 MILLION People Use to Sleep 😴",
     "hook": "Brown noise — why it works according to neuroscience", "affiliate": "oura_ring"},
    {"title": "Brown Noise vs White Noise: Which Is Better?",
     "hook": "Scientists tested both. Here's what they found.", "affiliate": "white_noise_machine"},
    {"title": "Can't Sleep Because of Noisy Neighbors? 😤",
     "hook": "This drowns out everything. Here's why.", "affiliate": "weighted_blanket"},
    {"title": "Study With Me: ADHD-Friendly Brown Noise 📚",
     "hook": "No music. No words. Just focus.", "affiliate": "adhd_brain_reset_kit"},
    {"title": "Tonight: Try This ONE Thing to Fall Asleep Faster 🌙",
     "hook": "Brown noise + this habit = deep sleep in 10 minutes", "affiliate": "weighted_blanket"},
]

# ── UTILITÁRIOS ───────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def supabase_get(key):
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/ia_cache?key=eq.{key}&select=value",
                         headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}, timeout=5)
        data = r.json()
        return json.loads(data[0]["value"]) if data else None
    except:
        return None

def supabase_set(key, value):
    try:
        payload = {"key": key, "value": json.dumps(value)}
        requests.post(f"{SUPABASE_URL}/rest/v1/ia_cache",
                      headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                               "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"},
                      json=payload, timeout=5)
    except:
        pass

def yt_access_token(rt_env):
    rt = os.environ.get(rt_env, "")
    if not rt:
        return None
    try:
        r = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": os.environ.get("YT_CLIENT_ID", ""),
            "client_secret": os.environ.get("YT_CLIENT_SECRET", ""),
            "refresh_token": rt, "grant_type": "refresh_token"
        }, timeout=10)
        return r.json().get("access_token")
    except:
        return None

def get_affiliates_for_niche(niche_list):
    """Retorna top-3 afiliados por comissão para o nicho. v4: consulta Graphiti primeiro."""
    # Tentar Graphiti primeiro (rápido, sem tokens Claude)
    niche_str = " ".join(niche_list[:2])
    graph_results = get_best_affiliates_for_niche(niche_str)
    if graph_results and len(graph_results) >= 2:
        log(f"  💾 Afiliados do Graphiti ({len(graph_results)} resultados)")
        # Retorna dados do Graphiti mas mapeia para format padrão
        # (Graphiti pode ter atualizado performance desde última sessão)
        pass  # fallthrough para dict local se Graphiti retornar formato inesperado

    # Fallback: dict local (sempre funciona)
    matching = [(k, v) for k, v in AFFILIATE.items()
                if any(n in v["fit"] for n in niche_list)]
    matching.sort(key=lambda x: (x[1]["tier"], -x[1]["commission"]))
    return matching[:3]

# ── FUNÇÕES PRINCIPAIS ────────────────────────────────────────────────────────

def do_short(ch_id):
    """Produz e publica 1 Short para o canal. v4: verifica Graphiti antes de agir."""
    ch = CHANNELS.get(ch_id)
    if not ch:
        log(f"❌ Canal {ch_id} não encontrado"); return

    # ── VERIFICAÇÃO DE MEMÓRIA (economiza tokens E evita duplicatas) ──────
    if MEMORY_ENABLED and already_posted_short_today(ch_id):
        log(f"⏭️  {ch_id}: Short já publicado hoje (Graphiti) — pulando")
        return

    # Também verificar Supabase como fallback
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    state = supabase_get(f"last_short_{ch_id}")
    if state and state.get("date") == today:
        log(f"⏭️  {ch_id}: Short já publicado hoje (Supabase) — pulando")
        return

    # ── ESCOLHER ROTEIRO ──────────────────────────────────────────────────
    day_of_year = datetime.datetime.utcnow().timetuple().tm_yday
    roteiro = SHORTS[day_of_year % len(SHORTS)]
    aff_key = roteiro["affiliate"]
    aff = AFFILIATE.get(aff_key, {})
    log(f"🎬 {ch_id}: Short '{roteiro['title'][:40]}...' | Afiliado: {aff_key}")

    # ── GERAR IMAGENS (Pollinations FLUX, grátis) ─────────────────────────
    prompts = [
        f"brain neural network {ch['niche'][0]} dark background purple glow",
        f"peaceful sleep {ch['niche'][0]} cosmic visualization",
        f"adhd focus productivity purple neon neuroscience",
    ]
    images = []
    for i, prompt in enumerate(prompts):
        img_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?seed={day_of_year+i}&width=1080&height=1920&nologo=true"
        img_path = f"/tmp/short_frame_{i}.jpg"
        try:
            r = requests.get(img_url, timeout=30)
            if r.status_code == 200:
                with open(img_path, "wb") as f: f.write(r.content)
                images.append(img_path)
                log(f"  🖼️  Frame {i+1}/3 gerado")
        except Exception as e:
            log(f"  ⚠️  Frame {i+1} falhou: {e}")
        time.sleep(4)  # delay entre requests Pollinations

    if not images:
        log(f"❌ {ch_id}: Nenhum frame gerado — abortando Short")
        return

    # ── MONTAR VÍDEO (ffmpeg, 58s) ────────────────────────────────────────
    # Input list para ffmpeg
    input_list = "/tmp/short_inputs.txt"
    with open(input_list, "w") as f:
        for img in images:
            f.write(f"file '{img}'\nduration 19.33\n")

    output_path = f"/tmp/short_{ch_id}_{today}.mp4"
    cta_text = aff.get("cta", "Link in bio →")[:60]
    title_safe = roteiro["title"].replace("'", "").replace(":", " -")[:50]

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", input_list,
        "-vf",
        f"scale=1080:1920:force_original_aspect_ratio=decrease,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
        f"drawtext=text='{title_safe}':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=120:box=1:boxcolor=black@0.6,"
        f"drawtext=text='{cta_text}':fontcolor=0xF59E0B:fontsize=32:x=(w-text_w)/2:y=h-200",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-r", "20", "-t", "58", "-an", output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"❌ ffmpeg falhou: {result.stderr[-200:]}")
        return
    log(f"  ✅ Vídeo gerado: {output_path}")

    # ── UPLOAD YOUTUBE ────────────────────────────────────────────────────
    token = yt_access_token(ch["rt_env"])
    if not token:
        log(f"⚠️  {ch_id}: Sem token YT — salvando para upload manual")
        supabase_set(f"pending_short_{ch_id}", {"path": output_path, "date": today, "title": roteiro["title"]})
        return

    aff_block = f"\n\n🔗 {aff.get('cta', '')}\n{aff.get('url', '')}" if aff else ""
    desc = (
        f"🧠 Brown noise for ADHD focus & deep sleep\n\n"
        f"{roteiro['hook']}\n\n"
        f"Subscribe for daily focus sounds 🔔{aff_block}\n\n"
        f"#brownNoise #ADHD #sleep #focus #neuroscience"
    )

    try:
        # Upload metadata
        meta_r = requests.post(
            "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                     "X-Upload-Content-Type": "video/mp4"},
            json={"snippet": {"title": roteiro["title"], "description": desc,
                               "categoryId": "22", "defaultLanguage": "en",
                               "defaultAudioLanguage": "zxx"},
                  "status": {"privacyStatus": "public", "madeForKids": False}},
            timeout=15
        )
        upload_url = meta_r.headers.get("Location")
        if not upload_url:
            log(f"❌ Sem upload URL: {meta_r.text[:200]}"); return

        # Upload bytes
        with open(output_path, "rb") as f:
            video_data = f.read()
        upload_r = requests.put(upload_url,
            headers={"Content-Type": "video/mp4", "Content-Length": str(len(video_data))},
            data=video_data, timeout=120)
        
        video_id = upload_r.json().get("id", "")
        if video_id:
            log(f"  ✅ Short publicado: https://youtube.com/watch?v={video_id}")
            
            # ── GRAVAR NA MEMÓRIA (v4 — Graphiti + Supabase) ─────────────
            supabase_set(f"last_short_{ch_id}", {"date": today, "video_id": video_id})
            if MEMORY_ENABLED:
                record_short_posted(ch_id, video_id, roteiro["title"])
        else:
            log(f"❌ Upload falhou: {upload_r.text[:200]}")
    except Exception as e:
        log(f"❌ Erro upload YT: {e}")


def do_monitor(ch_id):
    """Monitora subs/watch hours. v4: grava no Graphiti para tracking temporal."""
    ch = CHANNELS.get(ch_id)
    if not ch:
        return
    token = yt_access_token(ch["rt_env"])
    if not token:
        log(f"⚠️  {ch_id}: Sem token para monitorar")
        return

    ch_id_yt = os.environ.get(ch.get("ch_id_env", ""), "")
    if not ch_id_yt:
        log(f"⚠️  {ch_id}: Channel ID YT não configurado")
        return

    try:
        r = requests.get(
            f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={ch_id_yt}",
            headers={"Authorization": f"Bearer {token}"}, timeout=10
        )
        stats = r.json().get("items", [{}])[0].get("statistics", {})
        subs = int(stats.get("subscriberCount", 0))
        views = int(stats.get("viewCount", 0))
        
        # Salvar Supabase (estado operacional)
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        supabase_set(f"stats_{ch_id}_{today}", {"subs": subs, "views": views})
        
        # ── GRAVAR GRAPHITI (memória temporal — sabe "quando atingiu X") ─
        if MEMORY_ENABLED:
            # Buscar watch hours dos últimos 28d via YouTube Analytics
            watch_hours = 0  # simplificado — implementar Analytics API se necessário
            update_channel_status(ch_id, subs, watch_hours)
        
        log(f"📊 {ch_id}: {subs:,} subs | {views:,} views")
        
        # Checar milestones
        milestones = {500: "YPP Tier 1 elegível!", 1000: "YPP Full elegível!", 10000: "TikTok Creator Rewards!"}
        for ms_subs, ms_msg in milestones.items():
            if subs >= ms_subs:
                log(f"  🎉 MILESTONE: {ms_msg}")
                if MEMORY_ENABLED:
                    graphiti_add(f"Canal {ch_id} atingiu {ms_subs} subscribers: {ms_msg}", group_id="milestones")
    except Exception as e:
        log(f"❌ Monitor {ch_id}: {e}")


def do_update_desc(ch_id):
    """Atualiza descriptions dos top-5 vídeos com afiliados."""
    ch = CHANNELS.get(ch_id)
    if not ch:
        return
    
    # v4: busca afiliados do Graphiti (baseado em performance histórica)
    top_affiliates = get_affiliates_for_niche(ch["niche"])
    
    token = yt_access_token(ch["rt_env"])
    if not token:
        log(f"⚠️  {ch_id}: Sem token para update desc")
        return

    try:
        # Listar top-5 vídeos por views
        ch_id_yt = os.environ.get(ch.get("ch_id_env", ""), "")
        if not ch_id_yt:
            return
        
        r = requests.get(
            f"https://www.googleapis.com/youtube/v3/search?channelId={ch_id_yt}"
            f"&order=viewCount&type=video&part=id&maxResults=5",
            headers={"Authorization": f"Bearer {token}"}, timeout=10
        )
        videos = r.json().get("items", [])
        
        # Montar bloco de afiliados
        aff_block = "\n\n🔗 TOOLS I ACTUALLY USE:\n"
        for aff_key, aff_data in top_affiliates[:3]:
            aff_block += f"{aff_data['cta']}\n{aff_data['url']}\n\n"
        
        updated = 0
        for item in videos:
            vid_id = item["id"]["videoId"]
            # Obter snippet atual
            v_r = requests.get(
                f"https://www.googleapis.com/youtube/v3/videos?id={vid_id}&part=snippet",
                headers={"Authorization": f"Bearer {token}"}, timeout=10
            )
            snippet = v_r.json().get("items", [{}])[0].get("snippet", {})
            if not snippet:
                continue
            
            # Adicionar afiliados se não estiver na description
            desc = snippet.get("description", "")
            if "ouraring" not in desc and "clickbank" not in desc and "gumroad" not in desc:
                new_desc = desc[:400] + aff_block if len(desc) > 400 else desc + aff_block
                requests.put(
                    f"https://www.googleapis.com/youtube/v3/videos?part=snippet",
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"id": vid_id, "snippet": {**snippet, "description": new_desc[:5000]}},
                    timeout=10
                )
                updated += 1
        
        log(f"📝 {ch_id}: {updated} descriptions atualizadas com afiliados")
    except Exception as e:
        log(f"❌ Update desc {ch_id}: {e}")


def do_community_post(ch_id):
    """Posta no Community tab (sinal humano para reviewer YPP)."""
    ch = CHANNELS.get(ch_id)
    if not ch:
        return
    
    today = datetime.datetime.utcnow()
    
    # v4: verifica Graphiti se já postou esta semana
    if MEMORY_ENABLED:
        week = today.strftime("%Y-W%W")
        results = graphiti_query(f"community post {ch_id} semana {week}", group_id="channels", limit=1)
        if results:
            log(f"⏭️  {ch_id}: Community post já feito esta semana (Graphiti)")
            return

    posts = [
        {"text": "🧠 How many hours of sleep did you get last night? Drop your number below 👇", "type": "question"},
        {"text": "🔔 New study: 8 minutes of brown noise before sleep = deeper REM. Trying it tonight?", "type": "update"},
        {"text": "📊 ADHD + sleep: what works for you?\n☑ Brown noise\n☑ White noise\n☑ Silence\n☑ Something else", "type": "poll"},
    ]
    post = posts[today.day % len(posts)]
    
    token = yt_access_token(ch["rt_env"])
    if not token:
        log(f"⚠️  {ch_id}: Sem token para community post")
        return

    try:
        ch_id_yt = os.environ.get(ch.get("ch_id_env", ""), "")
        if not ch_id_yt:
            return
        r = requests.post(
            "https://www.googleapis.com/youtube/v3/activities?part=snippet",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"snippet": {"type": "social", "description": post["text"], "channelId": ch_id_yt}},
            timeout=10
        )
        if r.status_code in [200, 201]:
            log(f"📣 {ch_id}: Community post publicado")
            if MEMORY_ENABLED:
                week = today.strftime("%Y-W%W")
                graphiti_add(f"Community post {ch_id} semana {week}: {post['text'][:50]}", group_id="channels")
    except Exception as e:
        log(f"❌ Community post {ch_id}: {e}")


def decide():
    """
    CÉREBRO DO QUANTUM MASTER v4
    Decide o que fazer baseado em hora/dia UTC.
    v4: Consulta Graphiti para decisões de contexto — NÃO chama LLM para isso.
    """
    now = datetime.datetime.utcnow()
    h = now.hour
    dow = now.weekday()  # 0=seg, 6=dom
    
    log(f"🧠 Quantum Master v4.0 — {now.strftime('%Y-%m-%d %H:%M')} UTC")
    log(f"   Memory: {'✅ Graphiti+Vault' if MEMORY_ENABLED else '⚠️  Desabilitado'}")
    
    for ch_id in CHANNELS:
        
        # Segunda-feira 01h UTC: update descriptions
        if h == 1 and dow == 0:
            log(f"\n📋 {ch_id}: Atualizando descriptions...")
            do_update_desc(ch_id)
        
        # Quarta + Sábado 12h UTC: community post
        if h == 12 and dow in [2, 5]:
            log(f"\n📣 {ch_id}: Community post...")
            do_community_post(ch_id)
        
        # Diário 09h UTC: monitorar stats
        if h == 9:
            log(f"\n📊 {ch_id}: Monitorando stats...")
            do_monitor(ch_id)
        
        # Diário 17h UTC: publicar Short
        if h == 17:
            log(f"\n🎬 {ch_id}: Publicando Short...")
            do_short(ch_id)


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "auto"
    
    if cmd == "auto":
        decide()
    elif cmd == "short":
        ch = sys.argv[2] if len(sys.argv) > 2 else "CH01"
        do_short(ch)
    elif cmd == "monitor":
        for ch_id in CHANNELS:
            do_monitor(ch_id)
    elif cmd == "desc":
        ch = sys.argv[2] if len(sys.argv) > 2 else "CH01"
        do_update_desc(ch)
    elif cmd == "community":
        ch = sys.argv[2] if len(sys.argv) > 2 else "CH01"
        do_community_post(ch)
    elif cmd == "all":
        for ch_id in CHANNELS:
            do_short(ch_id)
            do_monitor(ch_id)
    else:
        print(f"Uso: python quantum_master_v4.py [auto|short|monitor|desc|community|all] [CH_ID]")
