import { NextRequest, NextResponse } from "next/server";



export async function POST(req: NextRequest) {

    const asin = await req.json();

    if (!asin) return NextResponse.json({ ok: false });

    await fetch(`${process.env.PYTHON_API_URL}/api/track/view`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ asin })
    });

    return NextResponse.json({ ok: true });

}