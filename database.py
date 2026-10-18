import os
import aiosqlite
import asyncpg
import random
import string
import uuid
import hashlib
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from config import DB_PATH, DATABASE_URL

logger = logging.getLogger("sbp_bot.db")
_pg_pool: Optional[asyncpg.Pool] = None


def generate_account_number(user_id: int) -> str:
    """Generates a memorable 5-digit SBP account format: СБП-XXXXX"""
    val = int(hashlib.md5(f"sbp_acc_{user_id}".encode()).hexdigest(), 16)
    num = (val % 90000) + 10000
    return f"СБП-{num}"


def normalize_account_input(raw: str) -> str:
    """Normalizes any account input (Latin/Cyrillic, with/without hyphen or prefix) to canonical form."""
    s = raw.strip()
    if s.upper().startswith("SBP"):
        s = "СБП" + s[3:]
    elif s.upper().startswith("СБП"):
        s = "СБП" + s[3:]

    if s.startswith("СБП"):
        rest = s[3:].lstrip(" -:")
        return f"СБП-{rest}"

    digits = "".join(c for c in s if c.isdigit())
    if len(digits) == 5:
        return f"СБП-{digits}"
    if len(digits) == 8:
        return f"СБП-{digits[:4]}-{digits[4:]}"

    return s.upper()


async def generate_unique_account_number(user_id: int, db) -> str:
    """Generates a guaranteed unique 5-digit SBP account number."""
    val = int(hashlib.md5(f"sbp_acc_{user_id}".encode()).hexdigest(), 16)
    candidate = f"СБП-{(val % 90000) + 10000}"
    row = await db.fetchone("SELECT user_id FROM users WHERE account_number = ? AND user_id != ?", (candidate, user_id))
    if not row:
        return candidate
    for _ in range(50):
        cand = f"СБП-{random.randint(10000, 99999)}"
        r = await db.fetchone("SELECT user_id FROM users WHERE account_number = ?", (cand,))
        if not r:
            return cand
    return f"СБП-{random.randint(100000, 999999)}"


def generate_trx_id(prefix: str = "TRX") -> str:
    """Generates unique transaction ID like SBP-TRX-20261017-X8K2"""
    date_str = datetime.now().strftime("%Y%m%d")
    rnd = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"SBP-{prefix}-{date_str}-{rnd}"


def to_pg_query(query: str) -> str:
    """Converts SQLite '?' parameter placeholders to PostgreSQL '$1, $2, ...' placeholders."""
    parts = query.split("?")
    if len(parts) == 1:
        return query
    res = []
    for i, part in enumerate(parts[:-1]):
        res.append(part)
        res.append(f"${i + 1}")
    res.append(parts[-1])
    return "".join(res)


def _row_to_dict(row) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.strftime("%Y-%m-%d %H:%M:%S")
    return d


def _rows_to_list(rows) -> List[Dict[str, Any]]:
    return [_row_to_dict(r) for r in rows if r]


class DBConnection:
    def __init__(self, is_pg: bool, conn=None, aio_db=None):
        self.is_pg = is_pg
        self.conn = conn
        self.aio_db = aio_db

    async def execute(self, query: str, params: tuple = ()):
        if self.is_pg:
            q = to_pg_query(query)
            return await self.conn.execute(q, *params)
        else:
            return await self.aio_db.execute(query, params)

    async def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        if self.is_pg:
            q = to_pg_query(query)
            row = await self.conn.fetchrow(q, *params)
            return _row_to_dict(row)
        else:
            cursor = await self.aio_db.execute(query, params)
            row = await cursor.fetchone()
            return _row_to_dict(row)

    async def fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        if self.is_pg:
            q = to_pg_query(query)
            rows = await self.conn.fetch(q, *params)
            return _rows_to_list(rows)
        else:
            cursor = await self.aio_db.execute(query, params)
            rows = await cursor.fetchall()
            return _rows_to_list(rows)

    async def commit(self):
        if not self.is_pg:
            await self.aio_db.commit()


@asynccontextmanager
async def get_db():
    if _pg_pool:
        async with _pg_pool.acquire() as conn:
            async with conn.transaction():
                yield DBConnection(is_pg=True, conn=conn)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            yield DBConnection(is_pg=False, aio_db=db)


