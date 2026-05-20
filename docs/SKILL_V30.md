---
name: psicologia-doc-v27
description: Use esta SKILL sempre que o usuário mencionar: psicologia.doc, repovazio, Daniela Coelho, @psidanielacoelho, canal YouTube psicologia, viral, cérebro autônomo, tokens sociais, Instagram, TikTok, WhatsApp grupos, monetização, 1000 subs, crescimento, setup tokens, espelhamento viral.
version: 30.0
date: 2026-05-20
---

**SKILL — psicologia.doc V30 YOUTUBE LINKING + SÉRIES COMPLETAS (20/mai/2026)**

## ⚠️ REGRA DE OURO — SEMPRE TESTAR ANTES

```
NUNCA liberar vídeo sem testar o #683 (narcisismo) primeiro.
Processo obrigatório:
  1. GitHub Action video_id=683, voice_version=B
  2. Verificar áudio: silencedetect + astats RMS trough = -inf
  3. Verificar imagens: cada imagem reflete a frase sendo dita
  4. SÓ após aprovação: disparar os 8 restantes
```

---

## INFRA CORE

```
Supabase: tpjvalzwkqwttvmszvie | Vercel: repovazio.vercel.app | GitHub: tafita81/Repovazio
Canal ATIVO:   UCyCkIpsVgME9yCj_oXJFheA · @psidanielacoelho · psidanielacoelho1982@gmail.com
Canal ⛔ BLOQUEADO: UCSH63tBfY6wEIdkC4u4zKdg — REMOVIDO 2026-05-07, NUNCA publicar
Script Short: scripts/render_short_george.py (V30)
Workflow Short: .github/workflows/render-short-george.yml (timeout: 45min)
```

---

## 📺 ESTRATÉGIA YOUTUBE SHORT → LONG (ALGORITMO)

### Como o YouTube Coloca o Long ao Lado do Short

O YouTube exibe o Long ao lado do Short quando:
1. **Mesmo canal** ✅ (já garantido)
2. **Related video configurado**: YouTube Studio → Short → Detalhes → "Vídeo relacionado" → colar ID do Long
3. **Mesmos keywords** no título e descrição (série + tema)
4. **Link direto** do Short para o Long na descrição

### Estrutura de Títulos (para o algoritmo reconhecer a relação)

```
SHORT:  "[Hook emocional] | [Série] S01"
LONG:   "[Série] S01 | [Subtítulo científico] (15min)"

Exemplo:
  Short: "O Narcisista Mais Perigoso Não Grita. Ele CHORA. | Narcisismo Encoberto S01"
  Long:  "Narcisismo Encoberto S01 | O Sinal Que Parece Cuidado Mas É Controle (15min)"
```

### Descrição do Short — Template com Link Específico

```
[Hook de 1-2 linhas]

▶ VÍDEO COMPLETO (15min) — [curiosity gap específico]:
https://youtube.com/watch?v=[LONG_VIDEO_ID]

👉 Canal: https://youtube.com/@psidanielacoelho

💾 Salva este vídeo para não perder.
🔔 Ativa o sino — posto toda semana.

#[serie] #psicologia #saudemental #relacionamentos
```

### Workflow YouTube Studio (após publicar)

```
1. Publicar o Long primeiro → copiar ID (ex: dQw4w9WgXcQ)
2. Publicar o Short
3. YouTube Studio → Short → Detalhes → rolar até "Vídeo relacionado"
4. Colar ID do Long → Salvar
5. YouTube mostrará o Long como card no rodapé do Short
```

### No Script (automático quando Long ID disponível)

```python
# O script V30 já inclui:
YT_LONG_ID = row[0].get("related_video_id") or ""

# Se Long ID cadastrado no Supabase:
if YT_LONG_ID:
    LONG_LINK = f"https://youtube.com/watch?v={YT_LONG_ID}"
    YT_DESC = YT_DESC.replace("https://youtube.com/@psidanielacoelho",
                               LONG_LINK + "\n\n👉 Canal: https://youtube.com/@psidanielacoelho")

# Cadastrar Long ID no Supabase:
UPDATE content_pipeline SET related_video_id = '[ID_DO_LONG]' WHERE id = [SHORT_ID];
```

---

## 📚 20 SÉRIES × 10 EPISÓDIOS = 200 EPISÓDIOS

### As 20 Séries (todas no Supabase: content_series)

