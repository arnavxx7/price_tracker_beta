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
                print("\n---------------------------")

                is_product_tracked = bool(cur.fetchone()[0])
                if is_product_tracked:
                    print(f"Product {asin} is tracked")
                else: 
                    print(f"Product {asin} is not tracked")

                if not is_product_tracked and current_price is None:
                    return print(f"Product {asin} not tracked since price is null")

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
                    print("---------------------------\n")
                # if product is already tracked then add only if price has changed
                else: 
                    cur.execute("SELECT price FROM amzn_price_history WHERE asin = '%s'", (asin,))
                    last_price = float(cur.fetchone()[0])   

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
                        print(f"Detected a price change, Recorded it: {asin} → {currency} {current_price}")
                
                    else:
                        conn.commit()
                        print(f"Price unchanged ({current_price}), skipping insert.")
                    


def save_to_database(product_data):
    # product url
    if type(product_data)==dict:
        if not product_data.get("asin"):
            return "[ERROR] Product data not saved to database due to no ASIN"
        
        # try:
        with psycopg2.connect("dbname=entity_info_db user=postgres password=$Am%1037$ host=localhost port=5432") as conn:
            with conn.cursor() as cur:
                # check if product is in product info table to avoid adding it again
                cur.execute("SELECT EXISTS(SELECT 1 FROM amzn_product_info WHERE asin = %s)", (product_data.get("asin"),))
                product_info_in_table = bool(cur.fetchone()[0])

                if not product_info_in_table:
                    insert_query = '''
                        INSERT INTO amzn_product_info (asin, name, price, brand, rating, currency, url, created_at, last_checked_at) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW());
                        '''
                    cur.execute(insert_query, (product_data.get("asin"), product_data.get("name"), product_data.get("price"), product_data.get("brand_name"), product_data.get("rating"), product_data.get("currency"), product_data.get("prod_url")))
                    conn.commit()

                    track_price_history(product_data.get("price"), product_data.get("asin"), product_data.get("currency"), True, product_data.get("rating"))
                    return print(f"[INFO] Saved 1 product {product_data.get("asin")} in db and started tracking it")
                
                else:
                    track_price_history(product_data.get("price"), product_data.get("asin"), product_data.get("currency"), True, product_data.get("rating"))
                    return print(f"[INFO] Product {product_data.get("asin")} metadata available in table. Updated the price in price history.")
        

        # except Exception as e:
        #     print(f"[ERROR] Could not save product id {product_data["asin"]} to db. Error - {e}")
    # search url or query    
    elif type(product_data)==list:
        if len(product_data)>0:
            i=1
            for prod in product_data:
                if not prod.get("asin"):
                    return "[ERROR] Product data not saved to database due to no ASIN"    

                print("#", i)                    
                with psycopg2.connect("dbname=entity_info_db user=postgres password=$Am%1037$ host=localhost port=5432") as conn:
                    with conn.cursor() as cur:

                        cur.execute("SELECT EXISTS(SELECT 1 FROM amzn_product_info WHERE asin = %s)", (prod.get("asin"),))
                        product_info_in_table = bool(cur.fetchone()[0])

                        if not product_info_in_table:
                            insert_query = '''
                                INSERT INTO amzn_product_info (asin, name, price, brand, rating, currency, url, created_at, last_checked_at) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW());
                                '''

                            cur.execute(insert_query, (prod.get("asin"), prod.get("title"), prod.get("price"), None, prod.get("rating"), prod.get("currency"), prod.get("url")))
                            conn.commit()

                            track_price_history(prod.get("price"), prod.get("asin"), prod.get("currency"), True, prod.get("rating"))
                            print(f"[INFO] Saved 1 product {product_data.get("asin")} in db and started tracking it")

                        else:
                            track_price_history(prod.get("price"), prod.get("asin"), prod.get("currency"), True, prod.get("rating"))

                
                
                i=i+1
            
            return print(f"[INFO] Saved {len(product_data)} products in db and started tracking them.")

            # except Exception as e:
            #         print(f"[ERROR] Unable to save {len(product_data)} products in db")

            


            


    
    # conn = mysql.connector.connect(**CONFIG)
    # cursor = conn.cursor()

    # cursor.execute(insert_query, (product_data["asin"], product_data["name"], product_data["price"], product_data["brand_name"], product_data["rating"], product_data["currency"], product_data["prod_url"])) 
    # conn.commit()

    # if conn in locals() and conn.is_connected():
    #     cursor.close()
    #     conn.close()

    return "[INFO] Product data successfully saved to database"