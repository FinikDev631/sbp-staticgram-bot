from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import database as db
from utils.formatters import format_electronic_receipt
from keyboards.main_kb import get_back_button

router = Router()

TYPE_NAMES = {
    "transfer_in": "Входящий перевод",
    "transfer_out": "Исходящий перевод",
    "deposit": "Пополнение",
    "withdrawal": "Вывод на аккаунт",
    "cheque_created": "Создание чека",
    "cheque_claimed": "Активация чека",
    "cheque_refund": "Возврат чека"
}

@router.callback_query(F.data == "menu_history")
@router.message(Command("history"))
async def show_history(event: Message | CallbackQuery):
    user_id = event.from_user.id
    history = await db.get_user_transactions(user_id, limit=8)

    if not history:
        text = "<b>История операций</b>\n\nУ вас пока нет транзакций."
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text, reply_markup=get_back_button())
            await event.answer()
        else:
            await event.answer(text, reply_markup=get_back_button())
        return

    text = "<b>История операций</b>\n\n"
    buttons = []

    for tx in history:
        name = TYPE_NAMES.get(tx["type"], "Операция")
        sign = "+" if tx["type"] in ("transfer_in", "deposit", "cheque_claimed", "cheque_refund") else "-"
        dt = tx["created_at"][5:16] if tx.get("created_at") else ""
        counterparty = f" • {tx['counterparty']}" if tx.get('counterparty') else ""
        text += f"• <code>{dt}</code>  <b>{sign}{tx['amount']:,} ⭐️</b>  {name}{counterparty}\n"

        buttons.append([
            InlineKeyboardButton(text=f"Чек #{tx['trx_id']}", callback_data=f"view_tx:{tx['trx_id']}")
        ])

    buttons.append([InlineKeyboardButton(text="← В меню", callback_data="back_to_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("view_tx:"))
async def view_transaction_check(callback: CallbackQuery):
    trx_id = callback.data.split(":")[1]
    tx = await db.get_transaction(trx_id)

    if not tx:
        await callback.answer("Чек не найден.", show_alert=True)
        return

    name = TYPE_NAMES.get(tx["type"], "Операция")
    user = await db.get_user(tx["user_id"])
    u_label = f"@{user['username']}" if user.get("username") else f"id{user['user_id']}"

    if tx["type"] in ("transfer_out", "withdrawal", "cheque_created"):
        sender_label = u_label
        recipient_label = tx.get("counterparty") or "Получатель"
    else:
        sender_label = tx.get("counterparty") or "Отправитель"
        recipient_label = u_label

    receipt = format_electronic_receipt(
        trx_id=tx["trx_id"],
        op_type=name,
        amount=tx["amount"],
        sender_label=sender_label,
        recipient_label=recipient_label,
        comment=tx.get("comment"),
        dt_str=tx.get("created_at")
    )

    rows = []
    if tx["type"] == "cheque_created":
        ch_id = tx.get("counterparty", "").replace("Чек ", "").strip()
        ch = await db.get_cheque(ch_id)
        if ch and ch["status"] == "active":
            rows.append([InlineKeyboardButton(text=f"↩️ Аннулировать чек ({ch['amount']:,} ⭐️)", callback_data=f"cancel_res_ch:{ch['cheque_id']}")])
    elif tx["type"] == "transfer_out":
        pt = await db.get_pending_transfer_by_query(tx["trx_id"])
        if pt and pt["status"] == "pending":
            rows.append([InlineKeyboardButton(text=f"↩️ Отменить перевод ({pt['amount']:,} ⭐️)", callback_data=f"cancel_res_pt:{pt['trx_id']}")])

    rows.append([
        InlineKeyboardButton(text="← К истории", callback_data="menu_history"),
        InlineKeyboardButton(text="В меню", callback_data="back_to_menu")
    ])
    back_kb = InlineKeyboardMarkup(inline_keyboard=rows)

    await callback.message.edit_text(receipt, reply_markup=back_kb)
    await callback.answer()
