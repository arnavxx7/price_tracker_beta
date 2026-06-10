from bs4 import BeautifulSoup
import mysql.connector
import re   
from curl_cffi import requests
import asyncio


CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "$Am%1037$",
    "database": "entity_info_database"
}

CURRENCY_MAPPING = {
    "$": "USD",
    "€": "EUR",
    "₹": "INR",
    "¥": "JPY"
}

url = "https://www.amazon.in/iPhone-16-Plus-256-GB/dp/B0DGJ8DP1M/ref=sr_1_3?crid=NWE6WD0LU1CO&dib=eyJ2IjoiMSJ9.ePpqqbL-nn7bDcnfNguz2eyoq6xgQvt9lW2fONfrgdqICdGiOBZ_JevxefI77ShsTcRYnj84OnV4_7vB_kmqLN3LlhJslPplCjnUpy--CNL36R_QF2X0oYEsgJZqUzmaMT-sfE7WUffaROlUxAx5dpBUCztJkLLhAA6jdZN2271nLd6PilH5GhvAsoh3_Kz6q-UPjpz5xRWPPz62Ji77cPvCzAF41W4W8SJSIXTr0gE.3jMd3XQptpbFZ5pzvR_59KPc9v8ZrXpRTuuV_Xj-fm4&dib_tag=se&keywords=iphone%2B17%2Bpro&qid=1780913862&sprefix=iphone%2Caps%2C289&sr=8-3&th=1"

url2 = "https://www.amazon.com/PlayStation%C2%AE5-console-1TB-PlayStation-5/dp/B0FRGTYSL5/ref=sr_1_1_mod_primary_new?sbo=RZvfv%2F%2FHxDF%2BO5021pAnSA%3D%3D&sr=8-1"


# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
#     "Accept-Language": 'en-US, en;q=0.9'
# }

# response = requests.get(url, headers=headers)
# soup = BeautifulSoup(response.content, 'html.parser')
# prod_name = soup.select_one('#productTitle').text.strip()
# prod_price_whole = soup.select_one('.a-price-whole').text.strip()



async def amzn_price_scraper(url: str):
    session = requests.AsyncSession()
    res = await session.get(url, impersonate="chrome")
    soup = BeautifulSoup(res.content, "html.parser")
    prod_name_element = soup.select_one('#productTitle')
    prod_name = prod_name_element.text.strip() if prod_name_element else None
    prod_price_whole_element = soup.select_one('.a-price-whole')
    prod_price_fraction_element = soup.select_one('.a-price-fraction')


    if prod_price_whole_element:
        prod_price_whole = prod_price_whole_element.text.strip().replace(".", "").replace(",", "")
        if prod_price_fraction_element:
            prod_price_fraction = prod_price_fraction_element.text.strip()
            price = float(f"{prod_price_whole}.{prod_price_fraction}")
        else:
            price = float(prod_price_whole)

    if price is None:
        price_element = soup.select_one('span.a-offscreen')
        if price_element:
            price_text = price_element.text.strip()
            # Extract numeric value from price text (e.g., "$29.99" -> 29.99)
            price_match = re.search(r'[\d,]+\.?\d*', price_text)
            if price_match:
                price = float(price_match.group().replace(',', ''))

    currency_element = soup.select_one('.a-price-symbol')
    currency = currency_element.text.strip() if currency_element else None

    if currency:
        try:
            currency = CURRENCY_MAPPING[currency]
        except Exception as e:
            currency = currency

    brand_element = soup.select_one('#bylineInfo')
    brand_name = None


    if brand_element:
        txt = brand_element.text.strip()
        match = re.search(r'visit the (.*?) store', txt, re.IGNORECASE)
        if match:
            brand_name = match.group(1).strip()

    rating = None
    rating_element = soup.select_one('#acrPopover') or soup.select_one('span.a-icon-alt')
    if rating_element:
        rating_text = rating_element.get('title', '') or rating_element.text
        rating_match = re.search(r'([\d\.]+)\s+out\s+of\s+5', rating_text)
        if rating_match:
            rating = float(rating_match.group(1))

    print(prod_name)
    print(price)
    print(currency)
    print(brand_name)
    print(rating)

    prod_id = extract_asin(url)
    print(prod_id)
    prod_cc = extract_country_code(url)
    print(prod_cc)
    canonical_url = get_canonical_url(prod_id, prod_cc, url)
    print(canonical_url)



    return prod_id, prod_name, price, brand_name, rating, currency, canonical_url


def extract_asin(url: str):
    if not url:
        return None
    
    patterns = [
        r'/(?:dp|gp/product|gp/aw/d|aw/d|product|gp/d)/([A-Z0-9]{10})',
        r'asin=([A-Z0-9]{10})',
        r'/([A-Z0-9]{10})(?:/|\?|$)' # Last resort: 10-char alphanumeric after a slash
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def extract_country_code(url: str):
    if not url:
        return None
    country_code = None
    
    match = re.search("amazon.(.*?)/", url, re.IGNORECASE)
    if match:
        country_code = match.group(1)

    return country_code

def get_canonical_url(asin: str, country_code: str, url: str):
    if not asin:
        return url   
    
    if not country_code:
        country_code = "com"

    canonical_url = f"https://amazon.{country_code}/dp/{asin}"

    return canonical_url



def run_scraping_job():
    prod_id, prod_name, prod_price, prod_brand, prod_rating, prod_currency, prod_url = asyncio.run(amzn_price_scraper(url))
    conn = mysql.connector.connect(**CONFIG)
    cursor = conn.cursor()

    insert_query = '''
        INSERT INTO amazon_entity_info (prod_id, prod_name, prod_price, prod_brand, prod_rating, info_fetched_at, prod_currency, prod_url) VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s);
    '''

    cursor.execute(insert_query, (prod_id, prod_name, prod_price, prod_brand, prod_rating, prod_currency, prod_url )) 
    conn.commit()

    if conn in locals() and conn.is_connected():
        cursor.close()
        conn.closr()



run_scraping_job()



