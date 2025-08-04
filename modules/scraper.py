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
    deduplicate_variants,
    format_offer_line
)
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
import random
import asyncio


# 🔍 Extract individual product data


import re

async def extract_product_data(card, context, category_name, markdown=False, detail_page=None):
    try:
        # --- Product Link ---
        link_element = (
            await card.query_selector("a.a-link-normal.aok-block") or
            await card.query_selector("a.a-link-normal")
        )
        url = await link_element.get_attribute("href") if link_element else None
        if url and not url.startswith("http"):
            url = "https://www.amazon.in" + url
        full_url = ensure_affiliate_tag(url) if url else None
        if not full_url:
            return None

        # --- Product Title ---
        title_element = (
            await card.query_selector("._cDEzb_p13n-sc-css-line-clamp-3_g3dy1") or
            await card.query_selector("h2.a-size-base-plus") or
            await card.query_selector("span.a-text-normal")
        )
        title = await title_element.inner_text() if title_element else None
        if not title:
            return None

        # --- Product Price ---
        price_element = (
            await card.query_selector("span._cDEzb_p13n-sc-price_3mJ9Z") or
            await card.query_selector("span.a-price > span.a-offscreen") or
            await card.query_selector("span.a-offscreen")
        )
        price = await price_element.inner_text() if price_element else None
        if not price:
            return None

        # --- Product Image ---
        img_element = (
            await card.query_selector("img.p13n-sc-dynamic-image") or
            await card.query_selector("img.s-image")
        )
        image_url = await img_element.get_attribute("src") if img_element else None
        image = f"[‎]({image_url})" if markdown and image_url else image_url

        # --- Rating ---
        rating_element = await card.query_selector("span.a-icon-alt")
        rating = await rating_element.inner_text() if rating_element else ""

        # === DETAIL PAGE ===
        product_page = detail_page or await context.new_page()
        await product_page.goto(full_url, timeout=20000)
        await product_page.wait_for_load_state("domcontentloaded")
        await product_page.keyboard.press("End")
        await product_page.wait_for_timeout(1000)

        # --- MRP ---
        mrp_element = (
            await product_page.query_selector('span.basisPrice span.a-price.a-text-price span.a-offscreen') or
            await product_page.query_selector('span.a-price.a-text-price span.a-offscreen') or
            await product_page.query_selector('span.a-text-price span.a-offscreen')
        )
        original_price = await mrp_element.inner_text() if mrp_element else ""

        # --- Deal Tag ---
        deal_element = (
            await product_page.query_selector('[id^="100_dealView_"] .a-text-bold') or
            await product_page.query_selector('span.a-badge-text')
        )
        deal = await deal_element.inner_text() if deal_element else ""

        # --- OFFERS: Robust Cashback & Bank Offer Extraction ---
        bank_offer, cashback = "", ""
        try:
            # 1. Try the prominent offers tiles
            offer_tiles = await product_page.query_selector_all('div[data-csa-c-type="widget"] div, div.a-box-group div')
            for tile in offer_tiles:
                tile_text = (await tile.inner_text()).strip().lower()
                # Cashback parsing
                if ("cashback" in tile_text or "amazon pay" in tile_text) and not cashback:
                    match = re.search(r'₹[\d,.]+', tile_text)
                    if match:
                        cashback = f"Upto {match.group(0)} cashback as Amazon Pay Balance"
                    else:
                        # Use the full line if regex fails
                        cashback_lines = [
                            line for line in tile_text.split("\n")
                            if ("cashback" in line or "amazon pay" in line) and "₹" in line
                        ]
                        if cashback_lines:
                            cashback = cashback_lines[0].capitalize()
                # Bank offer parsing
                if any(bank_kw in tile_text for bank_kw in ["bank", "credit", "debit", "upi", "sbi", "icici"]) and not bank_offer:
                    match = re.search(r'₹[\d,.]+', tile_text)
                    if match:
                        bank_offer = f"Upto {match.group(0)} off on select cards"
                    else:
                        bank_lines = [
                            line for line in tile_text.split("\n")
                            if any(bk in line for bk in ["bank", "credit", "debit", "upi", "sbi", "icici"]) and "₹" in line
                        ]
                        if bank_lines:
                            bank_offer = bank_lines[0].capitalize()
            # Short-circuit if both found
            if bank_offer or cashback:
                await product_page.close()
                offer_text = format_offer_line({"bank_offer": bank_offer, "normal_offer": cashback})
                return {
                    "title": title.strip(),
                    "url": full_url,
                    "image": image,
                    "price": price.strip(),
                    "original_price": original_price.strip(),
                    "rating": rating.strip() if rating else "",
                    "bank_offer": bank_offer,
                    "normal_offer": cashback,
                    "clean_offer": offer_text,
                    "deal": deal.strip(),
                    "discount": "",
                    "category": category_name,
                }
        except Exception as e:
            print(f"⚠️ Offers tile extraction error: {e}")

        # 2. Fallback: extract from visible spans
        try:
            offer_spans = await product_page.query_selector_all("span.a-truncate-full.a-offscreen, span.a-truncate-full")
            for span in offer_spans:
                text = (await span.inner_text()).strip()
                lower = text.lower()
                if "cashback" in lower and not cashback:
                    m = re.search(r'₹[\d,.]+', text)
                    cashback = text if m else cashback
                elif any(k in lower for k in ["bank", "credit", "debit", "instant", "upi", "sbi", "icici"]) and not bank_offer:
                    m = re.search(r'₹[\d,.]+', text)
                    bank_offer = text if m else bank_offer
        except Exception as e:
            print(f"⚠️ Offer span error: {e}")

        # 3. Fallback: static special promo blocks
        try:
            static_blocks = await product_page.query_selector_all('div[id^="GCCashback"], div[id^="InstantBankDiscount"]')
            for block in static_blocks:
                block_text = (await block.inner_text()).strip().lower()
                if "cashback" in block_text and "₹" in block_text and not cashback:
                    cashback = block_text.capitalize()
                if any(k in block_text for k in ["bank", "credit", "debit", "card", "upi", "sbi", "icici"]) and "₹" in block_text and not bank_offer:
                    bank_offer = block_text.capitalize()
        except Exception as e:
            print(f"⚠️ Static offer block error: {e}")

        # --- Discount Calculation ---
        discount = ""
        try:
            p = convert_price_to_float(price)
            op = convert_price_to_float(original_price)
            if op > p:
                discount = f"{round((op - p) / op * 100)}% off"
        except:
            pass

        # --- Format Clean Offer Line ---
        offer_text = format_offer_line({
            "bank_offer": bank_offer,
            "normal_offer": cashback
        })

        if not detail_page:
            await product_page.close()

        return {
            "title": title.strip(),
            "url": full_url,
            "image": image,
            "price": price.strip(),
            "original_price": original_price.strip(),
            "rating": rating.strip() if rating else "",
            "bank_offer": bank_offer,
            "normal_offer": cashback,
            "clean_offer": offer_text,
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

    page = await context.new_page()
    await page.goto(category_url, timeout=30000)
    await page.wait_for_load_state("domcontentloaded", timeout=10000)

    cards = await page.query_selector_all("div.p13n-sc-uncoverable-faceout")
    if not cards:
        print(f"⚠️ No cards for {category_name}")
        await page.close()
        return []

    seen_titles = set()
    products = []
    detail_page = await context.new_page()

    for card in cards[:20]:  # Limit scraping for speed
        try:
            product = await extract_product_data(card, context, category_name, detail_page=detail_page)
            if product and product["title"] not in seen_titles:
                seen_titles.add(product["title"])
                products.append(product)
            if len(products) >= max_results:
                break
        except Exception as e:
            print(f"⚠️ Error on product: {e}")

    await detail_page.close()
    await page.close()

    if not products:
        print(f"⚠️ No valid products scraped for: {category_name}")
        return []

    return deduplicate_variants(products)[:max_results]






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

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import random
from modules.utils import get_browser_type

# Optional: pass label for product's category_name
async def scrape_hidden_gem(category_url, category_display, label="Hidden Gem"):
    url = category_url

    async with async_playwright() as p:
        browser_type = get_browser_type(p)
        browser, context = await get_browser_context(browser_type)
        page = await context.new_page()

        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_selector('div[data-cy="asin-faceout-container"]', timeout=30000)
            cards = await page.query_selector_all('div[data-cy="asin-faceout-container"]')
            if not cards:
                print("No product cards found.")
                return label, []

            random.shuffle(cards)

            for card in cards:
                product = await extract_product_data(card, context, label)
                if product and product.get("image"):
                    product["category_url"] = url  # always include affiliate tag here!
                    product["category_display"] = category_display  # <-- added
                    await browser.close()
                    return label, [product]

        except PlaywrightTimeoutError as e:
            print(f"Playwright Timeout scraping hidden gem: {e}")
            await page.screenshot(path="hidden_gem_error.png")
        except Exception as e:
            print(f"Unexpected scraping error: {e}")
        finally:
            await browser.close()

    return label, []






