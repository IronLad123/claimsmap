import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# LLM Provider: gemini | openai_compat
# openai_compat works with any OpenAI-compatible API (OrcaRouter, Together, Groq, etc.)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini" if GEMINI_API_KEY else "openai_compat")

# OpenAI-compatible provider (OrcaRouter, Groq, Together, etc.)
OPENAI_COMPAT_BASE_URL = os.getenv("OPENAI_COMPAT_BASE_URL", "")
OPENAI_COMPAT_API_KEY = os.getenv("OPENAI_COMPAT_API_KEY", "")
OPENAI_COMPAT_MODEL = os.getenv("OPENAI_COMPAT_MODEL", "orcarouter/free")

# DEMO_MODE: true only if explicitly requested via env.
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/facts.db")
STARTER_DATASETS_DIR = Path(__file__).parent.parent.parent / "starter-datasets"
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Security and validation limits
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_MB", "30")) * 1024 * 1024
MAX_PAGE_COUNT = int(os.getenv("MAX_PAGE_COUNT", "300"))
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if o.strip()]


