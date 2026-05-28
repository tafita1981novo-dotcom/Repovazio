export const runtime = 'edge';

export const dynamic = 'force-dynamic';
export const maxDuration = 30;

const GEMINI_KEY = process.env.GEMINI_API_KEY;
const GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent";

export async function POST(request: Request) {
  let topic = "Ansiedade moderna";
  try {
    const body = await request.json();
    if (body?.topic) topic = body.topic;
  } catch {}

  if (!GEMINI_KEY) {
    return Response.json({
      status: "fallback",
      topic,
      content: `Conteúdo sobre ${topic}: A ciência explica por que você sente isso. Documentado em psicologia.doc.`,
      createdAt: new Date().toISOString(),
    });
  }

  try {
    const res = await fetch(`${GEMINI_URL}?key=${GEMINI_KEY}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text:
              "Canal psicologia.doc. Narrador anônimo, segunda pessoa 'você'. CRP compliance. DSM-5/APA.\n\n" +
              `Roteiro Short/Reel 60s sobre "${topic}".\nGANCHO 0-3s + REVELAÇÃO 3-20s + IDENTIFICAÇÃO 20-40s + CTA 40-60s.\nTÍTULO + 5 HASHTAGS.`
          }]
        }],
        generationConfig: { maxOutputTokens: 600, temperature: 0.9 }
      }),
    });

    const data = await res.json();
    const content = data.candidates?.[0]?.content?.parts?.[0]?.text || "fallback";

    return Response.json({ status: "ok", topic, content, modelo: "gemini-2.0-flash", createdAt: new Date().toISOString() });
  } catch (e: any) {
    return Response.json({ status: "error", topic, content: "fallback", createdAt: new Date().toISOString() });
  }
}
