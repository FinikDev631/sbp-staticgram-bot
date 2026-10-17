import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://sbp-staticgram-bot.onrender.com/webapp/index.html")

def get_main_menu_inline(user_id: int, reserved_total: int = 0) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="📱 Открыть СБП Mini App", web_app=WebAppInfo(url=WEBAPP_URL))
        ],
        [
            InlineKeyboardButton(text="💸 Отправить", callback_data="menu_transfer"),
            InlineKeyboardButton(text="📥 Пополнить", callback_data="menu_deposit")
        ],
        [
            InlineKeyboardButton(text="📤 Вывести", callback_data="menu_withdraw"),
            InlineKeyboardButton(text="🧾 Чек", callback_data="menu_cheque")
        ],
        [
            InlineKeyboardButton(text="📊 История операций", callback_data="menu_history")
        ]
    ]

    if reserved_total > 0:
        rows.append([
            InlineKeyboardButton(
                text=f"⏳ Зарезервировано: {reserved_total:,} ⭐️ (управление)",
                callback_data="menu_reserved"
            )
        ])

    rows.append([
        InlineKeyboardButton(text="📢 Официальный канал @sbpnews", url="https://staticgram.top/sbpnews")
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_cancel_kb(callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data=callback_data)]
    ])

def get_back_button(callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← В меню", callback_data=callback_data)]
    ])
