import { NextRequest, NextResponse } from "next/server";


export async function POST(req: NextRequest) {

    const body = await req.json();  // getting the json body

    const res = await fetch(`${process.env.PYTHON_API_URL}/api/alerts/create`, {
        method:  "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    });

    const data = await res.json();
    return NextResponse.json(data);
}