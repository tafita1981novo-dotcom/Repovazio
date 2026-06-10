-- QUANTUM BRAIN — Tabelas Supabase (free tier)
-- Rodar no Supabase SQL Editor: app.supabase.com → SQL Editor → New Query

-- Log de conteúdo publicado
CREATE TABLE IF NOT EXISTS content_log (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  date        DATE NOT NULL DEFAULT CURRENT_DATE,
  titulo      TEXT NOT NULL,
  video_id    TEXT,
  platform    TEXT DEFAULT 'youtube',
  status      TEXT DEFAULT 'generated',
  views       INT  DEFAULT 0,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Log de ganhos diários
CREATE TABLE IF NOT EXISTS earnings_log (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  date        DATE NOT NULL DEFAULT CURRENT_DATE,
  source      TEXT NOT NULL,   -- adsense | affiliate | service | product
  platform    TEXT,
  revenue     FLOAT DEFAULT 0,
  currency    TEXT DEFAULT 'USD',
  payment_via TEXT DEFAULT 'wise',
  notes       TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Programas de afiliado cadastrados
CREATE TABLE IF NOT EXISTS affiliate_programs (
  id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  nome         TEXT NOT NULL,
  url_cadastro TEXT,
  comissao     TEXT,
  nichos       TEXT[],
  pagamento    TEXT,
  active       BOOLEAN DEFAULT TRUE,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Padrões de monetização descobertos
CREATE TABLE IF NOT EXISTS money_patterns (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  platform      TEXT,
  pattern       TEXT,
  revenue_daily FLOAT DEFAULT 0,
  confidence    FLOAT DEFAULT 0.5,
  active        BOOLEAN DEFAULT TRUE,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Dados de exemplo para testar
INSERT INTO earnings_log (date, source, platform, revenue, payment_via) VALUES
  (CURRENT_DATE - 1, 'adsense',   'youtube',   4.20,  'adsense'),
  (CURRENT_DATE - 1, 'affiliate', 'clickbank', 47.00,  'wise'),
  (CURRENT_DATE - 2, 'adsense',   'youtube',   3.80,  'adsense'),
  (CURRENT_DATE - 2, 'affiliate', 'impact',    25.00,  'wise');

SELECT 'Tabelas criadas com sucesso!' AS status;
