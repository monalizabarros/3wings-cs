from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.renewal import ChurnCategory, RenewalStatus


class RenewalCreate(BaseModel):
    contract_end_date: date
    renewal_value: float | None = None
    risk_notes: str | None = None


class RenewalUpdate(BaseModel):
    contract_end_date: date | None = None
    renewal_value: float | None = None
    status: RenewalStatus | None = None
    risk_notes: str | None = None


class RenewalComplete(BaseModel):
    renewed: bool
    next_contract_end_date: date | None = None  # obrigatório se renewed=True
    churn_category: ChurnCategory | None = None  # obrigatório se renewed=False
    churn_description: str | None = None
    lost_value: float | None = None


class RenewalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str
    contract_end_date: date
    renewal_value: float | None
    status: RenewalStatus
    risk_notes: str | None
    resolved_at: datetime | None
    created_by_id: str | None
    created_at: datetime
    updated_at: datetime


class RenewalWithClientOut(RenewalOut):
    client_name: str


class ChurnRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str
    renewal_id: str | None
    churn_date: date
    category: ChurnCategory
    description: str | None
    lost_value: float | None
    created_by_id: str | None
    created_at: datetime
