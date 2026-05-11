import { createClient } from "@supabase/supabase-js";

// Forçar renderização dinâmica (não pré-renderizar no build)
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET() {
  try {
    const supabaseUrl = process.env.SUPABASE_URL || "https://tpjvalzwkqwttvmszvie.supabase.co";
    const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

    if (!supabaseKey) {
      return Response.json({ error: "SUPABASE_SERVICE_KEY não configurada" }, { status: 500 });
    }

    const supabase = createClient(supabaseUrl, supabaseKey);

    const [snaps, pub, mp4, series] = await Promise.all([
      supabase.from("channel_snapshots").select("*").order("snapshot_at", { ascending: false }).limit(1),
      supabase.from("content_pipeline").select("id").eq("status", "published"),
      supabase.from("content_pipeline").select("id").eq("status", "mp4_ready"),
      supabase.from("content_pipeline").select("status,metadata").not("metadata->>serie", "is", null).neq("status", "archived")
    ]);

    const snapshot = snaps.data?.[0] || {};
    const seriesData = {};
    for (const r of (series.data || [])) {
      const s = r.metadata?.serie;
      if (s) {
        if (!seriesData[s]) seriesData[s] = { total: 0, published: 0 };
        seriesData[s].total++;
        if (r.status === "published") seriesData[s].published++;
      }
    }

    return Response.json({
      snapshot,
      publicados: pub.data?.length || 0,
      mp4_ready: mp4.data?.length || 0,
      series: seriesData,
      pipeline: {
        published: pub.data?.length || 0,
        mp4_ready: mp4.data?.length || 0
      },
      ts: new Date().toISOString()
    }, {
      headers: {
        "Cache-Control": "no-store, max-age=0",
        "Access-Control-Allow-Origin": "*"
      }
    });
  } catch (err) {
    return Response.json({ error: err.message }, { status: 500 });
  }
}
