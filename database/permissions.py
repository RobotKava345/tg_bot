from database.admins import has_permission
from database.models import (
    VIEW_PROFILE,
    EDIT_NAME,
    EDIT_ROLE,
    EDIT_RANK,
    EDIT_LEGION,
    EDIT_STATUS,
    EDIT_REPUTATION,
    MANAGE_RANKS,
    MANAGE_LEGIONS,
    MANAGE_ROLES,
    MANAGE_STATUSES,
    MANAGE_ADMINS,
    MANAGE_PERMISSIONS,
    MODERATE_USERS,
    VIEW_AUDIT_LOG,
)


# ============================================================
# БАЗОВАЯ ПРОВЕРКА
# ============================================================

async def check_permission(
    bot,
    chat_id: int,
    user_id: int,
    permission: str,
) -> bool:
    """
    Проверяет, обладает ли пользователь указанным правом в конкретном чате.

    Учитывает и явное назначение в базе (chat_admins), и реальные права
    администратора в самом Telegram (см. database/admins.py).
    """
    return await has_permission(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        permission=permission,
    )


# ============================================================
# КАРТОЧКА УЧАСТНИКА
# ============================================================

async def can_view_profile(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, VIEW_PROFILE)


async def can_edit_name(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, EDIT_NAME)


async def can_edit_role(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, EDIT_ROLE)


async def can_edit_rank(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, EDIT_RANK)


async def can_edit_legion(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, EDIT_LEGION)


async def can_edit_status(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, EDIT_STATUS)


async def can_edit_reputation(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, EDIT_REPUTATION)


# ============================================================
# УПРАВЛЕНИЕ ЗВАНИЯМИ / ЛЕГИОНАМИ / РОЛЯМИ / СТАТУСАМИ
# ============================================================

async def can_manage_ranks(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, MANAGE_RANKS)


async def can_manage_legions(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, MANAGE_LEGIONS)


async def can_manage_roles(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, MANAGE_ROLES)


async def can_manage_statuses(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, MANAGE_STATUSES)


# ============================================================
# УПРАВЛЕНИЕ АДМИНИСТРАТОРАМИ
# ============================================================

async def can_manage_admins(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, MANAGE_ADMINS)


async def can_manage_permissions(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, MANAGE_PERMISSIONS)


# ============================================================
# МОДЕРАЦИЯ
# ============================================================

async def can_moderate_users(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, MODERATE_USERS)


# ============================================================
# АУДИТ
# ============================================================

async def can_view_audit_log(bot, chat_id: int, user_id: int) -> bool:
    return await check_permission(bot, chat_id, user_id, VIEW_AUDIT_LOG)