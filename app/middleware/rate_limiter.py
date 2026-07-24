import redis.asyncio as redis
from fastapi import Request

from app.core.config import settings
from app.core.exceptions import RateLimitExceededError
from app.core.logging import get_logger
from app.utils.idempotency import get_redis_client

logger = get_logger(__name__)


async def check_rate_limit(user_id: str) -> None:
    client = await get_redis_client()
    key = f"rate_limit:{user_id}"

    current = await client.get(key)
    if current is not None and int(current) >= settings.RATE_LIMIT_MAX:
        logger.warning("rate_limit_exceeded", user_id=user_id, current=current)
        raise RateLimitExceededError(user_id)

    pipe = client.pipeline()
    pipe.incr(key)
    pipe.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS, nx=True)
    await pipe.execute()
