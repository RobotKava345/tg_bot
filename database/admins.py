"""
Управление админ-типами и правами (RBAC) + автосинхронизация с
реальными правами администратора в самом Telegram.

Как это работает (полный гибрид, вариант B):

1. У каждого пользователя в чате может быть ЯВНАЯ запись в chat_admins
   (admin_type: owner / superadmin / admin / moderator / primarch).

2. Параллельно у пользователя есть РЕАЛЬНЫЕ права в Telegram
   (Owner/Senior Admin/Moderator/Helper из utils.Role — вычисляются
   из настоящих прав администратора чата).

3. При проверке прав (has_permission) берётся эффективный admin_type —
   тот из двух источников, у которого выше ранг (ADMIN_TYPE_RANK).

4. Если Telegram-права оказались выше того, что записано в chat_admins —
   запись в базе автоматически подтягивается вверх (write-through).
   Обратное (кто-то лишился прав в Telegram) автоматически НЕ снижает
   явную запись в базе — это осознанное решение вручную снимает
   владелец/старший админ.
"""

import logging

import aiosqlite

from config import DB_NAME
from utils import Role, get_role
from database.models import PERMISSIONS

logger = logging.getLogger(__name__)


# ============================================================
# КАТАЛОГ ADMIN_TYPES И ИХ РАНГ
# ============================================================
# Ранг нужен только для сравнения "у кого из двух источников
# прав больше" — сами права всё равно определяются таблицей
# admin_type_permissions, а не этим числом.

ADMIN_TYPE_RANK = {
    "owner": 4,
    "superadmin": 3,
    "admin": 2,
    "primarch": 2,   # тот же уровень, что admin, но другой набор прав
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


# Соответствие реальных прав Telegram -> admin_type по умолчанию
TELEGRAM_ROLE_TO_ADMIN_TYPE = {
    Role.OWNER: "owner",
    Role.SENIOR_ADMIN: "superadmin",
    Role.MODERATOR: "admin",
    Role.HELPER: "moderator",
    Role.MEMBER: None,
}


# ============================================================
# ДЕФОЛТНАЯ МАТРИЦА ПРАВ ПО УМОЛЧАНИЮ
# ============================================================
# MANAGE_ADMINS / MANAGE_PERMISSIONS / MANAGE_ROLES сознательно
# оставлены только у owner — иначе superadmin сможет сам себе
# выдать любые права, включая право назначать других owner'ов.

DEFAULT_TYPE_PERMISSIONS = {
    "owner": set(PERMISSIONS),  # всё

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
    async with aiosqlite.connect(DB_NAME) as db:
        for name, description in ADMIN_TYPE_DESCRIPTIONS.items():
            await db.execute(
                """
                INSERT OR IGNORE INTO admin_types (name, description)
                VALUES (?, ?)
                """,
                (name, description),
            )
        await db.commit()


async def seed_permissions():
    async with aiosqlite.connect(DB_NAME) as db:
        for code in PERMISSIONS:
            await db.execute(
                """
                INSERT OR IGNORE INTO permissions (code, name)
                VALUES (?, ?)
                """,
                (code, code.replace("_", " ").capitalize()),
            )
        await db.commit()


async def seed_admin_type_permissions():
    async with aiosqlite.connect(DB_NAME) as db:
        for type_name, codes in DEFAULT_TYPE_PERMISSIONS.items():
            type_row = await db.execute(
                "SELECT id FROM admin_types WHERE name = ?",
                (type_name,),
            )
            type_id_row = await type_row.fetchone()
            if type_id_row is None:
                continue
            admin_type_id = type_id_row[0]

            for code in codes:
                perm_row = await db.execute(
                    "SELECT id FROM permissions WHERE code = ?",
                    (code,),
                )
                perm_id_row = await perm_row.fetchone()
                if perm_id_row is None:
                    continue
                permission_id = perm_id_row[0]

                await db.execute(
                    """
                    INSERT OR IGNORE INTO admin_type_permissions
                    (admin_type_id, permission_id)
                    VALUES (?, ?)
                    """,
                    (admin_type_id, permission_id),
                )
        await db.commit()


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

    async with aiosqlite.connect(DB_NAME) as db:
        type_row = await db.execute(
            "SELECT id FROM admin_types WHERE name = ?",
            (admin_type_name,),
        )
        row = await type_row.fetchone()
        if row is None:
            return False
        admin_type_id = row[0]

        await db.execute(
            """
            INSERT INTO chat_admins (chat_id, user_id, admin_type_id, active, assigned_by)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET
                admin_type_id = excluded.admin_type_id,
                active = 1,
                assigned_by = excluded.assigned_by
            """,
            (chat_id, user_id, admin_type_id, assigned_by),
        )
        await db.commit()

    logger.info(
        "Назначен admin_type '%s' пользователю %s в чате %s",
        admin_type_name, user_id, chat_id,
    )
    return True


async def remove_admin(chat_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            UPDATE chat_admins SET active = 0
            WHERE chat_id = ? AND user_id = ?
            """,
            (chat_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_explicit_admin_type(chat_id: int, user_id: int) -> str | None:
    """Явно назначенный admin_type из базы (без учёта Telegram-прав)."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT admin_types.name
            FROM chat_admins
            JOIN admin_types ON admin_types.id = chat_admins.admin_type_id
            WHERE chat_admins.chat_id = ?
              AND chat_admins.user_id = ?
              AND chat_admins.active = 1
              AND admin_types.active = 1
            """,
            (chat_id, user_id),
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def get_chat_admins(chat_id: int) -> list[dict]:
    """Все активные назначенные админы конкретного чата."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT chat_admins.user_id, admin_types.name AS admin_type
            FROM chat_admins
            JOIN admin_types ON admin_types.id = chat_admins.admin_type_id
            WHERE chat_admins.chat_id = ?
              AND chat_admins.active = 1
            ORDER BY admin_types.id
            """,
            (chat_id,),
        )
        rows = await cursor.fetchall()
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
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO audit_logs
            (chat_id, actor_id, action, target_id, old_value, new_value)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (chat_id, actor_id, action, target_id, old_value, new_value),
        )
        await db.commit()


# ============================================================
# ПРОВЕРКА ПРАВА — ТОЧКА ВХОДА ДЛЯ permissions.py
# ============================================================

async def admin_type_has_permission(admin_type_name: str, permission_code: str) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT 1
            FROM admin_type_permissions
            JOIN admin_types ON admin_types.id = admin_type_permissions.admin_type_id
            JOIN permissions ON permissions.id = admin_type_permissions.permission_id
            WHERE admin_types.name = ?
              AND permissions.code = ?
              AND admin_types.active = 1
            LIMIT 1
            """,
            (admin_type_name, permission_code),
        )
        row = await cursor.fetchone()
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

    if not effective_type:
        return False

    return await admin_type_has_permission(effective_type, permission)