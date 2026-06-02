// api/wa-qr.js — Edge Runtime
// Retorna o QR code do WhatsApp como PNG (para <img src=...> no widget)
export const config = { runtime: 'edge' };

const SB_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const SB_KEY = process.env.SUPABASE_SERVICE_KEY;

export default async function handler(req) {
  // CORS para permitir acesso do iframe do Claude
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': '*',
    'Cache-Control': 'no-store, no-cache, must-revalidate',
  };

  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const r = await fetch(
      `${SB_URL}/rest/v1/wa_status?id=eq.singleton&select=connected,qr_base64,phone_name,updated_at`,
      {
        headers: {
          apikey: SB_KEY,
          Authorization: `Bearer ${SB_KEY}`,
        },
        signal: AbortSignal.timeout(8000),
      }
    );

    const rows = await r.json();
    const s = rows && rows[0];

    if (!s) {
      return new Response(JSON.stringify({ error: 'no data' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Se conectado, retorna status JSON
    if (s.connected) {
      return new Response(
        JSON.stringify({ connected: true, phone_name: s.phone_name || '' }),
        { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Se tem QR, retorna a imagem PNG diretamente
    if (s.qr_base64) {
      const dataUrl = s.qr_base64;
      const base64Data = dataUrl.split(',')[1];
      const binary = Uint8Array.from(atob(base64Data), c => c.charCodeAt(0));
      return new Response(binary, {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'image/png',
          'Content-Length': binary.length.toString(),
        },
      });
    }

    return new Response(
      JSON.stringify({ connected: false, qr: null }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
}
