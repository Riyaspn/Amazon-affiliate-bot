# modules/scraper.py

import re
from playwright.async_api import async_playwright
from modules.utils import deduplicate_variants

AFFILIATE_TAG = "storesofriyas-21"

async def scrape_bestsellers(category_name, url, max_products=40):
    print(f"🔍 Scraping Bestsellers: {category_name}")
    products = []
    seen_asins = set()

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)

        try:
            await page.wait_for_selector("div.p13n-sc-uncoverable-faceout", timeout=25000)
        except:
            print(f"⚠️ Timeout or selector issue for {category_name}")
            await browser.close()
            return []

        cards = await page.query_selector_all("div.p13n-sc-uncoverable-faceout")
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

                # ✅ Fallback price selectors
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
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)

        try:
            await page.wait_for_selector("div.s-result-item", timeout=20000)
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
    import re

    url = "https://www.amazon.in/s?i=stripbooks&rh=n%3A1318128031&s=popularity-rank&fs=true&ref=lp_1318128031_sar"

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36", viewport={"width": 1280, "height": 800})
        await page.goto(url, timeout=60000)
        await page.wait_for_selector("div.s-main-slot", timeout=60000)
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.s-main-slot div[data-asin]")

    books = []

    for card in cards:
        asin = card.get("data-asin", "")
        if not asin or len(asin) != 10:
            continue

        # Title
        title_tag = card.select_one("h2 span")
        title = title_tag.text.strip() if title_tag else "N/A"

        # Price
        price_tag = card.select_one("span.a-price span.a-offscreen")
        price = price_tag.text.strip() if price_tag else "N/A"

        # Rating
        rating_tag = card.select_one("span.a-icon-alt")
        rating = rating_tag.text.strip() if rating_tag else "N/A"

        # Image
        img_tag = card.select_one("img.s-image")
        image_url = img_tag['src'] if img_tag else ""

        # Build full URL
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






# modules/scraper/combo_scraper.py

import asyncio
from bs4 import BeautifulSoup
from modules.utils import extract_product_info
from playwright.async_api import async_playwright

async def scrape_single_combo_product(url, page, max_products=1):
    try:
        # Set user-agent and headers
        await page.set_user_agent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        await page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9"
        })

        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(5000)  # Let page render

        # 🧪 Screenshot for GitHub debugging
        await page.screenshot(path="combo_debug.png", full_page=True)

        product_elements = []
        used_selector = None

        # Try first selector
        try:
            used_selector = "div[data-cy='asin-faceout-container']"
            product_elements = await page.query_selector_all(used_selector)
            if not product_elements:
                raise Exception("No elements found for selector 1")
            print(f"✅ Used selector: {used_selector}")
        except:
            try:
                used_selector = "div[data-component-type='s-search-result']"
                product_elements = await page.query_selector_all(used_selector)
                if not product_elements:
                    raise Exception("No elements found for selector 2")
                print(f"✅ Used selector: {used_selector}")
            except Exception as e:
                print(f"❌ Failed both selectors: {e}")
                return "Combo Deal", []

        # Extract products
        products = []
        for elem in product_elements:
            html_content = await elem.inner_html()
            soup = BeautifulSoup(html_content, "html.parser")
            product = extract_product_info(soup)
            if product:
                products.append(product)
            if len(products) >= max_products:
                break

        label = url.split("k=")[-1].split("&")[0].replace("+", " ").title()
        return label, products

    except Exception as e:
        print(f"❌ Error scraping combo: {e}")
        return "Combo Deal", []



