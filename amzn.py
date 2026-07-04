from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from curl_cffi import requests
from curl_cffi.requests.errors import RequestsError
from fake_useragent import UserAgent
from app_logging import logger
import time
import random
import os, sys


# url = "https://www.amazon.in/iPhone-16-Plus-256-GB/dp/B0DGJ8DP1M/ref=sr_1_3?crid=NWE6WD0LU1CO&dib=eyJ2IjoiMSJ9.ePpqqbL-nn7bDcnfNguz2eyoq6xgQvt9lW2fONfrgdqICdGiOBZ_JevxefI77ShsTcRYnj84OnV4_7vB_kmqLN3LlhJslPplCjnUpy--CNL36R_QF2X0oYEsgJZqUzmaMT-sfE7WUffaROlUxAx5dpBUCztJkLLhAA6jdZN2271nLd6PilH5GhvAsoh3_Kz6q-UPjpz5xRWPPz62Ji77cPvCzAF41W4W8SJSIXTr0gE.3jMd3XQptpbFZ5pzvR_59KPc9v8ZrXpRTuuV_Xj-fm4&dib_tag=se&keywords=iphone%2B17%2Bpro&qid=1780913862&sprefix=iphone%2Caps%2C289&sr=8-3&th=1"

# url = "https://www.amazon.in/CP-PLUS-Outdoor-CP-URC-TC24PL3-Compatible/dp/B0FH5G1Z7P/ref=sr_1_3?sr=8-3"

# url = "https://www.amazon.in/s?k=night+vision+camera"

# url = url3
# url = None

# Default header template
DEFAULT_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}


def get_proxy() -> dict:
    username = os.getenv("PROXY_USERNAME")
    # username = f"{os.getenv('PROXY_USERNAME')}_session-{random.randint(1000,9999)}_lifetime-10m"
    password = os.getenv("PROXY_PASSWORD")
    host = os.getenv("PROXY_HOSTNAME")
    port = os.getenv("PROXY_PORT")

    # IPRoyal supports session stickiness via _session parameter
    # This keeps the same IP for a session (useful for multi-page scraping)
    session_id = random.randint(1000, 9999)
    
    proxy_url = f"http://{username}:{password}@{host}:{port}"
    
    return {
        "http": proxy_url,
        "https": proxy_url,
    }

def estimate_bandwidth(response):
    size_kb = len(response.content) / 1024
    print(f"Response size: {size_kb:.1f}KB")
    return size_kb

async def ping_amazon(url: str):
    ua_generator = UserAgent(browsers=['Chrome'], os=['Windows', 'MacOS'])
    headers = DEFAULT_HEADERS.copy()

    session = requests.Session()
    headers['User-Agent'] = ua_generator.random
    session.headers = headers
    session.impersonate = "chrome120"
    session.get("https://www.amazon.in/", headers=headers)


    merged_headers = session.headers.copy()
    merged_headers['User-Agent'] = ua_generator.random
    if headers:
        merged_headers.update(headers)

    max_retries = 3
    timeout = 25
    delay_range = (2, 5)

    for attempt in range(max_retries+1):
        try:
            # Calculate delay with some randomization (increases with each attempt)
            delay_factor = 1 + (attempt * 0.5)  # Exponential backoff factor
            min_delay, max_delay = delay_range
            delay = random.uniform(min_delay * delay_factor, max_delay * delay_factor)

            print("[INFO] Pinging amazon url")
            logger.info(f"{url}: Pinging amazon url")
            print(f"Request attempt {attempt+1}/{max_retries+1}: GET {url} (delay: {delay:.2f}s)")
            logger.info(f"Request attempt {attempt+1}/{max_retries+1}: GET {url} (delay: {delay:.2f}s)")
            time.sleep(delay)


            response = session.get(
                            url,
                            headers=merged_headers,
                            timeout=timeout,
                            allow_redirects=True
                        )
            
            # Handle HTTP error codes
            if response.status_code != 200:
                print(f"Non-200 status code: {response.status_code}")
                
                # Handle server errors specifically (5xx)
                if 500 <= response.status_code < 600 and attempt < max_retries:
                    print(f"Server error {response.status_code}, retrying...")
                    continue
                
                # For other status codes, continue but warn
                print(f"Error: Received HTTP {response.status_code} for {url}")

            # Check for CAPTCHA/blocking patterns in the content
            if "captcha" in response.text.lower() or "api-services-support@amazon.com" in response.text:
                print("CAPTCHA or anti-bot measure detected in response")
                
                if attempt < max_retries:
                    # Apply a longer delay before the next retry for anti-bot
                    captcha_delay = delay * 3
                    print(f"Detected anti-bot measure. Waiting {captcha_delay:.2f}s before retry")
                    time.sleep(captcha_delay)
                    continue
                
                print("Failed to bypass anti-bot measures after all retries")
                return None

            # If everything is good, return the response
            print(f"Request successful: {url} (Status: {response.status_code})")
            return response

        except RequestsError as e:
            print(f"Network error on attempt {attempt+1}: {e}")
            if attempt == max_retries:
                print(f"Max retries reached. Network error: {e}")
                return None
            time.sleep(delay * 2)  # Longer delay after network error
                
        except Exception as e:
            print(f"Unexpected error on attempt {attempt+1}: {e}")
            if attempt == max_retries:
                print(f"Max retries reached. Error: {e}")
                return None
            time.sleep(delay * 2)


    # res = await session.get(url, impersonate="chrome")

    return None

