import random
from modules.utils import escape_markdown, format_offer_line 

def format_price_block(price, mrp, discount):
    block = ""
    if discount:
        block += f"💰 *{discount}*"
    if mrp:
        mrp = mrp.lstrip("₹")
        if block:
            block += ", "
        block += f"MRP ~~₹{mrp}~~"
    if price:
        price = price.lstrip("₹")
        if block:
            block += ", "
        block += f"Now at ₹{price}"
    return block



def format_list_item_html(i, p):
    title = p['title']
    url = p['url']
    price = p.get('price', '')
    mrp = p.get('original_price') or p.get('mrp', '')
    discount = p.get('discount', '')
    bank_offer = p.get('bank_offer', "")
    normal_offer = p.get('normal_offer', "")
    deal = p.get('deal', '')
    label = p.get('label', '')

    label_str = f"{label} " if label else ""
    line = f"<b>{i}. {label_str}{title}</b>\n"

    if mrp and price:
        line += f"💰 {price} (MRP: {mrp}"
        if discount:
            line += f" | {discount}"
        line += ")\n"
    elif price:
        line += f"💰 {price}\n"

    if deal:
        line += f"⚡ {deal}\n"

    if bank_offer or normal_offer:
        offer_line = format_offer_line({
            "bank_offer": bank_offer,
            "normal_offer": normal_offer
        })
        if offer_line:
            line += f"{offer_line}\n"

    line += f"🛒 <a href=\"{url}\">Buy Now</a>\n\n"
    return line









def format_top5_html(products, category):
    message = f"📦 <b>Top 5 in {category}</b>\n\n"
    for i, p in enumerate(products, start=1):
        message += format_list_item_html(i, p)
    return message.strip()




def format_budget_picks_html(products):
    message = f"💸 <b>Budget Picks Under ₹999</b>\n\n"
    for i, p in enumerate(products, start=1):
        message += format_list_item_html(i, p)
    return message.strip()



def format_hidden_gems(products):
    message = "🧪 *Hidden Gems on Amazon*\n\n"
    for i, p in enumerate(products, start=1):
        caption = build_photo_caption(p, label_emoji="🧪", title_prefix=f"Hidden Gem #{i}", category_url=p.get("category_url"))
        message += caption + "\n\n"
    return message.strip()


def build_photo_caption(product, label_emoji="🛍️", title_prefix="", category_url=None):
    title = escape_markdown(product.get("title", "No Title"))
    url = escape_markdown(product.get("url", ""))
    price = escape_markdown(product.get("price", ""))
    mrp = escape_markdown(product.get("original_price") or product.get("mrp", ""))
    discount = escape_markdown(product.get("discount", ""))
    bank_offer = escape_markdown(product.get("bank_offer", ""))
    normal_offer = escape_markdown(product.get("normal_offer", ""))

    caption = f"{label_emoji} {escape_markdown(title_prefix)} *[{title}]({url})*\n\n"
    caption += format_price_block(price, mrp, discount) + "\n"
    if bank_offer:
        caption += f"💳 *{bank_offer}*\n"
    if normal_offer:
        caption += f"💥 *{normal_offer}*\n"
    if category_url:
        caption += f"\n\n🔗 [Explore more in this category]({escape_markdown(category_url)})"  
    return caption.strip()

def format_product_of_the_day(product, category=""):
    prefix = f"🎯 Product of the Day – {escape_markdown(category)}" if category else "🎯 Product of the Day"
    return build_photo_caption(product, label_emoji="🎯", title_prefix=prefix)

def format_combo_deal_markdown(product, label_text="🎉 Combo Deal"):
    return build_photo_caption(product, label_emoji=label_text)

def format_markdown_caption(product: dict, label: str) -> str:
    """
    Generic caption builder (fallback or manual use)
    """
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

    return caption.strip()
