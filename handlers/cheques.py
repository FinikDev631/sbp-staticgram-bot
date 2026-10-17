from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

import database as db
from utils.states import ChequeState
from keyboards.cheque_kb import (
    get_cheque_menu_kb,
    get_cheque_recipient_choice_kb,
    get_cheque_created_kb
)
from keyboards.main_kb import get_cancel_kb, get_back_button
from keyboards.transfer_kb import get_quick_amount_kb, get_skip_comment_kb

router = Router()

@router.callback_query(F.data == "menu_cheque")
@router.message(Command("cheque"))
async def start_cheque_menu(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    user = await db.get_user(user_id)

    text = (
        f"<b>Чеки СБП</b>\n\n"
        f"Доступно: <b>{user['balance']:,} ⭐️</b>\n\n"
        f"Чек можно отправить в любой чат или личные сообщения. "
        f"Получатель активирует его кнопкой в чате."
    )

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_cheque_menu_kb())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_cheque_menu_kb())


@router.callback_query(F.data == "cheque_create")
async def create_cheque_prompt(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)

    if not user or user["balance"] < 1:
        await callback.answer("Недостаточно звёзд на счёте.", show_alert=True)
        return

    await state.set_state(ChequeState.waiting_for_amount)
    await callback.message.edit_text(
        f"Доступно: <b>{user['balance']:,} ⭐️</b>\n\n"
        "Укажите сумму чека:",
        reply_markup=get_quick_amount_kb(user['balance'])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_amount:"), ChequeState.waiting_for_amount)
async def process_cheque_quick_amount(callback: CallbackQuery, state: FSMContext):
    amount = int(callback.data.split(":")[1])
    await handle_cheque_amount(callback.message, state, amount, callback=callback)


@router.message(ChequeState.waiting_for_amount)
async def process_cheque_custom_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace("⭐️", "").replace(" ", "")
    if not text.isdigit():
        await message.answer("Введите целое число звёзд:", reply_markup=get_cancel_kb())
        return

    amount = int(text)
    await handle_cheque_amount(message, state, amount)


async def handle_cheque_amount(message: Message, state: FSMContext, amount: int, callback: CallbackQuery = None):
    user_id = message.chat.id
    user = await db.get_user(user_id)

    if amount < 1:
        err = "Минимальная сумма — 1 ⭐️."
        if callback:
            await callback.answer(err, show_alert=True)
        else:
            await message.answer(err, reply_markup=get_cancel_kb())
        return

    if amount > user["balance"]:
        err = f"Недостаточно звёзд. Баланс: {user['balance']:,} ⭐️."
        if callback:
            await callback.answer(err, show_alert=True)
        else:
            await message.answer(err, reply_markup=get_cancel_kb())
        return

    await state.update_data(amount=amount)
    await state.set_state(ChequeState.waiting_for_recipient)

    prompt = (
        f"Сумма чека: <b>{amount:,} ⭐️</b>\n\n"
        "Кто сможет забрать этот чек?"
    )

    if callback:
        await callback.message.edit_text(prompt, reply_markup=get_cheque_recipient_choice_kb())
        await callback.answer()
    else:
        await message.answer(prompt, reply_markup=get_cheque_recipient_choice_kb())


@router.callback_query(F.data == "ch_target:any", ChequeState.waiting_for_recipient)
async def process_cheque_target_any(callback: CallbackQuery, state: FSMContext):
    await state.update_data(recipient_username=None)
    await state.set_state(ChequeState.waiting_for_comment)
    await callback.message.edit_text(
        "Напишите комментарий к чеку (или нажмите «Пропустить»):",
        reply_markup=get_skip_comment_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "ch_target:user", ChequeState.waiting_for_recipient)
async def process_cheque_target_user(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите <b>@username</b> получателя чека:",
        reply_markup=get_cancel_kb()
    )
    await callback.answer()


@router.message(ChequeState.waiting_for_recipient)
async def process_cheque_username(message: Message, state: FSMContext):
    target = message.text.strip().lstrip("@").lower()
    if not target:
        await message.answer("Введите корректный @username:", reply_markup=get_cancel_kb())
        return

    await state.update_data(recipient_username=target)
    await state.set_state(ChequeState.waiting_for_comment)
    await message.answer(
        f"Получатель: <b>@{target}</b>\n\n"
        "Напишите комментарий к чеку (или нажмите «Пропустить»):",
        reply_markup=get_skip_comment_kb()
    )


@router.callback_query(F.data == "skip_comment", ChequeState.waiting_for_comment)
async def process_cheque_skip_comment(callback: CallbackQuery, state: FSMContext):
    await finalize_cheque(callback.message, state, comment=None, callback=callback)


@router.message(ChequeState.waiting_for_comment)
async def process_cheque_comment(message: Message, state: FSMContext):
    comment = message.text.strip()[:100]
    await finalize_cheque(message, state, comment=comment)


async def finalize_cheque(message: Message, state: FSMContext, comment: str = None, callback: CallbackQuery = None):
    data = await state.get_data()
    user_id = message.chat.id
    user = await db.get_user(user_id)
    amount = data["amount"]
    rec_u = data.get("recipient_username")

    cheque_id = await db.create_cheque(
        creator_id=user_id,
        creator_username=user.get("username"),
        amount=amount,
        recipient_username=rec_u,
        comment=comment
    )

    if not cheque_id:
        err = "Не удалось создать чек."
        if callback:
            await callback.answer(err, show_alert=True)
        else:
            await message.answer(err, reply_markup=get_back_button())
        await state.clear()
        return

    me = await message.bot.get_me()
    bot_u = me.username or "sbpbot"
    link = f"https://staticgram.top/{bot_u}?start={cheque_id}"

    rec_label = f"@{rec_u}" if rec_u else "для всех"
    comm_str = f"\n• Комментарий: <i>{comment}</i>" if comment else ""

    text = (
        f"✅ <b>Чек на {amount:,} ⭐️ создан</b>\n\n"
        f"• Получатель: {rec_label}{comm_str}\n"
        f"• Ссылка: <code>{link}</code>\n\n"
        f"Нажмите кнопку ниже, чтобы отправить чек в чат:"
    )

    kb = get_cheque_created_kb(cheque_id, bot_u)
    if callback:
        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()
    else:
        await message.answer(text, reply_markup=kb)

    await state.clear()


@router.callback_query(F.data == "cheque_list")
async def show_active_cheques(callback: CallbackQuery):
    user_id = callback.from_user.id
    cheques = await db.get_active_cheques_by_user(user_id)

    if not cheques:
        await callback.message.edit_text(
            "У вас нет активных чеков.",
            reply_markup=get_back_button("menu_cheque")
        )
        await callback.answer()
        return

    text = "<b>Ваши активные чеки:</b>\n\n"
    buttons = []

    for ch in cheques:
        rec = f"@{ch['recipient_username']}" if ch.get('recipient_username') else "все"
        text += f"• <code>{ch['cheque_id']}</code>: <b>{ch['amount']:,} ⭐️</b> ({rec})\n"
        buttons.append([
            InlineKeyboardButton(text=f"Аннулировать {ch['amount']} ⭐️", callback_data=f"cancel_ch:{ch['cheque_id']}")
        ])

    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="menu_cheque")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_ch:"))
async def process_cancel_cheque(callback: CallbackQuery):
    cheque_id = callback.data.split(":")[1]
    user_id = callback.from_user.id

    ok = await db.cancel_cheque(cheque_id, user_id)
    if ok:
        await callback.answer("Чек аннулирован, звёзды возвращены.", show_alert=True)
        user = await db.get_user(user_id)
        from utils.formatters import format_sbp_card
        await callback.message.edit_text(format_sbp_card(user), reply_markup=get_back_button())
    else:
        await callback.answer("Чек уже активирован или не существует.", show_alert=True)
