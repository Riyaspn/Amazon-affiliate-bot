# modules/templates.py

def build_prebuilt_links_message(categories):
    message = "🔗 *Amazon Prebuilt Category Pages*\n\n"
    for cat in categories:
        message += f"📢 *{escape_markdown(cat['category'])}*\n🔗 [View Deals]({escape_markdown(cat['url'])})\n\n"
    return message.strip()





def build_hidden_gem_message(category_name, products):
    if not products:
        return None

    message = f"📢 💎 *HIDDEN GEM: {category_name.upper()} DEALS*\n\n"
    for i, product in enumerate(products):
        label = "🔥 Hot Deal" if i == 0 else "⭐ Top Pick"
        title = escape_markdown(product['title'])
        price = escape_markdown(product['price'])
        rating = escape_markdown(product['rating'])
        link = escape_markdown(product['link'])
        message += f"""{label}
        🛒 *{title}*
        💰 {price}
        ⭐ {rating}
        🔗 [View on Amazon]({link})

"""
    return message.strip()






def build_budget_picks_message(products):
    from modules.utils import apply_affiliate_tag, shorten_url

    header = "💸 *Top Budget Picks (Under ₹999)*\n"
    body = ""
    for p in products:
        title = escape_markdown(p["title"])
        price = p.get("price", "N/A")
        rating = escape_markdown(p.get("rating", ""))
        url = shorten_url(apply_affiliate_tag(p.get("url", "#")))

        body += f"\n[{title}]({url})\n💰 ₹{price}   ⭐ {rating}\n"
    return header + body.strip()







def build_flash_deals_message(deals):
    message = "⚡ *FLASH DEALS ALERT!*\n\n"
    for deal in deals:
        title = escape_markdown(deal['title'])
        url = escape_markdown(deal['url'])
        message += f"{title}\n🔗 [View Deal]({url})\n\n"
    return message.strip()







import re

def truncate(text, limit=100):
    text = text.strip()
    return text[:limit].rsplit(' ', 1)[0] + "..." if len(text) > limit else text

import re
from modules.utils import apply_affiliate_tag, shorten_url

def escape_markdown(text: str) -> str:
    """
    Escapes special characters in text for Markdown V2.
    """
    return re.sub(r'([_*\[\]()~`>#+-=|{}.!])', r'\\\1', text)

def build_combo_message(label, products):
    if not products:
        return None, None

    product = max(
        products,
        key=lambda p: int(p.get("discount_percent", "0").replace("%", "").strip())
    )

    title = escape_markdown(product["title"])
    original_price = product["original_price"]
    discounted_price = product["discounted_price"]
    discount_percent = product["discount_percent"]
    image_url = product["image"]
    product_url = shorten_url(apply_affiliate_tag(product["url"]))

    header = f"🎯 *{escape_markdown(label)} Combo Deal* 🎯"
    price_info = f"*Price:* ~~₹{original_price}~~ → *₹{discounted_price}* (`{discount_percent}`)"
    footer = f"[🛒 Grab Now]({product_url})"

    caption = f"{header}\n\n*{title}*\n\n{price_info}\n\n{footer}"
    return image_url, caption
















def build_product_of_day_message(product):
    from modules.utils import apply_affiliate_tag, shorten_url

    title = escape_markdown(product.get("title", "No title"))
    original_price = product.get("original_price", "")
    discounted_price = product.get("price", "N/A")
    discount_percent = product.get("discount_percent", "")
    rating = escape_markdown(product.get("rating", "⭐ N/A"))
    image = product.get("image", None)
    url = shorten_url(apply_affiliate_tag(product.get("url", "#")))

    caption = f"🔍 *Product of the Day*\n\n"
    caption += f"*{title}*\n"

    if original_price and original_price != discounted_price:
        caption += f"💰 ~~₹{original_price}~~ → *₹{discounted_price}* `{discount_percent}`\n"
    else:
        caption += f"💰 *₹{discounted_price}*\n"

    caption += f"⭐ {rating}\n[🔗 View on Amazon]({url})"

    return caption.strip(), caption.strip(), image






def format_product_message(product, label, show_affiliate=True):
    title = product.get("title", "")
    price = product.get("price", "")
    rating = product.get("rating", "")
    link = product.get("affiliate_link", product.get("url", ""))

    message = f"""{escape_markdown(label)} *{escape_markdown(title)}*\n💰 Price: ₹{escape_markdown(price)}\n⭐ Rating: {escape_markdown(rating)}\n🔗 [View on Amazon]({escape_markdown(link)})"""

    return message

def build_category_header(category: str) -> str:
    return f"\n📢 *{category.upper()} DEALS*\n"

def build_morning_intro(label: str) -> str:
    return f"🌅 *Good Morning!* Here's your {label} for today:\n"

def build_evening_intro(label: str) -> str:
    return f"🌆 *Evening Deals:* {label} just dropped! Don't miss out:\n"

def build_product_message(product: dict) -> str:
    title = escape_markdown(product.get("title", "No title"))
    price = product.get("price", "N/A")
    rating = escape_markdown(product.get("rating", "⭐ N/A"))
    url = product.get("url", "")
    label = product.get("label", "")

    # Add warning emoji if URL is missing
    if not url:
        url_display = "❌ URL Missing"
    else:
        url_display = f"🔗 [View on Amazon]({url})"

    return (
        f"🛍️ *{title}*\n"
        f"💰 {price}   ⭐ {rating}\n"
        f"{url_display}\n"
        f"{label}".strip()
    )




def format_top_5_product_message_markdown(product, index):
    label = "🔥 Hot Deal" if index == 0 else (
        "💸 Premium Pick" if index == 1 else "⭐ Top Rated"
    )

    title = escape_markdown(product.get("title", "No title"))
    price = product.get("price", "N/A")
    original_price = product.get("original_price", "")
    discount_percent = product.get("discount_percent", "")
    rating = escape_markdown(product.get("rating", ""))
    url = product.get("url", "#")

    message = f"*{label}*\n"
    message += f"*{title}*\n"

    if original_price and original_price != price:
        message += f"💰 ~~₹{original_price}~~ → *₹{price}* `{discount_percent}`\n"
    else:
        message += f"💰 *₹{price}*\n"

    message += f"⭐ {rating}\n[🔗 View Deal]({url})\n"
    return message.strip()




def format_markdown_caption(product: dict) -> str:
    from modules.utils import apply_affiliate_tag, shorten_url

    title = escape_markdown(product["title"])
    price = product.get("price", "N/A")
    original_price = product.get("original_price", "")
    discount_percent = product.get("discount_percent", "")
    rating = product.get("rating", "")
    reviews = product.get("reviews", "")
    label = escape_markdown(product.get("label", ""))
    url = shorten_url(apply_affiliate_tag(product["url"]))

    caption = f"{label} *{title}*\n"
    if original_price and original_price != price:
        caption += f"💰 ~~₹{original_price}~~ → *₹{price}* `{discount_percent}`\n"
    else:
        caption += f"💰 *₹{price}*\n"
    caption += f"⭐ {rating} ({reviews} reviews)\n"
    caption += f"[🔗 View on Amazon]({url})"
    return caption.strip()



