import { NextRequest, NextResponse } from "next/server";


export async function GET(req: NextRequest) {
    // Extract the query parameter ('q') from the incoming request URL
    const query = req.nextUrl.searchParams.get("q")

    console.log("This is the query received from pages.tsx here on route.ts: ", query)
    console.log("This is the python api url", process.env.PYTHON_API_URL)
    // Forward the request to your FastAPI backend
    const res = await fetch(
    `${process.env.PYTHON_API_URL}/api/search_user_input?q=${encodeURIComponent(query as string)}`,
    {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
        },
    },
    );
    // console.log("This is data received from fastapi before json", res)

    const data = await res.json();
    console.log("This is the status of data received @route.ts from fastapi", data.status)

    // Send the FastAPI response back to the Next.js frontend
    return NextResponse.json(data);

}