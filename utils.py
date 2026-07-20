import re
import psycopg2
import os
from dotenv import load_dotenv
from psycopg2 import sql
from app_logging import logger
from supabase import create_client, Client
import resend

load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(supabase_url, supabase_key)

resend.api_key = os.getenv("RESEND_EMAIL_API_KEY")

CONFIG = {
    "host": "aws-1-ap-south-1.pooler.supabase.com",
    "user": "postgres.mtsadefjhnqdvmsqcjps",
    "password": os.getenv("DB_PASSWORD"),
    "database": "postgres",
    "port": 5432
}

def is_url(string):
    pattern = r'^(http|https)'
    return bool(re.match(pattern, string))

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

def search_db(query: str, search_type: str) -> list:
    conn = psycopg2.connect(**CONFIG)
    try:
        if search_type == "search":
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                            asin, 
                            name,
                            price,
                            brand,
                            rating,
                            currency,
                            url,
                            prime,
                            org_price,
                            discount_percent,
                            img_url,
                            ts_rank(search_vector, websearch_to_tsquery('english', %s)) AS rank
                    FROM amzn_product_info
                    WHERE search_vector @@ websearch_to_tsquery('english', %s)
                    ORDER BY rank DESC NULLS LAST
                    LIMIT 60
                """, (query, query))
                
                columns = [desc[0] for desc in cur.description]
                columns[1] = "title"
                columns[8] = "original_price"
                rows = cur.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        
        elif search_type == "product":
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                            asin, 
                            name,
                            price,
                            brand,
                            rating,
                            currency,
                            url,
                            prime,
                            org_price,
                            discount_percent,
                            img_url
                    FROM amzn_product_info
                    WHERE asin = %s
                    LIMIT 1
                            """, (query,))
                
                columns = [desc[0] for desc in cur.description]
                columns[3] = "brand_name"
                row = cur.fetchall()
                if row:
                    print(row)
                    return dict(zip(columns, row[0]))
                return {}
    finally:
        conn.close()

