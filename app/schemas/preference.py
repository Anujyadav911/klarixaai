import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PreferenceRequest(BaseModel):
    email_enabled: bool = True
    sms_enabled: bool = True
    push_enabled: bool = True


class PreferenceResponse(BaseModel):
    id: uuid.UUID
    user_id: str
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
