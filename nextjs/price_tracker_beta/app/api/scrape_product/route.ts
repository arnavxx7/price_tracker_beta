import { NextRequest, NextResponse } from "next/server";


export async function GET(req: NextRequest) {
    // Extract the query parameter ('q') from the incoming request URL
    const query = req.nextUrl.searchParams.get("url")

    console.log("This is the product url received from pages.tsx here on /api/scrape_product: ", query)
    // console.log("This is the python api url", process.env.PYTHON_API_URL)
    // Forward the request to your FastAPI backend
    const res = await fetch(
    `${process.env.PYTHON_API_URL}/api/scrape_product?url=${encodeURIComponent(query as string)}`,
    {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
        },
    },
    );
    // console.log("This is data received from fastapi before json", res)

    const data = await res.json();
    console.log("This is the status of data received @/api/scraape_product from fastapi", data.status)

    // Send the FastAPI response back to the Next.js frontend
    return NextResponse.json(data);

}