import aiosqlite
import random
import string
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import DB_PATH


def generate_account_number(user_id: int) -> str:
    """Generates an SBP account format: СБП-XXXX-XXXX"""
    part1 = f"{abs(hash(str(user_id))) % 9000 + 1000}"
    part2 = f"{random.randint(1000, 9999)}"
    return f"СБП-{part1}-{part2}"


def generate_trx_id(prefix: str = "TRX") -> str:
    """Generates unique transaction ID like SBP-TRX-20261017-X8K2"""
    date_str = datetime.now().strftime("%Y%m%d")
    rnd = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"SBP-{prefix}-{date_str}-{rnd}"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            balance INTEGER DEFAULT 0,
            account_number TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_blocked INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trx_id TEXT UNIQUE,
            user_id INTEGER,
            counterparty TEXT,
            counterparty_id INTEGER,
            amount INTEGER,
            type TEXT, -- 'deposit', 'withdrawal', 'transfer_out', 'transfer_in', 'cheque_created', 'cheque_claimed', 'cheque_refund'
            status TEXT, -- 'success', 'failed', 'pending'
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
            status TEXT DEFAULT 'active', -- 'active', 'claimed', 'cancelled'
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
            status TEXT DEFAULT 'pending', -- 'pending', 'claimed'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.commit()


async def get_or_create_user(user_id: int, username: Optional[str], first_name: str, last_name: Optional[str]) -> Dict[str, Any]:
    username_clean = username.lstrip("@").lower() if username else None
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()

        if row:
            # Update names if changed
            await db.execute(
                "UPDATE users SET username = ?, first_name = ?, last_name = ? WHERE user_id = ?",
                (username_clean, first_name, last_name, user_id)
            )
            await db.commit()
            user_data = dict(row)
            user_data["username"] = username_clean
            user_data["first_name"] = first_name
            user_data["last_name"] = last_name
        else:
            acc_num = generate_account_number(user_id)
            await db.execute(
                "INSERT INTO users (user_id, username, first_name, last_name, balance, account_number) VALUES (?, ?, ?, ?, 0, ?)",
                (user_id, username_clean, first_name, last_name, acc_num)
            )
            await db.commit()
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_data = dict(await cursor.fetchone())

        # Check pending transfers for this username
        claimed_pending = []
        if username_clean:
            cursor = await db.execute(
                "SELECT * FROM pending_transfers WHERE recipient_username = ? AND status = 'pending'",
                (username_clean,)
            )
            pending_list = await cursor.fetchall()
            for pt in pending_list:
                amount = pt["amount"]
                # Credit balance
                await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
                await db.execute("UPDATE pending_transfers SET status = 'claimed' WHERE id = ?", (pt["id"],))

                # Log incoming transfer transaction
                await db.execute(
                    """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
                       VALUES (?, ?, ?, ?, ?, 'transfer_in', 'success', ?)""",
                    (pt["trx_id"], user_id, f"@{pt['sender_username']}" if pt['sender_username'] else f"ID {pt['sender_id']}",
                     pt['sender_id'], amount, pt['comment'] or "Перевод по СБП")
                )
                await db.commit()
                claimed_pending.append(dict(pt))

            if pending_list:
                # Refresh user data after claiming
                cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                user_data = dict(await cursor.fetchone())

        user_data["claimed_pending"] = claimed_pending
        return user_data


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    clean_u = username.lstrip("@").lower()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE username = ?", (clean_u,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_by_account(account_number: str) -> Optional[Dict[str, Any]]:
    clean_acc = account_number.strip().upper()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE account_number = ?", (clean_acc,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def admin_find_user(query: str) -> Optional[Dict[str, Any]]:
    """Flexible user search for admin by @username, ID, or SBP account."""
    q = query.strip()
    if q.startswith("@"):
        return await get_user_by_username(q[1:])
    if q.lower().startswith("id") and q[2:].isdigit():
        return await get_user(int(q[2:]))
    if q.isdigit():
        u = await get_user(int(q))
        if u:
            return u
    u = await get_user_by_username(q)
    if u:
        return u
    return await get_user_by_account(q)


async def credit_balance(user_id: int, amount: int, trx_type: str, comment: str, counterparty: str = "СБП Банк", custom_trx_id: Optional[str] = None) -> str:
    """Credits stars to user balance and records transaction."""
    trx_id = custom_trx_id or generate_trx_id(prefix="DEP" if trx_type == "deposit" else "TRX")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.execute(
            """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
               VALUES (?, ?, ?, NULL, ?, ?, 'success', ?)""",
            (trx_id, user_id, counterparty, amount, trx_type, comment)
        )
        await db.commit()
    return trx_id


