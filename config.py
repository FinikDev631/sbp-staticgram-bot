import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "1780245321:-vs-9wjhoEh9yBxCH36wfnZBcNbaC6GY6ZY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.staticgram.top")
PRIMARY_ADMIN_ID = 1780243463
ADMIN_ID = int(os.getenv("ADMIN_ID", "1780243463"))
ADMIN_IDS = {PRIMARY_ADMIN_ID, ADMIN_ID}
DB_PATH = BASE_DIR / "sbp_bank.db"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:NwkiHp8GjND3Q5H1@db.ecdqcscosklruehfjgax.supabase.co:5432/postgres"
)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
