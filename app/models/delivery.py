import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import Channel, DeliveryStatus
from app.models.base import BaseModel, FlexibleJSON, FlexibleUUID


class NotificationDelivery(BaseModel):
    __tablename__ = "notification_deliveries"

    notification_id: Mapped[uuid.UUID] = mapped_column(
        FlexibleUUID,
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[Channel] = mapped_column(Enum(Channel, name="channel_enum"), nullable=False)
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status_enum", create_type=False),
        nullable=False,
        default=DeliveryStatus.PENDING,
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider_response: Mapped[dict | None] = mapped_column(FlexibleJSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    notification: Mapped["Notification"] = relationship(back_populates="deliveries")