async def debit_balance(user_id: int, amount: int, trx_type: str, comment: str, counterparty: str = "Вывод СБП") -> Optional[str]:
    """Debits stars from user balance if sufficient and records transaction."""
    trx_id = generate_trx_id(prefix="WTH" if trx_type == "withdrawal" else "TRX")
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row or row[0] < amount:
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
    """Transfers stars between two registered users atomically."""
    trx_id = generate_trx_id(prefix="TRX")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Check sender balance
        c1 = await db.execute("SELECT * FROM users WHERE user_id = ?", (sender_id,))
        sender = await c1.fetchone()
        if not sender or sender["balance"] < amount:
            return None

        # Check recipient
        c2 = await db.execute("SELECT * FROM users WHERE user_id = ?", (recipient_id,))
        recipient = await c2.fetchone()
        if not recipient:
            return None

        # Update balances
        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, sender_id))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, recipient_id))

        sender_label = f"@{sender['username']}" if sender['username'] else f"{sender['first_name']} (ID {sender['user_id']})"
        recipient_label = f"@{recipient['username']}" if recipient['username'] else f"{recipient['first_name']} (ID {recipient['user_id']})"

        trx_id_out = f"{trx_id}-OUT"
        trx_id_in = f"{trx_id}-IN"

        # Sender transaction (transfer_out)
        await db.execute(
            """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
               VALUES (?, ?, ?, ?, ?, 'transfer_out', 'success', ?)""",
            (trx_id_out, sender_id, recipient_label, recipient_id, amount, comment or "Перевод по СБП")
        )

        # Recipient transaction (transfer_in)
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
    """Deducts sender and stores pending transfer for an unregistered username."""
    trx_id = generate_trx_id(prefix="TRX")
    clean_u = recipient_username.lstrip("@").lower()

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        c1 = await db.execute("SELECT * FROM users WHERE user_id = ?", (sender_id,))
        sender = await c1.fetchone()
        if not sender or sender["balance"] < amount:
            return None

        # Deduct sender balance
        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, sender_id))

        # Store pending record
        await db.execute(
            """INSERT INTO pending_transfers (trx_id, sender_id, sender_username, recipient_username, amount, comment)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (trx_id, sender_id, sender["username"], clean_u, amount, comment or "Перевод по СБП")
        )

        # Record sender transaction
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
    """Cancels a pending transfer and refunds the sender's balance."""
    clean_trx = trx_id.strip().lstrip("#")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        query = "SELECT * FROM pending_transfers WHERE (trx_id = ? OR trx_id LIKE ?) AND status = 'pending'"
        params = [clean_trx, f"%{clean_trx}%"]
        if sender_id is not None:
            query += " AND sender_id = ?"
            params.append(sender_id)

        cursor = await db.execute(query, tuple(params))
        pt = await cursor.fetchone()
        if not pt:
            return None

        pt_id = pt["id"]
        actual_sender_id = pt["sender_id"]
        amount = pt["amount"]
        recipient_username = pt["recipient_username"]

        # Mark pending transfer as cancelled
        await db.execute("UPDATE pending_transfers SET status = 'cancelled' WHERE id = ?", (pt_id,))

        # Refund sender
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, actual_sender_id))

        # Record refund transaction
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
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM pending_transfers WHERE trx_id = ? OR trx_id LIKE ? LIMIT 1",
            (clean_q, f"%{clean_q}%")
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


# --- Cheques / Inline transfers ---

