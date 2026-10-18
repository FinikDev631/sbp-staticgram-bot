import os
import sys
import asyncio
import logging
import json
import uuid
import urllib.parse

import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, LabeledPrice

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


@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        response = web.Response(status=200)
    else:
        try:
            response = await handler(request)
        except web.HTTPException as ex:
            response = ex
        except Exception as e:
            logger.error(f"Error handling {request.path}: {e}")
            response = web.json_response({"error": str(e)}, status=500)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    return response


def safe_json_response(data, status=200):
    return web.json_response(data, status=status, dumps=lambda o: json.dumps(o, default=str))


async def start_health_server(bot: Bot = None):
    """Starts a full HTTP server on $PORT for Render Web Services & Mini App API."""
    port_str = os.getenv("PORT")
    if not port_str:
        return None
    try:
        port = int(port_str)
    except ValueError:
        return None

    app = web.Application(middlewares=[cors_middleware])
    if bot:
        app["bot"] = bot

    async def handle_health(request):
        return web.Response(text="SBP Bot is healthy and polling updates!", content_type="text/plain")

    async def handle_app_redirect(request):
        raise web.HTTPFound("/webapp/index.html")

    async def handle_user_data(request):
        uid_str = request.query.get("user_id")
        username = request.query.get("username")
        first_name = request.query.get("first_name", "Клиент")
        last_name = request.query.get("last_name")

        if not uid_str or not uid_str.isdigit():
            return safe_json_response({
                "status": "guest",
                "user": {
                    "user_id": 0,
                    "username": None,
                    "first_name": "Гость",
                    "balance": 0,
                    "account_number": "Не подключён",
                    "reserved": 0,
                    "is_guest": True
                },
                "transactions": []
            })

        user_id = int(uid_str)
        user = await db.get_user(user_id)
        if not user:
            user = await db.get_or_create_user(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
        else:
            if username or first_name:
                await db.get_or_create_user(
                    user_id=user_id,
                    username=username or user.get("username"),
                    first_name=first_name or user.get("first_name", "Клиент"),
                    last_name=last_name or user.get("last_name")
                )
                user = await db.get_user(user_id)

        reserved = await db.get_user_reserved_summary(user_id)
        transactions = await db.get_user_transactions(user_id, limit=50)

        formatted_txs = []
        for t in transactions:
            t_type = "transfer"
            is_neg = False
            title = "Операция СБП"

            raw_type = t.get("type", "")
            if raw_type == "transfer_out":
                t_type = "transfer"
                is_neg = True
                title = f"Перевод получателю {t.get('counterparty') or 'СБП'}"
            elif raw_type == "transfer_in":
                t_type = "transfer"
                is_neg = False
                title = f"Перевод от {t.get('counterparty') or 'СБП'}"
            elif raw_type in ("deposit", "admin_deposit"):
                t_type = "deposit"
                is_neg = False
                title = "Пополнение счёта Stars"
            elif raw_type == "withdrawal":
                t_type = "withdrawal"
                is_neg = True
                title = "Вывод звёзд"
            elif raw_type == "cheque_created":
                t_type = "cheque"
                is_neg = True
                title = f"Создание чека ({t.get('counterparty') or 'СБП'})"
            elif raw_type == "cheque_claimed":
                t_type = "cheque"
                is_neg = False
                title = f"Активация чека от {t.get('counterparty') or 'СБП'}"
            elif "refund" in raw_type:
                t_type = "deposit"
                is_neg = False
                title = "Возврат средств (Escrow)"

            formatted_txs.append({
                "id": t.get("trx_id"),
                "type": t_type,
                "title": title,
                "amount": -abs(t.get("amount", 0)) if is_neg else abs(t.get("amount", 0)),
                "status": "Исполнен" if t.get("status") == "success" else (t.get("status") or "Исполнен"),
                "date": str(t.get("created_at") or ""),
                "from": "Ваш счёт" if is_neg else (t.get("counterparty") or "СБП Банк"),
                "to": (t.get("counterparty") or "СБП Банк") if is_neg else "Ваш счёт",
                "comment": t.get("comment") or "Операция СБП"
            })

        bot_instance = request.app.get("bot")
        bot_username = "sbpbot"
        if bot_instance:
            try:
                me = await bot_instance.get_me()
                if me and me.username:
                    bot_username = me.username
            except Exception:
                pass

        return safe_json_response({
            "status": "ok",
            "bot_username": bot_username,
            "user": {
                "user_id": user["user_id"],
                "username": user.get("username"),
                "first_name": user.get("first_name", "Клиент"),
                "last_name": user.get("last_name"),
                "balance": user.get("balance", 0),
                "account_number": user.get("account_number") or db.generate_account_number(user["user_id"]),
                "reserved": reserved.get("total_reserved", 0),
                "cheques_count": reserved.get("cheques_count", 0),
                "pending_count": reserved.get("pending_count", 0),
                "is_guest": False
            },
            "transactions": formatted_txs
        })

    async def handle_transfer(request):
        try:
            body = await request.json()
        except Exception:
            return safe_json_response({"error": "Неверный формат данных (JSON)"}, status=400)

        user_id = body.get("user_id")
        recipient_raw = str(body.get("recipient", "")).strip()
        amount = body.get("amount")
        comment = str(body.get("comment", "")).strip() or "Перевод по СБП"

        if not user_id or not recipient_raw or not amount:
            return safe_json_response({"error": "Заполните все обязательные поля"}, status=400)

        try:
            user_id = int(user_id)
            amount = int(amount)
        except ValueError:
            return safe_json_response({"error": "Сумма и ID должны быть числами"}, status=400)

        if amount <= 0:
            return safe_json_response({"error": "Сумма должна быть больше 0 ⭐️"}, status=400)

        user = await db.get_user(user_id)
        if not user:
            return safe_json_response({"error": "Отправитель не найден в базе данных"}, status=404)

        if user["balance"] < amount:
            return safe_json_response({"error": f"Недостаточно средств. Ваш баланс: {user['balance']} ⭐️"}, status=400)

        if (recipient_raw == str(user_id) or
            (user.get("username") and recipient_raw.lstrip("@").lower() == user["username"].lower()) or
            (user.get("account_number") and recipient_raw.upper() == user["account_number"].upper())):
            return safe_json_response({"error": "Нельзя переводить средства самому себе"}, status=400)

        target_user = None
        is_pending = False
        res = None

        if recipient_raw.upper().startswith("СБП-"):
            target_user = await db.get_user_by_account(recipient_raw)
            if not target_user:
                return safe_json_response({"error": f"Счёт {recipient_raw} не зарегистрирован в СБП"}, status=404)
            res = await db.direct_transfer(user_id, target_user["user_id"], amount, comment)
        elif recipient_raw.isdigit():
            target_user = await db.get_user(int(recipient_raw))
            if not target_user:
                return safe_json_response({"error": f"Пользователь с ID {recipient_raw} не зарегистрирован в СБП"}, status=404)
            res = await db.direct_transfer(user_id, target_user["user_id"], amount, comment)
        else:
            clean_u = recipient_raw.lstrip("@").lower()
            target_user = await db.get_user_by_username(clean_u)
            if target_user:
                res = await db.direct_transfer(user_id, target_user["user_id"], amount, comment)
            else:
                res = await db.pending_transfer(user_id, clean_u, amount, comment)
                is_pending = True

        if not res:
            return safe_json_response({"error": "Ошибка при обработке перевода"}, status=500)

        bot_instance = request.app.get("bot")
        if bot_instance and target_user and not is_pending:
            try:
                s_name = f"@{user['username']}" if user.get('username') else (user.get('first_name') or f"ID {user_id}")
                await bot_instance.send_message(
                    chat_id=target_user["user_id"],
                    text=(
                        f"⚡️ <b>Вам поступил перевод СБП!</b>\n\n"
                        f"Сумма: <b>+{amount:,} ⭐️</b>\n"
                        f"От: <b>{s_name}</b>\n"
                        f"Назначение: <i>{comment}</i>\n"
                        f"Квитанция: <code>#{res['trx_id']}</code>"
                    )
                )
            except Exception as e:
                logger.debug(f"Could not send telegram notification: {e}")

        updated_user = await db.get_user(user_id)
        return safe_json_response({
            "status": "ok",
            "trx_id": res["trx_id"],
            "new_balance": updated_user["balance"],
            "is_pending": is_pending,
            "message": f"Перевод {amount} ⭐️ успешно отправлен!" if not is_pending else f"Перевод {amount} ⭐️ зарезервирован и ожидает входа @{clean_u} в бота"
        })

    async def handle_create_cheque(request):
        try:
            body = await request.json()
        except Exception:
            return safe_json_response({"error": "Неверный формат данных (JSON)"}, status=400)

        user_id = body.get("user_id")
        amount = body.get("amount")
        recipient_raw = body.get("recipient")
        comment = str(body.get("comment") or "").strip() or "Чек СБП"

        if not user_id or not amount:
            return safe_json_response({"error": "Заполните все обязательные поля"}, status=400)

        try:
            user_id = int(user_id)
            amount = int(amount)
        except ValueError:
            return safe_json_response({"error": "Сумма и ID должны быть числами"}, status=400)

        if amount <= 0:
            return safe_json_response({"error": "Номинал чека должен быть больше 0 ⭐️"}, status=400)

        user = await db.get_user(user_id)
        if not user:
            return safe_json_response({"error": "Пользователь не найден в базе данных"}, status=404)

        if user["balance"] < amount:
            return safe_json_response({"error": f"Недостаточно средств. Ваш баланс: {user['balance']} ⭐️"}, status=400)

        if recipient_raw is not None and str(recipient_raw).strip().lower() not in ("none", "null", "", "all", "any", "любой", "любой участник", "все", "для всех"):
            clean_rec = str(recipient_raw).strip().lstrip("@").lower()
        else:
            clean_rec = None

        cheque_id = await db.create_cheque(
            creator_id=user_id,
            creator_username=user.get("username"),
            amount=amount,
            recipient_username=clean_rec,
            comment=comment
        )

        if not cheque_id:
            return safe_json_response({"error": "Не удалось создать чек"}, status=500)

        bot_instance = request.app.get("bot")
        bot_username = "sbpbot"
        if bot_instance:
            try:
                me = await bot_instance.get_me()
                if me and me.username:
                    bot_username = me.username
            except Exception:
                pass

        inline_code = f"@{bot_username} {cheque_id}"
        cheque_url = f"https://staticgram.top/{bot_username}?start={cheque_id}"
        updated_user = await db.get_user(user_id)
        reserved = await db.get_user_reserved_summary(user_id)

        return safe_json_response({
            "status": "ok",
            "cheque_id": cheque_id,
            "inline_code": inline_code,
            "bot_username": bot_username,
            "cheque_url": cheque_url,
            "new_balance": updated_user["balance"],
            "new_escrow": reserved.get("total_reserved", 0),
            "amount": amount
        })

    async def handle_claim_cheque(request):
        try:
            body = await request.json()
        except Exception:
            return safe_json_response({"error": "Неверный формат данных (JSON)"}, status=400)

        user_id = body.get("user_id")
        code = str(body.get("code") or "").strip()

        if not user_id or not code:
            return safe_json_response({"error": "Укажите код чека"}, status=400)

        try:
            user_id = int(user_id)
        except ValueError:
            return safe_json_response({"error": "Некорректный ID пользователя"}, status=400)

        user = await db.get_user(user_id)
        if not user:
            return safe_json_response({"error": "Пользователь не найден в базе данных"}, status=404)

        clean_code = code
        if "start=" in clean_code:
            clean_code = clean_code.split("start=")[-1].split("&")[0]
        if "@" in clean_code:
            parts = clean_code.split()
            for p in parts:
                if p.startswith("ch_"):
                    clean_code = p
                    break
        elif " " in clean_code:
            for p in clean_code.split():
                if p.startswith("ch_"):
                    clean_code = p
                    break
        clean_code = clean_code.strip()

        if not clean_code.startswith("ch_"):
            return safe_json_response({"error": "Неверный формат кода чека (должен начинаться с ch_)"}, status=400)

        username = user.get("username")
        first_name = user.get("first_name") or "Клиент"

        res = await db.claim_cheque(clean_code, user_id, username, first_name)
        status = res.get("status")

        if status == "ok":
            amount = res["amount"]
            creator_label = f"@{res['creator_username']}" if res.get("creator_username") else f"id{res['creator_id']}"
            updated_user = await db.get_user(user_id)

            bot_instance = request.app.get("bot")
            if bot_instance:
                try:
                    claimer_label = f"@{username}" if username else first_name
                    await bot_instance.send_message(
                        res["creator_id"],
                        f"🎉 Пользователь {claimer_label} забрал ваш чек на <b>{amount:,} ⭐️</b> через приложение СБП!"
                    )
                except Exception:
                    pass

            return safe_json_response({
                "status": "ok",
                "amount": amount,
                "creator": creator_label,
                "new_balance": updated_user["balance"],
                "message": f"Чек на +{amount:,} ⭐️ успешно активирован!"
            })
        elif status == "self_claim":
            return safe_json_response({
                "error": "Это ваш собственный чек. Вы не можете забрать его сами — он предназначен для других участников чата."
            }, status=400)
        elif status == "already_claimed":
            return safe_json_response({
                "error": "Этот чек уже кем-то активирован."
            }, status=400)
        elif status == "restricted":
            return safe_json_response({
                "error": f"Этот чек предназначен только для @{res.get('expected')}."
            }, status=400)
        else:
            return safe_json_response({
                "error": "Чек не найден или уже аннулирован создателем."
            }, status=404)

    async def handle_create_invoice(request):
        try:
            body = await request.json()
        except Exception:
            return safe_json_response({"error": "Неверный формат данных (JSON)"}, status=400)

        user_id = body.get("user_id")
        amount = body.get("amount")

        if not user_id or not amount:
            return safe_json_response({"error": "Неверные параметры"}, status=400)

        try:
            user_id = int(user_id)
            amount = int(amount)
        except ValueError:
            return safe_json_response({"error": "Неверные параметры"}, status=400)

        bot_instance = request.app.get("bot")
        invoice_link = None
        if bot_instance:
            payload = f"dep_{user_id}_{amount}_{uuid.uuid4().hex[:8]}"
            title = f"Пополнение СБП (+{amount:,} ⭐️)"
            desc = f"Зачисление {amount:,} звёзд на счёт СБП"

            try:
                invoice_link = await bot_instance.create_invoice_link(
                    title=title,
                    description=desc,
                    payload=payload,
                    currency="XTR",
                    prices=[LabeledPrice(label=f"{amount:,} ⭐️", amount=amount)]
                )
            except Exception as e:
                logger.warning(f"create_invoice_link notice: {e}")

            # Also send invoice directly to user's chat with the bot so it is 100% available
            try:
                await bot_instance.send_invoice(
                    chat_id=user_id,
                    title=title,
                    description=desc,
                    payload=payload,
                    currency="XTR",
                    prices=[LabeledPrice(label=f"{amount:,} ⭐️", amount=amount)]
                )
            except Exception as e2:
                logger.warning(f"send_invoice notice: {e2}")

        tme_link = invoice_link
        if invoice_link and "staticgram.top/invoice/" in invoice_link:
            slug = invoice_link.split("/invoice/")[-1]
            tme_link = f"https://t.me/${slug}"

        return safe_json_response({
            "status": "ok",
            "invoice_link": tme_link,
            "raw_link": invoice_link,
            "bot_url": f"https://staticgram.top/sbpbot?start=deposit_{amount}"
        })

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
                "db_type": "postgres" if db._pg_pool else "sqlite",
                "db_url_set": bool(os.getenv("DATABASE_URL")),
                "users": users,
                "transactions": trxs,
                "pending": pending,
                "cheques": cheques
            }
            return safe_json_response(data)
        except Exception as e:
            return safe_json_response({"error": str(e)}, status=500)

    async def handle_credit(request):
        key = request.query.get("key")
        if key != "sbp_diag_secret_2026":
            return web.Response(text="Forbidden", status=403)
        target = request.query.get("target")
        amount_str = request.query.get("amount", "1500")
        if not target:
            return safe_json_response({"error": "missing target"}, status=400)
        try:
            amount = int(amount_str)
            user = await db.admin_find_user(target)
            if not user and target.isdigit():
                user = await db.get_or_create_user(int(target), None, "Клиент", None)
            if not user:
                return safe_json_response({"error": f"user {target} not found"}, status=404)
            trx_id = await db.credit_balance(
                user_id=user["user_id"],
                amount=amount,
                trx_type="admin_deposit",
                comment="Восстановление перевода 1500 ⭐️",
                counterparty="Администратор СБП"
            )
            u = await db.get_user(user["user_id"])
            return safe_json_response({
                "status": "success",
                "trx_id": trx_id,
                "user_id": u["user_id"],
                "username": u.get("username"),
                "balance": u["balance"]
            })
        except Exception as e:
            return safe_json_response({"error": str(e)}, status=500)

    async def handle_sql(request):
        key = request.query.get("key")
        if key != "sbp_diag_secret_2026":
            return web.Response(text="Forbidden", status=403)
        sql = request.query.get("sql")
        if not sql:
            return safe_json_response({"error": "missing sql"}, status=400)
        try:
            async with db.get_db() as c:
                if sql.strip().upper().startswith("SELECT"):
                    res = await c.fetchall(sql)
                    return safe_json_response({"result": res})
                else:
                    await c.execute(sql)
                    await c.commit()
                    return safe_json_response({"status": "executed"})
        except Exception as e:
            return safe_json_response({"error": str(e)}, status=500)

    app.router.add_get("/", handle_health)
    app.router.add_get("/healthz", handle_health)
    app.router.add_get("/app", handle_app_redirect)
    app.router.add_get("/api/user_data", handle_user_data)
    app.router.add_post("/api/transfer", handle_transfer)
    app.router.add_post("/api/create_cheque", handle_create_cheque)
    app.router.add_post("/api/claim_cheque", handle_claim_cheque)
    app.router.add_post("/api/create_invoice", handle_create_invoice)
    app.router.add_get("/api/diag", handle_diag)
    app.router.add_get("/api/credit", handle_credit)
    app.router.add_get("/api/sql", handle_sql)

    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "docs"))
    if os.path.exists(docs_dir):
        app.router.add_static("/webapp", path=docs_dir, show_index=True)
        logger.info(f"Serving static webapp files from {docs_dir} at /webapp")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"HTTP API & WebApp server listening on port {port} for Render")
    return runner


