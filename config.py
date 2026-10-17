import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "1780245321:-vs-9wjhoEh9yBxCH36wfnZBcNbaC6GY6ZY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.staticgram.top")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DB_PATH = BASE_DIR / "sbp_bank.db"
