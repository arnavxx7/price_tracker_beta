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
    prod_name = prod_name_element.text.strip() if prod_name_element else None

    prod_info = {}
    prod_info["name"] = prod_name

    price = None 
    currency = None 

    # Strategy 1: Standard Amazon price classes (most product pages)
    prod_price_whole_element = soup.select_one('.a-price-whole')
    prod_price_fraction_element = soup.select_one('.a-price-fraction')
    currency_element = soup.select_one('.a-price-symbol')

    # print("strat1", (prod_price_whole_element, prod_price_fraction_element, currency_element))

    if prod_price_whole_element:
        prod_price_whole = prod_price_whole_element.text.strip().replace(".", "").replace(",", "")
        if prod_price_fraction_element:
            prod_price_fraction = prod_price_fraction_element.text.strip()
            price = float(f"{prod_price_whole}.{prod_price_fraction}")
        else:
            price = float(prod_price_whole)
        if currency_element:
            currency = CURRENCY_MAPPING.get(currency_element.text.strip())

    # print("strat1", price, currency)

    # Strategy 2: a-offscreen span (e.g. "₹69,900.00" as full string)
    if price is None:
        offscreen = soup.select_one('span.a-offscreen')
        if offscreen:
            m = re.search(r'([₹$€¥])\s*([\d,]+\.?\d*)', offscreen.text)
            if m:
                currency = CURRENCY_MAPPING.get(m.group(1), m.group(1))
                price = float(m.group(2).replace(',', ''))

    # print("strat2", price, currency)

    # Strategy 3: UCC widget / newer buybox — plain span with currency symbol
    if price is None:
        for span in soup.find_all('span'):
            text = span.text.strip()
            m = re.match(r'^([₹$€¥])\s*([\d,]+\.?\d*)$', text)
            if m and 'a-text-strike' not in (span.get('class') or []):
                currency = CURRENCY_MAPPING.get(m.group(1), m.group(1))
                price = float(m.group(2).replace(',', ''))
                break

    # print("strat3", price, currency)

    prod_info["price"] = price
    prod_info["currency"] = currency


    # print(price)

    # if price is None:
    #     price_element = soup.select_one('span.a-offscreen')
    #     if price_element:
    #         price_text = price_element.text.strip()
    #         # Extract numeric value from price text (e.g., "$29.99" -> 29.99)
    #         price_match = re.search(r'[\d,]+\.?\d*', price_text)
    #         if price_match: 
    #             price = float(price_match.group().replace(',', ''))
    # prod_info["price"] = price

    # currency_element = soup.select_one('.a-price-symbol')
    # currency = currency_element.text.strip() if currency_element else None

    # if currency:
    #     try:
    #         currency = CURRENCY_MAPPING[currency]
    #     except Exception as e:
    #         currency = currency

    # prod_info["currency"] = currency

    # brand_element = soup.select_one('#bylineInfo')
    # brand_name = None


    # if brand_element:
    #     txt = brand_element.text.strip()
    #     match = re.search(r'visit the (.*?) store', txt, re.IGNORECASE)
    #     if match:
    #         brand_name = match.group(1).strip()

    brand_name = None

    # Method 1: Byline "Visit the X Store" or "Brand: X"
    byline = soup.select_one('#bylineInfo')
    if byline:
        txt = byline.text.strip()
        # "Visit the Nike Store"
        match = re.search(r'visit the (.+?) store', txt, re.IGNORECASE)
        if match:
            brand_name = match.group(1).strip()
        # "Brand: Nike"
        if not brand_name:
            match = re.search(r'brand[:\s]+(.+)', txt, re.IGNORECASE)
            if match:
                brand_name = match.group(1).strip()

    # Method 2: Product details table (very reliable when present)
    if not brand_name:
        # Horizontal details table (most product pages)
        for row in soup.select('#productDetails_techSpec_section_1 tr, #productDetails_detailBullets_sections1 tr'):
            header = row.select_one('th')
            value = row.select_one('td')
            if header and value and 'brand' in header.text.strip().lower():
                brand_name = value.text.strip()
                break

    # Method 3: Detail bullets (older Amazon layout)
    if not brand_name:
        for item in soup.select('#detailBullets_feature_div li'):
            txt = item.text.strip()
            if 'brand' in txt.lower():
                parts = txt.split(':', 1)
                if len(parts) == 2:
                    brand_name = parts[1].strip().replace('\u200f', '').replace('\u200e', '')
                    break

    # Method 4: Brand in product overview table (common for electronics/tools)
    if not brand_name:
        for row in soup.select('#poExpander tr, #productOverview_feature_div tr'):
            header = row.select_one('td:first-child, th')
            value = row.select_one('td:last-child')
            if header and value and 'brand' in header.text.strip().lower():
                brand_name = value.text.strip()
                break

    # Method 5: Meta tag (clean, no parsing needed)
    if not brand_name:
        meta = soup.select_one('meta[name="brand"]') or \
               soup.select_one('meta[property="og:brand"]')
        if meta and meta.get('content'):
            brand_name = meta['content'].strip()

    # Method 6: Search result container selectors (your method 2, as last resort)
    if not brand_name:
        brand_selectors = [
            '.a-row .a-size-base-plus.a-color-base',
            '.a-size-base-plus:not([aria-label])',
            'h2 .a-size-base-plus',
            '.s-line-clamp-1 span',
        ]
        for selector in brand_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                brand_name = elem.text.strip()
                break

    # Cleanup
    if brand_name:
        # Remove unicode control characters Amazon sometimes injects
        brand_name = re.sub(r'[\u200e\u200f\u00a0]', '', brand_name).strip()
        # Remove trailing/leading punctuation
        brand_name = brand_name.strip('.:,')
        # If result is suspiciously long it's probably not a brand name
        if len(brand_name) > 50:
            brand_name = None

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


    # print(prod_info)


    return prod_info











