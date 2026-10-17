from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_inline(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
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
    ])

def get_cancel_kb(callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data=callback_data)]
    ])

def get_back_button(callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← В меню", callback_data=callback_data)]
    ])
