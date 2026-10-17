import uuid
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

import database as db
from custom_methods import WithdrawStarBalance
from utils.states import WithdrawState
from utils.formatters import format_electronic_receipt, mask_name
from keyboards.withdraw_kb import (
    get_withdraw_target_kb,
    get_withdraw_amount_kb,
    get_confirm_withdraw_kb
)
from keyboards.main_kb import get_cancel_kb, get_back_button

router = Router()

@router.callback_query(F.data == "menu_withdraw")
@router.message(Command("withdraw"))
async def start_withdraw(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    user = await db.get_user(user_id)

    if not user or user["balance"] < 1:
        text = "Недостаточно звёзд для вывода."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 Пополнить счёт", callback_data="menu_deposit")],
            [InlineKeyboardButton(text="← В главное меню", callback_data="back_to_menu")]
        ])
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text, reply_markup=kb)
            await event.answer()
        else:
            await event.answer(text, reply_markup=kb)
        return

    text = (
        f"<b>Вывод звёзд на аккаунт</b>\n\n"
        f"Доступно к выводу: <b>{user['balance']:,} ⭐️</b>\n\n"
        f"Звёзды зачисляются напрямую на баланс аккаунта в StaticGram через официальный шлюз.\n\n"
        f"Куда отправить звёзды?"
    )

    await state.set_state(WithdrawState.waiting_for_target)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_withdraw_target_kb())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_withdraw_target_kb())


@router.callback_query(F.data == "wd_target:self", WithdrawState.waiting_for_target)
async def process_target_self(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    u_label = f"@{user['username']}" if user.get("username") else f"id{user_id}"

    await state.update_data(target_id=user_id, target_label=u_label)
    await state.set_state(WithdrawState.waiting_for_amount)

    await callback.message.edit_text(
        f"Получатель: <b>{u_label}</b>\n"
        f"Доступно: <b>{user['balance']:,} ⭐️</b>\n\n"
        "Укажите сумму вывода:",
        reply_markup=get_withdraw_amount_kb(user['balance'])
    )
    await callback.answer()


@router.callback_query(F.data == "wd_target:other", WithdrawState.waiting_for_target)
async def process_target_other(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите <b>@username</b> или <b>Telegram ID</b> получателя:",
        reply_markup=get_cancel_kb()
    )
    await callback.answer()


@router.message(WithdrawState.waiting_for_target)
async def process_target_input(message: Message, state: FSMContext):
    target_raw = message.text.strip()
    sender_id = message.from_user.id
    sender = await db.get_user(sender_id)

    target_id = target_raw
    if target_raw.isdigit():
        target_id = int(target_raw)

    clean_label = target_raw if target_raw.startswith("@") else f"@{target_raw}" if not target_raw.isdigit() else f"id{target_raw}"

    await state.update_data(target_id=target_id, target_label=clean_label)
    await state.set_state(WithdrawState.waiting_for_amount)

    await message.answer(
        f"Получатель: <b>{clean_label}</b>\n"
        f"Доступно: <b>{sender['balance']:,} ⭐️</b>\n\n"
        "Укажите сумму вывода:",
        reply_markup=get_withdraw_amount_kb(sender['balance'])
    )


@router.callback_query(F.data.startswith("wd_amt:"), WithdrawState.waiting_for_amount)
async def process_preset_withdraw(callback: CallbackQuery, state: FSMContext):
    amount = int(callback.data.split(":")[1])
    await handle_withdraw_amount(callback.message, state, amount, callback=callback)


@router.callback_query(F.data == "wd_custom", WithdrawState.waiting_for_amount)
async def process_custom_withdraw_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите сумму вывода целым числом:",
        reply_markup=get_cancel_kb()
    )
    await callback.answer()


