import logging
 
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError
 
logger = logging.getLogger(__name__)
 
 
async def is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in {
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR
        }
    except TelegramAPIError as e:
        logger.warning(
            "Не удалось проверить права user_id=%s в chat_id=%s: %s",
            user_id, chat_id, e
        )
        return False
    except Exception as e:
        logger.error(
            "Неожиданная ошибка при проверке прав user_id=%s в chat_id=%s: %s",
            user_id, chat_id, e
        )
        return False
 
 
async def get_admin_ids(bot: Bot, chat_id: int) -> set[int]:
    try:
        admins = await bot.get_chat_administrators(chat_id)
        return {admin.user.id for admin in admins}
    except Exception as e:
        logger.warning(f"Не удалось получить список админов чата {chat_id}: {e}")
        return set()