import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.notification import (
    NotificationCreateRequest,
    NotificationListResponse,
    NotificationResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send a new notification",
)
async def send_notification(
    request: NotificationCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    service = NotificationService(session)
    return await service.create_notification(request)


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Get notification status",
)
async def get_notification(
    notification_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    service = NotificationService(session)
    return await service.get_notification(notification_id)
