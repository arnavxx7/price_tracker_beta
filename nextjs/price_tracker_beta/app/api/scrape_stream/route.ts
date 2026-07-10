// app/api/scrape_stream/route.ts
import { NextRequest } from "next/server";

export const dynamic = "force-dynamic"; // ← prevents caching
export const runtime = "nodejs";        // ← required for streaming

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q");
  if (!q) return new Response("Missing query", { status: 400 });

  console.log("This is the query received from pages.tsx here on scrape stream route.ts: ", q)
  console.log("This is the python api url", process.env.PYTHON_API_URL)
    
  // Forward the SSE stream from FastAPI to the browser
  const upstream = await fetch(
    `${process.env.PYTHON_API_URL}/api/scrape_stream?q=${encodeURIComponent(q)}`,
    { 
      headers: {"Accept": "text/event-stream"},
    }
  );
  console.log("Upstream status:", upstream.status);
  console.log("Upstream content-type:", upstream.headers.get("content-type"));
  console.log("Data received:", upstream.body);

  // Forwarding stream directly no buffering
  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}