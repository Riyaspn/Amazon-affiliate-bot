# modules/categories.py
import random

FIXED_CATEGORIES = {
    "Electronics": "https://www.amazon.in/gp/bestsellers/electronics/",
    "Beauty": "https://www.amazon.in/gp/bestsellers/beauty/",
    "Home & Kitchen": "https://www.amazon.in/gp/bestsellers/kitchen/",
}

ROTATING_CATEGORIES = {
    "Men’s Fashion": "https://www.amazon.in/gp/bestsellers/apparel/1968024031/",
    "Women’s Fashion": "https://www.amazon.in/gp/bestsellers/apparel/1968023031/",
    "Footwear": "https://www.amazon.in/gp/bestsellers/shoes/",
    "Grocery": "https://www.amazon.in/gp/bestsellers/grocery/",
    "Books": "https://www.amazon.in/gp/most-gifted/books/ref=zg_bs_tab_t_books_mg",
    "Toys": "https://www.amazon.in/gp/bestsellers/toys/",
    "Office Products": "https://www.amazon.in/s?k=Office+Products&s=exact-aware-popularity-rank&dc&language=en_IN&crid=10BXZMVLO17UB&linkCode=ll2&linkId=6666c1c5932d571ebf4edcd1fd576dec&qid=1752338154&sprefix=office+products%2Caps%2C250&tag=storesofriyas-21&ref=sr_ex_p_n_deal_type_0&ds=v1%3A%2BQTv%2FX7YphDmMvpHHvrfCg7Q%2BkNxEOmcrwPkYIclMls",
    "Home Decor": "https://www.amazon.in/gp/bestsellers/home-improvement/",
    "Watches": "https://www.amazon.in/gp/bestsellers/watches/",
    "Mobiles": "https://www.amazon.in/gp/bestsellers/electronics/1805560031/",
    "Earphones": "https://www.amazon.in/gp/bestsellers/electronics/1388921031/",
    "Chargers": "https://www.amazon.in/gp/bestsellers/electronics/1389396031/",
    "Sports": "https://www.amazon.in/gp/bestsellers/sports/",
    "Gaming": "https://www.amazon.in/gp/bestsellers/videogames/",
    "Car Accessories": "https://www.amazon.in/gp/bestsellers/automotive/",
    "Kitchen Tools": "https://www.amazon.in/gp/bestsellers/kitchen/1380442031/",
}

HIDDEN_GEM_CATEGORIES = [
    {"label": "🧳 Travel Accessories", "url": "https://www.amazon.in/s?i=luggage&bbn=2454164031"},  # Subcategory for travel gadgets
    {"label": "🎒 Backpacks & Trolleys", "url": "https://www.amazon.in/s?i=luggage&rh=n%3A2454163031"},  # Broader luggage
    {"label": "🛫 Packing Organizers", "url": "https://www.amazon.in/s?i=luggage&bbn=2454167031"},
    {"label": "😴 Travel Pillows & Comfort", "url": "https://www.amazon.in/s?i=luggage&bbn=2454168031"},
    # Add more hidden gems below...
    {"label": "🧸 Toys & Games", "url": "https://www.amazon.in/s?i=toys&rh=n%3A1350380031"},
    {"label": "🐾 Pet Supplies", "url": "https://www.amazon.in/s?i=pets&rh=n%3A2454181031"},
    {"label": "🎸 Musical Instruments", "url": "https://www.amazon.in/s?i=mi&rh=n%3A1377374031"},
    {"label": "🛒 Gourmet Foods", "url": "https://www.amazon.in/s?i=grocery&rh=n%3A2454178031"},
    {"label": "🔬 Industrial & Scientific", "url": "https://www.amazon.in/s?i=industrial&rh=n%3A976442031"},
    {"label": "🪴 Garden & Outdoors", "url": "https://www.amazon.in/s?i=lawn-garden&rh=n%3A2454182031"},
    {"label": "🚗 Car & Motorbike", "url": "https://www.amazon.in/s?i=automotive&rh=n%3A5257479031"},
    {"label": "🎁 Quirky Gifts & Gadgets", "url": "https://www.amazon.in/s?i=toys&rh=n%3A1378569031"},
]



def get_hidden_gem_category(day=None):
    """Return a deterministic hidden gem category based on day, or random one."""
    if not day:
        day = get_day()
    seed = sum(ord(c) for c in day)  # deterministic seed from day name
    random.seed(seed)
    return random.choice(HIDDEN_GEM_CATEGORIES)


def get_random_rotating_categories(n=3):
    """Return n random rotating categories (default: 3)."""
    return random.sample(list(ROTATING_CATEGORIES.items()), n)

from datetime import datetime

def get_day():
    """Returns the current weekday as a string, e.g., 'Monday'."""
    return datetime.now().strftime('%A')


