#!/usr/bin/env python3
"""
GERADOR AUTOMÁTICO DE SCRIPTS — @psidanicoelho
Usa API Claude para gerar scripts seguindo regras da SKILL v100
Roda via GitHub Actions todos os dias às 22h BR
"""
import os, json, requests, time
from datetime import datetime, timezone

SUPA_URL = os.environ.get('SUPABASE_URL', '')
SUPA_KEY = os.environ.get('SUPABASE_KEY', '')
ANTHROPIC_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

HEADERS_SUPA = {
    'apikey': SUPA_KEY,
    'Authorization': f'Bearer {SUPA_KEY}',
    'Content-Type': 'application/json'
}

# ============================================================
# REGRAS ETERNAS — NUNCA MUDAR
# ============================================================
REGRAS_SISTEMA = """
REGRAS ABSOLUTAS (NUNCA VIOLAR):
1. Daniela Coelho = "estudiosa da mente humana" — JAMAIS "psicóloga"
2. Emma (EN) = "Human Behavior Researcher" — NUNCA credencial clínica
3. Hook = PERIGO QUE PARECE SEGURO — nunca pergunta genérica
4. Pesquisador REAL com universidade real
5. Short 58s = exatamente 20 frases ~42 chars
6. Long 15min = 5 segmentos narrativos + 4 mid-rolls
7. Final = devolve poder (NUNCA vitimiza)
"""

NICHOS_PRIORITARIOS = [
    {"nicho": "narcisismo", "lingua": "pt", "canal": "psidanicoelho", 
     "pesquisadores": ["Craig Malkin PhD Harvard", "Ramani Durvasula PhD California"],
     "cpm_usd": 2.5, "afiliado": "hotmart_codependencia_60"},
    
    {"nicho": "gambling", "lingua": "en", "canal": "en_faceless_psych",
     "pesquisadores": ["Clark Cambridge 2009 near miss", "Kahneman Nobel loss aversion", "Langer Harvard illusion of control"],
     "cpm_usd": 11.0, "afiliado": "betterhelp_150+brightquest_100"},
    
    {"nicho": "gaming", "lingua": "en", "canal": "en_faceless_psych",
     "pesquisadores": ["Skinner Harvard variable ratio", "APA 2024 prefrontal cortex", "Sedikides Southampton self-esteem"],
     "cpm_usd": 11.0, "afiliado": "bark_parental_40+game_quitters_40"},
    
    {"nicho": "trauma", "lingua": "en", "canal": "en_faceless_psych",
     "pesquisadores": ["van der Kolk Boston Medical", "Ainsworth attachment", "Bessel van der Kolk Body Keeps the Score"],
     "cpm_usd": 12.0, "afiliado": "betterhelp_150"},
    
    {"nicho": "sono", "lingua": "pt", "canal": "psidanicoelho",
     "pesquisadores": ["Matthew Walker Berkeley", "Siegel UCLA polyvagal"],
     "cpm_usd": 2.5, "afiliado": "oura_ring_45"},
    
    {"nicho": "dark_psych", "lingua": "en", "canal": "en_faceless_psych",
     "pesquisadores": ["Cialdini influence", "Kahneman heuristics", "Milgram obedience"],
     "cpm_usd": 12.0, "afiliado": "betterhelp_150"},
    
    {"nicho": "money_psychology", "lingua": "pt", "canal": "psidanicoelho",
     "pesquisadores": ["Kahneman Nobel prospect theory", "Thaler Nobel nudge", "Ariely Duke predictably irrational"],
     "cpm_usd": 5.0, "afiliado": "amazon_br_kahneman"},
]

FORMULAS_VIRAIS = [
    ("N Sinais + [condição oculta]", "CTR 8-12%", "Psych2Go 28M views"),
    ("Por Que [comportamento] Foi Projetado Para Viciar", "CTR 9-14%", "gambling hook"),
    ("Harvard Descobriu Por Que [você não consegue parar]", "CTR 10-15%", "ciência hook"),
    ("Não É [X] — É [Y neurológico]", "CTR 11-16%", "redefinição"),
    ("A Verdade Desconfortável Sobre [comportamento]", "CTR 9-13%", "revelação"),
]

