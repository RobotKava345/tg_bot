import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database.db import init_db
from database.pool import close_pool, init_pool
from handlers import ext, info, stats, tracking
from mtproto import client as telethon_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()

# Command routers go before passive tracking.
dp.include_router(info.router)
dp.include_router(ext.router)
dp.include_router(stats.router)
dp.include_router(tracking.router)


async def main() -> None:
    await init_pool()
    await init_db()

    await telethon_client.connect()
    if not await telethon_client.is_user_authorized():
        raise RuntimeError(
            "Telethon session is not authorized. Generate a new "
            "TELETHON_SESSION_STRING with scripts/generate_telethon_session.py."
        )

    logger.info("Telethon connected")
    logger.info("Bot started")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot,
            allowed_updates=["message", "chat_member", "callback_query"],
        )
    finally:
        await telethon_client.disconnect()
        await close_pool()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
