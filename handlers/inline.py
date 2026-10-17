import hashlib
from aiogram import Router, F
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

import database as db
from utils.formatters import (
    format_cheque_message,
    format_cheque_claimed_message,
    format_electronic_receipt,
    mask_name
)
from keyboards.cheque_kb import get_inline_claim_kb, get_inline_bill_kb

router = Router()

@router.inline_query()
async def process_inline_query(query: InlineQuery):
    user_id = query.from_user.id
    raw_text = query.query.strip()
    user = await db.get_user(user_id)
    balance = user["balance"] if user else 0

    results = []

    # 1. Search for specific cheque (e.g. @sbpbot ch_abc123)
    if raw_text.startswith("ch_"):
        cheque = await db.get_cheque(raw_text)
        if cheque and cheque["status"] == "active":
            creator_label = f"@{cheque['creator_username']}" if cheque.get("creator_username") else f"ID {cheque['creator_id']}"
            rec_label = f"@{cheque['recipient_username']}" if cheque.get("recipient_username") else None
            msg_text = format_cheque_message(
                amount=cheque["amount"],
                creator_label=creator_label,
                recipient_label=rec_label,
                comment=cheque.get("comment")
            )
            results.append(InlineQueryResultArticle(
                id=f"ch_{cheque['cheque_id']}",
                title=f"⚡️ Чек СБП на {cheque['amount']:,} ⭐️",
                description=f"От {creator_label} • Нажмите, чтобы отправить перевод в чат",
                input_message_content=InputTextMessageContent(message_text=msg_text, parse_mode="HTML"),
                reply_markup=get_inline_claim_kb(cheque["cheque_id"], cheque["amount"])
            ))
            await query.answer(results, is_personal=True, cache_time=1)
            return

    # 2. Show active user cheques
    if user:
        active_cheques = await db.get_active_cheques_by_user(user_id)
        for ch in active_cheques[:5]:
            rec_label = f"@{ch['recipient_username']}" if ch.get("recipient_username") else None
            creator_label = f"@{user['username']}" if user.get("username") else f"{user['first_name']}"
            msg_text = format_cheque_message(
                amount=ch["amount"],
                creator_label=creator_label,
                recipient_label=rec_label,
                comment=ch.get("comment")
            )
            results.append(InlineQueryResultArticle(
                id=f"active_{ch['cheque_id']}",
                title=f"⚡️ Отправить чек на {ch['amount']:,} ⭐️",
                description=f"Ваш готовый чек ({rec_label or 'для всех'})",
                input_message_content=InputTextMessageContent(message_text=msg_text, parse_mode="HTML"),
                reply_markup=get_inline_claim_kb(ch["cheque_id"], ch["amount"])
            ))

    # 3. Bill / Invoice query: "bill 50" or "счет 50" or numbers
    amount_parsed = None
    if raw_text.isdigit():
        amount_parsed = int(raw_text)
    elif raw_text.lower().startswith("bill ") or raw_text.lower().startswith("счет ") or raw_text.lower().startswith("счёт "):
        parts = raw_text.split()
        if len(parts) > 1 and parts[1].isdigit():
            amount_parsed = int(parts[1])

    if amount_parsed and 1 <= amount_parsed <= 100000:
        sender_name = mask_name(query.from_user.first_name or "Клиент", query.from_user.last_name)
        bill_text = (
            "🧾 <b>СЧЁТ НА ОПЛАТУ ЧЕРЕЗ СБП</b>\n"
            "════════════════════════\n"
            f"👤 <b>Получатель:</b> {sender_name}\n"
            f"💰 <b>Сумма к оплате:</b> <b>{amount_parsed:,} ⭐️</b>\n"
            "🏦 <b>Банк:</b> StaticGram Stars СБП\n"
            "🏷 <b>Комиссия:</b> 0 ⭐️ (Бесплатно)\n"
            "════════════════════════\n"
            "<i>Нажмите кнопку ниже для быстрой оплаты со счёта СБП:</i>"
        )
        results.append(InlineQueryResultArticle(
            id=f"bill_{amount_parsed}_{user_id}",
            title=f"🧾 Запросить перевод на {amount_parsed:,} ⭐️",
            description=f"Отправить счёт на {amount_parsed:,} ⭐️ в этот чат",
            input_message_content=InputTextMessageContent(message_text=bill_text, parse_mode="HTML"),
            reply_markup=get_inline_bill_kb(user_id, amount_parsed)
        ))

    # 4. Standard default options if results are empty or list is small
    default_amounts = [10, 25, 50, 100]
    sender_name = mask_name(query.from_user.first_name or "Клиент", query.from_user.last_name)
    for amt in default_amounts:
        bill_text = (
            "🧾 <b>СЧЁТ НА ОПЛАТУ ЧЕРЕЗ СБП</b>\n"
            "════════════════════════\n"
            f"👤 <b>Получатель:</b> {sender_name}\n"
            f"💰 <b>Сумма к оплате:</b> <b>{amt:,} ⭐️</b>\n"
            "🏦 <b>Банк:</b> StaticGram Stars СБП\n"
            "🏷 <b>Комиссия:</b> 0 ⭐️ (Бесплатно)\n"
            "════════════════════════\n"
            "<i>Нажмите кнопку ниже для быстрой оплаты со счёта СБП:</i>"
        )
        results.append(InlineQueryResultArticle(
            id=f"quick_bill_{amt}_{user_id}",
            title=f"🧾 Счёт СБП на {amt:,} ⭐️",
            description=f"Запросить перевод на {amt:,} ⭐️ в чат",
            input_message_content=InputTextMessageContent(message_text=bill_text, parse_mode="HTML"),
            reply_markup=get_inline_bill_kb(user_id, amt)
        ))

    await query.answer(results, is_personal=True, cache_time=1)


