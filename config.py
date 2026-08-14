import os
from dotenv import load_dotenv
 
load_dotenv()
 
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DB_NAME = os.environ.get("DB_NAME", "admin_bot.db")
 
if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не найден. Создай файл .env рядом с bot.py "
        "и укажи в нём BOT_TOKEN=твой_токен"
    )