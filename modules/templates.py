import random
from modules.utils import escape_markdown

def format_top5_markdown(products, category):
    message = f"📦 *Top 5 in {escape_markdown(category)}*\n\n"
    for i, p in enumerate(products, start=1):
        title = escape_markdown(p['title'])
        url = escape_markdown(p['url'])
        price = escape_markdown(p['price'])
        mrp = escape_markdown(p.get('original_price') or p.get('mrp', ''))
        discount = escape_markdown(p['discount'])
        bank_offer = escape_markdown(p['bank_offer'])
        normal_offer = escape_markdown(p['normal_offer'])
        label = p.get('label', '')

        line = f"{i}. {label} [{title}]({url})\n"
        if discount:
            line += f"💰 *{discount}*"
        if mrp:
            line += f", MRP ~~₹{mrp}~~"
        if price:
            line += f", Now at ₹{price}"
        line += "\n"
        if bank_offer:
            line += f"💳 *{bank_offer}*\n"
        if normal_offer:
            line += f"💥 *{normal_offer}*\n"
        line += "\n"
        message += line
    return message.strip()

def format_budget_picks(products):
    message = f"💸 *Budget Picks Under ₹999*\n\n"
    for i, p in enumerate(products, start=1):
        title = escape_markdown(p['title'])
        url = escape_markdown(p['url'])
        price = escape_markdown(p['price'])
        mrp = escape_markdown(p.get('original_price') or p.get('mrp', ''))
        discount = escape_markdown(p['discount'])
        bank_offer = escape_markdown(p['bank_offer'])
        normal_offer = escape_markdown(p['normal_offer'])
        label = p.get('label', '')

        line = f"{i}. {label} [{title}]({url})\n"
        if discount:
            line += f"💰 *{discount}*"
        if mrp:
            line += f", MRP ~~₹{mrp}~~"
        if price:
            line += f", Now at ₹{price}"
        line += "\n"
        if bank_offer:
            line += f"💳 *{bank_offer}*\n"
        if normal_offer:
            line += f"💥 *{normal_offer}*\n"
        line += "\n"
        message += line
    return message.strip()

def build_product_message(product, label_emoji="⭐"):
    title = escape_markdown(product["title"])
    url = escape_markdown(product["url"])
    price = escape_markdown(product["price"])
    mrp = escape_markdown(product["mrp"])
    discount = escape_markdown(product["discount"])
    bank_offer = escape_markdown(product["bank_offer"])
    normal_offer = escape_markdown(product["normal_offer"])

    message = f"{label_emoji} *[{title}]({url})*\n\n"
    if discount:
        message += f"💰 *{discount}*"
    if mrp:
        message += f", MRP ~~₹{mrp}~~"
    if price:
        message += f", Now at ₹{price}"
    message += "\n"
    if bank_offer:
        message += f"💳 *{bank_offer}*\n"
    if normal_offer:
        message += f"💥 *{normal_offer}*\n"
    return message.strip()

def build_photo_caption(product, label_emoji="🛍️"):
    title = escape_markdown(product["title"])
    url = escape_markdown(product["url"])
    price = escape_markdown(product["price"])
    mrp = escape_markdown(product["mrp"])
    discount = escape_markdown(product["discount"])
    bank_offer = escape_markdown(product["bank_offer"])
    normal_offer = escape_markdown(product["normal_offer"])

    message = f"{label_emoji} *[{title}]({url})*\n\n"
    if discount:
        message += f"💰 *{discount}*"
    if mrp:
        message += f", MRP ~~₹{mrp}~~"
    if price:
        message += f", Now at ₹{price}"
    message += "\n"
    if bank_offer:
        message += f"💳 *{bank_offer}*\n"
    if normal_offer:
        message += f"💥 *{normal_offer}*\n"
    return message.strip()

def format_combo_deal_markdown(product, label_text):
    return build_photo_caption(product, label_text)

def format_product_of_the_day(product):
    return build_photo_caption(product, "🎯")

def format_hidden_gems(products):
    message = f"🧪 *Hidden Gems on Amazon*\n\n"
    for i, p in enumerate(products, start=1):
        title = escape_markdown(p['title'])
        url = escape_markdown(p['url'])
        price = escape_markdown(p['price'])
        mrp = escape_markdown(p.get('original_price') or p.get('mrp', ''))
        discount = escape_markdown(p['discount'])
        bank_offer = escape_markdown(p['bank_offer'])
        normal_offer = escape_markdown(p['normal_offer'])
        label = p.get('label', '')

        line = f"{i}. {label} [{title}]({url})\n"
        if discount:
            line += f"💰 *{discount}*"
        if mrp:
            line += f", MRP ~~₹{mrp}~~"
        if price:
            line += f", Now at ₹{price}"
        line += "\n"
        if bank_offer:
            line += f"💳 *{bank_offer}*\n"
        if normal_offer:
            line += f"💥 *{normal_offer}*\n"
        line += "\n"
        message += line
    return message.strip()


# In modules/templates.py

def format_markdown_caption(product: dict, label: str) -> str:
    title = product.get("title", "No title")
    price = product.get("price", "")
    original_price = product.get("original_price", "")
    discount = product.get("discount", "")
    bank_offer = product.get("bank_offer", "")
    url = product.get("short_url", product.get("url", ""))

    caption = f"*{label}*\n"
    caption += f"{title}\n\n"

    if original_price and original_price != price:
        caption += f"~₹{original_price}~  👉 ₹{price}\n"
    else:
        caption += f"Price: ₹{price}\n"

    if discount:
        caption += f"🔻 *{discount}*\n"

    if bank_offer:
        caption += f"🏦 {bank_offer}\n"

    caption += f"\n[🛒 Buy Now]({url})"

    return caption

