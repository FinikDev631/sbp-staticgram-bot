from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from utils.formatters import format_sbp_card, format_cheque_claimed_message
from keyboards.main_kb import get_main_menu_inline, get_back_button

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name or "Клиент"
    last_name = message.from_user.last_name

    # Check deep linking (e.g. /start ch_abc123)
    args = message.text.split(maxsplit=1)
    deep_link = args[1] if len(args) > 1 else None

    user = await db.get_or_create_user(user_id, username, first_name, last_name)

    if deep_link and deep_link.startswith("ch_"):
        cheque_id = deep_link
        claim_res = await db.claim_cheque(cheque_id, user_id, username, first_name)
        status = claim_res.get("status")

        if status == "ok":
            amount = claim_res["amount"]
            creator_label = f"@{claim_res['creator_username']}" if claim_res.get("creator_username") else f"ID {claim_res['creator_id']}"
            await message.answer(
                f"🎉 <b>ЧЕК СБП УСПЕШНО АКТИВИРОВАН!</b>\n\n"
                f"Вам зачислено <b>+{amount:,} ⭐️</b> на счёт СБП от {creator_label}.\n"
                f"Текущий баланс: <b>{user['balance'] + amount:,} ⭐️</b>",
                reply_markup=get_back_button()
            )
            # Notify creator
            try:
                claimer_label = f"@{username}" if username else f"{first_name} (ID {user_id})"
                await message.bot.send_message(
                    claim_res["creator_id"],
                    f"⚡️ <b>Уведомление СБП:</b>\n"
                    f"Ваш чек на <b>{amount:,} ⭐️</b> успешно забрал(а) {claimer_label}!"
                )
            except Exception:
                pass
            return
        elif status == "self_claim":
            await message.answer("⚠️ Вы не можете активировать собственный чек.", reply_markup=get_back_button())
            return
        elif status == "already_claimed":
            await message.answer("⚠️ Этот чек уже был активирован ранее.", reply_markup=get_back_button())
            return
        elif status == "restricted":
            await message.answer(
                f"⛔️ Этот чек предназначен только для пользователя @{claim_res.get('expected')}.",
                reply_markup=get_back_button()
            )
            return
        else:
            await message.answer("⚠️ Чек не найден или срок его действия истёк.", reply_markup=get_back_button())
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
    await callback.answer("Действие отменено.")
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    text = format_sbp_card(user)
    try:
        await callback.message.edit_text(text, reply_markup=get_main_menu_inline(user_id))
    except Exception:
        await callback.message.answer(text, reply_markup=get_main_menu_inline(user_id))


@router.callback_query(F.data == "menu_info")
async def cb_menu_info(callback: CallbackQuery):
    info_text = (
        "⚡️ <b>О СИСТЕМЕ БЫСТРЫХ ПЛАТЕЖЕЙ (СБП) ЗВЁЗД</b>\n"
        "────────────────────────\n"
        "СБП — это платёжный сервис для мгновенных переводов звёзд (Telegram Stars) "
        "между пользователями StaticGram.\n\n"
        "<b>Преимущества СБП:</b>\n"
        "• 💸 <b>0 ⭐️ комиссия:</b> переводы между счетами абсолютно бесплатны.\n"
        "• ⚡️ <b>Мгновенно:</b> зачисление звёзд за доли секунды.\n"
        "• 👤 <b>Удобно:</b> перевод по @username, Telegram ID или номеру счёта СБП.\n"
        "• 🧾 <b>Инлайн-чеки:</b> отправляйте переводы прямо в чаты и группы.\n"
        "• 📥 <b>Пополнение:</b> официальная оплата звёздами (XTR).\n"
        "• 📤 <b>Вывод звёзд:</b> перевод с баланса бота на ваш личный аккаунт через 777000.\n"
        "• 📄 <b>Квитанции:</b> электронные чеки с уникальным номером транзакции.\n\n"
        "<b>Лимиты СБП:</b>\n"
        "• Минимальный перевод: 1 ⭐️\n"
        "• Максимальный перевод: 100 000 ⭐️\n"
        "• Месячный лимит: 100 000 ⭐️ / аккаунт\n"
        "────────────────────────\n"
        "<i>Безопасность транзакций обеспечивается сервисом StaticGram Bot API.</i>"
    )
    await callback.message.edit_text(info_text, reply_markup=get_back_button())
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "⚡️ <b>Команды бота СБП:</b>\n\n"
        "/start — Главное меню и баланс СБП\n"
        "/pay — Перевести звёзды по СБП\n"
        "/deposit — Пополнить счёт звёздами\n"
        "/withdraw — Вывести звёзды на аккаунт\n"
        "/cheque — Создать чек СБП для чата\n"
        "/history — История операций и чеки\n"
        "/help — Справка о сервисе",
        reply_markup=get_back_button()
    )
