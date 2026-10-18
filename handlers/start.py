from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from utils.formatters import format_sbp_card
from keyboards.main_kb import get_main_menu_inline, get_back_button

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name or "Клиент"
    last_name = message.from_user.last_name

    args = message.text.split(maxsplit=1)
    deep_link = args[1] if len(args) > 1 else None

    user = await db.get_or_create_user(user_id, username, first_name, last_name)

    if deep_link and deep_link.startswith("ch_"):
        cheque_id = deep_link
        claim_res = await db.claim_cheque(cheque_id, user_id, username, first_name)
        status = claim_res.get("status")

        if status == "ok":
            amount = claim_res["amount"]
            creator_label = f"@{claim_res['creator_username']}" if claim_res.get("creator_username") else f"id{claim_res['creator_id']}"
            await message.answer(
                f"✅ Чек активирован\n\n"
                f"Получено: <b>+{amount:,} ⭐️</b> от {creator_label}\n"
                f"Баланс: <b>{user['balance'] + amount:,} ⭐️</b>",
                reply_markup=get_back_button()
            )
            try:
                claimer_label = f"@{username}" if username else f"{first_name}"
                await message.bot.send_message(
                    claim_res["creator_id"],
                    f"Чек на <b>{amount:,} ⭐️</b> активирован пользователем {claimer_label}"
                )
            except Exception:
                pass
            return
        elif status == "self_claim":
            await message.answer(
                "⚠️ <b>Это ваш собственный чек</b>\n\n"
                "Вы создатель этого чека и не можете забрать его сами — он предназначен для других пользователей!\n\n"
                "💡 Чтобы вернуть звёзды на баланс, аннулируйте чек в разделе «Чеки» бота или в Mini App.",
                reply_markup=get_back_button()
            )
            return
        elif status == "already_claimed":
            await message.answer("Этот чек уже активирован.", reply_markup=get_back_button())
            return
        elif status == "restricted":
            await message.answer(
                f"Этот чек предназначен только для @{claim_res.get('expected')}.",
                reply_markup=get_back_button()
            )
            return
        else:
            await message.answer("Чек не найден или аннулирован.", reply_markup=get_back_button())
            return

    reserved = await db.get_user_reserved_summary(user_id)
    rank_info = await db.get_user_rank(user_id)
    text = format_sbp_card(user, reserved, rank_info)
    await message.answer(text, reply_markup=get_main_menu_inline(user_id, reserved["total_reserved"]))

    if user.get("claimed_pending"):
        for cp in user["claimed_pending"]:
            s_label = f"@{cp['sender_username']}" if cp.get("sender_username") else f"ID {cp['sender_id']}"
            await message.answer(
                f"🎉 <b>Вам начислен отложенный перевод СБП!</b>\n\n"
                f"• Сумма: <b>+{cp['amount']:,} ⭐️</b>\n"
                f"• Отправитель: {s_label}\n"
                f"• Баланс счёта СБП: <b>{user['balance']:,} ⭐️</b>\n\n"
                f"<i>Вы можете перевести их, создать чек или вывести на баланс своего аккаунта StaticGram через кнопку «📤 Вывести».</i>"
            )
            try:
                rec_label = f"@{username}" if username else f"{first_name}"
                await message.bot.send_message(
                    cp["sender_id"],
                    f"✅ <b>Перевод доставлен!</b>\n\n"
                    f"Пользователь {rec_label} открыл бота, и ваш перевод на <b>{cp['amount']:,} ⭐️</b> успешно зачислен на его баланс СБП!"
                )
            except Exception:
                pass


@router.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    if not user:
        user = await db.get_or_create_user(
            user_id,
            callback.from_user.username,
            callback.from_user.first_name or "Клиент",
            callback.from_user.last_name
        )

    reserved = await db.get_user_reserved_summary(user_id)
    rank_info = await db.get_user_rank(user_id)
    text = format_sbp_card(user, reserved, rank_info)
    try:
        await callback.message.edit_text(text, reply_markup=get_main_menu_inline(user_id, reserved["total_reserved"]))
    except Exception:
        await callback.message.answer(text, reply_markup=get_main_menu_inline(user_id, reserved["total_reserved"]))
    await callback.answer()


@router.callback_query(F.data == "cancel_action")
async def cb_cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    reserved = await db.get_user_reserved_summary(user_id)
    text = format_sbp_card(user, reserved)
    try:
        await callback.message.edit_text(text, reply_markup=get_main_menu_inline(user_id, reserved["total_reserved"]))
    except Exception:
        await callback.message.answer(text, reply_markup=get_main_menu_inline(user_id, reserved["total_reserved"]))
    await callback.answer()


