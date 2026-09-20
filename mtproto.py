import logging

from telethon import TelegramClient
from telethon.sessions import StringSession

from config import settings
from database.db import add_user

logger = logging.getLogger(__name__)

client = TelegramClient(
    StringSession(settings.telethon_session_string),
    settings.telegram_api_id,
    settings.telegram_api_hash,
)


async def sync_chat_members(chat_id: int) -> int:
    chat = await client.get_entity(chat_id)
    title = getattr(chat, "title", str(chat_id))

    logger.info("Synchronizing chat '%s' (%s)", title, chat_id)

    count = 0

    async for user in client.iter_participants(chat):
        if user.bot:
            continue

        await add_user(chat_id=chat_id, user_id=user.id)
        count += 1

    logger.info(
        "Synchronization complete for '%s': %d users",
        title,
        count,
    )
    return count
