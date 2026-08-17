from aiogram import Router, types, Bot, F
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils import NO_RIGHTS_TEXT
from database.members import (
    ensure_member_profile,
    get_member_profile,
    update_member_name,
    update_member_legion,
    update_member_rank,
    update_member_status,
    change_member_reputation,
)
from database.legions import get_legion, get_legion_by_name
from database.ranks import get_rank, get_rank_by_name
from database.statuses import get_statuses, get_status
from database.roles import get_role as get_custom_role
from database.permissions import (
    can_view_profile,
    can_edit_name,
    can_edit_legion,
    can_edit_rank,
    can_edit_status,
    can_edit_reputation,
)

router = Router()


class ProfileStates(StatesGroup):
    waiting_for_name = State()


# ============================================================
# ФОРМАТИРОВАНИЕ КАРТОЧКИ
# ============================================================

async def format_profile_text(chat_id: int, target: types.User, profile_row) -> str:
    if profile_row is None:
        display_name = target.full_name
        role_id = rank_id = legion_id = status_id = None
        reputation = 0
    else:
        (
            _chat_id, _user_id, display_name,
            role_id, rank_id, legion_id, status_id,
            reputation, _created_at, _updated_at,
        ) = profile_row
        display_name = display_name or target.full_name

    legion_name = "—"
    if legion_id:
        legion = await get_legion(legion_id, chat_id)
        if legion:
            legion_name = legion["name"]

    rank_name = "—"
    if rank_id and legion_id:
        rank = await get_rank(rank_id, legion_id)
        if rank:
            rank_name = rank["name"]

    status_name = "—"
    if status_id:
        status = await get_status(chat_id, status_id)
        if status:
            status_name = status["name"]

    role_name = "—"
    if role_id:
        role = await get_custom_role(chat_id, role_id)
        if role:
            role_name = role["name"]

    return (
        "🗂 <b>КАРТОЧКА УЧАСТНИКА</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Имя: <b>{display_name}</b>\n"
        f"ID: <code>{target.id}</code>\n"
        f"Легион: {legion_name}\n"
        f"Звание: {rank_name}\n"
        f"Роль: {role_name}\n"
        f"Статус: {status_name}\n"
        f"Очки: <b>{reputation}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )


def build_profile_keyboard(target_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Изменить имя", callback_data=f"pcard:name:{target_id}"),
        ],
        [
            InlineKeyboardButton(text="➖ Очки", callback_data=f"pcard:repdown:{target_id}"),
            InlineKeyboardButton(text="➕ Очки", callback_data=f"pcard:repup:{target_id}"),
        ],
        [
            InlineKeyboardButton(text="🛠 Открыть панель управления", callback_data=f"pcard:panel:{target_id}"),
        ],
    ])


def _resolve_target(message: types.Message) -> tuple[types.User, bool]:
    """Возвращает (target_user, viewing_self)."""
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
        return target, target.id == message.from_user.id
    return message.from_user, True


# ============================================================
# /profile — просмотр карточки
# ============================================================

@router.message(Command("profile"))
async def cmd_profile(message: types.Message, bot: Bot):
    target, viewing_self = _resolve_target(message)

    if not viewing_self:
        if not await can_view_profile(bot, message.chat.id, message.from_user.id):
            return await message.reply(NO_RIGHTS_TEXT)

    await ensure_member_profile(message.chat.id, target.id, target.full_name)
    profile = await get_member_profile(message.chat.id, target.id)

    text = await format_profile_text(message.chat.id, target, profile)
    await message.reply(text, reply_markup=build_profile_keyboard(target.id))


# ============================================================
# CALLBACK: кнопки карточки
# ============================================================

