import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from modules.prebuilt import COMBO_DEAL_CATEGORIES, HIDDEN_GEM_CATEGORIES
from modules.categories import FIXED_CATEGORIES, ROTATING_CATEGORIES
from modules.utils import (
    convert_price_to_float,
    add_label,
    shorten_url,
    ensure_affiliate_tag,
    get_browser_type,
    USER_AGENT,
    deduplicate_variants
)
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote


import random
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from modules.utils import (
    convert_price_to_float,
    ensure_affiliate_tag,
    get_browser_type,
    USER_AGENT,
)

# 🔍 Extract individual product data
async def extract_product_data(card, context, category_name):
    try:
        # Product link
        link_element = await card.query_selector("a.a-link-normal.aok-block")
        url = await link_element.get_attribute("href") if link_element else None
        full_url = f"https://www.amazon.in{url}" if url else None
        if not full_url:
            print(f"❌ Invalid URL found for product.")
            return None

        # Title
        title_element = await card.query_selector("._cDEzb_p13n-sc-css-line-clamp-3_g3dy1")
        title = await title_element.inner_text() if title_element else None
        if not title:
            print("❌ Skipping product with missing title.")
            return None

        # Price
        price_element = await card.query_selector("span._cDEzb_p13n-sc-price_3mJ9Z")
        price = await price_element.inner_text() if price_element else None
        if not price:
            print("❌ Skipping product with missing price.")
            return None

        # Image
        img_element = await card.query_selector("img.p13n-sc-dynamic-image")
        image = await img_element.get_attribute("src") if img_element else None

        # Rating
        rating_element = await card.query_selector("span.a-icon-alt")
        rating = await rating_element.inner_text() if rating_element else None

        # Visit product page
        product_page = await context.new_page()
        await product_page.goto(full_url, timeout=60000)
        await product_page.wait_for_load_state("load")

        # 1️⃣ Try standard MRP (strikethrough price)
        original_price_element = await product_page.query_selector("span.a-price.a-text-price span.a-offscreen")
        original_price = await original_price_element.inner_text() if original_price_element else ""

        # 2️⃣ Fallback to aria-hidden MRP
        if not original_price:
            fallback_elem = await product_page.query_selector("span[aria-hidden='true']")
            original_price = await fallback_elem.inner_text() if fallback_elem else ""

        # Bank Offer
        offer_element = await product_page.query_selector("div#mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE span")
        bank_offer = await offer_element.inner_text() if offer_element else ""

        # Deal Label (e.g., Deal of the Day)
        deal_element = await product_page.query_selector('[id^="100_dealView_"] .a-text-bold')
        deal = await deal_element.inner_text() if deal_element else ""

        # Discount calculation
        discount = ""
        try:
            clean_price = float(price.replace("₹", "").replace(",", "").strip())
            clean_original = float(original_price.replace("₹", "").replace(",", "").strip())
            if clean_original > clean_price:
                percent = round((clean_original - clean_price) / clean_original * 100)
                discount = f"{percent}% off"
        except Exception as e:
            print(f"⚠️ Could not calculate discount for {title}: {e}")

        await product_page.close()

        return {
            "title": title.strip(),
            "url": full_url,
            "image": image,
            "price": price.strip(),
            "original_price": original_price.strip(),
            "rating": rating.strip() if rating else "",
            "coupon": "",  # Skipped as per your request
            "bank_offer": bank_offer.strip(),
            "deal": deal.strip(),
            "discount": discount,
            "category": category_name,
        }

    except Exception as e:
        print(f"❌ Error extracting data for product: {e}")
        return None





async def scrape_single_combo_product():
    combo = random.choice(COMBO_DEAL_CATEGORIES)
    label, url = combo['label'], combo['url']

    async with async_playwright() as p:
        browser_type = get_browser_type(p)
        browser = await browser_type.launch(headless=True)
        context = await get_browser_context(browser_type) 
        page = await context.new_page()

        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_selector('div[data-cy="asin-faceout-container"]', timeout=30000)
            cards = await page.query_selector_all('div[data-cy="asin-faceout-container"]')
            random.shuffle(cards)

            for card in cards:
                data = await extract_product_data(card, context, category_name)
                if data and data['url'] and data['image']:
                    await browser.close()
                    return label, [data]

        except PlaywrightTimeoutError:
            await page.screenshot(path="combo_error.png")
        finally:
            await browser.close()

    return label, []

