import os
import uuid
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest

import database as db
from custom_methods import GetMyStarBalance, WithdrawStarBalance
from config import is_admin
import logging

logger = logging.getLogger("sbp_bot.admin")
router = Router()


class BroadcastState(StatesGroup):
    waiting_for_message = State()
    confirm_broadcast = State()


class AdminChequeState(StatesGroup):
    waiting_for_cheque_query = State()


class AdminUserState(StatesGroup):
    waiting_for_user_query = State()


class AdminGiveState(StatesGroup):
    waiting_for_give_data = State()


class AdminTakeState(StatesGroup):
    waiting_for_take_data = State()


def get_admin_dashboard_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Проверить чек / перевод", callback_data="admin_check_cheque"),
            InlineKeyboardButton(text="👤 Пользователь", callback_data="admin_find_user")
        ],
        [
            InlineKeyboardButton(text="➕ Начислить звёзды", callback_data="admin_give_stars"),
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="📤 Вывести резерв владельцу", callback_data="admin_withdraw_all")
        ],
        [
            InlineKeyboardButton(text="💾 Скачать бэкап БД (/backup)", callback_data="admin_backup_db")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_refresh"),
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

    if ch.get("recipient_username"):
        rec_cond = f"🔒 Только для <b>@{ch['recipient_username']}</b>"
    else:
        rec_cond = "🌐 <b>Для всех</b> (любой участник чата)"

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
        InlineKeyboardButton(text="🔍 Найти другую операцию", callback_data="admin_check_cheque"),
        InlineKeyboardButton(text="← В админку", callback_data="admin_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def format_admin_pending_transfer_card(pt: Dict[str, Any]) -> str:
    status_map = {
        "pending": "⏳ <b>Ожидает активации (получатель ещё не запустил бота)</b>",
        "claimed": "✅ <b>Получен (зачислен на баланс)</b>",
        "cancelled": "❌ <b>Аннулирован (возвращён отправителю)</b>"
    }
    status_str = status_map.get(pt["status"], pt["status"])

    sender_u = f"@{pt['sender_username']}" if pt.get("sender_username") else f"ID {pt['sender_id']}"
    rec_u = f"@{pt['recipient_username']}"
    comm_str = f"\n• <b>Комментарий:</b> <i>{pt['comment']}</i>" if pt.get("comment") else ""

    text = (
        f"⏳ <b>Отложенный перевод:</b> <code>{pt['trx_id']}</code>\n"
        f"────────────────────────\n"
        f"• <b>Статус:</b> {status_str}\n"
        f"• <b>Сумма:</b> <b>{pt['amount']:,} ⭐️</b>\n"
        f"• <b>Отправитель:</b> {sender_u} (<code>{pt['sender_id']}</code>)\n"
        f"• <b>Получатель:</b> <b>{rec_u}</b>\n"
        f"• <b>Дата создания:</b> <code>{pt['created_at']}</code>{comm_str}\n\n"
        f"💡 <i>Перевод зарезервирован. Чтобы забрать его, {rec_u} должен открыть бота @sbpbot и нажать /start.</i>"
    )
    return text


def get_admin_pending_transfer_kb(pt: Dict[str, Any]) -> InlineKeyboardMarkup:
    rows = []
    if pt["status"] == "pending":
        rows.append([
            InlineKeyboardButton(
                text="↩️ Аннулировать и вернуть отправителю",
                callback_data=f"adm_cancel_pt:{pt['trx_id']}"
            )
        ])
    rows.append([
        InlineKeyboardButton(text="🔍 Найти другую операцию", callback_data="admin_check_cheque"),
        InlineKeyboardButton(text="← В админку", callback_data="admin_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def format_admin_trx_card(trx: Dict[str, Any]) -> str:
    type_map = {
        "deposit": "📥 Пополнение (звёзды)",
        "withdrawal": "📤 Вывод звёзд",
        "transfer_out": "↗️ Исходящий перевод",
        "transfer_in": "↙️ Входящий перевод",
        "transfer_refund": "↩️ Возврат перевода",
        "cheque_created": "🧾 Создание чека",
        "cheque_claimed": "✅ Активация чека",
        "cheque_refund": "↩️ Возврат чека",
        "admin_give": "➕ Начисление администратором",
        "admin_take": "➖ Списание администратором",
    }
    t_name = type_map.get(trx.get("type", ""), trx.get("type", "Операция"))
    comm = f"\n• <b>Комментарий:</b> <i>{trx['comment']}</i>" if trx.get("comment") else ""
    return (
        f"🧾 <b>Транзакция:</b> <code>{trx['trx_id']}</code>\n"
        f"────────────────────────\n"
        f"• <b>Тип:</b> {t_name}\n"
        f"• <b>Сумма:</b> <b>{trx['amount']:,} ⭐️</b>\n"
        f"• <b>Пользователь (ID):</b> <code>{trx['user_id']}</code>\n"
        f"• <b>Контрагент:</b> <b>{trx.get('counterparty', '—')}</b>\n"
        f"• <b>Статус:</b> <code>{trx.get('status', 'success')}</code>\n"
        f"• <b>Дата:</b> <code>{trx.get('created_at', '—')}</code>{comm}"
    )


async def render_operation_search_result(target_event: Message | CallbackQuery, query: str) -> bool:
    res = await db.admin_find_any_operation(query)
    if not res:
        text = f"❌ Операция по запросу <code>{query}</code> не найдена в базе данных."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Попробовать снова", callback_data="admin_check_cheque")],
            [InlineKeyboardButton(text="← В админку", callback_data="admin_menu")]
        ])
        if isinstance(target_event, CallbackQuery):
            try:
                await target_event.message.edit_text(text, reply_markup=kb)
            except Exception:
                await target_event.message.answer(text, reply_markup=kb)
        else:
            await target_event.answer(text, reply_markup=kb)
        return False

    op_type = res["type"]
    data = res["data"]
    if op_type == "cheque":
        text = format_admin_cheque_card(data)
        kb = get_admin_cheque_kb(data)
    elif op_type == "pending_transfer":
        text = format_admin_pending_transfer_card(data)
        kb = get_admin_pending_transfer_kb(data)
    else:
        text = format_admin_trx_card(data)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Найти другую операцию", callback_data="admin_check_cheque")],
            [InlineKeyboardButton(text="← В админку", callback_data="admin_menu")]
        ])

    if isinstance(target_event, CallbackQuery):
        try:
            await target_event.message.edit_text(text, reply_markup=kb)
        except Exception:
            await target_event.message.answer(text, reply_markup=kb)
    else:
        await target_event.answer(text, reply_markup=kb)
    return True


def format_admin_user_card(user: Dict[str, Any], transactions: list) -> str:
    name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or "Клиент"
    u_str = f"@{user['username']}" if user.get("username") else "без username"
    bal = user.get("balance", 0)
    acc = user.get("account_number", "—")
    reg_date = user.get("created_at", "—")

    trx_lines = []
    if transactions:
        for t in transactions[:5]:
            sign = "+" if "in" in t["type"] or "deposit" in t["type"] or "refund" in t["type"] else "-"
            dt = t["created_at"][:16] if t.get("created_at") else "—"
            comm = f" ({t['comment']})" if t.get("comment") else ""
            trx_lines.append(f"• <code>{dt}</code> | <b>{sign}{t['amount']:,} ⭐️</b>{comm}")
        trx_block = "\n".join(trx_lines)
    else:
        trx_block = "<i>Операций пока нет</i>"

    return (
        f"👤 <b>Пользователь:</b> {name} ({u_str})\n"
        f"────────────────────────\n"
        f"• <b>Telegram ID:</b> <code>{user['user_id']}</code>\n"
        f"• <b>Счёт СБП:</b> <code>{acc}</code>\n"
        f"• <b>Текущий баланс:</b> <b>{bal:,} ⭐️</b>\n"
        f"• <b>Регистрация:</b> <code>{reg_date}</code>\n\n"
        f"📊 <b>Последние 5 операций:</b>\n"
        f"{trx_block}"
    )


def get_admin_user_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Начислить звёзды", callback_data=f"adm_give_to:{user_id}"),
            InlineKeyboardButton(text="➖ Списать звёзды", callback_data=f"adm_take_from:{user_id}")
        ],
        [
            InlineKeyboardButton(text="🔍 Другой пользователь", callback_data="admin_find_user"),
            InlineKeyboardButton(text="← В админку", callback_data="admin_menu")
        ]
    ])


