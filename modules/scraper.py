
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
async def async_extract_product_data(card):
    try:
        # ==== TITLE ====
        title_elem = await card.query_selector(
            'span[data-cy="title-recipe-title"], h2 a span, .p13n-sc-truncate-desktop-type2'
        )
        title = (await title_elem.inner_text()).strip() if title_elem else "No title"

        # ==== URL ====
        link_elem = await card.query_selector('h2 a, .a-link-normal')
        link = await link_elem.get_attribute("href") if link_elem else ""
        raw_url = "https://www.amazon.in" + link
        affiliate_url = apply_affiliate_tag(raw_url)
        short_url = shorten_url(affiliate_url)

        # ==== IMAGE ====
        img_elem = await card.query_selector('img[src*=".jpg"], img[src*=".png"]')
        image = await img_elem.get_attribute("src") if img_elem else ""

        # ==== PRICE ====
        price_elem = await card.query_selector(
            'span.a-price .a-offscreen, span.a-price-whole'
        )
        price_str = await price_elem.inner_text() if price_elem else None

        # ==== ORIGINAL / MRP ====
        mrp_elem = await card.query_selector(
            'span.a-price.a-text-price .a-offscreen'
        )
        mrp_str = await mrp_elem.inner_text() if mrp_elem else None

        # ==== RATING ====
        rating_elem = await card.query_selector('span.a-icon-alt')
        rating = await rating_elem.inner_text() if rating_elem else "N/A"

        return {
            "title": title,
            "url": affiliate_url,
            "short_url": short_url,
            "price": format_price(price_str),
            "original_price": format_price(mrp_str) if mrp_str else None,
            "discount": None,  # calculate later if needed
            "rating": rating,
            "image": image,
        }
    except Exception as e:
        print("🔍 Extract error:", e)
        return None





import httpx
import re

async def scrape_category_products(category_name, category_url, max_results=15):
    """
    Fetch bestseller JSON for the given category.
    Example endpoint pattern used by Amazon:
    https://www.amazon.in/api/s?k=<keyword>&s=exact-aware-popularity-rank
    """
    # Derive keyword from category (fallback to category name)
    keyword = re.sub(r"[^\w\s]", "", category_name).replace(" ", "+")
    api_url = (
        f"https://www.amazon.in/api/s?k={keyword}"
        "&s=exact-aware-popularity-rank&crid=1&sprefix={keyword}%2Caps%2C"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/119.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(api_url, headers=headers)
            r.raise_for_status()
            data = r.json()

        # Navigate to the right node
        items = (
            data.get("searchResult", {})
                .get("items", [])[:max_results]
        )

        products = []
        for itm in items:
            title = (
                itm.get("title", {}).get("display", "")
                or itm.get("title", "")  # fallback
            )
            price = (
                itm.get("price", {})
                   .get("current", {})
                   .get("display", "")
            )
            mrp = (
                itm.get("price", {})
                   .get("previous", {})
                   .get("display", "")
            )
            img = itm.get("image", {}).get("url", "")
            url = "https://www.amazon.in" + itm.get("url", "")
            rating = itm.get("rating", {}).get("display", "N/A")

            products.append({
                "title": title,
                "url": apply_affiliate_tag(url),
                "short_url": shorten_url(apply_affiliate_tag(url)),
                "price": price,
                "original_price": mrp if mrp and mrp != price else None,
                "discount": None,
                "rating": rating,
                "image": img,
                "bank_offer": None,
                "normal_offer": None,
                "urgency": None,
            })
        return products

    except Exception as e:
        print("❌ JSON scrape failed:", e)
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
                await page.goto(category_url, timeout=60000)
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

