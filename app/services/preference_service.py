from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Channel
from app.core.exceptions import UserPreferencesNotFoundError
from app.repositories.preference_repository import PreferenceRepository
from app.schemas.preference import PreferenceRequest, PreferenceResponse


class PreferenceService:
    def __init__(self, session: AsyncSession):
        self.repo = PreferenceRepository(session)

    async def get_preferences(self, user_id: str) -> PreferenceResponse:
        preference = await self.repo.get_by_user_id(user_id)
        if not preference:
            raise UserPreferencesNotFoundError(user_id)
        return PreferenceResponse.model_validate(preference)

    async def upsert_preferences(
        self, user_id: str, request: PreferenceRequest
    ) -> PreferenceResponse:
        preference = await self.repo.upsert(
            user_id=user_id,
            email_enabled=request.email_enabled,
            sms_enabled=request.sms_enabled,
            push_enabled=request.push_enabled,
        )
        return PreferenceResponse.model_validate(preference)

    async def get_allowed_channels(
        self, user_id: str, requested_channels: list[Channel]
    ) -> list[Channel]:
        preference = await self.repo.get_by_user_id(user_id)
        if not preference:
            return requested_channels

        channel_enabled_map = {
            Channel.EMAIL: preference.email_enabled,
            Channel.SMS: preference.sms_enabled,
            Channel.PUSH: preference.push_enabled,
        }
        return [ch for ch in requested_channels if channel_enabled_map.get(ch, True)]
