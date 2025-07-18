# modules/templates.py

from modules.utils import apply_affiliate_tag, shorten_url

def build_prebuilt_links_message(categories):
    message = "🔗 *Amazon Prebuilt Category Pages*\n\n"
    for cat in categories:
        url = shorten_url(apply_affiliate_tag(cat['url']))
        message += f"📢 *{escape_markdown(cat['category'])}*\n🔗 [View Deals]({escape_markdown(url)})\n\n"
    return message.strip()






def build_hidden_gem_message(category_name, products):
    if not products:
        return None

    message = f"📢 💎 *HIDDEN GEM: {escape_markdown(category_name.upper())} DEALS*\n\n"
    for i, product in enumerate(products):
        label = "🔥 Hot Deal" if i == 0 else "⭐ Top Pick"
        title = escape_markdown(product.get('title', 'No title'))
        price = product.get('price', 'N/A')
        original_price = product.get('original_price', '')
        discount = product.get('discount', '')
        rating = escape_markdown(product.get('rating', ''))
        url = product.get('url', '')
        bank_offer = product.get("bank_offer", "")
        normal_offer = product.get("normal_offer", "")


        line = f"{label}\n🛒 *{title}*\n"

        if original_price and original_price != price:
            line += f"💰 ~~₹{original_price}~~ → *₹{price}* (⚡ {discount})\n"
        else:
            line += f"💰 ₹{price}\n"

        line += f"⭐ {rating}\n"

        if url:
            line += f"🔗 [View on Amazon]({escape_markdown(url)})\n"
        if bank_offer:
            line += f"💳 *{escape_markdown(bank_offer.strip())}*\n"
        if normal_offer:
            line += f"💥 *{escape_markdown(normal_offer.strip())}*\n"    

        message += line + "\n"

    return message.strip()







def build_budget_picks_message(products):
    """
    Format budget picks products into a Markdown message.
    Includes price, discount, and bank offers if available.
    """
    lines = ["💸 *Top Budget Picks (Under ₹999)*\n"]

    for product in products:
        title = product.get("title", "").strip()
        url = product.get("short_url", product.get("url", "")).strip()
        price = product.get("price", "")
        original_price = product.get("original_price", "")
        discount = product.get("discount_percent", "")
        bank_offer = product.get("bank_offer", "")
        normal_offer = product.get("normal_offer", "")

        line = f"🔹 [{title}]({url})\n"
        if price:
            line += f"   `₹{price}`"
        if discount:
            line += f" (⚡ {discount})"
        if original_price and original_price != price:
            line += f", MRP ₹{original_price}"
        if bank_offer:
            line += f"\n   💳 *{bank_offer.strip()}*"
        if normal_offer:
            line += f"\n   💥 *{normal_offer.strip()}*"

        lines.append(line)

    return "\n\n".join(lines).strip()







def build_flash_deals_message(deals):
    message = "⚡ *FLASH DEALS ALERT!*\n\n"
    for deal in deals:
        title = escape_markdown(deal.get('title', 'No title'))
        url = deal.get('url', '')
        price = deal.get('price', '')
        original_price = deal.get('original_price', '')
        discount = deal.get('discount', '')
        bank_offer = deal.get("bank_offer", "")
        normal_offer = deal.get("normal_offer", "")


        line = f"🔹 *{title}*\n"

        if original_price and original_price != price:
            line += f"💰 ~~₹{original_price}~~ → *₹{price}* (⚡ {discount})\n"
        else:
            line += f"💰 ₹{price}\n"

        if bank_offer:
            line += f"💳 *{escape_markdown(bank_offer.strip())}*\n"
        if normal_offer:
            line += f"💥 *{escape_markdown(normal_offer.strip())}*\n"


        if url:
            line += f"🔗 [View Deal]({escape_markdown(url)})\n"

        message += line + "\n"

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
    original_price = product.get("original_price", "")
    discounted_price = product.get("discounted_price", "")
    discount_percent = product.get("discount_percent", "")
    image_url = product.get("image", "")
    product_url = shorten_url(apply_affiliate_tag(product.get("url", "#")))

    bank_offer = escape_markdown(product.get("bank_offer", ""))
    normal_offer = escape_markdown(product.get("normal_offer", ""))

    header = f"🎯 *{escape_markdown(label)} Combo Deal* 🎯"
    price_info = f"*Price:* ~~₹{original_price}~~ → *₹{discounted_price}* (`{discount_percent}`)"

    # Collect both offers if available
    offer_lines = ""
    if bank_offer:
        offer_lines += f"\n💳 *{bank_offer.strip()}*"
    if normal_offer:
        offer_lines += f"\n💥 *{normal_offer.strip()}*"

    footer = f"[🛒 Grab Now]({product_url})"

    caption = f"{header}\n\n*{title}*\n\n{price_info}{offer_lines}\n\n{footer}"

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
    bank_offer = product.get("bank_offer", "")
    normal_offer = product.get("normal_offer", "")

    caption = f"🔍 *Product of the Day*\n\n"
    caption += f"*{title}*\n"

    if original_price and original_price != discounted_price:
        caption += f"💰 ~~₹{original_price}~~ → *₹{discounted_price}* `{discount_percent}`\n"
    else:
        caption += f"💰 *₹{discounted_price}*\n"

    if bank_offer:
        caption += f"💳 *{escape_markdown(bank_offer.strip())}*\n"
    if normal_offer:
        caption += f"💥 *{escape_markdown(normal_offer.strip())}*\n"    

    caption += f"⭐ {rating}\n[🔗 View on Amazon]({url})"

    return caption.strip(), caption.strip(), image







