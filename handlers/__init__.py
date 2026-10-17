from aiogram import Router

from handlers.start import router as start_router
from handlers.transfer import router as transfer_router
from handlers.deposit import router as deposit_router
from handlers.withdraw import router as withdraw_router
from handlers.cheques import router as cheques_router
from handlers.inline import router as inline_router
from handlers.history import router as history_router
from handlers.admin import router as admin_router

main_router = Router()
main_router.include_router(start_router)
main_router.include_router(transfer_router)
main_router.include_router(deposit_router)
main_router.include_router(withdraw_router)
main_router.include_router(cheques_router)
main_router.include_router(inline_router)
main_router.include_router(history_router)
main_router.include_router(admin_router)
