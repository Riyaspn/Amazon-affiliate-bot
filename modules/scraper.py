# modules/scraper.py
async def get_browser_context(playwright):
    browser_type = get_browser_type(playwright)
    browser = await browser_type.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800},
        java_script_enabled=True
    )
    return browser, context

import os

def get_browser_type(playwright):
    return playwright.chromium

import re
from playwright.async_api import async_playwright
from modules.utils import deduplicate_variants

AFFILIATE_TAG = "storesofriyas-21"

async def scrape_bestsellers(category_name, url, max_products=40):
    print(f"🔍 Scraping Bestsellers: {category_name}")
    products = []
    seen_asins = set()

    async with async_playwright() as p:
        browser, context = await get_browser_context(p)
        page = await context.new_page()
        await page.goto(url, timeout=120000, wait_until="domcontentloaded")

        try:
            await page.wait_for_selector("div.p13n-sc-uncoverable-faceout", timeout=30000)
        except Exception as e:
            print(f"⚠️ Primary selector failed for {category_name}: {e}")
            try:
                await page.wait_for_selector("div.zg-grid-general-faceout", timeout=10000)
            except Exception as fallback:
                print(f"⚠️ Fallback selector also failed for {category_name}: {fallback}")
                await browser.close()
                return []

        cards = await page.query_selector_all("div.p13n-sc-uncoverable-faceout") or \
                await page.query_selector_all("div.zg-grid-general-faceout")

        for card in cards:
            try:
                title_elem = await card.query_selector("._cDEzb_p13n-sc-css-line-clamp-4_2q2cc") or \
                             await card.query_selector("._cDEzb_p13n-sc-css-line-clamp-3_g3dy1")
                if not title_elem:
                    continue

                title = (await title_elem.inner_text()).strip()
                link_elem = await card.query_selector("a")
                link = await link_elem.get_attribute("href")
                asin_match = re.search(r"/dp/([A-Z0-9]{10})", link)
                if not asin_match:
                    continue
                asin = asin_match.group(1)
                if asin in seen_asins:
                    continue
                seen_asins.add(asin)

                full_link = f"https://www.amazon.in/dp/{asin}?tag={AFFILIATE_TAG}&th=1"

                price_elem = await card.query_selector("span._cDEzb_p13n-sc-price_3mJ9Z") or \
                             await card.query_selector("span.a-color-price") or \
                             await card.query_selector("span.a-price-whole")

                price = (await price_elem.inner_text()).strip() if price_elem else "N/A"
                rating_elem = await card.query_selector("span.a-icon-alt")
                rating = (await rating_elem.inner_text()).strip() if rating_elem else "N/A"

                products.append({
                    "title": title,
                    "link": full_link,
                    "price": price,
                    "rating": rating
                })

                if len(products) >= max_products:
                    break
            except Exception as e:
                print(f"⚠️ Error parsing bestseller product: {e}")
                continue

        await browser.close()
        return products




async def scrape_prebuilt_category(url, max_products=10):
    print(f"🔍 Scraping Prebuilt: {url}")
    products = []

    async with async_playwright() as p:
        browser_type = get_browser_type(p)
        browser, context = await get_browser_context(p)
        page = await context.new_page()

        await page.goto(url, timeout=120000, wait_until="domcontentloaded")

        try:
            await page.wait_for_selector("div.s-result-item", timeout=30000)
        except:
            print("⚠️ Selector timeout — no products found.")
            await browser.close()
            return []

        cards = await page.query_selector_all("div.s-result-item")
        for card in cards:
            try:
                title_elem = await card.query_selector("h2 span")
                link_elem = await card.query_selector("h2 a")
                price_elem = await card.query_selector("span.a-price > span.a-offscreen")
                rating_elem = await card.query_selector("span.a-icon-alt")

                if not (title_elem and link_elem and price_elem):
                    continue

                title = await title_elem.inner_text()
                relative_link = await link_elem.get_attribute("href")
                price = await price_elem.inner_text()
                rating = await rating_elem.inner_text() if rating_elem else "N/A"

                asin = None
                if "/dp/" in relative_link:
                    asin = relative_link.split("/dp/")[1].split("/")[0]
                elif "/gp/product/" in relative_link:
                    asin = relative_link.split("/gp/product/")[1].split("/")[0]
                else:
                    continue

                full_link = f"https://www.amazon.in/dp/{asin}?tag={AFFILIATE_TAG}&th=1"

                products.append({
                    "title": title.strip(),
                    "link": full_link,
                    "price": price.strip(),
                    "rating": rating.strip()
                })

                if len(products) >= max_products:
                    break
            except Exception as e:
                print(f"⚠️ Error parsing prebuilt product: {e}")
                continue

        await browser.close()
        return products


async def scrape_budget_picks(url="https://www.amazon.in/s?i=specialty-aps&bbn=1377374031&rh=n%3A1377374031%2Cp_36%3A-99900", max_products=10):
    print("💸 Scraping Budget Picks")
    return await scrape_prebuilt_category(url, max_products=max_products)


import random
import re
from modules.utils import get_soup_from_url, convert_price_to_float, deduplicate_variants

