import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.db import init_db
from mtproto import client as mtproto_client, sync_all_chats

from handlers import ext, tracking, moderation, stats, info


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)


bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()


# Порядок подключения важен:
# команды должны находиться выше tracking.
dp.include_router(moderation.router)
dp.include_router(stats.router)
dp.include_router(ext.router)
dp.include_router(info.router)
dp.include_router(tracking.router)


async def main():
    await init_db()

    logger.info("Запуск Telethon...")

    await mtproto_client.start()

    me = await mtproto_client.get_me()

    logger.info(
        "Telethon авторизован: @%s (%s)",
        me.username,
        me.id,
    )

    logger.info("Запуск синхронизации участников...")

    await sync_all_chats()

    logger.info("Синхронизация участников завершена")

    logger.info("Админ-бот запущен")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message",
                "chat_member",
            ],
        )

    finally:
        logger.info("Остановка Telethon...")
        await mtproto_client.disconnect()

        logger.info("Остановка бота...")
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Бот остановлен")
 