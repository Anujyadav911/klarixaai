from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Template(BaseModel):
    __tablename__ = "templates"

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
