import uuid
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
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
    """
    Direct star withdrawal via StaticGram API withdrawStarBalance:
    https://docs.staticgram.top/methods/withdrawStarBalance
    """
    await state.clear()
    user_id = event.from_user.id
    user = await db.get_user(user_id)

    if not user or user["balance"] < 1:
        text = (
            "⚠️ <b>НЕДОСТАТОЧНО ЗВЁЗД</b>\n"
            "────────────────────────\n"
            "На вашем счёте СБП <b>0 ⭐️</b>.\n"
            "Выводить пока нечего. Пополните счёт через /deposit или получите перевод по СБП!"
        )
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text, reply_markup=get_back_button())
            await event.answer()
        else:
            await event.answer(text, reply_markup=get_back_button())
        return

    text = (
        "📤 <b>ВЫВОД ЗВЁЗД ПО СБП (withdrawStarBalance)</b>\n"
        "────────────────────────\n"
        f"Ваш доступный баланс: <b>{user['balance']:,} ⭐️</b>\n\n"
        "Звёзды выводятся напрямую на баланс аккаунта в StaticGram через метод "
        "<code>withdrawStarBalance</code>.\n\n"
        "Получатель мгновенно получает официальное системное уведомление от <b>777000</b>:\n"
        "<i>«Вывод от бота @sbpbot в размере X ⭐️ зачислен на ваш баланс.»</i>\n\n"
        "Куда отправить звёзды?"
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
    u_label = f"@{user['username']}" if user.get("username") else f"{user['first_name']} (ID {user_id})"

    await state.update_data(target_id=user_id, target_label=f"Ваш аккаунт ({u_label})")
    await state.set_state(WithdrawState.waiting_for_amount)

    await callback.message.edit_text(
        f"👤 <b>Получатель вывода:</b> Ваш аккаунт ({u_label})\n"
        f"💰 <b>Доступно к выводу:</b> {user['balance']:,} ⭐️\n\n"
        "Выберите или введите сумму вывода в ⭐️:",
        reply_markup=get_withdraw_amount_kb(user['balance'])
    )
    await callback.answer()


@router.callback_query(F.data == "wd_target:other", WithdrawState.waiting_for_target)
async def process_target_other(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "👥 <b>ВЫВОД НА ДРУГОЙ АККАУНТ</b>\n\n"
        "Введите <b>@username</b> или <b>Telegram ID</b> получателя звёзд:",
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

    clean_label = target_raw if target_raw.startswith("@") else f"@{target_raw}" if not target_raw.isdigit() else f"ID {target_raw}"

    await state.update_data(target_id=target_id, target_label=clean_label)
    await state.set_state(WithdrawState.waiting_for_amount)

    await message.answer(
        f"👤 <b>Получатель вывода:</b> {clean_label}\n"
        f"💰 <b>Доступно к выводу:</b> {sender['balance']:,} ⭐️\n\n"
        "Выберите или введите сумму вывода в ⭐️:",
        reply_markup=get_withdraw_amount_kb(sender['balance'])
    )


@router.callback_query(F.data.startswith("wd_amt:"), WithdrawState.waiting_for_amount)
async def process_preset_withdraw(callback: CallbackQuery, state: FSMContext):
    amount = int(callback.data.split(":")[1])
    await handle_withdraw_amount(callback.message, state, amount, callback=callback)


@router.callback_query(F.data == "wd_custom", WithdrawState.waiting_for_amount)
async def process_custom_withdraw_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✏️ Введите сумму вывода в ⭐️ (целое число от 1 ⭐️):",
        reply_markup=get_cancel_kb()
    )
    await callback.answer()


@router.message(WithdrawState.waiting_for_amount)
async def process_withdraw_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace("⭐️", "").replace(" ", "")
    if not text.isdigit():
        await message.answer("⚠️ Введите корректную сумму целым числом:", reply_markup=get_cancel_kb())
        return

    amount = int(text)
    await handle_withdraw_amount(message, state, amount)


async def handle_withdraw_amount(message: Message, state: FSMContext, amount: int, callback: CallbackQuery = None):
    user_id = message.chat.id
    user = await db.get_user(user_id)

    if amount < 1:
        err = "⚠️ Минимальная сумма вывода — 1 ⭐️."
        if callback:
            await callback.answer(err, show_alert=True)
        else:
            await message.answer(err, reply_markup=get_cancel_kb())
        return

    if amount > user["balance"]:
        err = f"⚠️ Недостаточно звёзд. Ваш баланс: {user['balance']:,} ⭐️."
        if callback:
            await callback.answer(err, show_alert=True)
        else:
            await message.answer(err, reply_markup=get_cancel_kb())
        return

    await state.update_data(amount=amount)
    data = await state.get_data()
    target_label = data["target_label"]

    text = (
        "⚡️ <b>ПОДТВЕРЖДЕНИЕ ВЫВОДА ЗВЁЗД</b>\n"
        "────────────────────────\n"
        f"👤 <b>Получатель:</b> <b>{target_label}</b>\n"
        f"💰 <b>Сумма вывода:</b> <b>{amount:,} ⭐️</b>\n"
        "🏷 <b>Комиссия СБП:</b> <b>0 ⭐️ (0%)</b>\n"
        "🌐 <b>Метод API:</b> <code>withdrawStarBalance</code>\n"
        "📦 <b>Способ доставки:</b> Официальное зачисление от 777000\n"
        "────────────────────────\n"
        "<i>Звёзды спишутся с баланса СБП и будут начислены напрямую на аккаунт StaticGram.</i>"
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
        await callback.answer("⚠️ Недостаточно звёзд на счёте.", show_alert=True)
        await state.clear()
        return

    # Generate ASCII idempotency key up to 40 chars
    req_id = f"wd{user_id}_{uuid.uuid4().hex[:12]}"

    try:
        # Call StaticGram withdrawStarBalance method directly
        res = await callback.bot(WithdrawStarBalance(
            user_id=target_id,
            star_count=amount,
            request_id=req_id
        ))

        # Successfully executed on StaticGram: deduct from internal SBP balance
        trx_id = await db.debit_balance(
            user_id=user_id,
            amount=amount,
            trx_type="withdrawal",
            comment="Вывод звёзд через withdrawStarBalance",
            counterparty=str(target_label)
        )

        user_updated = await db.get_user(user_id)
        sender_label = f"@{user_updated['username']}" if user_updated.get("username") else f"{user_updated['first_name']} (ID {user_id})"

        receipt = format_electronic_receipt(
            trx_id=trx_id or req_id,
            op_type="Вывод звёзд (withdrawStarBalance)",
            amount=amount,
            sender_label=sender_label,
            recipient_label=target_label,
            comment="Официальная выплата StaticGram от 777000"
        )

        await callback.message.edit_text(
            f"🎉 <b>ВЫВОД ЗВЁЗД УСПЕШНО ИСПОЛНЕН!</b>\n\n"
            f"Получателю <b>{target_label}</b> зачислено <b>{amount:,} ⭐️</b>.\n"
            f"Входящее системное уведомление отправлено от 777000.\n"
            f"Ваш остаток в СБП: <b>{user_updated['balance']:,} ⭐️</b>\n\n"
            f"{receipt}",
            reply_markup=get_back_button()
        )

    except TelegramBadRequest as e:
        err_msg = e.message
        if "BALANCE_TOO_LOW" in err_msg:
            await callback.message.edit_text(
                "⚠️ <b>НЕДОСТАТОЧНО ЗВЁЗД НА БАЛАНСЕ БОТА</b>\n"
                "────────────────────────\n"
                f"На балансе бота сейчас нет {amount:,} ⭐️ для вывода через <code>withdrawStarBalance</code>.\n\n"
                "ℹ️ <i>Как это работает:</i> бот переводит звёзды со своего баланса StaticGram. "
                "Баланс бота увеличивается, когда пользователи совершают пополнения (депозиты) "
                "через команду <b>/deposit</b> или когда владелец бота вносит звёзды.\n\n"
                "💡 <b>Ваши средства на счёте СБП в полной сохранности!</b>\n"
                "Вы можете делать мгновенные переводы другим пользователям внутри СБП "
                "или повторить вывод позже.",
                reply_markup=get_back_button()
            )
        elif "user not found" in err_msg.lower():
            await callback.message.edit_text(
                f"⚠️ <b>ОШИБКА:</b> Получатель <code>{target_label}</code> не найден в StaticGram.\n"
                "Проверьте правильность @username или ID.",
                reply_markup=get_back_button()
            )
        elif "STAR_COUNT_TOO_SMALL" in err_msg:
            await callback.message.edit_text(
                "⚠️ Минимальная сумма вывода задана сервером (от 1 ⭐️).",
                reply_markup=get_back_button()
            )
        elif "Too Many Requests" in err_msg:
            await callback.message.edit_text(
                "⏳ Превышен лимит частоты вывода (не более 10 выводов в минуту). Подождите немного.",
                reply_markup=get_back_button()
            )
        else:
            await callback.message.edit_text(
                f"⚠️ <b>Ошибка withdrawStarBalance:</b> {err_msg}",
                reply_markup=get_back_button()
            )
    except Exception as e:
        await callback.message.edit_text(
            f"⚠️ <b>Непредвиденная ошибка:</b> {e}",
            reply_markup=get_back_button()
        )

    await state.clear()
    await callback.answer()