@router.message(Command("admin"))
@router.message(Command("bank"))
async def cmd_admin(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return

    await state.clear()

    args = message.text.split(maxsplit=1)
    if len(args) > 1 and len(args[1].strip()) >= 3:
        found = await render_operation_search_result(message, args[1].strip())
        if found:
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


@router.message(Command("backup"))
async def cmd_backup(message: Message):
    if not is_admin(message.from_user.id):
        return
    if os.path.exists(db.DB_PATH):
        dt = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc = FSInputFile(str(db.DB_PATH), filename=f"sbp_bank_{dt}.db")
        await message.answer_document(doc, caption=f"💾 <b>Резервная копия базы данных СБП</b>\nДата: <code>{dt}</code>")
    else:
        await message.answer("Файл базы данных не найден.")


@router.callback_query(F.data == "admin_backup_db")
async def cb_admin_backup_db(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    if os.path.exists(db.DB_PATH):
        dt = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc = FSInputFile(str(db.DB_PATH), filename=f"sbp_bank_{dt}.db")
        await callback.message.answer_document(doc, caption=f"💾 <b>Резервная копия базы данных СБП</b>\nДата: <code>{dt}</code>")
        await callback.answer()
    else:
        await callback.answer("Файл базы данных не найден", show_alert=True)


# --- OPERATION & CHEQUE INSPECTOR (FOR ADMIN) ---

@router.message(Command("check"))
@router.message(Command("cheque_info"))
async def cmd_check(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        query = args[1].strip()
        await render_operation_search_result(message, query)
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
        "🔍 <b>Проверка операции / чека / перевода</b>\n\n"
        "Отправьте в чат:\n"
        "• <b>Номер перевода / транзакции</b> (например: <code>1C5RC</code> или <code>#SBP-TRX-20261017-1C5RC</code>)\n"
        "• <b>ID чека</b> (например: <code>ch_abc123</code>)\n"
        "• Или <b>ссылку на чек</b>\n\n"
        "<i>Или выберите один из недавних чеков:</i>"
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
    await state.clear()
    await render_operation_search_result(message, query)


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

    try:
        await callback.bot.send_message(
            creator_id,
            f"ℹ️ Ваш чек <code>{cheque_id}</code> на <b>{amount:,} ⭐️</b> был аннулирован администратором.\n"
            f"Звёзды возвращены на ваш баланс СБП."
        )
    except Exception:
        pass

    updated_cheque = await db.get_cheque(cheque_id)
    if updated_cheque:
        await callback.message.edit_text(
            format_admin_cheque_card(updated_cheque),
            reply_markup=get_admin_cheque_kb(updated_cheque)
        )


@router.callback_query(F.data.startswith("adm_cancel_pt:"))
async def cb_adm_cancel_pending_transfer(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    trx_id = callback.data.split(":", 1)[1]
    pt = await db.cancel_pending_transfer(trx_id)

    if not pt:
        await callback.answer("Перевод не найден или уже был получен/аннулирован", show_alert=True)
        return

    amount = pt["amount"]
    sender_id = pt["sender_id"]

    await callback.answer(f"Перевод аннулирован. {amount:,} ⭐️ возвращены отправителю!", show_alert=True)

    try:
        await callback.bot.send_message(
            sender_id,
            f"ℹ️ Ваш отложенный перевод <code>{pt['trx_id']}</code> для @{pt['recipient_username']} на <b>{amount:,} ⭐️</b> был аннулирован администратором.\n"
            f"Звёзды возвращены на ваш баланс СБП."
        )
    except Exception:
        pass

    updated_pt = await db.get_pending_transfer_by_query(trx_id)
    if updated_pt:
        await callback.message.edit_text(
            format_admin_pending_transfer_card(updated_pt),
            reply_markup=get_admin_pending_transfer_kb(updated_pt)
        )


@router.message(Command("refund"))
@router.message(Command("cancel_transfer"))
async def cmd_admin_refund(message: Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "ℹ️ <b>Использование:</b> <code>/refund &lt;ID транзакции или чека&gt;</code>\n"
            "Пример: <code>/refund 1C5RC</code> или <code>/refund #SBP-TRX-20261017-1C5RC</code>"
        )
        return

    query = args[1].strip()

    # 1. Try pending transfer
    pt = await db.cancel_pending_transfer(query)
    if pt:
        await message.answer(
            f"✅ <b>Отложенный перевод аннулирован:</b> <code>{pt['trx_id']}</code>\n"
            f"• Сумма: <b>{pt['amount']:,} ⭐️</b>\n"
            f"• Отправитель: ID <code>{pt['sender_id']}</code> (@{pt.get('sender_username', '—')})\n"
            f"• Получатель: @{pt['recipient_username']}\n\n"
            f"Звёзды успешно возвращены на баланс отправителя!"
        )
        try:
            await message.bot.send_message(
                pt["sender_id"],
                f"ℹ️ Ваш перевод <code>{pt['trx_id']}</code> для @{pt['recipient_username']} на <b>{pt['amount']:,} ⭐️</b> был отменён администратором.\n"
                f"Звёзды возвращены на ваш счёт СБП."
            )
        except Exception:
            pass
        return

    # 2. Try cheque
    ch = await db.admin_cancel_cheque(query)
    if ch:
        await message.answer(
            f"✅ <b>Чек аннулирован:</b> <code>{ch['cheque_id']}</code>\n"
            f"• Сумма: <b>{ch['amount']:,} ⭐️</b>\n"
            f"• Создатель: ID <code>{ch['creator_id']}</code> (@{ch.get('creator_username', '—')})\n\n"
            f"Звёзды успешно возвращены на баланс создателя!"
        )
        try:
            await message.bot.send_message(
                ch["creator_id"],
                f"ℹ️ Ваш чек <code>{ch['cheque_id']}</code> на <b>{ch['amount']:,} ⭐️</b> был аннулирован администратором.\n"
                f"Звёзды возвращены на ваш счёт СБП."
            )
        except Exception:
            pass
        return

    await message.answer(
        f"❌ Операция <code>{query}</code> не найдена среди активных чеков или ожидающих переводов (возможно, уже получена или была аннулирована ранее)."
    )


# --- USER INSPECTOR & BALANCE MANAGEMENT (FOR ADMIN) ---

@router.message(Command("user"))
@router.message(Command("u"))
async def cmd_user(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        query = args[1].strip()
        user = await db.admin_find_user(query)
        if user:
            trxs = await db.get_user_transactions(user["user_id"], limit=5)
            await message.answer(format_admin_user_card(user, trxs), reply_markup=get_admin_user_kb(user["user_id"]))
            return
        else:
            await message.answer(f"❌ Пользователь <code>{query}</code> не найден в базе данных.")
            return

    await state.set_state(AdminUserState.waiting_for_user_query)
    await message.answer(
        "👤 <b>Поиск пользователя</b>\n\n"
        "Отправьте @username, Telegram ID или номер счёта СБП:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]
        ])
    )


@router.callback_query(F.data == "admin_find_user")
async def cb_admin_find_user(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await state.set_state(AdminUserState.waiting_for_user_query)
    await callback.message.edit_text(
        "👤 <b>Поиск пользователя</b>\n\n"
        "Отправьте @username, Telegram ID или номер счёта СБП:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]
        ])
    )
    await callback.answer()


@router.message(AdminUserState.waiting_for_user_query)
async def process_admin_user_query(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    query = message.text.strip()
    user = await db.admin_find_user(query)

    if not user:
        await message.answer(
            f"❌ Пользователь <code>{query}</code> не найден в базе данных.\n"
            f"Попробуйте снова или нажмите отмену:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]
            ])
        )
        return

    await state.clear()
    trxs = await db.get_user_transactions(user["user_id"], limit=5)
    await message.answer(format_admin_user_card(user, trxs), reply_markup=get_admin_user_kb(user["user_id"]))


# --- GIVE STARS / CREDIT MANUAL BALANCE ---

@router.message(Command("give"))
@router.message(Command("credit"))
async def cmd_give(message: Message):
    if not is_admin(message.from_user.id):
        return

    # /give @username 50 [комментарий]
    parts = message.text.split(maxsplit=3)
    if len(parts) < 3 or not parts[2].isdigit():
        await message.answer(
            "Формат команды:\n"
            "<code>/give &lt;@username или ID&gt; &lt;кол-во звёзд&gt; [комментарий]</code>\n\n"
            "Пример: <code>/give @durov 50 Возврат за платеж</code>"
        )
        return

    target_query = parts[1]
    amount = int(parts[2])
    comment = parts[3] if len(parts) > 3 else "Ручное начисление администратором"

    if amount <= 0:
        await message.answer("Сумма должна быть больше 0.")
        return

    user = await db.admin_find_user(target_query)
    if not user:
        if target_query.isdigit():
            uid = int(target_query)
            user = await db.get_or_create_user(uid, None, "Клиент", None)
        else:
            try:
                chat = await message.bot.get_chat(target_query if target_query.startswith("@") else f"@{target_query}")
                user = await db.get_or_create_user(
                    chat.id,
                    chat.username,
                    chat.first_name or "Клиент",
                    chat.last_name
                )
            except Exception as e:
                logger.warning(f"Could not resolve {target_query} via get_chat: {e}")

    if not user:
        await message.answer(f"❌ Пользователь <code>{target_query}</code> не найден в базе данных и его профиль недоступен.")
        return

    uid = user["user_id"]
    trx_id = await db.credit_balance(
        user_id=uid,
        amount=amount,
        trx_type="admin_deposit",
        comment=comment,
        counterparty="Администратор"
    )

    user_updated = await db.get_user(uid)
    new_bal = user_updated["balance"]
    u_label = f"@{user_updated['username']}" if user_updated.get("username") else f"ID {uid}"

    # Notify user in bot
    try:
        await message.bot.send_message(
            uid,
            f"💳 <b>Пополнение счёта администратором</b>\n\n"
            f"Вам зачислено: <b>+{amount:,} ⭐️</b>\n"
            f"Текущий баланс: <b>{new_bal:,} ⭐️</b>\n"
            f"Причина: <i>{comment}</i>"
        )
    except Exception:
        pass

    await message.answer(
        f"✅ <b>Звёзды успешно начислены!</b>\n\n"
        f"• Пользователь: {u_label} (<code>{uid}</code>)\n"
        f"• Начислено: <b>+{amount:,} ⭐️</b>\n"
        f"• Новый баланс: <b>{new_bal:,} ⭐️</b>\n"
        f"• Транзакция: <code>{trx_id}</code>"
    )


@router.message(Command("take"))
@router.message(Command("debit"))
async def cmd_take(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split(maxsplit=3)
    if len(parts) < 3 or not parts[2].isdigit():
        await message.answer(
            "Формат команды:\n"
            "<code>/take &lt;@username или ID&gt; &lt;кол-во звёзд&gt; [комментарий]</code>\n\n"
            "Пример: <code>/take @durov 10 Корректировка</code>"
        )
        return

    target_query = parts[1]
    amount = int(parts[2])
    comment = parts[3] if len(parts) > 3 else "Списание администратором"

    user = await db.admin_find_user(target_query)
    if not user:
        await message.answer(f"❌ Пользователь <code>{target_query}</code> не найден.")
        return

    uid = user["user_id"]
    trx_id = await db.debit_balance(uid, amount, trx_type="admin_debit", comment=comment, counterparty="Администратор")
    if not trx_id:
        await message.answer(f"❌ Недостаточно средств на балансе пользователя (Баланс: {user['balance']} ⭐️).")
        return

    user_updated = await db.get_user(uid)
    await message.answer(
        f"✅ Списано <b>-{amount:,} ⭐️</b> у пользователя {target_query}.\n"
        f"Новый баланс: <b>{user_updated['balance']:,} ⭐️</b>"
    )


@router.callback_query(F.data == "admin_give_stars")
async def cb_admin_give_stars(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await state.set_state(AdminGiveState.waiting_for_give_data)
    await callback.message.edit_text(
        "➕ <b>Начисление звёзд пользователю</b>\n\n"
        "Отправьте @username или ID пользователя и сумму через пробел:\n"
        "<i>Например: <code>@durov 50</code> или <code>123456789 25</code></i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_give_to:"))
async def cb_adm_give_to_user(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    uid = int(callback.data.split(":")[1])
    await state.update_data(target_uid=uid)
    await state.set_state(AdminGiveState.waiting_for_give_data)

    await callback.message.edit_text(
        f"➕ <b>Начисление звёзд пользователю ID <code>{uid}</code></b>\n\n"
        f"Введите количество звёзд для начисления:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]
        ])
    )
    await callback.answer()


@router.message(AdminGiveState.waiting_for_give_data)
async def process_admin_give_data(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    target_uid = data.get("target_uid")

    text = message.text.strip()
    if target_uid:
        if not text.isdigit() or int(text) <= 0:
            await message.answer("Введите корректное число звёзд:")
            return
        amount = int(text)
        user = await db.get_user(target_uid)
    else:
        parts = text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            await message.answer("Неверный формат. Введите <code>@username 50</code>:")
            return
        user = await db.admin_find_user(parts[0])
        if not user:
            try:
                target_q = parts[0] if parts[0].startswith("@") else f"@{parts[0]}"
                chat = await message.bot.get_chat(target_q)
                user = await db.get_or_create_user(chat.id, chat.username, chat.first_name or "Клиент", chat.last_name)
            except Exception as e:
                logger.warning(f"Could not resolve {parts[0]}: {e}")
        amount = int(parts[1])

    if not user:
        await message.answer("Пользователь не найден. Попробуйте снова или нажмите отмену.",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]
                             ]))
        return

    await state.clear()
    uid = user["user_id"]
    trx_id = await db.credit_balance(
        user_id=uid,
        amount=amount,
        trx_type="admin_deposit",
        comment="Ручное начисление администратором",
        counterparty="Администратор"
    )

    user_updated = await db.get_user(uid)
    u_label = f"@{user_updated['username']}" if user_updated.get("username") else f"ID {uid}"

    try:
        await message.bot.send_message(
            uid,
            f"💳 <b>Пополнение счёта администратором</b>\n\n"
            f"Вам зачислено: <b>+{amount:,} ⭐️</b>\n"
            f"Текущий баланс: <b>{user_updated['balance']:,} ⭐️</b>"
        )
    except Exception:
        pass

    await message.answer(
        f"✅ <b>Успешно зачислено +{amount:,} ⭐️</b>\n\n"
        f"• Пользователь: {u_label}\n"
        f"• Новый баланс: <b>{user_updated['balance']:,} ⭐️</b>\n"
        f"• Транзакция: <code>{trx_id}</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← В админку", callback_data="admin_menu")]
        ])
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
