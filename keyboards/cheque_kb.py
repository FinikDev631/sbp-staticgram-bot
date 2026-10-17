from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_cheque_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Создать новый чек СБП", callback_data="cheque_create")
        ],
        [
            InlineKeyboardButton(text="📋 Мои активные чеки", callback_data="cheque_list")
        ],
        [
            InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_menu")
        ]
    ])

def get_cheque_recipient_choice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Для любого участника чата", callback_data="ch_target:any")
        ],
        [
            InlineKeyboardButton(text="👤 Персонально (по @username)", callback_data="ch_target:user")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")
        ]
    ])

def get_cheque_created_kb(cheque_id: str, bot_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Отправить чек в чат",
                switch_inline_query=cheque_id
            )
        ],
        [
            InlineKeyboardButton(text="❌ Аннулировать чек", callback_data=f"cancel_ch:{cheque_id}")
        ],
        [
            InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_menu")
        ]
    ])

def get_inline_claim_kb(cheque_id: str, amount: int) -> InlineKeyboardMarkup:
    """Inline button attached to the cheque message in chat."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"⚡️ Забрать перевод ({amount:,} ⭐️)",
                callback_data=f"claim_ch:{cheque_id}"
            )
        ]
    ])

def get_inline_bill_kb(creator_id: int, amount: int) -> InlineKeyboardMarkup:
    """Inline button attached to an SBP bill in chat."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"💳 Оплатить {amount:,} ⭐️ через СБП",
                callback_data=f"pay_bill:{creator_id}:{amount}"
            )
        ]
    ])
