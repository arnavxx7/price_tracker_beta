import { NextRequest, NextResponse } from "next/server";


export async function GET(req: NextRequest) {
    // Extract asin from incoming request from /product page.tsx
    const asin  = req.nextUrl.searchParams.get("asin");

    console.log(`Fetching price data for product with asin = ${asin}`);

    const res = await fetch(
        `${process.env.PYTHON_API_URL}/api/price_chart?asin=${encodeURIComponent(asin as string)}`
    );

    const data = await res.json();
    console.log("Status of the response received from fastapi @price_chart/route.ts = ", data.status);


    return NextResponse.json(data)
}