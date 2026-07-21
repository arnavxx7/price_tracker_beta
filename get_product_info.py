from bs4 import BeautifulSoup
import re   
import json
from utils import extract_asin, extract_country_code, get_canonical_url



CURRENCY_MAPPING = {
    "$": "USD",
    "€": "EUR",
    "₹": "INR",
    "¥": "JPY"
}


def extract_field(soup, selectors, extract_attribute=None):
    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            if extract_attribute:
                return elem.get(extract_attribute)
            print(elem.text.strip())
            return elem.text.strip()

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


    print(price)

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

    premium_byline = soup.select_one('#premiumBylineInfo_feature_div')

    if premium_byline:
        logo = premium_byline.select_one('img[class*="logoByLine"], img[id*="brandLogo"]')
        if logo and logo.get('alt'):
            brand_name = logo['alt'].strip()

        # Fallback: "Visit the adidas Store" link text
        if not brand_name:
            store_link = premium_byline.select_one('#visitStoreDesktopUrl, #brandLogoBylineLink')
            if store_link:
                match = re.search(r'visit the (.+?) store', store_link.text.strip(), re.IGNORECASE)
                if match:
                    brand_name = match.group(1).strip()

    if not brand_name:
        # Method 1: Byline "Visit the X Store" or "Brand: X"
        byline = soup.select_one('#bylineInfo')
        if byline:
            txt = byline.text.strip()
            print(txt)
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
    
    byline_div = soup.select_one('#bylineInfo_feature_div')
    if byline_div and 'Platform:' in byline_div.text:
        link = byline_div.select_one('a')
        if link:
            brand_name = link.text.strip()


    # Cleanup
    if brand_name:
        # Remove unicode control characters Amazon sometimes injects
        brand_name = re.sub(r'[\u200e\u200f\u00a0]', '', brand_name).strip()
        # Remove trailing/leading punctuation
        brand_name = brand_name.strip('.:,')
        # If result is suspiciously long it's probably not a brand name
        if len(brand_name) > 50:
            brand_name = None
        if "$" in brand_name:
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


    original_price_selectors = [
    'span.a-price.a-text-price.apex-basis-price-value span.a-offscreen', # Current standard layout
    'span.a-price.a-text-price[data-a-strike="true"] span.a-offscreen',  # Alternative modern layout
    '#priceBlockStrikePriceString',                                      # Legacy layout (still seen on some items)
    '.basisPrice .a-offscreen'                                           # Fallback
    ]

    discount_selectors = [
    'span.savingsPercentage',               # Most common layout
    'span.apex-savings-percent',            # Newer "Apex" pricing layout
    '.a-color-price.savingPriceOverride',   # Deal pages
    'span:-soup-contains("% off")'          # Generic fallback using Soup text matching
    ]

    prime_selectors = [
                    'i.a-icon-prime',                     # Common layout
                    '.a-icon-prime',                      # Alternative layout
                    'span:-soup-contains("Prime")',       # Text-based detection
                    '.aok-relative.s-icon-text-medium',   # Format from example
                    '[aria-label="Prime"]'                # Aria-label based
                ]

    org_price = extract_field(soup, original_price_selectors)
    if org_price:
        org_price = str(org_price)
        org_price = org_price.replace(",", "")
        if org_price[0] in list(CURRENCY_MAPPING.keys()):
            org_price = float(org_price[1:])
            prod_info["org_price"] = org_price

    discount_percent = extract_field(soup, discount_selectors)

    if discount_percent:
        discount_percent = str(discount_percent)
        discount_percent = discount_percent[1:].split("%")[0]
        try:
            discount_percent = float(discount_percent)
            if discount_percent == 0.0:
                discount_percent = None
            if discount_percent < 0.0 or discount_percent > 100.0:
                discount_percent = None
        except Exception as e:
            discount_percent = None
            print(e)
        prod_info["discount_percent"] = discount_percent

    if not discount_percent:
        if price and org_price:
            discount_percent = round(100 - (price / org_price * 100))
            if discount_percent is not None:
                if discount_percent <= 0.0 or discount_percent > 100.0:
                    discount_percent = None
            prod_info['discount_percent'] = discount_percent
        

    if prod_info.get('discount_percent'):
        pattern = r'^(100(\.0+)?|\d{1,2}(\.\d+)?)%?$'
        if isinstance(prod_info['discount_percent'], str):
            if re.match(pattern, prod_info['discount_percent']):
                prod_info["discount_percent"] = round(float(prod_info["discount_percent"]))
            else:
                prod_info['discount_percent'] = None
        elif isinstance(prod_info["discount_percent"], float):
            prod_info["discount_percent"] = round(prod_info["discount_percent"])

    prime = extract_field(soup, prime_selectors)

    if prime:
        prod_info["prime"] = True
    else:
        prod_info["prime"] = False

    
    img_element = soup.select_one('#landingImage') or soup.select_one('#imgBlkFront')
    img_url = img_element.get('src') if img_element else None

    # Try to get high-resolution image URL if available
    if img_element and not img_url:
        data_old_hires = img_element.get('data-old-hires')
        data_a_dynamic_image = img_element.get('data-a-dynamic-image')
        
        if data_old_hires:
            img_url = data_old_hires
        elif data_a_dynamic_image:
            # This attribute contains a JSON string with multiple image URLs
            try:
                image_dict = json.loads(data_a_dynamic_image)
                # Get the URL with the highest resolution
                if image_dict:
                    img_url = list(image_dict.keys())[0]
            except Exception:
                pass
    prod_info["img_url"] = img_url
    
    prod_info["asin"] = extract_asin(url)
    prod_info["country_code"] = extract_country_code(url)
    prod_info["prod_url"] = get_canonical_url(prod_info["asin"], prod_info["country_code"], url)


    # print(prod_info)


    return prod_info











