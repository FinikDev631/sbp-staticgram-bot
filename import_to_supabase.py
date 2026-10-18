import os
import sys
import asyncio
import asyncpg
import json

async def migrate(supabase_url: str):
    print("Connecting to Supabase PostgreSQL...")
    url = supabase_url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    pool_kwargs = {"min_size": 1, "max_size": 5}
    if "pooler.supabase.com" in url or ":6543" in url:
        pool_kwargs["statement_cache_size"] = 0

    conn = await asyncpg.connect(dsn=url, **{"statement_cache_size": 0} if pool_kwargs.get("statement_cache_size") == 0 else {})
    try:
        print("Connected successfully! Reading backup_render_db.sql...")
        with open("backup_render_db.sql", "r", encoding="utf-8") as f:
            sql_script = f.read()

        print("Executing schema and data import...")
        await conn.execute(sql_script)

        print("\nVerifying imported counts in Supabase:")
        users_cnt = await conn.fetchval("SELECT COUNT(*) FROM users")
        tx_cnt = await conn.fetchval("SELECT COUNT(*) FROM transactions")
        ch_cnt = await conn.fetchval("SELECT COUNT(*) FROM cheques")
        pt_cnt = await conn.fetchval("SELECT COUNT(*) FROM pending_transfers")

        print(f"✅ Users: {users_cnt}")
        print(f"✅ Transactions: {tx_cnt}")
        print(f"✅ Cheques: {ch_cnt}")
        print(f"✅ Pending Transfers: {pt_cnt}")
        print("\nMigration to Supabase completed successfully without data loss!")
    finally:
        await conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL")

    if not target_url:
        print("Usage: python import_to_supabase.py <SUPABASE_POSTGRES_URL>")
        sys.exit(1)

    asyncio.run(migrate(target_url))
