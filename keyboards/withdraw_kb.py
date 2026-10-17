from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_withdraw_target_kb() -> InlineKeyboardMarkup:
    """Target selection for withdrawStarBalance."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 На свой аккаунт StaticGram", callback_data="wd_target:self")
        ],
        [
            InlineKeyboardButton(text="👥 Другому пользователю (@username или ID)", callback_data="wd_target:other")
        ],
        [
            InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_menu")
        ]
    ])

def get_withdraw_amount_kb(balance: int) -> InlineKeyboardMarkup:
    buttons = []
    row1 = []
    for val in [5, 10, 25]:
        if balance >= val:
            row1.append(InlineKeyboardButton(text=f"{val} ⭐️", callback_data=f"wd_amt:{val}"))
    if row1:
        buttons.append(row1)

    row2 = []
    for val in [50, 100]:
        if balance >= val:
            row2.append(InlineKeyboardButton(text=f"{val} ⭐️", callback_data=f"wd_amt:{val}"))
    if balance > 0:
        row2.append(InlineKeyboardButton(text=f"Вывести всё ({balance} ⭐️)", callback_data=f"wd_amt:{balance}"))
    if row2:
        buttons.append(row2)

    buttons.append([InlineKeyboardButton(text="✏️ Ввести свою сумму", callback_data="wd_custom")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_withdraw_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡️ Подтвердить вывод через СБП", callback_data="confirm_withdraw_btn")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])
