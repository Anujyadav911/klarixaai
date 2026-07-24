import asyncio
import random
import uuid

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.base import BaseProvider, ProviderResponse

logger = get_logger(__name__)


class MockEmailProvider(BaseProvider):
    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict | None = None,
    ) -> ProviderResponse:
        await asyncio.sleep(random.uniform(0.05, 0.2))

        if random.random() < settings.PROVIDER_FAILURE_RATE:
            logger.warning("mock_email_failed", recipient=recipient, subject=subject)
            return ProviderResponse(
                success=False,
                error_message="Mock email delivery failed (simulated)",
            )

        message_id = f"email-{uuid.uuid4().hex[:12]}"
        logger.info(
            "mock_email_sent",
            recipient=recipient,
            subject=subject,
            message_id=message_id,
        )
        return ProviderResponse(
            success=True,
            provider_message_id=message_id,
            raw_response={"provider": "mock_email", "status": "accepted"},
        )
