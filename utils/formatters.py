from typing import Optional, Dict, Any
from datetime import datetime

def mask_name(first_name: str, last_name: Optional[str] = None) -> str:
    """Formats name like banking apps: Иван И. or Алексей"""
    if last_name:
        return f"{first_name} {last_name[0]}."
    return first_name

def format_sbp_card(user: Dict[str, Any]) -> str:
    """Renders SBP card profile."""
    name = mask_name(user.get("first_name", "Клиент"), user.get("last_name"))
    acc = user.get("account_number", "СБП-0000-0000")
    bal = user.get("balance", 0)
    u_str = f"@{user['username']}" if user.get("username") else f"ID {user['user_id']}"

    return (
        "⚡️ <b>СИСТЕМА БЫСТРЫХ ПЛАТЕЖЕЙ (СБП)</b>\n"
        "<i>Официальный сервис мгновенных переводов звёзд</i>\n"
        "────────────────────────\n"
        f"👤 <b>Клиент:</b> {name} ({u_str})\n"
        f"💳 <b>Счёт СБП:</b> <code>{acc}</code>\n"
        f"🏦 <b>Банк:</b> StaticGram Stars СБП\n"
        f"💰 <b>Доступный остаток:</b> <b>{bal:,} ⭐️</b>\n"
        "📊 <b>Статус счёта:</b> 🟢 Активен (Лимит: 100 000 ⭐️)\n"
        "🏷 <b>Тариф:</b> 0 ⭐️ комиссия на все переводы\n"
        "────────────────────────\n"
        "<i>Выберите нужное действие в меню ниже:</i>"
    )

def format_transfer_confirmation(
    sender: Dict[str, Any],
    recipient_label: str,
    amount: int,
    comment: Optional[str] = None
) -> str:
    """Renders realistic SBP transfer confirmation screen."""
    s_acc = sender.get("account_number", "СБП-0000-0000")
    comm_str = f'"{comment}"' if comment else "Без сообщения"

    return (
        "⚡️ <b>ПОДТВЕРЖДЕНИЕ ПЕРЕВОДА ПО СБП</b>\n"
        "────────────────────────\n"
        f"👤 <b>Получатель:</b> <b>{recipient_label}</b>\n"
        "🏦 <b>Банк получателя:</b> StaticGram Stars СБП\n"
        f"💳 <b>Счёт списания:</b> <code>{s_acc}</code>\n"
        f"💰 <b>Сумма перевода:</b> <b>{amount:,} ⭐️</b>\n"
        "🏷 <b>Комиссия СБП:</b> <b>0 ⭐️ (0%)</b>\n"
        f"💬 <b>Сообщение:</b> {comm_str}\n"
        "────────────────────────\n"
        "⚠️ <i>Проверьте реквизиты перевода перед подтверждением. Перевод выполняется моментально и безотзывно.</i>"
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
    """Renders authentic electronic SBP receipt."""
    if not dt_str:
        dt_str = datetime.now().strftime("%d.%m.%Y, %H:%M:%S MSK")

    comm_line = f"\n💬 <b>Назначение:</b> {comment}" if comment else ""

    return (
        "🧾 <b>ЭЛЕКТРОННЫЙ ЧЕК СБП</b>\n"
        "════════════════════════\n"
        f"📌 <b>Операция:</b> {op_type}\n"
        f"🆔 <b>Номер транзакции:</b> <code>{trx_id}</code>\n"
        f"📅 <b>Дата и время:</b> {dt_str}\n"
        "🟢 <b>Статус:</b> <b>Исполнен</b>\n"
        "────────────────────────\n"
        f"📤 <b>Отправитель:</b> {sender_label}\n"
        f"📥 <b>Получатель:</b> {recipient_label}\n"
        "🏦 <b>Банк:</b> StaticGram Stars СБП\n"
        f"💰 <b>Сумма:</b> <b>{amount:,} ⭐️</b>\n"
        "🏷 <b>Комиссия:</b> 0 ⭐️ (Бесплатно)\n"
        f"{comm_line}"
        "════════════════════════\n"
        "⚡️ <i>Система Быстрых Платежей StaticGram</i>\n"
        "🔒 <i>Платеж защищен стандартом безопасности СБП</i>"
    )

def format_cheque_message(
    amount: int,
    creator_label: str,
    recipient_label: Optional[str] = None,
    comment: Optional[str] = None
) -> str:
    """Renders SBP Cheque card for chat inline sharing."""
    target_str = recipient_label if recipient_label else "Любой участник чата"
    comm_str = f"\n💬 <i>{comment}</i>" if comment else ""

    return (
        "⚡️ <b>ЧЕК НА ПЕРЕВОД ПО СБП</b>\n"
        "════════════════════════\n"
        f"💰 <b>Сумма:</b> <b>{amount:,} ⭐️</b>\n"
        f"👤 <b>Отправитель:</b> {creator_label}\n"
        f"🎯 <b>Получатель:</b> {target_str}\n"
        "🏦 <b>Банк:</b> StaticGram Stars СБП\n"
        "🟢 <b>Статус:</b> Готов к получению\n"
        f"{comm_str}\n"
        "════════════════════════\n"
        "👇 <i>Нажмите кнопку ниже, чтобы зачислить звёзды на свой счёт:</i>"
    )

def format_cheque_claimed_message(
    amount: int,
    creator_label: str,
    claimer_label: str,
    comment: Optional[str] = None
) -> str:
    """Renders claimed SBP Cheque card."""
    comm_str = f"\n💬 <i>{comment}</i>" if comment else ""
    return (
        "✅ <b>ЧЕК СБП УСПЕШНО АКТИВИРОВАН</b>\n"
        "════════════════════════\n"
        f"💰 <b>Сумма:</b> <b>{amount:,} ⭐️</b>\n"
        f"👤 <b>Отправитель:</b> {creator_label}\n"
        f"🎉 <b>Получил:</b> {claimer_label}\n"
        "🏦 <b>Банк:</b> StaticGram Stars СБП\n"
        "🟢 <b>Статус:</b> Зачислен\n"
        f"{comm_str}\n"
        "════════════════════════\n"
        "⚡️ <i>Средства мгновенно поступили на счёт получателя.</i>"
    )
