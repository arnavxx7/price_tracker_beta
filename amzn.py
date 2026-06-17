from get_product_info import amzn_product_info_scraper
from utils import extract_country_code, save_to_database
from get_search_results import get_search_results, parse_pagination_url
from bs4 import BeautifulSoup
from curl_cffi import requests
import re
import asyncio

# url = "https://www.amazon.in/iPhone-16-Plus-256-GB/dp/B0DGJ8DP1M/ref=sr_1_3?crid=NWE6WD0LU1CO&dib=eyJ2IjoiMSJ9.ePpqqbL-nn7bDcnfNguz2eyoq6xgQvt9lW2fONfrgdqICdGiOBZ_JevxefI77ShsTcRYnj84OnV4_7vB_kmqLN3LlhJslPplCjnUpy--CNL36R_QF2X0oYEsgJZqUzmaMT-sfE7WUffaROlUxAx5dpBUCztJkLLhAA6jdZN2271nLd6PilH5GhvAsoh3_Kz6q-UPjpz5xRWPPz62Ji77cPvCzAF41W4W8SJSIXTr0gE.3jMd3XQptpbFZ5pzvR_59KPc9v8ZrXpRTuuV_Xj-fm4&dib_tag=se&keywords=iphone%2B17%2Bpro&qid=1780913862&sprefix=iphone%2Caps%2C289&sr=8-3&th=1"

url = "https://www.amazon.in/CP-PLUS-Outdoor-CP-URC-TC24PL3-Compatible/dp/B0FH5G1Z7P/ref=sr_1_3?sr=8-3"

# url3 = "https://www.amazon.in/s?k=night+vision+camera"

# url = url3
# url = None

async def ping_amazon(url: str):
    session = requests.AsyncSession()
    print("[INFO] Pinging amazon url")
    res = await session.get(url, impersonate="chrome")

    return res

if not url:
    print("[INFO] No url detected. Please enter the query for search.")
    query = input()
    country_code = "in"
    url =  f"https://www.amazon.{country_code}/s?k={query.replace(' ', '+')}"

html_content = asyncio.run(ping_amazon(url))

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
        
    print(f"\nSearch completed. Total products found: {len(all_products)}")
    print(all_products[0]) 
    
            

        

                



        

        


         

        


        
