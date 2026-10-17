from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from utils.states import TransferState
from utils.formatters import (
    mask_name,
    format_transfer_confirmation,
    format_electronic_receipt,
    format_sbp_card
)
from keyboards.main_kb import get_cancel_kb, get_back_button
from keyboards.transfer_kb import (
    get_quick_amount_kb,
    get_skip_comment_kb,
    get_confirm_transfer_kb
)

router = Router()

@router.callback_query(F.data == "menu_transfer")
@router.message(Command("pay"))
async def start_transfer_flow(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    user = await db.get_user(user_id)

    if not user or user["balance"] < 1:
        text = (
            "⚠️ <b>НЕДОСТАТОЧНО СРЕДСТВ</b>\n"
            "────────────────────────\n"
            "На вашем счёте СБП <b>0 ⭐️</b>.\n"
            "Пополните счёт звёздами, чтобы совершать мгновенные переводы другим пользователям!"
        )
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text, reply_markup=get_back_button())
            await event.answer()
        else:
            await event.answer(text, reply_markup=get_back_button())
        return

    text = (
        "💸 <b>ПЕРЕВОД ПО СБП</b>\n"
        "────────────────────────\n"
        f"Ваш доступный баланс: <b>{user['balance']:,} ⭐️</b>\n\n"
        "Введите реквизиты получателя:\n"
        "• <b>@username</b> (например, <code>@durov</code>)\n"
        "• <b>Telegram ID</b> (например, <code>123456789</code>)\n"
        "• <b>Номер счёта СБП</b> (например, <code>СБП-1234-5678</code>)"
    )

    await state.set_state(TransferState.waiting_for_recipient)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_cancel_kb())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_cancel_kb())


@router.message(TransferState.waiting_for_recipient)
async def process_transfer_recipient(message: Message, state: FSMContext):
    query = message.text.strip()
    sender_id = message.from_user.id
    sender = await db.get_user(sender_id)

    recipient = None
    recipient_type = None
    recipient_label = None

    # Try by SBP account number
    if query.upper().startswith("СБП-") or query.upper().startswith("SBP-"):
        recipient = await db.get_user_by_account(query)
        if recipient:
            recipient_type = "direct"
            r_name = mask_name(recipient['first_name'], recipient['last_name'])
            recipient_label = f"{r_name} ({recipient['account_number']})"

    # Try by Telegram ID
    elif query.isdigit():
        target_id = int(query)
        if target_id == sender_id:
            await message.answer("⚠️ Вы не можете перевести звёзды самому себе. Введите другого получателя:", reply_markup=get_cancel_kb())
            return
        recipient = await db.get_user(target_id)
        if recipient:
            recipient_type = "direct"
            r_name = mask_name(recipient['first_name'], recipient['last_name'])
            recipient_label = f"{r_name} (ID {target_id})"
        else:
            # Try to resolve via bot get_chat
            try:
                chat = await message.bot.get_chat(target_id)
                recipient_type = "id_unregistered"
                recipient_label = f"{chat.first_name} (ID {target_id})"
            except Exception:
                recipient_type = "id_unregistered"
                recipient_label = f"Пользователь ID {target_id}"

    # Try by @username
    else:
        clean_u = query.lstrip("@").lower()
        if sender.get("username") and sender["username"].lower() == clean_u:
            await message.answer("⚠️ Вы не можете перевести звёзды самому себе. Введите другого получателя:", reply_markup=get_cancel_kb())
            return

        recipient = await db.get_user_by_username(clean_u)
        if recipient:
            recipient_type = "direct"
            r_name = mask_name(recipient['first_name'], recipient['last_name'])
            recipient_label = f"{r_name} (@{clean_u})"
        else:
            # Unregistered username
            recipient_type = "username_pending"
            recipient_label = f"@{clean_u}"

    if recipient and recipient["user_id"] == sender_id:
        await message.answer("⚠️ Вы не можете перевести звёзды самому себе. Введите другого получателя:", reply_markup=get_cancel_kb())
        return

    # Store recipient in state
    await state.update_data(
        recipient=recipient,
        recipient_type=recipient_type,
        recipient_label=recipient_label,
        recipient_raw=query
    )

    await state.set_state(TransferState.waiting_for_amount)
    await message.answer(
        f"👤 <b>Получатель:</b> {recipient_label}\n"
        f"💰 <b>Ваш баланс:</b> {sender['balance']:,} ⭐️\n\n"
        "Выберите или введите сумму перевода в ⭐️ (от 1 ⭐️):",
        reply_markup=get_quick_amount_kb(sender['balance'])
    )


@router.callback_query(F.data.startswith("set_amount:"), TransferState.waiting_for_amount)
async def process_quick_amount(callback: CallbackQuery, state: FSMContext):
    amount = int(callback.data.split(":")[1])
    await handle_amount_input(callback.message, state, amount, callback=callback)


@router.message(TransferState.waiting_for_amount)
async def process_transfer_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace("⭐️", "").replace(" ", "")
    if not text.isdigit():
        await message.answer("⚠️ Введите корректную сумму целым числом (например, <code>10</code>):", reply_markup=get_cancel_kb())
        return

    amount = int(text)
    await handle_amount_input(message, state, amount)


