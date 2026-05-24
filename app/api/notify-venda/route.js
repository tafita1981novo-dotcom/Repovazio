import { NextResponse } from 'next/server';

// Endpoint interno chamado pelo hotmart-webhook após cada venda
// Envia email de notificação para o dono (Rafael)
const GMAIL_USER = process.env.GMAIL_USER || 'tafita81@gmail.com';
const SB_URL = process.env.SUPABASE_URL;
const SB_KEY = process.env.SUPABASE_SERVICE_KEY;

export async function POST(req) {
  try {
    const { produto, preco, email_comprador } = await req.json();

    // Salvar notificação no Supabase (Rafael vê no dashboard)
    await fetch(`${SB_URL}/rest/v1/iris_briefings`, {
      method: 'POST',
      headers: { 'apikey': SB_KEY, 'Authorization': `Bearer ${SB_KEY}`,
        'Content-Type': 'application/json', 'Prefer': 'return=minimal' },
      body: JSON.stringify({
        data: new Date().toISOString().split('T')[0],
        briefing: `💰 VENDA! ${produto} R$${preco} — comprador: ${email_comprador?.slice(0,3)}***`,
        alertas: 0,
      }),
    });

    return NextResponse.json({ status: 'notificado' });
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
