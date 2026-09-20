import asyncio
import logging

from aiogram import Bot, Router, types
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from aiogram.filters import Command, CommandObject

from config import settings
from database.db import get_seen_users
from forum_topics import delete_all_topics_except
from utils import AdaptiveThrottle, get_admin_ids, is_admin

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("fire_exterminatus"))
async def cmd_ext(
    message: types.Message,
    command: CommandObject,
    bot: Bot,
) -> None:
    if not settings.destructive_commands_enabled:
        return await message.reply(
            "Destructive commands are disabled. "
            "Set ENABLE_DESTRUCTIVE_COMMANDS=true only if you intentionally need them."
        )

    if not message.from_user:
        return

    if not await is_admin(bot, message.chat.id, message.from_user.id):
        return await message.reply("This command is available to chat admins only.")

    if not command.args or command.args.strip().lower() != "confirm":
        return await message.reply(
            "<b>Destructive cleanup</b>\n\n"
            "This will ban every tracked non-admin member and delete "
            "forum topics except General and the current topic.\n\n"
            "Run <code>/fire_exterminatus confirm</code> to continue."
        )

    chat_id = message.chat.id
    keep_topic_id = message.message_thread_id
    status = await message.reply("Cleanup started...")

    admin_ids = await get_admin_ids(bot, chat_id)
    me = await bot.get_me()
    admin_ids.add(me.id)
    admin_ids.add(message.from_user.id)

    users = await get_seen_users(chat_id)

    banned = 0
    skipped = 0
    errors = 0
    throttle = AdaptiveThrottle()

    for user_id in users:
        if user_id in admin_ids:
            skipped += 1
            continue

        try:
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            banned += 1
            throttle.on_success()
            await throttle.wait()

        except TelegramRetryAfter as exc:
            throttle.on_flood_wait(exc.retry_after)
            await asyncio.sleep(exc.retry_after)

            try:
                await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                banned += 1
            except Exception:
                errors += 1
                logger.exception(
                    "Second ban attempt failed for user %s",
                    user_id,
                )

        except (TelegramForbiddenError, TelegramBadRequest):
            errors += 1
            logger.exception("Could not ban user %s", user_id)

    try:
        topics_total, topics_deleted, topic_errors = (
            await delete_all_topics_except(
                bot=bot,
                chat_id=chat_id,
                keep_topic_id=keep_topic_id,
            )
        )
    except Exception:
        topics_total = 0
        topics_deleted = 0
        topic_errors = 1
        logger.exception("Forum topic cleanup failed")

    await status.edit_text(
        "<b>Cleanup complete</b>\n\n"
        f"Tracked users: <b>{len(users)}</b>\n"
        f"Banned: <b>{banned}</b>\n"
        f"Skipped admins: <b>{skipped}</b>\n"
        f"Ban errors: <b>{errors}</b>\n"
        f"Topics found: <b>{topics_total}</b>\n"
        f"Topics deleted: <b>{topics_deleted}</b>\n"
        f"Topic errors: <b>{topic_errors}</b>"
    )
