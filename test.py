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

# with open("C:\\Users\\Arnav's Lappy\\Downloads\\tracker-logs-28364454346\\B0GY1J37HT_debug_response.html", 'r', encoding='utf-8') as file:
#     html_content = file.read()

# if "captcha" in html_content.lower() or "api-services-support@amazon.com" in html_content.lower():
#     print("CAPTCHA or anti-bot measure detected in response")

# import re
# def is_url(string):
#     pattern = r'^(http|https)'
#     return bool(re.match(pattern, string))
# # Example usage
# print(is_url("htt://www.amazon.in/s?k=ps5"))  # True
# print(is_url("not_a_url"))   


from get_product_info import amzn_product_info_scraper
from get_search_results import get_search_results
from amzn import ping_amazon2
import asyncio
test_url = "https://www.amazon.com/PS5-Playstation-Digital-Wireless-Controller/dp/B0966NLTZS/ref=sr_1_1?sr=8-1"
html_content = asyncio.run(ping_amazon2(test_url))

# product_info = amzn_product_info_scraper(html_content, test_url)
search_results = get_search_results(html_content)

# print(product_info)
print(len(search_results))
for prod in search_results:
    print(prod["title"])

