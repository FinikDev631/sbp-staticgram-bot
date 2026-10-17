import uuid
import asyncio
from typing import Optional, Dict, Any
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest

import database as db
from custom_methods import GetMyStarBalance, WithdrawStarBalance
from config import is_admin
from keyboards.main_kb import get_back_button

router = Router()


class BroadcastState(StatesGroup):
    waiting_for_message = State()
    confirm_broadcast = State()


class AdminChequeState(StatesGroup):
    waiting_for_cheque_query = State()


def get_admin_dashboard_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Проверить чек", callback_data="admin_check_cheque"),
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="📤 Вывести резерв владельцу", callback_data="admin_withdraw_all")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_refresh")
        ],
        [
            InlineKeyboardButton(text="← В главное меню", callback_data="back_to_menu")
        ]
    ])


def format_admin_cheque_card(ch: Dict[str, Any]) -> str:
    status_map = {
        "active": "🟢 <b>Активен (ожидает получения)</b>",
        "claimed": "✅ <b>Активирован (забран)</b>",
        "cancelled": "❌ <b>Аннулирован (средства возвращены)</b>"
    }
    status_text = status_map.get(ch["status"], ch["status"])

    creator_u = f"@{ch['creator_username']}" if ch.get("creator_username") else "без username"
    creator_str = f"{creator_u} (ID: <code>{ch['creator_id']}</code>)"

    # Recipient restriction
    if ch.get("recipient_username"):
        rec_cond = f"🔒 Только для <b>@{ch['recipient_username']}</b>"
    else:
        rec_cond = "🌐 <b>Для всех</b> (любой участник чата)"

    # Claimer details
    if ch["status"] == "claimed":
        claimer_u = f"@{ch['claimed_by_username']}" if ch.get("claimed_by_username") else "без username"
        claimer_str = f"{claimer_u} (ID: <code>{ch.get('claimed_by_id')}</code>)"
        claimed_at_str = ch.get("claimed_at") or "—"
        claim_info = f"\n• <b>Кто забрал:</b> {claimer_str}\n• <b>Когда забрал:</b> <code>{claimed_at_str}</code>"
    else:
        claim_info = ""

    comment_str = f"\n• <b>Комментарий:</b> <i>{ch['comment']}</i>" if ch.get("comment") else ""

    text = (
        f"🧾 <b>Карточка чека:</b> <code>{ch['cheque_id']}</code>\n"
        f"────────────────────────\n"
        f"• <b>Статус:</b> {status_text}\n"
        f"• <b>Сумма:</b> <b>{ch['amount']:,} ⭐️</b>\n"
        f"• <b>Создатель:</b> {creator_str}\n"
        f"• <b>Кому доступен:</b> {rec_cond}{claim_info}\n"
        f"• <b>Создан:</b> <code>{ch['created_at']}</code>{comment_str}\n"
        f"• <b>Ссылка:</b> <code>https://staticgram.top/sbpbot?start={ch['cheque_id']}</code>"
    )
    return text


