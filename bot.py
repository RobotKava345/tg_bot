import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.enums import ChatMemberStatus, ParseMode, ChatType
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import (
    TelegramRetryAfter,
    TelegramForbiddenError,
    TelegramBadRequest,
    TelegramAPIError
)
import aiosqlite

TOKEN = "8806434479:AAGIm6d7IhyBK9bCpxb6GFByp9ZM8ggQ_ow"  # <-- перегенерируй токен через BotFather, старый уже засветился
DB_NAME = "admin_bot.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


# ====================== База данных ======================

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS seen_users (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        await db.commit()


async def add_user(chat_id: int, user_id: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT OR IGNORE INTO seen_users (chat_id, user_id) VALUES (?, ?)",
                (chat_id, user_id)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Ошибка записи пользователя {user_id} в чат {chat_id}: {e}")


async def get_seen_users(chat_id: int) -> list[int]:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT user_id FROM seen_users WHERE chat_id = ?",
            (chat_id,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def count_seen_users(chat_id: int) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM seen_users WHERE chat_id = ?",
            (chat_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


# ====================== Вспомогательные функции ======================

async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in {
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR
        }
    except TelegramAPIError as e:
        logger.warning(
            "Не удалось проверить права user_id=%s в chat_id=%s: %s",
            user_id, chat_id, e
        )
        return False
    except Exception as e:
        logger.error(
            "Неожиданная ошибка при проверке прав user_id=%s в chat_id=%s: %s",
            user_id, chat_id, e
        )
        return False


async def get_admin_ids(chat_id: int) -> set[int]:
    try:
        admins = await bot.get_chat_administrators(chat_id)
        return {admin.user.id for admin in admins}
    except Exception as e:
        logger.warning(f"Не удалось получить список админов чата {chat_id}: {e}")
        return set()


# ====================== Отслеживание пользователей ======================
# ВАЖНО: фильтр ~F.text.startswith("/") исключает команды ещё на уровне
# регистрации хендлера, иначе aiogram считает апдейт "обработанным" здесь
# и не передаёт его дальше к обработчикам команд (/ban, /ext и т.д.)

@dp.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    ~F.text.startswith("/")
)
async def track_messages(message: types.Message):
    if not message.from_user or message.from_user.is_bot:
        return

    await add_user(message.chat.id, message.from_user.id)


@dp.chat_member()
async def track_joins(event: types.ChatMemberUpdated):
    new_member = event.new_chat_member
    if new_member.status in {"member", "restricted"} and not new_member.user.is_bot:
        await add_user(event.chat.id, new_member.user.id)


# ====================== Команды модерации ======================

@dp.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно прав.")

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("Ответь на сообщение пользователя, которого нужно забанить.")

    target = message.reply_to_message.from_user

    if target.is_bot:
        return await message.reply("Нельзя банить ботов этой командой.")

    if await is_admin(message.chat.id, target.id):
        return await message.reply("Нельзя банить администратора.")

    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target.id)
        await message.reply(f"Пользователь <b>{target.full_name}</b> [<code>{target.id}</code>] забанен.")
    except TelegramForbiddenError:
        await message.reply("У бота недостаточно прав для бана этого пользователя.")
    except TelegramBadRequest as e:
        await message.reply(f"Не удалось забанить: {e.message}")
    except TelegramAPIError as e:
        await message.reply(f"Ошибка Telegram API: {e}")
    except Exception as e:
        logger.exception("Неизвестная ошибка в /ban")
        await message.reply(f"Неизвестная ошибка: {type(e).__name__}")


@dp.message(Command("unban"))
async def cmd_unban(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно прав.")

    user_id = None

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif command.args and command.args.strip().isdigit():
        user_id = int(command.args.strip())
    else:
        return await message.reply(
            "Ответь на сообщение или укажи ID пользователя.\n"
            "Пример: <code>/unban 123456789</code>"
        )

    try:
        await bot.unban_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            only_if_banned=True
        )
        await message.reply(f"Пользователь <code>{user_id}</code> разбанен.")
    except TelegramForbiddenError:
        await message.reply("У бота недостаточно прав.")
    except TelegramBadRequest as e:
        await message.reply(f"Не удалось разбанить: {e.message}")
    except Exception as e:
        logger.exception("Ошибка в /unban")
        await message.reply(f"Ошибка: {type(e).__name__}")


@dp.message(Command("mute"))
async def cmd_mute(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно прав.")

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("Ответь на сообщение пользователя.")

    target = message.reply_to_message.from_user

    if await is_admin(message.chat.id, target.id):
        return await message.reply("Нельзя мутить администратора.")

    until_date = None
    time_text = "навсегда"

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
        await message.reply(f"Пользователь <b>{target.full_name}</b> замучен {time_text}.")
    except TelegramForbiddenError:
        await message.reply("У бота недостаточно прав для ограничения этого пользователя.")
    except TelegramBadRequest as e:
        await message.reply(f"Ошибка: {e.message}")
    except Exception as e:
        logger.exception("Ошибка в /mute")
        await message.reply(f"Ошибка: {type(e).__name__}")


@dp.message(Command("unmute"))
async def cmd_unmute(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно прав.")

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("Ответь на сообщение пользователя.")

    target = message.reply_to_message.from_user

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
            # Актуальные (не устаревшие) поля ChatPermissions вместо
            # снятого can_send_media_messages / can_send_other_messages как одного флага
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
        await message.reply(f"С пользователя <b>{target.full_name}</b> снят мут.")
    except TelegramForbiddenError:
        await message.reply("У бота недостаточно прав.")
    except TelegramBadRequest as e:
        await message.reply(f"Ошибка: {e.message}")
    except Exception as e:
        logger.exception("Ошибка в /unmute")
        await message.reply(f"Ошибка: {type(e).__name__}")


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно прав.")

    count = await count_seen_users(message.chat.id)
    await message.reply(f"В базе по этому чату зафиксировано: <b>{count}</b> пользователей.")


@dp.message(Command("ext"))
async def cmd_ext(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно прав.")

    # Защита от случайного массового бана: требуем явное подтверждение
    if not command.args or command.args.strip().lower() != "confirm":
        return await message.reply(
            "⚠️ ПРОИЗВОДИТСЯ ПРОЦЕДУРА ЭКСТЕРМИНАТУСА ЧАТА! ХАОС СОСАТЬ! АВЕ ИМП! АВЕ ИМПЕРАТОР! ГИДРА ДОМИНАТУС! \n"
            " ЧТОБЫ ОТКРЫТЬ ОГОНЬ! — напиши: <code>/ext confirm</code>"
        )

    chat_id = message.chat.id
    status_msg = await message.reply("Начинаю массовый бан известных пользователей...")

    admin_ids = await get_admin_ids(chat_id)
    try:
        me = await bot.get_me()
        admin_ids.add(me.id)
    except Exception:
        pass

    users = await get_seen_users(chat_id)
    total = len(users)
    banned = 0
    skipped = 0
    errors = 0

    for user_id in users:
        if user_id in admin_ids:
            skipped += 1
            continue

        success = False
        attempts = 0

        while attempts < 2 and not success:
            try:
                await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                banned += 1
                success = True
            except TelegramRetryAfter as e:
                wait = e.retry_after
                logger.warning(f"FloodWait {wait}s на user_id={user_id}")
                await asyncio.sleep(wait)
                attempts += 1
            except (TelegramForbiddenError, TelegramBadRequest):
                errors += 1
                break
            except Exception as e:
                logger.error(f"Ошибка бана {user_id}: {e}")
                errors += 1
                break

        if not success and attempts >= 2:
            errors += 1

        if success:
            await asyncio.sleep(0.25)

    text = (
        f"Массовый бан завершён.\n\n"
        f"Всего в базе: <b>{total}</b>\n"
        f"Забанено: <b>{banned}</b>\n"
        f"Пропущено (админы): <b>{skipped}</b>\n"
        f"Ошибок: <b>{errors}</b>"
    )

    try:
        await status_msg.edit_text(text)
    except Exception:
        await message.answer(text)


# ====================== Запуск ======================

async def main():
    await init_db()
    logger.info("Админ-бот запущен")
    await dp.start_polling(
        bot,
        allowed_updates=["message", "chat_member"]
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")