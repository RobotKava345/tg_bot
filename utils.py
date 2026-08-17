import logging
from enum import IntEnum

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)


class Role(IntEnum):
    MEMBER = 0
    HELPER = 1
    MODERATOR = 2
    SENIOR_ADMIN = 3
    OWNER = 4


ROLE_NAMES = {
    Role.OWNER: "Owner",
    Role.SENIOR_ADMIN: "Senior Admin",
    Role.MODERATOR: "Moderator",
    Role.HELPER: "Helper",
    Role.MEMBER: "Участник",
}

NO_RIGHTS_TEXT = "Недостаточно Порчи в твоей крови для этого ритуала."


async def get_member(bot: Bot, chat_id: int, user_id: int):
    try:
        return await bot.get_chat_member(chat_id, user_id)
    except TelegramAPIError as e:
        logger.warning(
            "Не удалось получить участника user_id=%s в chat_id=%s: %s",
            user_id, chat_id, e
        )
        return None
    except Exception as e:
        logger.error(
            "Неожиданная ошибка при получении участника user_id=%s в chat_id=%s: %s",
            user_id, chat_id, e
        )
        return None


def resolve_role(member) -> Role:
    if member is None:
        return Role.MEMBER

    if member.status == ChatMemberStatus.CREATOR:
        return Role.OWNER

    if member.status == ChatMemberStatus.ADMINISTRATOR:
        if getattr(member, "can_promote_members", False):
            return Role.SENIOR_ADMIN
        if getattr(member, "can_restrict_members", False) and getattr(member, "can_delete_messages", False):
            return Role.MODERATOR
        return Role.HELPER

    return Role.MEMBER


async def get_role(bot: Bot, chat_id: int, user_id: int) -> Role:
    member = await get_member(bot, chat_id, user_id)
    return resolve_role(member)


async def has_role(bot: Bot, chat_id: int, user_id: int, minimal: Role) -> bool:
    role = await get_role(bot, chat_id, user_id)
    return role >= minimal


# Используется в /exterminatus и для защиты "нельзя банить админа" —
# не завязана на RBAC специально, чтобы защищать любого Telegram-админа.
async def is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    member = await get_member(bot, chat_id, user_id)
    if member is None:
        return False
    return member.status in {ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR}


async def get_admin_ids(bot: Bot, chat_id: int) -> set[int]:
    try:
        admins = await bot.get_chat_administrators(chat_id)
        return {admin.user.id for admin in admins}
    except Exception as e:
        logger.warning(f"Не удалось получить список админов чата {chat_id}: {e}")
        return set()