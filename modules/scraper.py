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


async def extract_product_data(card, context, category_name, markdown=False, detail_page=None):
    try:
        # === CARD ELEMENTS ===
        link_element = await card.query_selector("a.a-link-normal.aok-block")
        url = await link_element.get_attribute("href") if link_element else None
        full_url = ensure_affiliate_tag(f"https://www.amazon.in{url}") if url else None
        if not full_url:
            return None

        title_element = await card.query_selector("._cDEzb_p13n-sc-css-line-clamp-3_g3dy1")
        title = await title_element.inner_text() if title_element else None
        if not title:
            return None

        price_element = await card.query_selector("span._cDEzb_p13n-sc-price_3mJ9Z")
        price = await price_element.inner_text() if price_element else None
        if not price:
            return None

        img_element = await card.query_selector("img.p13n-sc-dynamic-image")
        image_url = await img_element.get_attribute("src") if img_element else None
        image = f"[‎]({image_url})" if markdown and image_url else image_url

        rating_element = await card.query_selector("span.a-icon-alt")
        rating = await rating_element.inner_text() if rating_element else None

        # === DETAIL PAGE ===
        product_page = detail_page or await context.new_page()
        await product_page.goto(full_url, timeout=20000)
        await product_page.wait_for_load_state("domcontentloaded")
        await product_page.keyboard.press("End")
        await product_page.wait_for_timeout(1000)

        mrp_element = await product_page.query_selector('span.basisPrice span.a-price.a-text-price span.a-offscreen') \
                      or await product_page.query_selector('span.a-price.a-text-price span.a-offscreen')
        original_price = await mrp_element.inner_text() if mrp_element else ""

        deal_element = await product_page.query_selector('[id^="100_dealView_"] .a-text-bold')
        deal = await deal_element.inner_text() if deal_element else ""

        # === OFFERS: Bank & Cashback ===
        bank_offer, normal_offer = "", ""

        try:
            offer_spans = await product_page.query_selector_all("span.a-truncate-full.a-offscreen")
            for span in offer_spans:
                text = (await span.inner_text()).strip()
                lower = text.lower()
                if "cashback" in lower and not normal_offer:
                    normal_offer = text
                elif any(k in lower for k in ["bank", "credit", "debit", "instant", "upi"]) and not bank_offer:
                    bank_offer = text
        except Exception as e:
            print(f"⚠️ Offer span error: {e}")

        # === Fallback: Modal carousel ===
        if not bank_offer or not normal_offer:
            try:
                vse_container = await product_page.query_selector('#vse-offers-container')
                if vse_container:
                    await product_page.evaluate("""
                        const el = document.querySelector('#vse-offers-container');
                        if (el && window.getComputedStyle(el).display === 'none') {
                            el.style.display = 'block';
                        }
                    """)
                    await vse_container.scroll_into_view_if_needed()
                    await product_page.wait_for_timeout(800)

                    carousel_items = await vse_container.query_selector_all("li.a-carousel-card")
                    for item in carousel_items:
                        title_elem = await item.query_selector("h6.offers-items-title")
                        title_text = (await title_elem.inner_text()).strip().lower() if title_elem else ""

                        visible_offer_elem = await item.query_selector("span.a-truncate-full.a-offscreen")
                        visible_offer = (await visible_offer_elem.inner_text()).strip() if visible_offer_elem else ""

                        if "cashback" in title_text and not normal_offer and visible_offer:
                            normal_offer = visible_offer
                        elif any(k in title_text for k in ["bank", "credit", "debit", "upi"]) and not bank_offer and visible_offer:
                            bank_offer = visible_offer

                        if not (bank_offer and normal_offer):
                            click_trigger = await item.query_selector("span.a-declarative")
                            if click_trigger:
                                await click_trigger.click()
                                await product_page.wait_for_selector("#tp-side-sheet-main-section", timeout=3000)
                                await product_page.wait_for_timeout(800)

                                offer_blocks = await product_page.query_selector_all(
                                    "#tp-side-sheet-main-section .vsx-offers-desktop-lv__item p"
                                )
                                for offer_elem in offer_blocks:
                                    offer = (await offer_elem.inner_text()).strip()
                                    offer_l = offer.lower()
                                    if "cashback" in offer_l and not normal_offer:
                                        normal_offer = offer
                                    elif any(k in offer_l for k in ["bank", "credit", "debit", "upi", "instant"]) and not bank_offer:
                                        bank_offer = offer

                                close_btn = await product_page.query_selector("button[aria-label='Close']")
                                if close_btn:
                                    await close_btn.click()
                                    await product_page.wait_for_timeout(500)
            except Exception as e:
                print(f"⚠️ Carousel fallback error: {e}")

        # === Fallback: Static offer blocks ===
        if not bank_offer or not normal_offer:
            try:
                offer_blocks = await product_page.query_selector_all('div[id^="GCCashback"], div[id^="InstantBankDiscount"]')
                for block in offer_blocks:
                    title_elem = await block.query_selector("h1")
                    title_text = (await title_elem.inner_text()).strip().lower() if title_elem else ""
                    para_elems = await block.query_selector_all("p")
                    for p in para_elems:
                        line = (await p.inner_text()).strip()
                        l = line.lower()
                        if "cashback" in title_text and not normal_offer:
                            normal_offer = line
                        elif any(k in title_text for k in ["bank", "credit", "debit", "upi", "instant"]) and not bank_offer:
                            bank_offer = line
            except Exception as e:
                print(f"⚠️ Static offer block error: {e}")

        if not detail_page:
            await product_page.close()

        # === Discount Calculation ===
        discount = ""
        try:
            p = convert_price_to_float(price)
            op = convert_price_to_float(original_price)
            if op > p:
                discount = f"{round((op - p) / op * 100)}% off"
        except:
            pass

        # === Format Clean Offer Line ===
        offer_text = format_offer_line({
            "bank_offer": bank_offer,
            "normal_offer": normal_offer
        })

        return {
            "title": title.strip(),
            "url": full_url,
            "image": image,
            "price": price.strip(),
            "original_price": original_price.strip(),
            "rating": rating.strip() if rating else "",
            "bank_offer": bank_offer,
            "normal_offer": normal_offer,
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
async def scrape_hidden_gem(category_url, label="Hidden Gem"):
    """
    Scrapes one product (with image) from the supplied hidden gem category URL.
    Returns: (label, [product_dict]) or (label, []) if none found.
    """
    url = category_url

    async with async_playwright() as p:
        browser_type = get_browser_type(p)
        browser, context = await get_browser_context(browser_type)  # <-- Proper unpack
        page = await context.new_page()

        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_selector('div[data-cy="asin-faceout-container"]', timeout=30000)
            cards = await page.query_selector_all('div[data-cy="asin-faceout-container"]')
            if not cards:
                print("No product cards found.")
                return label, []

            random.shuffle(cards)  # Adds randomness for variety

            for card in cards:
                product = await extract_product_data(card, context, label)
                # Ensure product has an image and key details
                if product and product.get("image"):
                    await browser.close()
                    return label, [product]

        except PlaywrightTimeoutError as e:
            print(f"Playwright Timeout scraping hidden gem: {e}")
            await page.screenshot(path="hidden_gem_error.png")
        except Exception as e:
            print(f"Unexpected scraping error: {e}")
        finally:
            await browser.close()

    # If we reach here, nothing was found
    return label, []


    return label, []