# --- Handle inline button clicks ---

@router.callback_query(F.data.startswith("claim_ch:"))
async def process_claim_inline_cheque(callback: CallbackQuery):
    cheque_id = callback.data.split(":")[1]
    user_id = callback.from_user.id
    username = callback.from_user.username
    first_name = callback.from_user.first_name or "Клиент"

    # Ensure user exists in SBP database
    user = await db.get_user(user_id)
    if not user:
        user = await db.get_or_create_user(user_id, username, first_name, callback.from_user.last_name)

    res = await db.claim_cheque(cheque_id, user_id, username, first_name)
    status = res.get("status")

    if status == "ok":
        amount = res["amount"]
        creator_label = f"@{res['creator_username']}" if res.get("creator_username") else f"ID {res['creator_id']}"
        claimer_label = f"@{username}" if username else f"{first_name}"

        await callback.answer(f"⚡️ Вам зачислено +{amount:,} ⭐️ по СБП!", show_alert=True)

        # Update inline message in the chat
        updated_text = format_cheque_claimed_message(
            amount=amount,
            creator_label=creator_label,
            claimer_label=claimer_label,
            comment=res.get("comment")
        )
        try:
            await callback.message.edit_text(updated_text, reply_markup=None)
        except Exception:
            pass

        # Notify creator
        try:
            await callback.bot.send_message(
                res["creator_id"],
                f"⚡️ <b>Уведомление СБП:</b>\n"
                f"Пользователь {claimer_label} забрал(а) ваш перевод на <b>{amount:,} ⭐️</b>!"
            )
        except Exception:
            pass

    elif status == "self_claim":
        await callback.answer("⚠️ Вы не можете забрать собственный перевод.", show_alert=True)
    elif status == "already_claimed":
        await callback.answer("⚠️ Этот перевод уже был забран.", show_alert=True)
    elif status == "restricted":
        await callback.answer(f"⛔️ Этот перевод предназначен только для @{res.get('expected')}.", show_alert=True)
    else:
        await callback.answer("⚠️ Чек не найден или был аннулирован.", show_alert=True)


@router.callback_query(F.data.startswith("pay_bill:"))
async def process_pay_inline_bill(callback: CallbackQuery):
    parts = callback.data.split(":")
    creator_id = int(parts[1])
    amount = int(parts[2])

    payer_id = callback.from_user.id
    if payer_id == creator_id:
        await callback.answer("⚠️ Вы не можете оплатить собственный счёт.", show_alert=True)
        return

    payer = await db.get_user(payer_id)
    if not payer or payer["balance"] < amount:
        bal = payer['balance'] if payer else 0
        await callback.answer(
            f"⚠️ Недостаточно звёзд на счёте СБП.\nВаш баланс: {bal:,} ⭐️.\nОткройте @sbpbot для пополнения!",
            show_alert=True
        )
        return

    # Execute transfer
    comment = f"Оплата счёта СБП в чате на {amount:,} ⭐️"
    res = await db.direct_transfer(payer_id, creator_id, amount, comment)
    if not res:
        await callback.answer("⚠️ Ошибка транзакции. Попробуйте снова.", show_alert=True)
        return

    payer_label = f"@{payer['username']}" if payer.get("username") else f"{payer['first_name']}"
    await callback.answer(f"✅ Вы успешно оплатили счёт на {amount:,} ⭐️!", show_alert=True)

    # Edit chat message
    try:
        updated_text = (
            "✅ <b>СЧЁТ СБП УСПЕШНО ОПЛАЧЕН</b>\n"
            "════════════════════════\n"
            f"💰 <b>Сумма:</b> <b>{amount:,} ⭐️</b>\n"
            f"👤 <b>Оплатил:</b> {payer_label}\n"
            "🏦 <b>Банк:</b> StaticGram Stars СБП\n"
            "🟢 <b>Статус:</b> Исполнен (0 ⭐️ комиссия)\n"
            "════════════════════════\n"
            "⚡️ <i>Средства мгновенно поступили получателю.</i>"
        )
        await callback.message.edit_text(updated_text, reply_markup=None)
    except Exception:
        pass

    # Notify creator
    try:
        await callback.bot.send_message(
            creator_id,
            f"⚡️ <b>ВХОДЯЩИЙ ПЕРЕВОД ПО СБП:</b>\n"
            f"Пользователь {payer_label} оплатил ваш счёт на <b>+{amount:,} ⭐️</b>!"
        )
    except Exception:
        pass
