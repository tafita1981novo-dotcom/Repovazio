export const runtime = 'edge';

export const dynamic = 'force-dynamic';
const SU = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SK = process.env.SUPABASE_SERVICE_KEY;
async function db(path) {
  if (!SU || !SK) return null;
  try { const r = await fetch(SU + '/rest/v1/' + path, { headers: { apikey: SK, Authorization: 'Bearer ' + SK } }); return r.ok ? r.json() : null; } catch { return null; }
}
export async function GET() {
  const [plano, membros, regs] = await Promise.all([db('planejamento_revelacao?order=dia.asc'), db('whatsapp_membros?select=count'), db('registros?select=created_at&order=created_at.asc&limit=1')]);
  let dia = 1;
  if (regs && regs.length > 0) { const ini = new Date(regs[0].created_at); dia = Math.floor((Date.now() - ini.getTime()) / 86400000) + 1; }
  const cnt = Number((membros && membros[0] && membros[0].count) || 0);
  return Response.json({ plano: plano || [], membros_wa: cnt, dia_atual: dia, hora_sp: new Date().toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' }) });
}