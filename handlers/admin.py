import uuid
import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest

import database as db
from custom_methods import GetMyStarBalance, WithdrawStarBalance
from config import is_admin
from keyboards.main_kb import get_back_button

router = Router()


class BroadcastState(StatesGroup):
    waiting_for_message = State()
    confirm_broadcast = State()


@router.message(Command("admin"))
@router.message(Command("bank"))
async def cmd_admin(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return

    try:
        star_bal_res = await message.bot(GetMyStarBalance())
        bot_stars = star_bal_res.get("amount", 0)
    except Exception as e:
        bot_stars = f"Ошибка ({e})"

    stats = await db.get_system_stats()

    text = (
        "🏦 <b>Панель управления банком СБП</b>\n\n"
        f"⭐️ <b>Баланс звёзд бота:</b> <b>{bot_stars} ⭐️</b>\n"
        "<i>(Используется для внешних выводов пользователям через withdrawStarBalance)</i>\n\n"
        "📊 <b>Статистика сервиса:</b>\n"
        f"• Пользователей: <b>{stats['users_count']:,}</b>\n"
        f"• Баланс на счетах: <b>{stats['total_user_balance']:,} ⭐️</b>\n"
        f"• Переводов: <b>{stats['transfers_count']:,}</b>\n"
        f"• Объём: <b>{stats['transfers_volume']:,} ⭐️</b>\n"
        f"• Активных чеков: <b>{stats['active_cheques']}</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Рассылка (/broadcast)", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="📤 Вывести резерв владельцу", callback_data="admin_withdraw_all")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_refresh")
        ],
        [
            InlineKeyboardButton(text="← В меню", callback_data="back_to_menu")
        ]
    ])

    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "admin_refresh")
async def cb_admin_refresh(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    try:
        star_bal_res = await callback.bot(GetMyStarBalance())
        bot_stars = star_bal_res.get("amount", 0)
    except Exception:
        bot_stars = 0

    stats = await db.get_system_stats()
    text = (
        "🏦 <b>Панель управления банком СБП</b>\n\n"
        f"⭐️ <b>Баланс звёзд бота:</b> <b>{bot_stars} ⭐️</b>\n"
        "<i>(Используется для внешних выводов пользователям через withdrawStarBalance)</i>\n\n"
        "📊 <b>Статистика сервиса:</b>\n"
        f"• Пользователей: <b>{stats['users_count']:,}</b>\n"
        f"• Баланс на счетах: <b>{stats['total_user_balance']:,} ⭐️</b>\n"
        f"• Переводов: <b>{stats['transfers_count']:,}</b>\n"
        f"• Объём: <b>{stats['transfers_volume']:,} ⭐️</b>\n"
        f"• Активных чеков: <b>{stats['active_cheques']}</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Рассылка (/broadcast)", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="📤 Вывести резерв владельцу", callback_data="admin_withdraw_all")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_refresh")
        ],
        [
            InlineKeyboardButton(text="← В меню", callback_data="back_to_menu")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Данные обновлены")


@router.callback_query(F.data == "admin_withdraw_all")
async def cb_admin_withdraw_all(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    req_id = f"owner-wd-{uuid.uuid4().hex[:12]}"
    try:
        res = await callback.bot(WithdrawStarBalance(request_id=req_id))
        await callback.answer("✅ Весь баланс звёзд выведен владельцу!", show_alert=True)
    except TelegramBadRequest as e:
        if "BALANCE_TOO_LOW" in e.message:
            await callback.answer("⚠️ На балансе бота нет доступных звёзд для вывода.", show_alert=True)
        else:
            await callback.answer(f"⚠️ Ошибка: {e.message}", show_alert=True)
    except Exception as e:
        await callback.answer(f"⚠️ Ошибка: {e}", show_alert=True)


# --- BROADCAST HANDLERS ---

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        text_to_send = args[1]
        await state.update_data(broadcast_type="text", text=text_to_send)
        await state.set_state(BroadcastState.confirm_broadcast)

        user_ids = await db.get_all_user_ids()
        await message.answer(
            f"📢 <b>Предпросмотр рассылки:</b>\n\n{text_to_send}\n\n"
            f"👥 Получателей в базе: <b>{len(user_ids)} чел.</b>\n\n"
            f"Запустить рассылку?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚀 Начать рассылку", callback_data="confirm_broadcast_now"),
                    InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")
                ]
            ])
        )
        return

    await state.set_state(BroadcastState.waiting_for_message)
    await message.answer(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Отправьте сообщение (текст, фото, видео или перешлите готовый пост), которое нужно разослать всем пользователям СБП:\n\n"
        "<i>Вы сможете посмотреть предпросмотр перед подтверждением.</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")]
        ])
    )


@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await state.set_state(BroadcastState.waiting_for_message)
    await callback.message.answer(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Отправьте сообщение (текст, фото, видео или перешлите готовый пост), которое нужно разослать всем пользователям СБП:\n\n"
        "<i>Вы сможете посмотреть предпросмотр перед подтверждением.</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")]
        ])
    )
    await callback.answer()


@router.message(BroadcastState.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.update_data(
        broadcast_type="copy",
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    await state.set_state(BroadcastState.confirm_broadcast)

    user_ids = await db.get_all_user_ids()

    await message.answer("👆 <b>Сообщение для рассылки принято!</b>")
    await message.answer(
        f"👥 Получателей в базе: <b>{len(user_ids)} чел.</b>\n\n"
        f"Запустить рассылку?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Начать рассылку", callback_data="confirm_broadcast_now"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")
            ]
        ])
    )


@router.callback_query(F.data == "confirm_broadcast_now", BroadcastState.confirm_broadcast)
async def process_confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    data = await state.get_data()
    await state.clear()

    status_msg = await callback.message.answer("⏳ <b>Рассылка запущена...</b>")
    await callback.answer()

    user_ids = await db.get_all_user_ids()
    total = len(user_ids)
    success = 0
    failed = 0

    b_type = data.get("broadcast_type")
    from_chat_id = data.get("from_chat_id")
    msg_id = data.get("message_id")
    plain_text = data.get("text")

    for uid in user_ids:
        try:
            if b_type == "copy":
                await callback.bot.copy_message(
                    chat_id=uid,
                    from_chat_id=from_chat_id,
                    message_id=msg_id
                )
            else:
                await callback.bot.send_message(chat_id=uid, text=plain_text)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.04)

    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"• Всего пользователей: <b>{total}</b>\n"
        f"• Успешно доставлено: <b>{success}</b>\n"
        f"• Ошибок / заблокировали: <b>{failed}</b>"
    )


@router.callback_query(F.data == "cancel_broadcast")
async def cb_cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Рассылка отменена.")
    await callback.answer()
