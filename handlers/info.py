from aiogram import Router, types, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import MINIAPP_BASE_URL
from database.permissions import can_view_profile

router = Router()


WELCOME_TEXT = (
    "<b>СЕРВИТОР ХАОСА</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "Машинный дух пробуждён.\n"
    "Я слежу за порядком в этом Чате "
    "по воле тех, кто наделён Порчей власти.\n\n"
    "Флуд и хаос без спроса — не потерпим "
    "(остальной Хаос — сколько угодно).\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Список ритуалов — <code>/commands</code>"
)


COMMANDS_TEXT = (
    "<b>СПИСОК КОМАНД</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Модерация</b> (только для админов)\n"
    "<code>/ban</code> — ответом на сообщение, изгнать в Варп\n"
    "<code>/unban</code> — вернуть душу из Варпа (reply или ID)\n"
    "<code>/mute [минуты]</code> — сковать голос Порчей\n"
    "<code>/unmute</code> — снять Порчу с голоса\n\n"
    "<b>Информация</b>\n"
    "<code>/stats</code> — известно боту участников чата (админы)\n"
    "<code>/commands</code> — этот список\n"
    "━━━━━━━━━━━━━━━━━━━━"
)


@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject, bot: Bot):
    args = command.args or ""

    # Переход из группы по кнопке "Открыть панель управления"
    # (см. handlers/member_card.py) — формат аргумента: panel_<chat_id>
    if args.startswith("panel_"):
        return await handle_panel_deeplink(message, bot, args)

    await message.answer(WELCOME_TEXT)


async def handle_panel_deeplink(message: types.Message, bot: Bot, args: str):
    chat_id_raw = args[len("panel_"):]

    if not chat_id_raw.lstrip("-").isdigit():
        return await message.answer(
            "Не удалось разобрать ссылку на панель управления. "
            "Попробуй нажать кнопку в чате клана заново."
        )

    chat_id = int(chat_id_raw)
    user_id = message.from_user.id

    # Проверяем, что пользователь реально состоит в этом чате
    # и имеет право хотя бы на просмотр карточек — иначе кто угодно
    # мог бы подставить чужой chat_id в ссылку.
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception:
        return await message.answer(
            "Не удалось проверить твоё членство в этом чате. "
            "Попробуй нажать кнопку в чате клана заново."
        )

    if member.status in {"left", "kicked"}:
        return await message.answer("Ты не состоишь в этом чате.")

    if not await can_view_profile(bot, chat_id, user_id):
        return await message.answer("Недостаточно Порчи в твоей крови для этого ритуала.")

    if not MINIAPP_BASE_URL:
        return await message.answer(
            "Панель управления ещё не подключена (не задан MINIAPP_BASE_URL "
            "в .env бота)."
        )

    try:
        chat = await bot.get_chat(chat_id)
        chat_title = chat.title or "чат"
    except Exception:
        chat_title = "чат"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Открыть панель управления",
            web_app=WebAppInfo(url=f"{MINIAPP_BASE_URL}/?chat_id={chat_id}"),
        )
    ]])

    await message.answer(
        f"Панель управления для «{chat_title}» готова.\n\n"
        f"Нажми кнопку ниже, чтобы открыть её. "
        f"Она покажет только то, что доступно тебе по твоим правам в этом чате.",
        reply_markup=keyboard,
    )


@router.message(Command("commands"))
async def cmd_commands(message: types.Message):
    await message.answer(COMMANDS_TEXT)