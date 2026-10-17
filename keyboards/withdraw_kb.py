from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_withdraw_method_kb() -> InlineKeyboardMarkup:
    """Choose withdrawal method: direct stars or gifts."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚡️ Прямой вывод звёзд на аккаунт (0% ком.)",
                callback_data="wd_method:direct"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎁 Вывод подарком в профиль (конвертация)",
                callback_data="wd_method:gift"
            )
        ],
        [
            InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_menu")
        ]
    ])

def get_withdraw_target_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 На свой аккаунт", callback_data="wd_target:self")
        ],
        [
            InlineKeyboardButton(text="👥 На другой аккаунт (@username или ID)", callback_data="wd_target:other")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад к выбору способа", callback_data="menu_withdraw")
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
        [InlineKeyboardButton(text="⚡️ Подтвердить вывод", callback_data="confirm_withdraw_btn")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])

def get_gifts_selection_kb(gifts: List[Dict[str, Any]], balance: int) -> InlineKeyboardMarkup:
    """Renders catalog of available gifts."""
    buttons = []
    # Deduplicate gifts by star_count to offer clean choice
    seen_stars = set()
    for g in gifts:
        cost = g.get("star_count", 0)
        gid = g.get("id")
        if cost not in seen_stars and len(buttons) < 6:
            seen_stars.add(cost)
            status = "✅" if balance >= cost else "🔒"
            buttons.append([
                InlineKeyboardButton(
                    text=f"🎁 Подарок за {cost:,} ⭐️ {status}",
                    callback_data=f"select_gift:{gid}:{cost}"
                )
            ])

    buttons.append([InlineKeyboardButton(text="◀️ Назад к выбору способа", callback_data="menu_withdraw")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_gift_kb(gift_id: str, cost: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎁 Отправить мне подарок ({cost} ⭐️)", callback_data=f"send_gift_btn:{gift_id}:{cost}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])
