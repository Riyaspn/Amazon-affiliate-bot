import random
from datetime import datetime
from modules.categories import FIXED_CATEGORIES, ROTATING_CATEGORIES
from modules.telegram import send_photo, send as send_message, CHAT_ID
from modules.scraper import (
    scrape_top5_per_category,
    scrape_product_of_the_day,
    scrape_budget_products
)
from modules.prebuilt import get_prebuilt_links, get_hidden_gem, get_random_combo_category
from modules.templates import (
    format_top5_html,
    format_budget_picks_html,
    format_combo_deal_markdown,
    format_product_of_the_day,
    format_hidden_gems
)



def get_day():
    return datetime.now().strftime('%A')


# 🛒 Top 5 Per Category

from playwright.async_api import async_playwright
from modules.scraper import scrape_top5_per_category
from modules.templates import format_top5_html
from modules.telegram import send as send_message
from modules.categories import FIXED_CATEGORIES, get_random_rotating_categories

from modules.utils import deduplicate_variants, get_browser_context, get_browser_type

async def send_top5_per_category(fixed=False):
    await send_message("🛒 <b>Top 5 Per Category</b>", parse_mode="HTML")

    if fixed:
        categories = FIXED_CATEGORIES.items()
    else:
        categories = get_random_rotating_categories(n=3)

    async with async_playwright() as p:
        browser_type = get_browser_type(p)  # ✅ choose chromium/firefox based on env
        browser, context = await get_browser_context(browser_type)  # ✅ use persistent session

        for category_name, category_url in categories:
            products = await scrape_top5_per_category(
                category_name=category_name,
                category_url=category_url,
                context=context,
                fixed=fixed,
                max_results=15
            )

            if not products:
                print(f"⚠️ No products found in {category_name}")
                continue

            deduped = deduplicate_variants(products)
            top5 = deduped[:5]

            if not top5:
                print(f"⚠️ No deduplicated products in {category_name}")
                continue

            message = format_top5_html(top5, category_name)
            await send_message(message, parse_mode="HTML")

        await browser.close()















# 💎 Hidden Gem
from modules.prebuilt import get_hidden_gem
from modules.scraper import scrape_hidden_gem
from modules.templates import build_photo_caption
from modules.telegram import send_photo, send as send_message

async def send_hidden_gem():
    gem_category = get_hidden_gem()  # returns {label, category, url}

    # Make sure to pass the human-friendly category_display as the second arg!
    label, products = await scrape_hidden_gem(
        gem_category["url"],
        gem_category["category"],
        gem_category.get("label", "Hidden Gem")
    )

    if not products:
        await send_message("💎 No hidden gem found today. Check back tomorrow!")
        return

    product = products[0]
    caption = format_hidden_gems([product])
    await send_photo(product['image'], caption)









# 💸 Budget Picks


from modules.telegram import send as send_message
from modules.categories import get_random_rotating_categories
from modules.scraper import scrape_top5_per_category
from modules.templates import format_budget_picks_html
from modules.utils import truncate_title, ensure_affiliate_tag
from playwright.async_api import async_playwright

async def send_budget_picks():
    print("💸 Sending Budget Picks (Rotational)")
    selected_categories = get_random_rotating_categories(n=5)
    budget_products = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        for category_name, category_url in selected_categories:
            print(f"🔍 Scraping Bestsellers: {category_name}")
            products = await scrape_top5_per_category(category_name, category_url, context, max_results=15)
            for product in products:
                try:
                    # Verify and filter under ₹999
                    price = float(product["price"].replace("₹", "").replace(",", "").strip())
                    if price <= 999:
                        # Clean and format fields
                        product['title'] = truncate_title(product['title'])
                        product['url'] = ensure_affiliate_tag(product['url'])
                        budget_products.append(product)
                        break
                except Exception:
                    continue
        await browser.close()

    if not budget_products:
        await send_message("😔 Couldn't find any deals under ₹999 today. Check back tomorrow!", parse_mode="HTML")
        return

    # Format message using your template system
    message = format_budget_picks_html(budget_products)
    await send_message(message, parse_mode="HTML")










# ⚡ Flash Deals
async def send_flash_deals():
    await send_message("⚡ [ *Amazon Lightning Deals* ](https://www.amazon.in/gp/goldbox?tag=storesofriyas-21)")


# 🔍 Product of the Day
from modules.templates import build_photo_caption

async def send_product_of_day():
    product = await scrape_product_of_the_day()
    if not product:
        await send_message("🔍 <b>Book of the Day</b>\n\nNo product found today.", parse_mode="HTML")
        return

    caption = build_photo_caption(product, label_emoji="🔍", title_prefix="Book of the Day")
    await send_photo(product['image'], caption)




#Combo deals
from modules.scraper import scrape_single_combo_product
from modules.prebuilt import get_random_combo_category
from modules.utils import truncate_markdown
from modules.telegram import send_html, send_photo
from playwright.async_api import async_playwright


async def send_combo_deal(max_products=1):
    try:
       
        from modules.prebuilt import get_random_combo_category

        for attempt in range(3):  # Retry logic
            category_name, category_url = get_random_combo_category()
            print(f"🌐 Attempt {attempt + 1}: Visiting {category_url}")

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800},
                    java_script_enabled=True
                )
                page = await context.new_page()

                try:
                    label, all_products = await scrape_single_combo_product(category_url, page)
                except Exception as e:
                    print(f"❌ Error scraping combo: {e}")
                    all_products = []

                await browser.close()

            if all_products:
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
                return  # Exit after success

        await send_html("⚠️ No combo deal found after multiple attempts.")

    except Exception as e:
        print(f"❌ Fatal Combo deal error: {e}")
        await send_html("⚠️ Error while fetching Combo Deal.")



















# 🔗 Prebuilt Category Links
async def send_prebuilt_links():
    links = get_prebuilt_links()
    message = (
        "💥 <b>Amazon's Top Trending Deal Zones!</b>\n"
        "Click a category to unlock today's hottest finds:\n\n"
    )
    for i, item in enumerate(links, 1):
        message += (
            f"{i}. <b>{item['category']}</b>\n"
            f"   👉 <a href=\"{item['url']}\">Shop This Zone</a>\n\n"
        )
    message += "⏳ <b>Deals update daily—check back tomorrow for fresh picks!</b>"
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
    if day in ["Monday", "Friday"]:
       await send_top5_per_category(fixed=True)
    elif day in ["Wednesday", "Sunday"]:
       await send_top5_per_category(fixed=False)  
    if day in ["Tuesday", "Thursday", "Saturday"]:
        await send_flash_deals()
        await send_product_of_day()
    if day in ["Friday", "Sunday"]:
        await send_combo_deal()








