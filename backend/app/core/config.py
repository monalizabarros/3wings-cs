import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("CS_DATABASE_URL", f"sqlite:///{BASE_DIR / 'cs.db'}")

SECRET_KEY = os.getenv("CS_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "CS_SECRET_KEY não está configurado. Copie backend/.env.example para "
        "backend/.env e gere um valor com: openssl rand -hex 32"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("CS_ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

CORS_ORIGINS = os.getenv("CS_CORS_ORIGINS", "http://localhost:5173").split(",")
