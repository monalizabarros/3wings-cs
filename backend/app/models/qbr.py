import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QBRStatus(str, enum.Enum):
    AGENDADO = "agendado"
    REALIZADO = "realizado"
    CANCELADO = "cancelado"


def _uuid() -> str:
    return str(uuid.uuid4())


class QBR(Base):
    """Quarterly Business Review (RF-109 a RF-113). O plano de ação (RF-113)
    reaproveita o ActionPlan do Bloco 10, mesmo padrão já usado pelo plano de
    recuperação de risco (RF-102)."""

    __tablename__ = "qbrs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)

    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[QBRStatus] = mapped_column(Enum(QBRStatus), nullable=False, default=QBRStatus.AGENDADO)

    participants: Mapped[str | None] = mapped_column(Text, nullable=True)
    agenda: Mapped[str | None] = mapped_column(Text, nullable=True)
    achievements: Mapped[str | None] = mapped_column(Text, nullable=True)
    challenges: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_period_goals: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("action_plans.id"), nullable=True)

    created_by_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
