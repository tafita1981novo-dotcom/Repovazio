#!/usr/bin/env python3
"""
affiliate_ugc_engine.py — Sistema Automático de Afiliados com UGC IA
Replica o workflow do vídeo: Pesquisa → Produto → Vídeo UGC → Post → Comissão

FLUXO:
  1. Claude pesquisa nichos lucrativos (prompt do vídeo)
  2. Encontra produto mais vendido do nicho
  3. Gera vídeo UGC realista (Higfield/HeyGen/D-ID)
  4. Adiciona legenda + música
  5. Posta em TikTok + Instagram + YouTube Shorts
  6. Coloca link afiliado na bio e descrição
  7. Rastreia comissões

IMPORTANTE: Sempre disclose conteúdo gerado por IA conforme exigido
  pelo CONAR (Brasil) e termos das plataformas.
"""

import os, json, time, requests
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════
GROQ_KEY    = os.getenv("GROQ_API_KEY", "")
NVIDIA_KEY  = os.getenv("NVIDIA_API_KEY", "")
HEYGEN_KEY  = os.getenv("HEYGEN_API_KEY", "")
DID_KEY     = os.getenv("DID_API_KEY", "")
HIGFIELD_KEY= os.getenv("HIGFIELD_API_KEY", "")

# ══════════════════════════════════════════════════════════════
# PROMPT EXATO DO VÍDEO — pesquisa de nichos BR
# ══════════════════════════════════════════════════════════════
NICHO_PROMPT = """
Aja como estrategista de elite em marketing de afiliados, especializado 
em plataformas de conteúdo de formato curto como TikTok, Instagram e Pinterest.

Encontre 5 categorias de produtos que estão em alta no momento no Brasil 
e que têm forte potencial de monetização via afiliados.

Para cada categoria, forneça:
- Por que performa bem em vídeo curto
- Tipo de público que compra
- Faixa estimada de comissão (Shopee/Amazon/Hotmart)
- Estilo de vídeo com melhor conversão (UGC, demonstração, antes/depois)
- Hooks que costumam performar melhor
- Se é melhor para impulso (baixo ticket) ou comissão alta (alto ticket)
- Quão saturado está atualmente
- Ângulo mais fácil para iniciantes

Classifique as 5 categorias por:
1. Potencial de ganhos
2. Facilidade de criar conteúdo viral
3. Amigável para iniciantes
4. Escalabilidade a longo prazo

Foca em categorias performando bem em 2025/2026.
Análise prática, focada em oportunidades REAIS de ganhar dinheiro.
Responda em JSON com estrutura:
{
  "nichos": [
    {
      "categoria": "nome",
      "ranking": 1,
      "comissao_media": "5-20%",
      "plataformas": ["Shopee", "Amazon"],
      "tipo_video": "UGC demonstração",
      "hooks_top": ["hook 1", "hook 2"],
      "ticket": "baixo/alto",
      "saturacao": "baixa/media/alta",
      "facilidade": 8,
      "por_que_funciona": "explicação"
    }
  ]
}
"""

PRODUTO_PROMPT_TEMPLATE = """
Você é expert em marketing de afiliados no Brasil.

Nicho escolhido: {nicho}
Plataforma de afiliados: {plataforma}

Encontre o produto MAIS VENDIDO desse nicho que:
1. Paga boa comissão como afiliado
2. Tem avaliações acima de 4.5 estrelas
3. Está em alta (viralizando) agora
4. Tem imagem de produto disponível publicamente

Responda em JSON:
{{
  "produto": "nome completo",
  "marca": "nome da marca",
  "preco": "R$ XX",
  "comissao": "X%",
  "link_produto": "url",
  "imagem_url": "url da imagem oficial",
  "beneficios_top3": ["b1", "b2", "b3"],
  "publico": "descrição do comprador típico",
  "motivo_viral": "por que está viralizando"
}}
"""

VIDEO_PROMPT_TEMPLATE = """
Crie um vídeo UGC natural de afiliado de 15 segundos em formato vertical 9x16.

Produto: {produto}
Marca: {marca}
Benefícios: {beneficios}

Especificações:
- Use modelo Sidence 2.0 para movimentos ultra-realistas
- Estética Clean Beauty Premium (para beleza) / Lifestyle autêntico (geral)
- Iluminação suave e realista
- Aparência orgânica e emocionalmente autêntica

Fluxo do vídeo:
1. (0-3s) HOOK: {hook} — câmera selfie, pessoa natural, expressão genuína
2. (3-8s) PROBLEMA: mostrar frustração/dificuldade relacionada
3. (8-12s) SOLUÇÃO: aplicar/usar o produto naturalmente
4. (12-15s) RESULTADO: expressão de satisfação + produto visível

Tom: autocuidado genuíno, não comercial, como vídeo espontâneo do TikTok

IMPORTANTE: Este é conteúdo criado por IA. Adicionar #ad ou #publi e
texto "conteúdo gerado por IA" conforme regulamentação CONAR/FTC.

Descrição cena por cena para geração do vídeo IA:
"""

