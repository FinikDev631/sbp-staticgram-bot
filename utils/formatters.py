from typing import Optional, Dict, Any
from datetime import datetime

def mask_name(first_name: str, last_name: Optional[str] = None) -> str:
    if last_name:
        return f"{first_name} {last_name[0]}."
    return first_name

def format_sbp_card(user: Dict[str, Any]) -> str:
    """Sleek minimalist fintech card."""
    name = mask_name(user.get("first_name", "Клиент"), user.get("last_name"))
    acc = user.get("account_number", "SBP-0000-0000")
    bal = user.get("balance", 0)
    u_str = f"@{user['username']}" if user.get("username") else f"id{user['user_id']}"

    return (
        f"⚡️ <b>СБП • Stars</b>\n\n"
        f"Баланс: <b>{bal:,} ⭐️</b>\n"
        f"Счёт: <code>{acc}</code> • {name} ({u_str})\n\n"
        f"📢 Новости СБП: <a href=\"https://staticgram.top/sbpnews\">@sbpnews</a>"
    )

def format_transfer_confirmation(
    sender: Dict[str, Any],
    recipient_label: str,
    amount: int,
    comment: Optional[str] = None
) -> str:
    """Clean transfer confirmation."""
    comm_block = f"\n• Сообщение: <i>{comment}</i>" if comment else ""
    return (
        f"<b>Отправка {amount:,} ⭐️ по СБП</b>\n\n"
        f"• Получатель: <b>{recipient_label}</b>\n"
        f"• Сумма: <b>{amount:,} ⭐️</b>\n"
        f"• Комиссия: <b>0 ⭐️</b>{comm_block}\n\n"
        f"Подтвердите перевод:"
    )

def format_electronic_receipt(
    trx_id: str,
    op_type: str,
    amount: int,
    sender_label: str,
    recipient_label: str,
    comment: Optional[str] = None,
    dt_str: Optional[str] = None
) -> str:
    """Minimal receipt like CryptoBot / Revolut."""
    if not dt_str:
        dt_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    comm_line = f"\n• Комментарий: <i>{comment}</i>" if comment else ""
    sign = "+" if "Входящий" in op_type or "Пополнение" in op_type or "Активация" in op_type else "-"

    return (
        f"<b>{op_type}</b>\n\n"
        f"Сумма: <b>{sign}{amount:,} ⭐️</b>\n"
        f"• Статус: <b>Исполнен</b>\n"
        f"• От: {sender_label}\n"
        f"• Кому: {recipient_label}\n"
        f"• Дата: {dt_str}\n"
        f"• Чек: <code>#{trx_id}</code>{comm_line}"
    )

def format_cheque_message(
    amount: int,
    creator_label: str,
    recipient_label: Optional[str] = None,
    comment: Optional[str] = None
) -> str:
    """Clean inline cheque card for chat."""
    for_whom = f"для {recipient_label}" if recipient_label else "для всех"
    comm_block = f"\n<i>«{comment}»</i>" if comment else ""

    return (
        f"⚡️ <b>Чек СБП на {amount:,} ⭐️</b>\n"
        f"От: {creator_label} • {for_whom}{comm_block}"
    )

def format_cheque_claimed_message(
    amount: int,
    creator_label: str,
    claimer_label: str,
    comment: Optional[str] = None
) -> str:
    """Clean claimed state."""
    comm_block = f"\n<i>«{comment}»</i>" if comment else ""
    return (
        f"✅ <b>Чек СБП на {amount:,} ⭐️</b>\n"
        f"От: {creator_label}\n"
        f"Забрал: {claimer_label}{comm_block}"
    )
