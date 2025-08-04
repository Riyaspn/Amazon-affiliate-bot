# modules/prebuilt.py

import random
from datetime import datetime

AFFILIATE_TAG = "storesofriyas-21"

# 🔁 Rotating PREBUILT categories (3 per day)
PREBUILT_LINKS = [
    ("🛋️ Trending in Home Decor", "https://www.amazon.in/b?node=1380374031"),
    ("🧴 Top Beauty Essentials", "https://www.amazon.in/b?node=1374357031"),
    ("👕 Best Fashion Picks", "https://www.amazon.in/b?node=1968024031"),
    ("🍳 Kitchen Tools You’ll Love", "https://www.amazon.in/b?node=1380441031"),
    ("🛠️ Best Tools & Hardware", "https://www.amazon.in/b?node=4286640031"),
    ("🎧 Headphones & Speakers", "https://www.amazon.in/b?node=1388921031"),
    ("💼 Office Must-Haves", "https://www.amazon.in/s?rh=n%3A2454172031%2Cp_n_deal_type%3A26921224031"),
    ("🧹 Cleaning & Storage", "https://www.amazon.in/s?k=cleaning+and+storage&s=relevanceblender&crid=25KTWB4PHYL73&qid=1752392440&sprefix=cleaning+and+storage%2Caps%2C306&xpid=pBOh2BoU85Mtj&ref=sr_pg_1"),
    ("🖥️ Work from Home Essentials", "https://www.amazon.in/b?node=2088643031"),
    ("👶 Baby Must-Haves", "https://www.amazon.in/b?node=1571274031"),
    ("🚗 Car Accessories Deals", "https://www.amazon.in/b?node=5257479031"),
    ("🎮 Gaming Accessories", "https://www.amazon.in/b?node=4092115031"),
    ("🏕️ Outdoor & Travel Gear", "https://www.amazon.in/b?node=1984443031"),
    ("🏠 Smart Home Gadgets", "https://www.amazon.in/b?node=1629826031"),
    ("🧼 Under ₹999 Deals", "https://www.amazon.in/s?k=under+999&rh=p_36%3A-99900%2Cp_n_deal_type%3A26921224031"),
    ("📱 Smartphone Accessories", "https://www.amazon.in/b?node=1389401031"),
]

def get_prebuilt_links():
    today = datetime.now().toordinal()
    total = len(PREBUILT_LINKS)
    selected = []

    for i in range(3):  # 3 daily rotating picks
        idx = (today + i) % total
        title, url = PREBUILT_LINKS[idx]
        full_url = f"{url}&tag={AFFILIATE_TAG}"
        selected.append({"category": title, "url": full_url})

    return selected

def get_prebuilt_links_block():
    return PREBUILT_LINKS

# ⚡ Flash deal section
def get_flash_deal_links():
    return [
        {"title": "🟡 Lightning Deals", "url": f"https://www.amazon.in/deals?tag={AFFILIATE_TAG}"},
        {"title": "🛍️ Today’s Deals", "url": f"https://www.amazon.in/gp/goldbox?tag={AFFILIATE_TAG}"},
        {"title": "⚡ 50% Off or More", "url": f"https://www.amazon.in/s?i=deals&rh=p_n_deal_type%3A26921224031&tag={AFFILIATE_TAG}"},
    ]

# 💎 Hidden Gem logic 
import os
import random
from modules.utils import AFFILIATE_TAG
from modules.categories import HIDDEN_GEM_CATEGORIES

HIDDEN_GEM_LABELS = ["💎 Hidden Gem", "🆕 Niche Find", "💡 Smart Buy"]
HIDDEN_GEM_INDEX_FILE = "hidden_gem_index.txt"