| # | Slug | Série | Foco |
|---|------|-------|------|
| 1 | narcisismo | Narcisismo Encoberto | Reconhecer e sobreviver |
| 2 | apego | Estilos de Apego | Por que você ama como ama |
| 3 | gaslighting | Gaslighting e Manipulação | Realidade distorcida |
| 4 | infancia | Feridas de Infância | Família disfuncional |
| 5 | ansiedade | Ansiedade Invisível | Alto funcional |
| 6 | depressao | Depressão Silenciosa | A que sorri |
| 7 | limites | Limites Saudáveis | Dizer não sem culpa |
| 8 | autoestima | Autoestima e Autossabotagem | Por que você sabota |
| 9 | relacionamentos | Padrões Tóxicos | O que você repete |
| 10 | codependencia | Codependência Emocional | Amor que sufoca |
| 11 | impostor | Síndrome do Impostor | Medo de ser descoberto |
| 12 | abandono | Medo de Abandono | Apego ansioso extremo |
| 13 | cura | Processo de Cura | Não é linear |
| 14 | amorporprio | Amor Próprio Real | Além do Instagram |
| 15 | trauma | Trauma Complexo | Mora no corpo |
| 16 | manipulacao | Técnicas de Manipulação | Reconhecer antes |
| 17 | cerebro | Neurociência das Emoções | Por que você reage assim |
| 18 | vicoemocional | Vício Emocional | A química do amor que dói |
| 19 | familia | Família Disfuncional | Dinâmicas ocultas |
| 20 | resiliencia | Resiliência e Recomeço | Florescer após o fundo |

### Arco de 10 Episódios por Série (LOCKED)

| E | Fase | Descrição | Função |
|---|------|-----------|--------|
| 01 | GANCHO | O Problema Que Ninguém Nomeia | Identificação + viral |
| 02 | PROBLEMA | Por Que É Mais Sério | Profundidade + retenção |
| 03 | CIENCIA | O Que a Ciência Diz | Autoridade + pesquisadores |
| 04 | CUSTO | O Custo Invisível | Urgência + stakes |
| 05 | VIRADA | A Virada | Esperança + turning point |
| 06 | FERRAMENTA | O Que Realmente Funciona | Valor prático |
| 07 | PRATICA | Como Colocar em Prática | Implementação |
| 08 | RECAIDA | Quando Você Regride | Normalização + retenção |
| 09 | TRANSFORMACAO | Depois da Cura | Aspiração |
| 10 | FINAL | Fechamento e Próxima Série | Cliffhanger → próxima série |

### Sequência de Publicação Recomendada

```
Semana 1: Narcisismo E01 Short → Narcisismo E01 Long
Semana 2: Depressão E01 Short → Depressão E01 Long
Semana 3: Gaslighting E01 Short → Gaslighting E01 Long
Semana 4: Narcisismo E02 Short → Narcisismo E02 Long
(retornar à mesma série cria audience que espera os próximos episódios)
```

---

## 🎤 PIPELINE DE ÁUDIO — CHATTERBOX GEORGE CLONE (PADRÃO DEFINITIVO)

### Stack de Voz

```
PRIORIDADE 1: ElevenLabs George (JBFqnCBsd6RMkjVDRZzb)
  stability=0.20, similarity_boost=0.85, style=0.70, speed=1.0
  → Usar quando ELEVENLABS_API_KEY válida com quota

PRIORIDADE 2: Chatterbox Multilingual (MIT, grátis, ilimitado) ← PADRÃO ATUAL
  pip install torch (cpu) + chatterbox-tts
  Referência: v683_george_1779065193.mp4 (14s áudio limpo)
  63.75% preferem ao ElevenLabs em testes cegos

PRIORIDADE 3: AntonioNeural EdgeTTS (emergência)
  pt-BR-AntonioNeural, rate="-12%"
```

### Extração da Referência George

```python
GEORGE_SRC = "https://tpjvalzwkqwttvmszvie.supabase.co/storage/v1/object/public/videos/mp4s/v683_george_1779065193.mp4"
subprocess.run(["ffmpeg","-y","-i",src,"-ss","2","-t","14",
    "-vn","-ar","22050","-ac","1",
    "-af","highpass=f=80,lowpass=f=8000,volume=1.3", george_ref_wav])
```

---

## 🎭 NARRAÇÃO HUMANA — GRUPOS SEMÂNTICOS V2

**Fórmula: gancho → PAUSA DRAMÁTICA → twist → PAUSA → revelação → CTA**

### Parâmetros por Tipo de Linha

