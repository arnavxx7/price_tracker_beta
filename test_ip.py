# test_proxy.py
from curl_cffi import requests as curl_requests
import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")
host = os.getenv("PROXY_HOSTNAME")
port = os.getenv("PROXY_PORT")

proxy_url = f"http://{username}:{password}@{host}:{port}"

session = curl_requests.Session()
session.impersonate = "chrome120"
session.proxies = {"http": proxy_url, "https": proxy_url}

# Check your IP without proxy
direct = curl_requests.get("https://api.ipify.org?format=json")
print(f"Your real IP: {direct.json()['ip']}")

# Check your IP with proxy
proxied = session.get("https://api.ipify.org?format=json")
print(f"Proxy IP: {proxied.json()['ip']}")

# They should be different — if same, proxy isn't working