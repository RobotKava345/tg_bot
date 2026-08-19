"""
Управление админ-типами и правами (RBAC) + автосинхронизация с
реальными правами администратора в самом Telegram.

Как это работает (полный гибрид, вариант B) — см. подробное описание
в предыдущей версии файла. Здесь та же логика, переписанная под
Postgres/asyncpg вместо aiosqlite.
"""

import logging

from database.pool import get_pool
from utils import Role, get_role
from database.models import PERMISSIONS

logger = logging.getLogger(__name__)


def _parse_rowcount(status: str) -> int:
    """
    asyncpg возвращает статус команды строкой вида 'UPDATE 1',
    'INSERT 0 1', 'DELETE 3'. Достаём число изменённых строк.
    """
    try:
        return int(status.split()[-1])
    except (ValueError, IndexError):
        return 0


# ============================================================
# КАТАЛОГ ADMIN_TYPES И ИХ РАНГ
# ============================================================

ADMIN_TYPE_RANK = {
    "owner": 4,
    "superadmin": 3,
    "admin": 2,
    "primarch": 2,
    "moderator": 1,
}

ADMIN_TYPE_DESCRIPTIONS = {
    "owner": "Полный доступ ко всем функциям бота.",
    "superadmin": "Модерация, управление карточками участников, "
                  "званиями, легионами, статусами, просмотр аудита.",
    "admin": "Базовая модерация и работа с карточками участников.",
    "moderator": "Только просмотр карточек участников.",
    "primarch": "Управление своим легионом: звания, состав, редактирование.",
}

TELEGRAM_ROLE_TO_ADMIN_TYPE = {
    Role.OWNER: "owner",
    Role.SENIOR_ADMIN: "superadmin",
    Role.MODERATOR: "admin",
    Role.HELPER: "moderator",
    Role.MEMBER: None,
}

DEFAULT_TYPE_PERMISSIONS = {
    "owner": set(PERMISSIONS),

    "superadmin": {
        "moderate_users",
        "view_profile",
        "edit_name",
        "edit_role",
        "edit_rank",
        "edit_legion",
        "edit_status",
        "edit_reputation",
        "manage_ranks",
        "manage_legions",
        "manage_statuses",
        "manage_admins",
        "view_audit_log",
    },

    "admin": {
        "moderate_users",
        "view_profile",
        "edit_status",
        "edit_reputation",
    },

    "moderator": {
        "view_profile",
    },

    "primarch": {
        "view_profile",
        "edit_legion",
        "manage_ranks",
    },
}


# ============================================================
# СИДИРОВАНИЕ (идемпотентно — безопасно вызывать при каждом старте)
# ============================================================

async def seed_admin_types():
    pool = get_pool()
    for name, description in ADMIN_TYPE_DESCRIPTIONS.items():
        await pool.execute(
            """
            INSERT INTO admin_types (name, description)
            VALUES ($1, $2)
            ON CONFLICT (name) DO NOTHING
            """,
            name, description,
        )


async def seed_permissions():
    pool = get_pool()
    for code in PERMISSIONS:
        await pool.execute(
            """
            INSERT INTO permissions (code, name)
            VALUES ($1, $2)
            ON CONFLICT (code) DO NOTHING
            """,
            code, code.replace("_", " ").capitalize(),
        )


async def seed_admin_type_permissions():
    pool = get_pool()

    for type_name, codes in DEFAULT_TYPE_PERMISSIONS.items():
        admin_type_id = await pool.fetchval(
            "SELECT id FROM admin_types WHERE name = $1",
            type_name,
        )
        if admin_type_id is None:
            continue

        for code in codes:
            permission_id = await pool.fetchval(
                "SELECT id FROM permissions WHERE code = $1",
                code,
            )
            if permission_id is None:
                continue

            await pool.execute(
                """
                INSERT INTO admin_type_permissions (admin_type_id, permission_id)
                VALUES ($1, $2)
                ON CONFLICT (admin_type_id, permission_id) DO NOTHING
                """,
                admin_type_id, permission_id,
            )


async def seed_rbac_defaults():
    """Вызывать один раз при старте бота (после init_db)."""
    await seed_admin_types()
    await seed_permissions()
    await seed_admin_type_permissions()
    logger.info("RBAC: каталоги admin_types/permissions заполнены")


# ============================================================
# CHAT_ADMINS — явные назначения
# ============================================================