```python
TIPOS = {
    "IMPACTO":    # < 32 chars. "Ele CHORA."
        exag=0.92, cfg=0.10, sil_pre=0.9, sil_pos=1.4,
    "REVELACAO":  # "Isso tem NOME.", "Isso se chama"
        exag=0.90, cfg=0.11, sil_pre=0.6, sil_pos=1.2,
    "PAUSA":      # "E quando você tenta..." (reticências)
        exag=0.85, cfg=0.14, sil_pre=0.3, sil_pos=1.0,
    "CTA":        # "SALVA agora", "No vídeo completo..."
        exag=0.72, cfg=0.28, sil_pre=0.8, sil_pos=0.0,
    "NORMAL":     # demais frases
        exag=0.80, cfg=0.16, sil_pre=0.0, sil_pos=0.7,
}
```

### Pausas de Respiração (humanização)

```python
# Entre grupos semânticos: respiração natural de 0.3-0.9s
# Pausa máxima antes de IMPACTO: 0.9s (cria antecipação)
# Pausa máxima depois de IMPACTO: 1.4s (dá peso)
# Inspiração (0.1s) entre parágrafos longos → humano real
```

---

## 🔇 PIPELINE DE SILÊNCIO LIMPO (PERMANENTE)

```python
# SEMPRE usar pcm_s16le — zeros absolutos
subprocess.run(["ffmpeg","-y","-f","lavfi",
    "-i",f"anullsrc=r={SR}:cl=mono",
    "-t",str(secs),"-ar",str(SR),
    "-acodec","pcm_s16le","-f","wav", path])

# Fade 20ms in / 30ms out por segmento
subprocess.run(["ffmpeg","-y","-i",gpath,
    "-af","afade=t=in:st=0:d=0.02,afade=t=out:st={fade_out_start:.4f}:d=0.03",
    gpath_fade])

# Noise gate no output final
subprocess.run(["ffmpeg","-y","-i",raw_wav,
    "-af","highpass=f=80,agate=threshold=0.018:ratio=1000:attack=3:release=150",
    "-codec:a","libmp3lame","-b:a","256k", mp3_out])
```

### Verificação Obrigatória

```bash
# RMS trough deve ser -inf (silêncio digital perfeito)
ffmpeg -i audio.wav -af "astats=metadata=1" -f null - 2>&1 | grep "RMS trough"
# ESPERADO: "RMS trough dB: -inf" ✅
```

---

## 🖼️ IMAGEM PERFEITA — SINCRONIZAÇÃO COM ÁUDIO

**Cada imagem reflete EXATAMENTE o que está sendo dito no áudio**

```python
def prompt_for_frase(frase, idx, n_total):
    t = frase.lower()

    # Personagem por emoção da frase
    if any(k in t for k in ["grita","bate","perigoso","calculista","controle"]):
        char = MARCOS + " villainous expression, dark aura"
    elif any(k in t for k in ["chora","triste","culpada","errada","machucada","confusa"]):
        char = SARA + " crying, confused, hurt expression"
    elif any(k in t for k in ["salva","canal","assiste","inscrev","sino","vídeo"]):
        char = DANIELA + " pointing to camera, warm smile, golden bell 🔔"
    elif any(k in t for k in ["harvard","ciência","pesquisa","estudo","neurológ","clinica"]):
        char = ANA + " pointing at whiteboard, scientific diagram"
    elif any(k in t for k in ["não está exagerando","você não é","normal","ajuda"]):
        char = DANIELA + " caring, empowering gesture toward viewer"
    elif any(k in t for k in ["isso tem nome","mecanismo","padrão","comportamento","chama"]):
        char = ANA + " with labeled diagram, serious expression"
    elif any(k in t for k in ["afastar","terminar","sair","deixar","ir embora"]):
        char = SARA + " trying to leave, being held back"
    else:
        char = DANIELA + " speaking directly, engaged expression"

    scene = frase[:60].lower()
    return (
        f"{char}, {STYLE}, "
        f"scene: {scene}, "
        f"vertical composition 9:16, close-up emotional moment, "
        f"no text, no watermarks"
    )
```

### Exemplos de Sincronização Perfeita

```
"O narcisista mais PERIGOSO da sua vida não grita." → Marcos sorrindo sinistro
"Ele CHORA."                                        → Marcos com lágrimas, manipulador
"você é quem está ERRADA."                          → Sara confusa, culpada
"Isso tem NOME."                                    → Dra. Ana com clipboard
"No vídeo completo eu mostro X..."                  → Daniela pointing, curiosidade
"SALVA agora para não perder."                      → Daniela + sino dourado 🔔
```

---

## 📋 SCRIPTS V30 — ESTRUTURA (70% VALOR + CURIOSITY GAP ESPECÍFICA)

```
[Hook emocional — para o scroll]
[Revelação parcial — entrega valor real]
[Curiosity gap: "No vídeo completo eu mostro X ESPECÍFICO"]
[CTA: "SALVA agora para não perder."]
```

