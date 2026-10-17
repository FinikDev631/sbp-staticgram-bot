from typing import Any, Optional
from aiogram.methods.base import TelegramMethod

class WithdrawStarBalance(TelegramMethod[dict[str, Any]]):
    """
    StaticGram extension method:
    Withdraws stars from bot's balance to owner or to any user via user_id.
    """
    __returning__ = dict
    __api_method__ = "withdrawStarBalance"

    user_id: Optional[int | str] = None
    star_count: Optional[int] = None
    request_id: Optional[str] = None


class GetMyStarBalance(TelegramMethod[dict[str, Any]]):
    """
    Gets the bot's current Star balance.
    """
    __returning__ = dict
    __api_method__ = "getMyStarBalance"


class RefundStarPayment(TelegramMethod[bool]):
    """
    Refunds a star payment by charge_id.
    """
    __returning__ = bool
    __api_method__ = "refundStarPayment"

    user_id: int
    telegram_payment_charge_id: str
