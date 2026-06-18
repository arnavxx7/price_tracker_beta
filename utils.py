import re
# import psycopg2


CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "$Am%1037$",
    "database": "entity_info_database"
}

def extract_asin(url: str):
    if not url:
        return None
    
    patterns = [
        r'/(?:dp|gp/product|gp/aw/d|aw/d|product|gp/d)/([A-Z0-9]{10})',
        r'asin=([A-Z0-9]{10})',
        r'/([A-Z0-9]{10})(?:/|\?|$)' # Last resort: 10-char alphanumeric after a slash
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def extract_country_code(url: str):
    if not url:
        return None
    country_code = None
    
    match = re.search("amazon.(.*?)/", url, re.IGNORECASE)
    if match:
        country_code = match.group(1)

    return country_code

def get_canonical_url(asin: str, country_code: str, url: str):
    if not asin:
        return url   
    
    if not country_code:
        country_code = "com"

    canonical_url = f"https://amazon.{country_code}/dp/{asin}"

    return canonical_url

def save_to_database(product_data: dict):
    if not product_data["asin"]:
        return "[ERROR] Product data not saved to database due to no ASIN"

    with psycopg2.connect("dbname=entity_info_db user=postgres password=$Am%1037$ host=localhost port=5432") as conn:
        with conn.cursor() as cur:
            insert_query = '''
                 INSERT INTO amzn_product_info (asin, name, price, brand, rating, currency, url, created_at, last_checked_at) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW());
                '''
            cur.execute(insert_query, (product_data["asin"], product_data["name"], product_data["price"], product_data["brand_name"], product_data["rating"], product_data["currency"], product_data["prod_url"]))
            conn.commit()

            cur.execute("SELECT price FROM amzn_price_history WHERE prodcut_id = '%s'", (product_data["asin"]))
            last_price = float(cur.fetchone())
            current_price = float(product_data["price"])

            if last_price is None or last_price != current_price:
                cur.execute("""
                    INSERT INTO price_history (asin, price, rating, fetched_at)
                    VALUES (%s, %s, %s, %s)
                """, (
                    product_data["asin"],
                    current_price,
                    product_data["rating"],
                    datetime.now(timezone.utc),
                ))
                conn.commit()
                print(f"[DB] Price saved: {product_data['asin']} → {product_data['currency']} {current_price}")
                return True
            else:
                conn.commit()
                print(f"[DB] Price unchanged ({current_price}), skipping insert.")
                return False


    
    # conn = mysql.connector.connect(**CONFIG)
    # cursor = conn.cursor()

    # cursor.execute(insert_query, (product_data["asin"], product_data["name"], product_data["price"], product_data["brand_name"], product_data["rating"], product_data["currency"], product_data["prod_url"])) 
    # conn.commit()

    # if conn in locals() and conn.is_connected():
    #     cursor.close()
    #     conn.close()

    return "[INFO] Product data successfully saved to database"