@router.callback_query(F.data.startswith("pcard:"))
async def cb_profile_card(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    parts = callback.data.split(":")
    # pcard:<action>:<target_id>
    action = parts[1]
    target_id = int(parts[-1])

    chat_id = callback.message.chat.id
    clicker_id = callback.from_user.id

    # ------------------------------------------------------
    # Изменить имя
    # ------------------------------------------------------
    if action == "name":
        if not await can_edit_name(bot, chat_id, clicker_id):
            return await callback.answer(NO_RIGHTS_TEXT, show_alert=True)

        await state.update_data(target_id=target_id, chat_id=chat_id)
        await state.set_state(ProfileStates.waiting_for_name)

        await callback.message.reply(
            "Напиши новое имя следующим сообщением (ответом на это сообщение не обязательно)."
        )
        return await callback.answer()

    # ------------------------------------------------------
    # Очки +1 / -1
    # ------------------------------------------------------
    if action in {"repup", "repdown"}:
        if not await can_edit_reputation(bot, chat_id, clicker_id):
            return await callback.answer(NO_RIGHTS_TEXT, show_alert=True)

        amount = 1 if action == "repup" else -1
        await change_member_reputation(chat_id, target_id, amount)

        profile = await get_member_profile(chat_id, target_id)
        target = await bot.get_chat_member(chat_id, target_id)
        text = await format_profile_text(chat_id, target.user, profile)

        try:
            await callback.message.edit_text(text, reply_markup=build_profile_keyboard(target_id))
        except Exception:
            pass  # сообщение могло не измениться (например, лимит Telegram на идентичный текст)

        return await callback.answer(f"{'+' if amount > 0 else ''}{amount}")

    # ------------------------------------------------------
    # Открыть панель управления
    #
    # В группах web_app-кнопки не работают (ограничение Telegram —
    # такие кнопки доступны только в личных чатах с ботом). Поэтому
    # вместо прямого запуска мини-аппа отправляем пользователя в ЛС
    # с ботом через специальный url в ответе на callback: Telegram
    # сам откроет личный чат и отправит боту "/start panel_<chat_id>".
    # См. handlers/info.py -> handle_panel_deeplink().
    # ------------------------------------------------------
    if action == "panel":
        bot_info = await bot.get_me()
        start_link = f"https://t.me/{bot_info.username}?start=panel_{chat_id}"
        return await callback.answer(url=start_link)

    await callback.answer()


# ============================================================
# FSM: ловим новое имя после нажатия "Изменить имя"
# ============================================================

@router.message(StateFilter(ProfileStates.waiting_for_name))
async def process_new_name(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_id = data.get("target_id")
    chat_id = data.get("chat_id")

    await state.clear()

    if not message.text or not message.text.strip():
        return await message.reply("Имя не может быть пустым. Попробуй ещё раз через /profile.")

    new_name = message.text.strip()

    await ensure_member_profile(chat_id, target_id)
    await update_member_name(chat_id, target_id, new_name)

    await message.reply(f"Имя изменено на «{new_name}».")


# ============================================================
# /setname — оставлена как текстовая альтернатива кнопке
# ============================================================

@router.message(Command("setname"))
async def cmd_setname(message: types.Message, command: CommandObject, bot: Bot):
    if not await can_edit_name(bot, message.chat.id, message.from_user.id):
        return await message.reply(NO_RIGHTS_TEXT)

    target, _ = _resolve_target(message)

    if not command.args:
        return await message.reply(
            "Укажи новое имя.\nПример: <code>/setname Молчаливый</code>"
        )

    new_name = command.args.strip()
    await ensure_member_profile(message.chat.id, target.id, target.full_name)
    await update_member_name(message.chat.id, target.id, new_name)

    await message.reply(f"Имя <b>{target.full_name}</b> изменено на «{new_name}».")


# ============================================================
# /setlegion — назначить легион
# ============================================================

@router.message(Command("setlegion"))
async def cmd_setlegion(message: types.Message, command: CommandObject, bot: Bot):
    if not await can_edit_legion(bot, message.chat.id, message.from_user.id):
        return await message.reply(NO_RIGHTS_TEXT)

    target, _ = _resolve_target(message)

    if not command.args:
        return await message.reply(
            "Укажи название легиона.\nПример: <code>/setlegion Пожиратели Миров</code>"
        )

    legion_name = command.args.strip()
    legion = await get_legion_by_name(message.chat.id, legion_name)

    if legion is None:
        return await message.reply(
            f"Легион «{legion_name}» не найден в этом чате. "
            f"Сначала его нужно создать (команда создания легионов ещё не реализована)."
        )

    await ensure_member_profile(message.chat.id, target.id, target.full_name)
    await update_member_legion(message.chat.id, target.id, legion["id"])
    await update_member_rank(message.chat.id, target.id, None)

    await message.reply(
        f"<b>{target.full_name}</b> приписан к легиону «{legion['name']}». "
        f"Звание сброшено — назначь заново через /setrank."
    )


# ============================================================
# /setrank — назначить звание (в пределах текущего легиона)
# ============================================================

@router.message(Command("setrank"))
async def cmd_setrank(message: types.Message, command: CommandObject, bot: Bot):
    if not await can_edit_rank(bot, message.chat.id, message.from_user.id):
        return await message.reply(NO_RIGHTS_TEXT)

    target, _ = _resolve_target(message)

    if not command.args:
        return await message.reply(
            "Укажи название звания.\nПример: <code>/setrank Легионер</code>"
        )

    profile = await get_member_profile(message.chat.id, target.id)
    legion_id = profile[5] if profile else None

    if not legion_id:
        return await message.reply(
            f"У <b>{target.full_name}</b> ещё не назначен легион — "
            f"сначала используй /setlegion."
        )

    rank_name = command.args.strip()
    rank = await get_rank_by_name(legion_id, rank_name)

    if rank is None:
        return await message.reply(
            f"Звание «{rank_name}» не найдено в этом легионе."
        )

    await update_member_rank(message.chat.id, target.id, rank["id"])
    await message.reply(f"<b>{target.full_name}</b> получил звание «{rank['name']}».")


# ============================================================
# /setstatus — назначить статус
# ============================================================

@router.message(Command("setstatus"))
async def cmd_setstatus(message: types.Message, command: CommandObject, bot: Bot):
    if not await can_edit_status(bot, message.chat.id, message.from_user.id):
        return await message.reply(NO_RIGHTS_TEXT)

    target, _ = _resolve_target(message)

    if not command.args:
        return await message.reply(
            "Укажи название статуса.\nПример: <code>/setstatus Предатель Легиона</code>"
        )

    status_name = command.args.strip()
    statuses = await get_statuses(message.chat.id)

    matched = next(
        (s for s in statuses if s["name"].lower() == status_name.lower()),
        None,
    )

    if matched is None:
        available = ", ".join(s["name"] for s in statuses) or "нет ни одного статуса"
        return await message.reply(
            f"Статус «{status_name}» не найден.\nДоступные: {available}"
        )

    await ensure_member_profile(message.chat.id, target.id, target.full_name)
    await update_member_status(message.chat.id, target.id, matched["id"])

    await message.reply(f"Статус <b>{target.full_name}</b> изменён на «{matched['name']}».")


# ============================================================
# /rep — изменить очки (текстовая альтернатива кнопкам)
# ============================================================

@router.message(Command("rep"))
async def cmd_rep(message: types.Message, command: CommandObject, bot: Bot):
    if not await can_edit_reputation(bot, message.chat.id, message.from_user.id):
        return await message.reply(NO_RIGHTS_TEXT)

    target, _ = _resolve_target(message)

    if not command.args or not command.args.strip().lstrip("+-").isdigit():
        return await message.reply(
            "Укажи изменение очков.\nПример: <code>/rep +5</code> или <code>/rep -10</code>"
        )

    amount = int(command.args.strip())

    await ensure_member_profile(message.chat.id, target.id, target.full_name)
    await change_member_reputation(message.chat.id, target.id, amount)

    profile = await get_member_profile(message.chat.id, target.id)
    new_reputation = profile[7] if profile else amount

    sign = "+" if amount >= 0 else ""
    await message.reply(
        f"Очки <b>{target.full_name}</b>: {sign}{amount} "
        f"(теперь: <b>{new_reputation}</b>)"
    )