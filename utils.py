import re
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "host": "aws-1-ap-south-1.pooler.supabase.com",
    "user": "postgres.mtsadefjhnqdvmsqcjps",
    "password": os.getenv("DB_PASSWORD"),
    "database": "postgres",
    "port": 5432
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
     with psycopg2.connect(**CONFIG) as conn:
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
                    cur.execute("SELECT price FROM amzn_product_info WHERE asin = %s", (asin,))
                    last_price = float(cur.fetchone()[0])
                    print(f"Last price - {last_price}, Current price - {current_price}")

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
                        cur.execute("""
                            UPDATE amzn_product_info 
                            SET price = %s,
                                last_checked_at = NOW()
                            WHERE asin = %s
                        """, (current_price,
                              asin
                        ))
                        conn.commit()

                        print(f"Detected a price change, Recorded it: {asin} → {currency} {current_price}")
                        print("-------------------------------------\n")
                
                    else:
                        conn.commit()
                        print(f"{asin}: Price unchanged ({current_price}), skipping insert.")
                        print("--------------------------------------\n")
                    


def save_to_database(product_data):
    # product url
    if type(product_data)==dict:
        if not product_data.get("asin"):
            return "[ERROR] Product data not saved to database due to no ASIN"
        
        # try:
        with psycopg2.connect(**CONFIG) as conn:
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
                    # if product metadata available in main table, get the previous values and update any null values if found
                    cur.execute(
                        "SELECT name, brand, rating, currency, url, price FROM amzn_product_info WHERE asin = %s",
                        (product_data.get("asin"),)
                    )

                    row = cur.fetchone()

                    if row:
                        name, brand, rating, currency, url, price = row
                    prev_val = {"name": name, "brand": brand, "rating": rating, "currency": currency, "url": url, "price": price}
                    new_val = {"name": product_data.get("name"), "brand": product_data.get("brand_name"), "rating": product_data.get("rating"), "currency": product_data.get("currency"), "url": product_data.get("prod_url")}
                    old_missing = [k for k, v in prev_val.items() if v is None]
                    print(f"{product_data.get("asin")}: These fields are null in existing record in database - {old_missing}")
                    new_not_null = [k for k, v in new_val.items() if v is not None]
                    if new_not_null:
                        for k in new_not_null:
                            cur.execute(f"""
                                UPDATE amzn_product_info
                                SET {k} = %s,
                                    last_checked_at = NOW()
                                WHERE asin = %s
                            """, (new_val[k], product_data.get("asin")))
                    conn.commit()
                    print(f"{product_data.get("asin")}: Updated the values of following fields - {new_not_null}")
                    track_price_history(product_data.get("price"), product_data.get("asin"), product_data.get("currency"), True, product_data.get("rating"))
                    return print(f"[INFO] Product {product_data.get("asin")} metadata available in table. Updated or started tracking the price in price history.")
        

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
                with psycopg2.connect(**CONFIG) as conn:
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
                            print(f"[INFO] Saved 1 product {prod.get("asin")} in db and started tracking it\n")

                        else:
                            track_price_history(prod.get("price"), prod.get("asin"), prod.get("currency"), True, prod.get("rating"))
                            print(f"[INFO] Product {prod.get("asin")} metadata available in table. Updated or started tracking the price in price history.\n")

                         
                
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



