from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_cheque_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Создать чек", callback_data="cheque_create"),
            InlineKeyboardButton(text="Мои чеки", callback_data="cheque_list")
        ],
        [
            InlineKeyboardButton(text="← В меню", callback_data="back_to_menu")
        ]
    ])

def get_cheque_recipient_choice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Для всех", callback_data="ch_target:any"),
            InlineKeyboardButton(text="Для @username", callback_data="ch_target:user")
        ],
        [
            InlineKeyboardButton(text="Отмена", callback_data="cancel_action")
        ]
    ])

def get_cheque_created_kb(cheque_id: str, bot_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Поделиться чеком",
                switch_inline_query=cheque_id
            )
        ],
        [
            InlineKeyboardButton(text="Аннулировать чек", callback_data=f"cancel_ch:{cheque_id}")
        ],
        [
            InlineKeyboardButton(text="← В меню", callback_data="back_to_menu")
        ]
    ])

def get_inline_claim_kb(cheque_id: str, amount: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"⚡️ Получить {amount:,} ⭐️",
                callback_data=f"claim_ch:{cheque_id}"
            )
        ]
    ])

def get_inline_bill_kb(creator_id: int, amount: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"💳 Оплатить {amount:,} ⭐️",
                callback_data=f"ask_pay:{creator_id}:{amount}"
            )
        ]
    ])

def get_inline_bill_confirm_kb(creator_id: int, amount: int, payer_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"✅ Да, отправить {amount:,} ⭐️",
                callback_data=f"conf_pay:{creator_id}:{amount}:{payer_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Нет, не отправлять",
                callback_data=f"cancel_pay:{creator_id}:{amount}"
            )
        ]
    ])
