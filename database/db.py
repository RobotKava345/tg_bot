import logging

from database.pool import get_pool

logger = logging.getLogger(__name__)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

async def init_db():
    """
    Создаёт недостающие таблицы. Не удаляет существующие данные.

    ВАЖНО: перед вызовом должен быть инициализирован пул
    (database.pool.init_pool()).
    """

    pool = get_pool()

    async with pool.acquire() as db:
        # ====================================================
        # SEEN USERS
        # ====================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS seen_users (
                chat_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                first_seen TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, user_id)
            )
        """)

        # ====================================================
        # MEMBER PROFILES
        # ====================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS member_profiles (
                chat_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                display_name TEXT,
                role_id INTEGER,
                rank_id INTEGER,
                legion_id INTEGER,
                status_id INTEGER,
                reputation INTEGER DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, user_id)
            )
        """)

        # ====================================================
        # ROLES (кастомные "лорные" роли/титулы)
        # ====================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chat_id, name)
            )
        """)

        # ====================================================
        # LEGIONS
        # ====================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS legions (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                name TEXT NOT NULL,
                primarch_id BIGINT,
                description TEXT,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ====================================================
        # RANKS
        # ====================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ranks (
                id SERIAL PRIMARY KEY,
                legion_id INTEGER NOT NULL REFERENCES legions(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT,
                points_required INTEGER DEFAULT 0,
                position INTEGER DEFAULT 0,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ====================================================
        # STATUSES
        # ====================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS statuses (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chat_id, name)
            )
        """)

        # ====================================================
        # ADMIN TYPES
        # ====================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_types (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ====================================================
        # CHAT ADMINS
        # ====================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_admins (
                chat_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                admin_type_id INTEGER NOT NULL REFERENCES admin_types(id) ON DELETE RESTRICT,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                assigned_by BIGINT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, user_id)
            )
        """)

        # ====================================================
        # PERMISSIONS
        # ====================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id SERIAL PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ====================================================
        # ADMIN TYPE PERMISSIONS
        # ====================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_type_permissions (
                admin_type_id INTEGER NOT NULL REFERENCES admin_types(id) ON DELETE CASCADE,
                permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
                PRIMARY KEY (admin_type_id, permission_id)
            )
        """)

        # ====================================================
        # AUDIT LOG
        # ====================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                actor_id BIGINT NOT NULL,
                action TEXT NOT NULL,
                target_id BIGINT,
                old_value TEXT,
                new_value TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ====================================================
        # INDEXES
        # ====================================================
        await db.execute("CREATE INDEX IF NOT EXISTS idx_seen_users_chat ON seen_users(chat_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_member_profiles_chat ON member_profiles(chat_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_member_profiles_user ON member_profiles(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_roles_chat ON roles(chat_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_legions_chat ON legions(chat_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_ranks_legion ON ranks(legion_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_statuses_chat ON statuses(chat_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_admins_chat ON chat_admins(chat_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_chat ON audit_logs(chat_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs(actor_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_target ON audit_logs(target_id)")

    logger.info("Структура базы данных инициализирована (Postgres)")


# ============================================================
# SEEN USERS
# ============================================================

async def add_user(chat_id: int, user_id: int):
    pool = get_pool()
    try:
        await pool.execute(
            """
            INSERT INTO seen_users (chat_id, user_id)
            VALUES ($1, $2)
            ON CONFLICT (chat_id, user_id) DO NOTHING
            """,
            chat_id, user_id,
        )
    except Exception as e:
        logger.error(f"Ошибка записи пользователя {user_id} в чат {chat_id}: {e}")


async def get_seen_users(chat_id: int) -> list[int]:
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT user_id FROM seen_users WHERE chat_id = $1",
        chat_id,
    )
    return [row["user_id"] for row in rows]


async def count_seen_users(chat_id: int) -> int:
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT COUNT(*) AS cnt FROM seen_users WHERE chat_id = $1",
        chat_id,
    )
    return row["cnt"] if row else 0