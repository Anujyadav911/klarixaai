from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preference import UserPreference


class PreferenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: str) -> UserPreference | None:
        result = await self.session.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: str, **kwargs) -> UserPreference:
        existing = await self.get_by_user_id(user_id)
        if existing:
            for key, value in kwargs.items():
                setattr(existing, key, value)
            await self.session.flush()
            return existing

        preference = UserPreference(user_id=user_id, **kwargs)
        self.session.add(preference)
        await self.session.flush()
        return preference
