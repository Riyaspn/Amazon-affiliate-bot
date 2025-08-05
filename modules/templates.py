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

    # 💰 Price block
    if mrp and price:
        line += f"💰 <b>{price}</b> (MRP: <s>{mrp}</s>"
        if discount:
            line += f" | 🔻<b>{discount}</b>"
        line += ")\n"
    elif price:
        line += f"💰 <b>{price}</b>\n"

    # ⚡ Deal
    if deal:
        line += f"⚡ {deal}\n"

    # 💳 and 💥 Offers
    if bank_offer or normal_offer:
        offer_line = format_offer_line({
            "bank_offer": bank_offer,
            "normal_offer": normal_offer
        })
        if offer_line:
            line += f"{offer_line}\n"

    # 🛒 Buy Now
    line += f"🛒 <a href=\"{url}\">Buy Now</a>\n\n"
    return line










def format_top5_html(products, category):
    message = f"📦 <b>Top 5 in {category}</b>\n\n"
    for i, p in enumerate(products, start=1):
        message += format_list_item_html(i, p)
    return message.strip()




def format_budget_picks_html(products):
    message = "<b>Budget Picks of the Day (Under ₹999)</b>\n\n"
    for i, p in enumerate(products, start=1):
        category = p.get('category', '')
        if category:
            message += f"<b>{category}</b>\n"
        message += format_list_item_html(i, p)  # Re-use your existing detailed formatting!
    return message.strip()







def format_hidden_gems(products):
    if not products:
        return "No hidden gems found right now."
    # Get the main category display name and link from the first product
    main_category = products[0].get("category_display", "Hidden Gem")
    category_url = products[0].get("category_url")
    header = f"*Hidden Gem in {main_category}*" if main_category else "*Hidden Gem*"
    
    message = header + "\n\n"
    for p in products:
        caption = build_photo_caption(
            p,
            category_url=p.get("category_url")
        )
        message += caption + "\n\n"
    # Now place 'Explore more...' at the very end
    if category_url:
        message += f"🔎 Explore more in {main_category}: [Browse Category]({category_url})"

    return message.strip()


def build_photo_caption(product, category_url=None):
    def esc(text):
        if not text:
            return ""
        escape_chars = r"\_*[]()~`>#+-=|{}.!"
        return ''.join(['\\' + c if c in escape_chars else c for c in text])
    title        = esc(product.get("title", "No Title"))
    url          = esc(product.get("url", ""))
    price        = esc(product.get("price", ""))
    mrp          = esc(product.get("original_price") or product.get("mrp", ""))
    discount     = esc(product.get("discount", ""))
    rating       = esc(product.get("rating", ""))
    offer_line   = format_offer_line(product)
    # category_display for pretty text (like 'Travel & Shoe Bags')
    category_hr  = esc(product.get("category_display", ""))

    lines = []
    lines.append(f"*{title}*")  # Bold product title
    if rating:
        lines.append(f"⭐ {rating}")
    price_line = f"💰 {price}"
    if mrp and mrp != price:
        price_line += f" \\(MRP: ~{mrp}~"
        if discount:
            price_line += f" 🔻 {discount}"
        price_line += "\\)"
    lines.append(price_line)
    if offer_line:
        lines.append(esc(offer_line))
    if url:
        lines.append(f"🛒 [Buy Now]({url})")
    # The category link is already in the header, so you may skip it here
    return "\n".join(lines).strip()









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













