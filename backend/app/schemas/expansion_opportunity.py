from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.expansion_opportunity import ExpansionStage, ExpansionType


class ExpansionOpportunityCreate(BaseModel):
    type: ExpansionType
    description: str
    product_id: str | None = None
    module_id: str | None = None
    estimated_value: float | None = None
    probability: int | None = None
    expected_close_date: date | None = None
    responsible_user_id: str | None = None


class ExpansionOpportunityUpdate(BaseModel):
    type: ExpansionType | None = None
    description: str | None = None
    product_id: str | None = None
    module_id: str | None = None
    estimated_value: float | None = None
    stage: ExpansionStage | None = None
    probability: int | None = None
    expected_close_date: date | None = None
    responsible_user_id: str | None = None


class ExpansionOpportunityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str
    product_id: str | None
    module_id: str | None
    type: ExpansionType
    description: str
    estimated_value: float | None
    stage: ExpansionStage
    probability: int | None
    expected_close_date: date | None
    responsible_user_id: str | None
    created_by_id: str | None
    created_at: datetime
    updated_at: datetime


class ExpansionOpportunityWithClientOut(ExpansionOpportunityOut):
    client_name: str
