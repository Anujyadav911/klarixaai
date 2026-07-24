import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    subject: str = Field(..., min_length=1, max_length=512)
    body: str = Field(..., min_length=1)


class TemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    subject: str
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
