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

# LLM Provider Configuration (gemini | ollama)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama" if not GEMINI_API_KEY else "gemini")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Security and validation limits
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_MB", "30")) * 1024 * 1024
MAX_PAGE_COUNT = int(os.getenv("MAX_PAGE_COUNT", "300"))
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if o.strip()]