async def _migrate_from_sqlite(pg_conn):
    """Automatically imports data from existing SQLite DB file into PostgreSQL."""
    if not os.path.exists(DB_PATH):
        return

    logger.info("Migrating existing SQLite database into PostgreSQL...")
    async with aiosqlite.connect(DB_PATH) as s_db:
        s_db.row_factory = aiosqlite.Row

        # 1. Users
        cursor = await s_db.execute("SELECT * FROM users")
        users = await cursor.fetchall()
        for u in users:
            d = dict(u)
            await pg_conn.execute(
                """INSERT INTO users (user_id, username, first_name, last_name, balance, account_number, is_blocked)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)
                   ON CONFLICT (user_id) DO UPDATE SET balance = EXCLUDED.balance""",
                d["user_id"], d.get("username"), d.get("first_name"), d.get("last_name"),
                d.get("balance", 0), d.get("account_number"), d.get("is_blocked", 0)
            )

        # 2. Transactions
        cursor = await s_db.execute("SELECT * FROM transactions")
        trxs = await cursor.fetchall()
        for t in trxs:
            d = dict(t)
            await pg_conn.execute(
                """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                   ON CONFLICT (trx_id) DO NOTHING""",
                d["trx_id"], d.get("user_id"), d.get("counterparty"), d.get("counterparty_id"),
                d.get("amount", 0), d.get("type"), d.get("status", "success"), d.get("comment")
            )

        # 3. Cheques
        cursor = await s_db.execute("SELECT * FROM cheques")
        cheques = await cursor.fetchall()
        for ch in cheques:
            d = dict(ch)
            await pg_conn.execute(
                """INSERT INTO cheques (cheque_id, creator_id, creator_username, amount, recipient_id, recipient_username, claimed_by_id, claimed_by_username, status, comment)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                   ON CONFLICT (cheque_id) DO NOTHING""",
                d["cheque_id"], d.get("creator_id"), d.get("creator_username"), d.get("amount", 0),
                d.get("recipient_id"), d.get("recipient_username"), d.get("claimed_by_id"),
                d.get("claimed_by_username"), d.get("status", "active"), d.get("comment")
            )

        # 4. Pending transfers
        cursor = await s_db.execute("SELECT * FROM pending_transfers")
        pts = await cursor.fetchall()
        for p in pts:
            d = dict(p)
            await pg_conn.execute(
                """INSERT INTO pending_transfers (trx_id, sender_id, sender_username, recipient_username, amount, comment, status)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)
                   ON CONFLICT (trx_id) DO NOTHING""",
                d["trx_id"], d.get("sender_id"), d.get("sender_username"), d.get("recipient_username"),
                d.get("amount", 0), d.get("comment"), d.get("status", "pending")
            )

    logger.info(f"Migration complete: {len(users)} users, {len(trxs)} transactions, {len(cheques)} cheques, {len(pts)} pending transfers.")


