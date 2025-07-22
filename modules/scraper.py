import random
import re
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from modules.prebuilt import COMBO_DEAL_CATEGORIES, HIDDEN_GEM_CATEGORIES
from modules.categories import FIXED_CATEGORIES, ROTATING_CATEGORIES
from modules.utils import convert_price_to_float

from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from modules.utils import shorten_url, add_label, ensure_affiliate_tag

async def extract_product_data(page, max_products=10):
    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    
    containers = soup.select("div.p13n-sc-uncoverable-faceout, div.zg-grid-general-faceout, div._cDEzb_znj4z_1i3hH")  # fallback selectors
    products = []

    for container in containers:
        if len(products) >= max_products:
            break

        try:
            title_elem = container.select_one("div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1")
            price_elem = container.select_one("span.a-price > span.a-offscreen")
            original_price_elem = container.select_one("span.a-text-price > span.a-offscreen")
            rating_elem = container.select_one("span.a-icon-alt")
            image_elem = container.select_one("img")
            link_elem = container.select_one("a.a-link-normal")

            # New selectors for badges and bank/card offers
            badge_elem = container.select_one("span.a-badge-text")
            offer_elem = container.select_one("span.a-color-secondary, span.a-color-price")

            if not all([title_elem, price_elem, rating_elem, image_elem, link_elem]):
                continue

            title = title_elem.get_text(strip=True)
            price = price_elem.get_text(strip=True)
            original_price = original_price_elem.get_text(strip=True) if original_price_elem else None
            rating = rating_elem.get_text(strip=True)
            image = image_elem["src"]
            url_suffix = link_elem["href"]

            if "/sspa/" in url_suffix:
                continue  # skip sponsored

            full_url = f"https://www.amazon.in{url_suffix}"
            affiliate_url = shorten_url(ensure_affiliate_tag(full_url))

            badge_text = badge_elem.get_text(strip=True) if badge_elem else None
            offer_text = offer_elem.get_text(strip=True) if offer_elem else None

            products.append({
                "title": title,
                "price": price,
                "original_price": original_price,
                "rating": rating,
                "image": image,
                "url": affiliate_url,
                "label": add_label({"price": price, "rating": rating}),
                "badge": badge_text,
                "offer": offer_text
            })

        except Exception as e:
            print(f"⚠️ Error parsing product: {e}")
            continue

    return products






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
                data = await async_extract_product_data(card)
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
                data = await async_extract_product_data(card)
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
    page = None
    browser = None

    try:
        async with async_playwright() as playwright:
            # Setup browser
            browser_type = get_browser_type(playwright)
            browser = await browser_type.launch(headless=True)

            context = await browser.new_context(
                java_script_enabled=True,
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()

            # Load category page
            await page.goto(category_url, timeout=60000)
            await page.wait_for_selector("div.zg-grid-general-faceout", timeout=30000)
            cards = await page.query_selector_all("div.zg-grid-general-faceout")

            print(f"🔎 Found {len(cards)} products under {category_name}")
            results, seen_titles = [], set()

            # Process each card
            for card in cards:
                if len(results) >= max_results:
                    break

                data = await async_extract_product_data(card)
                if not data:
                    continue

                title = data.get("title")
                url = data.get("url")

                # Validate title & URL
                if (
                    not isinstance(title, str)
                    or not isinstance(url, str)
                    or not url.startswith("http")
                ):
                    print(f"⚠️ Skipping invalid product data: {data}")
                    continue

                if title in seen_titles:
                    continue

                seen_titles.add(title)

                try:
                    # Safely process URLs
                    data["url"] = ensure_affiliate_tag(url)
                    data["short_url"] = await shorten_url(data["url"])
                    results.append(data)
                except Exception as url_err:
                    print(f"⚠️ Skipping due to URL error: {url_err}")
                    continue

            return results[:5]

    except Exception as e:
        print(f"❌ Error scraping {category_name}: {e}")
        if page:
            try:
                category_str = str(category_name)
                filename = f"top5_error_{category_str.lower().replace(' ', '_')}.png"
                await page.screenshot(path=filename)
            except Exception as screenshot_err:
                print(f"❌ Screenshot failed for category ({category_name}): {screenshot_err}")

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
                    product = await async_extract_product_data(card)
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
                product = await async_extract_product_data(card)
                if product:
                    await browser.close()
                    return label, [product]

        except PlaywrightTimeoutError:
            await page.screenshot(path="hidden_gem_error.png")
        finally:
            await browser.close()

    return label, []
