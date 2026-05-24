import { NextResponse } from 'next/server';

const SB_URL = process.env.SUPABASE_URL;
const SB_KEY = process.env.SUPABASE_SERVICE_KEY;

export async function GET() {
  const cors = { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' };
  try {
    const sbH = { 'apikey': SB_KEY, 'Authorization': `Bearer ${SB_KEY}` };
    const hoje = new Date().toISOString().split('T')[0];

    const [vendas, wa, proj] = await Promise.all([
      fetch(`${SB_URL}/rest/v1/vendas?select=preco,produto,criado_em&status=eq.confirmada&order=criado_em.desc&limit=20`, { headers: sbH }).then(r => r.json()),
      fetch(`${SB_URL}/rest/v1/produto_whatsapp?select=assinantes&limit=1`, { headers: sbH }).then(r => r.json()),
      fetch(`${SB_URL}/rest/v1/receita_projetada?select=*&limit=1`, { headers: sbH }).then(r => r.json()),
    ]);

    const vendas_hoje = (vendas || []).filter(v => v.criado_em?.startsWith(hoje));
    const assinantes  = wa?.[0]?.assinantes ?? 0;
    const receita_mes_app = +(proj?.[0]?.receita_mes ?? 0);

    return NextResponse.json({
      vendas_hoje: vendas_hoje.length,
      receita_hoje: vendas_hoje.reduce((s, v) => s + (+v.preco||0), 0),
      assinantes_wa: assinantes,
      receita_mes_app,
      receita_mes_wa: assinantes * 18,
      total_mes: receita_mes_app + assinantes * 18,
      pct_meta: +((receita_mes_app + assinantes * 18) / 50000 * 100).toFixed(1),
      ultimas_vendas: (vendas||[]).slice(0, 5),
    }, { headers: cors });
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 500, headers: cors });
  }
}
