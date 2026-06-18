from bs4 import BeautifulSoup
import mysql.connector
import re   
from curl_cffi import requests
import asyncio
from utils import extract_asin, extract_country_code, get_canonical_url



CURRENCY_MAPPING = {
    "$": "USD",
    "€": "EUR",
    "₹": "INR",
    "¥": "JPY"
}

# url = "https://www.amazon.in/iPhone-16-Plus-256-GB/dp/B0DGJ8DP1M/ref=sr_1_3?crid=NWE6WD0LU1CO&dib=eyJ2IjoiMSJ9.ePpqqbL-nn7bDcnfNguz2eyoq6xgQvt9lW2fONfrgdqICdGiOBZ_JevxefI77ShsTcRYnj84OnV4_7vB_kmqLN3LlhJslPplCjnUpy--CNL36R_QF2X0oYEsgJZqUzmaMT-sfE7WUffaROlUxAx5dpBUCztJkLLhAA6jdZN2271nLd6PilH5GhvAsoh3_Kz6q-UPjpz5xRWPPz62Ji77cPvCzAF41W4W8SJSIXTr0gE.3jMd3XQptpbFZ5pzvR_59KPc9v8ZrXpRTuuV_Xj-fm4&dib_tag=se&keywords=iphone%2B17%2Bpro&qid=1780913862&sprefix=iphone%2Caps%2C289&sr=8-3&th=1"

# url2 = "https://www.amazon.com/PlayStation%C2%AE5-console-1TB-PlayStation-5/dp/B0FRGTYSL5/ref=sr_1_1_mod_primary_new?sbo=RZvfv%2F%2FHxDF%2BO5021pAnSA%3D%3D&sr=8-1"


# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
#     "Accept-Language": 'en-US, en;q=0.9'
# }

# response = requests.get(url, headers=headers)
# soup = BeautifulSoup(response.content, 'html.parser')
# prod_name = soup.select_one('#productTitle').text.strip()
# prod_price_whole = soup.select_one('.a-price-whole').text.strip()



def amzn_product_info_scraper(html_content, url: str = None) -> dict:
    if not html_content:
        print("[ERROR] Received empty html")
        return {}
    soup = BeautifulSoup(html_content.content, "html.parser")
    prod_name_element = soup.select_one('#productTitle')
    print(prod_name_element)
    prod_name = prod_name_element.text.strip() if prod_name_element else None
    prod_price_whole_element = soup.select_one('.a-price-whole')
    prod_price_fraction_element = soup.select_one('.a-price-fraction')

    prod_info = {}
    prod_info["name"] = prod_name
    
    price = None

    if prod_price_whole_element:
        prod_price_whole = prod_price_whole_element.text.strip().replace(".", "").replace(",", "")
        if prod_price_fraction_element:
            prod_price_fraction = prod_price_fraction_element.text.strip()
            price = float(f"{prod_price_whole}.{prod_price_fraction}")
        else:
            price = float(prod_price_whole)

    print(price)

    if price is None:
        price_element = soup.select_one('span.a-offscreen')
        if price_element:
            price_text = price_element.text.strip()
            # Extract numeric value from price text (e.g., "$29.99" -> 29.99)
            price_match = re.search(r'[\d,]+\.?\d*', price_text)
            if price_match:
                price = float(price_match.group().replace(',', ''))

    prod_info["price"] = price

    currency_element = soup.select_one('.a-price-symbol')
    currency = currency_element.text.strip() if currency_element else None

    if currency:
        try:
            currency = CURRENCY_MAPPING[currency]
        except Exception as e:
            currency = currency

    prod_info["currency"] = currency

    brand_element = soup.select_one('#bylineInfo')
    brand_name = None


    if brand_element:
        txt = brand_element.text.strip()
        match = re.search(r'visit the (.*?) store', txt, re.IGNORECASE)
        if match:
            brand_name = match.group(1).strip()

    prod_info["brand_name"] = brand_name

    rating = None
    rating_element = soup.select_one('#acrPopover') or soup.select_one('span.a-icon-alt')
    if rating_element:
        rating_text = rating_element.get('title', '') or rating_element.text
        rating_match = re.search(r'([\d\.]+)\s+out\s+of\s+5', rating_text)
        if rating_match:
            rating = float(rating_match.group(1))

    prod_info["rating"] = rating
    
    
    prod_info["asin"] = extract_asin(url)
    prod_info["country_code"] = extract_country_code(url)
    prod_info["prod_url"] = get_canonical_url(prod_info["asin"], prod_info["country_code"], url)


    print(prod_info)


    return prod_info











