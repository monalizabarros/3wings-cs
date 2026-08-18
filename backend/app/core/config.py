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

# SMTP para notificação por e-mail de alertas críticos (RF de segurança/
# observabilidade). Se CS_SMTP_HOST não estiver definido, o envio vira um
# no-op logado — não exigido para rodar o app localmente.
SMTP_HOST = os.getenv("CS_SMTP_HOST")
SMTP_PORT = int(os.getenv("CS_SMTP_PORT", "587"))
SMTP_USER = os.getenv("CS_SMTP_USER")
SMTP_PASSWORD = os.getenv("CS_SMTP_PASSWORD")
SMTP_FROM = os.getenv("CS_SMTP_FROM", "3Wings CS <no-reply@3wings.com.br>")
SMTP_USE_TLS = os.getenv("CS_SMTP_USE_TLS", "true").lower() != "false"
