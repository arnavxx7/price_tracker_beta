from amzn import ping_amazon
import asyncio
import psycopg2
import os
from dotenv import load_dotenv
from get_product_info import amzn_product_info_scraper


load_dotenv()

CONFIG = {
    "host": "aws-1-ap-south-1.pooler.supabase.com",
    "user": "postgres.mtsadefjhnqdvmsqcjps",
    "password": os.getenv("DB_PASSWORD"),
    "database": "postgres",
    "port": 5432
}

conn = psycopg2.connect(**CONFIG)
cur = conn.cursor()
cur.execute("SELECT asin, url FROM amzn_product_info")
rows = cur.fetchall()  # fetch all first, so cursor stays free for save_to_database

cur.close()  # close this cursor, save_to_database will use its own connection

for asin, url in rows:
    prod_html_content = asyncio.run(ping_amazon(url))
    product_info = amzn_product_info_scraper(prod_html_content, url)

    if len(product_info) == 0:
        print(f"[ERROR] Product information was not fetched for {asin}")
        continue

    save_to_database(product_info)  # commits internally

conn.close()