async def init_db():
    global _pg_pool
    if DATABASE_URL:
        url = DATABASE_URL.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        logger.info("Initializing PostgreSQL database...")
        pool_kwargs = {"min_size": 1, "max_size": 10}
        if "pooler.supabase.com" in url or ":6543" in url or "pgbouncer" in url.lower():
            pool_kwargs["statement_cache_size"] = 0
        _pg_pool = await asyncpg.create_pool(dsn=url, **pool_kwargs)
        async with _pg_pool.acquire() as conn:
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance BIGINT DEFAULT 0,
                account_number TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blocked INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                trx_id TEXT UNIQUE,
                user_id BIGINT,
                counterparty TEXT,
                counterparty_id BIGINT,
                amount BIGINT,
                type TEXT,
                status TEXT,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS cheques (
                cheque_id TEXT PRIMARY KEY,
                creator_id BIGINT,
                creator_username TEXT,
                amount BIGINT,
                recipient_id BIGINT,
                recipient_username TEXT,
                claimed_by_id BIGINT,
                claimed_by_username TEXT,
                status TEXT DEFAULT 'active',
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                claimed_at TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS pending_transfers (
                id SERIAL PRIMARY KEY,
                trx_id TEXT UNIQUE,
                sender_id BIGINT,
                sender_username TEXT,
                recipient_username TEXT,
                amount BIGINT,
                comment TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Ensure old_account_number column exists and auto-migrate long accounts to short 5-digit format
            try:
                await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS old_account_number TEXT")
            except Exception:
                pass

            try:
                old_rows = await conn.fetch("SELECT user_id, account_number FROM users WHERE account_number LIKE '%-%-%' OR LENGTH(account_number) > 10")
                for r in old_rows:
                    uid = r["user_id"]
                    old_acc = r["account_number"]
                    val = int(hashlib.md5(f"sbp_acc_{uid}".encode()).hexdigest(), 16)
                    cand = f"СБП-{(val % 90000) + 10000}"
                    exists = await conn.fetchval("SELECT user_id FROM users WHERE account_number = $1 AND user_id != $2", cand, uid)
                    if exists:
                        cand = f"СБП-{random.randint(10000, 99999)}"
                    await conn.execute("UPDATE users SET account_number = $1, old_account_number = $2 WHERE user_id = $3", cand, old_acc, uid)
                if old_rows:
                    logger.info(f"Auto-migrated {len(old_rows)} accounts to short 5-digit format in PostgreSQL.")
            except Exception as e:
                logger.warning(f"Could not migrate accounts in PostgreSQL: {e}")

            # Check if users is empty and auto-migrate from sqlite
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            if user_count == 0 and os.path.exists(DB_PATH):
                try:
                    await _migrate_from_sqlite(conn)
                except Exception as e:
                    logger.warning(f"Could not auto-migrate from SQLite: {e}")
        logger.info("PostgreSQL database initialized successfully.")
    else:
        logger.info("Using SQLite database (DATABASE_URL not set).")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance INTEGER DEFAULT 0,
                account_number TEXT UNIQUE,
                old_account_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blocked INTEGER DEFAULT 0
            )
            """)
            try:
                await db.execute("ALTER TABLE users ADD COLUMN old_account_number TEXT")
            except Exception:
                pass

            try:
                cursor = await db.execute("SELECT user_id, account_number FROM users WHERE account_number LIKE '%-%-%' OR LENGTH(account_number) > 10")
                old_rows = await cursor.fetchall()
                for r in old_rows:
                    uid = r[0]
                    old_acc = r[1]
                    val = int(hashlib.md5(f"sbp_acc_{uid}".encode()).hexdigest(), 16)
                    cand = f"СБП-{(val % 90000) + 10000}"
                    c2 = await db.execute("SELECT user_id FROM users WHERE account_number = ? AND user_id != ?", (cand, uid))
                    if await c2.fetchone():
                        cand = f"СБП-{random.randint(10000, 99999)}"
                    await db.execute("UPDATE users SET account_number = ?, old_account_number = ? WHERE user_id = ?", (cand, old_acc, uid))
                if old_rows:
                    logger.info(f"Auto-migrated {len(old_rows)} accounts to short 5-digit format in SQLite.")
            except Exception as e:
                logger.warning(f"Could not migrate accounts in SQLite: {e}")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trx_id TEXT UNIQUE,
                user_id INTEGER,
                counterparty TEXT,
                counterparty_id INTEGER,
                amount INTEGER,
                type TEXT,
                status TEXT,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS cheques (
                cheque_id TEXT PRIMARY KEY,
                creator_id INTEGER,
                creator_username TEXT,
                amount INTEGER,
                recipient_id INTEGER,
                recipient_username TEXT,
                claimed_by_id INTEGER,
                claimed_by_username TEXT,
                status TEXT DEFAULT 'active',
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                claimed_at TIMESTAMP
            )
            """)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS pending_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trx_id TEXT UNIQUE,
                sender_id INTEGER,
                sender_username TEXT,
                recipient_username TEXT,
                amount INTEGER,
                comment TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            await db.commit()


async def get_or_create_user(user_id: int, username: Optional[str], first_name: str, last_name: Optional[str]) -> Dict[str, Any]:
    username_clean = username.lstrip("@").lower() if username else None
    async with get_db() as db:
        row = await db.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))

        if row:
            await db.execute(
                "UPDATE users SET username = ?, first_name = ?, last_name = ? WHERE user_id = ?",
                (username_clean, first_name, last_name, user_id)
            )
            user_data = dict(row)
            user_data["username"] = username_clean
            user_data["first_name"] = first_name
            user_data["last_name"] = last_name
        else:
            acc_num = await generate_unique_account_number(user_id, db)
            await db.execute(
                "INSERT INTO users (user_id, username, first_name, last_name, balance, account_number) VALUES (?, ?, ?, ?, 0, ?)",
                (user_id, username_clean, first_name, last_name, acc_num)
            )
            user_data = await db.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))

        # Check pending transfers for this username
        claimed_pending = []
        if username_clean:
            pending_list = await db.fetchall(
                "SELECT * FROM pending_transfers WHERE recipient_username = ? AND status = 'pending'",
                (username_clean,)
            )
            for pt in pending_list:
                amount = pt["amount"]
                await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
                await db.execute("UPDATE pending_transfers SET status = 'claimed' WHERE id = ?", (pt["id"],))

                await db.execute(
                    """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
                       VALUES (?, ?, ?, ?, ?, 'transfer_in', 'success', ?)""",
                    (pt["trx_id"], user_id, f"@{pt['sender_username']}" if pt.get('sender_username') else f"ID {pt['sender_id']}",
                     pt['sender_id'], amount, pt.get('comment') or "Перевод по СБП")
                )
                claimed_pending.append(dict(pt))

            if pending_list:
                user_data = await db.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))

        user_data["claimed_pending"] = claimed_pending
        await db.commit()
        return user_data


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        return await db.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    clean_u = username.lstrip("@").lower()
    async with get_db() as db:
        return await db.fetchone("SELECT * FROM users WHERE username = ?", (clean_u,))


