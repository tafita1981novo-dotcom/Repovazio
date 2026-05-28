export const runtime = 'edge';

export async function POST() {
  return Response.json({
    status: "ok",
    published: {
      id: "mock",
      status: "published",
      platform: "mock",
      publishedAt: new Date().toISOString()
    }
  });
}
