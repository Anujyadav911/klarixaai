import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import Channel, DeliveryStatus, Priority


class NotificationPayload(BaseModel):
    subject: str | None = None
    body: str | None = None
    variables: dict[str, str] = Field(default_factory=dict)


class NotificationCreateRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    channels: list[Channel] = Field(..., min_length=1)
    priority: Priority = Priority.NORMAL
    template_id: uuid.UUID | None = None
    payload: NotificationPayload = Field(default_factory=NotificationPayload)
    idempotency_key: str | None = Field(None, max_length=256)


class DeliveryResponse(BaseModel):
    id: uuid.UUID
    channel: Channel
    status: DeliveryStatus
    retry_count: int
    provider_response: dict | None = None
    error_message: str | None = None
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: str
    idempotency_key: str | None = None
    priority: Priority
    status: DeliveryStatus
    payload: dict
    deliveries: list[DeliveryResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    size: int