async def keep_alive(bot: Bot = None):
    """Periodically pings the public Render URL to keep the free service awake 24/7."""
    external_url = os.getenv("RENDER_EXTERNAL_URL", "https://sbp-staticgram-bot.onrender.com").rstrip("/")
    # Wait 60 seconds after startup before initial ping
    await asyncio.sleep(60)
    counter = 0
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{external_url}/healthz", timeout=15) as resp:
                    logger.info(f"Keep-alive ping sent to {external_url} (HTTP {resp.status})")
        except Exception as e:
            logger.debug(f"Keep-alive notice: {e}")

        # Periodically re-verify bot profile and descriptions remain set
        counter += 1
        if bot and counter % 5 == 0:  # every ~40 minutes
            try:
                await setup_bot_profile(bot)
            except Exception:
                pass

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
        "Оффициальный канал: https://staticgram.top/sbpnews\n"
        "⚡️ СБП: Мгновенные переводы и чеки звёзд в StaticGram"
    )
    short_desc = "⚡️ СБП: Мгновенные переводы и чеки звёзд в StaticGram"

    for lang in [None, "ru", "en"]:
        try:
            await bot.set_my_description(desc, language_code=lang)
        except Exception as e:
            logger.debug(f"Could not set description for {lang}: {e}")
        try:
            await bot.set_my_short_description(short_desc, language_code=lang)
        except Exception as e:
            logger.debug(f"Could not set short description for {lang}: {e}")

    logger.info("Bot description successfully configured.")


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

    # 3. Start health check and Mini App API web server
    web_runner = await start_health_server(bot=bot)

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
    keep_alive_task = asyncio.create_task(keep_alive(bot))

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
