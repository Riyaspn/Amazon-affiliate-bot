
# modules/telegram.py
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# General text message
async def send(message: str, parse_mode: str = "HTML"):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Telegram credentials not set.")
        return

    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as res:
            if res.status != 200:
                print(f"❌ Telegram error: {await res.text()}")

# HTML sender shortcut (used for most messages)
async def send_html(message: str):
    await send(message, parse_mode="HTML")

# Markdown sender shortcut (for legacy or caption use if needed)
async def send_markdown(message: str):
    await send(message, parse_mode="Markdown")

# Photo message with Markdown caption (used for hidden gem, product of the day, etc.)
async def send_photo(photo_url: str, caption: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Telegram credentials not set.")
        return

    url = f"{BASE_URL}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "Markdown",  # Markdown is best supported in photo captions
        "disable_web_page_preview": True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as res:
            if res.status != 200:
                print(f"❌ Telegram photo error: {await res.text()}")
