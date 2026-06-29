from amzpy import AmazonScraper

# Create scraper with default settings (amazon.com)
# scraper = AmazonScraper(country_code = "in")


# # Fetch product details
# url = "https://www.amazon.in/CP-PLUS-Outdoor-CP-URC-TC24PL3-Compatible/dp/B0FH5G1Z7P/ref=sr_1_3?sr=8-3"
# product = scraper.get_product_details(url)
# products = scraper.search_products(query="wireless earbuds", max_pages=2)

# for prod in products:
#     print(prod)


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


from get_product_info import amzn_product_info_scraper
from amzn import ping_amazon
import asyncio

asin = "B09674DSPG"
url = f"https://www.amazon.in/dp/{asin}"

html_content = asyncio.run(ping_amazon(url))
with open("debug_response.html", "w", encoding="utf-8") as f:
    f.write(html_content.text)

product_info = amzn_product_info_scraper(html_content, url)

for k, v in product_info.items():
    print(k, " - ", v)
