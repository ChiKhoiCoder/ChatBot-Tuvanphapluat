import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "data" / "legal_assistant.db"))
)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
