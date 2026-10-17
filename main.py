import os
import sys
import asyncio
import logging
import json

import aiohttp
from aiohttp import web
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


async def start_health_server():
    """Starts a lightweight HTTP server on $PORT for Render Web Services."""
    port_str = os.getenv("PORT")
    if not port_str:
        return None
    try:
        port = int(port_str)
    except ValueError:
        return None

    app = web.Application()

    async def handle_health(request):
        return web.Response(text="SBP Bot is healthy and polling updates!", content_type="text/plain")

    async def handle_diag(request):
        key = request.query.get("key")
        if key != "sbp_diag_secret_2026":
            return web.Response(text="Forbidden", status=403)
        try:
            async with db.get_db() as conn:
                users = await conn.fetchall("SELECT * FROM users ORDER BY user_id DESC LIMIT 30")
                trxs = await conn.fetchall("SELECT * FROM transactions ORDER BY id DESC LIMIT 30")
                pending = await conn.fetchall("SELECT * FROM pending_transfers ORDER BY id DESC LIMIT 30")
                cheques = await conn.fetchall("SELECT * FROM cheques ORDER BY created_at DESC LIMIT 30")
            data = {
                "users": users,
                "transactions": trxs,
                "pending": pending,
                "cheques": cheques
            }
            return web.json_response(data, dumps=lambda o: json.dumps(o, default=str))
        except Exception as e:
            return web.json_response({"error": str(e)})

    async def handle_credit(request):
        key = request.query.get("key")
        if key != "sbp_diag_secret_2026":
            return web.Response(text="Forbidden", status=403)
        target = request.query.get("target")
        amount_str = request.query.get("amount", "1500")
        if not target:
            return web.json_response({"error": "missing target"})
        try:
            amount = int(amount_str)
            user = await db.admin_find_user(target)
            if not user and target.isdigit():
                user = await db.get_or_create_user(int(target), None, "Клиент", None)
            if not user:
                return web.json_response({"error": f"user {target} not found"})
            trx_id = await db.credit_balance(
                user_id=user["user_id"],
                amount=amount,
                trx_type="admin_deposit",
                comment="Восстановление перевода 1500 ⭐️",
                counterparty="Администратор СБП"
            )
            u = await db.get_user(user["user_id"])
            return web.json_response({
                "status": "success",
                "trx_id": trx_id,
                "user_id": u["user_id"],
                "username": u.get("username"),
                "balance": u["balance"]
            })
        except Exception as e:
            return web.json_response({"error": str(e)})

    app.router.add_get("/", handle_health)
    app.router.add_get("/healthz", handle_health)
    app.router.add_get("/api/diag", handle_diag)
    app.router.add_get("/api/credit", handle_credit)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check HTTP server listening on port {port} for Render")
    return runner


async def keep_alive():
    """Periodically pings the public Render URL to keep the free service awake 24/7."""
    external_url = os.getenv("RENDER_EXTERNAL_URL", "https://sbp-staticgram-bot.onrender.com").rstrip("/")
    # Wait 60 seconds after startup before initial ping
    await asyncio.sleep(60)
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{external_url}/healthz", timeout=15) as resp:
                    logger.info(f"Keep-alive ping sent to {external_url} (HTTP {resp.status})")
        except Exception as e:
            logger.debug(f"Keep-alive notice: {e}")
        # Ping every 8 minutes (Render sleeps after 15 min of HTTP inactivity)
        await asyncio.sleep(480)


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

    # 2. Start health check server if running on Render / Cloud host
    web_runner = await start_health_server()

    # 3. Configure AiohttpSession with custom StaticGram API server
    session = AiohttpSession(api=TelegramAPIServer.from_base(API_BASE_URL))

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(main_router)

    # 4. Verify connection and setup
    me = await bot.get_me()
    logger.info(f"Connected to StaticGram as @{me.username} (ID: {me.id}, Name: {me.first_name})")

    await setup_bot_profile(bot)

    # 5. Clear stale webhooks without dropping pending payments/updates
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Webhook cleared (pending payments preserved).")
    except Exception as e:
        logger.warning(f"Could not clear webhook: {e}")

    # 6. Start keep-alive loop to prevent Render from sleeping
    keep_alive_task = asyncio.create_task(keep_alive())

    # 7. Start polling
    logger.info("SBP Bot is now running and polling updates from StaticGram...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        keep_alive_task.cancel()
        if web_runner:
            await web_runner.cleanup()
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot terminated.")
