from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    FACEIT_API_KEY = os.getenv("FACEIT_API_KEY")
    FACEIT_GAME = os.getenv("FACEIT_GAME", "cs2")
    FACEIT_ACCOUNTS_PATH = os.getenv(
        "FACEIT_ACCOUNTS_PATH",
        os.path.join(BASE_DIR, "data", "faceit_accounts.json")
    )