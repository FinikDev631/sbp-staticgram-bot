from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_withdraw_target_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Себе на аккаунт", callback_data="wd_target:self")
        ],
        [
            InlineKeyboardButton(text="Другому пользователю (@username)", callback_data="wd_target:other")
        ],
        [
            InlineKeyboardButton(text="← В меню", callback_data="back_to_menu")
        ]
    ])

def get_withdraw_amount_kb(balance: int) -> InlineKeyboardMarkup:
    row1 = []
    for val in [10, 25, 50]:
        if balance >= val:
            row1.append(InlineKeyboardButton(text=f"{val} ⭐️", callback_data=f"wd_amt:{val}"))

    row2 = []
    if balance >= 100:
        row2.append(InlineKeyboardButton(text="100 ⭐️", callback_data="wd_amt:100"))
    if balance > 0:
        row2.append(InlineKeyboardButton(text=f"Всё ({balance} ⭐️)", callback_data=f"wd_amt:{balance}"))

    buttons = []
    if row1:
        buttons.append(row1)
    if row2:
        buttons.append(row2)

    buttons.append([InlineKeyboardButton(text="Своя сумма", callback_data="wd_custom")])
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_withdraw_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить вывод", callback_data="confirm_withdraw_btn")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_action")]
    ])
