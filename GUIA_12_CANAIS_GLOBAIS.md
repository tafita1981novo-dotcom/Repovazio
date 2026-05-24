# Guia: Criar 12 Canais YouTube — Multi-idioma Global
## Sistema psicologia.doc | tafita81@gmail.com

---

## RECEITA POTENCIAL TOTAL (após 1K subs cada canal)

| Idioma | Canal | CPM | Buscas/mês 528Hz | Receita potencial |
|--------|-------|-----|-----------------|-------------------|
| EN | @psychologyfrequencies | $28 | 22M | $2.000-8.000/mês |
| DE | @psychologiefrequenzen | $18 | 4M  | $800-3.000/mês |
| JA | @psychfreqjp           | $15 | 5M  | $700-2.500/mês |
| FR | @psychologiefrequences | $14 | 3M  | $600-2.000/mês |
| KO | @psychfreqkr           | $12 | 3M  | $500-1.800/mês |
| IT | @psicologiafrequenze   | $12 | 2M  | $500-1.800/mês |
| ZH | @psychfreqzh           | $10 | 8M  | $400-1.500/mês |
| ES | @psicologiafrecuencias |  $9 | 9M  | $400-1.200/mês |
| PT | @psidanielacoelho      |  $7 | 6M  | $300-1.000/mês |
| AR | @psychfreqar           |  $6 | 4M  | $200-800/mês  |
| RU | @psychfreqru           |  $5 | 3M  | $200-700/mês  |
| HI | @psychfreqhi           |  $4 | 15M | $150-500/mês  |
| **TOTAL** | 12 canais | — | **84M/mês** | **$6.750-24.800/mês** |

---

## COMO CRIAR CADA CANAL (2 min cada, via YouTube.com)

**Importante:** YouTube não permite criar canais via API.
Cada canal é criado uma vez manualmente, depois tudo é automático.

### Processo para cada canal:

1. **Acessar:** youtube.com (logado como tafita81@gmail.com)
2. **Clicar no avatar** → "Criar canal"
3. **Tipo:** Canal com nome personalizado
4. **Nome:** Conforme a tabela acima (ex: "Psychology Frequencies")
5. **Foto:** Usar as imagens da pasta `public/` geradas pelo sistema
6. **Depois de criado:** YouTube Studio → Go Live → Stream Setup → Copiar Stream Key
7. **Adicionar no GitHub:**
   - github.com/tafita81/Repovazio → Settings → Secrets → Actions
   - Nome: `YOUTUBE_STREAM_KEY_EN` (trocar EN pelo idioma)
   - Valor: [stream key copiada]
8. **Ativar live:**
   - Actions → YouTube Live Multi-Idioma → Run workflow → idioma: EN

### Prioridade de criação (por ROI):
1. 🇺🇸 **EN** — `YOUTUBE_STREAM_KEY_EN` → $28 CPM, 22M buscas/mês
2. 🇩🇪 **DE** — `YOUTUBE_STREAM_KEY_DE` → $18 CPM, mercado premium
3. 🇯🇵 **JA** — `YOUTUBE_STREAM_KEY_JA` → $15 CPM, high retention
4. 🇫🇷 **FR** — `YOUTUBE_STREAM_KEY_FR` → $14 CPM
5. 🇧🇷 **PT** — `YOUTUBE_STREAM_KEY` → já existe @psidanielacoelho

---

## LIVE JÁ AUTOMÁTICA após adicionar stream key:

O workflow `youtube-live-global.yml` roda automaticamente no schedule:
- EN: UTC 00h (8pm EST USA)
- ES: UTC 03h (9pm CST México)
- DE: UTC 20h (9pm CET Alemanha)
- JA: UTC 12h (9pm JST Japão)
- PT: UTC 00h (9pm BRT Brasil)
- FR: UTC 20h (9pm CET França)

Todo o conteúdo (insights de psicologia, frequências, imagens) é gerado
automaticamente pelo `scripts/live_global_master.py`.

---

## TÍTULOS SEO JÁ PRONTOS (copiar no YouTube Studio)

**EN:** `🔴 528Hz SLEEP | Anxiety & Narcissism Recovery | Psychology LIVE 24/7`
**ES:** `🔴 528Hz DORMIR PROFUNDO | Ansiedad y Narcisismo | Psicología EN VIVO`
**DE:** `🔴 528Hz SCHLAF | Angst und Narzissmus Heilung | Psychologie LIVE`
**JA:** `🔴 528Hz 睡眠音楽 | 不安と自己愛性 | 心理学ライブ 24/7`
**FR:** `🔴 528Hz SOMMEIL | Anxiété et Narcissisme | Psychologie EN DIRECT`
**IT:** `🔴 528Hz SONNO | Ansia e Narcisismo Guarigione | Psicologia IN DIRETTA`
**PT:** `🔴 528Hz SONO PROFUNDO | Ansiedade e Narcisismo | Psicologia AO VIVO`
**KO:** `🔴 528Hz 수면 음악 | 불안과 자기애성 | 심리학 라이브 24/7`
**ZH:** `🔴 528Hz 深度睡眠 | 焦虑与自恋症恢复 | 心理学直播 24/7`
**AR:** `🔴 528Hz نوم عميق | القلق والنرجسية | علم النفس مباشر`
**RU:** `🔴 528Гц СОН | Тревога и Нарциссизм | Психология ПРЯМОЙ ЭФИР`
**HI:** `🔴 528Hz गहरी नींद | चिंता और मनोविज्ञान | लाइव 24/7`

---

## PARA ATIVAR O YOUTUBE (única ação técnica pendente)

Abrir logado como tafita81@gmail.com:

```
https://accounts.google.com/o/oauth2/auth?client_id=552651753048-p26lb7afjs5f75nvfrmmf4eb1ps4sc98.apps.googleusercontent.com&redirect_uri=urn:ietf:wg:oauth:2.0:oob&scope=https://www.googleapis.com/auth/youtube&response_type=code&access_type=offline&prompt=consent&login_hint=tafita81@gmail.com
```

Copiar código → colar aqui → eu faço o resto automaticamente.