def get_admin_cheque_kb(ch: Dict[str, Any]) -> InlineKeyboardMarkup:
    rows = []
    if ch["status"] == "active":
        rows.append([
            InlineKeyboardButton(
                text="❌ Аннулировать и вернуть создателю",
                callback_data=f"adm_cancel_ch:{ch['cheque_id']}"
            )
        ])
    rows.append([
        InlineKeyboardButton(text="🔍 Найти другой чек", callback_data="admin_check_cheque"),
        InlineKeyboardButton(text="← В админку", callback_data="admin_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("admin"))
@router.message(Command("bank"))
async def cmd_admin(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return

    await state.clear()

    args = message.text.split(maxsplit=1)
    if len(args) > 1 and (args[1].startswith("ch_") or len(args[1]) >= 4):
        # Quick check: /admin ch_12345
        cheque = await db.admin_find_cheque(args[1])
        if cheque:
            await message.answer(format_admin_cheque_card(cheque), reply_markup=get_admin_cheque_kb(cheque))
            return

    try:
        star_bal_res = await message.bot(GetMyStarBalance())
        bot_stars = star_bal_res.get("amount", 0)
    except Exception as e:
        bot_stars = f"Ошибка ({e})"

    stats = await db.get_system_stats()

    text = (
        "🏦 <b>Панель управления банком СБП</b>\n\n"
        f"⭐️ <b>Баланс звёзд бота:</b> <b>{bot_stars} ⭐️</b>\n"
        "<i>(Используется для внешних выводов пользователям через withdrawStarBalance)</i>\n\n"
        "📊 <b>Статистика сервиса:</b>\n"
        f"• Пользователей: <b>{stats['users_count']:,}</b>\n"
        f"• Баланс на счетах: <b>{stats['total_user_balance']:,} ⭐️</b>\n"
        f"• Переводов: <b>{stats['transfers_count']:,}</b>\n"
        f"• Объём: <b>{stats['transfers_volume']:,} ⭐️</b>\n"
        f"• Активных чеков: <b>{stats['active_cheques']}</b>"
    )

    await message.answer(text, reply_markup=get_admin_dashboard_kb())


@router.callback_query(F.data == "admin_menu")
async def cb_admin_menu(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await state.clear()
    try:
        star_bal_res = await callback.bot(GetMyStarBalance())
        bot_stars = star_bal_res.get("amount", 0)
    except Exception:
        bot_stars = 0

    stats = await db.get_system_stats()
    text = (
        "🏦 <b>Панель управления банком СБП</b>\n\n"
        f"⭐️ <b>Баланс звёзд бота:</b> <b>{bot_stars} ⭐️</b>\n"
        "<i>(Используется для внешних выводов пользователям через withdrawStarBalance)</i>\n\n"
        "📊 <b>Статистика сервиса:</b>\n"
        f"• Пользователей: <b>{stats['users_count']:,}</b>\n"
        f"• Баланс на счетах: <b>{stats['total_user_balance']:,} ⭐️</b>\n"
        f"• Переводов: <b>{stats['transfers_count']:,}</b>\n"
        f"• Объём: <b>{stats['transfers_volume']:,} ⭐️</b>\n"
        f"• Активных чеков: <b>{stats['active_cheques']}</b>"
    )

    try:
        await callback.message.edit_text(text, reply_markup=get_admin_dashboard_kb())
    except Exception:
        await callback.message.answer(text, reply_markup=get_admin_dashboard_kb())
    await callback.answer()


@router.callback_query(F.data == "admin_refresh")
async def cb_admin_refresh(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    try:
        star_bal_res = await callback.bot(GetMyStarBalance())
        bot_stars = star_bal_res.get("amount", 0)
    except Exception:
        bot_stars = 0

    stats = await db.get_system_stats()
    text = (
        "🏦 <b>Панель управления банком СБП</b>\n\n"
        f"⭐️ <b>Баланс звёзд бота:</b> <b>{bot_stars} ⭐️</b>\n"
        "<i>(Используется для внешних выводов пользователям через withdrawStarBalance)</i>\n\n"
        "📊 <b>Статистика сервиса:</b>\n"
        f"• Пользователей: <b>{stats['users_count']:,}</b>\n"
        f"• Баланс на счетах: <b>{stats['total_user_balance']:,} ⭐️</b>\n"
        f"• Переводов: <b>{stats['transfers_count']:,}</b>\n"
        f"• Объём: <b>{stats['transfers_volume']:,} ⭐️</b>\n"
        f"• Активных чеков: <b>{stats['active_cheques']}</b>"
    )

    await callback.message.edit_text(text, reply_markup=get_admin_dashboard_kb())
    await callback.answer("Данные обновлены")


@router.callback_query(F.data == "admin_withdraw_all")
async def cb_admin_withdraw_all(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    req_id = f"owner-wd-{uuid.uuid4().hex[:12]}"
    try:
        res = await callback.bot(WithdrawStarBalance(request_id=req_id))
        await callback.answer("✅ Весь баланс звёзд выведен владельцу!", show_alert=True)
    except TelegramBadRequest as e:
        if "BALANCE_TOO_LOW" in e.message:
            await callback.answer("⚠️ На балансе бота нет доступных звёзд для вывода.", show_alert=True)
        else:
            await callback.answer(f"⚠️ Ошибка: {e.message}", show_alert=True)
    except Exception as e:
        await callback.answer(f"⚠️ Ошибка: {e}", show_alert=True)


# --- CHEQUE INSPECTOR (FOR ADMIN) ---

@router.message(Command("check"))
@router.message(Command("cheque_info"))
async def cmd_check(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        query = args[1].strip()
        cheque = await db.admin_find_cheque(query)
        if cheque:
            await message.answer(format_admin_cheque_card(cheque), reply_markup=get_admin_cheque_kb(cheque))
            return
        else:
            await message.answer(
                f"❌ Чек по запросу <code>{query}</code> не найден в базе данных.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔍 Попробовать снова", callback_data="admin_check_cheque")],
                    [InlineKeyboardButton(text="← В админку", callback_data="admin_menu")]
                ])
            )
            return

    await prompt_cheque_search(message, state)


@router.callback_query(F.data == "admin_check_cheque")
async def cb_admin_check_cheque(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await prompt_cheque_search(callback.message, state, is_edit=True)
    await callback.answer()


async def prompt_cheque_search(message: Message, state: FSMContext, is_edit: bool = False):
    await state.set_state(AdminChequeState.waiting_for_cheque_query)

    recent_cheques = await db.admin_get_recent_cheques(limit=5)
    rows = []

    if recent_cheques:
        for ch in recent_cheques:
            icon = "🟢" if ch["status"] == "active" else ("✅" if ch["status"] == "claimed" else "❌")
            btn_text = f"{icon} {ch['amount']:,} ⭐️ | {ch['cheque_id'][:12]}..."
            rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"adm_view_ch:{ch['cheque_id']}")])

    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    text = (
        "🔍 <b>Проверка чека администратором</b>\n\n"
        "Отправьте в чат <b>ID чека</b> (например, <code>ch_abc123</code>), часть ID или <b>ссылку на чек</b>.\n\n"
        "<i>Или выберите один из недавних чеков ниже:</i>"
    )

    if is_edit:
        try:
            await message.edit_text(text, reply_markup=kb)
        except Exception:
            await message.answer(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.message(AdminChequeState.waiting_for_cheque_query)
async def process_admin_cheque_query(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    query = message.text.strip()
    cheque = await db.admin_find_cheque(query)

    if not cheque:
        await message.answer(
            f"❌ Чек <code>{query}</code> не найден в базе данных.\n\n"
            f"Проверьте правильность ID или отправьте другой:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]
            ])
        )
        return

    await state.clear()
    await message.answer(format_admin_cheque_card(cheque), reply_markup=get_admin_cheque_kb(cheque))


@router.callback_query(F.data.startswith("adm_view_ch:"))
async def cb_adm_view_cheque(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await state.clear()
    cheque_id = callback.data.split(":", 1)[1]
    cheque = await db.get_cheque(cheque_id)

    if not cheque:
        await callback.answer("Чек не найден в базе данных", show_alert=True)
        return

    await callback.message.edit_text(format_admin_cheque_card(cheque), reply_markup=get_admin_cheque_kb(cheque))
    await callback.answer()


@router.callback_query(F.data.startswith("adm_cancel_ch:"))
async def cb_adm_cancel_cheque(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    cheque_id = callback.data.split(":", 1)[1]
    cheque = await db.admin_cancel_cheque(cheque_id)

    if not cheque:
        await callback.answer("Чек не найден или уже был забран/аннулирован", show_alert=True)
        return

    amount = cheque["amount"]
    creator_id = cheque["creator_id"]

    await callback.answer(f"Чек аннулирован. {amount:,} ⭐️ возвращены создателю!", show_alert=True)

    # Notify creator if possible
    try:
        await callback.bot.send_message(
            creator_id,
            f"ℹ️ Ваш чек <code>{cheque_id}</code> на <b>{amount:,} ⭐️</b> был аннулирован администратором.\n"
            f"Звёзды возвращены на ваш баланс СБП."
        )
    except Exception:
        pass

    # Refresh card view
    updated_cheque = await db.get_cheque(cheque_id)
    if updated_cheque:
        await callback.message.edit_text(
            format_admin_cheque_card(updated_cheque),
            reply_markup=get_admin_cheque_kb(updated_cheque)
        )


# --- BROADCAST HANDLERS ---

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        text_to_send = args[1]
        await state.update_data(broadcast_type="text", text=text_to_send)
        await state.set_state(BroadcastState.confirm_broadcast)

        user_ids = await db.get_all_user_ids()
        await message.answer(
            f"📢 <b>Предпросмотр рассылки:</b>\n\n{text_to_send}\n\n"
            f"👥 Получателей в базе: <b>{len(user_ids)} чел.</b>\n\n"
            f"Запустить рассылку?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚀 Начать рассылку", callback_data="confirm_broadcast_now"),
                    InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")
                ]
            ])
        )
        return

    await state.set_state(BroadcastState.waiting_for_message)
    await message.answer(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Отправьте сообщение (текст, фото, видео или перешлите готовый пост), которое нужно разослать всем пользователям СБП:\n\n"
        "<i>Вы сможете посмотреть предпросмотр перед подтверждением.</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")]
        ])
    )


