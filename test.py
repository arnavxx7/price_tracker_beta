# from amzpy import AmazonScraper

# Create scraper with default settings (amazon.com)
# scraper = AmazonScraper(country_code = "in")


# # Fetch product details
# url = "https://www.amazon.in/CP-PLUS-Outdoor-CP-URC-TC24PL3-Compatible/dp/B0FH5G1Z7P/ref=sr_1_3?sr=8-3"
# product = scraper.get_product_details(url)
# products = scraper.search_products(query="wireless earbuds", max_pages=2)

# print(products[0].keys())


# if product:   
#     print(f"Title: {product['title']}")
#     print(f"Price: {product['currency']}{product['price']}")
#     print(f"Brand: {product['brand']}")
#     print(f"Rating: {product['rating']}")
#     print(f"Image URL: {product['img_url']}")


CURRENCY_MAPPING = {
    "$": "USD",
    "€": "EUR",
    "₹": "INR",
    "¥": "JPY"
}

# print(CURRENCY_MAPPING.get("₹"))

# with open("debug_response.html", 'r', encoding='utf-8') as file:
#     html_content = file.read()

# if "captcha" in html_content.lower() or "api-services-support@amazon.com" in html_content.lower():
#     print("CAPTCHA or anti-bot measure detected in response")

import re
# def is_url(string):
#     pattern = r'^(http|https)'
#     return bool(re.match(pattern, string))
# # Example usage
# print(is_url("htt://www.amazon.in/s?k=ps5"))  # True
# print(is_url("not_a_url"))   
url = "https://www.amazon.com/adidas-Argentina-Replica-Jersey-White/dp/B0F7WYSPZK/ref=sr_1_1?sr=8-1&psc=1"
match = re.search(r'/dp/(.*?)/', url)
print(match.group(1))

from get_product_info import amzn_product_info_scraper
from get_search_results import get_search_results
from amzn import ping_amazon2
import asyncio
import json
from bs4 import BeautifulSoup

# test_url = "https://www.amazon.com/Samsung-32-Inch-H5000F-Tracking-Security/dp/B0DYVMZ4TV/ref=sr_1_2?sr=8-2"
# test_url = "https://www.amazon.com/s?k=backpack"
# test_url2 = "https://www.amazon.com/Porsche-Collectors-Cup-no-60Y/dp/B0D3863V9Z/?_encoding=UTF8&ref_=pd_hp_d_btf_ci_mcx_mr_ca_id_hp_d"
# html_content = asyncio.run(ping_amazon2(test_url))

# with open(f"debug_response.html", "w", encoding="utf-8") as f:
#     f.write(html_content.text)


# soup = BeautifulSoup(html_content.content, "html.parser")
# product_info = amzn_product_info_scraper(html_content, test_url)
# search_results = get_search_results(html_content)

# print(product_info)
# print(len(search_results))
# print(search_results[0].keys())
# for prod in search_results:
#     print(prod["title"])



# img_selectors = [
#     'img#landingImage',           # Standard items (Electronics, Home, etc.)
#     'img#imgBlkFront',            # Book listings
#     'img#main-image',             # Alternative layout
#     '#imgTagWrapperId img'        # Wrapper fallback
# ]

# img_selectors = [
#         'img.s-image',                     # Common layout
#         '.s-image img',                    # Alternative layout
#         '.a-section img[srcset]',          # Layout from example
#         '.s-product-image-container img'   # Another layout
#     ]

# from utils import search_db

# results = search_db("sony", "search")


# for result in results:
#     print(result)

