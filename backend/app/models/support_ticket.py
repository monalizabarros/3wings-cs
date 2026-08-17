import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TicketSeverity(str, enum.Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class TicketStatus(str, enum.Enum):
    ABERTO = "aberto"
    EM_ANDAMENTO = "em_andamento"
    RESOLVIDO = "resolvido"
    FECHADO = "fechado"


def _uuid() -> str:
    return str(uuid.uuid4())


class SupportTicket(Base):
    """Log manual de atividade de suporte por conta (RF-118 a RF-121).

    Assim como a Implantação (Bloco 6) não duplica o sistema de Projetos, o
    sistema de tickets de verdade fica fora do CS (`external_reference` é só
    um link/ID de referência) — este registro existe para o CS acompanhar
    volume, severidade e satisfação de suporte por cliente, sem recriar uma
    central de tickets completa.
    """

    __tablename__ = "support_tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)

    external_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    subject: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[TicketSeverity] = mapped_column(Enum(TicketSeverity), nullable=False, default=TicketSeverity.MEDIA)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), nullable=False, default=TicketStatus.ABERTO)
    opened_at: Mapped[date] = mapped_column(Date, nullable=False)
    closed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    satisfaction_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5

    created_by_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
