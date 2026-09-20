import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} is not configured. Copy .env.example to .env "
            f"and set the required value."
        )
    return value


def _as_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    database_ssl: bool
    telegram_api_id: int
    telegram_api_hash: str
    telethon_session_string: str
    destructive_commands_enabled: bool


def load_settings() -> Settings:
    try:
        api_id = int(_required("TELEGRAM_API_ID"))
    except ValueError as exc:
        raise RuntimeError("TELEGRAM_API_ID must be an integer.") from exc

    return Settings(
        bot_token=_required("BOT_TOKEN"),
        database_url=_required("DATABASE_URL"),
        database_ssl=_as_bool("DATABASE_SSL", True),
        telegram_api_id=api_id,
        telegram_api_hash=_required("TELEGRAM_API_HASH"),
        telethon_session_string=_required("TELETHON_SESSION_STRING"),
        destructive_commands_enabled=_as_bool(
            "ENABLE_DESTRUCTIVE_COMMANDS", False
        ),
    )


settings = load_settings()
