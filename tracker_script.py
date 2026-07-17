from amzn import ping_amazon2
import asyncio
import psycopg2
import os
from dotenv import load_dotenv
from get_product_info import amzn_product_info_scraper
from utils import save_to_database
from app_logging import logger


load_dotenv()

CONFIG = {
    "host": os.getenv("DB_HOSTNAME"),
    "user": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": 5432
}

logger.info("Starting session")
conn = psycopg2.connect(**CONFIG)
logger.info(f"Connected to db - {CONFIG["database"]}")
cur = conn.cursor()
cur.execute("SELECT asin, url FROM amzn_product_info WHERE brand IS NULL LIMIT 100")
rows = cur.fetchall()  # fetch all first, so cursor stays free for save_to_database
num = len(rows)
logger.info(f"Updating the fields of {num} records")


# cur.close()  # close this cursor, save_to_database will use its own connection
i=1
for asin, url in rows:
    logger.info(f"\nUpdating record - {i}/{num}\n")
    print(f"\nUpdating record - {i}/{num}\n")
    prod_html_content = asyncio.run(ping_amazon2(url))
    product_info = amzn_product_info_scraper(prod_html_content, url)
    print(product_info)

    if len(product_info) == 0:
        logger.error(f"{asin}: Product information was not fetched due to captcha page or other reason, unable to update.")
        print(f"{asin}: Product information was not fetched due to captcha page or other reason, unable to update.")
        continue
    if product_info.get("price") is None and product_info.get("rating") is None:
        if not os.getenv("GITHUB_ACTIONS"):  # only save locally, not on runner
            with open(f"logs/{product_info.get("asin")}_debug_response.html", "w", encoding="utf-8") as f:
                f.write(prod_html_content.text)
            
        else:
            # On GitHub Actions just log it instead
            logger.warning(f"{asin}: Possible captcha or parsing failure")

    save_to_database(product_info, conn, True)
    i = i+1


logger.info("Session completed")