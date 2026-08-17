import logging

from database.pool import get_pool

logger = logging.getLogger(__name__)


def _parse_rowcount(status: str) -> int:
    try:
        return int(status.split()[-1])
    except (ValueError, IndexError):
        return 0


# ============================================================
# CREATE
# ============================================================

async def create_role(
    chat_id: int,
    name: str,
    description: str | None = None,
) -> int | None:
    """
    Создаёт новую роль. Возвращает ID созданной роли,
    или None, если создать не удалось (например, роль
    с таким названием уже есть в этом чате).
    """
    name = name.strip()
    if not name:
        return None

    pool = get_pool()
    try:
        role_id = await pool.fetchval(
            """
            INSERT INTO roles (chat_id, name, description)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            chat_id, name, description,
        )
        logger.info("Создана роль '%s' (ID=%s, chat_id=%s)", name, role_id, chat_id)
        return role_id
    except Exception as e:
        logger.warning(
            "Не удалось создать роль '%s' в чате %s: %s",
            name, chat_id, e,
        )
        return None


# ============================================================
# GET ALL
# ============================================================

async def get_roles(chat_id: int) -> list[dict]:
    """Возвращает все активные роли чата."""
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT id, chat_id, name, description, active, created_at, updated_at
        FROM roles
        WHERE chat_id = $1 AND active = TRUE
        ORDER BY id ASC
        """,
        chat_id,
    )
    return [dict(row) for row in rows]


# ============================================================
# GET ALL INCLUDING INACTIVE
# ============================================================

async def get_all_roles(chat_id: int) -> list[dict]:
    """Возвращает все роли чата, включая отключённые."""
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT id, chat_id, name, description, active, created_at, updated_at
        FROM roles
        WHERE chat_id = $1
        ORDER BY id ASC
        """,
        chat_id,
    )
    return [dict(row) for row in rows]


# ============================================================
# GET BY ID
# ============================================================

async def get_role(chat_id: int, role_id: int) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, chat_id, name, description, active, created_at, updated_at
        FROM roles
        WHERE chat_id = $1 AND id = $2
        LIMIT 1
        """,
        chat_id, role_id,
    )
    return dict(row) if row else None


# ============================================================
# GET BY NAME
# ============================================================

async def get_role_by_name(chat_id: int, name: str) -> dict | None:
    name = name.strip()
    if not name:
        return None

    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, chat_id, name, description, active, created_at, updated_at
        FROM roles
        WHERE chat_id = $1 AND name = $2
        LIMIT 1
        """,
        chat_id, name,
    )
    return dict(row) if row else None


# ============================================================
# SEARCH
# ============================================================

async def search_roles(chat_id: int, query: str) -> list[dict]:
    query = query.strip()
    if not query:
        return await get_roles(chat_id)

    pattern = f"%{query}%"
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT id, chat_id, name, description, active, created_at, updated_at
        FROM roles
        WHERE chat_id = $1
          AND active = TRUE
          AND (name ILIKE $2 OR description ILIKE $2)
        ORDER BY id ASC
        """,
        chat_id, pattern,
    )
    return [dict(row) for row in rows]


# ============================================================
# UPDATE
# ============================================================

async def update_role(
    chat_id: int,
    role_id: int,
    name: str,
    description: str | None = None,
) -> bool:
    name = name.strip()
    if not name:
        return False

    pool = get_pool()
    try:
        status = await pool.execute(
            """
            UPDATE roles
            SET name = $1, description = $2, updated_at = CURRENT_TIMESTAMP
            WHERE chat_id = $3 AND id = $4
            """,
            name, description, chat_id, role_id,
        )
        updated = _parse_rowcount(status) > 0
        if updated:
            logger.info("Изменена роль ID=%s в чате %s", role_id, chat_id)
        return updated
    except Exception as e:
        logger.error("Ошибка изменения роли %s в чате %s: %s", role_id, chat_id, e)
        return False


# ============================================================
# UPDATE NAME
# ============================================================

async def update_role_name(chat_id: int, role_id: int, name: str) -> bool:
    name = name.strip()
    if not name:
        return False

    pool = get_pool()
    try:
        status = await pool.execute(
            """
            UPDATE roles
            SET name = $1, updated_at = CURRENT_TIMESTAMP
            WHERE chat_id = $2 AND id = $3
            """,
            name, chat_id, role_id,
        )
        return _parse_rowcount(status) > 0
    except Exception as e:
        logger.error("Ошибка изменения названия роли %s: %s", role_id, e)
        return False


# ============================================================
# UPDATE DESCRIPTION
# ============================================================

async def update_role_description(
    chat_id: int,
    role_id: int,
    description: str | None,
) -> bool:
    pool = get_pool()
    try:
        status = await pool.execute(
            """
            UPDATE roles
            SET description = $1, updated_at = CURRENT_TIMESTAMP
            WHERE chat_id = $2 AND id = $3
            """,
            description, chat_id, role_id,
        )
        return _parse_rowcount(status) > 0
    except Exception as e:
        logger.error("Ошибка изменения описания роли %s: %s", role_id, e)
        return False


# ============================================================
# ENABLE / DISABLE
# ============================================================

async def set_role_active(chat_id: int, role_id: int, active: bool) -> bool:
    """
    Включает/отключает роль — предпочтительнее физического удаления,
    если роль уже используется участниками.
    """
    pool = get_pool()
    status = await pool.execute(
        """
        UPDATE roles
        SET active = $1, updated_at = CURRENT_TIMESTAMP
        WHERE chat_id = $2 AND id = $3
        """,
        active, chat_id, role_id,
    )
    return _parse_rowcount(status) > 0


# ============================================================
# EXISTS
# ============================================================

async def role_exists(chat_id: int, role_id: int) -> bool:
    pool = get_pool()
    row = await pool.fetchval(
        """
        SELECT 1 FROM roles
        WHERE chat_id = $1 AND id = $2
        LIMIT 1
        """,
        chat_id, role_id,
    )
    return row is not None


# ============================================================
# COUNT
# ============================================================

async def count_roles(chat_id: int) -> int:
    pool = get_pool()
    row = await pool.fetchval(
        "SELECT COUNT(*) FROM roles WHERE chat_id = $1 AND active = TRUE",
        chat_id,
    )
    return row or 0


# ============================================================
# COUNT USAGE
# ============================================================

async def count_role_usage(chat_id: int, role_id: int) -> int:
    pool = get_pool()
    row = await pool.fetchval(
        """
        SELECT COUNT(*) FROM member_profiles
        WHERE chat_id = $1 AND role_id = $2
        """,
        chat_id, role_id,
    )
    return row or 0


# ============================================================
# DELETE
# ============================================================

async def delete_role(chat_id: int, role_id: int) -> bool:
    """
    Физически удаляет роль. Перед удалением проверяет,
    не используется ли она в карточках участников.
    """
    usage = await count_role_usage(chat_id, role_id)

    if usage > 0:
        logger.warning(
            "Нельзя удалить роль ID=%s в чате %s: используется в %s карточках",
            role_id, chat_id, usage,
        )
        return False

    pool = get_pool()
    status = await pool.execute(
        """
        DELETE FROM roles
        WHERE chat_id = $1 AND id = $2
        """,
        chat_id, role_id,
    )
    deleted = _parse_rowcount(status) > 0
    if deleted:
        logger.info("Удалена роль ID=%s из чата %s", role_id, chat_id)
    return deleted