async def assign_admin(
    chat_id: int,
    user_id: int,
    admin_type_name: str,
    assigned_by: int | None = None,
) -> bool:
    if admin_type_name not in ADMIN_TYPE_RANK:
        raise ValueError(f"Неизвестный admin_type: {admin_type_name}")

    pool = get_pool()

    admin_type_id = await pool.fetchval(
        "SELECT id FROM admin_types WHERE name = $1",
        admin_type_name,
    )
    if admin_type_id is None:
        return False

    await pool.execute(
        """
        INSERT INTO chat_admins (chat_id, user_id, admin_type_id, active, assigned_by)
        VALUES ($1, $2, $3, TRUE, $4)
        ON CONFLICT (chat_id, user_id) DO UPDATE SET
            admin_type_id = EXCLUDED.admin_type_id,
            active = TRUE,
            assigned_by = EXCLUDED.assigned_by
        """,
        chat_id, user_id, admin_type_id, assigned_by,
    )

    logger.info(
        "Назначен admin_type '%s' пользователю %s в чате %s",
        admin_type_name, user_id, chat_id,
    )
    return True


async def remove_admin(chat_id: int, user_id: int) -> bool:
    pool = get_pool()
    status = await pool.execute(
        """
        UPDATE chat_admins SET active = FALSE
        WHERE chat_id = $1 AND user_id = $2
        """,
        chat_id, user_id,
    )
    return _parse_rowcount(status) > 0


async def get_explicit_admin_type(chat_id: int, user_id: int) -> str | None:
    """Явно назначенный admin_type из базы (без учёта Telegram-прав)."""
    pool = get_pool()
    return await pool.fetchval(
        """
        SELECT admin_types.name
        FROM chat_admins
        JOIN admin_types ON admin_types.id = chat_admins.admin_type_id
        WHERE chat_admins.chat_id = $1
          AND chat_admins.user_id = $2
          AND chat_admins.active = TRUE
          AND admin_types.active = TRUE
        """,
        chat_id, user_id,
    )


async def get_chat_admins(chat_id: int) -> list[dict]:
    """Все активные назначенные админы конкретного чата."""
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT chat_admins.user_id, admin_types.name AS admin_type
        FROM chat_admins
        JOIN admin_types ON admin_types.id = chat_admins.admin_type_id
        WHERE chat_admins.chat_id = $1
          AND chat_admins.active = TRUE
        ORDER BY admin_types.id
        """,
        chat_id,
    )
    return [dict(row) for row in rows]


# ============================================================
# АУДИТ
# ============================================================

async def log_audit(
    chat_id: int,
    actor_id: int,
    action: str,
    target_id: int | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
):
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO audit_logs
        (chat_id, actor_id, action, target_id, old_value, new_value)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        chat_id, actor_id, action, target_id, old_value, new_value,
    )


# ============================================================
# ПРОВЕРКА ПРАВА — ТОЧКА ВХОДА ДЛЯ permissions.py
# ============================================================

async def admin_type_has_permission(admin_type_name: str, permission_code: str) -> bool:
    pool = get_pool()
    row = await pool.fetchval(
        """
        SELECT 1
        FROM admin_type_permissions
        JOIN admin_types ON admin_types.id = admin_type_permissions.admin_type_id
        JOIN permissions ON permissions.id = admin_type_permissions.permission_id
        WHERE admin_types.name = $1
          AND permissions.code = $2
          AND admin_types.active = TRUE
        LIMIT 1
        """,
        admin_type_name, permission_code,
    )
    return row is not None


async def has_permission(bot, chat_id: int, user_id: int, permission: str) -> bool:
    """
    Главная функция проверки прав. Требует объект bot — нужен,
    чтобы узнать реальные права пользователя в Telegram.
    """

    telegram_role = await get_role(bot, chat_id, user_id)
    telegram_type_name = TELEGRAM_ROLE_TO_ADMIN_TYPE.get(telegram_role)

    explicit_type_name = await get_explicit_admin_type(chat_id, user_id)

    # Автосинхронизация: если реальные права в Telegram выше того,
    # что записано явно в базе — подтягиваем запись вверх.
    if telegram_type_name and ADMIN_TYPE_RANK.get(
        telegram_type_name, 0
    ) > ADMIN_TYPE_RANK.get(explicit_type_name, 0):
        await assign_admin(chat_id, user_id, telegram_type_name)
        explicit_type_name = telegram_type_name

    effective_type = explicit_type_name or telegram_type_name

    result = False
    if effective_type:
        result = await admin_type_has_permission(effective_type, permission)

    logger.info(
        "DEBUG has_permission: user_id=%s, permission=%s, "
        "telegram_role=%s, telegram_type=%s, explicit_type=%s, "
        "effective_type=%s, result=%s",
        user_id, permission,
        telegram_role, telegram_type_name, explicit_type_name,
        effective_type, result,
    )

    return result