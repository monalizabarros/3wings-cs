from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.qbr import QBRStatus


class QBRCreate(BaseModel):
    scheduled_date: date
    participants: str | None = None
    agenda: str | None = None


class QBRUpdate(BaseModel):
    scheduled_date: date | None = None
    status: QBRStatus | None = None
    participants: str | None = None
    agenda: str | None = None
    achievements: str | None = None
    challenges: str | None = None
    next_period_goals: str | None = None


class QBRComplete(BaseModel):
    achievements: str | None = None
    challenges: str | None = None
    next_period_goals: str | None = None


class QBROut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str
    scheduled_date: date
    completed_at: datetime | None
    status: QBRStatus
    participants: str | None
    agenda: str | None
    achievements: str | None
    challenges: str | None
    next_period_goals: str | None
    action_plan_id: str | None
    created_by_id: str | None
    created_at: datetime
    updated_at: datetime
