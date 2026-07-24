import asyncio
import uuid
from datetime import datetime, timezone

from app.core.constants import DeliveryStatus, MAX_RETRIES, RETRY_BACKOFF_BASE
from app.core.logging import get_logger
from app.db.session import async_session_factory
from app.providers import get_provider
from app.repositories.notification_repository import NotificationRepository
from app.repositories.template_repository import TemplateRepository
from app.utils.template_engine import render_template
from app.worker.celery_app import celery_app

logger = get_logger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _process_delivery(delivery_id: str) -> None:
    async with async_session_factory() as session:
        repo = NotificationRepository(session)
        template_repo = TemplateRepository(session)

        delivery = await repo.get_delivery_by_id(uuid.UUID(delivery_id))
        if not delivery:
            logger.error("delivery_not_found", delivery_id=delivery_id)
            return

        await repo.update_delivery(delivery.id, status=DeliveryStatus.PROCESSING)
        await session.commit()

        notification = await repo.get_by_id(delivery.notification_id)
        if not notification:
            logger.error("notification_not_found", notification_id=str(delivery.notification_id))
            return

        payload = notification.payload or {}
        subject = payload.get("subject", "")
        body = payload.get("body", "")
        variables = payload.get("variables", {})

        if notification.template_id:
            template = await template_repo.get_by_id(notification.template_id)
            if template:
                subject = render_template(template.subject, variables)
                body = render_template(template.body, variables)
            else:
                subject = render_template(subject, variables)
                body = render_template(body, variables)
        elif variables:
            subject = render_template(subject, variables)
            body = render_template(body, variables)

        provider = get_provider(delivery.channel)
        response = await provider.send(
            recipient=notification.user_id,
            subject=subject,
            body=body,
            metadata={"notification_id": str(notification.id), "channel": delivery.channel.value},
        )

        now = datetime.now(timezone.utc)

        if response.success:
            await repo.update_delivery(
                delivery.id,
                status=DeliveryStatus.DELIVERED,
                provider_response=response.raw_response,
                sent_at=now,
                delivered_at=now,
                error_message=None,
            )
            logger.info(
                "delivery_success",
                delivery_id=delivery_id,
                channel=delivery.channel.value,
                provider_message_id=response.provider_message_id,
            )
        else:
            new_retry_count = delivery.retry_count + 1
            if new_retry_count > MAX_RETRIES:
                await repo.update_delivery(
                    delivery.id,
                    status=DeliveryStatus.FAILED,
                    retry_count=new_retry_count,
                    error_message=response.error_message,
                )
                logger.error(
                    "delivery_failed_permanently",
                    delivery_id=delivery_id,
                    channel=delivery.channel.value,
                    retry_count=new_retry_count,
                )
            else:
                await repo.update_delivery(
                    delivery.id,
                    status=DeliveryStatus.QUEUED,
                    retry_count=new_retry_count,
                    error_message=response.error_message,
                )
                await session.commit()
                raise Exception(f"Provider failed for delivery {delivery_id}: {response.error_message}")

        await session.commit()

        all_deliveries = await repo.get_deliveries_by_notification_id(notification.id)
        statuses = {d.status for d in all_deliveries}

        if all(s == DeliveryStatus.DELIVERED for s in statuses):
            aggregated = DeliveryStatus.DELIVERED
        elif DeliveryStatus.FAILED in statuses and all(
            s in (DeliveryStatus.DELIVERED, DeliveryStatus.FAILED) for s in statuses
        ):
            aggregated = DeliveryStatus.FAILED
        elif all(s == DeliveryStatus.SENT for s in statuses):
            aggregated = DeliveryStatus.SENT
        else:
            aggregated = DeliveryStatus.PROCESSING

        await repo.update_status(notification.id, aggregated)
        await session.commit()


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=RETRY_BACKOFF_BASE,
    retry_backoff_max=60,
    max_retries=MAX_RETRIES,
    acks_late=True,
)
def process_delivery(self, delivery_id: str) -> None:
    _run_async(_process_delivery(delivery_id))