@router.callback_query(F.data == "menu_reserved")
async def cb_menu_reserved(callback: CallbackQuery):
    user_id = callback.from_user.id
    items = await db.get_user_reserved_items(user_id)
    cheques = items["cheques"]
    pending = items["pending"]

    if not cheques and not pending:
        await callback.answer("У вас нет зарезервированных средств.", show_alert=True)
        user = await db.get_user(user_id)
        reserved = await db.get_user_reserved_summary(user_id)
        await callback.message.edit_text(format_sbp_card(user, reserved), reply_markup=get_main_menu_inline(user_id, 0))
        return

    text = "⏳ <b>Ваши зарезервированные средства</b>\n\n"
    text += "<i>Здесь находятся звёзды, которые временно списаны с баланса, но ещё не были забраны. Вы можете вернуть их на свой счёт в 1 клик:</i>\n\n"

    rows = []

    if cheques:
        text += "<b>🧾 Активные чеки:</b>\n"
        for ch in cheques:
            rec = f"@{ch['recipient_username']}" if ch.get('recipient_username') else "любой"
            text += f"• Чек <code>{ch['cheque_id']}</code>: <b>{ch['amount']:,} ⭐️</b> ({rec})\n"
            rows.append([
                InlineKeyboardButton(
                    text=f"↩️ Вернуть чек на {ch['amount']:,} ⭐️",
                    callback_data=f"cancel_res_ch:{ch['cheque_id']}"
                )
            ])
        text += "\n"

    if pending:
        text += "<b>⏳ Отложенные переводы:</b>\n"
        for pt in pending:
            text += f"• Перевод <code>{pt['trx_id']}</code>: <b>{pt['amount']:,} ⭐️</b> (для @{pt['recipient_username']})\n"
            rows.append([
                InlineKeyboardButton(
                    text=f"↩️ Вернуть перевод на {pt['amount']:,} ⭐️",
                    callback_data=f"cancel_res_pt:{pt['trx_id']}"
                )
            ])

    rows.append([InlineKeyboardButton(text="← В главное меню", callback_data="back_to_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_res_ch:"))
async def cb_cancel_res_cheque(callback: CallbackQuery):
    user_id = callback.from_user.id
    cheque_id = callback.data.split(":", 1)[1]
    ok = await db.cancel_cheque(cheque_id, user_id)
    if ok:
        await callback.answer("Чек аннулирован, звёзды возвращены на ваш баланс!", show_alert=True)
    else:
        await callback.answer("Чек уже активирован или не существует.", show_alert=True)
    await cb_menu_reserved(callback)


@router.callback_query(F.data.startswith("cancel_res_pt:"))
async def cb_cancel_res_pending(callback: CallbackQuery):
    user_id = callback.from_user.id
    trx_id = callback.data.split(":", 1)[1]
    pt = await db.cancel_pending_transfer(trx_id, sender_id=user_id)
    if pt:
        await callback.answer(f"Перевод отменён, {pt['amount']:,} ⭐️ возвращены на ваш баланс!", show_alert=True)
    else:
        await callback.answer("Перевод уже получен или отменён.", show_alert=True)
    await cb_menu_reserved(callback)


@router.callback_query(F.data == "menu_ranks")
@router.message(Command("rank"))
@router.message(Command("ranks"))
async def show_user_rank(event: Message | CallbackQuery):
    user_id = event.from_user.id
    user = await db.get_user(user_id)
    if not user:
        user = await db.get_or_create_user(
            user_id,
            event.from_user.username,
            event.from_user.first_name or "Клиент",
            event.from_user.last_name
        )
    rank_info = await db.get_user_rank(user_id)
    from utils.ranks import format_rank_view_text
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    text = format_rank_view_text(user, rank_info)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💸 Сделать перевод", callback_data="menu_transfer"),
            InlineKeyboardButton(text="📥 Пополнить", callback_data="menu_deposit")
        ],
        [
            InlineKeyboardButton(text="← В главное меню", callback_data="back_to_menu")
        ]
    ])
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb)


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>Команды бота:</b>\n\n"
        "/start — Главное меню\n"
        "/pay — Перевести звёзды\n"
        "/deposit — Пополнить баланс\n"
        "/withdraw — Вывести на аккаунт\n"
        "/cheque — Создать чек\n"
        "/history — История операций\n"
        "/rank — Мой ранг и статус\n\n"
        '📢 Официальный канал: <a href="https://staticgram.top/sbpnews">@sbpnews</a>',
        reply_markup=get_back_button()
    )
