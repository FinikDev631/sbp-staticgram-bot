import logging
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
from keyboards.cheque_kb import get_inline_claim_kb, get_inline_bill_kb, get_inline_bill_confirm_kb

logger = logging.getLogger("sbp_bot.inline")
router = Router()


async def edit_inline_or_message_reply_markup(callback: CallbackQuery, reply_markup):
    """Safely edits reply markup for both standard messages and inline messages."""
    try:
        if callback.inline_message_id:
            await callback.bot.edit_message_reply_markup(
                inline_message_id=callback.inline_message_id,
                reply_markup=reply_markup
            )
        elif callback.message:
            await callback.message.edit_reply_markup(reply_markup=reply_markup)
    except Exception as e:
        logger.warning(f"Could not edit reply markup: {e}")


async def edit_inline_or_message_text(callback: CallbackQuery, text: str, reply_markup=None):
    """Safely edits message text for both standard messages and inline messages."""
    try:
        if callback.inline_message_id:
            await callback.bot.edit_message_text(
                text=text,
                inline_message_id=callback.inline_message_id,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        elif callback.message:
            await callback.message.edit_text(text=text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Could not edit message text: {e}")

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
            rec_u = cheque.get("recipient_username")
            rec_label = f"@{rec_u}" if rec_u and str(rec_u).strip().lower() not in ("none", "null", "") else None
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
            rec_u = ch.get("recipient_username")
            rec_label = f"@{rec_u}" if rec_u and str(rec_u).strip().lower() not in ("none", "null", "") else None
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
    try:
        data_parts = callback.data.split(":")
        if len(data_parts) < 2:
            try:
                await callback.answer("Некорректный идентификатор чека.", show_alert=True)
            except Exception:
                await callback.answer()
            return

        cheque_id = data_parts[1]
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

            try:
                await callback.answer(f"⚡️ Получено: +{amount:,} ⭐️", show_alert=True)
            except Exception:
                try:
                    await callback.answer(f"+{amount:,} ⭐️")
                except Exception:
                    pass

            updated_text = format_cheque_claimed_message(
                amount=amount,
                creator_label=creator_label,
                claimer_label=claimer_label,
                comment=res.get("comment")
            )
            await edit_inline_or_message_text(callback, updated_text, reply_markup=None)

            try:
                await callback.bot.send_message(
                    res["creator_id"],
                    f"🎉 Пользователь {claimer_label} забрал ваш чек на <b>{amount:,} ⭐️</b>"
                )
            except Exception:
                pass

        elif status == "self_claim":
            alert_text = (
                "⚠️ Это ваш собственный чек.\n\n"
                "Вы создатель этого чека и не можете забрать его сами — "
                "он предназначен для других участников чата!\n\n"
                "💡 Чтобы вернуть звёзды на баланс, аннулируйте чек в Mini App или боте."
            )
            try:
                await callback.answer(alert_text, show_alert=True)
            except Exception:
                try:
                    await callback.answer("Это ваш собственный чек.")
                except Exception:
                    pass

        elif status == "already_claimed":
            try:
                await callback.answer("❌ Этот чек уже активирован.", show_alert=True)
            except Exception:
                try:
                    await callback.answer("Чек уже активирован.")
                except Exception:
                    pass

        elif status == "restricted":
            try:
                await callback.answer(f"🔒 Этот чек предназначен только для @{res.get('expected')}.", show_alert=True)
            except Exception:
                try:
                    await callback.answer(f"Только для @{res.get('expected')}.")
                except Exception:
                    pass

        else:
            try:
                await callback.answer("Чек не найден или уже аннулирован создателем.", show_alert=True)
            except Exception:
                try:
                    await callback.answer("Чек не найден.")
                except Exception:
                    pass

    except Exception as e:
        logger.exception(f"Unhandled error in process_claim_inline_cheque: {e}")
        try:
            await callback.answer("⚠️ Ошибка при обработке чека. Попробуйте еще раз.", show_alert=True)
        except Exception:
            try:
                await callback.answer()
            except Exception:
                pass


@router.callback_query(F.data == "ignore_action")
async def process_ignore_action(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("ask_pay:") | F.data.startswith("pay_bill:"))
async def process_ask_pay_inline_bill(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        creator_id = int(parts[1])
        amount = int(parts[2])

        payer_id = callback.from_user.id
        if payer_id == creator_id:
            try:
                await callback.answer("Нельзя оплатить собственный счёт.", show_alert=True)
            except Exception:
                await callback.answer("Нельзя оплатить собственный счёт.")
            return

        payer = await db.get_user(payer_id)
        if not payer or payer["balance"] < amount:
            bal = payer['balance'] if payer else 0
            try:
                await callback.answer(f"Недостаточно звёзд на балансе. Ваш баланс: {bal:,} ⭐️.", show_alert=True)
            except Exception:
                await callback.answer("Недостаточно звёзд.")
            return

        creator = await db.get_user(creator_id)
        creator_label = f"@{creator['username']}" if creator and creator.get("username") else (creator.get("first_name") if creator else f"ID {creator_id}")
        payer_label = f"@{payer['username']}" if payer.get("username") else f"{payer['first_name']}"

        confirm_text = (
            f"⚠️ <b>Подтверждение платежа</b>\n\n"
            f"Вы действительно хотите заплатить <b>{amount:,} ⭐️</b> получателю {creator_label}?\n\n"
            f"Плательщик: {payer_label}\n"
            f"Подтвердите отправку перевода:"
        )

        await edit_inline_or_message_text(
            callback,
            text=confirm_text,
            reply_markup=get_inline_bill_confirm_kb(creator_id, amount, payer_id)
        )
        try:
            await callback.answer()
        except Exception:
            pass
    except Exception as e:
        logger.exception(f"Error in process_ask_pay_inline_bill: {e}")
        try:
            await callback.answer("Ошибка при обработке запроса.", show_alert=True)
        except Exception:
            try:
                await callback.answer()
            except Exception:
                pass


@router.callback_query(F.data.startswith("conf_pay:"))
async def process_confirm_pay_inline_bill(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        creator_id = int(parts[1])
        amount = int(parts[2])
        expected_payer_id = int(parts[3])

        actual_payer_id = callback.from_user.id
        if actual_payer_id != expected_payer_id:
            try:
                await callback.answer("Подтверждение открыто для другого пользователя.", show_alert=True)
            except Exception:
                await callback.answer()
            return

        payer = await db.get_user(actual_payer_id)
        if not payer or payer["balance"] < amount:
            bal = payer['balance'] if payer else 0
            try:
                await callback.answer(f"Недостаточно звёзд. Ваш баланс: {bal:,} ⭐️.", show_alert=True)
            except Exception:
                await callback.answer("Недостаточно звёзд.")
            return

        comment = f"Оплата счёта в чате на {amount:,} ⭐️"
        res = await db.direct_transfer(actual_payer_id, creator_id, amount, comment)
        if not res:
            try:
                await callback.answer("Ошибка при обработке платежа.", show_alert=True)
            except Exception:
                await callback.answer()
            return

        payer_label = f"@{payer['username']}" if payer.get("username") else f"{payer['first_name']}"
        creator = await db.get_user(creator_id)
        creator_label = f"@{creator['username']}" if creator and creator.get("username") else (creator.get("first_name") if creator else f"ID {creator_id}")

        try:
            await callback.answer(f"Оплата на {amount:,} ⭐️ успешно выполнена!", show_alert=True)
        except Exception:
            try:
                await callback.answer(f"Оплачено {amount:,} ⭐️")
            except Exception:
                pass

        updated_text = (
            f"✅ <b>Счёт на {amount:,} ⭐️ оплачен</b>\n"
            f"Получатель: {creator_label}\n"
            f"Оплатил: {payer_label}\n"
            f"Квитанция: <code>#{res['trx_id']}</code>"
        )
        await edit_inline_or_message_text(callback, updated_text, reply_markup=None)

        try:
            await callback.bot.send_message(
                creator_id,
                f"⚡️ Пользователь {payer_label} оплатил ваш счёт на <b>+{amount:,} ⭐️</b>\n"
                f"Квитанция: <code>#{res['trx_id']}</code>"
            )
        except Exception:
            pass

        try:
            await callback.bot.send_message(
                actual_payer_id,
                f"✅ <b>Счёт успешно оплачен</b>\n\n"
                f"Получатель: {creator_label}\n"
                f"Списано: <b>{amount:,} ⭐️</b>\n"
                f"Квитанция: <code>#{res['trx_id']}</code>"
            )
        except Exception:
            pass
    except Exception as e:
        logger.exception(f"Error in process_confirm_pay_inline_bill: {e}")
        try:
            await callback.answer("Ошибка при проведении платежа.", show_alert=True)
        except Exception:
            try:
                await callback.answer()
            except Exception:
                pass


@router.callback_query(F.data.startswith("cancel_pay:"))
async def process_cancel_pay_inline_bill(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        creator_id = int(parts[1])
        amount = int(parts[2])

        creator = await db.get_user(creator_id)
        creator_label = f"@{creator['username']}" if creator and creator.get("username") else (creator.get("first_name") if creator else f"ID {creator_id}")

        original_text = (
            f"<b>Счёт на {amount:,} ⭐️</b>\n"
            f"Получатель: {creator_label}\n\n"
            f"Нажмите кнопку для оплаты со счёта СБП:"
        )

        await edit_inline_or_message_text(
            callback,
            text=original_text,
            reply_markup=get_inline_bill_kb(creator_id, amount)
        )
        try:
            await callback.answer("Оплата отменена.")
        except Exception:
            pass
    except Exception as e:
        logger.exception(f"Error in process_cancel_pay_inline_bill: {e}")
        try:
            await callback.answer()
        except Exception:
            pass
