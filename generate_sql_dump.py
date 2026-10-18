import json

with open("backup_render_db.json", "r", encoding="utf-8") as f:
    data = json.load(f)

lines = []
lines.append("-- Schema creation for Supabase PostgreSQL")
lines.append("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    balance BIGINT DEFAULT 0,
    account_number TEXT UNIQUE,
    old_account_number TEXT,
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

def esc(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v).replace("'", "''")
    return f"'{s}'"

lines.append("-- Insert Users")
for u in data["users"]:
    lines.append(
        f"INSERT INTO users (user_id, username, first_name, last_name, balance, account_number, old_account_number, created_at, is_blocked) "
        f"VALUES ({esc(u.get('user_id'))}, {esc(u.get('username'))}, {esc(u.get('first_name'))}, {esc(u.get('last_name'))}, {esc(u.get('balance'))}, {esc(u.get('account_number'))}, {esc(u.get('old_account_number'))}, {esc(u.get('created_at'))}, {esc(u.get('is_blocked', 0))}) "
        f"ON CONFLICT (user_id) DO UPDATE SET balance = EXCLUDED.balance, account_number = EXCLUDED.account_number, old_account_number = EXCLUDED.old_account_number;"
    )

lines.append("\n-- Insert Transactions")
for t in data["transactions"]:
    lines.append(
        f"INSERT INTO transactions (id, trx_id, user_id, counterparty, counterparty_id, amount, type, status, comment, created_at) "
        f"VALUES ({esc(t.get('id'))}, {esc(t.get('trx_id'))}, {esc(t.get('user_id'))}, {esc(t.get('counterparty'))}, {esc(t.get('counterparty_id'))}, {esc(t.get('amount'))}, {esc(t.get('type'))}, {esc(t.get('status'))}, {esc(t.get('comment'))}, {esc(t.get('created_at'))}) "
        f"ON CONFLICT (trx_id) DO NOTHING;"
    )

lines.append("\n-- Reset transactions id sequence")
lines.append("SELECT setval('transactions_id_seq', (SELECT COALESCE(MAX(id), 1) FROM transactions));")

lines.append("\n-- Insert Cheques")
for c in data["cheques"]:
    lines.append(
        f"INSERT INTO cheques (cheque_id, creator_id, creator_username, amount, recipient_id, recipient_username, claimed_by_id, claimed_by_username, status, comment, created_at, claimed_at) "
        f"VALUES ({esc(c.get('cheque_id'))}, {esc(c.get('creator_id'))}, {esc(c.get('creator_username'))}, {esc(c.get('amount'))}, {esc(c.get('recipient_id'))}, {esc(c.get('recipient_username'))}, {esc(c.get('claimed_by_id'))}, {esc(c.get('claimed_by_username'))}, {esc(c.get('status'))}, {esc(c.get('comment'))}, {esc(c.get('created_at'))}, {esc(c.get('claimed_at'))}) "
        f"ON CONFLICT (cheque_id) DO NOTHING;"
    )

lines.append("\n-- Insert Pending Transfers")
for p in data["pending_transfers"]:
    lines.append(
        f"INSERT INTO pending_transfers (id, trx_id, sender_id, sender_username, recipient_username, amount, comment, status, created_at) "
        f"VALUES ({esc(p.get('id'))}, {esc(p.get('trx_id'))}, {esc(p.get('sender_id'))}, {esc(p.get('sender_username'))}, {esc(p.get('recipient_username'))}, {esc(p.get('amount'))}, {esc(p.get('comment'))}, {esc(p.get('status'))}, {esc(p.get('created_at'))}) "
        f"ON CONFLICT (trx_id) DO NOTHING;"
    )

lines.append("\n-- Reset pending_transfers id sequence")
lines.append("SELECT setval('pending_transfers_id_seq', (SELECT COALESCE(MAX(id), 1) FROM pending_transfers));")

with open("backup_render_db.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("SQL script generated: backup_render_db.sql")
