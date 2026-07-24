from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.notification import NotificationListResponse
from app.schemas.preference import PreferenceRequest, PreferenceResponse
from app.services.notification_service import NotificationService
from app.services.preference_service import PreferenceService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/{user_id}/notifications",
    response_model=NotificationListResponse,
    summary="Get notification history for a user",
)
async def get_user_notifications(
    user_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    service = NotificationService(session)
    return await service.get_user_notifications(user_id, page, size)


@router.post(
    "/{user_id}/preferences",
    response_model=PreferenceResponse,
    summary="Set user channel preferences",
)
async def set_preferences(
    user_id: str,
    request: PreferenceRequest,
    session: AsyncSession = Depends(get_session),
):
    service = PreferenceService(session)
    return await service.upsert_preferences(user_id, request)


@router.get(
    "/{user_id}/preferences",
    response_model=PreferenceResponse,
    summary="Get user channel preferences",
)
async def get_preferences(
    user_id: str,
    session: AsyncSession = Depends(get_session),
):
    service = PreferenceService(session)
    return await service.get_preferences(user_id)
