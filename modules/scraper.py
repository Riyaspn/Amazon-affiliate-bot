
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





import random
import asyncio
from modules.utils import get_browser_type

async def scrape_top5_per_category(category, url):
    try:
        browser_type = get_browser_type()
        browser = await browser_type.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            java_script_enabled=True,
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        await page.goto(url, timeout=60000)
        await page.wait_for_selector('div[data-cy="asin-faceout-container"]', timeout=15000)

        cards = await page.query_selector_all('div[data-cy="asin-faceout-container"]')

        # Fallback if primary selector fails
        if not cards or len(cards) < 5:
            print(f"⚠️ Fallback selector used for: {category}")
            cards = await page.query_selector_all('div.s-result-item[data-component-type="s-search-result"]')

        if not cards:
            await page.screenshot(path=f"top5_error_{category.lower().replace(' ', '_')}.png")
            print(f"⚠️ No product cards found for {category}")
            await browser.close()
            return []

        # Deduplicate and shuffle
        unique = []
        seen_titles = set()
        for card in cards:
            data = await async_extract_product_data(card)
            if data and data['title'] not in seen_titles:
                unique.append(data)
                seen_titles.add(data['title'])
            if len(unique) >= 15:
                break

        await browser.close()

        # Pick top 5 random from cleaned list
        return random.sample(unique, k=min(5, len(unique)))

    except Exception as e:
        print(f"❌ Error scraping category {category}: {e}")
        await page.screenshot(path=f"top5_error_{category.lower().replace(' ', '_')}_exception.png")
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

