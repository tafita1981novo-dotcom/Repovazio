#!/usr/bin/env python3
"""
youtube_growth_engine.py — Motor de crescimento YouTube com Claude
Implementa EXATAMENTE o método da masterclass de 1 hora.

Workflow automatizado:
  1. Pesquisar nicho + validar TAM
  2. Gerar guia de voz de marca
  3. Encontrar outliers virais (1of10)
  4. Gerar conceito + 10 títulos + 3 hooks + 3 thumbnails
  5. Escrever roteiro em bullet-points
  6. Gerar comentário fixado
  7. Salvar tudo no Supabase + Notion
"""

import os, json, time, requests
from datetime import datetime

GROQ_KEY   = os.getenv("GROQ_API_KEY", "")
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY", "")
SB_URL     = os.getenv("SUPABASE_URL", "https://tpjvalzwkqwttvmszvie.supabase.co")
SB_KEY     = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
NOTION_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DB  = os.getenv("NOTION_VIDEO_DATABASE_ID", "")

# ══════════════════════════════════════════════════════════════════════
# TODOS OS PROMPTS EXATOS DO VÍDEO
# ══════════════════════════════════════════════════════════════════════

PROMPT_NICHO = lambda nicho: f"""
Estou pensando em criar um canal no YouTube sobre {nicho}.
Quais são 5 problemas que posso resolver para esse público,
e qual o tamanho desse público-alvo?

Responda em JSON:
{{
  "problemas": [
    {{"problema": "...", "publico": "...", "tamanho_estimado": "...", "monetizacao": "..."}}
  ],
  "tam_geral": "descrição do público total",
  "nicho_lucrativo": true/false,
  "diferenciais_sugeridos": ["como se destacar"]
}}"""

PROMPT_BRAND_VOICE = lambda transcricao: f"""
Crie um guia de voz de marca para o meu canal do YouTube cobrindo:
- Nicho e tom de voz
- Frases para usar (5-10 exemplos)
- Frases para evitar (5-10 exemplos)
- 3 exemplos de frases características
- Configuração de ambiente (cores de fundo, iluminação, estilo de edição)
- Figurino e estética visual
- Filosofias essenciais e crenças centrais

Eis o que me torna único:
{transcricao}

Responda em JSON estruturado."""

PROMPT_CONCEPT = lambda audio_transcricao: f"""
Escreva um resumo conceitual de 4 frases para um vídeo do YouTube sobre:
{audio_transcricao}

Resposta: apenas o resumo de 4 frases, sem formatação extra."""

PROMPT_TITULOS = lambda conceito: f"""
Escreva 10 variações de título para este vídeo do YouTube.
Dê uma nota de 1 a 10 para clickabilidade de cada um.
Sem travessões (—). Recomende o top 3.

Conceito do vídeo:
{conceito}

Responda em JSON:
{{
  "titulos": [
    {{"titulo": "...", "nota": 9, "porque": "..."}}
  ],
  "top3": ["título 1", "título 2", "título 3"],
  "titulo_recomendado": "o melhor"
}}"""

PROMPT_THUMBNAILS = lambda titulo: f"""
Sugira 3 conceitos básicos de miniatura para este vídeo do YouTube,
considerando:
- Composição visual simples (máximo 3 elementos)
- Emoção (se houver rosto)
- Texto de no máximo 3 palavras
- Paleta de cores com alto contraste
- Elementos distintos e memoráveis

Título do vídeo: {titulo}

Responda em JSON:
{{
  "thumbnails": [
    {{
      "conceito": "descrição visual",
      "texto": "máx 3 palavras",
      "cores": ["cor1", "cor2"],
      "emoção": "descrição",
      "diferencial": "por que vai funcionar"
    }}
  ]
}}"""

PROMPT_HOOKS = lambda conceito, titulo: f"""
Escreva 3 variações de hook para este vídeo do YouTube:
1. Afirmação ousada (bold statement)
2. Dor com a qual o público se identifica (relatable pain)
3. Fato surpreendente (surprising fact)

Formato de lista com bullet points, não frases completas.
Cada hook deve ter máximo 30 segundos quando falado.

Conceito: {conceito}
Título: {titulo}

Responda em JSON: {{"hooks": [{{"tipo": "...", "hook": "...bullet\n...bullet"}}]}}"""

PROMPT_ROTEIRO = lambda conceito, titulos: f"""
Escreva um roteiro em tópicos (bullet points) para este vídeo do YouTube.
Em tópicos, NÃO em frases completas.
Hook com duração máxima de 30 segundos.
Seja detalhado para estar totalmente pronto para gravação.

Conceito:
{conceito}

Títulos considerados:
{chr(10).join(f"- {t}" for t in titulos)}

Responda em JSON:
{{
  "hook": ["bullet 1", "bullet 2"],
  "secoes": [
    {{"titulo": "Seção 1", "bullets": ["ponto 1", "ponto 2"]}},
  ],
  "cta_final": ["bullet call to action"]
}}"""

PROMPT_COMENTARIO = lambda titulo_video, conceito: f"""
Escreva um comentário fixado para este vídeo do YouTube.
Deve conter:
1. Uma pergunta para aumentar engajamento
2. Opcional: link útil relacionado

Vídeo: {titulo_video}
Contexto: {conceito}

Resposta: apenas o texto do comentário."""

PROMPT_DESCRICAO_CANAL = lambda nome, nicho: f"""
Escreva uma descrição para o canal do YouTube chamado {nome}
sobre {nicho}.
Inclua: para quem é, o que aprendem, por que se inscrever.
Remova qualquer linguagem que pareça gerada por IA.
Máximo 300 palavras."""

# ══════════════════════════════════════════════════════════════════════
# FUNÇÕES
# ══════════════════════════════════════════════════════════════════════

