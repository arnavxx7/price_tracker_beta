// app/api/scrape_stream/route.ts
import { NextRequest } from "next/server";

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q");
  if (!q) return new Response("Missing query", { status: 400 });

  console.log("This is the query received from pages.tsx here on scrape stream route.ts: ", q)
  console.log("This is the python api url", process.env.PYTHON_API_URL)
    
  // Forward the SSE stream from FastAPI to the browser
  const upstream = await fetch(
    `${process.env.PYTHON_API_URL}/api/scrape_stream?q=${encodeURIComponent(q)}`
  );

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
    },
  });
}