async def get_user_by_account(account_number: str) -> Optional[Dict[str, Any]]:
    if not account_number or not isinstance(account_number, str):
        return None
    raw = account_number.strip()
    norm = normalize_account_input(raw)
    digits = "".join(c for c in raw if c.isdigit())

    candidates = {raw, raw.upper(), norm, norm.upper()}
    if digits:
        candidates.add(digits)
        candidates.add(f"СБП-{digits}")
        candidates.add(f"SBP-{digits}")
        if len(digits) == 8:
            candidates.add(f"СБП-{digits[:4]}-{digits[4:]}")
            candidates.add(f"SBP-{digits[:4]}-{digits[4:]}")
            candidates.add(f"{digits[:4]}-{digits[4:]}")

    cand_list = list(candidates)
    placeholders = ", ".join(["?"] * len(cand_list))

    async with get_db() as db:
        query = f"SELECT * FROM users WHERE account_number IN ({placeholders}) OR old_account_number IN ({placeholders}) LIMIT 1"
        params = cand_list + cand_list
        return await db.fetchone(query, tuple(params))


async def admin_find_user(query: str) -> Optional[Dict[str, Any]]:
    """Flexible user search for admin by @username, ID, SBP account, or name."""
    q = query.strip()
    if q.startswith("@"):
        return await get_user_by_username(q[1:])
    if q.lower().startswith("id") and q[2:].isdigit():
        return await get_user(int(q[2:]))
    if q.upper().startswith("СБП") or q.upper().startswith("SBP"):
        acc = await get_user_by_account(q)
        if acc:
            return acc
    if q.isdigit():
        if len(q) == 5:
            acc = await get_user_by_account(q)
            if acc:
                return acc
        u = await get_user(int(q))
        if u:
            return u
    acc = await get_user_by_account(q)
    if acc:
        return acc
    u = await get_user_by_username(q)
    if u:
        return u

    async with get_db() as db:
        return await db.fetchone(
            "SELECT * FROM users WHERE first_name LIKE ? OR username LIKE ? LIMIT 1",
            (f"%{q}%", f"%{q}%")
        )


async def credit_balance(user_id: int, amount: int, trx_type: str, comment: str, counterparty: str = "СБП Банк", custom_trx_id: Optional[str] = None) -> str:
    trx_id = custom_trx_id or generate_trx_id(prefix="DEP" if trx_type == "deposit" else "TRX")
    async with get_db() as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.execute(
            """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
               VALUES (?, ?, ?, NULL, ?, ?, 'success', ?)""",
            (trx_id, user_id, counterparty, amount, trx_type, comment)
        )
        await db.commit()
    return trx_id


