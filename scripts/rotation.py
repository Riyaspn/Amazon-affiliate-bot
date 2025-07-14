import random
from datetime import datetime
from modules.templates import format_top_5_product_message
from modules.categories import FIXED_CATEGORIES, ROTATING_CATEGORIES
from modules.scraper import scrape_category_products
from modules.templates import build_product_message
from modules.templates import build_category_header
from modules.telegram import send as send_message, send_photo, CHAT_ID
from modules.scraper import (
    scrape_category_products,
    scrape_product_of_the_day,
    scrape_budget_products
)
from modules.prebuilt import get_prebuilt_links, get_hidden_gem, get_random_combo_category


def get_day():
    return datetime.now().strftime('%A')


# 🛒 Top 5 Per Category
from modules.templates import build_product_message, build_category_header
from modules.telegram import send as send_message
from modules.scraper import scrape_category_products
from modules.categories import FIXED_CATEGORIES, ROTATING_CATEGORIES
import random
from datetime import datetime
from modules.utils import deduplicate_variants


def get_day():
    return datetime.now().strftime('%A')

# rotation.py

from modules.categories import ROTATING_CATEGORIES, FIXED_CATEGORIES
from modules.scraper import scrape_category_products
from modules.templates import build_product_message


from modules.templates import format_top_5_product_message  # ✅ Ensure this is imported properly

from random import sample

import random
from modules.categories import FIXED_CATEGORIES, ROTATING_CATEGORIES
from modules.scraper import scrape_category_products
from modules.telegram import send_html
from modules.templates import format_top5_html

async def send_top5_per_category(fixed=False):
    # Step 1: Decide category pool
    if fixed:
        selected_categories = list(FIXED_CATEGORIES.items())[:3]
    else:
        selected_categories = random.sample(list(ROTATING_CATEGORIES.items()), 3)

    # Step 2: Send header message
    await send_html("🛒 <b>Top 5 Per Category</b>")

    # Step 3: Loop through categories and send products
    for category_name, category_url in selected_categories:
        print(f"🔍 Scraping Bestsellers: {category_name}")
        products = await scrape_category_products(category_name, category_url, max_results=15)


        if not products:
            await send_html(f"⚠️ No products found for <b>{category_name}</b>.")
            continue

        deduped_products = deduplicate_variants(products)
        products = deduplicate_variants(products)
        top5 = deduped_products[:5]
        message = format_top5_html(category_name, top5)
        await send_html(message)













# 💎 Hidden Gem
async def send_hidden_gem():
    gem = get_hidden_gem()
    if gem:
        message = f"💎 *HIDDEN GEM:*\n\n*{gem['category']}*\n🔗 [View on Amazon]({gem['url']})"
        await send_message(message)


# 💸 Budget Picks
# 💸 Budget Picks
from modules.telegram import send as send_message
from modules.categories import get_random_rotating_categories
from modules.scraper import scrape_category_products
import re

def truncate_title(title, limit=60):
    return title[:limit].rstrip() + "..." if len(title) > limit else title

async def send_budget_picks():
    print("💸 Sending Budget Picks (Rotational)")
    selected_categories = get_random_rotating_categories(n=5)

    message = "<b>💸 Budget Picks of the Day (Under ₹999)</b>\n\n"
    any_product_found = False

    for category_name, category_url in selected_categories:
        print(f"🔍 Scraping Bestsellers: {category_name}")
        products = await scrape_category_products(category_name, category_url, max_results=15)

        valid_prices = 0
        budget_product = None

        for product in products:
            try:
                price_text = product.get("price", "").replace("₹", "").replace(",", "").strip()
                if not price_text or not price_text.replace(".", "", 1).isdigit():
                    continue

                price = float(price_text)
                valid_prices += 1

                if price <= 999:
                    budget_product = product
                    break
            except Exception as e:
                print(f"❌ Error parsing price for {product.get('title', '')[:40]}: {e}")
                continue

        print(f"✅ {valid_prices} products with valid prices in: {category_name}")

        if not budget_product:
            print(f"⚠️ No valid budget product in: {category_name}")
            continue

        any_product_found = True

        # Clean and truncate
        short_title = truncate_title(budget_product['title'].replace("🛍️", "").strip())
        short_url = re.sub(r"(ref=.*)", "", budget_product['url'].split("?")[0])
        asin_match = re.search(r"/dp/([A-Z0-9]{10})", short_url)
        final_url = f"https://www.amazon.in/dp/{asin_match.group(1)}?tag=storesofriyas-21" if asin_match else budget_product['url']

        message += (
            f"<b>{category_name}</b>\n"
            f"<b>🛍️ {short_title}</b>\n"
            f"{budget_product['price']} | ⭐ {budget_product['rating']}\n"
            f"<a href=\"{final_url}\">🔗 View Deal</a>\n\n"
        )

    if not any_product_found:
        message += "😔 Couldn't find any deals under ₹999 today. Check back tomorrow!"

    await send_message(message.strip(), parse_mode="HTML")









