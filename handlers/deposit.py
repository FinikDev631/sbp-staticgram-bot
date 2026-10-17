import uuid
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from aiogram.fsm.context import FSMContext

import database as db
from utils.states import DepositState
from utils.formatters import format_electronic_receipt
from keyboards.deposit_kb import get_deposit_amounts_kb
from keyboards.main_kb import get_cancel_kb, get_back_button

router = Router()

@router.callback_query(F.data == "menu_deposit")
@router.message(Command("deposit"))
async def start_deposit(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "📥 <b>ПОПОЛНЕНИЕ СЧЁТА СБП ЗВЁЗДАМИ (XTR)</b>\n"
        "────────────────────────\n"
        "Вы можете мгновенно пополнить свой счёт СБП официальными звёздами Telegram Stars (XTR).\n\n"
        "Выберите сумму пополнения или введите свою:"
    )

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_deposit_amounts_kb())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_deposit_amounts_kb())


@router.callback_query(F.data.startswith("deposit_amt:"))
async def process_preset_deposit(callback: CallbackQuery, state: FSMContext):
    amount = int(callback.data.split(":")[1])
    await send_deposit_invoice(callback.message, callback.from_user.id, amount)
    await callback.answer()


@router.callback_query(F.data == "deposit_custom")
async def process_custom_deposit_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DepositState.waiting_for_amount)
    await callback.message.edit_text(
        "✏️ Введите сумму пополнения в ⭐️ (целое число от 1 до 100 000):",
        reply_markup=get_cancel_kb()
    )
    await callback.answer()


@router.message(DepositState.waiting_for_amount)
async def process_custom_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace("⭐️", "").replace(" ", "")
    if not text.isdigit():
        await message.answer("⚠️ Введите корректное целое число (например, <code>50</code>):", reply_markup=get_cancel_kb())
        return

    amount = int(text)
    if amount < 1 or amount > 100000:
        await message.answer("⚠️ Сумма должна быть от 1 до 100 000 ⭐️. Попробуйте снова:", reply_markup=get_cancel_kb())
        return

    await state.clear()
    await send_deposit_invoice(message, message.from_user.id, amount)


async def send_deposit_invoice(message: Message, user_id: int, amount: int):
    payload = f"dep_{user_id}_{amount}_{uuid.uuid4().hex[:8]}"
    title = f"Пополнение СБП (+{amount:,} ⭐️)"
    desc = f"Зачисление {amount:,} звёзд на ваш счёт в Системе Быстрых Платежей StaticGram"

    try:
        await message.bot.send_invoice(
            chat_id=user_id,
            title=title,
            description=desc,
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label=f"Пополнение {amount:,} ⭐️", amount=amount)]
        )
    except Exception as e:
        await message.answer(
            f"⚠️ Ошибка при создании счёта: {e}\nПопробуйте позже.",
            reply_markup=get_back_button()
        )


@router.pre_checkout_query()
async def process_pre_checkout(query: PreCheckoutQuery):
    # StaticGram requires pre_checkout_query response within 10s
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    sp = message.successful_payment
    user_id = message.from_user.id
    stars_amount = sp.total_amount

    user = await db.get_user(user_id)
    if not user:
        user = await db.get_or_create_user(
            user_id,
            message.from_user.username,
            message.from_user.first_name or "Клиент",
            message.from_user.last_name
        )

    trx_id = await db.credit_balance(
        user_id=user_id,
        amount=stars_amount,
        trx_type="deposit",
        comment="Пополнение счёта Telegram Stars (XTR)",
        counterparty="Telegram Stars"
    )

    user_updated = await db.get_user(user_id)
    u_label = f"@{user_updated['username']}" if user_updated.get("username") else f"{user_updated['first_name']} ({user_updated['account_number']})"

    receipt = format_electronic_receipt(
        trx_id=trx_id,
        op_type="Пополнение счёта СБП",
        amount=stars_amount,
        sender_label="Telegram Stars (XTR)",
        recipient_label=u_label,
        comment="Официальная оплата звёздами StaticGram"
    )

    await message.answer(
        f"🎉 <b>СЧЁТ СБП УСПЕШНО ПОПОЛНЕН!</b>\n\n"
        f"Вам зачислено: <b>+{stars_amount:,} ⭐️</b>\n"
        f"Текущий баланс: <b>{user_updated['balance']:,} ⭐️</b>\n\n"
        f"{receipt}",
        reply_markup=get_back_button()
    )
