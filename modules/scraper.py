
import random
import time
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from modules.utils import (
    apply_affiliate_tag,
    shorten_url,
    simplify_title,
    format_price,
    get_browser_context,
)
from modules.prebuilt import BUDGET_PICK_CATEGORIES

# Shared product extraction function
# scraper.py
async def async_extract_product_data(card):
    try:
        title = await card.query_selector_eval('h2 span', 'el => el.innerText') if await card.query_selector('h2 span') else None
        url_suffix = await card.query_selector_eval('h2 a', 'el => el.getAttribute("href")') if await card.query_selector('h2 a') else None
        url = f"https://www.amazon.in{url_suffix.split('?')[0]}" if url_suffix else None

        # Extract current price
        price_whole = await card.query_selector_eval('.a-price-whole', 'el => el.innerText') if await card.query_selector('.a-price-whole') else None
        price_fraction = await card.query_selector_eval('.a-price-fraction', 'el => el.innerText') if await card.query_selector('.a-price-fraction') else "00"
        current_price = f"{price_whole}.{price_fraction}" if price_whole else None

        # Extract original price (MRP)
        original_price_raw = await card.query_selector_eval('.a-price.a-text-price span', 'el => el.innerText') if await card.query_selector('.a-price.a-text-price span') else None
        original_price = original_price_raw.replace("₹", "").replace(",", "").strip() if original_price_raw else None

        # Calculate discount
        discount = None
        if original_price and current_price:
            try:
                original = float(original_price)
                current = float(current_price.replace(",", ""))
                discount = int(round(((original - current) / original) * 100))
            except:
                discount = None

        # Extract normal offer text
        normal_offer = None
        if await card.query_selector('.a-row.a-size-base.a-color-secondary span'):
            normal_offer = await card.query_selector_eval('.a-row.a-size-base.a-color-secondary span', 'el => el.innerText')

        # Extract bank offer (e.g., SBI card deal)
        bank_offer = None
        bank_offer_selector = 'span[class*="dealBadgeText"]'
        if await card.query_selector(bank_offer_selector):
            bank_offer = await card.query_selector_eval(bank_offer_selector, 'el => el.innerText')

        return {
            "title": title.strip() if title else None,
            "url": url,
            "price": f"₹{current_price}" if current_price else None,
            "original_price": f"₹{original_price}" if original_price else None,
            "discount": f"{discount}% OFF" if discount else None,
            "normal_offer": normal_offer.strip() if normal_offer else None,
            "bank_offer": bank_offer.strip() if bank_offer else None,
        }

    except Exception as e:
        print(f"❌ Error extracting product data: {e}")
        return None



async def scrape_top5_per_category(category_name, category_url, max_results=15):
    from playwright.async_api import async_playwright
    from modules.utils import shorten_url, ensure_affiliate_tag
    from modules.browser import get_browser_type, USER_AGENT

    print(f"🔍 Scraping {category_name}: {category_url}")
    page = None  # Must define before try

    try:
        async with async_playwright() as p:
            browser_type = get_browser_type(p)  # ✅ Fix here
            browser = await browser_type.launch(headless=True)

            context = await browser.new_context(
                java_script_enabled=True,
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()

            await page.goto(url, timeout=60000)
            await page.wait_for_selector('div[data-cy="asin-faceout-container"]', timeout=20000)

            cards = await page.query_selector_all('div[data-cy="asin-faceout-container"]')

            print(f"🔎 Found {len(cards)} products under {category_name}")
            results = []
            seen_titles = set()

            for card in cards:
                if len(results) >= max_results:
                    break

                data = await async_extract_product_data(card)
                if not data or data["title"] in seen_titles:
                    continue

                seen_titles.add(data["title"])
                data["url"] = ensure_affiliate_tag(data["url"])
                data["short_url"] = await shorten_url(data["url"])
                results.append(data)

            await browser.close()
            return results[:5]  # Return top 5 only

    except Exception as e:
        print(f"❌ Error scraping category_name {category_name}: {e}")
        if page:
            await page.screenshot(path=f"top5_error_{category_name.lower().replace(' ', '_')}_exception.png")
        return []












async def scrape_product_of_the_day(url):
    print("🔍 Scraping Product of the Day")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
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
            browser = await p.chromium.launch(headless=True)
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




import random
from modules.utils import apply_affiliate_tag, shorten_url
from modules.prebuilt import BUDGET_PICK_CATEGORIES
from playwright.async_api import async_playwright

async def scrape_budget_products():
    selected = random.sample(list(BUDGET_PICK_CATEGORIES.items()), 5)
    results = []

    browser = await p.chromium.launch(headless=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await get_browser_context(browser)
        page = await context.new_page()

        for label, url in selected:
            try:
                await page.goto(url, timeout=60000)
                await page.wait_for_selector('div[data-cy="asin-faceout-container"]', timeout=15000)

                cards = await page.query_selector_all('div[data-cy="asin-faceout-container"]')
                for card in cards:
                    product = await async_extract_product_data(card)
                    if product and product.get("price") and product.get("price") < 999:
                        product["url"] = await shorten_url(apply_affiliate_tag(product["url"]))
                        results.append((label, product))
                        break  # Only one product per category
                if len(results) >= max_results:
                    break  # Stop once 5 total products are collected

            except Exception as e:
                print(f"[Budget] Skipping {label} due to error: {e}")
                continue

        await browser.close()
    return results

