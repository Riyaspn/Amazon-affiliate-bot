
import random
import time
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from modules.utils import (
    apply_affiliate_tag,
    shorten_url,
    clean_title,
    format_price,
    get_browser_type
)

# Shared product extraction function
async def async_extract_product_data(card):
    try:
        title_elem = await card.query_selector("h2 a span")
        title = await title_elem.inner_text() if title_elem else None
        title = clean_title(title) if title else "No Title"

        link_elem = await card.query_selector("h2 a")
        link = await link_elem.get_attribute("href") if link_elem else None
        if not link:
            return None
        link = "https://www.amazon.in" + link
        link = await shorten_url(apply_affiliate_tag(link))

        price_whole = await card.query_selector("span.a-price-whole")
        price_frac = await card.query_selector("span.a-price-fraction")
        if price_whole and price_frac:
            price = f"{await price_whole.inner_text()}.{await price_frac.inner_text()}"
        else:
            price_elem = await card.query_selector("span.a-price")
            price = await price_elem.inner_text() if price_elem else "Unavailable"

        rating_elem = await card.query_selector("span.a-icon-alt")
        rating = await rating_elem.inner_text() if rating_elem else "No rating"

        return {
            "title": title.strip(),
            "url": link,
            "price": format_price(price),
            "rating": rating
        }
    except Exception:
        return None


async def scrape_category_products(category_name, url, limit=15):
    print(f"🔍 Scraping Bestsellers: {category_name}")
    try:
        async with async_playwright() as p:
            browser_type = get_browser_type(p)
            browser = await browser_type.launch(headless=True)
            context = await browser.new_context(
                java_script_enabled=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto(url, timeout=60000)
            await page.wait_for_selector("div.p13n-sc-uncoverable-faceout", timeout=15000)
            cards = await page.query_selector_all("div.p13n-sc-uncoverable-faceout")

            results = []
            seen_titles = set()
            for card in cards:
                data = await async_extract_product_data(card)
                if data and data["title"] not in seen_titles:
                    results.append(data)
                    seen_titles.add(data["title"])
                if len(results) >= limit:
                    break

            await browser.close()
            return results
    except Exception as e:
        print(f"⚠️ Failed to fetch page for {category_name}")
        return []


async def scrape_budget_picks(url, max_results=10):
    print("🔍 Scraping Budget Picks")
    try:
        async with async_playwright() as p:
            browser_type = get_browser_type(p)
            browser = await browser_type.launch(headless=True)
            context = await browser.new_context(
                java_script_enabled=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto(url, timeout=60000)
            await page.wait_for_selector("div.s-main-slot div[data-component-type='s-search-result']", timeout=15000)
            cards = await page.query_selector_all("div.s-main-slot div[data-component-type='s-search-result']")

            results = []
            seen_titles = set()
            for card in cards:
                data = await async_extract_product_data(card)
                if data and data["title"] not in seen_titles and "₹" in data["price"] and float(data["price"].replace("₹", "").replace(",", "")) <= 999:
                    results.append(data)
                    seen_titles.add(data["title"])
                if len(results) >= max_results:
                    break

            await browser.close()
            return results
    except Exception:
        return []


async def scrape_product_of_the_day(url):
    print("🔍 Scraping Product of the Day")
    try:
        async with async_playwright() as p:
            browser_type = get_browser_type(p)
            browser = await browser_type.launch(headless=True)
            context = await browser.new_context(
                java_script_enabled=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto(url, timeout=60000)
            await page.wait_for_selector("div.s-main-slot div[data-component-type='s-search-result']", timeout=15000)
            cards = await page.query_selector_all("div.s-main-slot div[data-component-type='s-search-result']")

            all_products = []
            seen_titles = set()
            for card in cards:
                data = await async_extract_product_data(card)
                if data and data["title"] not in seen_titles:
                    all_products.append(data)
                    seen_titles.add(data["title"])

            await browser.close()
            if not all_products:
                return None
            return sorted(all_products, key=lambda x: x["rating"], reverse=True)[0]
    except Exception:
        return None


async def scrape_single_combo_product(label, url):
    print(f"🌐 Scraping Combo Deal: {label}")
    try:
        async with async_playwright() as p:
            browser_type = get_browser_type(p)
            browser = await browser_type.launch(headless=True)
            context = await browser.new_context(
                java_script_enabled=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto(url, timeout=60000)
            await page.wait_for_selector("div.s-main-slot div[data-component-type='s-search-result']", timeout=15000)
            cards = await page.query_selector_all("div.s-main-slot div[data-component-type='s-search-result']")

            results = []
            seen_titles = set()
            for card in cards:
                data = await async_extract_product_data(card)
                if data and data["title"] not in seen_titles:
                    results.append(data)
                    seen_titles.add(data["title"])
                if len(results) >= 5:
                    break

            await browser.close()
            return label, results
    except Exception as e:
        print(f"❌ Error scraping combo: {e}")
        return label, []
