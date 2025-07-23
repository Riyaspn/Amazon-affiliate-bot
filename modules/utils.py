import re
import html
import unicodedata
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# === CONSTANTS ===
AFFILIATE_TAG = "storesofriyas-21"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/119.0.0.0 Safari/537.36"
)

# === TEXT PROCESSING ===

def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2 format."""
    if not text:
        return ""
    escape_chars = r"\_*[]()~>#+-=|{}.!"
    return ''.join(['\\' + c if c in escape_chars else c for c in text])

def truncate_markdown(text, limit=80):
    text = text.strip()
    if len(text) <= limit:
        return escape_markdown(text)
    truncated = text[:limit].rsplit(' ', 1)[0]
    return escape_markdown(truncated + "...")

def escape_caption_html(text: str, max_bytes: int = 1024) -> str:
    """Truncate caption HTML to a max byte limit without breaking tags."""
    while len(text.encode('utf-8')) > max_bytes:
        text = text[:-1]
    text = re.sub(r'<[^>]*?$', '', text)
    return text.strip()

def clean_html(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r'[\n\r\t]+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def normalize_text(text):
    text = unicodedata.normalize("NFKD", text)
    return ''.join(c for c in text if not unicodedata.combining(c))

# === TITLE PROCESSING ===

def simplify_title(title):
    title = title.lower()
    title = re.sub(r'\([^)]*\)', '', title)

    blacklist = [
        "black", "blue", "pink", "red", "green", "white", "yellow", "gray", "silver", "gold",
        "128gb", "256gb", "512gb", "1tb",
        "12gb", "8gb", "6gb", "4gb", "3gb", "2gb",
        "ram", "rom", "storage", "variant",
        "buy now", "amazon exclusive", "limited edition", "deal", "offer"
    ]

    for word in blacklist:
        title = title.replace(word, '')

    title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
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

# === AFFILIATE TAG HANDLING ===

def apply_affiliate_tag(link, tag=AFFILIATE_TAG):
    parsed = urlparse(link)
    query = parse_qs(parsed.query)
    query["tag"] = [tag]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

def ensure_affiliate_tag(url: str, tag: str = AFFILIATE_TAG) -> str:
    if not isinstance(url, str) or not url.startswith("http"):
        raise TypeError(f"[ensure_affiliate_tag] Invalid URL (not a str): {url}")
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["tag"] = [tag]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

def shorten_url(url):
    try:
        parsed = urlparse(url)
        path = parsed.path
        short_base = f"https://www.amazon.in{path}"
        return f"{short_base}?tag={AFFILIATE_TAG}"
    except Exception as e:
        print(f"Error in shorten_url: {e}")
        return url

# === PRICING / LABEL ===

def format_price(raw):
    try:
        price = float(str(raw).replace("₹", "").replace(",", "").strip())
        return f"₹{price:,.0f}"
    except:
        return "₹0"

def convert_price_to_float(price_str):
    price_str = price_str.replace("₹", "").replace(",", "").strip()
    return float(price_str)

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

# === DATE UTIL ===

def get_day():
    return datetime.now().strftime('%A')

# === PLAYWRIGHT BROWSER UTILS ===

async def get_soup_from_url(url: str):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                java_script_enabled=True,
                user_agent=USER_AGENT
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

async def get_browser_context(browser_type):
    browser = await browser_type.launch(headless=True)
    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        java_script_enabled=True,
        user_agent=USER_AGENT
    )
    return browser, context

def get_browser_type(playwright):
    import os
    if os.getenv("GITHUB_ACTIONS") == "true":
        return playwright.chromium
    return playwright.firefox