### Os 9 Shorts Prontos (status: pending_credentials)

| ID | Tema | Hook | Long ID pendente |
|----|------|------|-----------------|
| 683 | Narcisismo | "Ele CHORA" | configurar |
| 682 | Celular/vício | "Ansiedade no peito" | configurar |
| 684 | Ansiedade alto funcional | "Sofia dormia DUAS HORAS" | configurar |
| 688 | Colapso neurológico | "Lucas não conseguia sair da cama" | configurar |
| 689 | Síndrome do impostor | "Medo de ser DESCOBERTO" | configurar |
| 701 | Depressão silenciosa | "Ela ria nas reuniões" | configurar |
| 710 | Gaslighting | "Aquilo NUNCA aconteceu" | configurar |
| 711 | Ex/vício emocional | "Cabeça NÃO PARA" | configurar |
| 712 | Família imatura | "Sensível demais" | configurar |

---

## 🎬 PIPELINE COMPLETO — CHECKLIST

```
PRÉ-RENDER:
  □ Script com CAPS nas ênfases
  □ youtube_title e youtube_description no Supabase
  □ series_slug e ep_number corretos

RENDER:
  □ video_id=683 PRIMEIRO (testar)
  □ voice_version=B
  □ Verificar logs: "Narração final: XXs | Chatterbox"
  □ Verificar logs: "Imagens válidas: 7/7"

PÓS-RENDER:
  □ RMS trough = -inf ✅
  □ silencedetect detecta pausas
  □ Cada imagem certa para a frase

PUBLICAÇÃO (quando YouTube OAuth disponível):
  □ Publicar Long PRIMEIRO → copiar ID
  □ Cadastrar Long ID: UPDATE content_pipeline SET related_video_id='[ID]' WHERE id=[SHORT_ID]
  □ Publicar Short
  □ YouTube Studio → Short → Vídeo relacionado → ID do Long
  □ Horário: 18-20h BR | Canal: UCyCkIpsVgME9yCj_oXJFheA
```

---

## PERSONAGENS

```python
DANIELA = "kawaii chibi anime girl, short dark bob hair, mint-green blouse, gold psi pin, warm smile"
SARA    = "kawaii chibi anime girl, wavy auburn hair, round glasses, yellow cardigan, emotional eyes"
MARCOS  = "kawaii chibi anime man, styled dark hair, navy blazer, charming calculating smile"
JULIA   = "kawaii chibi anime girl, curly dark hair, orange sweater, warm caring expression"
ANA     = "kawaii chibi anime woman, dark bun, white lab coat, clipboard, authoritative calm"
STYLE   = "Psych2Go anime flat illustration, soft cream background #F5F0E8, pastel, clean line art"
```

---

## PARÂMETROS TRAVADOS V30

```python
EXAG_IMPACTO  = 0.92   # drama máximo
CFG_IMPACTO   = 0.10   # fala mais lenta
SIL_PRE_IMP   = 0.9    # 0.9s antes do impacto
SIL_POS_IMP   = 1.4    # 1.4s depois do impacto
EXAG_NORMAL   = 0.80
CFG_NORMAL    = 0.16
NOISE_GATE    = "agate=threshold=0.018:ratio=1000:attack=3:release=150"
HIGHPASS      = "highpass=f=80"
FADE_IN       = 0.02   # 20ms
FADE_OUT      = 0.03   # 30ms
SILENCE_PCM   = "pcm_s16le"
```

---

## LLM ROUTER V4

```
1. NVIDIA deepseek-ai/deepseek-v4-pro ← DEFAULT
2. NVIDIA meta/llama-3.3-70b-instruct
3. Groq llama-3.3-70b-versatile (14.400 req/dia)
4. OpenAI gpt-4o-mini
```

---

## CREDENCIAIS

```
✅ GH_PAT, Vercel, Supabase, Groq, NVIDIA, OpenAI
⚠️ ELEVENLABS_API_KEY (quota pode estar esgotada → Chatterbox)
❌ FALTA: YouTube OAuth (psidanielacoelho1982@gmail.com), GEMINI_API_KEY
```

---

## ESTRATÉGIA R$50K/MÊS

```
RPM psicologia BR: R$10-16 | Para R$50K: 3.5M views/mês × R$15
Mês 3-4: 10K subs R$3K | Mês 9-10: 300K subs R$50K ✅
Shorts: crescimento de subs | Longs: mid-rolls E03/E06/E09 (3/6/9min)
```

---

## LINKS

- Hub: https://repovazio.vercel.app/hub.html
- Vídeos prontos: https://repovazio.vercel.app/videos-prontos.html
