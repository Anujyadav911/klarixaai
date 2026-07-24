import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template


class TemplateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, template_id: uuid.UUID) -> Template | None:
        result = await self.session.execute(
            select(Template).where(Template.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Template | None:
        result = await self.session.execute(
            select(Template).where(Template.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Template:
        template = Template(**kwargs)
        self.session.add(template)
        await self.session.flush()
        return template