# ══════════════════════════════════════════════════════════════
# FUNÇÕES DO SISTEMA
# ══════════════════════════════════════════════════════════════

def pesquisar_nicho(llm_key: str = None) -> dict:
    """Usa LLM para pesquisar nichos lucrativos como no vídeo"""
    
    key = llm_key or GROQ_KEY or NVIDIA_KEY
    if not key:
        print("⚠️  Configure GROQ_API_KEY ou NVIDIA_API_KEY")
        return {}
    
    # Tenta Groq primeiro (mais rápido)
    if GROQ_KEY:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        model = "llama-3.3-70b-versatile"
    else:
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"}
        model = "deepseek-ai/deepseek-r1-distill-llama-70b"
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": NICHO_PROMPT}],
        "max_tokens": 2000,
        "response_format": {"type": "json_object"}
    }
    
    print("🔍 Pesquisando nichos lucrativos no Brasil...")
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    
    if r.status_code == 200:
        content = r.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    else:
        print(f"❌ LLM erro: {r.status_code}")
        return {}

def encontrar_produto(nicho: str, plataforma: str = "Shopee") -> dict:
    """Encontra produto mais vendido do nicho"""
    
    if not (GROQ_KEY or NVIDIA_KEY): return {}
    
    prompt = PRODUTO_PROMPT_TEMPLATE.format(nicho=nicho, plataforma=plataforma)
    
    if GROQ_KEY:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        model = "llama-3.3-70b-versatile"
    else:
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"}
        model = "deepseek-ai/deepseek-r1-distill-llama-70b"
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "response_format": {"type": "json_object"}
    }
    
    print(f"🛍️  Encontrando produto top do nicho: {nicho}...")
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    
    if r.status_code == 200:
        content = r.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    return {}

def gerar_prompt_video(produto: dict, hook: str) -> str:
    """Gera o prompt de vídeo UGC exatamente como no workflow do vídeo"""
    
    return VIDEO_PROMPT_TEMPLATE.format(
        produto=produto.get("produto", ""),
        marca=produto.get("marca", ""),
        beneficios=", ".join(produto.get("beneficios_top3", [])),
        hook=hook
    )

def gerar_video_higfield(prompt: str, produto_img: str = None) -> dict:
    """Gera vídeo via Higfield API (quando conectado via MCP)"""
    
    if not HIGFIELD_KEY:
        print("⚠️  HIGFIELD_API_KEY não configurada")
        print("   → Configure em hixsfield.ai/mcp para usar via Claude Desktop")
        return {"status": "pending_mcp_setup"}
    
    # Endpoint Higfield (baseado na documentação MCP)
    url = "https://api.hixsfield.ai/v1/videos/generate"
    headers = {"Authorization": f"Bearer {HIGFIELD_KEY}", "Content-Type": "application/json"}
    
    payload = {
        "prompt": prompt,
        "model": "sidence-2.0",
        "aspect_ratio": "9:16",
        "duration": 15,
        "style": "ugc_natural"
    }
    
    if produto_img:
        payload["reference_image"] = produto_img
    
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    return r.json() if r.status_code == 200 else {"error": r.text}

def gerar_video_heygen(prompt: str, avatar_id: str = "Angela-inTshirt-20220820") -> dict:
    """Alternativa: gerar vídeo via HeyGen (quando Higfield não disponível)"""
    
    if not HEYGEN_KEY:
        return {"status": "sem_key_heygen"}
    
    url = "https://api.heygen.com/v2/video/generate"
    headers = {"X-Api-Key": HEYGEN_KEY, "Content-Type": "application/json"}
    
    payload = {
        "video_inputs": [{
            "character": {"type": "avatar", "avatar_id": avatar_id, "avatar_style": "normal"},
            "voice": {"type": "text", "input_text": prompt[:500], "voice_id": "pt_BR_female_1"},
            "background": {"type": "color", "value": "#F5F5F5"}
        }],
        "dimension": {"width": 720, "height": 1280},
        "aspect_ratio": "9:16"
    }
    
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    return r.json() if r.status_code == 200 else {"error": r.text}

def gerar_video_did(script: str, imagem_presenter: str = None) -> dict:
    """Alternativa: D-ID para talking head realista"""
    
    if not DID_KEY:
        return {"status": "sem_key_did"}
    
    url = "https://api.d-id.com/talks"
    headers = {"Authorization": f"Basic {DID_KEY}", "Content-Type": "application/json"}
    
    payload = {
        "script": {"type": "text", "input": script[:300], "provider": {"type": "elevenlabs"}},
        "config": {"fluent": True, "pad_audio": 0.0}
    }
    
    if imagem_presenter:
        payload["source_url"] = imagem_presenter
    
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    return r.json() if r.status_code == 200 else {"error": r.text}

