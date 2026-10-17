from aiogram.fsm.state import State, StatesGroup

class TransferState(StatesGroup):
    waiting_for_recipient = State()
    waiting_for_amount = State()
    waiting_for_comment = State()
    confirm_transfer = State()

class DepositState(StatesGroup):
    waiting_for_amount = State()

class WithdrawState(StatesGroup):
    waiting_for_target = State()
    waiting_for_amount = State()
    confirm_withdraw = State()

class ChequeState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_recipient = State()
    waiting_for_comment = State()
