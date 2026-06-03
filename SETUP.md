# 🔑 SETUP — psicologia.doc @psidanicoelho

## ✅ Secrets Configurados (Automático)

| Secret | Status |
|--------|--------|
| SUPABASE_URL | ✅ |
| SUPABASE_SERVICE_KEY | ✅ |
| YT_REFRESH_TOKEN | ✅ |
| YT_CLIENT_ID | ✅ |
| YT_CLIENT_SECRET | ✅ |
| YT_REFRESH_TOKEN_2 | ✅ |
| YT_CLIENT_ID_2 | ✅ |
| YT_CLIENT_SECRET_2 | ✅ |
| GROQ_API_KEY | ✅ |
| ELEVENLABS_API_KEY | ✅ |

## ❌ Pendente (Ação Manual Necessária)

### 1. YOUTUBE_STREAM_KEY — Live 24/7

Sem esta chave o live-broadcast-v2 fica inativo.

**Como obter:**
1. Acesse [YouTube Studio](https://studio.youtube.com)
2. Menu lateral → **Ir ao vivo**
3. Clique em **Transmissão ao vivo** → **Gerenciar**
4. Copie a **Chave de stream** (começa com `xxxx-xxxx-xxxx-xxxx`)
5. Vá em GitHub → Settings → Secrets → Actions
6. Crie: `YOUTUBE_STREAM_KEY` com o valor copiado

### 2. Instagram da Daniela Coelho

Requer conta Business + App Meta OAuth.

**Passos:**
1. Criar conta `@psidanielacoelho` no Instagram
2. Converter para conta Profissional (Business)
3. Acessar [developers.facebook.com](https://developers.facebook.com)
4. Criar App → Instagram Graph API
5. Obter token e salvar como `INSTAGRAM_ACCESS_TOKEN`

### 3. TikTok da Daniela Coelho

**Passos:**
1. Criar conta `@psidanielacoelho` no TikTok Creator
2. Solicitar acesso à TikTok API: [developers.tiktok.com](https://developers.tiktok.com)
3. App aprovação leva ~2-4 semanas
4. Obter `client_key` e `client_secret`
5. OAuth flow → salvar como `TIKTOK_ACCESS_TOKEN`

### 4. LinkedIn da Daniela Coelho

**Passos:**
1. Criar conta LinkedIn para Daniela
2. Acessar [linkedin.com/developers](https://www.linkedin.com/developers/apps)
3. Criar App → "Share on LinkedIn"
4. OAuth 2.0 → salvar como `LINKEDIN_ACCESS_TOKEN`

---

## 🎬 Sistema Ativo

| Workflow | Frequência | Função |
|----------|-----------|--------|
| render-mp4-v3 | 5min | Render vídeos Ken Burns + TTS |
| render-hyperframes | 30min | Render HyperFrames 3D (Three.js + GSAP) |
| smart-publisher | 6x/dia | Publica em horários de pico BR |
| quality-control | 30min | QC automático (score ≥ 50) |
| auto-optimizer | 1h | Títulos A/B + EN/ES + pinned_comment |
| channel-branding | Domingo | Banner + SEO |
| live-broadcast-v2 | 4x/dia | ⚠️ INATIVO (sem YOUTUBE_STREAM_KEY) |

## 📊 Dashboard

URL: https://tpjvalzwkqwttvmszvie.supabase.co/functions/v1/dashboard

## 🎯 Próximos Vídeos (pub_order)

1. #683 — Narcisismo encoberto (score 98)
2. #682 — Celular 80 vezes/dia (score 97)
3. #693 — Gaslighting (score 97)
4. #688 — Lucas não conseguia sair da cama (score 96)
5. #701 — Depressão Silenciosa (score 88)

## 🎬 HyperFrames

Render local: `hyperframes render --workers 1`
Template: `/tmp/hf_test_10s/index.html`
Qualidade: H.264 CRF20 3500kbps + AAC 192kbps Stereo 48kHz
