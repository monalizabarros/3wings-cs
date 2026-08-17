import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExpansionType(str, enum.Enum):
    CROSS_SELL = "cross_sell"
    UPSELL = "upsell"


class ExpansionStage(str, enum.Enum):
    IDENTIFICADA = "identificada"
    EM_QUALIFICACAO = "em_qualificacao"
    PROPOSTA = "proposta"
    NEGOCIACAO = "negociacao"
    GANHA = "ganha"
    PERDIDA = "perdida"


def _uuid() -> str:
    return str(uuid.uuid4())


class ExpansionOpportunity(Base):
    """Oportunidade de expansão de conta — cross-sell/upsell (RF-122 a RF-126)."""

    __tablename__ = "expansion_opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)
    product_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("products.id"), nullable=True)
    module_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("modules.id"), nullable=True)

    type: Mapped[ExpansionType] = mapped_column(Enum(ExpansionType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    stage: Mapped[ExpansionStage] = mapped_column(Enum(ExpansionStage), nullable=False, default=ExpansionStage.IDENTIFICADA)
    probability: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    expected_close_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    responsible_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    created_by_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
