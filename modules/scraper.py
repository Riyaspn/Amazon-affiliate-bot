import random
import re
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from modules.prebuilt import COMBO_DEAL_CATEGORIES, HIDDEN_GEM_CATEGORIES, TOP5_CATEGORIES
from modules.utils import get_browser_type, get_browser_context, extract_price

async def async_extract_product_data(card):
    try:
        title_element = await card.query_selector('h2 a span')
        title = await title_element.inner_text() if title_element else "No title"

        url_element = await card.query_selector('h2 a')
        url = "https://www.amazon.in" + await url_element.get_attribute('href') if url_element else None

        image_element = await card.query_selector('img')
        image = await image_element.get_attribute('src') if image_element else None

        price_element = await card.query_selector("span.a-price > span.a-offscreen")
        price = await price_element.inner_text() if price_element else None

        original_price_element = await card.query_selector("span.a-price.a-text-price > span.a-offscreen")
        original_price = await original_price_element.inner_text() if original_price_element else None

        discount_element = await card.query_selector("span.a-letter-space + span.a-color-base")
        discount = await discount_element.inner_text() if discount_element else None

        bank_offer = None
        normal_offer = None

        # Check for bank or normal offers (like coupon)
        offer_spans = await card.query_selector_all("span.a-size-small")
        for span in offer_spans:
            text = await span.inner_text()
            if any(keyword in text.lower() for keyword in ["bank offer", "credit", "debit", "emi"]):
                bank_offer = text
            elif any(keyword in text.lower() for keyword in ["coupon", "offer", "discount"]):
                normal_offer = text

        return {
            "title": title.strip(),
            "url": url,
            "image": image,
            "price": price,
            "original_price": original_price,
            "discount": discount,
            "bank_offer": bank_offer,
            "normal_offer": normal_offer
        }

    except Exception as e:
        print("Error in extract_product_data:", e)
        return None

async def scrape_single_combo_product():
    combo = random.choice(COMBO_DEAL_CATEGORIES)
    label, url = combo['label'], combo['url']

    async with async_playwright() as p:
        browser_type = get_browser_type()
        browser = await p[browser_type].launch(headless=True)
        context = await get_browser_context(browser)
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
        browser_type = get_browser_type()
        browser = await p[browser_type].launch(headless=True)
        context = await get_browser_context(browser)
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
                        price_val = extract_price(data["price"])
                        original_price_val = extract_price(data["original_price"])
                        discount_pct = round((original_price_val - price_val) / original_price_val * 100)
                        if discount_pct >= 20:
                            data["discount"] = f"{discount_pct}% off"
                            all_data.append(data)
                    except:
                        pass

            sorted_data = sorted(all_data, key=lambda d: extract_price(d["price"]))
            return sorted_data[:1]

        except PlaywrightTimeoutError:
            await page.screenshot(path="potd_error.png")
        finally:
            await browser.close()

    return []

async def scrape_top5_per_category():
    all_results = []
    for label, url in TOP5_CATEGORIES.items():
        async with async_playwright() as p:
            browser_type = get_browser_type()
            browser = await p[browser_type].launch(headless=True)
            context = await get_browser_context(browser)
            page = await context.new_page()

            try:
                await page.goto(url, timeout=60000)
                await page.wait_for_selector('div[data-cy="asin-faceout-container"]', timeout=30000)
                cards = await page.query_selector_all('div[data-cy="asin-faceout-container"]')
                seen = set()
                data = []

                for card in cards:
                    product = await async_extract_product_data(card)
                    if product and product["title"] not in seen:
                        seen.add(product["title"])
                        data.append(product)
                    if len(data) >= 5:
                        break

                all_results.append((label, data))
            except PlaywrightTimeoutError:
                await page.screenshot(path=f"top5_error_{label}.png")
            finally:
                await browser.close()

    return all_results

async def scrape_budget_products():
    results = []
    for label, url in TOP5_CATEGORIES.items():
        async with async_playwright() as p:
            browser_type = get_browser_type()
            browser = await p[browser_type].launch(headless=True)
            context = await get_browser_context(browser)
            page = await context.new_page()

            try:
                await page.goto(url, timeout=60000)
                await page.wait_for_selector('div[data-cy="asin-faceout-container"]', timeout=30000)
                cards = await page.query_selector_all('div[data-cy="asin-faceout-container"]')

                for card in cards:
                    product = await async_extract_product_data(card)
                    if product and product["price"]:
                        try:
                            price_val = extract_price(product["price"])
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
        browser_type = get_browser_type()
        browser = await p[browser_type].launch(headless=True)
        context = await get_browser_context(browser)
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
