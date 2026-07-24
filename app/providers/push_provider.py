import asyncio
import random
import uuid

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.base import BaseProvider, ProviderResponse

logger = get_logger(__name__)


class MockPushProvider(BaseProvider):
    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict | None = None,
    ) -> ProviderResponse:
        await asyncio.sleep(random.uniform(0.03, 0.1))

        if random.random() < settings.PROVIDER_FAILURE_RATE:
            logger.warning("mock_push_failed", recipient=recipient)
            return ProviderResponse(
                success=False,
                error_message="Mock push delivery failed (simulated)",
            )

        message_id = f"push-{uuid.uuid4().hex[:12]}"
        logger.info("mock_push_sent", recipient=recipient, message_id=message_id)
        return ProviderResponse(
            success=True,
            provider_message_id=message_id,
            raw_response={"provider": "mock_push", "status": "accepted"},
        )
