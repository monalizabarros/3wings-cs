from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.product_feedback import FeedbackCategory, FeedbackStatus


class ProductFeedbackCreate(BaseModel):
    category: FeedbackCategory
    description: str
    product_id: str | None = None
    module_id: str | None = None
    contact_id: str | None = None


class ProductFeedbackUpdate(BaseModel):
    category: FeedbackCategory | None = None
    description: str | None = None
    status: FeedbackStatus | None = None
    product_id: str | None = None
    module_id: str | None = None
    contact_id: str | None = None


class ProductFeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str
    product_id: str | None
    module_id: str | None
    contact_id: str | None
    category: FeedbackCategory
    description: str
    status: FeedbackStatus
    created_by_id: str | None
    created_at: datetime
    updated_at: datetime


class ProductFeedbackWithClientOut(ProductFeedbackOut):
    client_name: str
