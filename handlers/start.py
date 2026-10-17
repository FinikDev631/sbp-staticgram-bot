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
            await message.answer("Вы не можете активировать собственный чек.", reply_markup=get_back_button())
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

    text = format_sbp_card(user)
    await message.answer(text, reply_markup=get_main_menu_inline(user_id))


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

    text = format_sbp_card(user)
    try:
        await callback.message.edit_text(text, reply_markup=get_main_menu_inline(user_id))
    except Exception:
        await callback.message.answer(text, reply_markup=get_main_menu_inline(user_id))
    await callback.answer()


@router.callback_query(F.data == "cancel_action")
async def cb_cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    text = format_sbp_card(user)
    try:
        await callback.message.edit_text(text, reply_markup=get_main_menu_inline(user_id))
    except Exception:
        await callback.message.answer(text, reply_markup=get_main_menu_inline(user_id))
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>Команды бота:</b>\n\n"
        "/start — Главное меню\n"
        "/pay — Перевести звёзды\n"
        "/deposit — Пополнить баланс\n"
        "/withdraw — Вывести на аккаунт\n"
        "/cheque — Создать чек\n"
        "/history — История операций\n\n"
        "Официальный канал: @sbpnews",
        reply_markup=get_back_button()
    )
