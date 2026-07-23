import uuid

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import Channel, DeliveryStatus, Priority
from app.models.base import BaseModel, FlexibleJSON, FlexibleUUID


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=True, unique=True, index=True)
    priority: Mapped[Priority] = mapped_column(Enum(Priority, name="priority_enum"), nullable=False, default=Priority.NORMAL)
    template_id: Mapped[uuid.UUID | None] = mapped_column(FlexibleUUID, ForeignKey("templates.id"), nullable=True)
    payload: Mapped[dict] = mapped_column(FlexibleJSON, nullable=False, default=dict)
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status_enum"),
        nullable=False,
        default=DeliveryStatus.PENDING,
    )

    deliveries: Mapped[list["NotificationDelivery"]] = relationship(
        back_populates="notification",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_notifications_user_id_created_at", "user_id", "created_at"),
    )
