# modules/utils.py

import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from datetime import datetime

AFFILIATE_TAG = "storesofriyas-21"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/119.0.0.0 Safari/537.36"
)

import re

def simplify_title(title):
    title = title.lower()

    # Remove content in parentheses (like (128 GB), (Black), etc.)
    title = re.sub(r'\([^)]*\)', '', title)

    # Remove color names and common specs
    blacklist = [
        "black", "blue", "pink", "red", "green", "white", "yellow", "gray", "silver", "gold",
        "128gb", "256gb", "512gb", "1tb",
        "12gb", "8gb", "6gb", "4gb", "3gb", "2gb",
        "ram", "rom", "storage", "variant"
    ]
    blacklist += ["buy now", "amazon exclusive", "limited edition", "deal", "offer"]

    for word in blacklist:
        title = title.replace(word, '')

    # Remove non-alphanumeric characters
    title = re.sub(r'[^a-zA-Z0-9\s]', '', title)

    # Normalize whitespace
    title = re.sub(r'\s+', ' ', title).strip()

    return title


def deduplicate_variants(products):
    seen = set()
    deduped = []
    for product in products:
        key = simplify_title(product['title'])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(product)
    return deduped


def apply_affiliate_tag(link, tag=AFFILIATE_TAG):
    parsed = urlparse(link)
    query = parse_qs(parsed.query)
    query["tag"] = [tag]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

def format_price(raw):
    try:
        price = float(str(raw).replace("₹", "").replace(",", "").strip())
        return f"₹{price:,.0f}"
    except:
        return "₹0"

def add_label(product):
    labels = []
    try:
        price = float(product['price'].replace("₹", "").replace(",", "").strip())
        if price > 10000:
            labels.append("💸 Premium Pick")
    except:
        pass

    try:
        rating = float(product['rating'].split()[0])
        if rating >= 4.5:
            labels.append("🌟 Top Rated")
    except:
        pass

    if product.get("discount", "").endswith("% off"):
        labels.append("🔥 Hot Deal")

    return labels[0] if labels else "⭐ Recommended"



def get_day():
    return datetime.now().strftime('%A')

def ensure_affiliate_tag(url: str, tag: str = "storesofriyas-21") -> str:
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    if not isinstance(url, str) or not url.startswith("http"):
        raise TypeError(f"[ensure_affiliate_tag] Invalid URL (not a str): {url}")

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["tag"] = [tag]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))



def convert_price_to_float(price_str):
    price_str = price_str.replace("₹", "").replace(",", "").strip()
    return float(price_str)



from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def get_soup_from_url(url: str):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                java_script_enabled=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/112.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            await page.goto(url, timeout=60000, wait_until="networkidle")
            await page.wait_for_selector("div.p13n-sc-uncoverable-faceout", timeout=15000)

            html = await page.content()
            await browser.close()
            return BeautifulSoup(html, "html.parser")

    except Exception as e:
        print(f"❌ Error fetching URL: {url}\n{e}")
        return None




def shorten_url(url):
    try:
        parsed = urlparse(url)
        path = parsed.path
        short_base = f"https://www.amazon.in{path}"
        return f"{short_base}?tag={AFFILIATE_TAG}"
    except Exception as e:
        print(f"Error in shorten_url: {e}")
        return url





import re

def escape_caption_html(text: str, max_bytes: int = 1024) -> str:
    """
    Truncate caption HTML to a max byte limit without breaking tags.
    """
    while len(text.encode('utf-8')) > max_bytes:
        text = text[:-1]

    # Fix unclosed anchor or bold/italic tags if cut mid-way
    # Remove any broken tags at the end
    text = re.sub(r'<[^>]*?$', '', text)

    return text.strip()



import html
import re

def clean_html(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r'[\n\r\t]+', ' ', text)           # Remove line breaks/tabs
    text = re.sub(r'\s{2,}', ' ', text)              # Collapse multiple spaces
    return text.strip()


import unicodedata

def normalize_text(text):
    # Remove smart quotes and other non-ASCII characters
    text = unicodedata.normalize("NFKD", text)
    return ''.join(c for c in text if not unicodedata.combining(c))

def truncate_markdown(text, limit=80):
    text = text.strip()
    if len(text) <= limit:
        return escape_markdown(text)
    truncated = text[:limit].rsplit(' ', 1)[0]
    return escape_markdown(truncated + "...")


async def get_browser_context(browser_type):
    """Return a new browser context with proper settings"""
    browser = await browser_type.launch(headless=True)
    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        java_script_enabled=True,
        user_agent=USER_AGENT
    )
    return browser, context



import re

def escape_markdown_v2(text):
    if not text:
        return ""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', str(text))








def get_browser_type(playwright):
    import os
    # Default to Chromium on GitHub Actions; Firefox for local testing
    if os.getenv("GITHUB_ACTIONS") == "true":
        return playwright.chromium
    return playwright.firefox



def format_markdown_price_info(product):
    price = escape_markdown(product.get("price", "₹0"))
    discount = escape_markdown(product.get("discount", ""))
    offer = escape_markdown(product.get("bank_offer", ""))
    result = f"{price}"
    if discount:
        result += f" | {discount}"
    if offer:
        result += f" | {offer}"
    return result