def format_product_message(product, label, show_affiliate=True):
    from modules.utils import apply_affiliate_tag, shorten_url

    title = escape_markdown(product.get("title", ""))
    price = product.get("price", "")
    original_price = product.get("original_price", "")
    discount_percent = product.get("discount_percent", "")
    rating = escape_markdown(product.get("rating", ""))
    url = product.get("url", "")
    bank_offer = escape_markdown(product.get("bank_offer", ""))
    normal_offer = escape_markdown(product.get("normal_offer", ""))

    if show_affiliate:
        url = shorten_url(apply_affiliate_tag(url))

    message = f"{escape_markdown(label)} *{title}*\n"

    if original_price and original_price != price:
        message += f"💰 ~~₹{original_price}~~ → *₹{price}* `{discount_percent}`\n"
    else:
        message += f"💰 *₹{price}*\n"

    if bank_offer:
        message += f"💳 *{bank_offer}*\n"
    if normal_offer:
        message += f"💥 *{normal_offer}*\n"

    message += f"⭐ {rating}\n🔗 [View on Amazon]({escape_markdown(url)})"

    return message.strip()



def build_category_header(category: str) -> str:
    return f"\n📢 *{category.upper()} DEALS*\n"

def build_morning_intro(label: str) -> str:
    return f"🌅 *Good Morning!* Here's your {label} for today:\n"

def build_evening_intro(label: str) -> str:
    return f"🌆 *Evening Deals:* {label} just dropped! Don't miss out:\n"

def build_product_message(product: dict) -> str:
    from modules.utils import apply_affiliate_tag, shorten_url

    title = escape_markdown(product.get("title", "No title"))
    price = product.get("price", "N/A")
    original_price = product.get("original_price", "")
    discount_percent = product.get("discount_percent", "")
    rating = escape_markdown(product.get("rating", "⭐ N/A"))
    url = shorten_url(apply_affiliate_tag(product.get("url", "#")))
    bank_offer = escape_markdown(product.get("bank_offer", ""))
    normal_offer = escape_markdown(product.get("normal_offer", ""))
    label = product.get("label", "")

    msg = f"🛍️ *{title}*\n"
    if original_price and original_price != price:
        msg += f"💰 ~~₹{original_price}~~ → *₹{price}* `{discount_percent}`\n"
    else:
        msg += f"💰 *₹{price}*\n"

    if bank_offer:
        message += f"💳 *{bank_offer}*\n"
    if normal_offer:
        message += f"💥 *{normal_offer}*\n"

    msg += f"⭐ {rating}\n🔗 [View on Amazon]({url})"

    if label:
        msg += f"\n_{escape_markdown(label)}_"

    return msg.strip()




def format_top_5_product_message(product, index):
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

def format_top5_markdown(category: str, products: list) -> str:
    lines = [f"*📦 {category}*"]
    for product in products:
        title = product.get("title", "").strip()
        url = product.get("short_url", product.get("url", "")).strip()
        price = product.get("price", "")
        mrp = product.get("original_price", "")
        discount = product.get("discount", "")
        offer = product.get("offer", "") or product.get("bank_offer", "")

        line = f"🔹 [{title}]({url})\n"
        if price:
            line += f"   `{price}`"
        if discount:
            line += f" (⚡ {discount})"
        if mrp and mrp != price:
            line += f", MRP {mrp}"
        if offer:
            line += f"\n   💳 *{offer.strip()}*"

        lines.append(line)

    return "\n\n".join(lines)