# ⚡ Flash Deals
async def send_flash_deals():
    await send_message("⚡ [*Amazon Lightning Deals*](https://www.amazon.in/gp/goldbox?tag=storesofriyas-21)")


# 🔍 Product of the Day
async def send_product_of_day():
    product = await scrape_product_of_the_day()
    if not product:
        await send_message("🔍 *Book of the Day*\n\nNo product found today.")
        return

    message = (
        f"🔍 *Book of the Day*\n\n"
        f"📘 *{product['title']}*\n"
        f"💰 {product['price']}   ⭐ {product['rating']}\n"
        f"🔗 [View on Amazon]({product['url']})\n"
        f"{product['label']}"
    )

    await send_photo(product['image'], message)



#Combo deals
import html
from modules.utils import escape_caption_html
from modules.prebuilt import get_random_combo_category
from modules.scraper import scrape_single_combo_product
from modules.telegram import send_html, send_photo
from playwright.async_api import async_playwright

def truncate_markdown(text, limit=80):
    text = text.strip()
    text = text[:limit].rsplit(' ', 1)[0]
    return text + "..." if len(text) >= limit else text

async def send_combo_deal(max_products=1):
    try:
        category_name, category_url = get_random_combo_category()
        print(f"🌐 Visiting: {category_url}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            label, all_products = await scrape_single_combo_product(category_url)
            await browser.close()

        if not all_products:
            await send_html("⚠️ No combo deal found.")
            return

        product = all_products[0]
        title = truncate_markdown(product["title"], 80).replace('*', '')
        price = product["price"]
        rating = product["rating"]
        url = product["url"]
        image = product["image"]

        caption = (
            f"🎯 *Combo Deal – {label}*\n\n"
            f"⭐ *{title}*\n"
            f"💰 {price}   ⭐ {rating}\n"
            f"🔗 [View Deal]({url})\n\n"
            f"_🔎 Explore more combo deals:_ [Browse Category]({category_url})"
        )

        await send_photo(image, caption)

    except Exception as e:
        print(f"❌ Combo deal error: {e}")
        await send_html("⚠️ Error while fetching Combo Deal.")

















# 🔗 Prebuilt Category Links
async def send_prebuilt_links():
    links = get_prebuilt_links()
    message = "🔗 *Amazon Prebuilt Category Pages*\n\n"
    for item in links:
        message += f"📢 {item['category']}\n🔗 [View Deals]({item['url']})\n\n"
    await send_message(message.strip())


# 🌅 Morning Rotation
async def run_morning_rotation(current_day=None):
    day = current_day if current_day else get_day()
    await send_prebuilt_links()
    if day in ["Monday", "Wednesday", "Friday", "Sunday"]:
        await send_hidden_gem()
    if day in ["Tuesday", "Thursday", "Saturday"]:
        await send_budget_picks()


# 🌆 Evening Rotation
async def run_evening_rotation(current_day=None):
    day = current_day if current_day else get_day()
    if day in ["Monday", "Wednesday", "Friday"]:
       await send_top5_per_category(fixed=True)
    elif day == "Sunday":
       await send_top5_per_category(fixed=False)  
    if day in ["Tuesday", "Thursday", "Saturday"]:
        await send_flash_deals()
        await send_product_of_day()
    if day in ["Friday", "Sunday"]:
        await send_combo_deal()