def get_and_update_hidden_gem_index(num_categories):
    """
    Loads the current index from hidden_gem_index.txt,
    returns it, increments, and saves for next run.
    Wraps at num_categories.
    """
    idx = 0
    # Try to load the existing index if file exists
    if os.path.exists(HIDDEN_GEM_INDEX_FILE):
        try:
            with open(HIDDEN_GEM_INDEX_FILE, "r") as f:
                data = f.read().strip()
                if data:
                    idx = int(data)
        except Exception:
            idx = 0
    # Calculate next index (wraps around)
    new_idx = (idx + 1) % num_categories
    # Save new index back to file for next run
    with open(HIDDEN_GEM_INDEX_FILE, "w") as f:
        f.write(str(new_idx))
    return idx

def get_hidden_gem():
    """
    Returns the current hidden gem dict with:
    - label
    - category (user-friendly)
    - url (with your affiliate tag)
    Increments the category pointer, ensuring round-robin rotation.
    """
    num_categories = len(HIDDEN_GEM_CATEGORIES)
    idx = get_and_update_hidden_gem_index(num_categories)
    selected = HIDDEN_GEM_CATEGORIES[idx]
    label = random.choice(HIDDEN_GEM_LABELS)
    return {
        "label": label,
        "category": selected["label"],
        "url": f"{selected['url']}&tag={AFFILIATE_TAG}"
    }





# 🎯 Combo Deal Categories (easily editable)
COMBO_DEAL_CATEGORIES = {
    "🧖 Self-Care Combo": "https://www.amazon.in/s?k=self+care+combo&crid=28CFPBVG8MSPX&sprefix=Self-Care+Combo%2Caps%2C265&ref=nb_sb_ss_mvt-t11-ranker_1_15",
    "🧔 Men’s Grooming Combo": "https://www.amazon.in/s?k=Men%E2%80%99s+Grooming+Combo&crid=2B43QQLTS4VF5&sprefix=men+s+grooming+combo%2Caps%2C260&ref=nb_sb_noss_2",
    "👶 Baby Care Starter Pack": "https://www.amazon.in/s?k=baby+care+pack&crid=307GZ8A03Y3O0&sprefix=Baby+Care+Pack%2Caps%2C250&ref=nb_sb_ss_mvt-t11-ranker_1_14",
    "🧴 Glow-Up Kit": "https://www.amazon.in/s?k=Glow-Up+Kit&crid=2S5UVWXGY885M&sprefix=glow-up+kit%2Caps%2C259&ref=nb_sb_noss_2",
    "💆 Spa-at-Home Bundle": "https://www.amazon.in/s?k=home+spa+kit&crid=3NV8NAL9YVJ3E&sprefix=Home+spa+%2Caps%2C251&ref=nb_sb_ss_mvt-t11-ranker_2_9",
    "💪 Fitness Fuel Combo": "https://www.amazon.in/s?k=Fitness+Fuel+Combo&s=relevanceblender&crid=8JXNDYFJQBIW&qid=1752099927&sprefix=fitness+fuel+combo%2Caps%2C276&ref=sr_st_relevanceblender&ds=v1%3AVSItZ3IZGYy%2FX2vA0BovknpZwe91NPxpMY10E9Dtvj8",
}

# 🎯 Randomly pick one combo deal category (like Product of the Day)
def get_random_combo_category():
    category = random.choice(list(COMBO_DEAL_CATEGORIES.keys()))
    return category, COMBO_DEAL_CATEGORIES[category]


# 💸 Budget Picks Categories (under ₹999)
BUDGET_PICK_CATEGORIES = {
    "🧴 Beauty Essentials": "https://www.amazon.in/s?k=beauty&rh=p_36%3A-99900",
    "🧹 Kitchen Essentials": "https://www.amazon.in/s?k=kitchen&rh=p_36%3A-99900",
    "🎧 Mobile Accessories": "https://www.amazon.in/s?k=mobile+accessories&rh=p_36%3A-99900",
    "🧦 Fashion Under ₹999": "https://www.amazon.in/s?k=clothing&rh=p_36%3A-99900",
    "🖊️ Stationery & Supplies": "https://www.amazon.in/s?k=stationery&rh=p_36%3A-99900",
    "🧴 Health & Wellness": "https://www.amazon.in/s?k=health&rh=p_36%3A-99900",
}





