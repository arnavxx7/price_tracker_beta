from amzn import ping_amazon2
from get_product_info import amzn_product_info_scraper
from get_search_results import get_search_results, parse_pagination_url
from app_logging import logger
from utils import save_to_database, extract_country_code, is_url, search_db
from fastapi import FastAPI, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import Response, StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import asyncio
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
import json
import os
from dotenv import load_dotenv
import re



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



#         while current_url and current_page<=max_pages:
#             print(f"[INFO] Scraping search page {current_page}/{max_pages}: {current_url}")
#             logger.info(f"Scraping search page {current_page}/{max_pages}: {current_url}")

#             if current_page!=1:
#                 html_content = asyncio.run(ping_amazon2(current_url))
           

#             if not html_content or not html_content.content:
#                 print("[ERROR] Received empty html or failed to fetch search page")
#                 logger.error("Received empty html or failed to fetch search page")
#                 break

#             country_code = extract_country_code(current_url)
#             base_url = f"https://www.amazon.{country_code}"

#             products = get_search_results(html_content, base_url, country_code)

#             # Check if we got valid results
#             if not products:
#                 print(f"[ERROR] No products found on page {current_page} (or page was blocked)")
#                 logger.error(f"No products found on page {current_page} (or page was blocked)")
#                 break

#             print(f"[INFO] Found {len(products)} products on page {current_page}")
#             logger.info(f"Found {len(products)} products on page {current_page}")
#             all_products.extend(products)

#             # Stop if we've reached the requested number of pages
#             if current_page >= max_pages:
#                 break
                
#             # Get URL for the next page
#             next_url = parse_pagination_url(html_content, base_url)
#             if not next_url:
#                 print("No next page found. End of results.")
#                 break
                
#             current_url = next_url
#             current_page += 1


        
@app.get("/api/search_user_input")    
def search_user_input(q: str):
    print(f"Query received on search_user_input endpoint: {q}")
    logger.info(f"Query received on search_user_input endpoint: {q}")
    if not q:
        logger.error(f"Received none as search query: {q}")
        return {
            "status": "error",
            "details": f"Received none as search query, {q}"
        }
    all_products_db = []
    if is_url(q):
        print(f"Received an url = {q}")
        url = q
        is_product_url = re.search(r"/dp/([A-Z0-9]{10})(?:[/?]|$)", url)
        if is_product_url:
            print(f"Received product url = {q}")
            # search_type = "product"
            asin = is_product_url.group(1)
            print(asin)
            logger.info(f"Received product url with asin = {asin}")
            product_info_db = search_db(asin, "product")
            if len(product_info_db)==0:
                return {
                    "status": "no_db",
                    "url-type": "product",
                    "details": f"{asin}: Product not in db"
                }

            return {
                "status": "success",
                "details": f"Received product details for: {product_info_db.get("asin")}",
                "url-type": "product",
                "content-type": f"{type(product_info_db)}",
                "content": product_info_db
            }
        else:
            # search_type = "search"
            print("Received search url with text: ", text_query)
            match = re.search(r'[?&]k=([^&]+)', url)
            text_query = match.group(1).replace('+', ' ')
            logger.info(f"Received search url, with text = {text_query}")
            all_products_db = search_db(text_query, "search")
        
    else:
        logger.info(f"Received text query, with text = {q}")
        print(f"Received text query, with text = {q}")
        all_products_db = search_db(q, "search")

    if len(all_products_db) == 0:
            return {
                "status": "no_db",
                "url-type": "search",
                "details": f"{q}: No matching results in db"
            }
        
    # Deduplicate by ASIN before returning
    seen = set()
    unique_products = []
    for p in all_products_db:
        asin = p.get("asin")
        if asin and asin in seen:
            continue
        if asin:
            seen.add(asin)
        unique_products.append(p)
    return {
            "status": "success",
            "details": f"Found {len(unique_products)} unique products from database for query: {q}",
            "url-type": "search",
            "content-type": f"{type(all_products_db)}",
            "content": unique_products
        } 


@app.get("/api/scrape_product")
def scrape_product(url: str, background_tasks: BackgroundTasks):

    print(f"Query received on scrape_product endpoint: {url}")
    logger.info(f"Query received on scrape_product endpoint: {url}")

    if not url:
        logger.error(f"Received none as product url: {url}")
        return {
            "status": "error",
            "details": f"Received none as product url, {url}"
        }

    html_content = asyncio.run(ping_amazon2(url))
    is_product_url = re.search("/dp/(.*?)/", url) # check if url is product or search 

    conn = psycopg2.connect(**CONFIG)

    if is_product_url:
        print("[INFO] Product url detected")
        logger.info("Product url detected")
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        asin =  match.group(1) if match else None
        product_info = amzn_product_info_scraper(html_content, url)

        if len(product_info)==0:
            logger.error(f"{asin}: Product information was not fetched due to captcha page or other reason, unable to update.")
            print("[ERROR] Product information was not fetched (or page was blocked)")
            conn.close()
            return {
                "status": "error",
                "details": f"{asin}: Unable to fetch product details. Could be due to captcha or other reason."
            }

        else:
            background_tasks.add_task(save_to_database, product_info, conn) 
            return {
                "status": "success",
                "details": f"Received product details for: {product_info.get("asin")}",
                "url-type": "product",
                "content-type": f"{type(product_info)}",
                "content": product_info
            }
        
    return {
        "status": "error",
        "details": f"scrape_product endpoint did not received product url: {url}"
    }

        
    
