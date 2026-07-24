import redis.asyncio as redis

from app.core.config import settings
from app.core.constants import IDEMPOTENCY_KEY_TTL_SECONDS
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def close_redis_client() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def check_idempotency_key(key: str) -> str | None:
    client = await get_redis_client()
    existing_id = await client.get(f"idempotency:{key}")
    return existing_id


async def set_idempotency_key(key: str, notification_id: str) -> None:
    client = await get_redis_client()
    await client.setex(
        f"idempotency:{key}",
        IDEMPOTENCY_KEY_TTL_SECONDS,
        notification_id,
    )
