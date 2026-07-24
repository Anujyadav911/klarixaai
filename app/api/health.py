from fastapi import APIRouter, status

from app.core.logging import get_logger
from app.db.session import engine
from app.utils.idempotency import get_redis_client

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Service health check",
)
async def health_check():
    health = {"status": "healthy", "database": "unknown", "redis": "unknown"}

    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        health["database"] = "connected"
    except Exception as exc:
        health["database"] = "disconnected"
        health["status"] = "degraded"
        logger.error("health_check_db_failed", error=str(exc))

    try:
        client = await get_redis_client()
        await client.ping()
        health["redis"] = "connected"
    except Exception as exc:
        health["redis"] = "disconnected"
        health["status"] = "degraded"
        logger.error("health_check_redis_failed", error=str(exc))

    status_code = status.HTTP_200_OK if health["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return health
