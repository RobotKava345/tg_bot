import logging
from datetime import datetime, timedelta, timezone

from aiogram import Router, types, Bot
from aiogram.filters import Command, CommandObject
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramAPIError

from utils import is_admin

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("ban"))
async def cmd_ban(message: types.Message, bot: Bot):
    if not await is_admin(bot, message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно Порчи в твоей крови для этого ритуала.")

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("Укажи жертву для ритуала — ответь на её сообщение.")

    target = message.reply_to_message.from_user

    if target.is_bot:
        return await message.reply("Машинный дух не подвластен Хаосу. Ботов этой командой не изгнать.")

    if await is_admin(bot, message.chat.id, target.id):
        return await message.reply("Даже Хаос чтит иерархию. Повелителей культа трогать нельзя.")

    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target.id)
        await message.reply(
            f"<b>{target.full_name}</b> [<code>{target.id}</code>] низвергнут в Варп. "
            f"Да поглотит его Тьма."
        )
    except TelegramForbiddenError:
        await message.reply("Демонической мощи бота недостаточно, чтобы изгнать эту душу.")
    except TelegramBadRequest as e:
        await message.reply(f"Ритуал прерван: {e.message}")
    except TelegramAPIError as e:
        await message.reply(f"Порча эфира Варпа: {e}")
    except Exception as e:
        logger.exception("Неизвестная ошибка в /ban")
        await message.reply(f"Неведомая сила вмешалась в ритуал: {type(e).__name__}")


@router.message(Command("unban"))
async def cmd_unban(message: types.Message, command: CommandObject, bot: Bot):
    if not await is_admin(bot, message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно Порчи в твоей крови для этого ритуала.")

    user_id = None

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif command.args and command.args.strip().isdigit():
        user_id = int(command.args.strip())
    else:
        return await message.reply(
            "Укажи заблудшую душу — ответом на сообщение или её ID.\n"
            "Пример: <code>/unban 123456789</code>"
        )

    try:
        await bot.unban_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            only_if_banned=True
        )
        await message.reply(f"Душа <code>{user_id}</code> возвращена из Варпа.")
    except TelegramForbiddenError:
        await message.reply("Демонической мощи бота недостаточно для этого ритуала.")
    except TelegramBadRequest as e:
        await message.reply(f"Ритуал прерван: {e.message}")
    except Exception as e:
        logger.exception("Ошибка в /unban")
        await message.reply(f"Неведомая сила вмешалась: {type(e).__name__}")


@router.message(Command("mute"))
async def cmd_mute(message: types.Message, command: CommandObject, bot: Bot):
    if not await is_admin(bot, message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно Порчи в твоей крови для этого ритуала.")

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("Укажи еретика — ответь на его сообщение.")

    target = message.reply_to_message.from_user

    if await is_admin(bot, message.chat.id, target.id):
        return await message.reply("Голос Повелителя культа заглушить нельзя.")

    until_date = None
    time_text = "до конца времён"

    if command.args and command.args.strip().isdigit():
        minutes = int(command.args.strip())
        if minutes <= 0:
            return await message.reply("Укажи положительное количество минут.")
        until_date = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        time_text = f"на {minutes} мин."

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
            permissions=types.ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.reply(f"Голос <b>{target.full_name}</b> скован Порчей {time_text}.")
    except TelegramForbiddenError:
        await message.reply("Демонической мощи бота недостаточно, чтобы связать этот голос.")
    except TelegramBadRequest as e:
        await message.reply(f"Ритуал прерван: {e.message}")
    except Exception as e:
        logger.exception("Ошибка в /mute")
        await message.reply(f"Неведомая сила вмешалась: {type(e).__name__}")


@router.message(Command("unmute"))
async def cmd_unmute(message: types.Message, bot: Bot):
    if not await is_admin(bot, message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно Порчи в твоей крови для этого ритуала.")

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("Укажи еретика — ответь на его сообщение.")

    target = message.reply_to_message.from_user

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
            permissions=types.ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
        )
        await message.reply(f"С <b>{target.full_name}</b> снята Порча — голос восстановлен.")
    except TelegramForbiddenError:
        await message.reply("Демонической мощи бота недостаточно для этого ритуала.")
    except TelegramBadRequest as e:
        await message.reply(f"Ритуал прерван: {e.message}")
    except Exception as e:
        logger.exception("Ошибка в /unmute")
        await message.reply(f"Неведомая сила вмешалась: {type(e).__name__}")