async def ping_amazon2(url: str):
    max_retries = 3
    timeout = 30

    for attempt in range(max_retries + 1):
        try:
            # Fresh session per attempt
            session = requests.Session()

            # Let curl_cffi handle UA + TLS fingerprint — don't override it
            session.impersonate = "chrome120"
            proxies = get_proxy()
            session.proxies = proxies
            print("[INFO] Pinging amazon url")
            logger.info(f"{url}: Pinging amazon url")
            

            # Step 1 — warm up with homepage to get cookies
            # (only on first attempt to avoid hammering)
            if attempt == 0:
                warmup_delay = random.uniform(1.5, 3.0)
                time.sleep(warmup_delay)

                session.get(
                    "https://www.amazon.in/",
                    headers=DEFAULT_HEADERS,
                    timeout=timeout,
                    allow_redirects=True
                )
                print(f"Warmup request completed cookies acquired, delay - {warmup_delay}")
                logger.info(f"Warm-up request completed, cookies acquired, delay - {warmup_delay}")

            # Step 2 — hit the actual target URL
            # Add Referer to look like user navigated from homepage
            request_headers = DEFAULT_HEADERS.copy()
            request_headers["Referer"] = "https://www.amazon.in/"

            delay = random.uniform(2, 5) * (1 + attempt * 0.5)
            if attempt > 0:
                print(f"Retry attempt {attempt + 1}/{max_retries + 1}, waiting {delay:.2f}s")
                logger.info(f"Retry attempt {attempt + 1}/{max_retries + 1}, waiting {delay:.2f}s")
                time.sleep(delay)
            
            
            logger.info(f"Attempt {attempt + 1}: GET {url}")
            print(f"Attempt {attempt + 1}: GET {url}")
            response = session.get(
                url,
                headers=request_headers,
                timeout=timeout,
                allow_redirects=True
            )

            if response.status_code != 200:
                logger.warning(f"Non-200 status: {response.status_code}")
                if 500 <= response.status_code < 600 and attempt < max_retries:
                    continue

            # CAPTCHA check
            if "captcha" in response.text.lower() or "api-services-support@amazon.com" in response.text:
                print(f"CAPTCHA detected on attempt {attempt + 1}")
                logger.warning(f"CAPTCHA detected on attempt {attempt + 1}")
                # if attempt < max_retries:
                #     # Long delay + fresh session on next attempt
                #     time.sleep(random.uniform(15, 30))
                #     continue
                print("Failed to bypass CAPTCHA after all retries")
                logger.error("Failed to bypass CAPTCHA after all retries")
                return None

            logger.info(f"Success: {url} (status {response.status_code})")
            print(f"Success: {url} (status {response.status_code})")
            size = estimate_bandwidth(response)
            logger.info(f"Estimated size of response - {size} KB")
            return response
                
        except RequestsError as e:
            logger.error(f"Network error on attempt {attempt + 1}: {e}")
            if attempt == max_retries:
                return None
            time.sleep(random.uniform(5, 10))

        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt == max_retries:
                return None
            time.sleep(random.uniform(5, 10))
        
    return None


