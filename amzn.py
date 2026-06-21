from get_product_info import amzn_product_info_scraper
from utils import extract_country_code, save_to_database
from get_search_results import get_search_results, parse_pagination_url
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from curl_cffi import requests
from curl_cffi.requests.errors import RequestsError
from fake_useragent import UserAgent
import re
import asyncio

# url = "https://www.amazon.in/iPhone-16-Plus-256-GB/dp/B0DGJ8DP1M/ref=sr_1_3?crid=NWE6WD0LU1CO&dib=eyJ2IjoiMSJ9.ePpqqbL-nn7bDcnfNguz2eyoq6xgQvt9lW2fONfrgdqICdGiOBZ_JevxefI77ShsTcRYnj84OnV4_7vB_kmqLN3LlhJslPplCjnUpy--CNL36R_QF2X0oYEsgJZqUzmaMT-sfE7WUffaROlUxAx5dpBUCztJkLLhAA6jdZN2271nLd6PilH5GhvAsoh3_Kz6q-UPjpz5xRWPPz62Ji77cPvCzAF41W4W8SJSIXTr0gE.3jMd3XQptpbFZ5pzvR_59KPc9v8ZrXpRTuuV_Xj-fm4&dib_tag=se&keywords=iphone%2B17%2Bpro&qid=1780913862&sprefix=iphone%2Caps%2C289&sr=8-3&th=1"

# url = "https://www.amazon.in/CP-PLUS-Outdoor-CP-URC-TC24PL3-Compatible/dp/B0FH5G1Z7P/ref=sr_1_3?sr=8-3"

# url = "https://www.amazon.in/s?k=night+vision+camera"

# url = url3
url = None

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

    response = session.get(
                    url,
                    headers=merged_headers,
                    timeout=timeout,
                    allow_redirects=True
                )


    print("[INFO] Pinging amazon url")
    # res = await session.get(url, impersonate="chrome")

    return response

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
    


if not url:
    print("[INFO] No url detected. Please enter the query for search.")
    query = input()
    country_code = "in"
    url =  f"https://www.amazon.{country_code}/s?k={query.replace(' ', '+')}"

# html_content = asyncio.run(ping_amazon(url))
html_content = asyncio.run(ping_amazon(url))
with open("debug_response.html", "w", encoding="utf-8") as f:
    f.write(html_content.text)
print("[DEBUG] Status code:", html_content.status_code)

check_url = re.search("/dp/(.*?)/", url)

if check_url:
    print("[INFO] Product url detected")
    product_info = amzn_product_info_scraper(html_content, url)

    save_to_database(product_info) 


    if len(product_info)==0:
        print("[ERROR] Product information was not fetched (or page was blocked)")

else:
    print("[INFO] Search url detected") 
    print("[INFO] Starting product search")
    
    max_pages = 5
    current_page = 1

    current_url = url
    all_products = []

    while current_url and current_page<=max_pages:
        print(f"[INFO] Scraping search page {current_page}/{max_pages}: {current_url}")

        if current_page!=1:
            html_content = asyncio.run(ping_amazon(current_url))

        if not html_content or not html_content.content:
            print("[ERROR] Received empty html or failed to fetch search page")
            break

        country_code = extract_country_code(current_url)
        base_url = f"https://www.amazon.{country_code}"

        products = get_search_results(html_content, base_url, country_code)

        # Check if we got valid results
        if not products:
            print(f"[ERROR] No products found on page {current_page} (or page was blocked)")
            break

        print(f"[INFO] Found {len(products)} products on page {current_page}")
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
    save_to_database(all_products)

            

        

                



        

        


         

        


        
