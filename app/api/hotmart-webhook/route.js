import { NextResponse } from 'next/server';

const SB_URL = process.env.SUPABASE_URL;
const SB_KEY = process.env.SUPABASE_SERVICE_KEY;

export async function OPTIONS() {
  return NextResponse.json({}, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, x-hotmart-hottok',
    }
  });
}

export async function POST(req) {
  const cors = { 'Access-Control-Allow-Origin': '*' };
  try {
    const body = await req.json();
    const event    = body.event || body.data?.event || 'PURCHASE_COMPLETE';
    const buyer    = body.data?.buyer || body.buyer || {};
    const purchase = body.data?.purchase || body.purchase || {};
    const preco    = purchase.price?.value || 29.90;
    const email    = buyer.email || '';
    const produto  = preco >= 200 ? 'whatsapp_anual' : 'app_psicologia';

    if (!['PURCHASE_COMPLETE','PURCHASE_APPROVED'].includes(event)) {
      return NextResponse.json({ status: 'ignored', event }, { headers: cors });
    }

    const sbH = {
      'apikey': SB_KEY,
      'Authorization': `Bearer ${SB_KEY}`,
      'Content-Type': 'application/json',
      'Prefer': 'return=minimal',
    };

    // Registrar venda
    await fetch(`${SB_URL}/rest/v1/vendas`, {
      method: 'POST', headers: sbH,
      body: JSON.stringify({ produto, preco, plataforma: 'hotmart',
        email_comprador: email, status: 'confirmada', origem: 'instagram' }),
    });

    // Upsell: comprou app → fila email WA
    if (produto === 'app_psicologia' && email) {
      await fetch(`${SB_URL}/rest/v1/dm_sequencia`, {
        method: 'POST', headers: sbH,
        body: JSON.stringify({ step: 2, trigger: 'comprou_app',
          mensagem: `Upsell WA: ${email}`, delay_min: 60, ativo: true }),
      });
    }

    return NextResponse.json(
      { status: 'ok', produto, preco, email: email.slice(0,3)+'***' },
      { headers: cors }
    );
  } catch (err) {
    return NextResponse.json({ status: 'error', message: String(err) },
      { status: 500, headers: cors });
  }
}