@router.message(WithdrawState.waiting_for_amount)
async def process_withdraw_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace("⭐️", "").replace(" ", "")
    if not text.isdigit():
        await message.answer("Введите целое число звёзд:", reply_markup=get_cancel_kb())
        return

    amount = int(text)
    await handle_withdraw_amount(message, state, amount)


async def handle_withdraw_amount(message: Message, state: FSMContext, amount: int, callback: CallbackQuery = None):
    user_id = message.chat.id
    user = await db.get_user(user_id)

    if amount < 1:
        err = "Минимальная сумма вывода — 1 ⭐️."
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
    data = await state.get_data()
    target_label = data["target_label"]

    text = (
        f"<b>Вывод {amount:,} ⭐️ на аккаунт</b>\n\n"
        f"• Получатель: <b>{target_label}</b>\n"
        f"• Сумма списания: <b>{amount:,} ⭐️</b>\n"
        f"• Комиссия: <b>0 ⭐️</b>\n\n"
        f"Звёзды поступят на аккаунт официальным уведомлением."
    )

    await state.set_state(WithdrawState.confirm_withdraw)
    if callback:
        await callback.message.edit_text(text, reply_markup=get_confirm_withdraw_kb())
        await callback.answer()
    else:
        await message.answer(text, reply_markup=get_confirm_withdraw_kb())


@router.callback_query(F.data == "confirm_withdraw_btn", WithdrawState.confirm_withdraw)
async def execute_withdraw(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    user = await db.get_user(user_id)

    amount = data["amount"]
    target_id = data["target_id"]
    target_label = data["target_label"]

    if user["balance"] < amount:
        await callback.answer("Недостаточно звёзд на счёте.", show_alert=True)
        await state.clear()
        return

    req_id = f"wd{user_id}_{uuid.uuid4().hex[:12]}"

    try:
        res = await callback.bot(WithdrawStarBalance(
            user_id=target_id,
            star_count=amount,
            request_id=req_id
        ))

        trx_id = await db.debit_balance(
            user_id=user_id,
            amount=amount,
            trx_type="withdrawal",
            comment="Вывод звёзд через withdrawStarBalance",
            counterparty=str(target_label)
        )

        user_updated = await db.get_user(user_id)
        sender_label = f"@{user_updated['username']}" if user_updated.get("username") else f"id{user_id}"

        receipt = format_electronic_receipt(
            trx_id=trx_id or req_id,
            op_type="Вывод звёзд на аккаунт",
            amount=amount,
            sender_label=sender_label,
            recipient_label=target_label,
            comment="Официальная выплата"
        )

        await callback.message.edit_text(
            f"✅ <b>Вывод успешно исполнен</b>\n\n"
            f"На аккаунт <b>{target_label}</b> зачислено <b>{amount:,} ⭐️</b>.\n"
            f"Остаток в СБП: <b>{user_updated['balance']:,} ⭐️</b>\n\n"
            f"{receipt}",
            reply_markup=get_back_button()
        )

    except TelegramBadRequest as e:
        err_msg = e.message
        if "BALANCE_TOO_LOW" in err_msg:
            await callback.message.edit_text(
                "<b>В резерве бота временно недостаточно звёзд</b>\n\n"
                f"На балансе бота сейчас нет {amount:,} ⭐️.\n"
                "Резерв пополняется при депозитах пользователей (/deposit) или владельцем.\n\n"
                "Ваши звёзды на балансе сохранены.",
                reply_markup=get_back_button()
            )
        elif "user not found" in err_msg.lower():
            await callback.message.edit_text(
                f"Пользователь <code>{target_label}</code> не найден в StaticGram.\nПроверьте @username или ID.",
                reply_markup=get_back_button()
            )
        else:
            await callback.message.edit_text(
                f"Ошибка при выводе: {err_msg}",
                reply_markup=get_back_button()
            )
    except Exception as e:
        await callback.message.edit_text(
            f"Ошибка: {e}",
            reply_markup=get_back_button()
        )

    await state.clear()
    await callback.answer()