def gerar_link_afiliado(produto_url: str, plataforma: str = "shopee") -> str:
    """Gera link afiliado para o produto — LEGAL e obrigatório divulgar #publi"""
    
    # Cada plataforma tem seu próprio sistema de geração de deep link
    templates = {
        "shopee":   f"https://s.shopee.com.br/affiliate?url={produto_url}&affid=SEU_ID",
        "amazon":   f"https://amzn.to/XXXXX?tag=SEU_TAG",
        "hotmart":  f"https://go.hotmart.com/SEU_ID",
        "mercadolivre": f"https://go.meli.com/SEU_ID"
    }
    
    return templates.get(plataforma, produto_url)

def salvar_workflow(nicho: dict, produto: dict, prompt_video: str, video_result: dict):
    """Salva todo o workflow no Supabase para tracking"""
    
    SB_URL = "https://tpjvalzwkqwttvmszvie.supabase.co"
    SB_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    if not SB_KEY: return
    
    record = {
        "nicho": nicho.get("categoria", ""),
        "produto": produto.get("produto", ""),
        "comissao": produto.get("comissao", ""),
        "prompt_video": prompt_video[:500],
        "video_status": video_result.get("status", "pending"),
        "video_url": video_result.get("video_url", ""),
        "data_criacao": datetime.now().isoformat()
    }
    
    headers = {
        "apikey": SB_KEY,
        "Authorization": f"Bearer {SB_KEY}",
        "Content-Type": "application/json"
    }
    
    requests.post(
        f"{SB_URL}/rest/v1/affiliate_campaigns",
        headers=headers,
        json=record,
        timeout=15
    )

# ══════════════════════════════════════════════════════════════
# EXECUÇÃO PRINCIPAL
# ══════════════════════════════════════════════════════════════
def run_full_workflow():
    """Roda o workflow completo do vídeo de ponta a ponta"""
    
    print("\n⚡ AFFILIATE UGC ENGINE — Workflow Completo")
    print("=" * 60)
    
    # PASSO 1: Pesquisar nichos (como no vídeo)
    resultado = pesquisar_nicho()
    if not resultado:
        print("❌ Falhou na pesquisa de nichos. Configure as keys.")
        return
    
    nichos = resultado.get("nichos", [])
    print(f"\n✅ {len(nichos)} nichos encontrados:")
    for n in nichos[:3]:
        print(f"  #{n.get('ranking','?')} {n.get('categoria','?')} — {n.get('comissao_media','?')} comissão")
    
    # PASSO 2: Pegar nicho #1 (mais lucrativo)
    nicho_top = nichos[0] if nichos else {}
    print(f"\n🎯 Nicho escolhido: {nicho_top.get('categoria','')}")
    
    # PASSO 3: Encontrar produto top
    produto = encontrar_produto(
        nicho=nicho_top.get("categoria",""),
        plataforma=nicho_top.get("plataformas",["Shopee"])[0]
    )
    print(f"\n🛍️  Produto: {produto.get('produto','?')} — {produto.get('comissao','?')} comissão")
    
    # PASSO 4: Gerar prompt do vídeo
    hooks = nicho_top.get("hooks_top", ["Você NÃO vai acreditar no resultado"])
    prompt_video = gerar_prompt_video(produto, hooks[0])
    print(f"\n🎬 Prompt vídeo gerado: {len(prompt_video)} chars")
    
    # PASSO 5: Gerar vídeo UGC
    print("\n🎥 Gerando vídeo UGC...")
    
    if HIGFIELD_KEY:
        video = gerar_video_higfield(prompt_video, produto.get("imagem_url",""))
        print(f"  → Higfield: {video}")
    elif HEYGEN_KEY:
        video = gerar_video_heygen(prompt_video)
        print(f"  → HeyGen: {video.get('video_id','?')}")
    elif DID_KEY:
        video = gerar_video_did(prompt_video)
        print(f"  → D-ID: {video.get('id','?')}")
    else:
        print("  ⚠️  Configure Higfield/HeyGen/DID key para gerar vídeo")
        video = {"status": "keys_needed"}
    
    # PASSO 6: Gerar link afiliado  
    plataforma = nicho_top.get("plataformas",["shopee"])[0].lower()
    link_afiliado = gerar_link_afiliado(produto.get("link_produto",""), plataforma)
    print(f"\n🔗 Link afiliado: {link_afiliado}")
    
    # PASSO 7: Salvar no Supabase
    salvar_workflow(nicho_top, produto, prompt_video, video)
    
    # PASSO 8: Resumo para postar
    print("\n" + "=" * 60)
    print("📋 PRONTO PARA POSTAR:")
    print(f"  Produto: {produto.get('produto','?')}")
    print(f"  Comissão: {produto.get('comissao','?')}")
    print(f"  Hook: {hooks[0]}")
    print(f"  Caption sugerida:")
    print(f"    {hooks[0]} 😱")
    print(f"    Link na bio ⬆️")
    print(f"    #publi #ad (conteúdo gerado por IA)")
    print(f"  Link: {link_afiliado}")
    
    return {
        "nicho": nicho_top,
        "produto": produto,
        "video": video,
        "link_afiliado": link_afiliado
    }

if __name__ == "__main__":
    run_full_workflow()