def gerar_script_short(nicho_config):
    """Gera script Short 58s via API Claude"""
    nicho = nicho_config['nicho']
    lingua = nicho_config['lingua']
    pesquisadores = ", ".join(nicho_config['pesquisadores'][:2])
    canal = nicho_config['canal']
    
    prompt = f"""
{REGRAS_SISTEMA}

Gera um script Short 58s para YouTube/TikTok/Instagram.

NICHO: {nicho}
LÍNGUA: {lingua}
PESQUISADORES A CITAR: {pesquisadores}
CANAL: {canal}
PERSONAGEM: {"Daniela Coelho, estudiosa da mente humana" if lingua=="pt" else "Emma, Human Behavior Researcher"}

FORMATO OBRIGATÓRIO (20 frases EXATAS ~42 chars cada):
- Frase 1: Hook visual impactante
- Frases 2-3: Contexto do problema
- Frases 4-6: Pesquisador real + dado chocante
- Frases 7-12: Mecanismo neurológico
- Frases 13-17: Sinais práticos
- Frases 18-19: CTA produto/afiliado
- Frase 20: Identidade canal + urgência

RESPONDA APENAS JSON:
{{
  "titulo_pt": "...",
  "titulo_en": "...",
  "hook": "primeira frase...",
  "frases": ["frase1", "frase2", ..., "frase20"],
  "cenas": [
    {{"idx": 0, "personagem": "...", "emocao": "shocked|empathy|thinking|default", "prompt_pollinations": "masterpiece chibi anime..."}}
  ],
  "tts_voz": "ThalitaMultilingualNeural",
  "tts_rate": "+37%",
  "cta_produto": "bundle_{nicho}_pt_r97",
  "hashtags_tiktok": ["tag1","tag2","tag3","tag4","tag5"]
}}
"""
    
    r = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key': ANTHROPIC_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        },
        json={
            'model': 'claude-sonnet-4-6',
            'max_tokens': 2000,
            'messages': [{'role': 'user', 'content': prompt}]
        },
        timeout=60
    )
    
    if not r.ok:
        print(f"  ❌ API erro: {r.status_code}")
        return None
    
    content = r.json()['content'][0]['text']
    
    # Parse JSON da resposta
    try:
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            script_data = json.loads(json_match.group())
            return script_data
    except Exception as e:
        print(f"  ❌ Parse erro: {e}")
    
    return None


def inserir_script_no_banco(script_data, nicho_config):
    """Insere script gerado no Supabase video_scripts"""
    nicho = nicho_config['nicho']
    lingua = nicho_config['lingua']
    
    frases = script_data.get('frases', [])
    script_tts = ". ".join(frases)
    
    payload = {
        'titulo_pt': script_data.get('titulo_pt', f'[Auto] {nicho} PT'),
        'titulo_en': script_data.get('titulo_en', f'[Auto] {nicho} EN'),
        'tipo': 'short_58s',
        'topico': nicho,
        'nicho': nicho,
        'lingua': lingua,
        'plataforma': ['youtube', 'instagram', 'tiktok'],
        'personagem_principal': 'daniela_host' if lingua == 'pt' else 'emma_en_host',
        'hook_texto': script_data.get('hook', frases[0] if frases else ''),
        'script_completo': script_tts,
        'cenas_json': json.dumps(script_data.get('cenas', [])),
        'tts_voz': script_data.get('tts_voz', 'ThalitaMultilingualNeural'),
        'tts_rate': '+37%',
        'duracao_estimada_s': 58,
        'cta_produto': script_data.get('cta_produto', ''),
        'cta_afiliado': nicho_config.get('afiliado', ''),
        'hashtags_tiktok': script_data.get('hashtags_tiktok', []),
        'virality_score': 8,
        'status': 'script_pronto',
        'semana': datetime.now().isocalendar()[1]
    }
    
    r = requests.post(
        f'{SUPA_URL}/rest/v1/video_scripts',
        headers=HEADERS_SUPA,
        json=payload
    )
    
    if r.ok:
        print(f"  ✅ Script inserido: {payload['titulo_pt'][:50]}")
        return True
    else:
        print(f"  ❌ Erro inserir script: {r.status_code} {r.text[:200]}")
        return False


def main():
    print("🧠 Gerador Automático de Scripts — @psidanicoelho")
    print(f"⏰ {datetime.now(timezone.utc).isoformat()}")
    
    # Verificar quantos scripts já existem prontos
    r = requests.get(
        f'{SUPA_URL}/rest/v1/video_scripts?status=eq.script_pronto&select=count',
        headers={**HEADERS_SUPA, 'Prefer': 'count=exact', 'Range': '0-0'}
    )
    
    scripts_prontos = int(r.headers.get('Content-Range', '0/0').split('/')[-1] or 0)
    print(f"📊 Scripts prontos na fila: {scripts_prontos}")
    
    # Manter pelo menos 6 scripts na fila
    TARGET_SCRIPTS = 10
    scripts_a_gerar = max(0, TARGET_SCRIPTS - scripts_prontos)
    
    if scripts_a_gerar == 0:
        print("✅ Fila suficiente. Nada a gerar.")
        return
    
    print(f"🔄 Gerando {scripts_a_gerar} novos scripts...")
    
    gerados = 0
    for i, nicho_config in enumerate(NICHOS_PRIORITARIOS):
        if gerados >= scripts_a_gerar:
            break
        
        print(f"\n📝 Gerando script {i+1}: {nicho_config['nicho']} ({nicho_config['lingua']})")
        
        script_data = gerar_script_short(nicho_config)
        if script_data:
            if inserir_script_no_banco(script_data, nicho_config):
                gerados += 1
        
        time.sleep(3)  # Rate limit
    
    print(f"\n✅ Geração completa: {gerados} scripts adicionados")


if __name__ == '__main__':
    main()
