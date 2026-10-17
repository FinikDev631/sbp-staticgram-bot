from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_quick_amount_kb(balance: int) -> InlineKeyboardMarkup:
    """Quick amounts for transfer or cheque."""
    buttons = []
    row1 = []
    for val in [5, 10, 25]:
        if balance >= val:
            row1.append(InlineKeyboardButton(text=f"{val} ⭐️", callback_data=f"set_amount:{val}"))
    if row1:
        buttons.append(row1)

    row2 = []
    for val in [50, 100]:
        if balance >= val:
            row2.append(InlineKeyboardButton(text=f"{val} ⭐️", callback_data=f"set_amount:{val}"))
    if balance > 0:
        row2.append(InlineKeyboardButton(text=f"Всё ({balance} ⭐️)", callback_data=f"set_amount:{balance}"))
    if row2:
        buttons.append(row2)

    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_skip_comment_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Без сообщения (Пропустить)", callback_data="skip_comment")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])

def get_confirm_transfer_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡️ Подтвердить и перевести", callback_data="confirm_transfer_btn")],
        [InlineKeyboardButton(text="❌ Отменить перевод", callback_data="cancel_action")]
    ])
