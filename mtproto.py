import logging
import os

from dotenv import load_dotenv
from telethon import TelegramClient

from database.db import add_user


load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

logger = logging.getLogger(__name__)

client = TelegramClient(
    "telegram_session",
    API_ID,
    API_HASH,
)


SYNC_CHATS = {
    -1002427719174: "Хаоситы",
    -1003993853383: "ТЕСТ",
}


async def sync_chat_members(chat_id: int) -> int:
    """
    Синхронизирует участников указанного Telegram-чата
    с таблицей seen_users.

    Возвращает количество обработанных пользователей.
    """

    chat = await client.get_entity(chat_id)

    title = getattr(chat, "title", str(chat_id))

    logger.info(
        "Начинается синхронизация чата '%s' (%s)",
        title,
        chat_id,
    )

    count = 0

    async for user in client.iter_participants(chat):
        if user.bot:
            continue

        await add_user(
            chat_id=chat_id,
            user_id=user.id,
        )

        count += 1

    logger.info(
        "Синхронизация '%s' завершена. Обработано: %d",
        title,
        count,
    )

    return count


async def sync_all_chats():
    """
    Синхронизирует все чаты из SYNC_CHATS.
    """

    for chat_id, title in SYNC_CHATS.items():
        try:
            await sync_chat_members(chat_id)

        except Exception:
            logger.exception(
                "Ошибка синхронизации чата '%s' (%s)",
                title,
                chat_id,
            )