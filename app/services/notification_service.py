import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Channel, DeliveryStatus, PRIORITY_QUEUE_MAP
from app.core.exceptions import (
    AllChannelsOptedOutError,
    DuplicateNotificationError,
    NotificationNotFoundError,
    TemplateNotFoundError,
)
from app.core.logging import get_logger
from app.middleware.rate_limiter import check_rate_limit
from app.repositories.notification_repository import NotificationRepository
from app.repositories.template_repository import TemplateRepository
from app.schemas.notification import (
    NotificationCreateRequest,
    NotificationListResponse,
    NotificationResponse,
)
from app.services.preference_service import PreferenceService
from app.utils.idempotency import check_idempotency_key, set_idempotency_key

logger = get_logger(__name__)


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = NotificationRepository(session)
        self.template_repo = TemplateRepository(session)
        self.preference_service = PreferenceService(session)

    async def create_notification(
        self, request: NotificationCreateRequest
    ) -> NotificationResponse:
        await check_rate_limit(request.user_id)

        if request.idempotency_key:
            existing_id = await check_idempotency_key(request.idempotency_key)
            if existing_id:
                existing = await self.repo.get_by_id(uuid.UUID(existing_id))
                if existing:
                    logger.info(
                        "duplicate_notification_skipped",
                        idempotency_key=request.idempotency_key,
                        existing_id=existing_id,
                    )
                    return NotificationResponse.model_validate(existing)

        if request.template_id:
            template = await self.template_repo.get_by_id(request.template_id)
            if not template:
                raise TemplateNotFoundError(str(request.template_id))

        allowed_channels = await self.preference_service.get_allowed_channels(
            request.user_id, request.channels
        )
        if not allowed_channels:
            raise AllChannelsOptedOutError(request.user_id)

        notification = await self.repo.create(
            user_id=request.user_id,
            idempotency_key=request.idempotency_key,
            priority=request.priority,
            template_id=request.template_id,
            payload=request.payload.model_dump(),
            status=DeliveryStatus.PENDING,
        )

        for channel in allowed_channels:
            await self.repo.create_delivery(
                notification_id=notification.id,
                channel=channel,
                status=DeliveryStatus.PENDING,
            )

        await self.session.commit()

        if request.idempotency_key:
            await set_idempotency_key(request.idempotency_key, str(notification.id))

        queue_name = PRIORITY_QUEUE_MAP[request.priority]
        from app.worker.tasks import process_delivery

        deliveries = await self.repo.get_deliveries_by_notification_id(notification.id)
        for delivery in deliveries:
            process_delivery.apply_async(
                args=[str(delivery.id)],
                queue=queue_name,
            )

        await self.repo.update_status(notification.id, DeliveryStatus.QUEUED)
        await self.session.commit()

        refreshed = await self.repo.get_by_id(notification.id)
        logger.info(
            "notification_created",
            notification_id=str(notification.id),
            user_id=request.user_id,
            channels=[ch.value for ch in allowed_channels],
            priority=request.priority.value,
        )
        return NotificationResponse.model_validate(refreshed)

    async def get_notification(self, notification_id: uuid.UUID) -> NotificationResponse:
        notification = await self.repo.get_by_id(notification_id)
        if not notification:
            raise NotificationNotFoundError(str(notification_id))
        return NotificationResponse.model_validate(notification)

    async def get_user_notifications(
        self, user_id: str, page: int = 1, size: int = 20
    ) -> NotificationListResponse:
        notifications, total = await self.repo.get_by_user_id(user_id, page, size)
        return NotificationListResponse(
            items=[NotificationResponse.model_validate(n) for n in notifications],
            total=total,
            page=page,
            size=size,
        )
