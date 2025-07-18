
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
    from modules.utils import apply_affiliate_tag, shorten_url, format_price

    try:
        title_elem = await card.query_selector("h2 a span")
        title = await title_elem.inner_text() if title_elem else "No title"

        link_elem = await card.query_selector("h2 a")
        link = await link_elem.get_attribute("href") if link_elem else ""
        raw_url = "https://www.amazon.in" + link
        affiliate_url = apply_affiliate_tag(raw_url)
        short_url = await shorten_url(affiliate_url)

        image_elem = await card.query_selector("img")
        image = await image_elem.get_attribute("src") if image_elem else ""

        price_elem = await card.query_selector("span.a-price > span.a-offscreen")
        price_str = await price_elem.inner_text() if price_elem else None

        mrp_elem = await card.query_selector("span.a-price.a-text-price > span.a-offscreen")
        mrp_str = await mrp_elem.inner_text() if mrp_elem else None

        rating_elem = await card.query_selector("span.a-icon-alt")
        rating = await rating_elem.inner_text() if rating_elem else ""

        # Discount percent
        discount_percent = None
        if price_str and mrp_str:
            try:
                price = float(price_str.replace("₹", "").replace(",", "").strip())
                mrp = float(mrp_str.replace("₹", "").replace(",", "").strip())
                if mrp > price:
                    discount_percent = round((mrp - price) / mrp * 100)
            except:
                pass

        # Extract ONLY Bank Offer from offers section
        bank_offer_text = None
        offers_section = await card.query_selector('div.vsx__offers.multipleProducts')
        if offers_section:
            offer_cards = await offers_section.query_selector_all('li.a-carousel-card')
            for offer_card in offer_cards:
                title_elem = await offer_card.query_selector('h6.offers-items-title')
                desc_elem = await offer_card.query_selector('span.a-truncate-full.a-offscreen')
                title_text = (await title_elem.inner_text()).strip() if title_elem else None
                desc_text = (await desc_elem.inner_text()).strip() if desc_elem else None
                if title_text == "Bank Offer" and desc_text:
                    bank_offer_text = desc_text
                    break  # stop after first bank offer found

        # Urgency flag (optional)
        urgency = None
        urgency_elem = await card.query_selector("span.a-color-price")
        if urgency_elem:
            urgency_text = await urgency_elem.inner_text()
            if any(keyword in urgency_text.lower() for keyword in ["limited", "only", "left"]):
                urgency = urgency_text

        return {
            "title": title.strip(),
            "url": affiliate_url,
            "short_url": short_url,
            "price": format_price(price_str),
            "original_price": format_price(mrp_str) if mrp_str else None,
            "discount_percent": f"{discount_percent}%" if discount_percent else None,
            "discount": f"{discount_percent}%" if discount_percent else None,
            "rating": rating.strip(),
            "urgency": urgency,
            "image": image,
            "bank_offer": bank_offer_text,  # Only bank offer text here
        }

    except Exception as e:
        print("Error in async_extract_product_data:", e)
        return None





async def scrape_category_products(category_name, url, limit=15):
    print(f"🔍 Scraping Bestsellers: {category_name}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
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
from modules.utils import get_browser_type, get_browser_context
from modules.prebuilt import BUDGET_PICK_CATEGORIES
from playwright.async_api import async_playwright

async def scrape_budget_products():
    selected = random.sample(list(BUDGET_PICK_CATEGORIES.items()), 5)
    results = []

    browser_type = get_browser_type()
    async with async_playwright() as p:
        browser = await browser_type.launch(headless=True)
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
                if len(results) == 5:
                    break  # Stop once 5 total products are collected

            except Exception as e:
                print(f"[Budget] Skipping {label} due to error: {e}")
                continue

        await browser.close()
    return results

