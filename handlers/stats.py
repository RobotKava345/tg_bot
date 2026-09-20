from aiogram import Bot, Router, types
from aiogram.filters import Command

from database.db import count_seen_users
from mtproto import sync_chat_members
from utils import is_admin

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: types.Message, bot: Bot) -> None:
    tracked_count = await count_seen_users(message.chat.id)

    try:
        real_count = await bot.get_chat_member_count(message.chat.id)
    except Exception:
        real_count = None

    lines: list[str] = []

    if real_count is not None:
        lines.append(f"Telegram members: <b>{real_count}</b>")

    lines.append(f"Tracked in PostgreSQL: <b>{tracked_count}</b>")

    if real_count is not None and real_count > tracked_count:
        lines.append(
            "\n<i>The database is incomplete. An administrator can run /sync.</i>"
        )

    await message.reply("\n".join(lines))


@router.message(Command("sync"))
async def cmd_sync(message: types.Message, bot: Bot) -> None:
    if not message.from_user:
        return

    if not await is_admin(bot, message.chat.id, message.from_user.id):
        return await message.reply("This command is available to chat admins only.")

    status = await message.reply("Synchronizing members through Telethon...")

    try:
        count = await sync_chat_members(message.chat.id)
    except Exception as exc:
        return await status.edit_text(
            f"Synchronization failed: <code>{type(exc).__name__}</code>"
        )

    await status.edit_text(
        f"Synchronization complete. Processed: <b>{count}</b>"
    )
