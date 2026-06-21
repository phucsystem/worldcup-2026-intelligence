import { getLiveFixtures } from "@/lib/api";

// Same-origin proxy so the client island can poll for live scores without the
// backend URL (API_BASE) ever reaching the browser, and without CORS. Runs
// server-side; never cached.
export const dynamic = "force-dynamic";

export async function GET() {
  const live = await getLiveFixtures();
  return Response.json(live, { headers: { "Cache-Control": "no-store" } });
}