def track_price_history(current_price: float, asin: str, currency: str, avlble: bool):
     with psycopg2.connect(**CONFIG) as conn:
            with conn.cursor() as cur:
                
                cur.execute("SELECT EXISTS(SELECT 1 FROM amzn_price_history WHERE asin = %s)", (asin,))
                # print("\n---------------------------")

                is_product_tracked = bool(cur.fetchone()[0])

                if not is_product_tracked and current_price is None:
                    logger.error(f"{asin}: Price of product not tracked since price is null")
                    return print(f"[ERROR]: Price of product {asin} not tracked since price is null")

                # if product is not tracked then add it in the table
                if not is_product_tracked:
                    logger.info(f"{asin}: Price of product is not tracked")
                    cur.execute("""
                        INSERT INTO amzn_price_history (asin, price, currency, is_available, recorded_at)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (
                        asin,
                        current_price,
                        currency,
                        avlble
                    ))
                    conn.commit()
                    logger.info(f"{asin}: Started tracking price of product - {current_price}")
                    # print("---------------------------\n")
                # if product is already tracked then add only if price has changed
                else: 
                    logger.info(f"{asin}: Price of product is tracked")
                    cur.execute("SELECT price FROM amzn_product_info WHERE asin = %s", (asin,))
                    try:
                        last_price = float(cur.fetchone()[0])
                    except Exception as e:
                        last_price = None
                        logger.error(f"{asin}: Previous price in record is {last_price}, getting error - {e}")
                        # print(f"[ERROR] {asin}: Previous price is None - {e}")
                    logger.info(f"{asin}: Last price - {last_price}, Current price - {current_price}")
                    # print(f"Last price - {last_price}, Current price - {current_price}")

                    if current_price is None:
                        logger.warning(f"{asin}: Updated price of product is {current_price}, skipping insert")
                        return print(f"[WARN] {asin}: New price is none, skipping insert")
                    
                    
                    if last_price is not None:
                        last_price = round(last_price)
                    current_price = round(current_price)
                    
                    if last_price is None or current_price!=last_price:
                        cur.execute("""
                            INSERT INTO amzn_price_history (asin, price, currency, is_available, recorded_at)
                            VALUES (%s, %s, %s, %s, NOW())
                        """, (
                            asin,
                            current_price,
                            currency,
                            avlble
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
                        logger.info(f"{asin}: Price change detected {last_price} → {current_price}")
                        logger.info(f"{asin}: Successfully recorded the price change in the database")
                        # print(f"Detected a price change, Recorded it: {asin} - {last_price} → {current_price}\n")
                        # print("-------------------------------------\n")
                
                    else:
                        conn.commit()
                        logger.info(f"{asin}: Price unchanged (Current: {current_price}, Last: {last_price}), skipping insert.\n")
                        # print(f"{asin}: Price unchanged ({current_price}), skipping insert.\n")
                        # print("--------------------------------------\n")
                    
def track_rating_history(current_rating: float, asin: str):
    with psycopg2.connect(**CONFIG) as conn:
        with conn.cursor() as cur:
            
            cur.execute("SELECT EXISTS(SELECT 1 FROM amzn_rating_history WHERE asin = %s)", (asin,))
            # print("\n---------------------------")

            is_product_tracked = bool(cur.fetchone()[0])

            if not is_product_tracked and current_rating is None:
                logger.error(f"{asin}: Rating of product not tracked since it is {current_rating}")
                return print(f"[ERROR] {asin}: Product not tracked since rating is none")

            # if product is not tracked then add it in the table
            if not is_product_tracked:
                logger.info(f"{asin}: Rating of product is not tracked")
                cur.execute("""
                    INSERT INTO amzn_rating_history (asin, rating, recorded_at)
                    VALUES (%s, %s, NOW())
                """, (
                    asin,
                    current_rating
                ))
                conn.commit()
                logger.info(f"{asin}: Started tracking rating of product - {current_rating}")
                # print(f"Started tracking rating of product id - {asin}")
                # print("---------------------------\n")
            # if product is already tracked then add only if price has changed
            else: 
                logger.info(f"{asin}: Rating of product is tracked")
                cur.execute("SELECT rating FROM amzn_product_info WHERE asin = %s", (asin,))
                try:
                    last_rating = float(cur.fetchone()[0])
                except Exception as e:
                    last_rating = None
                    logger.error(f"{asin}: Previous rating in record is {last_rating}, getting error - {e}")
                    # print(f"[ERROR] {asin}: Previous rating is None - {e}")
                logger.info(f"{asin}: Last rating - {last_rating}, Current rating - {current_rating}")

                if current_rating is None:
                    logger.warning(f"{asin}: Updated rating of product is {current_rating}, skipping insert")
                    return print(f"[WARN] {asin}: New rating is none, skipping insert")
                
                if last_rating is not None:
                    last_rating = round(last_rating, 1)
                current_rating = round(current_rating, 1)

                if last_rating is None or last_rating != current_rating:
                    cur.execute("""
                        INSERT INTO amzn_rating_history (asin, rating, recorded_at)
                        VALUES (%s, %s, NOW())
                    """, (
                        asin,
                        current_rating
                    ))
                    cur.execute("""
                        UPDATE amzn_product_info 
                        SET rating = %s,
                            last_checked_at = NOW()
                        WHERE asin = %s
                    """, (current_rating,
                            asin
                    ))
                    conn.commit()
                    logger.info(f"{asin}: Detected a change in rating: {last_rating} → {current_rating}")
                    logger.info(f"{asin}: Rating successfully updated in database")
                    # print(f"Detected a rating change, Recorded it: {asin} - {last_rating} → {current_rating}")
                    # print("-------------------------------------\n")
            
                else:
                    conn.commit()
                    logger.info(f"{asin}: Rating unchanged (Current: {current_rating}, Last: {last_rating}), skipping insert.")
                    # print(f"{asin}: Rating unchanged ({current_rating}), skipping insert.")
                    # print("--------------------------------------\n")

            

def save_to_database(product_data, conn, is_tracker_script: bool):
    # product url
    if type(product_data)==dict:
        if not product_data.get("asin"):
            logger.error("Unable to save or update the product in database since ASIN was not provided")
            return "[ERROR] Product data not saved to database due to no ASIN"
        
        if product_data.get("discount_percent"):
            pattern = r'^(100(\.0+)?|\d{1,2}(\.\d+)?)%?$'
            if isinstance(product_data["discount_percent"], str):
                if re.match(pattern, product_data['discount_percent']):
                    product_data["discount_percent"] = round(float(product_data["discount_percent"]))
                else:
                    product_data['discount_percent'] = None 
            elif isinstance(product_data["discount_percent"], float):
                product_data["discount_percent"] = round(product_data["discount_percent"])
        
        logger.info(f"{product_data.get("asin")}: Saving this product")
        
        
        # try:
        with conn.cursor() as cur:
            # check if product is in product info table to avoid adding it again
            cur.execute("SELECT EXISTS(SELECT 1 FROM amzn_product_info WHERE asin = %s)", (product_data.get("asin"),))
            product_info_in_table = bool(cur.fetchone()[0])


            if not product_info_in_table:
                logger.info(f"{product_data.get("asin")}: Product metadata not available in table")
                insert_query = '''
                    INSERT INTO amzn_product_info (asin, name, price, brand, rating, currency, url, created_at, last_checked_at, prime, org_price, discount_percent, img_url) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s, %s, %s);
                    '''
                cur.execute(insert_query, (product_data.get("asin"), product_data.get("name"), product_data.get("price"), product_data.get("brand_name"), product_data.get("rating"), product_data.get("currency"), product_data.get("prod_url"), product_data.get("prime"), product_data.get("org_price"), product_data.get("discount_percent"), product_data.get("img_url")))
                conn.commit()

                track_price_history(product_data.get("price"), product_data.get("asin"), product_data.get("currency"), True)
                track_rating_history(product_data.get("rating"), product_data.get("asin"))
                logger.info(f"{product_data.get("asin")}: Saved 1 product metadata in db")
                # return print(f"[INFO] Saved 1 product {product_data.get("asin")} metadata in db\n")
            
            else:
                # if product metadata available in main table, update the fields with latest values
                logger.info(f"{product_data.get("asin")}: Product metadata available in table")
                cur.execute(
                    "SELECT name, brand, rating, currency, url, price, prime, org_price, discount_percent, img_url FROM amzn_product_info WHERE asin = %s",
                    (product_data.get("asin"),)
                )

                row = cur.fetchone() 

                if row:
                    name, brand, rating, currency, url, price, prime, org_price, discount_percent, img_url = row
                prev_val = {"name": name, "brand": brand, "rating": rating, "currency": currency, "url": url, "price": price, "prime": prime, "org_price": org_price, "discount_percent": discount_percent, "img_url": img_url}
                new_val = {"name": product_data.get("name"), "brand": product_data.get("brand_name"), "currency": product_data.get("currency"), "url": product_data.get("prod_url"), "prime": product_data.get("prime"), "org_price": product_data.get("org_price"), "discount_percent": product_data.get("discount_percent"), "img_url": product_data.get("img_url")}
                old_missing = [k for k, v in prev_val.items() if v is None]
                logger.info(f"{product_data.get("asin")}: These fields are null in existing record in database - {old_missing}")
                new_not_null = [k for k, v in new_val.items() if v is not None]
                if new_not_null:
                    for k in new_not_null:
                        cur.execute(
                            sql.SQL(
                                """
                                UPDATE amzn_product_info
                                SET {column} = %s,
                                    last_checked_at = NOW()
                                WHERE asin = %s
                            """
                            ).format(column=sql.Identifier(k)), 
                            (new_val[k], product_data.get("asin"))
                        )
                conn.commit()
                logger.info(f"{product_data.get("asin")}: Updated the values of following fields - {new_not_null}")
                track_price_history(product_data.get("price"), product_data.get("asin"), product_data.get("currency"), True)
                track_rating_history(product_data.get("rating"), product_data.get("asin"))
                logger.info(f"{product_data.get("asin")}: Updated the price and rating of product")
                # return print(f"[INFO] Product {product_data.get("asin")} metadata available in db\n")
        

        # except Exception as e:
        #     print(f"[ERROR] Could not save product id {product_data["asin"]} to db. Error - {e}")
    # search url or query    
    elif type(product_data)==list:
        if len(product_data)>0:
            i=1
            logger.info("Search url or query received")
            logger.info(f"Saving or updating {len(product_data)} products")
            for prod in product_data:
                if not prod.get("asin"):
                    logger.error("Unable to save or update the product in database since ASIN was not provided")
                    return "[ERROR] Product data not saved to database due to no ASIN" 

                if prod.get("discount_percent"):
                    pattern = r'^(100(\.0+)?|\d{1,2}(\.\d+)?)%?$'
                    if isinstance(prod["discount_percent"], str):
                        if re.match(pattern, prod['discount_percent']):
                            prod["discount_percent"] = round(float(prod["discount_percent"]))
                        else:
                            prod['discount_percent'] = None 
                    elif isinstance(prod["discount_percent"], float):
                        prod["discount_percent"] = round(prod["discount_percent"])

                # print("#", i)                    
                logger.info(f"##{i}/{len(product_data)}: Saving or updating product - {prod.get("asin")}")
                with conn.cursor() as cur:
                    cur.execute("SELECT EXISTS(SELECT 1 FROM amzn_product_info WHERE asin = %s)", (prod.get("asin"),))
                    product_info_in_table = bool(cur.fetchone()[0])
                    # Product info is not available in main table
                    if not product_info_in_table:
                        logger.info(f"{prod.get('asin')}: Product metadata is not available in table")
                        insert_query = '''
                            INSERT INTO amzn_product_info (asin, name, price, brand, rating, currency, url, created_at, last_checked_at, prime, org_price, discount_percent, img_url) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s, %s, %s);
                            '''

                        cur.execute(insert_query, (prod.get("asin"), prod.get("title"), prod.get("price"), prod.get("brand"), prod.get("rating"), prod.get("currency"), prod.get("url"), prod.get("prime"), prod.get("original_price"), prod.get("discount_percent"), prod.get("img_url")))
                        conn.commit()

                        track_price_history(prod.get("price"), prod.get("asin"), prod.get("currency"), True)
                        track_rating_history(prod.get("rating"), prod.get("asin"))
                        logger.info(f"{prod.get('asin')}: Saved 1 product metadata in db")
                        # print(f"[INFO] Saved 1 product {prod.get("asin")} metadata in db\n")

                    else:
                        # if product metadata available in main table, update the values of fields with the lastest not null data
                        logger.info(f"{prod.get('asin')}: Product metadata is available in table")
                        cur.execute(
                            "SELECT name, brand, rating, currency, url, price, prime, org_price, discount_percent, img_url FROM amzn_product_info WHERE asin = %s",
                            (prod.get("asin"),)
                        )

                        row = cur.fetchone()

                        if row:
                            name, brand, rating, currency, url, price, prime, org_price, discount_percent, img_url = row
                        prev_val = {"name": name, "brand": brand, "rating": rating, "currency": currency, "url": url, "price": price, "prime": prime, "org_price": org_price, "discount_percent": discount_percent, "img_url": img_url}
                        new_val = {"name": prod.get("name"), "brand": prod.get("brand_name"), "currency": prod.get("currency"), "url": prod.get("prod_url"),  "prime": prod.get("prime"), "org_price": prod.get("original_price"), "discount_percent": prod.get("discount_percent"), "img_url": prod.get("img_url")}
                        old_missing = [k for k, v in prev_val.items() if v is None]
                        logger.info(f"{prod.get("asin")}: These fields are null in existing record in database - {old_missing}")
                        new_not_null = [k for k, v in new_val.items() if v is not None]
                        if new_not_null:
                            for k in new_not_null:
                                cur.execute(
                                    sql.SQL(
                                        """
                                        UPDATE amzn_product_info
                                        SET {column} = %s,
                                            last_checked_at = NOW()
                                        WHERE asin = %s
                                    """
                                    ).format(column=sql.Identifier(k)), 
                                    (new_val[k], prod.get("asin"))
                                )
                        conn.commit()
                        logger.info(f"{prod.get("asin")}: Updated the values of following fields - {new_not_null}")
                        
                
                        track_price_history(prod.get("price"), prod.get("asin"), prod.get("currency"), True)
                        track_rating_history(prod.get("rating"), prod.get("asin"))
                        # print(f"[INFO] Product {prod.get("asin")} metadata available in db\n")
                        logger.info(f"{prod.get("asin")}: Updated the price and rating of product")

                         
                
                i=i+1
            logger.info(f"Saved or updated {len(product_data)} products in db")
            return print(f"[INFO] Saved {len(product_data)} products in db and started tracking them.")

            # except Exception as e:
            #         print(f"[ERROR] Unable to save {len(product_data)} products in db")

    if not is_tracker_script:
        conn.close()     


    
    # conn = mysql.connector.connect(**CONFIG)
    # cursor = conn.cursor()

    # cursor.execute(insert_query, (product_data["asin"], product_data["name"], product_data["price"], product_data["brand_name"], product_data["rating"], product_data["currency"], product_data["prod_url"])) 
    # conn.commit()

    # if conn in locals() and conn.is_connected():
    #     cursor.close()
    #     conn.close()

    return "[INFO] Product data successfully saved to database"


def send_alerts(product_info: dict, conn):
    asin = product_info.get("asin")
    new_price = product_info.get("price")

    if not asin or new_price is None:
        return
    
    print(f"Checking price alerts for product: {asin}")

    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS(SELECT 1 FROM price_alerts WHERE asin = %s)", (asin,))
        alert_exists = bool(cur.fetchone()[0])

        if not alert_exists:
            return print(f"No alert exists for product: {asin}")
        
        # get all alerts for a specific product asin where current price is less than target price
        cur.execute("""SELECT id, user_id, asin, target_price, current_price, channel, triggered_count 
                        FROM price_alerts
                        WHERE asin = %s
                        AND is_active = true
                        AND target_price > %s
                        AND (last_triggered IS NULL OR last_triggered < NOW() - INTERVAL '24 hours')
                    """, (asin, new_price))
        
        rows = cur.fetchall() # multiple users could be watching the same alert

        if not rows:
            print("No eligible alerts found for product: ", asin)
            return 
        
        for row in rows:
        
            alert_id, user_id, asin, target_price, old_price, channel, triggered_count = row
        

            try:    
                print("Current price = ", new_price)
                print("Target price = ", target_price)
                print("Current price is less than target price, sending alert")

                res = supabase.auth.admin.get_user_by_id(user_id)
                user_email = res.user.email

                if not user_email:
                    print(f"No user email found for user id", user_id)
                    continue
                
                email_html = get_alert_email_html(asin, new_price, target_price)
                # send alert
                email = resend.Emails.send({
                    "from": "arnavmalhotra73@gmail.com",
                    "to": user_email,
                    "subject": "The product you wanted has just had a price drop - trial",
                    "html": email_html
                })
                print(email)

                cur.execute("""
                    UPDATE price_alerts
                    SET current_price = %s,
                        triggered_count = %s,
                        last_triggered = NOW()
                    WHERE id = %s
                            """, (new_price, triggered_count + 1, alert_id))
                
                cur.execute("""
                    INSERT INTO alert_history (alert_id, asin, old_price, new_price, sent_at, channel, status)
                            VALUES (%s, %s, %s, %s, NOW(), %s, %s)
                            """, (alert_id, asin, old_price, new_price, channel, "sent"))
                
                conn.commit()
                print(f"Alert sent for {asin} - new price {new_price} below target price {target_price}")
            
            except Exception as e:
                conn.rollback()
                cur.execute("""
                    INSERT INTO alert_history (alert_id, asin, old_price, new_price, sent_at, channel, status)
                            VALUES (%s, %s, %s, %s, NOW(), %s, %s)
                            """, (alert_id, asin, old_price, new_price, channel, "failed"))
                conn.commit()
                print(f"[ERROR]: Failed to send alert for {asin}: {e}")

        
def get_alert_email_html(asin: str, new_price: float, target_price: float, currency_symbol: str = "$") -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background:#0a0a0f; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f; padding:40px 16px;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px; width:100%;">

          <!-- Header -->
          <tr>
            <td style="padding-bottom:24px; text-align:center;">
              <span style="font-size:22px; font-weight:700; color:#ffffff; letter-spacing:-0.5px;">
                ⬡ PriceLens
              </span>
            </td>
          </tr>

          <!-- Main card -->
          <tr>
            <td style="background:#13131a; border:1px solid #2a2a3a; border-radius:16px; padding:32px;">

              <!-- Icon + title -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="padding-bottom:24px; text-align:center;">
                    <div style="display:inline-block; background:rgba(76,175,130,0.12); border:1px solid rgba(76,175,130,0.25); border-radius:50%; width:56px; height:56px; line-height:56px; text-align:center; font-size:24px;">
                      📉
                    </div>
                    <h1 style="margin:16px 0 6px; font-size:22px; font-weight:700; color:#ffffff; letter-spacing:-0.5px;">
                      Price drop detected!
                    </h1>
                    <p style="margin:0; font-size:14px; color:#6e6e88;">
                      A product on your watchlist just dropped below your target.
                    </p>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <div style="border-top:1px solid #2a2a3a; margin-bottom:24px;"></div>

              <!-- Price comparison -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
                <tr>
                  <td width="48%" style="background:#0a0a0f; border:1px solid #2a2a3a; border-radius:10px; padding:16px; text-align:center;">
                    <p style="margin:0 0 4px; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; color:#6e6e88;">Current price</p>
                    <p style="margin:0; font-size:28px; font-weight:700; color:#4caf82; letter-spacing:-1px;">{currency_symbol}{new_price:,.2f}</p>
                  </td>
                  <td width="4%" style="text-align:center;">
                    <span style="font-size:18px; color:#3e3e56;">→</span>
                  </td>
                  <td width="48%" style="background:#0a0a0f; border:1px solid #2a2a3a; border-radius:10px; padding:16px; text-align:center;">
                    <p style="margin:0 0 4px; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; color:#6e6e88;">Your target</p>
                    <p style="margin:0; font-size:28px; font-weight:700; color:#ffffff; letter-spacing:-1px;">{currency_symbol}{target_price:,.2f}</p>
                  </td>
                </tr>
              </table>

              <!-- ASIN -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
                <tr>
                  <td style="background:#0a0a0f; border:1px solid #2a2a3a; border-radius:10px; padding:14px 16px;">
                    <table width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="font-size:12px; color:#6e6e88;">Product ASIN</td>
                        <td style="text-align:right; font-size:13px; font-family:monospace; color:#a99fff; font-weight:600;">{asin}</td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- CTA -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
                <tr>
                  <td align="center">
                    <a href="https://amazon.com/dp/{asin}"
                       style="display:inline-block; background:linear-gradient(135deg,#7c6bff,#9f6bff); color:#ffffff; text-decoration:none; font-size:14px; font-weight:600; padding:14px 32px; border-radius:10px; letter-spacing:-0.1px;">
                      View on Amazon →
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <div style="border-top:1px solid #2a2a3a; margin-bottom:20px;"></div>

              <!-- Unsubscribe -->
              <p style="margin:0; font-size:12px; color:#3e3e56; text-align:center;">
                Don't want alerts for this product?
                <a href="https://yourdomain.com/unsubscribe?asin={asin}"
                   style="color:#6e6e88; text-decoration:underline;">
                  Turn off this alert
                </a>
              </p>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding-top:24px; text-align:center;">
              <p style="margin:0; font-size:12px; color:#3e3e56;">
                You're receiving this because you set a price alert on PriceLens.
                <br/>
                <a href="https://yourdomain.com/alerts" style="color:#3e3e56; text-decoration:underline;">
                  Manage all alerts
                </a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
    """
    