async def handle_amount_input(message: Message, state: FSMContext, amount: int, callback: CallbackQuery = None):
    sender_id = message.chat.id
    sender = await db.get_user(sender_id)

    if amount < 1:
        err = "⚠️ Минимальная сумма перевода по СБП — 1 ⭐️."
        if callback:
            await callback.answer(err, show_alert=True)
        else:
            await message.answer(err, reply_markup=get_cancel_kb())
        return

    if amount > sender["balance"]:
        err = f"⚠️ Недостаточно звёзд. Ваш баланс: {sender['balance']:,} ⭐️."
        if callback:
            await callback.answer(err, show_alert=True)
        else:
            await message.answer(err, reply_markup=get_cancel_kb())
        return

    await state.update_data(amount=amount)
    await state.set_state(TransferState.waiting_for_comment)

    prompt = (
        f"💰 Сумма перевода: <b>{amount:,} ⭐️</b>\n\n"
        "💬 Введите сообщение или комментарий к переводу (например, <i>«За пиццу 🍕»</i> или <i>«Возврат долга»</i>)\n"
        "или нажмите кнопку, чтобы перевести без сообщения:"
    )

    if callback:
        await callback.message.edit_text(prompt, reply_markup=get_skip_comment_kb())
        await callback.answer()
    else:
        await message.answer(prompt, reply_markup=get_skip_comment_kb())


@router.callback_query(F.data == "skip_comment", TransferState.waiting_for_comment)
async def process_skip_comment(callback: CallbackQuery, state: FSMContext):
    await state.update_data(comment=None)
    await show_confirmation(callback.message, state, is_callback=True)
    await callback.answer()


@router.message(TransferState.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    comment = message.text.strip()[:100]
    await state.update_data(comment=comment)
    await show_confirmation(message, state, is_callback=False)


async def show_confirmation(message: Message, state: FSMContext, is_callback: bool = False):
    data = await state.get_data()
    sender_id = message.chat.id
    sender = await db.get_user(sender_id)

    recipient_label = data["recipient_label"]
    amount = data["amount"]
    comment = data.get("comment")

    text = format_transfer_confirmation(sender, recipient_label, amount, comment)
    await state.set_state(TransferState.confirm_transfer)

    if is_callback:
        await message.edit_text(text, reply_markup=get_confirm_transfer_kb())
    else:
        await message.answer(text, reply_markup=get_confirm_transfer_kb())


@router.callback_query(F.data == "confirm_transfer_btn", TransferState.confirm_transfer)
async def execute_transfer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sender_id = callback.from_user.id
    sender = await db.get_user(sender_id)

    amount = data["amount"]
    comment = data.get("comment")
    recipient = data.get("recipient")
    recipient_type = data.get("recipient_type")
    recipient_label = data["recipient_label"]

    if sender["balance"] < amount:
        await callback.answer("⚠️ Недостаточно средств для совершения перевода.", show_alert=True)
        await state.clear()
        return

    sender_label = f"@{sender['username']}" if sender.get("username") else f"{sender['first_name']} (ID {sender['user_id']})"

    if recipient_type == "direct" and recipient:
        res = await db.direct_transfer(sender_id, recipient["user_id"], amount, comment)
        if not res:
            await callback.answer("⚠️ Ошибка транзакции. Попробуйте снова.", show_alert=True)
            await state.clear()
            return

        trx_id = res["trx_id"]
        receipt = format_electronic_receipt(
            trx_id=trx_id,
            op_type="Перевод через СБП",
            amount=amount,
            sender_label=sender_label,
            recipient_label=recipient_label,
            comment=comment,
            dt_str=res["created_at"]
        )

        await callback.message.edit_text(
            f"✅ <b>ПЕРЕВОД УСПЕШНО ВЫПОЛНЕН!</b>\n\n{receipt}",
            reply_markup=get_back_button()
        )

        # Notify recipient
        try:
            r_receipt = format_electronic_receipt(
                trx_id=trx_id,
                op_type="Входящий перевод СБП",
                amount=amount,
                sender_label=sender_label,
                recipient_label=recipient_label,
                comment=comment,
                dt_str=res["created_at"]
            )
            await callback.bot.send_message(
                recipient["user_id"],
                f"⚡️ <b>ВХОДЯЩИЙ ПЕРЕВОД ПО СБП!</b>\n\n"
                f"Вам зачислено <b>+{amount:,} ⭐️</b> на счёт СБП.\n\n{r_receipt}"
            )
        except Exception:
            pass

    else:
        # Username pending transfer
        clean_u = data["recipient_raw"].lstrip("@").lower()
        res = await db.pending_transfer(sender_id, clean_u, amount, comment)
        if not res:
            await callback.answer("⚠️ Ошибка транзакции. Попробуйте снова.", show_alert=True)
            await state.clear()
            return

        trx_id = res["trx_id"]
        receipt = format_electronic_receipt(
            trx_id=trx_id,
            op_type="Перевод через СБП (в обработке)",
            amount=amount,
            sender_label=sender_label,
            recipient_label=f"@{clean_u}",
            comment=comment,
            dt_str=res["created_at"]
        )

        await callback.message.edit_text(
            f"✅ <b>ПЕРЕВОД ОТПРАВЛЕН!</b>\n\n"
            f"Звёзды зарезервированы в СБП. Как только <b>@{clean_u}</b> запустит бота @sbpbot, "
            f"перевод в размере <b>+{amount:,} ⭐️</b> будет зачислен на его баланс мгновенно!\n\n"
            f"{receipt}",
            reply_markup=get_back_button()
        )

    await state.clear()
    await callback.answer()
