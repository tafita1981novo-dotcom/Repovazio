export const runtime = 'edge';

export const dynamic = 'force-dynamic';

import { createClient } from '@supabase/supabase-js';

function getClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return null;
  return createClient(url, key);
}

export async function GET() {
  const client = getClient();

  if (!client) {
    return Response.json({
      theme: { primaryColor: '#00ff88', background: '#0b0f1a' },
      widgets: { clock: true },
      texts: { title: 'Dashboard' }
    });
  }

  try {
    const { data } = await client
      .from('config')
      .select('data')
      .limit(1)
      .single();

    return Response.json(data?.data || {});
  } catch {
    return Response.json({});
  }
}

export async function POST(req: Request) {
  const client = getClient();
  if (!client) return Response.json({ ok: true });

  const body = await req.json();
  await client.from('config').upsert({ id: 'global', data: body });

  return Response.json({ ok: true });
}
