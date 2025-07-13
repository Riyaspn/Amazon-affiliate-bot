# modules/templates.py

def build_prebuilt_links_message(categories):
    message = "🔗 *Amazon Prebuilt Category Pages*\n\n"
    for cat in categories:
        message += f"📢 *{cat['category']}*\n🔗 [View Deals]({cat['url']})\n\n"
    return message.strip()





def build_hidden_gem_message(category_name, products):
    if not products:
        return None

    message = f"📢 💎 *HIDDEN GEM: {category_name.upper()} DEALS*\n\n"
    for i, product in enumerate(products):
        label = "🔥 Hot Deal" if i == 0 else "⭐ Top Pick"
        message += f"""{label}
🛒 *{product['title']}*
💰 {product['price']}
⭐ {product['rating']}
🔗 [View on Amazon]({product['link']})

"""
    return message.strip()






def build_budget_picks_message(products):
    header = "💸 *Top Budget Picks (Under ₹999)*\n"
    body = ""
    for p in products:
        body += f"\n[{p['title']}]({p['link']})\n💰 ₹{p['price']}   ⭐ {p['rating']}\n"
    return header + body






def build_flash_deals_message(deals):
    message = "⚡ *FLASH DEALS ALERT!*\n\n"
    for deal in deals:
        message += f"{deal['title']}\n🔗 [View Deal]({deal['url']})\n\n"
    return message.strip()







import html
import re

def truncate(text, limit=100):
    text = text.strip()
    return text[:limit].rsplit(' ', 1)[0] + "..." if len(text) > limit else text

def build_combo_message(label, products, category_url=None):
    if not products or not isinstance(products, list):
        return f"⚠️ No combo products found for <b>{html.escape(label)}</b>."

    message = f"🎯 <b>Combo Deal – {html.escape(label)}</b>\n\n"

    for product in products:
        try:
            title = html.escape(truncate(product.get("title", "No title")))
            price = html.escape(product.get("price", "N/A"))
            rating = html.escape(product.get("rating", "⭐ N/A"))
            url = product.get("url", "#")  # DO NOT escape href URLs
            label_tag = html.escape(product.get("label", "⭐ Top Rated"))

            message += (
                f"{label_tag} <b>{title}</b>\n"
                f"{price} | ⭐ {rating}\n"
                f"<a href=\"{url}\">🔗 View Deal</a>\n\n"
            )
        except Exception as e:
            message += f"⚠️ Error formatting product: {html.escape(str(e))}\n"

    if category_url:
        # DO NOT escape href URL
        message += (
            f"<i>🔎 Explore more combo deals:</i> "
            f"<a href=\"{category_url}\">Browse Category</a>"
        )

    return message.strip()















def build_product_of_day_message(product):
    label = "🔍 *Product of the Day*"
    return f"""{label}

🛒 *{product['title']}*
💰 {product['price']}
⭐ {product['rating']}
🔗 [View on Amazon]({product['link']})
"""





def format_product_message(product, label, show_affiliate=True):
    title = product.get("title", "")
    price = product.get("price", "")
    rating = product.get("rating", "")
    link = product.get("affiliate_link", product.get("url", ""))

    message = f"""{label} *{title}*\n💰 Price: ₹{price}\n⭐ Rating: {rating}\n🔗 [View on Amazon]({link})"""
    return message

def build_category_header(category: str) -> str:
    return f"\n📢 *{category.upper()} DEALS*\n"

def build_morning_intro(label: str) -> str:
    return f"🌅 *Good Morning!* Here's your {label} for today:\n"

def build_evening_intro(label: str) -> str:
    return f"🌆 *Evening Deals:* {label} just dropped! Don't miss out:\n"

def build_product_message(product: dict) -> str:
    title = product.get("title", "No title")
    price = product.get("price", "N/A")
    rating = product.get("rating", "⭐ N/A")
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




def format_top_5_product_message(product, index):
    label = "🔥 Hot Deal" if index == 0 else (
        "💸 Premium Pick" if index == 1 else "⭐ Top Rated"
    )

    name = product.get("title") or product.get("name") or "No Name"
    price = product.get("price", "Price Not Available")
    rating = product.get("rating", "N/A")
    url = product.get("url", "#")

    return (
        f"<b>{label}</b>\n"
        f"🛒 <b>{name}</b>\n"
        f"💰 {price}\n"
        f"⭐ {rating}\n"
        f"🔗 <a href=\"{url}\">View on Amazon</a>"
    )

def format_top5_html(category_name: str, products: list) -> str:
    header = f"<b>📢 {category_name.upper()} DEALS</b>\n\n"
    body = ""

    for i, product in enumerate(products[:5]):
        body += format_top_5_product_message(product, i) + "\n\n"

    return (header + body).strip()