# async def ping_amazon_playwright(url: str):
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         context = await browser.new_context(
#             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
#             locale="en-IN",
#         )
#         page = await context.new_page()
#         await page.goto(url, wait_until="domcontentloaded")


#         # Wait specifically for the product title to appear
#         try:
#             await page.wait_for_selector("#productTitle", timeout=10000)
#         except:
#             print("[WARN] productTitle didn't appear in time")

#         html = await page.content()
#         await browser.close()

#         return html
    

# if __name__ == "__main__":
#     url = None
#     # url = "https://www.amazon.in/s?k=night+vision+camera"
#     # url = "https://www.amazon.in/CP-PLUS-Outdoor-CP-URC-TC24PL3-Compatible/dp/B0FH5G1Z7P/ref=sr_1_3?sr=8-3"
#     # url = "https://www.amazon.in/iPhone-16-Plus-256-GB/dp/B0DGJ8DP1M/ref=sr_1_3?crid=NWE6WD0LU1CO&dib=eyJ2IjoiMSJ9.ePpqqbL-nn7bDcnfNguz2eyoq6xgQvt9lW2fONfrgdqICdGiOBZ_JevxefI77ShsTcRYnj84OnV4_7vB_kmqLN3LlhJslPplCjnUpy--CNL36R_QF2X0oYEsgJZqUzmaMT-sfE7WUffaROlUxAx5dpBUCztJkLLhAA6jdZN2271nLd6PilH5GhvAsoh3_Kz6q-UPjpz5xRWPPz62Ji77cPvCzAF41W4W8SJSIXTr0gE.3jMd3XQptpbFZ5pzvR_59KPc9v8ZrXpRTuuV_Xj-fm4&dib_tag=se&keywords=iphone%2B17%2Bpro&qid=1780913862&sprefix=iphone%2Caps%2C289&sr=8-3&th=1"
#     if not url:
#         print("[INFO] No url detected. Please enter the query for search.")
#         query = input()
#         country_code = "in"
#         url =  f"https://www.amazon.{country_code}/s?k={query.replace(' ', '+')}"

#     # html_content = asyncio.run(ping_amazon(url))
#     html_content = asyncio.run(ping_amazon(url))
#     with open("debug_response.html", "w", encoding="utf-8") as f:
#         f.write(html_content.text)
#     print("[DEBUG] Status code:", html_content.status_code)

#     check_url = re.search("/dp/(.*?)/", url)
#     conn = psycopg2.connect(**CONFIG)

#     if check_url:
#         print("[INFO] Product url detected")
#         product_info = amzn_product_info_scraper(html_content, url)
#         if len(product_info)==0:
#             print("[ERROR] Product information was not fetched (or page was blocked)")
#         else:
#             save_to_database(product_info, conn) 
#         conn.close()

#     else:
#         print("[INFO] Search url detected") 
#         print("[INFO] Starting product search")
        
#         max_pages = 5
#         current_page = 1

#         current_url = url
#         all_products = []

#         while current_url and current_page<=max_pages:
#             print(f"[INFO] Scraping search page {current_page}/{max_pages}: {current_url}")

#             if current_page!=1:
#                 html_content = asyncio.run(ping_amazon(current_url))
           

#             if not html_content or not html_content.content:
#                 print("[ERROR] Received empty html or failed to fetch search page")
#                 break

#             country_code = extract_country_code(current_url)
#             base_url = f"https://www.amazon.{country_code}"

#             products = get_search_results(html_content, base_url, country_code)

#             # Check if we got valid results
#             if not products:
#                 print(f"[ERROR] No products found on page {current_page} (or page was blocked)")
#                 break

#             print(f"[INFO] Found {len(products)} products on page {current_page}")
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
            
#         print(f"\nSearch completed. Total products found: {len(all_products)}\n")
#         conn = psycopg2.connect(**CONFIG)
#         # for prod in all_products:
#         #     if len(prod)>0:
#         #         prod_html_content = asyncio.run(ping_amazon(prod["url"]))
#         #         product_info = amzn_product_info_scraper(prod_html_content, prod["url"])
#         #         if len(product_info)==0:
#         #             print("[ERROR] Product information was not fetched (or page was blocked)")
#         #         else:
#         #             save_to_database(product_info, conn) 
#         save_to_database(all_products, conn)
#         conn.close()  

            

        

                



        

        


         

        


        
