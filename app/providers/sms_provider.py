import asyncio
import random
import uuid

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.base import BaseProvider, ProviderResponse

logger = get_logger(__name__)


class MockSMSProvider(BaseProvider):
    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict | None = None,
    ) -> ProviderResponse:
        await asyncio.sleep(random.uniform(0.05, 0.15))

        if random.random() < settings.PROVIDER_FAILURE_RATE:
            logger.warning("mock_sms_failed", recipient=recipient)
            return ProviderResponse(
                success=False,
                error_message="Mock SMS delivery failed (simulated)",
            )

        message_id = f"sms-{uuid.uuid4().hex[:12]}"
        logger.info("mock_sms_sent", recipient=recipient, message_id=message_id)
        return ProviderResponse(
            success=True,
            provider_message_id=message_id,
            raw_response={"provider": "mock_sms", "status": "accepted"},
        )
