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
    get_withdraw_method_kb,
    get_withdraw_target_kb,
    get_withdraw_amount_kb,
    get_confirm_withdraw_kb,
    get_gifts_selection_kb,
    get_confirm_gift_kb
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
        text = (
            "⚠️ <b>НЕДОСТАТОЧНО ЗВЁЗД</b>\n"
            "────────────────────────\n"
            "На вашем счёте СБП <b>0 ⭐️</b>.\n"
            "Выводить пока нечего. Пополните счёт или получите перевод по СБП!"
        )
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text, reply_markup=get_back_button())
            await event.answer()
        else:
            await event.answer(text, reply_markup=get_back_button())
        return

    text = (
        "📤 <b>ВЫВОД ЗВЁЗД ИЗ СБП</b>\n"
        "────────────────────────\n"
        f"Ваш доступный баланс: <b>{user['balance']:,} ⭐️</b>\n\n"
        "Выберите удобный способ вывода:\n\n"
        "1️⃣ <b>Прямой вывод звёзд на аккаунт:</b>\n"
        "• Звёзды начисляются на баланс от официального сервиса 777000.\n"
        "• 0% комиссия сервиса.\n"
        "• Можно вывести себе или любому пользователю по @username.\n\n"
        "2️⃣ <b>Вывод подарком в профиль (конвертация):</b>\n"
        "• Бот отправляет официальный Telegram подарок в ваш профиль.\n"
        "• Подарок можно оставить в профиле или <b>конвертировать в звёзды</b>.\n"
        "• Комиссию за конвертацию берёт платформа/пользователь."
    )

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_withdraw_method_kb())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_withdraw_method_kb())


# --- Method 1: Direct Stars Withdrawal (withdrawStarBalance) ---

@router.callback_query(F.data == "wd_method:direct")
async def choose_direct_target(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)

    text = (
        "⚡️ <b>ПРЯМОЙ ВЫВОД ЗВЁЗД НА АККАУНТ</b>\n"
        "────────────────────────\n"
        f"Доступно к выводу: <b>{user['balance']:,} ⭐️</b>\n\n"
        "Куда отправить звёзды?"
    )
    await state.set_state(WithdrawState.waiting_for_target)
    await callback.message.edit_text(text, reply_markup=get_withdraw_target_kb())
    await callback.answer()


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
        "📦 <b>Способ доставки:</b> Официальное зачисление от 777000\n"
        "────────────────────────\n"
        "<i>Звёзды спишутся с вашего счёта СБП и поступят на баланс аккаунта StaticGram.</i>"
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

    req_id = f"sbp-wd-{user_id}-{uuid.uuid4().hex[:12]}"

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
            comment="Вывод звёзд на аккаунт StaticGram",
            counterparty=str(target_label)
        )

        user_updated = await db.get_user(user_id)
        sender_label = f"@{user_updated['username']}" if user_updated.get("username") else f"{user_updated['first_name']} (ID {user_id})"

        receipt = format_electronic_receipt(
            trx_id=trx_id or req_id,
            op_type="Вывод звёзд из СБП",
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
                "⚠️ <b>РЕЗЕРВ БОТА ВРЕМЕННО ПУСТ</b>\n"
                "────────────────────────\n"
                f"На балансе бота сейчас нет {amount:,} ⭐️ для прямого вывода.\n"
                "💡 <i>Вы можете воспользоваться выводом через подарки (🎁) или дождаться пополнения резерва.</i>\n\n"
                "Ваши средства на счёте СБП в полной сохранности!",
                reply_markup=get_back_button()
            )
        elif "user not found" in err_msg.lower():
            await callback.message.edit_text(
                f"⚠️ <b>ОШИБКА:</b> Получатель <code>{target_label}</code> не найден в StaticGram.\n"
                "Проверьте правильность @username или ID.",
                reply_markup=get_back_button()
            )
        else:
            await callback.message.edit_text(
                f"⚠️ <b>Ошибка при выводе:</b> {err_msg}",
                reply_markup=get_back_button()
            )
    except Exception as e:
        await callback.message.edit_text(
            f"⚠️ <b>Непредвиденная ошибка:</b> {e}",
            reply_markup=get_back_button()
        )

    await state.clear()
    await callback.answer()


# --- Method 2: Gift Withdrawal (sendGift) ---

