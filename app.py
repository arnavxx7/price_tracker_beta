from amzn import ping_amazon2
from get_product_info import amzn_product_info_scraper
from get_search_results import get_search_results, parse_pagination_url
from app_logging import logger
from utils import save_to_database, extract_country_code
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import Response, StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import psycopg2
import asyncio
import os
from dotenv import load_dotenv
import re


def is_url(string):
    pattern = r'^(http|https)'
    return bool(re.match(pattern, string))

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
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/api/search_query")
def search_query(q: str):
    print(f"Query received on fastapi server: {q}")
    logger.info(f"Fastapi server received this query from nextjs: {q}")
    if not q:
        logger.error(f"Received none as search query: {q}")
        return {
            "status": "error",
            "details": f"Received none as search query, {q}"
        }
    if is_url(q):
        print("Recieved an url")
        logger.info(f"Received an url: {q}")
        url = q
    else:
        print("Received text")
        logger.info(f"Received text: {q}")
        country_code = "in"
        url =  f"https://www.amazon.{country_code}/s?k={q.replace(' ', '+')}"

    html_content = asyncio.run(ping_amazon2(url))
    check_url = re.search("/dp/(.*?)/", url) # check if url is product or search 

    conn = psycopg2.connect(**CONFIG)

    # Product url
    if check_url:
        print("[INFO] Product url detected")
        logger.info("Product url detected")
        # match = re.search(r'/dp/([A-Z0-9]{10})', url)
        # asin =  match.group(1) if match else None
        product_info = amzn_product_info_scraper(html_content, url)

        if len(product_info)==0:
            logger.error(f"{product_info.get("asin")}: Product information was not fetched due to captcha page or other reason, unable to update.")
            print("[ERROR] Product information was not fetched (or page was blocked)")
            conn.close()
            return {
                "status": "error",
                "details": f"{product_info.get("asin")}: Unable to fetch product details. Could be due to captcha or other reason."
            }

        else:
            # save_to_database(product_info, conn) 
            conn.close()
            return {
                "status": "success",
                "details": f"Received product details for: {product_info.get("asin")}",
                "url-type": "product",
                "content-type": f"{type(product_info)}",
                "content": product_info
            }
            
        
    # Search url
    else:
        print("[INFO] Search url detected") 
        print("[INFO] Starting product search")
        logger.info("Search url detected")
        logger.info("Starting product search")
        
        max_pages = 5
        current_page = 1

        current_url = url
        all_products = []

        while current_url and current_page<=max_pages:
            print(f"[INFO] Scraping search page {current_page}/{max_pages}: {current_url}")
            logger.info(f"Scraping search page {current_page}/{max_pages}: {current_url}")

            if current_page!=1:
                html_content = asyncio.run(ping_amazon2(current_url))
           

            if not html_content or not html_content.content:
                print("[ERROR] Received empty html or failed to fetch search page")
                logger.error("Received empty html or failed to fetch search page")
                break

            country_code = extract_country_code(current_url)
            base_url = f"https://www.amazon.{country_code}"

            products = get_search_results(html_content, base_url, country_code)

            # Check if we got valid results
            if not products:
                print(f"[ERROR] No products found on page {current_page} (or page was blocked)")
                logger.error(f"No products found on page {current_page} (or page was blocked)")
                break

            print(f"[INFO] Found {len(products)} products on page {current_page}")
            logger.info(f"Found {len(products)} products on page {current_page}")
            all_products.extend(products)

            # Stop if we've reached the requested number of pages
            if current_page >= max_pages:
                break
                
            # Get URL for the next page
            next_url = parse_pagination_url(html_content, base_url)
            if not next_url:
                print("No next page found. End of results.")
                break
                
            current_url = next_url
            current_page += 1
            
        print(f"\nSearch completed. Total products found: {len(all_products)}\n")
        logger.info(f"Search completed. Total products found: {len(all_products)}\n")

        if len(all_products) == 0:
            return {
                "status": "error",
                "details": f"{url}: Could not find any products on search page. Could be due to captcha or other reason."
            }
        
        # save_to_database(all_products, conn)
        conn.close() 
        return {
            "status": "success",
            "details": f"Found {len(all_products)} products from amazon search pages for query: {q}",
            "url-type": "search",
            "content-type": f"{type(all_products)}",
            "content": all_products
        } 
        
    


