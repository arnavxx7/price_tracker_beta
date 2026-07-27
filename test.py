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
    # html_content = file.read()

# if "captcha" in html_content.lower() or "api-services-support@amazon.com" in html_content.lower():
#     print("CAPTCHA or anti-bot measure detected in response")


# is_product_url = re.search("/dp/(.*?)", url)
# print(is_product_url.group(1))
# def is_url(string):
#     pattern = r'^(http|https)'
#     return bool(re.match(pattern, string))
# # Example usage
# print(is_url("htt://www.amazon.in/s?k=ps5"))  # True
# print(is_url("not_a_url"))   
# url = "www.amazon.com/dp/B006FEK6WM?"
# match = re.search(r"/dp/([A-Z0-9]{10})(?:[/?]|$)", url)
# print(match.group(1))

from get_product_info import amzn_product_info_scraper
from amzn import ping_amazon2
import asyncio
import json
import time
import random
from bs4 import BeautifulSoup
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_response(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r

url = "https://www.amazon.com/amazon-fire-tv-stick-4K-select/dp/B0C6W3D4RM/ref=zg_bs_g_amazon-devices_d_sccl_2/142-3225097-9928409?psc=1"
html_content = get_response(url)
product_info = amzn_product_info_scraper(html_content, url)
print(product_info)
# product_info = amzn_product_info_scraper(html_content, test_url)
# search_results = get_search_results(html_content)

# print(product_info)
# print(len(search_results))
# print(search_results[0].keys())
# for prod in search_results:
#     print(prod, "\n")



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

# import resend
# import os
# from dotenv import load_dotenv

# load_dotenv()

# resend.api_key = os.getenv("RESEND_EMAIL_API_KEY")

# email =  resend.Emails.send({
#                     "from": "arnavmalhotra73@gmail.com",
#                     "to": "arnavmalhotra1037@gmail.com",
#                     "subject": "The product you wanted has just had a price drop - trial",
#                     "html": "<<p> <strong>Pyshceeee it works</strong> </p>"
#                 })


# print(email)