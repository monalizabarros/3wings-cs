from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.support_ticket import TicketSeverity, TicketStatus


class SupportTicketCreate(BaseModel):
    subject: str
    description: str | None = None
    external_reference: str | None = None
    severity: TicketSeverity = TicketSeverity.MEDIA
    opened_at: date


class SupportTicketUpdate(BaseModel):
    subject: str | None = None
    description: str | None = None
    external_reference: str | None = None
    severity: TicketSeverity | None = None
    status: TicketStatus | None = None
    closed_at: date | None = None
    satisfaction_score: int | None = None


class SupportTicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str
    external_reference: str | None
    subject: str
    description: str | None
    severity: TicketSeverity
    status: TicketStatus
    opened_at: date
    closed_at: date | None
    satisfaction_score: int | None
    created_by_id: str | None
    created_at: datetime
    updated_at: datetime


class SupportSummaryOut(BaseModel):
    open_tickets: int
    critical_open_tickets: int
    total_tickets: int
    avg_satisfaction: float | None
