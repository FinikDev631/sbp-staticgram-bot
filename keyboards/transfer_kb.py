from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_quick_amount_kb(balance: int) -> InlineKeyboardMarkup:
    row1 = []
    for val in [10, 25, 50]:
        if balance >= val:
            row1.append(InlineKeyboardButton(text=f"{val} ⭐️", callback_data=f"set_amount:{val}"))

    row2 = []
    if balance >= 100:
        row2.append(InlineKeyboardButton(text="100 ⭐️", callback_data="set_amount:100"))
    if balance > 0:
        row2.append(InlineKeyboardButton(text=f"Всё ({balance} ⭐️)", callback_data=f"set_amount:{balance}"))

    buttons = []
    if row1:
        buttons.append(row1)
    if row2:
        buttons.append(row2)
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_skip_comment_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="skip_comment")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_action")]
    ])

def get_confirm_transfer_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить отправку", callback_data="confirm_transfer_btn")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_action")]
    ])
