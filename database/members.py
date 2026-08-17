
import logging
 
from database.pool import get_pool
 
logger = logging.getLogger(__name__)
 
 
# ============================================================
# CREATE / GET
# ============================================================
 
async def create_member_profile(
    chat_id: int,
    user_id: int,
    display_name: str | None = None,
):
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO member_profiles (chat_id, user_id, display_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (chat_id, user_id) DO NOTHING
        """,
        chat_id, user_id, display_name,
    )
 
 
async def get_member_profile(chat_id: int, user_id: int):
    """
    Возвращает карточку участника в виде кортежа:
 
    (
        chat_id, user_id, display_name, role_id, rank_id,
        legion_id, status_id, reputation, created_at, updated_at
    )
 
    Если карточки нет - None. Формат сохранён совместимым с тем,
    что использует handlers/member_card.py (индексация по позиции).
    """
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT
            chat_id, user_id, display_name, role_id, rank_id,
            legion_id, status_id, reputation, created_at, updated_at
        FROM member_profiles
        WHERE chat_id = $1 AND user_id = $2
        """,
        chat_id, user_id,
    )
    if row is None:
        return None
    return tuple(row)
 
 
async def get_member_profiles(chat_id: int):
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT
            chat_id, user_id, display_name, role_id, rank_id,
            legion_id, status_id, reputation, created_at, updated_at
        FROM member_profiles
        WHERE chat_id = $1
        ORDER BY user_id
        """,
        chat_id,
    )
    return [tuple(row) for row in rows]
 
 
# ============================================================
# NAME
# ============================================================
 
async def update_member_name(chat_id: int, user_id: int, display_name: str):
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO member_profiles (chat_id, user_id, display_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (chat_id, user_id) DO UPDATE SET
            display_name = EXCLUDED.display_name,
            updated_at = CURRENT_TIMESTAMP
        """,
        chat_id, user_id, display_name,
    )
 
 
# ============================================================
# ROLE
# ============================================================
 
async def update_member_role(chat_id: int, user_id: int, role_id: int | None):
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO member_profiles (chat_id, user_id, role_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (chat_id, user_id) DO UPDATE SET
            role_id = EXCLUDED.role_id,
            updated_at = CURRENT_TIMESTAMP
        """,
        chat_id, user_id, role_id,
    )
 
 
# ============================================================
# RANK
# ============================================================
 
async def update_member_rank(chat_id: int, user_id: int, rank_id: int | None):
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO member_profiles (chat_id, user_id, rank_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (chat_id, user_id) DO UPDATE SET
            rank_id = EXCLUDED.rank_id,
            updated_at = CURRENT_TIMESTAMP
        """,
        chat_id, user_id, rank_id,
    )
 
 
# ============================================================
# LEGION
# ============================================================
 
async def update_member_legion(chat_id: int, user_id: int, legion_id: int | None):
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO member_profiles (chat_id, user_id, legion_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (chat_id, user_id) DO UPDATE SET
            legion_id = EXCLUDED.legion_id,
            updated_at = CURRENT_TIMESTAMP
        """,
        chat_id, user_id, legion_id,
    )
 
 
# ============================================================
# STATUS
# ============================================================
 
async def update_member_status(chat_id: int, user_id: int, status_id: int | None):
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO member_profiles (chat_id, user_id, status_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (chat_id, user_id) DO UPDATE SET
            status_id = EXCLUDED.status_id,
            updated_at = CURRENT_TIMESTAMP
        """,
        chat_id, user_id, status_id,
    )
 
 
# ============================================================
# REPUTATION
# ============================================================
 
async def update_member_reputation(chat_id: int, user_id: int, reputation: int):
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO member_profiles (chat_id, user_id, reputation)
        VALUES ($1, $2, $3)
        ON CONFLICT (chat_id, user_id) DO UPDATE SET
            reputation = EXCLUDED.reputation,
            updated_at = CURRENT_TIMESTAMP
        """,
        chat_id, user_id, reputation,
    )
 
 
async def change_member_reputation(chat_id: int, user_id: int, amount: int):
    """
    Изменяет репутацию относительно текущего значения (+5 / -10).
    """
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO member_profiles (chat_id, user_id, reputation)
        VALUES ($1, $2, $3)
        ON CONFLICT (chat_id, user_id) DO UPDATE SET
            reputation = member_profiles.reputation + $4,
            updated_at = CURRENT_TIMESTAMP
        """,
        chat_id, user_id, amount, amount,
    )
 
 
# ============================================================
# FULL UPDATE
# ============================================================
 
async def update_member_profile(
    chat_id: int,
    user_id: int,
    display_name: str | None = None,
    role_id: int | None = None,
    rank_id: int | None = None,
    legion_id: int | None = None,
    status_id: int | None = None,
    reputation: int = 0,
):
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO member_profiles
        (chat_id, user_id, display_name, role_id, rank_id, legion_id, status_id, reputation)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (chat_id, user_id) DO UPDATE SET
            display_name = EXCLUDED.display_name,
            role_id = EXCLUDED.role_id,
            rank_id = EXCLUDED.rank_id,
            legion_id = EXCLUDED.legion_id,
            status_id = EXCLUDED.status_id,
            reputation = EXCLUDED.reputation,
            updated_at = CURRENT_TIMESTAMP
        """,
        chat_id, user_id, display_name, role_id, rank_id, legion_id, status_id, reputation,
    )
 
 
# ============================================================
# DELETE
# ============================================================
 
async def delete_member_profile(chat_id: int, user_id: int):
    pool = get_pool()
    await pool.execute(
        """
        DELETE FROM member_profiles
        WHERE chat_id = $1 AND user_id = $2
        """,
        chat_id, user_id,
    )
 
 
# ============================================================
# EXISTENCE
# ============================================================
 
async def member_profile_exists(chat_id: int, user_id: int) -> bool:
    pool = get_pool()
    row = await pool.fetchval(
        """
        SELECT 1 FROM member_profiles
        WHERE chat_id = $1 AND user_id = $2
        LIMIT 1
        """,
        chat_id, user_id,
    )
    return row is not None
 
 
# ============================================================
# ENSURE PROFILE
# ============================================================
 
async def ensure_member_profile(
    chat_id: int,
    user_id: int,
    display_name: str | None = None,
):
    await create_member_profile(
        chat_id=chat_id,
        user_id=user_id,
        display_name=display_name,
    )
 