async def create_cheque(creator_id: int, creator_username: Optional[str], amount: int,
                        recipient_username: Optional[str] = None, comment: Optional[str] = None) -> Optional[str]:
    """Reserves funds from user balance and creates an SBP cheque."""
    cheque_id = "ch_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    clean_rec = recipient_username.lstrip("@").lower() if recipient_username else None

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (creator_id,))
        row = await cursor.fetchone()
        if not row or row[0] < amount:
            return None

        # Deduct balance into escrow
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
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM cheques WHERE cheque_id = ?", (cheque_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def claim_cheque(cheque_id: str, claimer_id: int, claimer_username: Optional[str], claimer_name: str) -> Dict[str, Any]:
    """
    Attempts to claim an active cheque.
    Returns dict with status: 'ok', 'already_claimed', 'self_claim', 'restricted', 'not_found'
    """
    clean_u = claimer_username.lstrip("@").lower() if claimer_username else None

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM cheques WHERE cheque_id = ?", (cheque_id,))
        cheque = await cursor.fetchone()

        if not cheque:
            return {"status": "not_found"}

        if cheque["status"] != "active":
            return {"status": "already_claimed", "claimed_by": cheque["claimed_by_username"]}

        if cheque["creator_id"] == claimer_id:
            return {"status": "self_claim"}

        if cheque["recipient_username"]:
            if not clean_u or clean_u != cheque["recipient_username"].lower():
                return {"status": "restricted", "expected": cheque["recipient_username"]}

        # Perform claim
        amount = cheque["amount"]
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, claimer_id))
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            """UPDATE cheques SET status = 'claimed', claimed_by_id = ?, claimed_by_username = ?, claimed_at = ?
               WHERE cheque_id = ?""",
            (claimer_id, clean_u or claimer_name, now, cheque_id)
        )

        # Record recipient transaction
        trx_id = generate_trx_id(prefix="CHK")
        creator_label = f"@{cheque['creator_username']}" if cheque['creator_username'] else f"ID {cheque['creator_id']}"
        await db.execute(
            """INSERT INTO transactions (trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment)
               VALUES (?, ?, ?, ?, ?, 'cheque_claimed', 'success', ?)""",
            (trx_id, claimer_id, creator_label, cheque['creator_id'], amount, cheque['comment'] or "Активация чека СБП")
        )

        await db.commit()

        return {
            "status": "ok",
            "amount": amount,
            "creator_id": cheque["creator_id"],
            "creator_username": cheque["creator_username"],
            "comment": cheque["comment"]
        }


async def cancel_cheque(cheque_id: str, user_id: int) -> bool:
    """Cancels active cheque and refunds creator."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM cheques WHERE cheque_id = ? AND creator_id = ? AND status = 'active'",
                                  (cheque_id, user_id))
        cheque = await cursor.fetchone()
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
    """Admin cancels any active cheque and refunds creator."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM cheques WHERE cheque_id = ? AND status = 'active'", (cheque_id,))
        cheque = await cursor.fetchone()
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
    """Finds a cheque by ID, part of ID, or deep-link."""
    q = query_str.strip()
    if "start=" in q:
        q = q.split("start=")[-1].split("&")[0].split()[0]
    q = q.strip()

    variants = [q]
    if not q.startswith("ch_"):
        variants.append(f"ch_{q}")
    else:
        variants.append(q[3:])

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        for var in variants:
            cursor = await db.execute("SELECT * FROM cheques WHERE cheque_id = ?", (var,))
            row = await cursor.fetchone()
            if row:
                return dict(row)

        cursor = await db.execute("SELECT * FROM cheques WHERE cheque_id LIKE ? LIMIT 1", (f"%{q}%",))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def admin_find_any_operation(query_str: str) -> Optional[Dict[str, Any]]:
    """
    Searches across:
    1. Pending transfers
    2. Cheques
    3. Transactions
    """
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

    trx = await get_transaction(q)
    if trx:
        return {"type": "transaction", "data": trx}

    return None


async def admin_get_recent_cheques(limit: int = 5) -> List[Dict[str, Any]]:
    """Returns the most recent cheques for admin overview."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM cheques ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_active_cheques_by_user(user_id: int) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM cheques WHERE creator_id = ? AND status = 'active' ORDER BY created_at DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_user_transactions(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_transaction(trx_id: str) -> Optional[Dict[str, Any]]:
    clean_trx = trx_id.strip().lstrip("#")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM transactions WHERE trx_id = ? OR trx_id LIKE ? LIMIT 1", (clean_trx, f"%{clean_trx}%"))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_system_stats() -> Dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        c1 = await db.execute("SELECT COUNT(*), SUM(balance) FROM users")
        u_count, total_balance = await c1.fetchone()

        c2 = await db.execute("SELECT COUNT(*), SUM(amount) FROM transactions WHERE type IN ('transfer_out', 'transfer_in')")
        t_count, total_transfers = await c2.fetchone()

        c3 = await db.execute("SELECT COUNT(*) FROM cheques WHERE status = 'active'")
        active_cheques = (await c3.fetchone())[0]

        return {
            "users_count": u_count or 0,
            "total_user_balance": total_balance or 0,
            "transfers_count": (t_count or 0) // 2,
            "transfers_volume": (total_transfers or 0) // 2,
            "active_cheques": active_cheques or 0
        }


async def get_all_user_ids() -> List[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE is_blocked = 0")
        rows = await cursor.fetchall()
        return [r[0] for r in rows]
