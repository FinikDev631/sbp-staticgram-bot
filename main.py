import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN, API_BASE_URL
import database as db
from handlers import main_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("sbp_bot")

async def setup_bot_profile(bot: Bot):
    """Sets commands, name and descriptions in StaticGram Bot API."""
    commands = [
        BotCommand(command="start", description="⚡️ Главное меню и баланс СБП"),
        BotCommand(command="pay", description="💸 Перевести по СБП"),
        BotCommand(command="deposit", description="📥 Пополнить баланс звёзд"),
        BotCommand(command="withdraw", description="📤 Вывести звёзды на аккаунт"),
        BotCommand(command="cheque", description="🧾 Создать чек СБП для чата"),
        BotCommand(command="history", description="📊 История операций и квитанции"),
        BotCommand(command="help", description="ℹ️ Справка и правила сервиса"),
    ]
    try:
        await bot.set_my_commands(commands)
        logger.info("Bot commands successfully updated.")
    except Exception as e:
        logger.warning(f"Could not set commands: {e}")

    desc = (
        "Работаю ✅\n"
        "Оффициальный канал: @sbpnews\n"
        "⚡️ СБП: Мгновенные переводы и чеки звёзд в StaticGram"
    )
    short_desc = "⚡️ СБП: Мгновенные переводы и чеки звёзд в StaticGram"

    try:
        await bot.set_my_description(desc)
        await bot.set_my_short_description(short_desc)
    except Exception:
        pass


async def main():
    logger.info("Starting SBP StaticGram Bot...")

    # 1. Initialize SQLite Database
    await db.init_db()
    logger.info("Database initialized successfully.")

    # 2. Configure AiohttpSession with custom StaticGram API server
    session = AiohttpSession(api=TelegramAPIServer.from_base(API_BASE_URL))

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(main_router)

    # 3. Verify connection and setup
    me = await bot.get_me()
    logger.info(f"Connected to StaticGram as @{me.username} (ID: {me.id}, Name: {me.first_name})")

    await setup_bot_profile(bot)

    # 4. Start polling
    logger.info("SBP Bot is now running and polling updates from StaticGram...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot terminated.")
