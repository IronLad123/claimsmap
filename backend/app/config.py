import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true" or not GEMINI_API_KEY
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/facts.db")
STARTER_DATASETS_DIR = Path(__file__).parent.parent.parent / "starter-datasets"
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
