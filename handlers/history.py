from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import database as db
from utils.formatters import format_electronic_receipt
from keyboards.main_kb import get_back_button

router = Router()

TYPE_NAMES = {
    "transfer_in": ("🟢", "Входящий перевод СБП"),
    "transfer_out": ("🔴", "Перевод через СБП"),
    "deposit": ("📥", "Пополнение звёздами"),
    "withdrawal": ("📤", "Вывод звёзд на аккаунт"),
    "cheque_created": ("🧾", "Создание чека СБП"),
    "cheque_claimed": ("🎉", "Активация чека СБП"),
    "cheque_refund": ("🔄", "Возврат чека СБП")
}

@router.callback_query(F.data == "menu_history")
@router.message(Command("history"))
async def show_history(event: Message | CallbackQuery):
    user_id = event.from_user.id
    history = await db.get_user_transactions(user_id, limit=10)

    if not history:
        text = (
            "📊 <b>ВЫПИСКА ПО СЧЁТУ СБП</b>\n"
            "────────────────────────\n"
            "У вас пока нет совершённых операций.\n"
            "Все ваши переводы, пополнения и выводы будут отображаться здесь с подробными электронными чеками!"
        )
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text, reply_markup=get_back_button())
            await event.answer()
        else:
            await event.answer(text, reply_markup=get_back_button())
        return

    text = "📊 <b>ВЫПИСКА ПО СЧЁТУ СБП</b>\n────────────────────────\n"
    buttons = []

    for tx in history:
        icon, name = TYPE_NAMES.get(tx["type"], ("⚪️", "Операция СБП"))
        sign = "+" if tx["type"] in ("transfer_in", "deposit", "cheque_claimed", "cheque_refund") else "-"
        dt = tx["created_at"][:16] if tx.get("created_at") else ""
        text += f"{icon} <b>{sign}{tx['amount']:,} ⭐️</b> — {name}\n"
        text += f"   <i>{dt} • {tx.get('counterparty') or ''}</i>\n\n"

        buttons.append([
            InlineKeyboardButton(text=f"📄 Чек: {tx['trx_id']}", callback_data=f"view_tx:{tx['trx_id']}")
        ])

    buttons.append([InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_menu")])
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
        await callback.answer("⚠️ Чек не найден.", show_alert=True)
        return

    icon, name = TYPE_NAMES.get(tx["type"], ("⚪️", "Операция СБП"))
    user = await db.get_user(tx["user_id"])
    u_label = f"@{user['username']}" if user.get("username") else f"{user['first_name']} ({user['account_number']})"

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

    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к выписке", callback_data="menu_history")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_menu")]
    ])

    await callback.message.edit_text(receipt, reply_markup=back_kb)
    await callback.answer()
