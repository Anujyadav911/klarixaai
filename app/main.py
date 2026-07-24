from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.health import router as health_router
from app.api.notifications import router as notifications_router
from app.api.users import router as users_router
from app.core.logging import setup_logging
from app.utils.idempotency import close_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield
    await close_redis_client()


app = FastAPI(
    title="Notification Service",
    description="Centralized notification service supporting Email, SMS, and Push channels with priority queuing, delivery tracking, and retry mechanisms.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(notifications_router)
app.include_router(users_router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

