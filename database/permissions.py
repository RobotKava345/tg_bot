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
    chat_id: int,
    user_id: int,
    permission: str,
) -> bool:
    """
    Проверяет, обладает ли пользователь указанным правом
    в конкретном чате.
    """

    return await has_permission(
        chat_id=chat_id,
        user_id=user_id,
        permission=permission,
    )


# ============================================================
# КАРТОЧКА УЧАСТНИКА
# ============================================================

async def can_view_profile(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        VIEW_PROFILE,
    )


async def can_edit_name(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        EDIT_NAME,
    )


async def can_edit_role(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        EDIT_ROLE,
    )


async def can_edit_rank(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        EDIT_RANK,
    )


async def can_edit_legion(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        EDIT_LEGION,
    )


async def can_edit_status(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        EDIT_STATUS,
    )


async def can_edit_reputation(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        EDIT_REPUTATION,
    )


# ============================================================
# УПРАВЛЕНИЕ ЗВАНИЯМИ
# ============================================================

async def can_manage_ranks(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        MANAGE_RANKS,
    )


# ============================================================
# УПРАВЛЕНИЕ ЛЕГИОНАМИ
# ============================================================

async def can_manage_legions(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        MANAGE_LEGIONS,
    )


# ============================================================
# УПРАВЛЕНИЕ РОЛЯМИ
# ============================================================

async def can_manage_roles(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        MANAGE_ROLES,
    )


# ============================================================
# УПРАВЛЕНИЕ СТАТУСАМИ
# ============================================================

async def can_manage_statuses(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        MANAGE_STATUSES,
    )


# ============================================================
# УПРАВЛЕНИЕ АДМИНИСТРАТОРАМИ
# ============================================================

async def can_manage_admins(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        MANAGE_ADMINS,
    )


async def can_manage_permissions(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        MANAGE_PERMISSIONS,
    )


# ============================================================
# МОДЕРАЦИЯ
# ============================================================

async def can_moderate_users(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        MODERATE_USERS,
    )


# ============================================================
# АУДИТ
# ============================================================

async def can_view_audit_log(
    chat_id: int,
    user_id: int,
) -> bool:
    return await check_permission(
        chat_id,
        user_id,
        VIEW_AUDIT_LOG,
    )