async def scrape_category_products(category_name, url, max_results=5):
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

            title = title_elem.text.strip() if title_elem else None
            price = price_elem.text.strip() if price_elem else None
            rating = rating_elem.text.strip() if rating_elem else "⭐ N/A"
            url_suffix = link_elem['href'].split('?')[0] if link_elem else None
            url = f"https://www.amazon.in{url_suffix}&tag=storesofriyas-21" if url_suffix else None

            if not title or not price or not url:
                continue  # Skip incomplete product entries

            try:
                price_value = convert_price_to_float(price)
            except Exception:
                price_value = None

            product = {
                "title": f"🛍️ {title}",
                "price": price,
                "rating": rating,
                "url": url,
                "label": "🔥 Hot Deal",
                "category": category_name,
                "price_value": price_value
            }

            products.append(product)

            if len(products) >= 20:  # Collect more to allow effective deduplication
                break

        except Exception as e:
            print(f"⚠️ Error processing a product card in {category_name}: {e}")
            continue

    if not products:
        print(f"⚠️ No valid products scraped for: {category_name}")
        return []

    deduped = deduplicate_variants(products)
    return deduped[:max_results]





import random
import re
from playwright.async_api import async_playwright
from modules.utils import ensure_affiliate_tag


async def scrape_product_of_the_day():
    from bs4 import BeautifulSoup
    import random

    url = "https://www.amazon.in/s?i=stripbooks&rh=n%3A1318128031&s=popularity-rank&fs=true&ref=lp_1318128031_sar"

    async with async_playwright() as p:
        browser, context = await get_browser_context(p)
        page = await context.new_page()
        await page.goto(url, timeout=120000, wait_until="domcontentloaded")

        try:
            await page.wait_for_selector("div.s-main-slot", timeout=60000)
        except Exception as e:
            print(f"⚠️ Primary selector failed for Product of the Day: {e}")
            try:
                await page.wait_for_selector("div.s-result-item", timeout=10000)
            except Exception as fallback:
                print(f"⚠️ Fallback selector also failed for Product of the Day: {fallback}")
                await browser.close()
                return None

        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.s-main-slot div[data-asin]")

    books = []

    for card in cards:
        asin = card.get("data-asin", "")
        if not asin or len(asin) != 10:
            continue

        title_tag = card.select_one("h2 span")
        title = title_tag.text.strip() if title_tag else "N/A"

        price_tag = card.select_one("span.a-price span.a-offscreen")
        price = price_tag.text.strip() if price_tag else "N/A"

        rating_tag = card.select_one("span.a-icon-alt")
        rating = rating_tag.text.strip() if rating_tag else "N/A"

        img_tag = card.select_one("img.s-image")
        image_url = img_tag['src'] if img_tag else ""

        product_url = f"https://www.amazon.in/dp/{asin}?tag=storesofriyas-21"

        books.append({
            "title": title,
            "price": price,
            "rating": rating,
            "url": product_url,
            "image": image_url,
            "label": "📚 Bestseller Pick"
        })

    return random.choice(books) if books else None





async def scrape_budget_products(category_urls=None, price_threshold=999, limit=5):
    from modules.categories import ROTATING_CATEGORIES

    if not category_urls:
        category_urls = ROTATING_CATEGORIES

    budget_products = []

    for name, url in category_urls.items():
        print(f"🔎 Checking budget products in: {name}")
        products = await scrape_category_products(name, url)

        for product in products:
            try:
                price = float(product['price'].replace('₹', '').replace(',', '').strip())
                if price <= price_threshold:
                    product["category"] = name  # ✅ Add this line
                    budget_products.append(product)
            except:
                continue

    budget_products.sort(key=lambda x: float(x['price'].replace('₹', '').replace(',', '').strip()))
    return budget_products[:limit]






# combo_scraper

from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from modules.utils import shorten_url, add_label, ensure_affiliate_tag

async def scrape_single_combo_product(url, page, max_products=3):
    await page.goto(url, timeout=120000, wait_until="domcontentloaded")
    try:
        # Primary selector used by combo pages
        await page.wait_for_selector("div[data-cy='asin-faceout-container']", timeout=30000)
    except:
        print("⚠️ Primary combo selector not found — trying fallback...")
        # Let the calling function handle retry/fallback
        raise

    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")

    containers = soup.select("div[data-cy='asin-faceout-container']")
    products = []

    for container in containers:
        if len(products) >= max_products:
            break

        try:
            title_elem = container.select_one("h2 span")
            price_elem = container.select_one("span.a-price > span.a-offscreen")
            rating_elem = container.select_one("span.a-icon-alt")
            image_elem = container.select_one("img")
            link_elem = container.select_one("a.a-link-normal")

            if not all([title_elem, price_elem, image_elem, link_elem]):
                continue

            title = title_elem.get_text(strip=True)
            price = price_elem.get_text(strip=True)
            rating = rating_elem.get_text(strip=True) if rating_elem else "N/A"
            image = image_elem["src"]
            url_suffix = link_elem["href"]

            if "/sspa/" in url_suffix:
                continue  # Skip sponsored products

            full_url = f"https://www.amazon.in{url_suffix}"
            affiliate_url = shorten_url(ensure_affiliate_tag(full_url))

            products.append({
                "title": title,
                "price": price,
                "rating": rating,
                "image": image,
                "url": affiliate_url,
                "label": add_label({"price": price, "rating": rating}),
            })

        except Exception as e:
            print(f"⚠️ Error parsing product: {e}")
            continue

    # Use 'k' param from URL for label
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    raw_label = query.get('k', ['Combo Deal'])[0]
    label = unquote(raw_label).replace('+', ' ').title()

    return label, products