@app.get("/api/scrape_stream")
async def scrape_stream(q: str, background_tasks: BackgroundTasks):

    async def event_generator():
        if is_url(q):
            print("Recieved an url")
            logger.info(f"Received an url: {q}")
            url = q
        else:
            print("Received text")
            logger.info(f"Received text: {q}")
            country_code = "com"
            url =  f"https://www.amazon.{country_code}/s?k={q.replace(' ', '+')}"
        
        html_content = await ping_amazon2(url)
        conn = psycopg2.connect(**CONFIG)

        print("[INFO] Search url detected") 
        print("[INFO] Starting product search")
        logger.info("Search url detected")
        logger.info("Starting product search")
        
        max_pages = 5
        current_page = 1

        current_url = url
        seen_asins = set()
        all_products = []

        while current_url and current_page<=max_pages:
            try:

                print(f"[INFO] Scraping search page {current_page}/{max_pages}: {current_url}")
                logger.info(f"Scraping search page {current_page}/{max_pages}: {current_url}")

                if current_page!=1:
                    html_content = await ping_amazon2(current_url)
            

                if not html_content or not html_content.content:
                    print("[ERROR] Received empty html or failed to fetch search page")
                    logger.error("Received empty html or failed to fetch search page")
                    payload = json.dumps({"status": 'error', 'page': current_page, 'details': 'Failed to fetch page'})
                    yield f"data: {payload}\n\n"
                    break

                country_code = extract_country_code(current_url)
                base_url = f"https://www.amazon.{country_code}"

                products = get_search_results(html_content, base_url, country_code)

                # Check if we got valid results
                if not products:
                    print(f"[ERROR] No products found on page {current_page} (or page was blocked)")
                    logger.error(f"No products found on page {current_page} (or page was blocked)")
                    payload = json.dumps({'status': 'error', 'page': current_page, 'details': 'No products found or page blocked'})
                    yield f"data: {payload}\n\n"

                # deduplicate products before sending
                new_products = []
                for p in products:
                    asin = p.get("asin")
                    if asin and asin in seen_asins:
                        continue
                    if asin:
                        seen_asins.add(asin)
                    new_products.append(p)
                
                if new_products:
                    payload = json.dumps({'status': 'success', 
                                          'num_products': f'{len(new_products)}', 
                                          'url-type': 'search', 
                                          'content-type': f'{type(new_products)}', 
                                          'content': new_products, 
                                          'page': current_page})
                    yield f"data: {payload}\n\n"

                
                print(f"[INFO] Found {len(new_products)} products on page {current_page}")
                logger.info(f"Found {len(new_products)} products on page {current_page}")
                all_products.extend(new_products)

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

            except Exception as e:
                payload = json.dumps({'status': 'error', 'details': str(e)})
                yield f"data: {payload}\n\n"
                break

        # Signal completion
        background_tasks.add_task(save_to_database, all_products, conn) 
        payload = json.dumps({'status': 'done', 'total_pages': current_page})
        yield f"data: {payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # important for nginx
            "Connection": "keep-alive",
        }
    )

executor = ThreadPoolExecutor(max_workers=4)
scrape_jobs: dict = {}
# job_id: job => {query, status, products, seen_asins, page, total_pages, error}
# {123: {"query": "ps5", "status": "running", "products": [].....}}
@app.get("/api/start_scrape")
def start_scrape(q: str):
    '''Start a background scrape, Frontend calls this route to begin background scrape operations
        Returns the job_id of scrape operation and the status. Frontend sees the job_id and status of new scraping operation'''
    # Checking if job exists with same query
    for job_id, job in scrape_jobs.items():
        if job["query"]==q and job["status"]!="done":
            return {"job_id": job_id, "status": job["status"]}
        
    new_job_id = str(uuid.uuid4())
    scrape_jobs[new_job_id] = {
        "query": q,
        "status": "running",
        "products": [],
        "seen_asins": set(),
        "page": 0,
        "total_pages": 0,
        "error": None
    }
    #  New job created
    # Start the scraping operation
    executor.submit(run_scrape_job, new_job_id, q)
    return {"job_id": new_job_id, "status": scrape_jobs[new_job_id]["status"]}


