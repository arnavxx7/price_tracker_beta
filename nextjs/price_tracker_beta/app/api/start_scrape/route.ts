// app/api/start_scrape/route.ts
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q");
  if (!q) return NextResponse.json({ error: "Missing query" }, { status: 400 });

  const res = await fetch(
    `${process.env.PYTHON_API_URL}/api/start_scrape?q=${encodeURIComponent(q)}`
  );
  return NextResponse.json(await res.json());
}