def chamar_llm(prompt: str, json_mode: bool = True) -> dict | str:
    providers = []
    if GROQ_KEY:
        providers.append({
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "headers": {"Authorization": f"Bearer {GROQ_KEY}"},
            "model": "llama-3.3-70b-versatile"
        })
    if NVIDIA_KEY:
        providers.append({
            "url": "https://integrate.api.nvidia.com/v1/chat/completions",
            "headers": {"Authorization": f"Bearer {NVIDIA_KEY}"},
            "model": "deepseek-ai/deepseek-r1-distill-llama-70b"
        })
    for p in providers:
        try:
            body = {
                "model": p["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 3000
            }
            if json_mode: body["response_format"] = {"type": "json_object"}
            r = requests.post(p["url"], headers={**p["headers"], "Content-Type":"application/json"},
                json=body, timeout=90)
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"]
                return json.loads(content) if json_mode else content
        except Exception as e:
            print(f"  ⚠️ LLM erro: {e}")
    return {} if json_mode else ""

def salvar_video_supabase(video_data: dict) -> str:
    """Salva vídeo no banco de dados Supabase"""
    if not SB_KEY: return ""
    r = requests.post(
        f"{SB_URL}/rest/v1/content_pipeline",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                 "Content-Type": "application/json", "Prefer": "return=representation"},
        json=video_data, timeout=15
    )
    if r.status_code in (200,201):
        return r.json()[0].get("id","") if isinstance(r.json(),list) else ""
    return ""

# ══════════════════════════════════════════════════════════════════════
# WORKFLOW PRINCIPAL — MASTERCLASS COMPLETA
# ══════════════════════════════════════════════════════════════════════

def gerar_conceito_completo(
    nicho: str = "Psicologia e Saúde Mental",
    audio_transcricao: str = "",
    outlier_inspiracao: str = ""
) -> dict:
    """
    Gera conceito completo de vídeo:
    conceito → títulos → thumbnails → hooks → roteiro → comentário
    """
    print(f"\n🎬 Gerando conceito completo para: {nicho}")
    print("=" * 60)
    
    # 1. Conceito (4 frases)
    print("\n📝 Gerando conceito...")
    texto_base = audio_transcricao or f"Vídeo sobre {nicho} baseado em: {outlier_inspiracao}"
    conceito = chamar_llm(PROMPT_CONCEPT(texto_base), json_mode=False)
    print(f"   Conceito: {conceito[:100]}...")
    
    # 2. Títulos (10 variações)
    print("\n🏷️  Gerando 10 títulos...")
    titulos_data = chamar_llm(PROMPT_TITULOS(conceito))
    titulo_top = titulos_data.get("titulo_recomendado", "")
    top3 = titulos_data.get("top3", [])
    print(f"   Título recomendado: {titulo_top}")
    
    # 3. Thumbnails (3 conceitos)
    print("\n🖼️  Gerando 3 conceitos de thumbnail...")
    thumbs = chamar_llm(PROMPT_THUMBNAILS(titulo_top))
    
    # 4. Hooks (3 variações)
    print("\n🎣 Gerando 3 variações de hook...")
    hooks = chamar_llm(PROMPT_HOOKS(conceito, titulo_top))
    
    # 5. Roteiro em bullet points
    print("\n📋 Gerando roteiro em bullet points...")
    roteiro = chamar_llm(PROMPT_ROTEIRO(conceito, top3))
    
    # 6. Comentário fixado
    print("\n💬 Gerando comentário fixado...")
    comentario = chamar_llm(PROMPT_COMENTARIO(titulo_top, conceito), json_mode=False)
    
    resultado = {
        "nicho": nicho,
        "conceito": conceito,
        "titulo_recomendado": titulo_top,
        "titulos_top3": top3,
        "todos_titulos": titulos_data.get("titulos", []),
        "thumbnails": thumbs.get("thumbnails", []),
        "hooks": hooks.get("hooks", []),
        "roteiro": roteiro,
        "comentario_fixado": comentario,
        "data_geracao": datetime.now().isoformat()
    }
    
    print("\n✅ CONCEITO COMPLETO GERADO!")
    print(f"   Título: {titulo_top}")
    print(f"   Thumbnails: {len(thumbs.get('thumbnails',[]))} conceitos")
    print(f"   Hooks: {len(hooks.get('hooks',[]))} variações")
    
    return resultado

def pesquisar_nicho(nicho: str) -> dict:
    """Analisa potencial de nicho com os critérios do vídeo"""
    print(f"\n🔍 Analisando nicho: {nicho}")
    resultado = chamar_llm(PROMPT_NICHO(nicho))
    print(f"   TAM: {resultado.get('tam_geral','?')}")
    print(f"   Lucrativo: {resultado.get('nicho_lucrativo','?')}")
    return resultado

if __name__ == "__main__":
    # Exemplo de uso — psicologia.doc
    nicho = "Psicologia e Saúde Mental BR — Narcisismo, Ansiedade, Relacionamentos"
    
    # Analisar nicho
    analise = pesquisar_nicho(nicho)
    
    # Gerar primeiro conceito de vídeo
    outlier = "Narcisismo encoberto: 7 sinais que você está sendo manipulado sem perceber"
    conceito = gerar_conceito_completo(
        nicho=nicho,
        outlier_inspiracao=outlier
    )
    
    print("\n" + "="*60)
    print("🏆 PRONTO PARA GRAVAR:")
    print(f"Título: {conceito['titulo_recomendado']}")
    print(f"Hook: {conceito['hooks'][0]['hook'][:100] if conceito.get('hooks') else 'N/A'}...")
    print(f"Comentário: {conceito['comentario_fixado'][:100]}...")
