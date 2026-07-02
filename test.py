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
from amzn import ping_amazon
import asyncio
test_url = "https://www.amazon.in/Rockstar-Games-Digital-Gaming-System/dp/B09XJ8FGVP/ref=sr_1_1?crid=29DKW37JID302&dib=eyJ2IjoiMSJ9.zHtsD-l7WdR777G_vZLO7Vrj_egljAfh31j0aoHZiLyjDyW9ipW9zk0_e7lGAz-LcYTJLncz0KahdN5NgoC9U2isUUu8I7huj3al8zzOcr1vbIcqyFZBKjJikrc-qi2DK9b_eSRvRDLvCVnVtobY18rUD8zvutO_2duf4jWwxgvOEPAmmJpiKn2jnaT_MNUdWddBsIC7SQN2OzTYZNjRN7PrutMyaBLic9pN0EkyS6s.uAyEQRG2Ete2ua-4RUNhlp_80-tvhCmMN_RncuFNKLY&dib_tag=se&keywords=gta+vi&qid=1782989044&s=videogames&sprefix=gta+vi%2Cvideogames%2C316&sr=1-1"
html_content = asyncio.run(ping_amazon(test_url))

product_info = amzn_product_info_scraper(html_content, test_url)

print(product_info.keys())