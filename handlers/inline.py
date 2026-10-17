from aiogram import Router, F
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    CallbackQuery
)

import database as db
from utils.formatters import (
    format_cheque_message,
    format_cheque_claimed_message,
    mask_name
)
from keyboards.cheque_kb import get_inline_claim_kb, get_inline_bill_kb

router = Router()

@router.inline_query()
async def process_inline_query(query: InlineQuery):
    user_id = query.from_user.id
    raw_text = query.query.strip()
    user = await db.get_user(user_id)

    results = []

    # 1. Specific cheque by ID (@sbpbot ch_abc123)
    if raw_text.startswith("ch_"):
        cheque = await db.get_cheque(raw_text)
        if cheque and cheque["status"] == "active":
            creator_label = f"@{cheque['creator_username']}" if cheque.get("creator_username") else f"id{cheque['creator_id']}"
            rec_label = f"@{cheque['recipient_username']}" if cheque.get("recipient_username") else None
            msg_text = format_cheque_message(
                amount=cheque["amount"],
                creator_label=creator_label,
                recipient_label=rec_label,
                comment=cheque.get("comment")
            )
            results.append(InlineQueryResultArticle(
                id=f"ch_{cheque['cheque_id']}",
                title=f"Чек на {cheque['amount']:,} ⭐️",
                description=f"От {creator_label}",
                input_message_content=InputTextMessageContent(message_text=msg_text, parse_mode="HTML"),
                reply_markup=get_inline_claim_kb(cheque["cheque_id"], cheque["amount"])
            ))
            await query.answer(results, is_personal=True, cache_time=1)
            return

    # 2. User's active cheques
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
                title=f"Отправить чек на {ch['amount']:,} ⭐️",
                description=f"Для: {rec_label or 'всех'}",
                input_message_content=InputTextMessageContent(message_text=msg_text, parse_mode="HTML"),
                reply_markup=get_inline_claim_kb(ch["cheque_id"], ch["amount"])
            ))

    # 3. Bill / Invoice query: "bill 50" or numbers
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
            f"<b>Счёт на {amount_parsed:,} ⭐️</b>\n"
            f"Получатель: {sender_name}\n\n"
            f"Нажмите кнопку для оплаты со счёта СБП:"
        )
        results.append(InlineQueryResultArticle(
            id=f"bill_{amount_parsed}_{user_id}",
            title=f"Запросить {amount_parsed:,} ⭐️",
            description=f"Отправить счёт в чат",
            input_message_content=InputTextMessageContent(message_text=bill_text, parse_mode="HTML"),
            reply_markup=get_inline_bill_kb(user_id, amount_parsed)
        ))

    # Default preset bills
    default_amounts = [10, 25, 50, 100]
    sender_name = mask_name(query.from_user.first_name or "Клиент", query.from_user.last_name)
    for amt in default_amounts:
        bill_text = (
            f"<b>Счёт на {amt:,} ⭐️</b>\n"
            f"Получатель: {sender_name}\n\n"
            f"Нажмите кнопку для оплаты со счёта СБП:"
        )
        results.append(InlineQueryResultArticle(
            id=f"quick_bill_{amt}_{user_id}",
            title=f"Счёт на {amt:,} ⭐️",
            description=f"Запросить {amt:,} ⭐️ в чат",
            input_message_content=InputTextMessageContent(message_text=bill_text, parse_mode="HTML"),
            reply_markup=get_inline_bill_kb(user_id, amt)
        ))

    await query.answer(results, is_personal=True, cache_time=1)


@router.callback_query(F.data.startswith("claim_ch:"))
async def process_claim_inline_cheque(callback: CallbackQuery):
    cheque_id = callback.data.split(":")[1]
    user_id = callback.from_user.id
    username = callback.from_user.username
    first_name = callback.from_user.first_name or "Клиент"

    user = await db.get_user(user_id)
    if not user:
        user = await db.get_or_create_user(user_id, username, first_name, callback.from_user.last_name)

    res = await db.claim_cheque(cheque_id, user_id, username, first_name)
    status = res.get("status")

    if status == "ok":
        amount = res["amount"]
        creator_label = f"@{res['creator_username']}" if res.get("creator_username") else f"id{res['creator_id']}"
        claimer_label = f"@{username}" if username else f"{first_name}"

        await callback.answer(f"Получено: +{amount:,} ⭐️", show_alert=True)

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

        try:
            await callback.bot.send_message(
                res["creator_id"],
                f"Пользователь {claimer_label} забрал ваш чек на <b>{amount:,} ⭐️</b>"
            )
        except Exception:
            pass

    elif status == "self_claim":
        await callback.answer("Это ваш собственный чек.", show_alert=True)
    elif status == "already_claimed":
        await callback.answer("Чек уже активирован.", show_alert=True)
    elif status == "restricted":
        await callback.answer(f"Чек только для @{res.get('expected')}.", show_alert=True)
    else:
        await callback.answer("Чек не найден или аннулирован.", show_alert=True)


@router.callback_query(F.data.startswith("pay_bill:"))
async def process_pay_inline_bill(callback: CallbackQuery):
    parts = callback.data.split(":")
    creator_id = int(parts[1])
    amount = int(parts[2])

    payer_id = callback.from_user.id
    if payer_id == creator_id:
        await callback.answer("Нельзя оплатить собственный счёт.", show_alert=True)
        return

    payer = await db.get_user(payer_id)
    if not payer or payer["balance"] < amount:
        bal = payer['balance'] if payer else 0
        await callback.answer(f"Недостаточно звёзд. Баланс: {bal:,} ⭐️.", show_alert=True)
        return

    comment = f"Оплата счёта в чате на {amount:,} ⭐️"
    res = await db.direct_transfer(payer_id, creator_id, amount, comment)
    if not res:
        await callback.answer("Ошибка при оплате.", show_alert=True)
        return

    payer_label = f"@{payer['username']}" if payer.get("username") else f"{payer['first_name']}"
    await callback.answer(f"Счёт на {amount:,} ⭐️ оплачен!", show_alert=True)

    try:
        updated_text = (
            f"✅ <b>Счёт на {amount:,} ⭐️ оплачен</b>\n"
            f"Оплатил: {payer_label}"
        )
        await callback.message.edit_text(updated_text, reply_markup=None)
    except Exception:
        pass

    try:
        await callback.bot.send_message(
            creator_id,
            f"Пользователь {payer_label} оплатил ваш счёт на <b>+{amount:,} ⭐️</b>"
        )
    except Exception:
        pass
