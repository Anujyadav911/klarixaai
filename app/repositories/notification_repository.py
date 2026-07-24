import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Channel, DeliveryStatus
from app.models.delivery import NotificationDelivery
from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Notification:
        notification = Notification(**kwargs)
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, key: str) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(Notification.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self, user_id: str, page: int = 1, size: int = 20
    ) -> tuple[list[Notification], int]:
        count_query = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id
        )
        total = (await self.session.execute(count_query)).scalar_one()

        offset = (page - 1) * size
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def update_status(
        self, notification_id: uuid.UUID, status: DeliveryStatus
    ) -> None:
        await self.session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(status=status)
        )
        await self.session.flush()

    async def create_delivery(self, **kwargs) -> NotificationDelivery:
        delivery = NotificationDelivery(**kwargs)
        self.session.add(delivery)
        await self.session.flush()
        return delivery

    async def get_delivery_by_id(
        self, delivery_id: uuid.UUID
    ) -> NotificationDelivery | None:
        result = await self.session.execute(
            select(NotificationDelivery).where(NotificationDelivery.id == delivery_id)
        )
        return result.scalar_one_or_none()

    async def update_delivery(
        self, delivery_id: uuid.UUID, **kwargs
    ) -> None:
        await self.session.execute(
            update(NotificationDelivery)
            .where(NotificationDelivery.id == delivery_id)
            .values(**kwargs)
        )
        await self.session.flush()

    async def get_deliveries_by_notification_id(
        self, notification_id: uuid.UUID
    ) -> list[NotificationDelivery]:
        result = await self.session.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.notification_id == notification_id
            )
        )
        return list(result.scalars().all())
