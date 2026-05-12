export const dynamic = "force-dynamic";

const STACK_OFICIAL = {
  llm: [
    {nome: "Groq", env: "GROQ_API_KEY", modelo: "llama-3.3-70b-versatile", custo: "GRATIS", limite: "14.400 req/dia", url: "console.groq.com"},
    {nome: "Cerebras", env: "CEREBRAS_API_KEY", modelo: "llama-3.3-70b", custo: "GRATIS", limite: "ilimitado/dia 30/min", url: "cloud.cerebras.ai"},
    {nome: "NVIDIA NIM", env: "NVIDIA_API_KEY", modelo: "deepseek-ai/deepseek-r1", custo: "GRATIS", limite: "1.000/dia", url: "build.nvidia.com"},
    {nome: "OpenRouter", env: "OPENROUTER_API_KEY", modelo: "deepseek-r1:free", custo: "GRATIS", limite: "20/min ilimitado", url: "openrouter.ai"}
  ],
  tts: [
    {nome: "Edge TTS Microsoft", env: null, vozes: "FranciscaNeural/AntonioNeural/ThalitaNeural", custo: "GRATIS", limite: "ILIMITADO sempre", url: "github.com/rany2/edge-tts"}
  ],
  imagem: [
    {nome: "Pollinations.ai", env: null, modelo: "Flux.1 Schnell", custo: "GRATIS", limite: "ILIMITADO sem rate limit", url: "image.pollinations.ai"},
    {nome: "NVIDIA NIM", env: "NVIDIA_API_KEY", modelo: "black-forest-labs/flux.1-schnell", custo: "GRATIS", limite: "1.000/dia", url: "build.nvidia.com"},
    {nome: "Together.ai", env: "TOGETHER_API_KEY", modelo: "FLUX.1-schnell-Free", custo: "GRATIS", limite: "60/min 10.000/dia", url: "together.ai"}
  ],
  render: [
    {nome: "ffmpeg", env: null, custo: "GRATIS", limite: "ILIMITADO open source", uso: "Ken Burns + H.264 1080p 30fps"}
  ],
  transcript: [
    {nome: "Groq Whisper", env: "GROQ_API_KEY", modelo: "whisper-large-v3-turbo", custo: "GRATIS", uso: "SRT para legendas + auto-traducao"}
  ],
  hosting: [
    {nome: "Vercel", custo: "GRATIS Hobby", limite: "100GB bandwidth/mes"},
    {nome: "Supabase", custo: "GRATIS Free Tier", limite: "500MB DB + 1GB storage"},
    {nome: "GitHub Actions", custo: "GRATIS", limite: "2.000 min/mes private"}
  ],
  publicacao: [
    {nome: "YouTube Data API v3", custo: "GRATIS", limite: "10.000 quota units/dia"},
    {nome: "Meta Graph API", custo: "GRATIS", limite: "200 calls/hora"},
    {nome: "TikTok Content Posting", custo: "GRATIS", limite: "6 uploads/dia"},
    {nome: "Pinterest API v5", custo: "GRATIS", limite: "1.000 calls/hora"}
  ]
};

export async function GET() {
  const status = {};
  for (const [cat, items] of Object.entries(STACK_OFICIAL)) {
    status[cat] = items.map(i => ({
      ...i,
      configurado: i.env ? !!process.env[i.env] : true
    }));
  }

  const totalServicos = Object.values(STACK_OFICIAL).flat().length;
  const totalConfigurados = Object.values(status).flat().filter(s => s.configurado).length;
  const totalGratis = Object.values(STACK_OFICIAL).flat().filter(s => s.custo === "GRATIS" || s.custo?.includes("GRATIS")).length;

  return Response.json({
    sistema: "psicologia.doc — Stack 100% Grátis de Extrema Qualidade",
    principio: "Toda produção usa exclusivamente ferramentas grátis. Única despesa: impulsionamento pago (Ads) após validação orgânica.",
    custo_producao_por_video: "$0.00",
    custo_1000_videos_por_mes: "$0.00",
    custo_infraestrutura_mes: "$0.00",
    totais: { servicos: totalServicos, configurados: totalConfigurados, gratis: totalGratis },
    stack: status,
    fallback_redundancia: {
      llm: "4 providers (Groq → Cerebras → NVIDIA → OpenRouter)",
      imagem: "3 providers (Pollinations → NVIDIA → Together)",
      tts: "1 primary (Edge TTS ilimitado) + 2 backups locais (Coqui, Piper)"
    },
    qualidade_apesar_gratis: [
      "Flux.1 Schnell = mesmo modelo usado em serviços pagos (Black Forest Labs)",
      "Llama 3.3 70B supera GPT-4 em PT-BR (benchmarks)",
      "Edge TTS Neural = usado nos próprios produtos Microsoft Office/Teams",
      "Whisper Large v3 Turbo = state-of-the-art mundial",
      "ffmpeg = padrão de Netflix, YouTube, todas as plataformas"
    ],
    impulsionamento_paga: {
      regra: "Apenas após validação orgânica: 1.000 views em 48h + 50%+ retenção + 5%+ CTR",
      orcamento_fase_1: "R$200 nas primeiras 2 semanas",
      plataformas: ["Google Ads YouTube In-stream", "Meta Ads Reels", "TikTok Ads Spark"]
    }
  });
}