async def scrape_product_of_the_day():
    url = "https://www.amazon.in/s?i=computers&rh=n%3A1377374031&fs=true"
    async with async_playwright() as p:
        browser_type = get_browser_type(p)
        browser = await browser_type.launch(headless=True)
        context = await get_browser_context(browser_type) 
        page = await context.new_page()

        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_selector('div[data-cy="asin-faceout-container"]', timeout=30000)
            cards = await page.query_selector_all('div[data-cy="asin-faceout-container"]')

            all_data = []
            for card in cards:
                data = await extract_product_data(card, context, category_name)
                if data and data["price"] and data["original_price"]:
                    try:
                        price_val = convert_price_to_float(data["price"])
                        original_price_val = convert_price_to_float(data["original_price"])
                        discount_pct = round((original_price_val - price_val) / original_price_val * 100)
                        if discount_pct >= 20:
                            data["discount"] = f"{discount_pct}% off"
                            all_data.append(data)
                    except:
                        pass

            sorted_data = sorted(all_data, key=lambda d: convert_price_to_float(d["price"]))
            return sorted_data[:1]

        except PlaywrightTimeoutError:
            await page.screenshot(path="potd_error.png")
        finally:
            await browser.close()

    return []

from modules.categories import FIXED_CATEGORIES, ROTATING_CATEGORIES
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import random
import re
from modules.utils import get_soup_from_url, convert_price_to_float, deduplicate_variants, ensure_affiliate_tag, get_browser_type, USER_AGENT, get_browser_context

async def scrape_top5_per_category(category_name, category_url, context, fixed=False, max_results=15):
    print(f"🔍 Scraping Bestsellers: {category_name}")

    soup = await get_soup_from_url(category_url)
    if soup is None:
        print(f"⚠️ Failed to fetch page for {category_name}")
        return []

    product_cards = soup.select("div.p13n-sc-uncoverable-faceout")
    if not product_cards:
        print(f"⚠️ No product cards found for {category_name}")
        return []

    # Open bestseller page in browser context so we can use Playwright to extract from card
    page = await context.new_page()
    await page.goto(category_url, timeout=60000)
    await page.wait_for_load_state("load")

    cards = await page.query_selector_all("div.p13n-sc-uncoverable-faceout")
    seen_titles = set()
    products = []

    for card in cards:
        try:
            product = await extract_product_data(card, context, category_name)
            if product and product["title"] not in seen_titles:
                seen_titles.add(product["title"])
                products.append(product)
            if len(products) >= 20:
                break
        except Exception as e:
            print(f"⚠️ Error extracting product from card: {e}")
            continue

    await page.close()

    if not products:
        print(f"⚠️ No valid products scraped for: {category_name}")
        return []

    deduped = deduplicate_variants(products)
    return deduped[:max_results]






async def scrape_budget_products():
    results = []
    for label, url in TOP5_CATEGORIES.items():
        async with async_playwright() as p:
            browser_type = get_browser_type(p)
            browser = await browser_type.launch(headless=True)
            context = await get_browser_context(browser_type) 
            page = await context.new_page()

            try:
                await page.goto(url, timeout=60000)
                await page.wait_for_selector('div[data-cy="asin-faceout-container"]', timeout=30000)
                cards = await page.query_selector_all('div[data-cy="asin-faceout-container"]')

                for card in cards:
                    product = await extract_product_data(card, context, category_name)
                    if product and product["price"]:
                        try:
                            price_val = convert_price_to_float(product["price"])
                            if price_val <= 999:
                                results.append((label, product))
                                break
                        except:
                            continue

            except PlaywrightTimeoutError:
                await page.screenshot(path=f"budget_error_{label}.png")
            finally:
                await browser.close()

    return results

async def scrape_hidden_gem():
    category = random.choice(HIDDEN_GEM_CATEGORIES)
    label, url = category["label"], category["url"]

    async with async_playwright() as p:
        browser_type = get_browser_type(p)
        browser = await browser_type.launch(headless=True)
        context = await get_browser_context(browser_type) 
        page = await context.new_page()

        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_selector('div[data-cy="asin-faceout-container"]', timeout=30000)
            cards = await page.query_selector_all('div[data-cy="asin-faceout-container"]')
            random.shuffle(cards)

            for card in cards:
                product = await extract_product_data(card, context, category_name)
                if product and product.get("image"):
                    await browser.close()
                    return label, [product]

        except PlaywrightTimeoutError:
            await page.screenshot(path="hidden_gem_error.png")
        finally:
            await browser.close()

    return label, []