async def debit_balance(user_id: int, amount: int, trx_type: str, comment: str, counterparty: str = "Вывод СБП") -> Optional[str]:
    trx_id = generate_trx_id(prefix="WTH" if trx_type == "withdrawal" else "TRX")
    async with get_db() as db:
        row = await db.fetchone("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        if not row or row["balance"] < amount:
            return None

        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        await db.execute(
            """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
               VALUES (?, ?, ?, NULL, ?, ?, 'success', ?)""",
            (trx_id, user_id, counterparty, amount, trx_type, comment)
        )
        await db.commit()
    return trx_id


async def direct_transfer(sender_id: int, recipient_id: int, amount: int, comment: Optional[str]) -> Optional[Dict[str, Any]]:
    trx_id = generate_trx_id(prefix="TRX")
    async with get_db() as db:
        sender = await db.fetchone("SELECT * FROM users WHERE user_id = ?", (sender_id,))
        if not sender or sender["balance"] < amount:
            return None

        recipient = await db.fetchone("SELECT * FROM users WHERE user_id = ?", (recipient_id,))
        if not recipient:
            return None

        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, sender_id))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, recipient_id))

        sender_label = f"@{sender['username']}" if sender.get("username") else f"{sender['first_name']} (ID {sender['user_id']})"
        recipient_label = f"@{recipient['username']}" if recipient.get("username") else f"{recipient['first_name']} (ID {recipient['user_id']})"

        trx_id_out = f"{trx_id}-OUT"
        trx_id_in = f"{trx_id}-IN"

        await db.execute(
            """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
               VALUES (?, ?, ?, ?, ?, 'transfer_out', 'success', ?)""",
            (trx_id_out, sender_id, recipient_label, recipient_id, amount, comment or "Перевод по СБП")
        )
        await db.execute(
            """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
               VALUES (?, ?, ?, ?, ?, 'transfer_in', 'success', ?)""",
            (trx_id_in, recipient_id, sender_label, sender_id, amount, comment or "Перевод по СБП")
        )
        await db.commit()

        return {
            "trx_id": trx_id,
            "sender": dict(sender),
            "recipient": dict(recipient),
            "amount": amount,
            "comment": comment,
            "created_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }


async def pending_transfer(sender_id: int, recipient_username: str, amount: int, comment: Optional[str]) -> Optional[Dict[str, Any]]:
    trx_id = generate_trx_id(prefix="TRX")
    clean_u = recipient_username.lstrip("@").lower()

    async with get_db() as db:
        sender = await db.fetchone("SELECT * FROM users WHERE user_id = ?", (sender_id,))
        if not sender or sender["balance"] < amount:
            return None

        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, sender_id))
        await db.execute(
            """INSERT INTO pending_transfers (trx_id, sender_id, sender_username, recipient_username, amount, comment)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (trx_id, sender_id, sender.get("username"), clean_u, amount, comment or "Перевод по СБП")
        )
        await db.execute(
            """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
               VALUES (?, ?, ?, NULL, ?, 'transfer_out', 'success', ?)""",
            (trx_id, sender_id, f"@{clean_u}", amount, comment or "Перевод по СБП (ожидает активации)")
        )
        await db.commit()

        return {
            "trx_id": trx_id,
            "sender": dict(sender),
            "recipient_username": clean_u,
            "amount": amount,
            "comment": comment,
            "created_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }


async def cancel_pending_transfer(trx_id: str, sender_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    clean_trx = trx_id.strip().lstrip("#")
    async with get_db() as db:
        query = "SELECT * FROM pending_transfers WHERE (trx_id = ? OR trx_id LIKE ?) AND status = 'pending'"
        params = [clean_trx, f"%{clean_trx}%"]
        if sender_id is not None:
            query += " AND sender_id = ?"
            params.append(sender_id)

        pt = await db.fetchone(query, tuple(params))
        if not pt:
            return None

        pt_id = pt["id"]
        actual_sender_id = pt["sender_id"]
        amount = pt["amount"]
        recipient_username = pt["recipient_username"]

        await db.execute("UPDATE pending_transfers SET status = 'cancelled' WHERE id = ?", (pt_id,))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, actual_sender_id))

        ref_trx = generate_trx_id(prefix="REF")
        await db.execute(
            """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
               VALUES (?, ?, ?, NULL, ?, 'transfer_refund', 'success', ?)""",
            (ref_trx, actual_sender_id, f"@{recipient_username}", amount, f"Возврат отложенного перевода {pt['trx_id']}")
        )
        await db.commit()
        return dict(pt)


async def get_pending_transfer_by_query(query: str) -> Optional[Dict[str, Any]]:
    clean_q = query.strip().lstrip("#")
    async with get_db() as db:
        return await db.fetchone(
            "SELECT * FROM pending_transfers WHERE trx_id = ? OR trx_id LIKE ? LIMIT 1",
            (clean_q, f"%{clean_q}%")
        )


async def create_cheque(creator_id: int, creator_username: Optional[str], amount: int,
                        recipient_username: Optional[str] = None, comment: Optional[str] = None) -> Optional[str]:
    cheque_id = f"ch_{uuid.uuid4().hex[:12]}"
    clean_rec = recipient_username.lstrip("@").lower() if recipient_username else None

    async with get_db() as db:
        row = await db.fetchone("SELECT balance FROM users WHERE user_id = ?", (creator_id,))
        if not row or row["balance"] < amount:
            return None

        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, creator_id))
        await db.execute(
            """INSERT INTO cheques (cheque_id, creator_id, creator_username, amount, recipient_username, comment)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (cheque_id, creator_id, creator_username, amount, clean_rec, comment)
        )

        trx_id = generate_trx_id(prefix="CHK")
        await db.execute(
            """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
               VALUES (?, ?, ?, NULL, ?, 'cheque_created', 'success', ?)""",
            (trx_id, creator_id, f"Чек {cheque_id}", amount, comment or "Создание чека СБП")
        )
        await db.commit()
        return cheque_id


