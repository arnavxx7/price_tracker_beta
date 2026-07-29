import time
import random
from bs4 import BeautifulSoup
import requests
import json
import re
from playwright.sync_api import sync_playwright
import psycopg2
from dotenv import load_dotenv
import os


load_dotenv()

CONFIG = {
    "host": os.getenv("DB_HOSTNAME"),
    "user": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": 5432
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

CURRENCY_MAPPING = {"$": "USD", "£": "GBP", "€": "EUR", "¥": "JPY"}

def get_response_playwright(url, timeout=10000):
    """
    Loads url in a headless browser, waits for at least one price element
    to appear in the DOM, then returns the fully-hydrated HTML.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 1600},
        )
        context.add_cookies([{
            "name": "i18n-prefs",
            "value": "USD",
            "domain": ".amazon.com",
            "path": "/"
        }])
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)

        prev = 0

        while True:
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(500)
            count = page.locator("div#gridItemRoot").count()
            if count == prev:
                break
            prev = count

        return page.content()



def parse_money(text):
    """Return (currency, amount) from a string like '$1,234.56'."""
    if not text:
        return None, None
    cur_m = re.search(r'^[^\d]+', text.strip())
    amt_m = re.search(r'[\d,]+\.?\d*', text)
    currency = CURRENCY_MAPPING.get(cur_m.group().strip()) if cur_m else None
    amount = None
    if amt_m:
        s = amt_m.group().replace(',', '')
        if s and s != '.':
            try:
                amount = float(s)
            except ValueError:
                print(f"Warning: bad price string '{s}'")
    return currency, amount

def extract_price(card):
    """Returns (currency, price, price_type, offer_count)."""
    # Format A: direct buy-box price (hashed class, inside a-color-price)
    el = card.select_one("span.a-color-price span[class*='p13n-sc-price']")
    if el:
        cur, amt = parse_money(el.get_text(strip=True))
        return cur, amt, "buybox", None

    # Format B: "N offers from $X" (plain class, inside a-color-secondary)
    el = card.select_one("span.a-color-secondary span.p13n-sc-price")
    if el:
        cur, amt = parse_money(el.get_text(strip=True))
        offer_count = None
        wrapper = el.find_parent("span", class_="a-color-secondary")
        if wrapper:
            m = re.search(r"(\d+)\s+offers?\s+from", wrapper.get_text())
            if m:
                offer_count = int(m.group(1))
        return cur, amt, "lowest_offer", offer_count

    # Generic fallbacks (search pages / other layouts)
    el = card.select_one("span[class*='p13n-sc-price']") or card.select_one(".a-price .a-offscreen")
    if el:
        cur, amt = parse_money(el.get_text(strip=True))
        return cur, amt, "unknown", None

    return None, None, None, None


def parse_items(soup) -> list[dict]:
    items = []
    for card in soup.select("div[data-asin]"):
        asin = card.get("data-asin")
        if not asin:
            continue
        d = {"asin": asin}

        # --- Rank ---
        rank = card.select_one("span.zg-bdg-text")
        d["rank"] = int(rank.text.strip("#")) if rank else None

        # --- Title & image (from the product img) ---
        img = card.select_one("img.p13n-product-image, img.p13n-sc-dynamic-image, img[data-a-dynamic-image]")
        title = None
        if img:
            title = img.get("alt") or None
        # Better title source: the truncate div (alt is often empty on zgbs)
        title_div = card.select_one("div.p13n-sc-truncate, div[class*='p13n-sc-css-line-clamp']")
        if title_div and title_div.get_text(strip=True):
            title = title_div.get_text(strip=True)
        d["title"] = title

        # --- Image URL: pick highest resolution from data-a-dynamic-image JSON ---
        d["img_url"] = None
        if img:
            dyn = img.get("data-a-dynamic-image")
            if dyn:
                try:
                    res_map = json.loads(dyn)  # {url: [w, h], ...}
                    d["img_url"] = max(res_map, key=lambda u: res_map[u][0])
                except (json.JSONDecodeError, TypeError):
                    pass
            if not d["img_url"]:
                d["img_url"] = img.get("src")

        # --- Product URL (canonical, tracking-free) ---
        d["product_url"] = f"https://www.amazon.com/dp/{asin}"

        # --- Price & currency ---

        d["currency"], d["price"], d["price_type"], _ = extract_price(card)
 

        # --- Rating (aria-label on the review link, or icon alt text) ---
        d["rating"] = None
        rating_el = (card.select_one("a[aria-label*='out of 5 stars']")
                     or card.select_one("i[class*='a-icon-star'] span.a-icon-alt")
                     or card.select_one("span.a-icon-alt"))
        if rating_el:
            text = rating_el.get("aria-label") or rating_el.get_text(strip=True)
            m = re.search(r'([\d.]+)\s+out\s+of\s+5', text)
            if m:
                try:
                    d["rating"] = float(m.group(1))
                except ValueError:
                    pass

        # --- Prime badge ---
        # d["prime"] = bool(
        #     card.select_one("i.a-icon-prime")
        #     or card.select_one("[class*='p13n-prime-badge']")
        #     or card.select_one("[aria-label='Prime']")
        # )

        items.append(d)
    return items

def get_response(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r


html_response = get_response("https://www.amazon.com/Best-Sellers/zgbs")
soup = BeautifulSoup(html_response.content, "html.parser")

categories = {}

for a in soup.select("#zg-left-col a[href*='/zgbs/']"):
    categories[a.get_text(strip=True)] = "https://www.amazon.com" + a["href"].split("/ref=")[0]

print(f"Found {len(categories)} categories")

results = {}
i = 0
for name, url in categories.items():
    cat_items = []
    for page in (1, 2):
        html_response = get_response_playwright(f"{url}?pg={page}")
        soup = BeautifulSoup(html_response, "html.parser")

        page_items = parse_items(soup)
        # print(f"Found {len(page_items)} products on page {page} in category {name}")
        # print(f"Price list extracted for all products: {[item["price"] for item in page_items]}. Length of list = {len([item["price"] for item in page_items])}")
        # print("\n")
        cat_items.extend(page_items)
        # if name == "Amazon Renewed":
        #     with open('debug_response.html', 'w', encoding = 'utf-8') as f:
        #         f.write(html_response)

        time.sleep(random.uniform(0.1, 0.3))
    results[name] = cat_items
    print(f"{name}: {len(cat_items)} items")
    i += 1
    if i > 3:
        break

null_counts = {}
for category, items in results.items():
    for item in items:
        for field, value in item.items():
            if not value:
                null_counts[field] = null_counts.get(field, 0) + 1
tp = 0
for category, items in results.items():
    tp = tp + len(items)

    
for key, value in null_counts.items():
    print(f"{key} is none for {value}/{tp} products")
print("\n\n Done")


conn = psycopg2.connect(**CONFIG)
with conn.cursor() as cur:
    for category, products in results.items():
        for prod in products:
            cur.execute("""
                INSERT INTO amzn_product_info
                 (asin, name, img_url, url, currency, price, rating, priority)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'medium')
                ON CONFLICT (asin) DO NOTHING
                    """, (
                        prod["asin"], prod["title"], prod["img_url"], prod["product_url"], prod["currency"], prod["price"], prod["rating"],
                    ))
conn.commit()
            