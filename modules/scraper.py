import random
import re
import asyncio
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
    shorten_url,
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
            print(f"❌ Invalid URL found for product: {url}")
            return None

        # Title
        title_element = await link_element.query_selector("div") if link_element else None
        title = await title_element.inner_text() if title_element else None

        # Price (current price)
        price_element = await card.query_selector("span._cDEzb_p13n-sc-price_3mJ9Z")
        price = await price_element.inner_text() if price_element else None

        # Image
        img_element = await card.query_selector("img.p13n-sc-dynamic-image")
        image = await img_element.get_attribute("src") if img_element else None

        # Rating
        rating_element = await card.query_selector("span.a-icon-alt")
        rating = await rating_element.inner_text() if rating_element else None

        # Open individual product page
        product_page = await context.new_page()
        await product_page.goto(full_url, timeout=60000)
        await product_page.wait_for_load_state("load")

        # Original price (strikethrough price)
        original_price_element = await product_page.query_selector("span.a-price.a-text-price span.a-offscreen")
        original_price = await original_price_element.inner_text() if original_price_element else ""

        # Coupon
        coupon_element = await product_page.query_selector("#vpcButton input, span.a-color-success")
        coupon = await coupon_element.inner_text() if coupon_element else ""
        if not coupon:
            coupon = await coupon_element.get_attribute("value") if coupon_element else ""

        # Bank Offer (Delivery block)
        offer_element = await product_page.query_selector("div#mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE span")
        bank_offer = await offer_element.inner_text() if offer_element else ""

        # Deal label (Deal of the Day / Lightning Deal)
        deal_element = await product_page.query_selector('[id^="100_dealView_"] .a-text-bold')
        deal = await deal_element.inner_text() if deal_element else ""

        await product_page.close()

        return {
            "title": title,
            "url": full_url,
            "image": image,
            "price": price,
            "original_price": original_price,
            "rating": rating,
            "coupon": coupon.strip(),
            "bank_offer": bank_offer.strip(),
            "deal": deal.strip(),
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
from modules.utils import get_browser_type, get_browser_context
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import random

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from modules.utils import ensure_affiliate_tag, shorten_url
from modules.utils import get_browser_type, USER_AGENT
from modules.utils import deduplicate_variants

async def scrape_top5_per_category(category_name, category_url, fixed=False, max_results=15):
    print(f"🔍 Scraping {category_name}: {category_url}")
    browser = None

    try:
        async with async_playwright() as playwright:
            browser_type = get_browser_type(playwright)
            browser = await browser_type.launch(headless=True)

            context = await browser.new_context(
                java_script_enabled=True,
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()

            # Load category page
            await page.goto(category_url, timeout=60000)
            await page.wait_for_selector("div.zg-grid-general-faceout", timeout=30000)
            cards = await page.query_selector_all("div.zg-grid-general-faceout")

            print(f"🔎 Found {len(cards)} products under {category_name}")
            results, seen_titles = [], set()

            for card in cards:
                if len(results) >= max_results:
                    break

                data = await extract_product_data(card, context, category_name)
                if not data:
                    continue

                title, url = data.get("title"), data.get("url")
                if not isinstance(title, str) or not isinstance(url, str) or not url.startswith("http"):
                    print(f"⚠️ Skipping invalid product data: {data}")
                    continue

                if title in seen_titles:
                    continue

                seen_titles.add(title)

                try:
                    data["url"] = ensure_affiliate_tag(url)
                    data["short_url"] = await shorten_url(data["url"])
                    results.append(data)
                except Exception as url_err:
                    print(f"⚠️ Skipping due to URL error: {url_err}")
                    continue

            return results[:5]

    except Exception as e:
        print(f"❌ Error scraping {category_name}: {e}")
        try:
            await page.screenshot(path=f"top5_error_{category_name.lower().replace(' ', '_')}.png")
        except Exception:
            print(f"❌ Screenshot failed for category: {category_name}")

    finally:
        if browser:
            await browser.close()

    return []




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
                if product:
                    await browser.close()
                    return label, [product]

        except PlaywrightTimeoutError:
            await page.screenshot(path="hidden_gem_error.png")
        finally:
            await browser.close()

    return label, []
