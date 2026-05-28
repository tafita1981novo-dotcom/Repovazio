export const runtime = 'edge';

export const dynamic = 'force-dynamic';

const SU = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const SK = process.env.SUPABASE_SERVICE_KEY!;

const LIMITS = {
  // Groq (engine principal)
  groq_requests_per_day: 14400,    // llama-3.1-8b-instant
  groq_requests_versatile: 1000,   // llama-3.3-70b-versatile
  groq_tokens_per_minute: 6000,
  // Gemini (fallback)
  gemini_requests_per_day: 1500,
  gemini_tokens_per_day: 1_000_000,
  tokens_por_cerebro: 1350,
  tokens_por_aprender: 700,
  tokens_por_assistente: 2500,
};

async function db(path: string) {
  if (!SU || !SK) return null;
  try {
    const r = await fetch(`${SU}/rest/v1/${path}`, {
      headers: { apikey: SK, Authorization: `Bearer ${SK}`, 'Cache-Control': 'no-cache' }
    });
    return r.ok ? r.json() : null;
  } catch { return null; }
}

export async function GET() {
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const hojeISO = hoje.toISOString();
  const agora_sp = new Date().toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' });

  const [registros, aprendizado] = await Promise.all([
    db(`registros?created_at=gte.${hojeISO}&select=id,modelo,created_at`),
    db(`cerebro_aprendizado?data=gte.${hojeISO}&select=id,data`),
  ]);

  const ciclosCerebro = (registros || []).length;
  const ciclosAprender = (aprendizado || []).length;
  const requests = ciclosCerebro + ciclosAprender;

  // Tokens estimados
  const tokensCerebro = ciclosCerebro * LIMITS.tokens_por_cerebro;
  const tokensAprender = ciclosAprender * LIMITS.tokens_por_aprender;
  const tokensTotal = tokensCerebro + tokensAprender;

  // Percentuais Groq (engine principal agora)
  const pctGroqVersatile = Math.min(100, (ciclosCerebro / LIMITS.groq_requests_versatile) * 100);
  const pctGroqInstant = Math.min(100, (requests / LIMITS.groq_requests_per_day) * 100);
  // Percentuais Gemini (fallback)
  const pctGeminiReqs = Math.min(100, (requests / LIMITS.gemini_requests_per_day) * 100);
  const pctGeminiTokens = Math.min(100, (tokensTotal / LIMITS.gemini_tokens_per_day) * 100);

  // Meta: usar 80% do Groq versatile (800 req/dia de qualidade)
  const META_GROQ = 800;
  const pctMeta = Math.min(100, (ciclosCerebro / META_GROQ) * 100);
  const ciclosRestantes = Math.max(0, META_GROQ - ciclosCerebro);

  const saude = pctGroqVersatile > 90 ? 'critico' : pctGroqVersatile > 70 ? 'atencao' : 'saudavel';

  // Manter campos legados para compatibilidade com o widget existente
  return Response.json({
    status: 'ok',
    agora_sp,
    engine_principal: 'groq/llama-3.3-70b-versatile',
    engine_fallback: 'gemini-2.0-flash',
    plano: 'free',
    limites: LIMITS,
    uso_hoje: {
      ciclos_cerebro: ciclosCerebro,
      ciclos_aprender: ciclosAprender,
      requests_total: requests,
      tokens_estimados: tokensTotal,
    },
    percentuais: {
      tokens: parseFloat(pctGeminiTokens.toFixed(4)),
      requests: parseFloat(pctGeminiReqs.toFixed(4)),
      meta_85pct: parseFloat(pctMeta.toFixed(2)),
      groq_versatile: parseFloat(pctGroqVersatile.toFixed(2)),
      groq_instant: parseFloat(pctGroqInstant.toFixed(4)),
    },
    saude,
    tokens_restantes: LIMITS.gemini_tokens_per_day - tokensTotal,
    requests_restantes: LIMITS.groq_requests_versatile - ciclosCerebro,
    ciclos_restantes_hoje: ciclosRestantes,
    meta_diaria_tokens: META_GROQ,
    timestamp: new Date().toISOString(),
  });
}