import logging

from database.pool import get_pool

logger = logging.getLogger(__name__)

# Таблица statuses создаётся в database/db.py (init_db()).
# Отдельной init-функции здесь больше нет (см. историю чата —
# раньше была своя init_statuses_table() с устаревшей схемой,
# удалена как дублирующая и потенциально опасная).


def _parse_rowcount(status: str) -> int:
    try:
        return int(status.split()[-1])
    except (ValueError, IndexError):
        return 0


# ============================================================
# Создание статуса
# ============================================================

async def create_status(
    chat_id: int,
    name: str,
    description: str | None = None,
) -> int | None:
    name = name.strip()
    if not name:
        return None

    pool = get_pool()
    try:
        return await pool.fetchval(
            """
            INSERT INTO statuses (chat_id, name, description)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            chat_id, name, description,
        )
    except Exception as e:
        # UniqueViolationError входит в это же except, как и раньше
        # ловился aiosqlite.IntegrityError.
        logger.warning(
            "Не удалось создать статус '%s' в чате %s: %s",
            name, chat_id, e,
        )
        return None


# ============================================================
# Получение статуса
# ============================================================

async def get_status(chat_id: int, status_id: int) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, chat_id, name, description, created_at
        FROM statuses
        WHERE chat_id = $1 AND id = $2
        """,
        chat_id, status_id,
    )
    return dict(row) if row else None


# ============================================================
# Получение всех статусов
# ============================================================

async def get_statuses(chat_id: int) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT id, chat_id, name, description, created_at
        FROM statuses
        WHERE chat_id = $1
        ORDER BY id ASC
        """,
        chat_id,
    )
    return [dict(row) for row in rows]


# ============================================================
# Поиск статусов
# ============================================================

async def search_statuses(chat_id: int, query: str) -> list[dict]:
    query = query.strip()
    if not query:
        return await get_statuses(chat_id)

    pattern = f"%{query}%"
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT id, chat_id, name, description, created_at
        FROM statuses
        WHERE chat_id = $1
          AND (name ILIKE $2 OR description ILIKE $2)
        ORDER BY id ASC
        """,
        chat_id, pattern,
    )
    return [dict(row) for row in rows]


# ============================================================
# Изменение статуса
# ============================================================

async def update_status(
    chat_id: int,
    status_id: int,
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
            UPDATE statuses
            SET name = $1, description = $2
            WHERE chat_id = $3 AND id = $4
            """,
            name, description, chat_id, status_id,
        )
        return _parse_rowcount(status) > 0
    except Exception as e:
        logger.warning(
            "Не удалось изменить статус %s в чате %s: %s",
            status_id, chat_id, e,
        )
        return False


# ============================================================
# Удаление статуса
# ============================================================

async def delete_status(chat_id: int, status_id: int) -> bool:
    pool = get_pool()
    try:
        status = await pool.execute(
            """
            DELETE FROM statuses
            WHERE chat_id = $1 AND id = $2
            """,
            chat_id, status_id,
        )
        return _parse_rowcount(status) > 0
    except Exception as e:
        logger.error(
            "Ошибка удаления статуса %s в чате %s: %s",
            status_id, chat_id, e,
        )
        return False


# ============================================================
# Проверка существования
# ============================================================

async def status_exists(chat_id: int, status_id: int) -> bool:
    pool = get_pool()
    row = await pool.fetchval(
        """
        SELECT 1 FROM statuses
        WHERE chat_id = $1 AND id = $2
        LIMIT 1
        """,
        chat_id, status_id,
    )
    return row is not None


# ============================================================
# Проверка использования статуса
# ============================================================

async def count_status_usage(chat_id: int, status_id: int) -> int:
    pool = get_pool()
    row = await pool.fetchval(
        """
        SELECT COUNT(*) FROM member_profiles
        WHERE chat_id = $1 AND status_id = $2
        """,
        chat_id, status_id,
    )
    return row or 0