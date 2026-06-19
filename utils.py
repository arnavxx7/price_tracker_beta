import re
import psycopg2


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

def track_price_history(current_price: float, asin: str, currency: str, avlble: bool, rating: float):
     with psycopg2.connect("dbname=entity_info_db user=postgres password=$Am%1037$ host=localhost port=5432") as conn:
            with conn.cursor() as cur:

                cur.execute("SELECT EXISTS(SELECT 1 FROM amzn_price_history WHERE asin = %s)", (asin,))

                is_product_tracked = bool(cur.fetchone()[0])
                print(is_product_tracked)

                # if product is not tracked then add it in the table
                if not is_product_tracked:
                    cur.execute("""
                        INSERT INTO amzn_price_history (asin, price, currency, is_available, rating, recorded_at)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                    """, (
                        asin,
                        current_price,
                        currency,
                        avlble,
                        rating
                    ))
                    conn.commit()
                    print(f"Started tracking product id - {asin}")

                else: 
                    cur.execute("SELECT price FROM amzn_price_history WHERE asin = '%s'", (asin))
                    last_price = float(cur.fetchone())   

                    if last_price is None or last_price != current_price:
                        cur.execute("""
                            INSERT INTO amzn_price_history (asin, price, currency, is_available, rating, recorded_at)
                            VALUES (%s, %s, %s, %s, %s, NOW())
                        """, (
                            asin,
                            current_price,
                            currency,
                            avlble,
                            rating
                        ))
                        conn.commit()
                        print(f"[DB] Price saved: {asin} → {currency} {current_price}")
                        return True
                    else:
                        conn.commit()
                        print(f"[DB] Price unchanged ({current_price}), skipping insert.")
                        return False


def save_to_database(product_data):

    if type(product_data)==dict:
        if not product_data["asin"]:
            return "[ERROR] Product data not saved to database due to no ASIN"
        
        # try:
        with psycopg2.connect("dbname=entity_info_db user=postgres password=$Am%1037$ host=localhost port=5432") as conn:
            with conn.cursor() as cur:
                insert_query = '''
                    INSERT INTO amzn_product_info (asin, name, price, brand, rating, currency, url, created_at, last_checked_at) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW());
                    '''
                cur.execute(insert_query, (product_data["asin"], product_data["name"], product_data["price"], product_data["brand_name"], product_data["rating"], product_data["currency"], product_data["prod_url"]))
                conn.commit()

                track_price_history(product_data["price"], product_data["asin"], product_data["currency"], True, product_data["rating"])
                return print(f"[INFO] Saved 1 product {product_data["asin"]} in db and started tracking it")
        

        # except Exception as e:
        #     print(f"[ERROR] Could not save product id {product_data["asin"]} to db. Error - {e}")
        
    elif type(product_data)==list:
        if len(product_data)>0:
            for prod in product_data:
                if not prod["asin"]:
                    return "[ERROR] Product data not saved to database due to no ASIN"
                
                try:
                    with psycopg2.connect("dbname=entity_info_db user=postgres password=$Am%1037$ host=localhost port=5432") as conn:
                        with conn.cursor() as cur:
                            insert_query = '''
                                INSERT INTO amzn_product_info (asin, name, price, brand, rating, currency, url, created_at, last_checked_at) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW());
                                '''
                            cur.execute(insert_query, (prod["asin"], prod["title"], prod["price"], None, prod["rating"], prod["currency"], prod["url"]))
                            conn.commit()

                            track_price_history(prod["price"], prod["asin"], prod["currency"], True, prod["rating"])
                            return print(f"[INFO] Saved {len(product_data)} products in db and started tracking them.")

                except Exception as e:
                    print(f"[ERROR] Unable to save {len(product_data)} products in db")

            


            


    
    # conn = mysql.connector.connect(**CONFIG)
    # cursor = conn.cursor()

    # cursor.execute(insert_query, (product_data["asin"], product_data["name"], product_data["price"], product_data["brand_name"], product_data["rating"], product_data["currency"], product_data["prod_url"])) 
    # conn.commit()

    # if conn in locals() and conn.is_connected():
    #     cursor.close()
    #     conn.close()

    return "[INFO] Product data successfully saved to database"