from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_inline(user_id: int) -> InlineKeyboardMarkup:
    """Returns main SBP menu inline keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💸 Перевести по СБП", callback_data="menu_transfer")
        ],
        [
            InlineKeyboardButton(text="📥 Пополнить (⭐️)", callback_data="menu_deposit"),
            InlineKeyboardButton(text="📤 Вывести (⭐️)", callback_data="menu_withdraw")
        ],
        [
            InlineKeyboardButton(text="🧾 Чек СБП (Инлайн)", callback_data="menu_cheque"),
            InlineKeyboardButton(text="📊 История операций", callback_data="menu_history")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Справка и Лимиты", callback_data="menu_info")
        ]
    ])

def get_cancel_kb(callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    """Simple cancel / back button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=callback_data)]
    ])

def get_back_button(callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В главное меню", callback_data=callback_data)]
    ])
