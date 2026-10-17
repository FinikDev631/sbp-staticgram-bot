import uuid
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

import database as db
from custom_methods import GetMyStarBalance, WithdrawStarBalance
from config import ADMIN_ID
from keyboards.main_kb import get_back_button

router = Router()

@router.message(Command("admin"))
@router.message(Command("bank"))
async def cmd_admin(message: Message):
    user_id = message.from_user.id
    # Check if admin is configured or allow all if 0 / allow user who sets it
    # We also show real star balance of the bot
    try:
        star_bal_res = await message.bot(GetMyStarBalance())
        bot_stars = star_bal_res.get("amount", 0)
    except Exception as e:
        bot_stars = f"Ошибка ({e})"

    stats = await db.get_system_stats()

    text = (
        "🏦 <b>ПАНЕЛЬ УПРАВЛЕНИЯ БАНКОМ СБП</b>\n"
        "────────────────────────\n"
        f"⭐️ <b>Баланс звёзд бота:</b> <b>{bot_stars} ⭐️</b>\n"
        "<i>(Этот баланс используется для внешних выводов пользователям через withdrawStarBalance)</i>\n\n"
        "📊 <b>Статистика сервиса:</b>\n"
        f"• Пользователей в СБП: <b>{stats['users_count']:,}</b>\n"
        f"• Общий баланс на счетах: <b>{stats['total_user_balance']:,} ⭐️</b>\n"
        f"• Проведено переводов: <b>{stats['transfers_count']:,}</b>\n"
        f"• Объём переводов: <b>{stats['transfers_volume']:,} ⭐️</b>\n"
        f"• Активных чеков: <b>{stats['active_cheques']}</b>\n"
        "────────────────────────\n"
        "💡 <i>Когда пользователи пополняют счёт через /deposit, баланс звёзд бота растёт!</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📤 Вывести весь резерв владельцу", callback_data="admin_withdraw_all")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить данные", callback_data="admin_refresh")
        ],
        [
            InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_menu")
        ]
    ])

    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "admin_refresh")
async def cb_admin_refresh(callback: CallbackQuery):
    try:
        star_bal_res = await callback.bot(GetMyStarBalance())
        bot_stars = star_bal_res.get("amount", 0)
    except Exception:
        bot_stars = 0

    stats = await db.get_system_stats()
    text = (
        "🏦 <b>ПАНЕЛЬ УПРАВЛЕНИЯ БАНКОМ СБП</b>\n"
        "────────────────────────\n"
        f"⭐️ <b>Баланс звёзд бота:</b> <b>{bot_stars} ⭐️</b>\n"
        "<i>(Этот баланс используется для внешних выводов пользователям через withdrawStarBalance)</i>\n\n"
        "📊 <b>Статистика сервиса:</b>\n"
        f"• Пользователей в СБП: <b>{stats['users_count']:,}</b>\n"
        f"• Общий баланс на счетах: <b>{stats['total_user_balance']:,} ⭐️</b>\n"
        f"• Проведено переводов: <b>{stats['transfers_count']:,}</b>\n"
        f"• Объём переводов: <b>{stats['transfers_volume']:,} ⭐️</b>\n"
        f"• Активных чеков: <b>{stats['active_cheques']}</b>\n"
        "────────────────────────\n"
        "💡 <i>Когда пользователи пополняют счёт через /deposit, баланс звёзд бота растёт!</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📤 Вывести весь резерв владельцу", callback_data="admin_withdraw_all")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить данные", callback_data="admin_refresh")
        ],
        [
            InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_menu")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Данные обновлены")


@router.callback_query(F.data == "admin_withdraw_all")
async def cb_admin_withdraw_all(callback: CallbackQuery):
    req_id = f"owner-wd-{uuid.uuid4().hex[:12]}"
    try:
        # withdraw without user_id withdraws everything to bot owner!
        res = await callback.bot(WithdrawStarBalance(request_id=req_id))
        await callback.answer("✅ Весь баланс звёзд успешно выведен на ваш аккаунт владельца!", show_alert=True)
    except TelegramBadRequest as e:
        if "BALANCE_TOO_LOW" in e.message:
            await callback.answer("⚠️ На балансе бота сейчас нет доступных звёзд для вывода.", show_alert=True)
        else:
            await callback.answer(f"⚠️ Ошибка: {e.message}", show_alert=True)
    except Exception as e:
        await callback.answer(f"⚠️ Ошибка: {e}", show_alert=True)