@router.callback_query(F.data == "wd_method:gift")
async def choose_gift_withdrawal(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    balance = user["balance"] if user else 0

    try:
        gifts_obj = await callback.bot.get_available_gifts()
        raw_gifts = [
            {"id": g.id, "star_count": g.star_count}
            for g in gifts_obj.gifts
        ]
    except Exception:
        raw_gifts = [
            {"id": "9000000000000001", "star_count": 15},
            {"id": "9000000000000003", "star_count": 25},
            {"id": "9000000000000005", "star_count": 50},
            {"id": "9000000000000008", "star_count": 100}
        ]

    text = (
        "🎁 <b>ВЫВОД ПОДАРКОМ TELEGRAM / STATICGRAM</b>\n"
        "────────────────────────\n"
        f"Ваш доступный баланс СБП: <b>{balance:,} ⭐️</b>\n\n"
        "<b>Как это работает:</b>\n"
        "1. Вы выбираете подарок нужной стоимости.\n"
        "2. Бот мгновенно отправляет подарок в ваш профиль StaticGram.\n"
        "3. Вы можете оставить подарок на память или нажать кнопку "
        "<b>«Конвертировать в звёзды»</b> прямо в профиле!\n"
        "<i>(При конвертации подарка платформа берёт стандартную комиссию 15%).</i>\n\n"
        "Выберите подарок для отправки:"
    )

    await callback.message.edit_text(text, reply_markup=get_gifts_selection_kb(raw_gifts, balance))
    await callback.answer()


@router.callback_query(F.data.startswith("select_gift:"))
async def confirm_gift_selection(callback: CallbackQuery):
    parts = callback.data.split(":")
    gift_id = parts[1]
    cost = int(parts[2])
    user_id = callback.from_user.id
    user = await db.get_user(user_id)

    if not user or user["balance"] < cost:
        await callback.answer(f"⚠️ Недостаточно звёзд. Требуется {cost} ⭐️, у вас {user['balance']} ⭐️.", show_alert=True)
        return

    text = (
        "🎁 <b>ПОДТВЕРЖДЕНИЕ ВЫВОДА ПОДАРКОМ</b>\n"
        "────────────────────────\n"
        f"Стоимость подарка: <b>{cost:,} ⭐️</b>\n"
        f"Получатель: <b>{mask_name(callback.from_user.first_name, callback.from_user.last_name)}</b>\n"
        "────────────────────────\n"
        "Подарок отобразится в вашем профиле StaticGram. "
        "Вы сможете конвертировать его в звёзды в любой момент!"
    )

    await callback.message.edit_text(text, reply_markup=get_confirm_gift_kb(gift_id, cost))
    await callback.answer()


@router.callback_query(F.data.startswith("send_gift_btn:"))
async def execute_send_gift(callback: CallbackQuery):
    parts = callback.data.split(":")
    gift_id = parts[1]
    cost = int(parts[2])
    user_id = callback.from_user.id
    user = await db.get_user(user_id)

    if not user or user["balance"] < cost:
        await callback.answer("⚠️ Недостаточно звёзд на счёте.", show_alert=True)
        return

    try:
        # Send gift directly to the user
        await callback.bot.send_gift(
            user_id=user_id,
            gift_id=gift_id,
            text="Вывод звёзд из сервиса СБП ⚡️"
        )

        # Debit from SBP balance
        trx_id = await db.debit_balance(
            user_id=user_id,
            amount=cost,
            trx_type="withdrawal",
            comment=f"Вывод подарком за {cost} ⭐️ (ID {gift_id})",
            counterparty="Подарок Telegram"
        )

        user_updated = await db.get_user(user_id)
        u_label = f"@{user_updated['username']}" if user_updated.get("username") else f"{user_updated['first_name']}"

        receipt = format_electronic_receipt(
            trx_id=trx_id or "SBP-GIFT",
            op_type="Вывод подарком СБП",
            amount=cost,
            sender_label="СБП Банк",
            recipient_label=u_label,
            comment=f"Отправлен подарок за {cost} ⭐️ в профиль"
        )

        await callback.message.edit_text(
            f"🎉 <b>ПОДАРОК УСПЕШНО ОТПРАВЛЕН!</b>\n\n"
            f"Подарок за <b>{cost:,} ⭐️</b> зачислен в ваш профиль StaticGram.\n"
            f"Вы можете оставить его или обменять на звёзды в своём профиле.\n"
            f"Остаток на счёте СБП: <b>{user_updated['balance']:,} ⭐️</b>\n\n"
            f"{receipt}",
            reply_markup=get_back_button()
        )

    except TelegramBadRequest as e:
        if "BALANCE_TOO_LOW" in e.message:
            await callback.message.edit_text(
                "⚠️ <b>РЕЗЕРВ БОТА ВРЕМЕННО ПУСТ</b>\n"
                "────────────────────────\n"
                f"На балансе бота сейчас нет {cost:,} ⭐️ для покупки этого подарка.\n"
                "Попробуйте позже или используйте прямой перевод внутри СБП!",
                reply_markup=get_back_button()
            )
        else:
            await callback.message.edit_text(
                f"⚠️ <b>Ошибка при отправке подарка:</b> {e.message}",
                reply_markup=get_back_button()
            )
    except Exception as e:
        await callback.message.edit_text(
            f"⚠️ <b>Непредвиденная ошибка:</b> {e}",
            reply_markup=get_back_button()
        )

    await callback.answer()
