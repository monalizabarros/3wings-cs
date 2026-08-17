import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FeedbackCategory(str, enum.Enum):
    MELHORIA = "melhoria"
    BUG = "bug"
    NOVA_FUNCIONALIDADE = "nova_funcionalidade"
    ELOGIO = "elogio"
    RECLAMACAO = "reclamacao"


class FeedbackStatus(str, enum.Enum):
    NOVO = "novo"
    EM_ANALISE = "em_analise"
    PLANEJADO = "planejado"
    ENTREGUE = "entregue"
    RECUSADO = "recusado"


def _uuid() -> str:
    return str(uuid.uuid4())


class ProductFeedback(Base):
    """Feedback do cliente sobre o produto, encaminhado para o time de
    Produto (RF-114 a RF-117). Vínculo opcional a produto/módulo e contato
    de origem — mesmo padrão de vínculo opcional já usado em Interaction
    (Bloco 9)."""

    __tablename__ = "product_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)
    product_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("products.id"), nullable=True)
    module_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("modules.id"), nullable=True)
    contact_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("contacts.id"), nullable=True)

    category: Mapped[FeedbackCategory] = mapped_column(Enum(FeedbackCategory), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[FeedbackStatus] = mapped_column(Enum(FeedbackStatus), nullable=False, default=FeedbackStatus.NOVO)

    created_by_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