@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await state.set_state(BroadcastState.waiting_for_message)
    await callback.message.answer(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Отправьте сообщение (текст, фото, видео или перешлите готовый пост), которое нужно разослать всем пользователям СБП:\n\n"
        "<i>Вы сможете посмотреть предпросмотр перед подтверждением.</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")]
        ])
    )
    await callback.answer()


@router.message(BroadcastState.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.update_data(
        broadcast_type="copy",
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    await state.set_state(BroadcastState.confirm_broadcast)

    user_ids = await db.get_all_user_ids()

    await message.answer("👆 <b>Сообщение для рассылки принято!</b>")
    await message.answer(
        f"👥 Получателей в базе: <b>{len(user_ids)} чел.</b>\n\n"
        f"Запустить рассылку?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Начать рассылку", callback_data="confirm_broadcast_now"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")
            ]
        ])
    )


@router.callback_query(F.data == "confirm_broadcast_now", BroadcastState.confirm_broadcast)
async def process_confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    data = await state.get_data()
    await state.clear()

    status_msg = await callback.message.answer("⏳ <b>Рассылка запущена...</b>")
    await callback.answer()

    user_ids = await db.get_all_user_ids()
    total = len(user_ids)
    success = 0
    failed = 0

    b_type = data.get("broadcast_type")
    from_chat_id = data.get("from_chat_id")
    msg_id = data.get("message_id")
    plain_text = data.get("text")

    for uid in user_ids:
        try:
            if b_type == "copy":
                await callback.bot.copy_message(
                    chat_id=uid,
                    from_chat_id=from_chat_id,
                    message_id=msg_id
                )
            else:
                await callback.bot.send_message(chat_id=uid, text=plain_text)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.04)

    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"• Всего пользователей: <b>{total}</b>\n"
        f"• Успешно доставлено: <b>{success}</b>\n"
        f"• Ошибок / заблокировали: <b>{failed}</b>"
    )


@router.callback_query(F.data == "cancel_broadcast")
async def cb_cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Рассылка отменена.")
    await callback.answer()