async def get_cheque(cheque_id: str) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        return await db.fetchone("SELECT * FROM cheques WHERE cheque_id = ?", (cheque_id,))


async def claim_cheque(cheque_id: str, claimer_id: int, claimer_username: Optional[str], claimer_name: str) -> Dict[str, Any]:
    clean_u = claimer_username.lstrip("@").lower() if claimer_username else None

    async with get_db() as db:
        cheque = await db.fetchone("SELECT * FROM cheques WHERE cheque_id = ?", (cheque_id,))
        if not cheque:
            return {"status": "not_found"}

        if cheque["status"] != "active":
            return {"status": "already_claimed", "claimed_by": cheque.get("claimed_by_username")}

        if cheque["creator_id"] == claimer_id:
            return {"status": "self_claim"}

        rec_u = cheque.get("recipient_username")
        if rec_u and str(rec_u).strip().lower() not in ("none", "null", ""):
            if not clean_u or clean_u != rec_u.lower():
                return {"status": "restricted", "expected": rec_u}

        amount = cheque["amount"]
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, claimer_id))
        await db.execute(
            """UPDATE cheques SET status = 'claimed', claimed_by_id = ?, claimed_by_username = ?, claimed_at = CURRENT_TIMESTAMP
               WHERE cheque_id = ?""",
            (claimer_id, clean_u or claimer_name, cheque_id)
        )

        trx_id = generate_trx_id(prefix="CHK")
        creator_label = f"@{cheque['creator_username']}" if cheque.get("creator_username") else f"ID {cheque['creator_id']}"
        await db.execute(
            """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
               VALUES (?, ?, ?, ?, ?, 'cheque_claimed', 'success', ?)""",
            (trx_id, claimer_id, creator_label, cheque['creator_id'], amount, cheque.get('comment') or "Активация чека СБП")
        )
        await db.commit()

        return {
            "status": "ok",
            "amount": amount,
            "creator_id": cheque["creator_id"],
            "creator_username": cheque.get("creator_username"),
            "comment": cheque.get("comment")
        }


async def cancel_cheque(cheque_id: str, user_id: int) -> bool:
    async with get_db() as db:
        cheque = await db.fetchone(
            "SELECT * FROM cheques WHERE cheque_id = ? AND creator_id = ? AND status = 'active'",
            (cheque_id, user_id)
        )
        if not cheque:
            return False

        amount = cheque["amount"]
        await db.execute("UPDATE cheques SET status = 'cancelled' WHERE cheque_id = ?", (cheque_id,))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))

        trx_id = generate_trx_id(prefix="REF")
        await db.execute(
            """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
               VALUES (?, ?, ?, NULL, ?, 'cheque_refund', 'success', 'Отмена чека СБП')""",
            (trx_id, user_id, f"Чек {cheque_id}", amount)
        )
        await db.commit()
        return True


async def admin_cancel_cheque(cheque_id: str) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        cheque = await db.fetchone("SELECT * FROM cheques WHERE cheque_id = ? AND status = 'active'", (cheque_id,))
        if not cheque:
            return None

        amount = cheque["amount"]
        creator_id = cheque["creator_id"]
        await db.execute("UPDATE cheques SET status = 'cancelled' WHERE cheque_id = ?", (cheque_id,))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, creator_id))

        trx_id = generate_trx_id(prefix="REF")
        await db.execute(
            """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
               VALUES (?, ?, ?, NULL, ?, 'cheque_refund', 'success', 'Аннулирование чека администратором')""",
            (trx_id, creator_id, f"Чек {cheque_id}", amount)
        )
        await db.commit()
        return dict(cheque)


async def admin_find_cheque(query_str: str) -> Optional[Dict[str, Any]]:
    q = query_str.strip()
    if "start=" in q:
        q = q.split("start=")[-1].split("&")[0].split()[0]
    q = q.strip()

    variants = [q]
    if not q.startswith("ch_"):
        variants.append(f"ch_{q}")
    else:
        variants.append(q[3:])

    async with get_db() as db:
        for var in variants:
            row = await db.fetchone("SELECT * FROM cheques WHERE cheque_id = ?", (var,))
            if row:
                return row

        return await db.fetchone("SELECT * FROM cheques WHERE cheque_id LIKE ? LIMIT 1", (f"%{q}%",))


