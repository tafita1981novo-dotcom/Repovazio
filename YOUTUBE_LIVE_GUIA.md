# Guia: YouTube Live 24/7 — Monetização por Stream
## Daniela Coelho · Canal @psidanielacoelho
## Receita potencial: $1-5/hora após monetização (1K subs + 4K horas)

---

## COMO FUNCIONA

O sistema gera automaticamente:
1. **Insight de psicologia** via Groq (frase baseada em pesquisa real)
2. **Imagem kawaii** via Pollinations FLUX (gratuito, ilimitado)
3. **Overlay com texto e marca** via FFmpeg
4. **Stream RTMP** → YouTube Live 24/7

Conteúdo novo a cada 30 segundos. Completamente automático.

---

## CONFIGURAÇÃO — 5 MINUTOS

### 1. Obter Stream Key (YouTube Studio)
1. studio.youtube.com → Conteúdo → Live
2. "Programar transmissão" → Título: "Psicologia | Mente em Foco LIVE 🔴"
3. Configurações → Stream Key → Copiar

### 2. Adicionar ao GitHub
1. github.com/tafita81/Repovazio → Settings → Secrets → Actions
2. New Secret:
   - Nome: `YOUTUBE_STREAM_KEY`
   - Valor: [stream key copiada]
3. Salvar

### 3. Iniciar a Live
1. GitHub → Actions → "YouTube Live 24/7 — Psicologia Continua"
2. Run workflow → duracao_horas: `6` (ou mais)
3. Em ~2 minutos: live aparece no YouTube Studio

---

## CONFIGURAÇÃO DO VÍDEO (YouTube Studio)

### Título da Live:
```
Psicologia Ao Vivo 🔴 | Narcisismo, Ansiedade, Apego | Daniela Coelho
```

### Descrição:
```
Live de psicologia baseada em evidências 24/7.

Temas: narcisismo encoberto, apego ansioso, neurociência da ansiedade,
síndrome do impostor, burnout, gaslighting, fronteiras emocionais.

Baseado em pesquisas de: van der Kolk, Ainsworth, Gross, Neff, Malkin (Harvard).

⚠️ Conteúdo educacional. Não substitui acompanhamento profissional.

Daniela Coelho · Pesquisa e Conteúdo em Psicologia
@psidanielacoelho

🎧 Podcast: Mente em Foco (Spotify)
📧 Newsletter: [link Substack]
```

### Categoria: Educação
### Linguagem: Português
### Tags: psicologia, saude mental, ansiedade, narcisismo, apego, comportamento humano

---

## RECEITA ESPERADA

| Fase | Subs | CPM Estimado | Receita/hora live |
|------|------|-------------|------------------|
| Início | 0-500 | - | $0 (sem monetização) |
| Monetização | 1K subs + 4K h | $1-2 | $0.10-0.20 |
| Crescimento | 10K | $2-4 | $0.50-1.00 |
| Escala | 100K | $3-6 | $2-5 |

**Meta prática:** Acumular as 4.000 horas de visualização necessárias para monetização.
Live 24/7 por 1 mês = ~720 horas × visualizadores simultâneos.

---

## AUTOMAÇÃO PERMANENTE

Depois de configurar o YOUTUBE_STREAM_KEY, adicionar este cron ao workflow:

```yaml
schedule:
  - cron: "0 */6 * * *"  # a cada 6 horas
```

A live reinicia automaticamente sem intervenção.

---

## STATUS ATUAL

- ✅ Script criado: `scripts/youtube_live_24_7.py`
- ✅ Workflow criado: `.github/workflows/youtube-live-24-7.yml`
- ⏳ Faltando: `YOUTUBE_STREAM_KEY` no GitHub Secrets (5 min)
- ✅ Canal ativo: UCyCkIpsVgME9yCj_oXJFheA (@psidanielacoelho)
- ⛔ Canal bloqueado: UCSH63tBfY6wEIdkC4u4zKdg (NUNCA usar)
