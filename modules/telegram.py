import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send(message: str, parse_mode: str = "Markdown"):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Telegram credentials not set.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
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


async def send_photo(photo_url: str, caption: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Telegram credentials not set.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as res:
            if res.status != 200:
                print(f"❌ Telegram photo error: {await res.text()}")

async def send_html(message: str):
    await send(message, parse_mode="HTML")

