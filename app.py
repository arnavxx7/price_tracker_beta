from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import Response, StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "host": os.getenv("DB_HOSTNAME"),
    "user": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": 5432
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://localhost:3000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/api/search_query")
def search_query(q: str):
    print(f"Query received on fastapi server: {q}")

    return {
        "status": "success",
        "query_received": q
    }
