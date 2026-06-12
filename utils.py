import re
import mysql.connector


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
    conn = mysql.connector.connect(**CONFIG)
    cursor = conn.cursor()
    if not product_data["asin"]:
        return "[ERROR] Product data not saved to database due to no ASIN"

    insert_query = '''
        INSERT INTO amazon_entity_info (prod_id, prod_name, prod_price, prod_brand, prod_rating, info_fetched_at, prod_currency, prod_url) VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s);
    '''

    cursor.execute(insert_query, (product_data["asin"], product_data["name"], product_data["price"], product_data["brand_name"], product_data["rating"], product_data["currency"], product_data["prod_url"])) 
    conn.commit()

    if conn in locals() and conn.is_connected():
        cursor.close()
        conn.close()

    return "[INFO] Product data successfully saved to database"