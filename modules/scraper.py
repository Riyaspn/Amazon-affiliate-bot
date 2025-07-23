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
            print(f"❌ Invalid URL found for product: {url}")
            return None

        # Title (more specific selector from card)
        title_element = await card.query_selector("._cDEzb_p13n-sc-css-line-clamp-3_g3dy1")
        title = await title_element.inner_text() if title_element else None
        if not title:
            print("❌ Skipping product with missing title.")
            return None

        # Price (current price)
        price_element = await card.query_selector("span._cDEzb_p13n-sc-price_3mJ9Z")
        price = await price_element.inner_text() if price_element else None
        if not price:
            print("❌ Skipping product with missing price.")
            return None

        # Image
        img_element = await card.query_selector("img.p13n-sc-dynamic-image")
        image = await img_element.get_attribute("src") if img_element else None
        if not image:
            print(f"⚠️ No image found for product: {title}")


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
        if coupon_element:
            try:
                coupon = await coupon_element.inner_text()
            except:
                coupon = await coupon_element.get_attribute("value")
        else:
            coupon = ""

        # Bank Offer (Delivery block)
        offer_element = await product_page.query_selector("div#mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE span")
        bank_offer = await offer_element.inner_text() if offer_element else ""

        # Deal label (Deal of the Day / Lightning Deal)
        deal_element = await product_page.query_selector('[id^="100_dealView_"] .a-text-bold')
        deal = await deal_element.inner_text() if deal_element else ""

        await product_page.close()

        return {
            "title": title.strip(),
            "url": full_url,
            "image": image,
            "price": price.strip(),
            "original_price": original_price.strip(),
            "rating": rating.strip() if rating else "",
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
from modules.utils import ensure_affiliate_tag
from modules.utils import get_browser_type, USER_AGENT
from modules.utils import deduplicate_variants

import re
from modules.utils import get_soup_from_url, convert_price_to_float, deduplicate_variants, ensure_affiliate_tag

async def scrape_top5_per_category(category_name, url, num_products=5, category_url=None):
    print(f"🔍 Scraping Bestsellers: {category_name}")
    soup = await get_soup_from_url(url)
    if soup is None:
        print(f"⚠️ Failed to fetch page for {category_name}")
        return []

    product_cards = soup.select("div.p13n-sc-uncoverable-faceout")
    seen_titles = set()
    products = []

    for card in product_cards:
        try:
            title_elem = card.select_one("._cDEzb_p13n-sc-css-line-clamp-3_g3dy1") or card.select_one("._cDEzb_p13n-sc-css-line-clamp-4_2q2cc")
            price_elem = card.select_one("._cDEzb_p13n-sc-price_3mJ9Z") or card.select_one("span.a-price > span.a-offscreen")
            rating_elem = card.select_one("span.a-icon-alt")
            link_elem = card.select_one("a[href]")

            discount_elem = card.select_one("span.a-letter-space + span")  # Sometimes appears with coupon
            bank_offer_elem = card.select_one("span.a-color-base")         # Bank offer text
            normal_offer_elem = card.select_one("span.a-text-bold")       # "Deal of the day" style tag

            title = title_elem.text.strip() if title_elem else None
            price = price_elem.text.strip() if price_elem else None
            rating = rating_elem.text.strip() if rating_elem else "⭐ N/A"
            discount = discount_elem.text.strip() if discount_elem else ""
            bank_offer = bank_offer_elem.text.strip() if bank_offer_elem else ""
            normal_offer = normal_offer_elem.text.strip() if normal_offer_elem else ""

            url_suffix = link_elem['href'].split('?')[0] if link_elem else None
            product_url = f"https://www.amazon.in{url_suffix}" if url_suffix else None
            if product_url:
                product_url = ensure_affiliate_tag(product_url)

            if not title or not price or not product_url:
                continue

            try:
                price_value = convert_price_to_float(price)
            except:
                price_value = None

            product = {
                "title": title,
                "price": price,
                "rating": rating,
                "url": product_url,
                "label": "🔥 Hot Deal",
                "category": category_name,
                "price_value": price_value,
                "discount": discount,
                "bank_offer": bank_offer,
                "normal_offer": normal_offer
            }

            if title not in seen_titles:
                seen_titles.add(title)
                products.append(product)

            if len(products) >= 20:  # Collect more to allow for filtering and deduping
                break

        except Exception as e:
            print(f"⚠️ Error processing a product card in {category_name}: {e}")
            continue

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
