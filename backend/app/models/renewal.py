import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RenewalStatus(str, enum.Enum):
    PENDENTE = "pendente"
    EM_NEGOCIACAO = "em_negociacao"
    RENOVADO = "renovado"
    NAO_RENOVADO = "nao_renovado"


def _uuid() -> str:
    return str(uuid.uuid4())


class Renewal(Base):
    """Ciclo de renovação de contrato (RF-127 a RF-131). Concluir com
    RENOVADO reabre `Client.status=ativo` e atualiza `Client.renewal_date`;
    concluir com NAO_RENOVADO muda `Client.status=churn` e cria um
    ChurnRecord automaticamente — mesmo padrão de transição automática de
    status já usado no aceite de handoff (Bloco 8)."""

    __tablename__ = "renewals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)

    contract_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    renewal_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[RenewalStatus] = mapped_column(Enum(RenewalStatus), nullable=False, default=RenewalStatus.PENDENTE)
    risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_by_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ChurnCategory(str, enum.Enum):
    PRECO = "preco"
    PRODUTO = "produto"
    SUPORTE = "suporte"
    CONCORRENCIA = "concorrencia"
    ORCAMENTO_CLIENTE = "orcamento_cliente"
    INSATISFACAO = "insatisfacao"
    OUTRO = "outro"


class ChurnRecord(Base):
    """Registro formal de churn (RF-132 a RF-134)."""

    __tablename__ = "churn_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)
    renewal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("renewals.id"), nullable=True)

    churn_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[ChurnCategory] = mapped_column(Enum(ChurnCategory), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    lost_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_by_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
