from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_deposit_amounts_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="15 ⭐️", callback_data="deposit_amt:15"),
            InlineKeyboardButton(text="25 ⭐️", callback_data="deposit_amt:25"),
            InlineKeyboardButton(text="50 ⭐️", callback_data="deposit_amt:50")
        ],
        [
            InlineKeyboardButton(text="100 ⭐️", callback_data="deposit_amt:100"),
            InlineKeyboardButton(text="250 ⭐️", callback_data="deposit_amt:250"),
            InlineKeyboardButton(text="500 ⭐️", callback_data="deposit_amt:500")
        ],
        [
            InlineKeyboardButton(text="Своя сумма", callback_data="deposit_custom")
        ],
        [
            InlineKeyboardButton(text="← Назад", callback_data="back_to_menu")
        ]
    ])
