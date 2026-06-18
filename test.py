from amzpy import AmazonScraper

# Create scraper with default settings (amazon.com)
scraper = AmazonScraper()

# Fetch product details
url = "https://www.amazon.in/CP-PLUS-Outdoor-CP-URC-TC24PL3-Compatible/dp/B0FH5G1Z7P/ref=sr_1_3?sr=8-3"
product = scraper.get_product_details(url)

if product:
    print(f"Title: {product['title']}")
    print(f"Price: {product['currency']}{product['price']}")
    print(f"Brand: {product['brand']}")
    print(f"Rating: {product['rating']}")
    print(f"Image URL: {product['img_url']}")