async def admin_find_any_operation(query_str: str) -> Optional[Dict[str, Any]]:
    q = query_str.strip().lstrip("#")
    if "start=" in q:
        q = q.split("start=")[-1].split("&")[0].split()[0]
    q = q.strip()

    pt = await get_pending_transfer_by_query(q)
    if pt:
        return {"type": "pending_transfer", "data": pt}

    ch = await admin_find_cheque(q)
    if ch:
        return {"type": "cheque", "data": ch}

    trx = await admin_find_transaction(q)
    if trx:
        return {"type": "transaction", "data": trx}

    return None


async def admin_get_recent_cheques(limit: int = 5) -> List[Dict[str, Any]]:
    async with get_db() as db:
        return await db.fetchall("SELECT * FROM cheques ORDER BY created_at DESC LIMIT ?", (limit,))


async def admin_get_cheques(limit: int = 10, offset: int = 0, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    async with get_db() as db:
        if status_filter and status_filter != "all":
            return await db.fetchall(
                "SELECT * FROM cheques WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (status_filter, limit, offset)
            )
        else:
            return await db.fetchall(
                "SELECT * FROM cheques ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )


async def admin_count_cheques(status_filter: Optional[str] = None) -> int:
    async with get_db() as db:
        if status_filter and status_filter != "all":
            r = await db.fetchone("SELECT COUNT(*) as c FROM cheques WHERE status = ?", (status_filter,))
        else:
            r = await db.fetchone("SELECT COUNT(*) as c FROM cheques")
        return r["c"] if r else 0


async def admin_find_transaction(query_str: str) -> Optional[Dict[str, Any]]:
    clean = query_str.strip().lstrip("#")
    async with get_db() as db:
        # 1. Exact match
        row = await db.fetchone("SELECT * FROM transactions WHERE trx_id = ?", (clean,))
        if row:
            return row
        # 2. Case-insensitive substring
        row = await db.fetchone("SELECT * FROM transactions WHERE trx_id LIKE ? LIMIT 1", (f"%{clean}%",))
        if row:
            return row
        # 3. Numeric ID
        if clean.isdigit():
            row = await db.fetchone("SELECT * FROM transactions WHERE id = ?", (int(clean),))
            if row:
                return row
        return None


async def admin_get_recent_transactions(limit: int = 10, offset: int = 0, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
    async with get_db() as db:
        if filter_type and filter_type != "all":
            if filter_type == "transfer":
                return await db.fetchall(
                    "SELECT * FROM transactions WHERE type IN ('transfer_out', 'transfer_in') ORDER BY id DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                )
            elif filter_type == "deposit":
                return await db.fetchall(
                    "SELECT * FROM transactions WHERE type IN ('deposit', 'admin_deposit', 'admin_give') ORDER BY id DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                )
            elif filter_type == "withdrawal":
                return await db.fetchall(
                    "SELECT * FROM transactions WHERE type IN ('withdrawal', 'admin_debit', 'admin_take') ORDER BY id DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                )
            elif filter_type == "cheque":
                return await db.fetchall(
                    "SELECT * FROM transactions WHERE type IN ('cheque_created', 'cheque_claimed', 'cheque_refund') ORDER BY id DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                )
            else:
                return await db.fetchall(
                    "SELECT * FROM transactions WHERE type = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                    (filter_type, limit, offset)
                )
        else:
            return await db.fetchall(
                "SELECT * FROM transactions ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )


async def admin_count_transactions(filter_type: Optional[str] = None) -> int:
    async with get_db() as db:
        if filter_type and filter_type != "all":
            if filter_type == "transfer":
                r = await db.fetchone("SELECT COUNT(*) as c FROM transactions WHERE type IN ('transfer_out', 'transfer_in')")
            elif filter_type == "deposit":
                r = await db.fetchone("SELECT COUNT(*) as c FROM transactions WHERE type IN ('deposit', 'admin_deposit', 'admin_give')")
            elif filter_type == "withdrawal":
                r = await db.fetchone("SELECT COUNT(*) as c FROM transactions WHERE type IN ('withdrawal', 'admin_debit', 'admin_take')")
            elif filter_type == "cheque":
                r = await db.fetchone("SELECT COUNT(*) as c FROM transactions WHERE type IN ('cheque_created', 'cheque_claimed', 'cheque_refund')")
            else:
                r = await db.fetchone("SELECT COUNT(*) as c FROM transactions WHERE type = ?", (filter_type,))
        else:
            r = await db.fetchone("SELECT COUNT(*) as c FROM transactions")
        return r["c"] if r else 0


async def get_active_cheques_by_user(user_id: int) -> List[Dict[str, Any]]:
    async with get_db() as db:
        return await db.fetchall(
            "SELECT * FROM cheques WHERE creator_id = ? AND status = 'active' ORDER BY created_at DESC",
            (user_id,)
        )


async def get_user_transactions(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    async with get_db() as db:
        return await db.fetchall(
            "SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )


async def get_transaction(trx_id: str) -> Optional[Dict[str, Any]]:
    return await admin_find_transaction(trx_id)



async def get_system_stats() -> Dict[str, Any]:
    async with get_db() as db:
        r1 = await db.fetchone("SELECT COUNT(*) as c, SUM(balance) as s FROM users")
        u_count = r1["c"] if r1 else 0
        total_balance = r1["s"] if r1 and r1.get("s") else 0

        r2 = await db.fetchone("SELECT COUNT(*) as c, SUM(amount) as s FROM transactions WHERE type IN ('transfer_out', 'transfer_in')")
        t_count = r2["c"] if r2 else 0
        total_transfers = r2["s"] if r2 and r2.get("s") else 0

        r3 = await db.fetchone("SELECT COUNT(*) as c FROM cheques WHERE status = 'active'")
        active_cheques = r3["c"] if r3 else 0

        # Telegram Stars donations/deposits
        r_don = await db.fetchone("SELECT COUNT(*) as c, SUM(amount) as s FROM transactions WHERE type = 'deposit'")
        don_count = r_don["c"] if r_don else 0
        total_donated = r_don["s"] if r_don and r_don.get("s") else 0

        # All deposits including admin credit
        r_all_dep = await db.fetchone("SELECT COUNT(*) as c, SUM(amount) as s FROM transactions WHERE type IN ('deposit', 'admin_deposit', 'admin_give')")
        all_dep_count = r_all_dep["c"] if r_all_dep else 0
        all_dep_sum = r_all_dep["s"] if r_all_dep and r_all_dep.get("s") else 0

        return {
            "users_count": u_count or 0,
            "total_user_balance": total_balance or 0,
            "transfers_count": (t_count or 0) // 2,
            "transfers_volume": (total_transfers or 0) // 2,
            "active_cheques": active_cheques or 0,
            "total_donated": total_donated or 0,
            "donations_count": don_count or 0,
            "total_deposits_all": all_dep_sum or 0,
            "all_deposits_count": all_dep_count or 0
        }


async def get_all_user_ids() -> List[int]:
    async with get_db() as db:
        rows = await db.fetchall("SELECT user_id FROM users WHERE is_blocked = 0")
        return [r["user_id"] for r in rows]


async def get_user_reserved_summary(user_id: int) -> Dict[str, Any]:
    async with get_db() as db:
        r1 = await db.fetchone("SELECT COUNT(*) as c, SUM(amount) as s FROM cheques WHERE creator_id = ? AND status = 'active'", (user_id,))
        ch_count = r1["c"] if r1 else 0
        ch_sum = r1["s"] if r1 and r1.get("s") else 0

        r2 = await db.fetchone("SELECT COUNT(*) as c, SUM(amount) as s FROM pending_transfers WHERE sender_id = ? AND status = 'pending'", (user_id,))
        pt_count = r2["c"] if r2 else 0
        pt_sum = r2["s"] if r2 and r2.get("s") else 0

        return {
            "cheques_count": ch_count or 0,
            "cheques_sum": ch_sum or 0,
            "pending_count": pt_count or 0,
            "pending_sum": pt_sum or 0,
            "total_reserved": (ch_sum or 0) + (pt_sum or 0)
        }


async def get_user_reserved_items(user_id: int) -> Dict[str, Any]:
    async with get_db() as db:
        cheques = await db.fetchall("SELECT * FROM cheques WHERE creator_id = ? AND status = 'active' ORDER BY created_at DESC", (user_id,))
        pending = await db.fetchall("SELECT * FROM pending_transfers WHERE sender_id = ? AND status = 'pending' ORDER BY created_at DESC", (user_id,))
        return {
            "cheques": cheques,
            "pending": pending
        }
