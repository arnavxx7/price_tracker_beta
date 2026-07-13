// app/api/scrape_status/route.ts
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest)
//   { params }: { params: { job_id: string } }
 {
  const since = req.nextUrl.searchParams.get("since_index") ?? "0";
  const job_id = req.nextUrl.searchParams.get("job_id")
  const q = req.nextUrl.searchParams.get("q") 

  const res = await fetch(
    `${process.env.PYTHON_API_URL}/api/get_status?job_id=${job_id}&q=${q}&since_index=${since}`
  );
  return NextResponse.json(await res.json());
}