@app.get("/api/get_status")
def get_status(job_id, q: str, since_index: int = 0):
    '''The frontend pings this routes every 3s to get the status of the scraping operation\
        Returns the status of the scraping operation, page #, new products found'''

    if job_id not in scrape_jobs:
        return {"status": "not_found", "products": [], "page": 0}
    
    job = scrape_jobs[job_id]
    if job["query"] == q:
        status = job["status"]
        products = job["products"]
        new_products = products[since_index:] # returing only new products since last poll
        print(f"{len(new_products)} new products found")
        return {
            "status": status,
            "page": job["page"],
            "total_products": len(products),
            "new_products": new_products,
            "next_index": len(products),
            "error": job.get("error") 
        }
    
def run_scrape_job(job_id: uuid, q: str):
    """Runs the scraping operation in a seperate isloated background thread. Keeping the frontend free"""
    job = scrape_jobs[job_id]
    logger.info(f"Starting scraping job = {job_id}")
    print(f'Starting scraping job = {job_id}')
    try:
        if is_url(q):
            print("Recieved an url")
            logger.info(f"Received an url: {q}")
            url = q
        else:
            print("Received text")
            logger.info(f"Received text: {q}")
            country_code = "com"
            url =  f"https://www.amazon.{country_code}/s?k={q.replace(' ', '+')}"
        
        html_content = asyncio.run(ping_amazon2(url)) 
        conn = psycopg2.connect(**CONFIG)

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
            job["page"] = current_page

            if current_page!=1:
                html_content = asyncio.run(ping_amazon2(current_url))


            if not html_content or not html_content.content:
                print(f"[ERROR] {job_id}: Received empty html or failed to fetch search page, {current_page}")
                logger.error(f"{job_id}: Received empty html or failed to fetch search page, {current_page}")
                break

            country_code = extract_country_code(current_url)
            base_url = f"https://www.amazon.{country_code}"

            products = get_search_results(html_content, base_url, country_code)

            # Check if we got valid results
            if not products:
                print(f"[ERROR] {job_id}: No products found on page {current_page} (or page was blocked)")
                logger.error(f"{job_id}: No products found on page {current_page} (or page was blocked)")

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
                continue

            # deduplicate products before sending
            new_products = []
            for p in products:
                asin = p.get("asin")
                if asin and asin in job["seen_asins"]:
                    continue
                if asin:
                    job["seen_asins"].add(asin)
                new_products.append(p)
            
            if new_products:
                job["products"].extend(new_products)
                job["total_pages"] = current_page

            
            print(f"[INFO] {job_id}: Found {len(new_products)} products on page {current_page}")
            logger.info(f"{job_id}: Found {len(new_products)} products on page {current_page}")
            all_products.extend(new_products)

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
        
    except Exception as e:
        job["error"] = str(e)
        logger.error(f"{job_id}: Received this error in scraping job, {str(e)}")
        print(f"{job_id}: Received this error in scraping job, {str(e)}")

    finally:
        # conn = psycopg2.connect(**CONFIG)
        # threading.Thread(
        #     target=save_to_database,
        #     args=(job["products"], conn),
        #     daemon=True
        # ).start()
        job["status"] = "done"
        print(f"{job_id}: Scraping job completed, with {len(job["products"])} produts scraped")
        print(f"""
                  {job["status"]}

                                       ._ o o
                                       \_`-)|_
                                    ,""       \ 
                                  ,"  ## |   ಠ ಠ. 
                                ," ##   ,-\__    `.
                              ,"       /     `--._;)
                            ,"     ## /
                          ,"   ##    /


                    """.encode('utf-8'))




    
    

@app.get("/api/price_chart")
def get_price_data(asin: str):
    conn = psycopg2.connect(**CONFIG)

    with conn.cursor() as cur:
        cur.execute("""
                SELECT price, currency, recorded_at
                FROM amzn_price_history
                WHERE asin = %s
                ORDER BY recorded_at;
                    """, (asin,))
        
        rows = cur.fetchall()
    
    conn.close()
    if rows:
        price_points = []
        for row in rows:
            dt = row[2]
            dt_yaxis = f"{dt.day} {dt.strftime('%b')}" # 4 Jul
            dt_hover = f"{dt.strftime('%a')}, {dt.day} {dt.strftime('%b %Y')}" # Sat, 4 Jui 2026
            price_point_dict = {"price": row[0], "currency": row[1], "date_yaxis": dt_yaxis, "date_hover": dt_hover} 
            price_points.append(price_point_dict)
        return {
            "status": "success",
            "num_dp": len(price_points),
            "dp": price_points  
        }
    
    return {
        "status": "error",
        "details": "No price points received"
    }