"""Envio de e-mail via SMTP para notificações de alertas críticos.

Sem `CS_SMTP_HOST` configurado, `send_email` vira um no-op logado — assim
o app continua rodando normalmente em dev/teste sem exigir um servidor SMTP
real. Configure `backend/.env` (ver `.env.example`) para habilitar o envio
de verdade em produção.
"""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import (
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
    SMTP_USE_TLS,
)

logger = logging.getLogger("app.email")


def send_email(to: str, subject: str, body: str) -> bool:
    if not SMTP_HOST:
        logger.info("SMTP não configurado — e-mail não enviado (destinatário=%s, assunto=%r)", to, subject)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SMTP_FROM
    message["To"] = to
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
        return True
    except OSError:
        logger.exception("Falha ao enviar e-mail para %s", to)
        return False
